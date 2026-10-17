import json
import os
import re
import socket
import threading
import time

from utils.appPaths import appBaseDir

TELEMETRY_MODULE = 'telemetry'
_telemetryNamePattern = re.compile(r'^LoGet[A-Za-z0-9]+(\.[^.]+)*$')

# Common LoGet* fields, listed in DCSControlPanel's telemetry module.  Any other path into a LoGet* result can be read too.
TELEMETRY_CATALOGUE = {
	'LoGetModelTime': 'Mission time since start (s)',
	'LoGetMissionStartTime': 'Mission start time of day (s after midnight)',
	'LoGetPilotName': 'Pilot name',
	'LoGetSelfData.Name': 'Aircraft type',
	'LoGetSelfData.LatLongAlt.Lat': 'Latitude (deg)',
	'LoGetSelfData.LatLongAlt.Long': 'Longitude (deg)',
	'LoGetSelfData.LatLongAlt.Alt': 'Altitude MSL (m)',
	'LoGetSelfData.Heading': 'True heading (rad)',
	'LoGetSelfData.Pitch': 'Pitch (rad)',
	'LoGetSelfData.Bank': 'Bank (rad)',
	'LoGetIndicatedAirSpeed': 'Indicated airspeed (m/s)',
	'LoGetTrueAirSpeed': 'True airspeed (m/s)',
	'LoGetMachNumber': 'Mach number',
	'LoGetVerticalVelocity': 'Vertical velocity (m/s)',
	'LoGetAltitudeAboveSeaLevel': 'Altitude above sea level (m)',
	'LoGetAltitudeAboveGroundLevel': 'Altitude above ground level (m)',
	'LoGetRadarAltimeter': 'Radar altimeter (m)',
	'LoGetAngleOfAttack': 'Angle of attack (rad)',
	'LoGetEngineInfo.RPM.left': 'Engine RPM, left (%)',
	'LoGetEngineInfo.RPM.right': 'Engine RPM, right (%)',
	'LoGetEngineInfo.Temperature.left': 'Engine temperature, left (deg C)',
	'LoGetEngineInfo.Temperature.right': 'Engine temperature, right (deg C)',
	'LoGetEngineInfo.HydraulicPressure.left': 'Hydraulic pressure, left (kg/cm2)',
	'LoGetEngineInfo.HydraulicPressure.right': 'Hydraulic pressure, right (kg/cm2)',
	'LoGetEngineInfo.FuelConsumption.left': 'Fuel flow, left (kg/s)',
	'LoGetEngineInfo.FuelConsumption.right': 'Fuel flow, right (kg/s)',
	'LoGetEngineInfo.fuel_internal': 'Internal fuel (kg)',
	'LoGetEngineInfo.fuel_external': 'External fuel (kg)',
	'LoGetMechInfo.gear.value': 'Gear position (0 = up, 1 = down)',
	'LoGetMechInfo.flaps.value': 'Flap position',
	'LoGetMechInfo.speedbrakes.value': 'Speed brake position',
	'LoGetMechInfo.canopy.value': 'Canopy position',
	'LoGetMechInfo.hook.value': 'Hook position',
	'LoGetMechInfo.wheelbrakes.value': 'Wheel brakes',
	'LoGetPayloadInfo.CurrentStation': 'Selected weapon station (0 = none)',
	'LoGetPayloadInfo.Cannon.shells': 'Gun rounds remaining',
	# Added in DCS 2.9.30.  LoGetPlayerSeat and LoGetFMData need ownship export allowed.
	'LoGetPlayerSeat': 'Player seat in a multicrew aircraft (0 = first seat)',
	'LoGetFMData.master': 'Player is flying the flight model (multicrew)',
	'LoGetModelTimeAcceleration': 'Time acceleration factor',
	'LoGetNetIsRunning': 'Multiplayer session running',
	'LoGetTrackIsReading': 'Track replay playing',
}


def parseTelemetryRef(ref):
	"""'telemetry/LoGetEngineInfo.RPM.right' -> ('LoGetEngineInfo', ['RPM', 'right']); None if ref isn't a telemetry ref."""
	if not isinstance(ref, str) or not ref.startswith(f'{TELEMETRY_MODULE}/'):
		return None
	name = ref[len(TELEMETRY_MODULE) + 1:]
	if not _telemetryNamePattern.match(name):
		return None
	parts = name.split('.')
	return parts[0], parts[1:]


def telemetryValueAt(value, path):
	"""Follow path into a decoded LoGet* result.  List indexes are 1-based, as in Lua.  Returns None if the path doesn't exist."""
	for key in path:
		if isinstance(value, dict):
			value = value.get(key)
		elif isinstance(value, list) and key.isdigit() and 1 <= int(key) <= len(value):
			value = value[int(key) - 1]
		else:
			return None
		if value is None:
			return None
	return value


def telemetryControl(name):
	return {
		'telemetry': name.split('.', 1)[0],
		'description': TELEMETRY_CATALOGUE.get(name, name),
		'category': 'Telemetry',
	}


# Left out because they change constantly: mission time, and the flight model data (accelerations, rates, ...).
SNAPSHOT_TELEMETRY_FUNCTIONS = sorted({name.split('.', 1)[0] for name in TELEMETRY_CATALOGUE} - {'LoGetModelTime', 'LoGetFMData'})


def flattenTelemetry(functionName, value):
	"""{'telemetry/<functionName>.<path>': leaf} for a decoded LoGet* result, with list entries numbered from 1 as in Lua, so each ref can be read back."""
	flat = {}
	def walk(ref, node):
		if isinstance(node, dict):
			for key, child in node.items():
				walk(f'{ref}.{key}', child)
		elif isinstance(node, list):
			for index, child in enumerate(node, start=1):
				walk(f'{ref}.{index}', child)
		elif node is not None:
			flat[ref] = node
	walk(f'{TELEMETRY_MODULE}/{functionName}', value)
	return flat


