
import inspect
import os
import pprint
import re
import socket
import time
from PySide6 import QtWidgets
from lupa import LuaRuntime

from network.UdpWireLogger import UdpWireLogger

_noDefault = object()

class SequenceHelper:
	"""
	This class is used to store helper functions for sequence generation.
	It is passed into the script function when it runs.
	"""
	def __init__(self, config, settingsManager = None, logger = None):
		self.config = config
		self.udpWireLogger = UdpWireLogger(self.config)
		self.settingsManager = settingsManager
		self.activeModuleName = ''
		self.activeScriptName = ''
		# Accept a logger callable from outside (e.g. DCSAutoMate.log). If none
		# provided, fall back to a simple print-based logger.
		if callable(logger):
			self.log = logger
		else:
			def _default_log(msg):
				try:
					print(msg, flush=True)
				except Exception:
					pass
			self.log = _default_log

	def setActiveModuleName(self, moduleName):
		self.activeModuleName = moduleName or ''

	def setActiveScriptName(self, scriptName):
		self.activeScriptName = scriptName or ''

	def makePushSeqCmd(self, seq):
		"""Return a pushSeqCmd closure that appends steps to seq.
		Usage in a script function: pushSeqCmd = helper.makePushSeqCmd(seq)
		Call syntax (unchanged from the old local definition):
		  pushSeqCmd(dt, cmd, arg)
		  pushSeqCmd(dt, cmd, arg, msg)
		  pushSeqCmd(dt, cmd, control='...', value=..., condition='=', duration=0)
		  pushSeqCmd(dt, 'scriptSpeech', 'text', asyncFlag=False)  # sync speech
		"""
		def pushSeqCmd(dt, cmd, *args, **kwargs):
			step = {'time': round(dt, 2), 'cmd': cmd}
			if args:
				step['arg'] = args[0]
				step['msg'] = args[1] if len(args) > 1 else ''
			step.update(kwargs)
			seq.append(step)
		self._queuedSeq = seq
		self._queuedTaken = 0
		return pushSeqCmd

	def takeQueued(self):
		"""Return the commands added by the current script's pushSeqCmd since the last call.  Used by the executor between a live script's yields."""
		seq = getattr(self, '_queuedSeq', None)
		if seq is None:
			return []
		batch = seq[self._queuedTaken:]
		self._queuedTaken = len(seq)
		return batch

	def setControlReader(self, reader):
		"""Install the function helper.read() uses: reader(control) returns the live value, or None if it can't be read."""
		self._controlReader = reader

	def read(self, control, default=_noDefault):
		"""Read a cockpit control's current value in a live script (call after a yield so earlier commands have run).

		Returns default if the value can't be read (e.g. DCS not connected); without a default, raises RuntimeError.
		"""
		reader = getattr(self, '_controlReader', None)
		value = reader(control) if reader else None
		if value is not None:
			return value
		if default is not _noDefault:
			return default
		raise RuntimeError(f'Could not read {control} from DCS, and no default was given.')

	def collectSequence(self, scriptResult):
		"""Return a script's full command list without running it: a list as-is, or a live script drained with no delays between batches."""
		if not inspect.isgenerator(scriptResult):
			return scriptResult
		commands = []
		for _ in scriptResult:
			commands.extend(self.takeQueued())
		commands.extend(self.takeQueued())
		return commands

	def _getPresetsPath(self):
		# Use the pre-calculated path from config
		savedGamesPath = self.config.get('dcsSavedGamesPath', '')
		if savedGamesPath:
			return os.path.join(savedGamesPath, 'Config', 'RouteToolPresets')

		# Fallback (shouldn't be reached if config is loaded correctly)
		userProfile = os.environ.get('USERPROFILE', '')
		if userProfile:
			return os.path.join(userProfile, 'Saved Games', 'DCS', 'Config', 'RouteToolPresets')

		return ''

	def _parseKeyValueMessage(self, msg):
		data = {}
		data['_type'] = msg.split(';', 1)[0] if ';' in msg else msg
		for part in msg.split(';'):
			if '=' in part:
				key, value = part.split('=', 1)
				data[key] = value
		return data

	def _luaTableGet(self, luaTable, key, defaultValue = None):
		try:
			value = luaTable[key]
		except Exception:
			return defaultValue
		if value is None:
			return defaultValue
		return value

	def mgrsTruncate(self, mgrs, totalDigits):
		"""Truncate an MGRS string (no spaces) to a specific numeric precision (e.g. 8 or 10).
		This only reduces precision; it does not add precision.
		"""
		if not mgrs:
			return ''
		mgrs = str(mgrs).upper().replace(' ', '')
		match = re.match(r'^(\d{1,2}[A-Z])([A-Z]{2})(\d+)$', mgrs)
		if not match:
			return mgrs
		zoneBand, digraph, digits = match.groups()
		if len(digits) % 2 != 0:
			return mgrs
		half = len(digits) // 2
		desiredHalf = int(totalDigits // 2)
		if desiredHalf >= half:
			return mgrs
		easting = digits[:half][:desiredHalf]
		northing = digits[half:][:desiredHalf]
		return f'{zoneBand}{digraph}{easting}{northing}'

	def _convertCoordInDcs(self, x, y, z, timeoutSeconds = 1.5):
		requestId = str(int(time.time() * 1000))
		recvSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
		try:
			recvSocket.bind(('127.0.0.1', 0))
			recvSocket.settimeout(0.25)
			replyPort = recvSocket.getsockname()[1]

			message = f'DCSAUTOMATE_COORD_CONVERT;requestId={requestId};replyPort={replyPort};x={x};y={y};z={z};'
			sendSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
			try:
				payload = message.encode('utf-8')
				addr = ('127.0.0.1', 7779)
				self.udpWireLogger.logUiTx(addr, payload)
				sendSocket.sendto(payload, addr)
			finally:
				sendSocket.close()

			startTime = time.time()
			while time.time() - startTime < timeoutSeconds:
				try:
					respBytes, respAddr = recvSocket.recvfrom(65535)
					self.udpWireLogger.logUiRx(respAddr, respBytes)
				except socket.timeout:
					continue
				respText = respBytes.decode('utf-8', errors = 'replace')
				data = self._parseKeyValueMessage(respText)
				if data.get('requestId') != requestId:
					continue
				if data.get('_type') != 'DCSAUTOMATE_COORD_CONVERT':
					continue

				okFlag = data.get('ok', '').lower() == 'true'
				if not okFlag:
					return {
						'ok': 'false',
						'error': data.get('error', 'Unknown error'),
						'_raw': respText,
					}

				mgrsText = data.get('mgrs', '')
				envName = data.get('env', '')
				mgrsZone = data.get('mgrsZone', '')
				mgrsDigraph = data.get('mgrsDigraph', '')
				mgrsEasting = data.get('mgrsEasting', '')
				mgrsNorthing = data.get('mgrsNorthing', '')

				if mgrsZone and mgrsDigraph and mgrsEasting and mgrsNorthing:
					try:
						eInt = int(float(mgrsEasting))
						nInt = int(float(mgrsNorthing))
						zoneMatch = re.match(r'^(\d{1,2})([A-Z])$', str(mgrsZone).strip().upper().replace(' ', ''))
						if zoneMatch:
							zoneNum, zoneBand = zoneMatch.groups()
							mgrsText = f'{zoneNum} {zoneBand} {str(mgrsDigraph).strip().upper()} {eInt:05d} {nInt:05d}'
						else:
							mgrsText = f'{str(mgrsZone).strip().upper()} {str(mgrsDigraph).strip().upper()} {eInt:05d} {nInt:05d}'
					except Exception:
						pass

				return {
					'ok': 'true',
					'env': envName,
					'groundAlt': float(data.get('groundAlt', '0') or 0),
					'lat': float(data.get('lat', '0') or 0),
					'lon': float(data.get('lon', '0') or 0),
					'mgrs': mgrsText,
					'mgrsZone': mgrsZone,
					'mgrsDigraph': mgrsDigraph,
					'mgrsEasting': mgrsEasting,
					'mgrsNorthing': mgrsNorthing,
					'_raw': respText,
				}

			return {
				'ok': 'false',
				'error': 'Timed out waiting for DCS coordinate conversion response',
				'_raw': 'timeout',
			}
		finally:
			recvSocket.close()

	def _loadRouteFromPresetFile(self, mapName, routeName):
		presetsPath = self._getPresetsPath()
		filePath = os.path.join(presetsPath, mapName + '.lua')
		with open(filePath, 'r') as f:
			content = f.read()

		lua = LuaRuntime(unpack_returned_tuples=True)
		lua.execute(content)
		presets = lua.globals().presets
		if not presets:
			raise RuntimeError('No presets table found')
		route = presets[routeName]
		if not route:
			raise RuntimeError(f'Route not found: {routeName}')

		indices = []
		for key in route:
			try:
				indices.append(int(key))
			except Exception:
				pass
		indices.sort()

		waypoints = []
		for idx in indices:
			wp = route[idx]
			x = float(self._luaTableGet(wp, 'x', 0) or 0)
			z = float(self._luaTableGet(wp, 'y', 0) or 0)
			y = float(self._luaTableGet(wp, 'alt', 0) or 0)
			waypoints.append({
				'x': x,
				'y': y,
				'z': z,
			})
		return waypoints

	def _processRouteData(self, mapName, routeName):
		"""
		Loads a RouteTool preset route and asks DCS to convert each waypoint xyz to lat/lon and MGRS.
		"""
		def metersToFeet(altMeters):
			try:
				altMeters = float(altMeters)
			except Exception:
				altMeters = 0.0
			altFeet = altMeters * 3.28084
			return altFeet

		def decimalDegreesToDdm(decimalDegrees):
			try:
				decimalDegrees = float(decimalDegrees)
			except Exception:
				decimalDegrees = 0.0
			absValue = abs(decimalDegrees)
			deg = int(absValue)
			minutes = (absValue - deg) * 60.0
			if decimalDegrees < 0:
				deg = -deg
			return {
				'deg': deg,
				'min': minutes,
			}

		def decimalDegreesToDms(decimalDegrees):
			try:
				decimalDegrees = float(decimalDegrees)
			except Exception:
				decimalDegrees = 0.0
			absValue = abs(decimalDegrees)
			deg = int(absValue)
			minutesTotal = (absValue - deg) * 60.0
			minInt = int(minutesTotal)
			seconds = (minutesTotal - minInt) * 60.0
			if decimalDegrees < 0:
				deg = -deg
			return {
				'deg': deg,
				'min': minInt,
				'sec': seconds,
			}

		try:
			rawWaypoints = self._loadRouteFromPresetFile(mapName, routeName)
		except Exception as e:
			QtWidgets.QMessageBox.warning(None, 'Route Conversion Error', f'Failed to load route from RouteTool presets.\n\nError: {e}')
			return None

		self.log(f'Coord convert: route={routeName} map={mapName} waypoints={len(rawWaypoints)}')

		waypoints = []
		waypointCount = len(rawWaypoints)
		wpIndex = 0
		for wp in rawWaypoints:
			wpIndex += 1
			altMeters = wp.get('y', 0)
			altFeet = metersToFeet(altMeters)
			try:
				resp = self._convertCoordInDcs(wp['x'], wp['y'], wp['z'])
			except Exception as e:
				QtWidgets.QMessageBox.warning(None, 'Route Conversion Error', f'Failed to get coordinate conversion from DCS.\n\nMake sure DCS is running in-mission and DCSAutoMateHook.lua is installed.\n\nError: {e}')
				return None

			if altMeters != 0 and float(resp.get('groundAlt', 0)) == 0:
				self.log(f"Warning: Waypoint altitude is {altMeters} but ground altitude converted as 0. You might be on the wrong map.")

			respOk = resp.get('ok', '').lower() == 'true'
			self.log(f"Coord convert {wpIndex}/{waypointCount}: ok={respOk} env={resp.get('env','')} groundAlt={resp.get('groundAlt',0)} lat={resp.get('lat',0)} lon={resp.get('lon',0)} mgrs='{resp.get('mgrs','')}' zone='{resp.get('mgrsZone','')}' digraph='{resp.get('mgrsDigraph','')}' e='{resp.get('mgrsEasting','')}' n='{resp.get('mgrsNorthing','')}' error='{resp.get('error','')}'")

			if resp.get('ok', '').lower() != 'true':
				waypoints.append({
					'dcsCoord': {
						'x': wp.get('x', 0),
						'y': wp.get('y', 0),
						'z': wp.get('z', 0),
					},
					'altMeters': altMeters,
					'altFeet': altFeet,
					'latLonDD': None,
					'latLonDDM': None,
					'latLonDMS': None,
					'mgrs10': '',
					'mgrs6': '',
					'mgrs8': '',
					'groundAltMeters': 0,
					'groundAltFeet': 0,
					'env': resp.get('env', ''),
					'error': resp.get('error', 'Unknown error'),
				})
				continue

			lat = resp.get('lat', 0)
			lon = resp.get('lon', 0)
			mgrs10 = str(resp.get('mgrs', '')).upper().replace(' ', '')
			mgrs6 = self.mgrsTruncate(mgrs10, 6)
			mgrs8 = self.mgrsTruncate(mgrs10, 8)

			waypoints.append({
				'dcsCoord': {
					'x': wp.get('x', 0),
					'y': wp.get('y', 0),
					'z': wp.get('z', 0),
				},
				'altMeters': altMeters,
				'altFeet': altFeet,
				'latLonDD': {
					'lat': {'deg': lat},
					'lon': {'deg': lon},
				},
				'latLonDDM': {
					'lat': decimalDegreesToDdm(lat),
					'lon': decimalDegreesToDdm(lon),
				},
				'latLonDMS': {
					'lat': decimalDegreesToDms(lat),
					'lon': decimalDegreesToDms(lon),
				},
				'mgrs10': mgrs10,
				'mgrs6': mgrs6,
				'mgrs8': mgrs8,
				'groundAltMeters': resp.get('groundAlt', 0),
				'groundAltFeet': metersToFeet(resp.get('groundAlt', 0)),
				'env': resp.get('env', ''),
				'error': '',
			})

		output = {
			'map': mapName,
			'route': routeName,
			'waypoints': waypoints,
		}
		self.log(f'Parsed {len(waypoints)} waypoints from {routeName} in {mapName}')
		self.log(pprint.pformat(output))

		return output

	def getRouteFiles(self):
		"""
		Returns a list of available route file names (map names) from RouteToolPresets.
		"""
		presetsPath = self._getPresetsPath()
		if not os.path.exists(presetsPath):
			return []
		try:
			files = [os.path.splitext(f)[0] for f in os.listdir(presetsPath) if f.endswith('.lua')]
			files.sort()
			return files
		except Exception as e:
			self.log(f"Error listing route files: {e}")
			return []

	def getRouteNames(self, routeFile):
		"""
		Returns a list of route names within the specified route file.
		"""
		if not routeFile:
			return []
		presetsPath = self._getPresetsPath()
		filePath = os.path.join(presetsPath, routeFile + '.lua')
		if not os.path.exists(filePath):
			return []
		try:
			with open(filePath, 'r') as f:
				content = f.read()
			lua = LuaRuntime(unpack_returned_tuples=True)
			lua.execute(content)
			presets = lua.globals().presets
			if not presets:
				return []
			routes = [str(key) for key in presets]
			routes.sort()
			return routes
		except Exception as e:
			self.log(f"Error reading routes from {routeFile}: {e}")
			return []

	def getRouteData(self, routeFile, routeName):
		"""
		Returns the processed route data for the specified route file and route name.
		"""
		if not routeFile or not routeName:
			return None
		return self._processRouteData(routeFile, routeName)

	def _getScratchpadPath(self):
		# Use the pre-calculated path from config
		savedGamesPath = self.config.get('dcsSavedGamesPath', '')
		if savedGamesPath:
			return os.path.join(savedGamesPath, 'Scratchpad')

		# Fallback
		userProfile = os.environ.get('USERPROFILE', '')
		if userProfile:
			return os.path.join(userProfile, 'Saved Games', 'DCS', 'Scratchpad')

		return ''

	def getScratchpadFiles(self):
		"""
		Returns a list of available scratchpad file names (*.txt) from the Scratchpad folder.
		"""
		scratchpadPath = self._getScratchpadPath()
		if not os.path.exists(scratchpadPath):
			return []
		try:
			files = [f for f in os.listdir(scratchpadPath) if f.endswith('.txt')]
			files.sort()
			return files
		except Exception as e:
			self.log(f"Error listing scratchpad files: {e}")
			return []

	def getScratchpadData(self, filename):
		"""
		Parses a scratchpad file and returns a list of waypoints.  Sample scratchpad entry:

		DMS: N  42°03'00.89", E 041°46'04.84"
		DDM: N  42°03.0150', E 041°46.0808'
		MGRS: 37 T GG 29069 59063
		N/S (m): -305405, E/W (m): 626345
		5m, 16ft
		"""
		if not filename:
			return []

		scratchpadPath = self._getScratchpadPath()
		filePath = os.path.join(scratchpadPath, filename)

		if not os.path.exists(filePath):
			return []

		try:
			with open(filePath, 'r', encoding='utf-8', errors='replace') as f:
				content = f.read()
		except Exception as e:
			self.log(f"Error reading scratchpad file {filename}: {e}")
			return []

		waypoints = []

		blockRegex = re.compile(
			r'^DMS:\s*'
			r'(?P<dmsLatHem>[NS])\s*(?P<dmsLatDeg>\d{1,3})°(?P<dmsLatMin>\d{2})\'(?P<dmsLatSec>\d{2}(?:\.\d+)?)",\s*'
			r'(?P<dmsLonHem>[EW])\s*(?P<dmsLonDeg>\d{1,3})°(?P<dmsLonMin>\d{2})\'(?P<dmsLonSec>\d{2}(?:\.\d+)?)"\s*\r?\n'
			r'^DDM:\s*'
			r'(?P<ddmLatHem>[NS])\s*(?P<ddmLatDeg>\d{1,3})°(?P<ddmLatMin>\d{2}(?:\.\d+)?)\',\s*'
			r'(?P<ddmLonHem>[EW])\s*(?P<ddmLonDeg>\d{1,3})°(?P<ddmLonMin>\d{2}(?:\.\d+)?)\'\s*\r?\n'
			r'^MGRS:\s*'
			r'(?P<mgrsZone>\d{1,2})\s*(?P<mgrsBand>[C-HJ-NP-X])\s*(?P<mgrsSquare>[A-Z]{2})\s*'
			r'(?P<mgrsEasting>\d+)\s+(?P<mgrsNorthing>\d+)\s*\r?\n'
			r'^N/S \(m\):\s*(?P<nsMeters>-?\d+(?:\.\d+)?),\s*E/W \(m\):\s*(?P<ewMeters>-?\d+(?:\.\d+)?)\s*\r?\n'
			r'(?P<altMeters>\d+(?:\.\d+)?)m,\s*(?P<altFeet>\d+(?:\.\d+)?)ft\s*$',
			re.MULTILINE
		)

		def dd_from_dms(deg, minutes, seconds, hemisphere):
			try:
				deg = float(deg)
				minutes = float(minutes)
				seconds = float(seconds)
			except Exception:
				return 0.0
			abs_deg = abs(deg)
			value = abs_deg + (minutes / 60.0) + (seconds / 3600.0)
			if hemisphere in ('S', 'W'):
				value = -value
			return value

		for match in blockRegex.finditer(content):
			groups = match.groupdict()

			dmsLatHem = groups.get('dmsLatHem', '').upper()
			dmsLonHem = groups.get('dmsLonHem', '').upper()
			ddmLatHem = groups.get('ddmLatHem', '').upper()
			ddmLonHem = groups.get('ddmLonHem', '').upper()

			dmsLatDeg = int(groups.get('dmsLatDeg', 0) or 0)
			dmsLatMin = int(groups.get('dmsLatMin', 0) or 0)
			dmsLatSec = float(groups.get('dmsLatSec', 0) or 0)
			dmsLonDeg = int(groups.get('dmsLonDeg', 0) or 0)
			dmsLonMin = int(groups.get('dmsLonMin', 0) or 0)
			dmsLonSec = float(groups.get('dmsLonSec', 0) or 0)

			ddmLatDeg = int(groups.get('ddmLatDeg', 0) or 0)
			ddmLatMin = float(groups.get('ddmLatMin', 0) or 0)
			ddmLonDeg = int(groups.get('ddmLonDeg', 0) or 0)
			ddmLonMin = float(groups.get('ddmLonMin', 0) or 0)

			altMeters = float(groups.get('altMeters', 0) or 0)
			altFeet = float(groups.get('altFeet', 0) or 0)

			if dmsLatHem == 'S':
				dmsLatDeg = -dmsLatDeg
			if dmsLonHem == 'W':
				dmsLonDeg = -dmsLonDeg
			if ddmLatHem == 'S':
				ddmLatDeg = -ddmLatDeg
			if ddmLonHem == 'W':
				ddmLonDeg = -ddmLonDeg

			latDd = dd_from_dms(dmsLatDeg, dmsLatMin, dmsLatSec, dmsLatHem)
			lonDd = dd_from_dms(dmsLonDeg, dmsLonMin, dmsLonSec, dmsLonHem)

			mgrsZone = str(groups.get('mgrsZone', '') or '').strip().upper()
			mgrsBand = str(groups.get('mgrsBand', '') or '').strip().upper()
			mgrsSquare = str(groups.get('mgrsSquare', '') or '').strip().upper()
			mgrsEasting = str(groups.get('mgrsEasting', '') or '').strip()
			mgrsNorthing = str(groups.get('mgrsNorthing', '') or '').strip()
			mgrs10 = f'{mgrsZone}{mgrsBand}{mgrsSquare}{mgrsEasting}{mgrsNorthing}'
			mgrs10 = mgrs10.replace(' ', '')
			mgrs6 = self.mgrsTruncate(mgrs10, 6)
			mgrs8 = self.mgrsTruncate(mgrs10, 8)

			waypoints.append({
				'latLonDD': {
					'lat': {'deg': latDd},
					'lon': {'deg': lonDd},
				},
				'latLonDDM': {
					'lat': {
						'deg': ddmLatDeg,
						'min': ddmLatMin,
					},
					'lon': {
						'deg': ddmLonDeg,
						'min': ddmLonMin,
					},
				},
				'latLonDMS': {
					'lat': {
						'deg': dmsLatDeg,
						'min': dmsLatMin,
						'sec': dmsLatSec,
					},
					'lon': {
						'deg': dmsLonDeg,
						'min': dmsLonMin,
						'sec': dmsLonSec,
					},
				},
				'mgrs': {
					'zone': mgrsZone,
					'band': mgrsBand,
					'square': mgrsSquare,
					'easting': mgrsEasting,
					'northing': mgrsNorthing,
				},
				'mgrs10': mgrs10,
				'mgrs8': mgrs8,
				'mgrs6': mgrs6,
				'nsMeters': float(groups.get('nsMeters', 0) or 0),
				'ewMeters': float(groups.get('ewMeters', 0) or 0),
				'altMeters': altMeters,
				'altFeet': altFeet,
				'groundAltFeet': altFeet,
			})

		self.log(f'Parsed {len(waypoints)} waypoints from scratchpad file {filename}')
		self.log(pprint.pformat(waypoints))

		return waypoints