class DCSDirectManager:
	"""TCP-based connection manager for DCS World cockpit control.

	Connects to the DCSAutoMateExport.lua TCP server in DCS World to send
	commands and query cockpit state directly, without DCS BIOS.

	Public interface:
		- sendControl(controlName, value) -> bool
		- getControlState(controlRef) -> [(ref, description, value), ...]
		- controlExists(controlName) -> bool
		- getDescriptions(moduleName) -> {canonical: {description, category}}
		- getDescription(controlName) -> {description, category}
		- start() / stop()
		- outputString (status text for UI)
		- controlIndex (for controlExists lookups)
	"""

	def __init__(self, config):
		self.config = config
		self.host = config.get('dcsDirectHost', '127.0.0.1')
		self.port = config.get('dcsDirectPort', 7780)

		self.lock = threading.Lock()
		self.stopEvent = threading.Event()
		self.thread = None
		self.socket = None
		self.connected = False
		self.receiveBuffer = ''

		# Pending query responses, keyed by request tag (e.g. 'Q:0:181').
		self.pendingResponses = {}
		self.responseEvents = {}

		# Lightweight query stats — counters that DCSControlPanel (or any UI)
		# can read via getQueryStats() to detect a backlogged poll loop.
		# `timeouts` counts _queryWithResponse calls that didn't get a response
		# before the wait expired; `lateResponses` counts R:/D:/I:/E: lines that
		# arrived without a matching event still waiting (usually a late reply
		# to a previously-timed-out query).
		self.queryStats = {
			'queries': 0,
			'timeouts': 0,
			'lateResponses': 0,
			'reconnects': 0,
		}

		self.messages = {
			'base': 'DCS Direct connection: ',
			'notConnected': 'Not connected',
			'connected': 'Connected',
			'connecting': 'Connecting...',
			'error': 'Error',
		}
		self.outputString = f'{self.messages["base"]}{self.messages["notConnected"]}'

		# Load unified control mappings.
		self.controlMappings = self._loadControlMapping()

		# Build a controlIndex for O(1) lookups by 'moduleName/canonical'.
		self.controlIndex = self._buildControlIndex()


	def _loadControlMapping(self):
		"""Load the unified control mapping files from config/controlMappings/.

		Only loads files named exactly <moduleName>.json — ignores nameMap files
		and any other suffixed files.
		"""
		mappings = {}
		mappingsDir = os.path.join(appBaseDir(), 'config', 'controlMappings')
		if not os.path.exists(mappingsDir):
			return mappings

		for filename in os.listdir(mappingsDir):
			if not filename.endswith('.json'):
				continue
			if filename.endswith('_nameMap.json'):
				continue
			filepath = os.path.join(mappingsDir, filename)
			with open(filepath, 'r', encoding='utf-8') as f:
				data = json.load(f)
			moduleName = data.get('moduleName', filename.replace('.json', ''))
			expectedFilename = f'{moduleName}.json'
			if filename != expectedFilename:
				continue
			mappings[moduleName] = data

		return mappings

	def _buildControlIndex(self):
		"""Build a controlIndex dict for O(1) control lookups.

		Maps 'moduleName/canonical' to the control dict.
		"""
		index = {}
		for moduleName, mapping in self.controlMappings.items():
			controls = mapping.get('controls', {})
			for canonical, control in controls.items():
				index[f'{moduleName}/{canonical}'] = control
		return index

	def getControl(self, ref):
		"""The control dict for a 'module/canonical' ref, including telemetry refs; None if unknown."""
		if parseTelemetryRef(ref):
			return telemetryControl(ref.split('/', 1)[1])
		return self.controlIndex.get(ref)

	def reloadControlMappings(self):
		"""Reload all control mapping files from disk and rebuild the control index."""
		self.controlMappings = self._loadControlMapping()
		self.controlIndex = self._buildControlIndex()

	def getElementName(self, moduleControlRef):
		"""Return the DCS cockpit highlight element name for a module/canonical ref, or None."""
		control = self.controlIndex.get(moduleControlRef)
		return control.get('elementName') if control else None

	def highlightControl(self, moduleControlRef):
		"""Highlight a cockpit element in DCS via the Hook.lua UDP channel.

		Sends a DCSAUTOMATE_UI event=highlight packet to port 7779 (Hook.lua listener),
		which calls net.dostring_in('mission', 'a_cockpit_highlight(...)').
		Returns True if an element name was found and the UDP packet was sent.
		"""
		elementName = self.getElementName(moduleControlRef)
		if not elementName:
			return False
		msg = f'DCSAUTOMATE_UI;event=highlight;elementName={elementName};'
		port = self.config.get('uiRemoteControlReplyPort', 7779)
		try:
			s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
			s.sendto(msg.encode('utf-8'), ('127.0.0.1', port))
			s.close()
		except OSError:
			return False
		return True

	def clearHighlight(self):
		"""Remove any active cockpit highlight via the Hook.lua UDP channel."""
		msg = 'DCSAUTOMATE_UI;event=highlightClear;'
		port = self.config.get('uiRemoteControlReplyPort', 7779)
		try:
			s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
			s.sendto(msg.encode('utf-8'), ('127.0.0.1', port))
			s.close()
		except OSError:
			pass

	def getDescriptions(self, moduleName=None):
		"""Get a description dict for all controls in a module.

		Returns {canonical: {description, category}} dict for use by
		DCSSeqExecute's execute() and validateSequence() methods.
		"""
		descriptions = {}

		if moduleName and moduleName in self.controlMappings:
			moduleNames = [moduleName]
		else:
			moduleNames = list(self.controlMappings.keys())

		for modName in moduleNames:
			controls = self.controlMappings[modName].get('controls', {})
			for canonical, control in controls.items():
				descriptions[canonical] = {
					'description': control.get('description', ''),
					'category': control.get('category', ''),
				}

		return descriptions

	# ---- TCP Connection ----

	def _connect(self):
		"""Attempt to connect to the DCS export script TCP server."""
		try:
			sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
			sock.settimeout(2.0)
			sock.connect((self.host, self.port))
			sock.setblocking(False)
			with self.lock:
				self.socket = sock
				self.connected = True
				self.receiveBuffer = ''
			self.outputString = f'{self.messages["base"]}{self.messages["connected"]}'
			return True
		except (ConnectionRefusedError, TimeoutError, OSError):
			with self.lock:
				self.connected = False
				self.socket = None
			self.outputString = f'{self.messages["base"]}{self.messages["notConnected"]}'
			return False

	def _disconnect(self):
		"""Close the TCP connection."""
		with self.lock:
			if self.socket:
				try:
					self.socket.shutdown(socket.SHUT_RDWR)
				except Exception:
					pass
				try:
					self.socket.close()
				except Exception:
					pass
				self.socket = None
			self.connected = False
		self.outputString = f'{self.messages["base"]}{self.messages["notConnected"]}'

	def _send(self, message):
		"""Send a message to the DCS export script.

		Returns True on success, False on failure (will trigger reconnect).
		"""
		with self.lock:
			if not self.socket or not self.connected:
				return False
			try:
				self.socket.sendall((message + '\n').encode('utf-8'))
				return True
			except (BrokenPipeError, ConnectionResetError, OSError):
				self.connected = False
				return False

	def _receiveLines(self):
		"""Read any available data from the socket and return complete lines.

		Returns a list of complete lines (without newline). Incomplete lines
		are buffered for the next call.
		"""
		lines = []
		with self.lock:
			if not self.socket or not self.connected:
				return lines
			try:
				data = self.socket.recv(8192)
				if not data:
					# Connection closed by server.
					self.connected = False
					return lines
				self.receiveBuffer += data.decode('utf-8', errors='replace')
			except BlockingIOError:
				pass  # No data available right now.
			except (ConnectionResetError, OSError):
				self.connected = False
				return lines

		# Split buffer into complete lines.
		with self.lock:
			while '\n' in self.receiveBuffer:
				line, self.receiveBuffer = self.receiveBuffer.split('\n', 1)
				lines.append(line)

		return lines

	def _processResponse(self, line):
		"""Process a single response line from the DCS export script."""
		if not line:
			return

		prefix = line[0] if line else ''

		if prefix == 'R':
			# R:device:arg:value — response to Q query.
			parts = line.split(':', 3)
			if len(parts) >= 4:
				key = f'Q:{parts[1]}:{parts[2]}'
				value = parts[3]
				with self.lock:
					self.pendingResponses[key] = value
					if key in self.responseEvents:
						self.responseEvents[key].set()
					else:
						self.queryStats['lateResponses'] += 1

		elif prefix == 'U':
			# U:device:arg:value — subscription update.
			parts = line.split(':', 3)
			if len(parts) >= 4:
				key = f'W:{parts[1]}:{parts[2]}'
				with self.lock:
					self.pendingResponses[key] = parts[3]

		elif prefix == 'D':
			# D:indicationId:jsonText — display text response.
			parts = line.split(':', 2)
			if len(parts) >= 3:
				key = f'T:{parts[1]}'
				with self.lock:
					self.pendingResponses[key] = parts[2]
					if key in self.responseEvents:
						self.responseEvents[key].set()
					else:
						self.queryStats['lateResponses'] += 1

		elif prefix == 'I':
			# I:moduleName — module identification response.
			key = 'I'
			value = line[2:] if len(line) > 2 else ''
			with self.lock:
				self.pendingResponses[key] = value
				if key in self.responseEvents:
					self.responseEvents[key].set()

		elif prefix == 'E':
			# E:jsonData — engine info response.
			key = 'E'
			value = line[2:] if len(line) > 2 else ''
			with self.lock:
				self.pendingResponses[key] = value
				if key in self.responseEvents:
					self.responseEvents[key].set()

		elif prefix == 'G':
			# G:functionName:jsonResult — response to a G: telemetry query.
			parts = line.split(':', 2)
			if len(parts) >= 3:
				key = f'G:{parts[1]}'
				with self.lock:
					self.pendingResponses[key] = parts[2]
					if key in self.responseEvents:
						self.responseEvents[key].set()
					else:
						self.queryStats['lateResponses'] += 1

		elif line.startswith('BULKR:'):
			# BULKR:jsonObject — response to BULKQ bulk query.
			key = 'BULKQ'
			value = line[6:]  # After 'BULKR:'
			with self.lock:
				self.pendingResponses[key] = value
				if key in self.responseEvents:
					self.responseEvents[key].set()

	# ---- Thread Lifecycle ----

	def _runLoop(self):
		"""Main connection and receive loop. Runs in a separate thread."""
		while not self.stopEvent.is_set():
			# Connect if not connected.
			if not self.connected:
				self.outputString = f'{self.messages["base"]}{self.messages["connecting"]}'
				if not self._connect():
					# Wait before retrying, but check stop event.
					if self.stopEvent.wait(timeout=2.0):
						break
					continue

			# Read and process responses.
			lines = self._receiveLines()
			for line in lines:
				self._processResponse(line)

			# Check if still connected.
			if not self.connected:
				self._disconnect()
				continue

			# Brief sleep to avoid busy-waiting.
			if self.stopEvent.wait(timeout=0.01):
				break

	def start(self):
		"""Start the connection thread."""
		if self.thread and self.thread.is_alive():
			return

		self.stopEvent.clear()
		self.thread = threading.Thread(target=self._runLoop)
		self.thread.daemon = True
		self.thread.start()

	def stop(self):
		"""Stop the connection thread and close the socket."""
		self.stopEvent.set()
		self._disconnect()
		if self.thread:
			self.thread.join(timeout=1.0)
		self.outputString = f'{self.messages["base"]}{self.messages["notConnected"]}'

	def reconnect(self):
		"""Force a full TCP reset: drop the socket and clear all in-flight state.

		The background `_runLoop` will re-establish the connection on its next
		iteration.  Any callers currently blocked in `_queryWithResponse` are
		woken so they return `None` quickly instead of hanging for their full
		timeout.

		This is the "big hammer" used by DCSControlPanel's Force Refresh button
		when the user wants to clear a backlogged or wedged poll loop.
		"""
		with self.lock:
			# Wake any waiters first so they unwind cleanly.
			for event in self.responseEvents.values():
				event.set()
			self.responseEvents.clear()
			self.pendingResponses.clear()
			self.receiveBuffer = ''
			self.queryStats['reconnects'] += 1
		self._disconnect()
		self.outputString = f'{self.messages["base"]}{self.messages["connecting"]}'

	def getQueryStats(self):
		"""Return a snapshot copy of the query-stats counters."""
		with self.lock:
			return dict(self.queryStats)

	# ---- Query Methods ----

	def _queryWithResponse(self, sendCmd, responseKey, timeout=2.0):
		"""Send a command and wait for a specific response.

		Args:
			sendCmd: The command string to send (without newline).
			responseKey: The key to look up in pendingResponses.
			timeout: Maximum seconds to wait for response.

		Returns:
			The response value string, or None on timeout/failure.
		"""
		event = threading.Event()
		with self.lock:
			self.responseEvents[responseKey] = event
			self.queryStats['queries'] += 1

		if not self._send(sendCmd):
			with self.lock:
				self.responseEvents.pop(responseKey, None)
			return None

		# Wait for the response.
		signaled = event.wait(timeout=timeout)

		with self.lock:
			self.responseEvents.pop(responseKey, None)
			if not signaled:
				self.queryStats['timeouts'] += 1
			return self.pendingResponses.pop(responseKey, None)

	def queryArgumentValue(self, arg, device=0, timeout=2.0):
		"""Query get_argument_value(arg) on the specified device.

		Args:
			arg: The argument number to query.
			device: The device number (default 0 = mainpanel).
			timeout: Max seconds to wait.

		Returns:
			Float value, or None on timeout.
		"""
		sendCmd = f'Q:{device}:{arg}'
		responseKey = f'Q:{device}:{arg}'
		result = self._queryWithResponse(sendCmd, responseKey, timeout)
		if result is not None:
			try:
				return float(result)
			except (ValueError, TypeError):
				return None
		return None

	def queryIndication(self, indicationId, timeout=2.0):
		"""Query list_indication(indicationId) for display text.

		Args:
			indicationId: The indication ID number.
			timeout: Max seconds to wait.

		Returns:
			Dict of field name -> value (parsed from DCS indication format),
			or None on timeout.
		"""
		sendCmd = f'T:{indicationId}'
		responseKey = f'T:{indicationId}'
		result = self._queryWithResponse(sendCmd, responseKey, timeout)
		if result is not None and result != 'null':
			return self._parseIndication(result)
		return None

	def queryTelemetry(self, functionName, timeout=1.0):
		"""Call a LoGet* export function in DCS (e.g. 'LoGetEngineInfo') and return its decoded result, or None."""
		result = self._queryWithResponse(f'G:{functionName}', f'G:{functionName}', timeout)
		if result is None:
			return None
		try:
			return json.loads(result)
		except (json.JSONDecodeError, ValueError):
			return None

	def snapshotTelemetry(self, functionNames=None, timeout=0.5):
		"""Every field of the snapshot LoGet* functions, flattened to telemetry refs; functions DCS doesn't answer are left out."""
		snapshot = {}
		for functionName in functionNames or SNAPSHOT_TELEMETRY_FUNCTIONS:
			snapshot.update(flattenTelemetry(functionName, self.queryTelemetry(functionName, timeout=timeout)))
		return snapshot

	def queryModuleName(self, timeout=2.0):
		"""Query the current module/aircraft name from DCS.

		Returns:
			Module name string (e.g. 'FA-18C_hornet'), or None on timeout.
		"""
		result = self._queryWithResponse('I', 'I', timeout)
		return result if result else None

	def bulkQueryArgs(self, argList, timeout=10.0):
		"""Query multiple cockpit arg values in a single BULKQ round-trip.

		The Lua handler calls update_arguments() before reading, so values
		are guaranteed fresh from the DCS engine.

		Args:
			argList: Iterable of integer arg numbers to query.
			timeout: Max seconds to wait for the response.

		Returns:
			Dict of {argNum (int): float value}, or None on timeout/failure.
		"""
		jsonPayload = json.dumps([int(a) for a in argList])
		result = self._queryWithResponse(f'BULKQ:{jsonPayload}', 'BULKQ', timeout)
		if result is None:
			return None
		try:
			raw = json.loads(result)
			return {int(k): float(v) for k, v in raw.items() if v is not None}
		except (json.JSONDecodeError, ValueError, TypeError):
			return None

	def snapshotCockpitState(self, moduleName=None, timeout=10.0):
		"""Snapshot the current cockpit state for all controls with an arg.

		Queries every control in the loaded mapping (or a specific module) and
		returns a dict of canonical ref -> native float value. Indication-only
		controls (no arg field) are excluded. Wheel controls use displayArgs[0]
		as the read-back arg, matching getControlState() behaviour.

		Args:
			moduleName: Limit snapshot to a specific module. If None, all
				loaded modules are included.
			timeout: Max seconds to wait for the BULKQ response.

		Returns:
			Dict of {'moduleName/canonical': float}, or None on timeout/failure.
			Returns {} if no controls with args are found.
		"""
		if moduleName:
			moduleNames = [moduleName] if moduleName in self.controlMappings else []
		else:
			moduleNames = list(self.controlMappings.keys())

		# Build arg → canonical ref mapping (one entry per queryable control).
		argToRef = {}
		for modName in moduleNames:
			controls = self.controlMappings[modName].get('controls', {})
			for canonical, control in controls.items():
				if 'arg' not in control:
					continue
				# Wheel controls: use displayArgs[0] for readback (same as getControlState).
				if control.get('wheel') and control.get('displayArgs'):
					arg = control['displayArgs'][0]
				else:
					arg = control['arg']
				argToRef[int(arg)] = f'{modName}/{canonical}'

		if not argToRef:
			return {}

		values = self.bulkQueryArgs(list(argToRef.keys()), timeout=timeout)
		if values is None:
			return None

		return {argToRef[arg]: val for arg, val in values.items() if arg in argToRef}

	def rawScanSnapshot(self, maxArg=999, timeout=30.0):
		"""Scan all cockpit args 0..maxArg and return their current values.

		Useful for modules that don't have a control mapping yet — you can
		take two scans, diff them, and identify which arg number changed when
		you moved a switch.

		Args:
			maxArg: Highest arg number to scan (inclusive).
			timeout: Max seconds to wait (scanning 1000 args is fast in Lua
				but the response can be large; 30s is conservative).

		Returns:
			Dict of {argNum (int): float value}, or None on timeout/failure.
		"""
		result = self._queryWithResponse(f'BULKQ:scan:{maxArg}', 'BULKQ', timeout)
		if result is None:
			return None
		try:
			raw = json.loads(result)
			return {int(k): float(v) for k, v in raw.items() if v is not None}
		except (json.JSONDecodeError, ValueError, TypeError):
			return None

	def sendCommand(self, deviceId, commandId, value):
		"""Send a clickable action command to DCS.

		Args:
			deviceId: Target device number.
			commandId: Command number.
			value: Command value (typically -1, 0, or 1 for switches).

		Returns:
			True if sent successfully.
		"""
		return self._send(f'C:{deviceId}:{commandId}:{value}')

	def sendSimCommand(self, commandId, value=None):
		"""Send a simulator command (an iCommand, e.g. 312 = right throttle IDLE) via LoSetCommand.  No keyboard focus needed.

		Returns:
			True if sent successfully.
		"""
		if value is None:
			return self._send(f'L:{int(commandId)}')
		return self._send(f'L:{int(commandId)}:{value}')

	def sendSimCommandHold(self, commandId, seconds, stopCommandId=None, value=None):
		"""Hold a simulator command like a held key: DCS repeats it every frame (with value, for an axis) for seconds, or until releaseSimCommandHold if seconds is None, then sends stopCommandId once.

		Returns:
			True if sent successfully.
		"""
		if seconds is None or value is not None:
			stop = '' if stopCommandId is None else int(stopCommandId)
			return self._send(f'H:{int(commandId)}:{seconds or 0}:{stop}:{"" if value is None else value}')
		if stopCommandId is None:
			return self._send(f'H:{int(commandId)}:{seconds}')
		return self._send(f'H:{int(commandId)}:{seconds}:{int(stopCommandId)}')

	def releaseSimCommandHold(self, commandId):
		"""End a hold from sendSimCommandHold now, sending its stop command.  Does nothing if it isn't held."""
		return self._send(f'H:{int(commandId)}:release')

	def sendSetCommand(self, deviceId, commandId, value, arg=None):
		"""Send a SetCommand (for potentiometers/axes) to DCS.

		For defineSetCommandTumb controls, pass arg to also call set_argument_value
		on device 0 (MAIN_PANEL), matching what DCS BIOS does internally.

		Args:
			deviceId: Target device number.
			commandId: Command number.
			value: Value to set (typically 0.0 to 1.0).
			arg: Optional cockpit argument number. When provided, the Lua handler
				also calls set_argument_value(arg, value) on MAIN_PANEL.

		Returns:
			True if sent successfully.
		"""
		msg = f'S:{deviceId}:{commandId}:{value}'
		if arg is not None:
			msg += f':{arg}'
		return self._send(msg)

	# ---- Control Interface ----

	def _lookupControl(self, controlName, moduleName=None):
		"""Look up a control in the loaded mappings by canonical name.

		Args:
			controlName: The canonical control name (e.g. 'AHCP.AHCP_MASTER_ARM').
			moduleName: Optional module to search in.

		Returns:
			Control dict, or None if not found.
		"""
		if moduleName == TELEMETRY_MODULE:
			return telemetryControl(controlName) if parseTelemetryRef(f'{TELEMETRY_MODULE}/{controlName}') else None
		if moduleName:
			mapping = self.controlMappings.get(moduleName, {})
			return mapping.get('controls', {}).get(controlName)

		# Search all modules.
		for modName, mapping in self.controlMappings.items():
			hit = mapping.get('controls', {}).get(controlName)
			if hit:
				return hit
		return None

	def getDescription(self, controlName, moduleName=None):
		"""Get the description and category for a single control.

		Args:
			controlName: The control name (e.g. 'batterySw').
			moduleName: Optional module to search in.

		Returns:
			Dict with 'description' and 'category', or None if not found.
		"""
		control = self._lookupControl(controlName, moduleName)
		if control:
			return {
				'description': control.get('description', ''),
				'category': control.get('category', ''),
			}
		return None

	def _translateValue(self, control, value):
		"""Translate a script value to the native DCS value.

		Scripts send:
			Discrete: position index (0, 1, 2, ...)
			Continuous: proportional float (0.0 = min, 1.0 = max)
			Relative: delta float (passthrough)

		Args:
			control: The control dict from the mapping.
			value: The value from the script.

		Returns:
			The translated native value.
		"""
		controlType = control.get('type', '')

		if controlType == 'discrete':
			if 'positionMap' in control:
				# Multi-command control — value is position index, looked up in positionMap.
				# The actual command routing is handled by sendControl().
				# pdp_special entries use 'sendValue' (not 'value') as the trigger to send.
				idx = int(value)
				posMap = control['positionMap']
				if 0 <= idx < len(posMap) and posMap[idx] is not None:
					entry = posMap[idx]
					return entry.get('sendValue', entry.get('value', 0.0))
				return 0.0  # Center/release position.

			# Simple discrete: position index to native float.
			argLim = control.get('argLim', [0.0, 1.0])
			step = control.get('step', 1.0)
			return argLim[0] + step * float(value)

		elif controlType == 'continuous':
			# Continuous: script sends proportional 0.0-1.0 (0%=min, 100%=max), scale to argLim.
			argLim = control.get('argLim', [0.0, 1.0])
			proportion = max(0.0, min(1.0, float(value)))
			return argLim[0] + proportion * (argLim[1] - argLim[0])

		elif controlType == 'relative':
			# Relative: sign-driven normalization for incrementalTumb controls
			# (multiswitch_stop — any positive → incrementValue, any negative → decrementValue).
			# Other relative controls: passthrough.
			if 'incrementValue' in control or 'decrementValue' in control:
				v = float(value)
				if v > 0:
					return float(control.get('incrementValue', v))
				elif v < 0:
					return float(control.get('decrementValue', v))
				return 0.0
			return float(value)

		elif controlType == 'toggle':
			# Toggle: value is irrelevant — any send fires the flip. Always send 1.0.
			return 1.0

		# Unknown type — passthrough.
		return value

	def _reverseTranslateValue(self, control, nativeValue):
		"""Translate a native DCS value back to a script-convention value.

		Used by getControlState() to return values in the format scripts expect.

		Args:
			control: The control dict from the mapping.
			nativeValue: The raw float from get_argument_value.

		Returns:
			The script-convention value.
		"""
		controlType = control.get('type', '')

		if controlType == 'discrete':
			# Prefer positionMap when present — works for any position spacing
			# (including fractional spacings like FUEL_INTERFACE.FuelQtySelSw
			# which uses 0.0/0.1/0.2/0.3/0.4/0.5).  Fall back to argLim+step
			# for discrete controls defined without a positionMap.
			positionMap = control.get('positionMap')
			if positionMap:
				# Build a resolved value for every position, including None
				# (spring-loaded center) entries.  None entries have no explicit
				# command value but the cockpit arg still lands at the midpoint
				# between their neighbors; linear interpolation recovers that
				# value so nearest-neighbor matching returns the correct index.
				# pdp_special entries use 'readbackValue' (not 'value') for the stable arg.
				nonNone = [(i, e.get('readbackValue', e.get('value'))) for i, e in enumerate(positionMap) if e is not None and ('value' in e or 'readbackValue' in e)]
				resolvedValues = []
				for index, entry in enumerate(positionMap):
					rv = None
					if entry is not None:
						rv = entry.get('readbackValue', entry.get('value'))
					if rv is not None:
						resolvedValues.append((index, rv))
					else:
						left = next(((i, v) for i, v in reversed(nonNone) if i < index), None)
						right = next(((i, v) for i, v in nonNone if i > index), None)
						if left and right:
							t = (index - left[0]) / (right[0] - left[0])
							resolvedValues.append((index, left[1] + t * (right[1] - left[1])))
						elif left:
							resolvedValues.append((index, left[1]))
						elif right:
							resolvedValues.append((index, right[1]))
				bestIndex = 0
				bestDist = None
				for index, value in resolvedValues:
					dist = abs(value - nativeValue)
					if bestDist is None or dist < bestDist:
						bestDist = dist
						bestIndex = index
				return bestIndex

			# `indicatorPositions` is a list of physical stop-values from a
			# non-linear gauge scale (>2 elements).  Reverse-translate by
			# finding the index of the nearest value.
			indicatorPositions = control.get('indicatorPositions')
			if indicatorPositions:
				bestIndex = 0
				bestDist = None
				for index, stopValue in enumerate(indicatorPositions):
					dist = abs(stopValue - nativeValue)
					if bestDist is None or dist < bestDist:
						bestDist = dist
						bestIndex = index
				return bestIndex

			# `indicatorArgLim` overrides `argLim` for readback only — used
			# when the autopilot/controller writes back a value in a different
			# range than the command range.  E.g. Ka-50 autopilot buttons:
			# argLim=[0,1] is the press/release command range, but the
			# autopilot controller writes 0.0 (off) or ~0.1 (mode active)
			# back to the same arg.  With argLim+step the 0.1 rounds to 0;
			# indicatorArgLim=[0, 0.1] gives step=0.1 so 0.1 → position 1.
			# Values outside the indicator range are clamped.
			indicatorArgLim = control.get('indicatorArgLim')
			if indicatorArgLim:
				span = indicatorArgLim[1] - indicatorArgLim[0]
				positions = control.get('positions', 2)
				indicatorStep = span / (positions - 1) if positions > 1 else span
				if indicatorStep == 0:
					return 0
				pos = round((nativeValue - indicatorArgLim[0]) / indicatorStep)
				return max(0, min(positions - 1, pos))

			argLim = control.get('argLim', [0.0, 1.0])
			step = control.get('step', 1.0)
			if step == 0:
				return 0
			return round((nativeValue - argLim[0]) / step)

		elif controlType == 'continuous':
			# Native float to proportional 0.0-1.0.
			argLim = control.get('argLim', [0.0, 1.0])
			span = argLim[1] - argLim[0]
			if span == 0:
				return 0.0
			return (nativeValue - argLim[0]) / span

		elif controlType == 'toggle':
			# Return 0 at low state, 1 at high state.
			argLim = control.get('argLim', [0.0, 1.0])
			return 1 if abs(nativeValue - argLim[1]) < abs(nativeValue - argLim[0]) else 0

		# For read-only controls (no type), return native value as-is.
		return nativeValue

	def sendControl(self, controlName, value, moduleName=None):
		"""Send a command to DCS using a control name.

		Args:
			controlName: The control name (e.g. 'batterySw').
			value: The value to send (position index for discrete, float for continuous/relative).
			moduleName: Optional module name. If not provided, searches all loaded modules.

		Returns:
			True if sent successfully, False if control not found or send failed.
		"""
		# Split module/control prefix if present (e.g. 'FA-18C_hornet/batterySw').
		if '/' in controlName and moduleName is None:
			moduleName, controlName = controlName.split('/', 1)

		control = self._lookupControl(controlName, moduleName)
		if not control:
			return False

		controlType = control.get('type', '')
		if not controlType:
			return False  # Read-only control, can't send commands.

		# Handle positionMap controls (multi-command springloaded switches).
		if 'positionMap' in control:
			return self._sendPositionMapCommand(control, value)

		# Handle wheel controls (radio_wheel_1: 2-button increment/decrement
		# rotaries).  These are inherently click-based — each click moves one
		# notch CW or CCW with no seek.  Script value is a signed click count.
		if control.get('wheel'):
			return self._sendWheelCommand(control, value)

		deviceId = control.get('deviceId')
		commandId = control.get('commandId')
		if deviceId is None or commandId is None:
			return False

		# Raw controls bypass translation — pass the caller-supplied value directly to DCS.
		if controlType == 'raw':
			return self.sendCommand(deviceId, commandId, value)

		nativeValue = self._translateValue(control, value)

		# Allow per-control protocol override (e.g. DCS ITER commands need
		# performClickableAction with delta values, not SetCommand).
		sendProtocol = control.get('sendProtocol')
		if sendProtocol == 'C':
			return self.sendCommand(deviceId, commandId, nativeValue)
		elif sendProtocol == 'S':
			return self.sendSetCommand(deviceId, commandId, nativeValue, arg=control.get('arg'))
		elif controlType == 'relative':
			return self.sendSetCommand(deviceId, commandId, nativeValue)
		else:
			return self.sendCommand(deviceId, commandId, nativeValue)

	def _sendPositionMapCommand(self, control, value):
		"""Send a command for a positionMap control.

		Each command is explicit: pressing a position sends that position's command
		and value. Selecting the center/null position releases all commands (sends 0.0) for the control.
		No automatic releasing is done when pressing a non-null position, matching the
		DCS BIOS convention where every action must be explicitly commanded.

		Args:
			control: The control dict (must have 'positionMap').
			value: Position index (0, 1, 2, ...).

		Returns:
			True if all sends succeeded.
		"""
		posMap = control['positionMap']
		idx = int(value)

		# If the target position is non-null, just press it.
		if 0 <= idx < len(posMap) and posMap[idx] is not None:
			entry = posMap[idx]
			sendVal = entry.get('sendValue', entry.get('value', 0.0))
			result = self.sendCommand(entry['deviceId'], entry['commandId'], sendVal)
			# pdp_special controls use a trigger sendValue that differs from the
			# stable readbackValue.  A 0.0 release must follow the trigger send.
			if 'sendValue' in entry:
				self.sendCommand(entry['deviceId'], entry['commandId'], 0.0)
			return result

		# Center/null position: release all commands.
		success = True
		releaseCmds = set()
		for entry in posMap:
			if entry is not None:
				releaseCmds.add((entry['deviceId'], entry['commandId']))
		for deviceId, commandId in releaseCmds:
			if not self.sendCommand(deviceId, commandId, 0.0):
				success = False
		return success

	def _sendWheelCommand(self, control, value):
		"""Drive a wheel control (radio_wheel_1) by issuing click commands.

		Wheels are inherently relative in the cockpit: each click rotates one
		notch CW or CCW and there is no provision for seeking to an absolute
		position.  The script value is a signed integer click count: positive
		issues `incrementValue` clicks (CW), negative issues `decrementValue`
		clicks (CCW), 0 is a no-op.  Higher-level "set to frequency X" logic
		belongs in script helpers, not here.

		Args:
			control: The control dict (must have 'deviceId', 'commandId',
				'incrementValue', 'decrementValue').
			value: Signed integer click count.

		Returns:
			True if all sends succeeded (or no clicks were needed).
		"""
		deviceId = control.get('deviceId')
		commandId = control.get('commandId')
		decCommandId = control.get('decrementCommandId', commandId)
		incValue = control.get('incrementValue')
		decValue = control.get('decrementValue')

		if deviceId is None or commandId is None or incValue is None or decValue is None:
			return False

		clicks = int(value)
		if clicks == 0:
			return True

		clickValue = incValue if clicks > 0 else decValue
		sendCommandId = commandId if clicks > 0 else decCommandId
		count = abs(clicks)
		success = True
		for _ in range(count):
			if not self.sendCommand(deviceId, sendCommandId, clickValue):
				success = False
		return success

	def getControlState(self, listControlsToGet):
		"""Retrieve the state of specified controls.

		Args:
			listControlsToGet: A string or list of control references
				(e.g. 'FA-18C_hornet/canopyPos' or 'MetadataStart/_ACFT_NAME').

		Returns:
			List of tuples: [(controlRef, description, value), ...]
		"""
		if isinstance(listControlsToGet, str):
			listControlsToGet = [listControlsToGet]

		results = []

		for controlRef in listControlsToGet:
			telemetry = parseTelemetryRef(controlRef)
			if telemetry:
				functionName, path = telemetry
				description = telemetryControl(controlRef.split('/', 1)[1])['description']
				results.append((controlRef, description, telemetryValueAt(self.queryTelemetry(functionName), path)))
				continue

			# Handle MetadataStart/_ACFT_NAME specially — use I: command.
			if controlRef == 'MetadataStart/_ACFT_NAME':
				moduleName = self.queryModuleName(timeout=1.0)
				if moduleName:
					results.append((controlRef, 'Aircraft Name', moduleName))
				continue

			# Parse module/control from the reference.
			if '/' in controlRef:
				moduleName, controlName = controlRef.split('/', 1)
			else:
				moduleName = None
				controlName = controlRef

			control = self._lookupControl(controlName, moduleName)
			if not control:
				continue

			description = control.get('description', controlName)

			if 'indicationId' in control and 'fieldName' in control:
				# Query indication text via TCP.
				indicationId = control['indicationId']
				fieldName = control['fieldName']
				indication = self.queryIndication(indicationId, timeout=1.0)
				if indication and fieldName in indication:
					results.append((controlRef, description, indication[fieldName]))
				else:
					results.append((controlRef, description, ''))

			elif 'indicationId' in control:
				# Aggregate query: return all non-empty fields joined by newline.
				indicationId = control['indicationId']
				indication = self.queryIndication(indicationId, timeout=1.0)
				if indication:
					value = '\n'.join(v for v in indication.values() if v)
					results.append((controlRef, description, value))
				else:
					results.append((controlRef, description, ''))

			elif 'arg' in control:
				# Query get_argument_value via TCP.
				# For wheel controls with a separate display-arg chain (Mi-8/Mi-24
				# radio_wheel_1 / radio_wheel_double helpers), read the master
				# display arg instead of the pulse-counter arg so callers see the
				# visible cockpit position.
				if control.get('wheel') and control.get('displayArgs'):
					arg = control['displayArgs'][0]
				else:
					arg = control['arg']
				rawNative = self.queryArgumentValue(arg, device=0, timeout=1.0)
				if rawNative is not None:
					# Reverse translate to script convention; preserve raw native
					# value as a 4th tuple element for UIs that want to show it.
					translated = self._reverseTranslateValue(control, rawNative)
					results.append((controlRef, description, translated, rawNative))

		return results

	def pollControlStates(self, refs):
		"""Batched poll variant for DCSControlPanel's poll worker.

		Differs from `getControlState` in that all arg-style controls are
		queried in a single BULKQ TCP round-trip, so one slow or unresponsive
		arg cannot stall the rest of the poll set.  Indication/text controls
		(`indicationId`) and `MetadataStart/_ACFT_NAME` still use their
		per-ref T:/I: queries (with a tighter timeout) because there is no
		batched protocol for them today; if any of those times out it only
		holds up the others of the same kind, not the arg poll.

		Returns the same shape `getControlState` does:
		    [(controlRef, description, value, rawNative?), ...]
		Arg-style results always include the 4-tuple form (`rawNative`);
		indication and metadata results return 3-tuples.
		"""
		if isinstance(refs, str):
			refs = [refs]

		# Partition refs into arg-style, indication-style, and metadata.
		argEntries = []  # List of (controlRef, control, arg).
		indicationRefs = []
		metadataRefs = []
		telemetryRefs = {}  # functionName -> [(controlRef, path)], so each LoGet* function is queried once.
		for controlRef in refs:
			telemetry = parseTelemetryRef(controlRef)
			if telemetry:
				telemetryRefs.setdefault(telemetry[0], []).append((controlRef, telemetry[1]))
				continue
			if controlRef == 'MetadataStart/_ACFT_NAME':
				metadataRefs.append(controlRef)
				continue
			if '/' in controlRef:
				moduleName, controlName = controlRef.split('/', 1)
			else:
				moduleName, controlName = None, controlRef
			control = self._lookupControl(controlName, moduleName)
			if not control:
				continue
			if 'indicationId' in control:
				indicationRefs.append((controlRef, control))
				continue
			if 'arg' in control:
				# Wheel controls: read the master display arg (matches getControlState).
				if control.get('wheel') and control.get('displayArgs'):
					arg = control['displayArgs'][0]
				else:
					arg = control['arg']
				if arg is None or arg == -1:
					continue
				argEntries.append((controlRef, control, int(arg)))

		results = []

		# --- One BULKQ for every arg-style ref. ---
		if argEntries:
			# Multiple refs may share the same arg; bulkQueryArgs returns one
			# value per unique arg, and we fan it back out below.
			uniqueArgs = list({arg for _, _, arg in argEntries})
			values = self.bulkQueryArgs(uniqueArgs, timeout=2.0)
			if values is not None:
				for controlRef, control, arg in argEntries:
					rawNative = values.get(arg)
					if rawNative is None:
						continue
					description = control.get('description', controlRef.split('/', 1)[-1])
					translated = self._reverseTranslateValue(control, rawNative)
					results.append((controlRef, description, translated, rawNative))

		# --- Indication / text refs (still per-ref). ---
		for controlRef, control in indicationRefs:
			description = control.get('description', controlRef.split('/', 1)[-1])
			indicationId = control['indicationId']
			indication = self.queryIndication(indicationId, timeout=0.5)
			if 'fieldName' in control:
				fieldName = control['fieldName']
				if indication and fieldName in indication:
					results.append((controlRef, description, indication[fieldName]))
				else:
					results.append((controlRef, description, ''))
			else:
				if indication:
					value = '\n'.join(v for v in indication.values() if v)
					results.append((controlRef, description, value))
				else:
					results.append((controlRef, description, ''))

		# --- Metadata module-name ref. ---
		for controlRef in metadataRefs:
			moduleName = self.queryModuleName(timeout=0.5)
			if moduleName:
				results.append((controlRef, 'Aircraft Name', moduleName))

		# --- Telemetry refs: one G: query per LoGet* function. ---
		for functionName, entries in telemetryRefs.items():
			data = self.queryTelemetry(functionName, timeout=0.5)
			for controlRef, path in entries:
				description = telemetryControl(controlRef.split('/', 1)[1])['description']
				results.append((controlRef, description, telemetryValueAt(data, path)))

		return results

	def controlExists(self, controlName):
		"""Check if a control exists in the loaded mappings.

		Args:
			controlName: Full control reference (e.g. 'FA-18C_hornet/canopyPos')
				or bare name (e.g. 'canopyPos').

		Returns:
			bool
		"""
		if controlName.startswith(f'{TELEMETRY_MODULE}/'):
			return parseTelemetryRef(controlName) is not None

		# Check controlIndex directly (O(1)).
		if controlName in self.controlIndex:
			return True

		# Also check by bare name across all modules.
		if '/' in controlName:
			_, bareName = controlName.split('/', 1)
		else:
			bareName = controlName

		for moduleName, mapping in self.controlMappings.items():
			if bareName in mapping.get('controls', {}):
				return True

		return False

	# ---- Indication Parsing ----

	@staticmethod
	def _parseIndication(rawText):
		"""Parse a DCS list_indication() result into a key-value dict.

		The raw format from list_indication() is a string with entries separated
		by lines of dashes, with alternating key and value lines:
			-----------------------------------------
			txt_RPM_L
			 63
			-----------------------------------------
			txt_RPM_R
			 64

		Our Lua export script JSON-encodes this string, so we first JSON-decode it,
		then parse the key-value pairs.

		Args:
			rawText: The JSON-encoded raw indication string from the Lua export.

		Returns:
			Dict of {fieldName: value}.
		"""
		# JSON-decode the string first (it comes wrapped in quotes with escaped chars).
		try:
			text = json.loads(rawText)
		except (json.JSONDecodeError, TypeError):
			text = rawText

		if not isinstance(text, str):
			# If it's already a dict (shouldn't happen but handle gracefully).
			if isinstance(text, dict):
				return text
			return {}

		result = {}
		lines = text.split('\n')
		i = 0
		while i < len(lines):
			line = lines[i].strip()
			# Skip separator lines.
			if line.startswith('-') and len(line) > 3:
				i += 1
				continue
			# Skip empty lines.
			if not line:
				i += 1
				continue
			# Skip DCS indicator hierarchy markers (e.g. "children are {", "}").
			if line == '}' or line.startswith('children are {'):
				i += 1
				continue
			# This should be a key. The next non-separator, non-empty line is its value.
			key = line
			i += 1
			# Find the value.
			while i < len(lines):
				valueLine = lines[i].strip()
				if valueLine.startswith('-') and len(valueLine) > 3:
					i += 1
					continue
				if not valueLine:
					# Empty value.
					result[key] = ''
					break
				result[key] = valueLine
				i += 1
				break
			else:
				# End of lines — key with no value.
				result[key] = ''

		return result
