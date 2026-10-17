import inspect
import math
from pprint import pprint
import time

import pydirectinput

import pygetwindow as gw
from PySide6 import QtWidgets

from engine.cockpitLookahead import isIndicationControl, mayStillNeedCockpit, mayStillUseCommsMenu, rowNeedsCockpit
from engine.simCommands import resolveSimCommand, rowUsesCommsMenu, simCommandProblem
from network.DCSDirectManager import TELEMETRY_MODULE, parseTelemetryRef

def lastRowAfterLoops(rows, loopMarkers):
	"""The last of rows, moved to the end of any loop around it (the loop can run it again); None if rows is empty."""
	lastRow = max(rows) if rows else None
	changed = lastRow is not None
	while changed:
		changed = False
		for startRow, endRow in loopMarkers.items():
			if startRow <= lastRow < endRow:
				lastRow = endRow
				changed = True
	return lastRow

def formatClock(seconds):
	"""Seconds since midnight (any day) as HH:MM:SS, rounded to the nearest second."""
	seconds = round(seconds) % 86400
	return f'{seconds // 3600:02d}:{seconds // 60 % 60:02d}:{seconds % 60:02d}'

def formatDuration(seconds):
	"""225 -> '3m45s', rounded to the nearest second."""
	hours, remainder = divmod(round(seconds), 3600)
	minutes, seconds = divmod(remainder, 60)
	if hours:
		return f'{hours}h{minutes:02d}m{seconds:02d}s'
	if minutes:
		return f'{minutes}m{seconds:02d}s'
	return f'{seconds}s'

def newScriptTimer(duration, gameTime, wallTime):
	"""A script timer started now; gameTime is the mission time (LoGetModelTime), or None if DCS didn't answer."""
	return {'duration': duration, 'startTime': wallTime, 'gameStart': gameTime, 'lastGameElapsed': 0.0, 'lastWallTime': wallTime}

def scriptTimerElapsed(timer, gameTime, wallTime):
	"""Seconds a script timer has run, in mission time when DCS answers (so time acceleration and DCS pauses count), else carrying on from the last answer with the PC clock."""
	if timer['gameStart'] is None:
		return wallTime - timer['startTime']
	if gameTime is not None:
		timer['lastGameElapsed'] = gameTime - timer['gameStart']
		timer['lastWallTime'] = wallTime
		return timer['lastGameElapsed']
	return timer['lastGameElapsed'] + wallTime - timer['lastWallTime']

def telemetryFunctionsWaitedOn(seq):
	"""The LoGet* functions that seq's waits and loops read, in first-use order.  Malformed telemetry refs are left to validateSequence."""
	names = []
	for command in seq:
		if command.get('cmd') in ('scriptCockpitState', 'scriptLoopUntilStart', 'scriptLoopUntilEnd'):
			ref = parseTelemetryRef(command.get('control'))
			if ref and ref[0] not in names:
				names.append(ref[0])
	return names

class DCSSeqExecute:
	def __init__(self, root, config, dbe, scriptData, vars, updateOutput, stopFlag, logFunc, ttsManager, uiLogFunc = None, resumeEvent = None, pauseCallback = None, skipWaitEvent = None, waitStateCallback = None):
		self.root = root # The UI root object.  Needed to force updates during long loops to prevent Windows from thinking the app is frozen.
		self.config = config
		self.dbe = dbe
		self.scriptData = scriptData
		self.vars = vars
		self.updateOutput = updateOutput # Callback function to send output to.
		self.stopFlag = stopFlag
		self.log = logFunc
		self.ttsManager = ttsManager
		self.uiLog = uiLogFunc
		self.uiLogBuffer = ''
		self.resumeEvent = resumeEvent
		self.pauseCallback = pauseCallback
		self.skipWaitEvent = skipWaitEvent # Set by the UI's Skip Wait button.
		self.waitStateCallback = waitStateCallback # Told True/False as a skippable wait starts/ends, so the UI can enable Skip Wait.
		self.waiting = False
		self.loopStack = [] # The running batch's active loops; a loop counts as a wait for Skip Wait.
		self.telemetryChecked = set() # LoGet* functions already checked for an answer from DCS.
		self.simCommandsChecked = False
		self.simCommandsBlocked = False # The server ignores LoSetCommand, so the player does each sim command step by hand.
		self.heldSimCommands = set() # Sim commands this script holds that may still be running, released when it ends.
		self.noDescriptionFlag = False # If True, it means we found a command with no description, which means it wasn't found in the control mapping and therefore was never executed.  That indicates a problem with the script that should be fixed.

	def sendToOverlay(self, text, flush = False):
		if not self.uiLog:
			return
		text = str(text or '')
		if text == '':
			if flush and self.uiLogBuffer != '':
				try:
					self.uiLog(self.uiLogBuffer)
				except Exception:
					pass
				self.uiLogBuffer = ''
			return
		text = text.replace('\r\n', '\n').replace('\r', '\n')
		self.uiLogBuffer += text
		while '\n' in self.uiLogBuffer:
			line, rest = self.uiLogBuffer.split('\n', 1)
			self.uiLogBuffer = rest
			line = str(line or '')
			if line != '':
				try:
					self.uiLog(line)
				except Exception:
					pass
		if flush and self.uiLogBuffer != '':
			try:
				self.uiLog(self.uiLogBuffer)
			except Exception:
				pass
			self.uiLogBuffer = ''

	def getDcsInputSocket(self):
		# Legacy method — no longer needed since commands go through dbe.sendControl().
		# Kept for backward compatibility in case any external code references it.
		return None

	def getDcsWindow(self):
		dcsWindow = None
		# If we're in debug mode, just return None since we won't be sending any commands to DCS.
		if self.config['debug']:
			return dcsWindow

		# If the selected method to find the DCS window is by title, try to find it.
		if self.config['dcsWindowUseTitle']:
			if self.config['dcsWindowTitleOverride']:
				dcsWindowTitle = self.config['dcsWindowTitleOverride']
			else:
				dcsWindowTitle = 'Digital Combat Simulator'
			self.updateOutput(f'Trying to find DCS window by title: "{dcsWindowTitle}"...\n', flush=True)
			matches = gw.getWindowsWithTitle(dcsWindowTitle)
			self.log(f'Found {len(matches)} windows with title "{dcsWindowTitle}"')
			if matches:
				dcsWindow = matches[0]
				self.updateOutput('Found DCS window by title\n', flush=True)

			if not dcsWindow:
				self.updateOutput('Could not find DCS window.  Please ensure DCS is running, and/or set correct title in Tools -> Settings.\n', flush=True)

			return dcsWindow

		# Else try to find the DCS window by exe path.
		else:
			dcsExePath = None
			if self.config['dcsExePathOverride']:
				self.log(f'Using DCS exe path override: {self.config["dcsExePathOverride"]}')
				dcsExePath = self.config['dcsExePathOverride']
				self.updateOutput(f'Trying to find DCS window by exe path: {dcsExePath}...\n', flush=True)
			else:
				self.log('Using default DCS exe path')
				self.updateOutput(f'Trying to find DCS window by exe path: *\\bin\\DCS.exe or *\\bin-mt\\DCS.exe...\n', flush=True)

			try:
				import ctypes
				from ctypes import wintypes

				import psutil
				import win32api
				import win32con
				import win32security

				def isProcessAdmin(processId):
					try:
						hProcess = win32api.OpenProcess(win32con.PROCESS_QUERY_INFORMATION, False, processId)
						hToken = win32security.OpenProcessToken(hProcess, win32con.TOKEN_QUERY)
						elevation = win32security.GetTokenInformation(hToken, win32security.TokenElevation)
						# elevation is an int; 1 means elevated, 0 means not elevated
						if elevation == 1:
							return 'elevated'
						else:
							return 'nonelevated'
					except Exception as e:
						self.log('Error checking token elevation:', e)
						return 'unknown' # If we can't determine the elevation, return unknown.  We'll assume it's elevated though.

				def getProcessIdFromHwnd(hWnd):
					processID = wintypes.DWORD()
					ctypes.windll.user32.GetWindowThreadProcessId(hWnd, ctypes.byref(processID))
					return processID.value

				def getProcessPath(processId):
					hProcess = ctypes.windll.kernel32.OpenProcess(0x1000, False, processId)
					if hProcess:
						try:
							buf = ctypes.create_unicode_buffer(512)
							size = wintypes.DWORD(512)
							if ctypes.windll.psapi.GetModuleFileNameExW(hProcess, None, buf, size):
								return buf.value
						finally:
							ctypes.windll.kernel32.CloseHandle(hProcess)
					return None

				# Check each window's process path to see if it matches the DCS exe path.
				windows = gw.getAllWindows()
				for window in windows:
					if window._hWnd:
						pid = getProcessIdFromHwnd(window._hWnd)
						procPath = getProcessPath(pid)
						#self.log(f'Window: {window.title}, PID: {pid}, Path: {procPath}')
						if dcsExePath and procPath and procPath.lower() == dcsExePath.lower():
							dcsWindow = window
							self.updateOutput(f'Found DCS window by exe path: {dcsExePath}\n', flush=True)
							break
						elif procPath and procPath.lower().endswith(r'\bin\dcs.exe'):
							dcsWindow = window
							self.updateOutput(f'Found DCS window by exe path: *\\bin\\DCS.exe\n', flush=True)
							break
						elif procPath and procPath.lower().endswith(r'\bin-mt\dcs.exe'):
							dcsWindow = window
							self.updateOutput(f'Found DCS window by exe path: *\\bin-mt\\DCS.exe\n', flush=True)
							break

				# If we found the window, check to see if DCS is running as admin, and if DCSAutoMate is not, show a warning.
				if dcsWindow:
					self.log(f'Found DCS window with Process Path: {procPath}')
					dcsIsAdmin = isProcessAdmin(pid)
					self.log(f'DCS UAC elevation: {dcsIsAdmin}')
					dcsAutoMateIsAdmin = 'elevated' if ctypes.windll.shell32.IsUserAnAdmin() else 'nonelevated'
					self.log(f'DCSAutoMate UAC elevation: {dcsAutoMateIsAdmin}')
					# If DCS is running as admin (or unknown) and DCSAutoMate is not, show a warning.  If DCS is admin but DCSAutoMate is not, DCSAutoMate may not be able to send keystrokes to the DCS window with DirectInput.
					if dcsAutoMateIsAdmin == 'nonelevated' and dcsIsAdmin in ['elevated', 'unknown']:
						self.updateOutput('Warning: DCSAutoMate is not running as Administrator, but DCS is (or can\'t detect).  If keyboard input is not sent to DCS, try running DCSAutoMate as Administrator.', flush=True)
						self.ttsManager.speak('Warning: DCSAutoMate is not running as Administrator, but DCS is (or can\'t detect).  If keyboard input is not sent to DCS, try running DCSAutoMate as Administrator.', asyncFlag=False) # Since a mismatch may prevent keyboard input, make sure this message is heard immediately.

				# If we didn't find the window, show an error.
				else:
					self.updateOutput('Could not find DCS window. Please ensure DCS is running.\n', flush=True)
					return dcsWindow

			except Exception as e:
				self.updateOutput(f'Error finding DCS window: {e}\n', flush=True)

			return dcsWindow

	def getSecToMin(self, numSeconds):
		mins = int(math.floor(numSeconds / 60))
		secs = int(numSeconds - (mins * 60))
		return f'{mins}m{secs:02}s'

	def getDescriptions(self, moduleName):
		return self.dbe.getDescriptions(moduleName)

	def validateSequence(self, seq, descriptions, announceSuccess=True):
		errors = []
		pseudoCommands = {
			'scriptKeyboard',
			'scriptSpeech',
			'scriptPause',
			'scriptText',
			'scriptTimerStart',
			'scriptTimerEnd',
			'scriptLoopUntilStart',
			'scriptLoopUntilEnd',
			'scriptCockpitDone',
			'scriptSimCommand',
		}
		for command in seq:
			cmd = command.get('cmd', '')
			if cmd in ('scriptCockpitState', 'scriptLoopUntilStart', 'scriptLoopUntilEnd'):
				control = command.get('control')
				if control and control.startswith(f'{TELEMETRY_MODULE}/'):
					if parseTelemetryRef(control) is None:
						errors.append(f"Control '{control}' not found: telemetry controls are telemetry/LoGet<Function>[.path].")
				elif control:
					controlName = control.split('/')[1] if '/' in control else control
					description = descriptions.get(controlName, {}).get('description', controlName)
					if description == controlName:
						errors.append(f"Control '{control}' not found in control descriptions.")
			elif cmd == 'scriptSimCommand':
				problem = simCommandProblem(command)
				if problem:
					errors.append(problem)
			elif cmd and cmd not in pseudoCommands:
				# Assuming these are DCS commands.
				controlName = cmd.split('/')[1] if '/' in cmd else cmd
				description = descriptions.get(controlName, {}).get('description', controlName)
				if description == controlName:
					errors.append(f"DCS command '{cmd}' not found in descriptions.")

		# Validate scriptLoopUntilStart / scriptLoopUntilEnd marker pairing.
		loopStack = []
		for rowNum, command in enumerate(seq):
			cmd = command.get('cmd', '')
			if cmd == 'scriptLoopUntilStart':
				loopStack.append(rowNum)
			elif cmd == 'scriptLoopUntilEnd':
				if not loopStack:
					errors.append(f'scriptLoopUntilEnd at row {rowNum} has no matching scriptLoopUntilStart.')
				else:
					loopStack.pop()
		for rowNum in loopStack:
			errors.append(f'scriptLoopUntilStart at row {rowNum} has no matching scriptLoopUntilEnd.')

		cockpitDoneRow = None
		for rowNum, command in enumerate(seq):
			if command.get('cmd') == 'scriptCockpitDone' and cockpitDoneRow is None:
				cockpitDoneRow = rowNum
			elif cockpitDoneRow is not None and rowNeedsCockpit(command):
				errors.append(f"{command.get('cmd')} at row {rowNum} needs the cockpit but comes after scriptCockpitDone at row {cockpitDoneRow}.")

		if errors:
			self.updateOutput('Warning: Found commands with no description, please check script for errors.\n', flush=True)
			self.sendToOverlay('Warning: Found commands with no description, please check script for errors.', flush=True)
			for error in errors:
				self.updateOutput(error + '\n', flush=True)
			self.ttsManager.speak('Warning: Found commands with no description, please check script for errors.', asyncFlag=False)
			return False
		elif announceSuccess:
			self.updateOutput('Script validated\n', flush=True)
			self.sendToOverlay('Script validated', flush=True)
		return True

	######
	# Seq must be a List of Dictionaries.  Each Dictionary must have {time, cmd, ...}, other keys are needed based on the command, see code.
	######
	def execute(self, script, helper=None):
		"""Run a script: either a list of commands, or a live script's generator, which is resumed after each batch of queued commands has run."""
		live = inspect.isgenerator(script)
		self.moduleName = self.scriptData.get('moduleName', None)
		self.descriptions = self.getDescriptions(self.moduleName)

		# Validate the sequence before executing it.  If any controls don't have a matching description from the control mapping, it means they won't be executed, so we should show an error in the output.  However, continue executing the script.
		if not live:
			self.validateSequence(script, self.descriptions)

		if self.config['debug']:
			self.updateOutput('RUNNING IN DEBUG MODE, nothing will be sent to the game, all conditions will be met when time is elapsed\n', flush=True)
			self.sendToOverlay('RUNNING IN DEBUG MODE, nothing will be sent to the game, all conditions will be met when time is elapsed\n', flush=True)

		self.dcsWindow = self.getDcsWindow()
		if not self.config['debug'] and not self.dcsWindow:
			if live:
				script.close()
			return

		self.updateOutput(f"Beginning script execution.\n", flush=True)
		self.sendToOverlay('Begin', flush=True)

		self.executedScriptKeyboardCommands = 0
		self.cockpitWarningGiven = False
		self.cockpitAllClear = False
		self.commsMenuWarningGiven = False
		self.commsMenuAllClear = False
		self.executionStartTime = time.time() # Unlike startTime, not shifted by pauses, so the total time is how long the script really took.
		self.startTime = time.time() # Start the timer immediately before starting the execution loop.
		self.timers = {} # A dictionary to track the currently running timers.

		if live:
			helper.setControlReader(self.readControl)
			try:
				finished = False
				while not finished and not self.stopFlag.is_set():
					try:
						next(script)
					except StopIteration:
						finished = True
					batch = helper.takeQueued()
					if batch:
						self.validateSequence(batch, self.descriptions, announceSuccess=False)
					moreCockpitAfter = not finished and self.scriptMayStillReach(mayStillNeedCockpit, script)
					moreCommsMenuAfter = not finished and self.scriptMayStillReach(mayStillUseCommsMenu, script)
					if not self.runBatch(batch, live=True, moreCockpitAfter=moreCockpitAfter, moreCommsMenuAfter=moreCommsMenuAfter):
						return
			finally:
				script.close()
				self.releaseHeldSimCommands()
		else:
			try:
				if not self.runBatch(script, live=False, moreCockpitAfter=False, moreCommsMenuAfter=False):
					return
			finally:
				self.releaseHeldSimCommands()

		completeMessage = f'Script complete ({formatDuration(time.time() - self.executionStartTime)})'
		self.updateOutput(completeMessage + '\n', flush=True)
		self.sendToOverlay(completeMessage, flush=True)
		self.ttsManager.speak('Script complete', asyncFlag=False)

	def releaseHeldSimCommands(self):
		"""End the holds this script may still have running, so a finished, stopped or failed script never leaves a control held."""
		if not self.heldSimCommands:
			return
		for commandId in sorted(self.heldSimCommands):
			self.dbe.releaseSimCommandHold(commandId)
		self.updateOutput(f"Released held simulator commands: {', '.join(str(commandId) for commandId in sorted(self.heldSimCommands))}\n", flush=True)
		self.heldSimCommands.clear()

	def readControl(self, control):
		"""Live read for helper.read(): the control's current value, or None if DCS didn't answer.  Bare names get this script's module prefix."""
		if '/' not in control:
			control = f'{self.moduleName}/{control}'
		if not self.dbe.controlExists(control):
			raise ValueError(f'Control "{control}" does not exist in the control mapping.')
		if isIndicationControl(control) and self.cockpitAllClear:
			self.askPlayerToReturn()
			self.startTime += self.waitWhilePaused()
		return self.readControlState(control)

	def readControlState(self, control):
		"""The control's current value, or None if DCS didn't answer (e.g. a query timeout on a laggy MP server)."""
		results = self.dbe.getControlState(control)
		return results[0][2] if results else None

	def scriptMayStillReach(self, lookahead, script):
		"""Lookahead for a paused live script; any failure counts as 'maybe', which only delays the all-clear."""
		try:
			return lookahead(script)
		except Exception as e:
			self.log(f'{lookahead.__name__} failed, assuming yes: {e}')
			return True

	def announceCockpitAllClear(self):
		if self.cockpitAllClear:
			return
		self.cockpitAllClear = True
		self.executedScriptKeyboardCommands = -1
		self.updateOutput('\nLast keyboard command or cockpit display read done, OK to leave cockpit.', flush=True)
		# Send a blank line to the overlay to move to the next line before sending the all-clear message.
		self.sendToOverlay('', flush=True)
		self.sendToOverlay('OK to leave cockpit.', flush=True)
		self.ttsManager.speak('OK to leave cockpit.')

	def announceCommsMenuAllClear(self):
		if self.commsMenuAllClear:
			return
		self.commsMenuAllClear = True
		self.updateOutput('\nLast comms menu command done, OK to use comms menu.', flush=True)
		self.sendToOverlay('', flush=True)
		self.sendToOverlay('OK to use comms menu.', flush=True)
		self.ttsManager.speak('OK to use comms menu.')

	def askPlayerToReturn(self):
		"""The player was told they could leave, but the cockpit is needed again: ask them back and pause rather than grabbing focus."""
		self.cockpitAllClear = False
		self.updateOutput('The cockpit is needed again: return to the cockpit, then click Resume.\n', flush=True)
		self.sendToOverlay('Cockpit needed: return to the cockpit, then click Resume.', flush=True)
		self.ttsManager.speak('Cockpit needed.  Return to the cockpit, then click Resume.', asyncFlag=False)
		if self.pauseCallback:
			self.pauseCallback()

	def waitWhilePaused(self):
		"""Block (keeping the UI responsive) while the script is paused; returns the seconds spent paused."""
		if not self.resumeEvent or self.resumeEvent.is_set():
			return 0
		pauseStart = time.time()
		while not self.resumeEvent.is_set() and not self.stopFlag.is_set():
			QtWidgets.QApplication.processEvents()
			time.sleep(0.1)
		return time.time() - pauseStart

	def setWaiting(self, waiting):
		"""Tell the UI whether Skip Wait applies.  A click from before the change is dropped, so it can't skip the next wait."""
		if waiting == self.waiting:
			return
		self.waiting = waiting
		if self.skipWaitEvent:
			self.skipWaitEvent.clear()
		if self.waitStateCallback:
			self.waitStateCallback(waiting)

	def takeSkipRequest(self):
		"""True once per Skip Wait click."""
		if self.skipWaitEvent and self.skipWaitEvent.is_set():
			self.skipWaitEvent.clear()
			return True
		return False

	def checkTelemetry(self, seq):
		"""Warn and pause if DCS sends nothing for a LoGet* function that seq waits on (e.g. on a server that blocks ownship export), as that wait would never finish."""
		if self.config['debug']:
			return
		functionNames = [name for name in telemetryFunctionsWaitedOn(seq) if name not in self.telemetryChecked]
		self.telemetryChecked.update(functionNames)
		missing = [name for name in functionNames if self.dbe.queryTelemetry(name) is None]
		if not missing:
			return
		names = ', '.join(missing)
		self.updateOutput(f'Warning: No telemetry from DCS for {names}, which this script waits on, so the wait would never finish.  The server may block aircraft data export.  Script paused: click Stop, or Resume and click Skip Wait when the script gets stuck.\n', flush=True)
		self.sendToOverlay(f'No telemetry from DCS for {names} - the server may block export.  Paused: Stop, or Resume and Skip Wait when stuck.', flush=True)
		self.ttsManager.speak('Warning: no telemetry from DCS.  Script paused.', asyncFlag=False)
		if self.pauseCallback:
			self.pauseCallback()

	def checkSimCommands(self, seq):
		"""Warn and pause if seq has sim commands and the server blocks them.  A server that blocks ownship export also ignores LoSetCommand from clients and strips LoGetSelfData down to who you are, with no position."""
		if self.config['debug'] or self.simCommandsChecked or not any(command.get('cmd') == 'scriptSimCommand' for command in seq):
			return
		self.simCommandsChecked = True
		selfData = self.dbe.queryTelemetry('LoGetSelfData')
		self.simCommandsBlocked = isinstance(selfData, dict) and 'LatLongAlt' not in selfData
		if not self.simCommandsBlocked:
			return
		self.updateOutput('Warning: This server blocks simulator commands, which this script uses (e.g. to move the throttles), so DCS will ignore them.  At each one, the script will tell you what to do and pause: do it yourself, then click Resume.  Script paused: click Resume to continue, or Stop.\n', flush=True)
		self.sendToOverlay('Server blocks simulator commands: at each one, do it yourself, then Resume.  Paused: Resume or Stop.', flush=True)
		self.ttsManager.speak('Warning: this server blocks simulator commands.  Script paused.', asyncFlag=False)
		if self.pauseCallback:
			self.pauseCallback()

	def promptManualStep(self, step):
		"""A sim command step the server ignores: ask the player to do it, and pause until they Resume."""
		self.updateOutput(f'Do it yourself: {step}, then click Resume.\n', flush=True)
		self.sendToOverlay(f'Do it yourself: {step}, then Resume.', flush=True)
		self.ttsManager.speak(f'{step}, then resume.', asyncFlag=False)
		if self.pauseCallback:
			self.pauseCallback()

	def runBatch(self, seq, live, moreCockpitAfter, moreCommsMenuAfter):
		"""Run one list of commands.  moreCockpitAfter / moreCommsMenuAfter say whether later batches might still need the cockpit / use the comms menu.  Returns False if the batch was aborted (mismatched loop markers)."""
		moduleName = self.moduleName
		descriptions = self.descriptions

		rowNum = 0
		cmdStartTime = time.time() # Start the timer for this command.
		timers = self.timers

		# Build map of scriptLoopUntilStart row → scriptLoopUntilEnd row.  Abort on
		# mismatch.  This pre-pass mirrors the validateSequence check but is needed
		# again here because execute() must be able to jump between paired rows.
		loopMarkers = {} # {startRow: endRow}
		pairStack = []
		for r, c in enumerate(seq):
			if c.get('cmd') == 'scriptLoopUntilStart':
				pairStack.append(r)
			elif c.get('cmd') == 'scriptLoopUntilEnd':
				if not pairStack:
					self.updateOutput(f'Error: scriptLoopUntilEnd at row {r} has no matching scriptLoopUntilStart.  Aborting.\n', flush=True)
					return False
				startR = pairStack.pop()
				loopMarkers[startR] = r
		if pairStack:
			self.updateOutput(f'Error: scriptLoopUntilStart with no matching End at rows {pairStack}.  Aborting.\n', flush=True)
			return False
		loopStack = [] # Stack of active loop frames.
		self.loopStack = loopStack

		# The all-clear comes once execution is past the last row that needs the cockpit, or past the end of any loop around it (the loop can run it again).
		cockpitRows = [r for r, c in enumerate(seq) if rowNeedsCockpit(c)]
		allClearRow = lastRowAfterLoops(cockpitRows, loopMarkers)
		commsMenuRows = [r for r, c in enumerate(seq) if rowUsesCommsMenu(c)]
		commsMenuAllClearRow = lastRowAfterLoops(commsMenuRows, loopMarkers)
		warnCockpit = bool(cockpitRows) and not self.cockpitWarningGiven
		warnCommsMenu = bool(commsMenuRows) and not self.commsMenuWarningGiven
		if warnCockpit:
			self.cockpitWarningGiven = True
			if live:
				self.updateOutput('This script sends keyboard commands or reads cockpit displays.  Stay in cockpit until told it\'s OK to leave.\n', flush=True)
			else:
				self.updateOutput(f'Found {len(cockpitRows)} keyboard commands or cockpit display reads in script.  Stay in cockpit until told it\'s OK to leave.\n', flush=True)
		if warnCommsMenu:
			self.commsMenuWarningGiven = True
			self.updateOutput("This script uses the comms menu.  Don't use comms menu until told it's OK.\n", flush=True)
		if warnCockpit or warnCommsMenu:
			if warnCockpit and warnCommsMenu:
				warning = "Stay in cockpit and don't use comms menu until told it's OK."
			elif warnCockpit:
				warning = "Stay in cockpit until told it's OK to leave."
			else:
				warning = "Don't use comms menu until told it's OK."
			self.sendToOverlay(warning, flush=True)
			self.ttsManager.speak(warning, asyncFlag=False) # We want to make sure this message is read before any other speech in the script gets played.
		if not cockpitRows and not moreCockpitAfter and self.cockpitWarningGiven:
			self.announceCockpitAllClear()
		if not commsMenuRows and not moreCommsMenuAfter and self.commsMenuWarningGiven:
			self.announceCommsMenuAllClear()
		self.checkTelemetry(seq)
		self.checkSimCommands(seq)

		while not self.stopFlag.is_set():
			# Check if paused
			pauseDuration = self.waitWhilePaused()
			self.startTime += pauseDuration
			cmdStartTime += pauseDuration

			if allClearRow is not None and rowNum > allClearRow and not moreCockpitAfter:
				self.announceCockpitAllClear()
			if commsMenuAllClearRow is not None and rowNum > commsMenuAllClearRow and not moreCommsMenuAfter:
				self.announceCommsMenuAllClear()

			# When our counter gets past the last row, break out of the loop.
			if rowNum >= len(seq):
				break

			currentTime = time.time()
			elapsedTime = currentTime - self.startTime
			cmdElapsedTime = currentTime - cmdStartTime

			# Get the current command.
			command = seq[rowNum]
			# If the time since we started is greater than the command we're executing, run that command and go on to the next one.
			if cmdElapsedTime > command['time']:
				cmd = command['cmd']
				msg = command.get('msg', '')
				manualStep = None # A sim command step the player has to do, as the server ignores it.
				displayTime = round(elapsedTime, 1)
				displayCmdTime = round(command['time'], 1)
				self.updateOutput(f'Time: {displayTime}, Cmd: {displayCmdTime}\t\t', flush=True)
				self.sendToOverlay(f"T:{displayTime} ")

				if self.cockpitAllClear and rowNeedsCockpit(command):
					self.askPlayerToReturn()
					continue

				if cmd == 'scriptKeyboard':
					self.handleScriptKeyboard(command)
				elif cmd == 'scriptCockpitDone':
					if self.cockpitWarningGiven:
						self.announceCockpitAllClear()
				elif cmd == 'scriptSimCommand':
					arg = command['arg']
					commandId = resolveSimCommand(arg)
					value = command.get('value')
					hold = command.get('hold')
					stop = command.get('stop')
					release = command.get('release')
					label = f'{arg} ({commandId})' if isinstance(arg, str) else f'{arg}'
					if value is not None:
						label += f' {value}'
					if release:
						label += ' released'
					elif hold is True:
						label += ' held until released'
					elif hold is not None:
						label += f' held {hold}s'
					if stop is not None:
						label += f', then {stop}'
					self.updateOutput(f'Sim command:\t{label}', flush=True)
					self.sendToOverlay(f'Sim cmd: {label}')
					problem = simCommandProblem(command)
					if problem:
						self.updateOutput(f' - not sent: {problem}', flush=True)
					elif not self.config['debug']:
						if release:
							self.dbe.releaseSimCommandHold(commandId)
							self.heldSimCommands.discard(commandId)
						elif hold is not None:
							seconds = None if hold is True else hold
							stopId = resolveSimCommand(stop) if stop is not None else None
							if value is None:
								self.dbe.sendSimCommandHold(commandId, seconds, stopId)
							else:
								self.dbe.sendSimCommandHold(commandId, seconds, stopId, value=value)
							self.heldSimCommands.add(commandId)
						else:
							self.dbe.sendSimCommand(commandId, value)
						if self.simCommandsBlocked and not release:
							manualStep = msg or str(arg)
				elif cmd == 'scriptSpeech':
					arg = command['arg']
					msg = command['msg']
					asyncFlag = command.get('asyncFlag', True)
					self.updateOutput(f'Speaking:\t"{arg}"', flush=True)
					self.sendToOverlay(f"Speak: {arg}")
					self.ttsManager.speak(arg, asyncFlag=asyncFlag)
				elif cmd == 'scriptPause':
					if self.pauseCallback:
						self.pauseCallback()
				elif cmd == 'scriptText':
					arg = command.get('arg', '')
					self.updateOutput(f'{arg}\n', flush=True)
					self.sendToOverlay(arg)
				elif cmd == 'scriptCockpitState':
					self.handleScriptCockpitState(command, descriptions)
				elif cmd == 'scriptTimerStart' or cmd == 'scriptTimerEnd':
					self.handleScriptTimer(command, timers)
				elif cmd == 'scriptLoopUntilStart':
					action = self.handleScriptLoopUntilStart(command, descriptions, rowNum, loopMarkers, loopStack)
					# action is either None (continue into body) or an int row number to jump to.
					if action is not None:
						# Skip the normal "rowNum += 1" advance below by overwriting rowNum
						# with our target and continuing.
						self.updateOutput('\n', flush=True)
						self.sendToOverlay('\n', flush=True)
						rowNum = action
						cmdStartTime = time.time()
						QtWidgets.QApplication.processEvents()
						time.sleep(0.01)
						continue
				elif cmd == 'scriptLoopUntilEnd':
					action = self.handleScriptLoopUntilEnd(command, descriptions, rowNum, loopStack)
					if action is not None:
						self.updateOutput('\n', flush=True)
						self.sendToOverlay('\n', flush=True)
						rowNum = action
						cmdStartTime = time.time()
						QtWidgets.QApplication.processEvents()
						time.sleep(0.01)
						continue
				elif cmd != '':
					arg = command['arg']
					msg = command['msg']
					control_name = cmd.split('/')[1] if '/' in cmd else cmd
					description = descriptions.get(control_name, {}).get('description', cmd)
					self.updateOutput(f'DCS command:\t{description} ({cmd}) {arg}', flush=True)
					self.sendToOverlay(f"Cmd: {description} {arg}")
					if not self.config['debug']:
						self.dbe.sendControl(cmd, arg, moduleName)

				if msg != '':
					if cmd:
						self.updateOutput(f' - {msg}', flush=True)
					else:
						self.updateOutput(f'Message:\t{msg}', flush=True)

				self.updateOutput('\n', flush=True)
				self.sendToOverlay('\n', flush=True)
				if manualStep:
					self.promptManualStep(manualStep)

				# Go on to the next command.
				rowNum += 1
				cmdStartTime = time.time() # Reset the timer for the next command.

			QtWidgets.QApplication.processEvents()
			time.sleep(0.01)  # Sleep for a short time to save CPU cycles.

		return True

	def handleScriptKeyboard(self, command):
		#print('in handleScriptKeyboard', command)
		keyString = command['arg']
		keySplit = keyString.lower().split(' ') # Split the key string into key and action.
		key = keySplit[0]
		action = keySplit[1] if len(keySplit) > 1 else 'press' # If no action, default to 'press'.

		# Map of alternate key names for pydirectinput, so users can use familiar key names from DCS controls.
		keyMap = {
			'altleft': [
				'lalt',
				'leftalt',
			],
			'altright': [
				'ralt',
				'rightalt',
			],
			'ctrlleft': [
				'lctrl',
				'leftctrl',
			],
			'ctrlright': [
				'rctrl',
				'rightctrl',
			],
			'shiftleft': [
				'lshift',
				'leftshift',
			],
			'shiftright': [
				'rshift',
				'rightshift',
			],
			'winleft': [
				'lwin',
				'leftwin',
			],
			'winright': [
				'rwin',
				'rightwin',
			],
			'pagedown': [
				'pgdn',
			],
			'pageup': [
				'pgup',
			],
			'add': {
				'numadd',
				'num+',
			},
			'subtract': {
				'numsubtract',
				'num-',
			},
			'multiply': {
				'nummultiply',
				'num*',
			},
			'divide': {
				'numdivide',
				'num/',
			},
			'decimal': {
				'numdecimal',
				'num.',
			},
		}

		# Check if the key is in any of the keyMap lists.
		if len(key) > 1 and key not in keyMap:
			for mapKey, aliases in keyMap.items():
				if key in aliases:
					key = mapKey
					break

		#print('in handleScriptKeyboard', key, action)
		self.updateOutput(f'Keyboard command:\t{keyString}', flush=True)
		self.sendToOverlay(f"Key: {command['arg']}")

		# Add the numpad keys to the pydirectinput.KEYBOARD_MAPPING dictionary.  These are supported by pyautogui, but pyautogui.press() doesn't work in DCS.  They are commented out in pydirectinput, but seem to work fine if we add them back in.
		pydirectinput.KEYBOARD_MAPPING['num0'] = 0x52
		pydirectinput.KEYBOARD_MAPPING['num1'] = 0x4F
		pydirectinput.KEYBOARD_MAPPING['num2'] = 0x50
		pydirectinput.KEYBOARD_MAPPING['num3'] = 0x51
		pydirectinput.KEYBOARD_MAPPING['num4'] = 0x4B
		pydirectinput.KEYBOARD_MAPPING['num5'] = 0x4C
		pydirectinput.KEYBOARD_MAPPING['num6'] = 0x4D
		pydirectinput.KEYBOARD_MAPPING['num7'] = 0x47
		pydirectinput.KEYBOARD_MAPPING['num8'] = 0x48
		pydirectinput.KEYBOARD_MAPPING['num9'] = 0x49
		pydirectinput.KEYBOARD_MAPPING['numenter'] = 0x9C + 1024

		if not self.config['debug']:
			try:
				# If the DCS window isn't active, activate it (focus and bring to top).
				if not self.dcsWindow.isActive:
					self.dcsWindow.activate() # .focus() doesn't work, but .activate() does.  Then you need to wait a short time.
					time.sleep(0.06) # See pywinauto timings.py after_setfocus_wait, default is 0.06 seconds, and that seems to work here.

				#self.log(f'Sending key: {key}, action: {action}')
				if action == 'keydown' or action == 'down':
					sentKey = pydirectinput.keyDown(key)
				elif action == 'keyup' or action == 'up':
					sentKey = pydirectinput.keyUp(key)
				elif action == 'press':
					sentKey = pydirectinput.press(key)
				#self.log(f'sentKey: {sentKey}')

				if not sentKey:
					self.updateOutput(f"\nUnknown error sending key command to DCS.\nYou'll probably need to restart the script.\n", flush=True)
					self.stopFlag.set()
			except Exception as e:
				self.updateOutput(f"\nError sending key command to DCS: {e}\nYou'll probably need to restart the script.\n", flush=True)
				self.stopFlag.set()

		self.executedScriptKeyboardCommands += 1

	def _evaluateCondition(self, controlState, condition, value, valueType, resolution=5):
		"""Evaluate a single (controlState, condition, value) comparison.

		Returns True if the condition is met, False otherwise.  Returns None if the
		controlState cannot be coerced to the expected type (e.g. empty string from
		an unpowered display when expecting a number) — caller should treat None as
		"not yet readable, try again later".  Raises ValueError for an invalid
		condition operator.

		Args:
			resolution: Number of decimal places to round the DCS-returned value to
				before comparing.  Absorbs the 32-bit float precision artifact from
				DCS's Lua engine (e.g. a fully-open canopy returns 0.89999997... rather
				than exactly 0.9).  Defaults to 5 (~1×10⁻⁵), comparable to DCS BIOS's
				16-bit integer resolution (~1.53×10⁻⁵).  Only applied to numeric
				comparisons; string comparisons are unaffected.
		"""
		# Cast the controlState to the correct type based on the value type.
		# Use float() to handle numeric strings from display text (e.g. "63" or "63.5").
		# Don't truncate to int — Python compares int and float correctly (e.g. 63 >= 62.8),
		# and truncation would break continuous values like canopy position (0.98 → 0).
		# Round to `resolution` decimal places to absorb the 32-bit float precision artifact
		# from DCS's Lua engine (e.g. a fully-open canopy arg returns 0.89999997615814, not 0.9).
		# Only the DCS-returned value is rounded; the script-specified `value` is left exact.
		# If the value can't be converted (e.g. empty string from an unpowered display),
		# or DCS didn't answer at all (None), return None — the condition can't be
		# evaluated without a readable value.
		if controlState is None:
			return None
		if valueType == 'num':
			try:
				controlState = round(float(controlState), resolution)
			except (ValueError, TypeError):
				return None
			if condition == '=':
				return controlState == value
			elif condition == '<':
				return controlState < value
			elif condition == '<=':
				return controlState <= value
			elif condition == '>':
				return controlState > value
			elif condition == '>=':
				return controlState >= value
			else:
				raise ValueError(f'Invalid condition: {condition} not supported for numeric values')
		else:
			controlState = str(controlState)
			if condition == '=':
				return controlState == value
			elif condition == 'startsWith':
				return controlState.startswith(value)
			elif condition == 'endsWith':
				return controlState.endswith(value)
			elif condition == 'contains':
				return value in controlState
			else:
				raise ValueError(f'Invalid condition: {condition} not supported for str values')

	def _resolveValueType(self, value):
		"""Return 'num' if value is int/float, 'str' if str, else raise TypeError."""
		if isinstance(value, (int, float)) and not isinstance(value, bool):
			return 'num'
		if isinstance(value, str):
			return 'str'
		raise TypeError('Only int, float, or str are supported for condition values')

	def handleScriptLoopUntilStart(self, command, descriptions, rowNum, loopMarkers, loopStack):
		"""Push a new loop frame.  If the Start marker has a condition and that
		condition is already met (pre-test / "while" semantics), skip the body by
		returning the row number after the matching End.  Otherwise return None
		to fall through into the body.

		Frame fields:
			startRow:        row of the Start marker (body starts at startRow + 1)
			endRow:          row of the End marker
			control:         optional, qualified control name to evaluate at End
			condition:       comparison operator (=, <, <=, >, >=, startsWith, ...)
			value:           value to compare against
			valueType:       'num' or 'str'
			maxIterations:   0 = unlimited (default)
			timeout:         0 = unlimited (default), otherwise seconds
			iterCount:       number of completed iterations
			startTime:       wall-clock time when the loop began
		"""
		endRow = loopMarkers[rowNum]
		control = command.get('control')
		condition = command.get('condition', '=')
		value = command.get('value')
		valueType = self._resolveValueType(value) if value is not None else None
		maxIterations = command.get('maxIterations', 0)
		timeout = command.get('timeout', 0)
		resolution = command.get('resolution', 5)

		if control is not None and not self.dbe.controlExists(control):
			raise ValueError(f'Control "{control}" does not exist in the control mapping.')

		frame = {
			'startRow': rowNum,
			'endRow': endRow,
			'control': control,
			'condition': condition,
			'value': value,
			'valueType': valueType,
			'maxIterations': maxIterations,
			'timeout': timeout,
			'resolution': resolution,
			'iterCount': 0,
			'startTime': time.time(),
		}
		loopStack.append(frame)

		# Display the loop header.
		if control is not None:
			displayCtrl = descriptions.get(control.split('/')[1], {}).get('description', control) if '/' in control else control
			self.updateOutput(f'Loop until:\t{displayCtrl} ({control}) {condition} {value}', flush=True)
			self.sendToOverlay(f'Loop until: {displayCtrl} {condition} {value}')
		else:
			self.updateOutput('Loop start', flush=True)
			self.sendToOverlay('Loop start')

		# Pre-test: if Start has a condition AND it's already met, skip the body.
		if control is not None and not self.config['debug']:
			controlState = self.readControlState(control)
			result = self._evaluateCondition(controlState, condition, value, valueType, resolution=frame['resolution'])
			if result:
				self.updateOutput(' (already met, skipping body)', flush=True)
				self.sendToOverlay(' (skip)')
				loopStack.pop()
				return endRow + 1
		self.setWaiting(True)
		return None

	def handleScriptLoopUntilEnd(self, command, descriptions, rowNum, loopStack):
		"""Decide whether to exit or repeat the current loop.

		Resolution order for the condition: End marker's params take precedence
		over the Start marker's params (allowing post-test / "do-while" usage).
		If neither marker provides a condition, the loop only terminates when a
		budget (maxIterations or timeout) is exhausted.

		Returns the row to jump to, or None to fall through (which is effectively
		"advance to the next row" — the same as exiting the loop normally).
		"""
		if not loopStack:
			# Should be impossible — pre-pass guarantees pairing.
			self.updateOutput('Error: scriptLoopUntilEnd reached with empty loop stack.\n', flush=True)
			return None
		frame = loopStack[-1]

		# Resolve condition: End's params override Start's where given.
		control = command.get('control', frame['control'])
		condition = command.get('condition', frame['condition'])
		value = command.get('value', frame['value'])
		valueType = self._resolveValueType(value) if value is not None else None
		maxIterations = command.get('maxIterations', frame['maxIterations'])
		timeout = command.get('timeout', frame['timeout'])
		resolution = command.get('resolution', frame['resolution'])

		if control is not None and not self.dbe.controlExists(control):
			raise ValueError(f'Control "{control}" does not exist in the control mapping.')

		frame['iterCount'] += 1
		elapsed = time.time() - frame['startTime']

		if self.takeSkipRequest():
			self.updateOutput(f'Loop end: skipped by user after {frame["iterCount"]} iter', flush=True)
			self.sendToOverlay('Loop skipped')
			loopStack.pop()
			self.setWaiting(bool(loopStack))
			return None

		conditionMet = False
		if self.config['debug']:
			# In debug mode, exit the loop after one iteration regardless.
			conditionMet = True
		elif control is not None:
			controlState = self.readControlState(control)
			result = self._evaluateCondition(controlState, condition, value, valueType, resolution=resolution)
			# None (unreadable) is treated as "not met" — try again next iteration.
			conditionMet = bool(result)

		budgetExceeded = False
		if maxIterations and frame['iterCount'] >= maxIterations:
			budgetExceeded = True
			self.updateOutput(f'Loop end: max iterations ({maxIterations}) reached', flush=True)
			self.sendToOverlay(f'Loop max iters {maxIterations}')
		elif timeout and elapsed >= timeout:
			budgetExceeded = True
			self.updateOutput(f'Loop end: timeout ({timeout}s) reached', flush=True)
			self.sendToOverlay(f'Loop timeout {timeout}s')

		if conditionMet or budgetExceeded:
			# Exit the loop.
			if conditionMet and not budgetExceeded and control is not None:
				self.updateOutput(f'Loop end: condition met after {frame["iterCount"]} iter', flush=True)
				self.sendToOverlay(f'Loop done iter {frame["iterCount"]}')
			loopStack.pop()
			self.setWaiting(bool(loopStack))
			return None # Fall through to normal rowNum += 1 advance.

		# Repeat: jump to the row after Start.
		self.updateOutput(f'Loop iter {frame["iterCount"]}, repeating', flush=True)
		self.sendToOverlay(f'Loop iter {frame["iterCount"]}')
		return frame['startRow'] + 1

	def handleScriptCockpitState(self, command, descriptions):
		"""
		This will start looping, watching the current control state.  When the control state meets the command condition and value, start a timer.  If the control state ever fails to meet the condition, reset the timer.  When the control value has been in the command condition for the duration, exit the loop.
		"""
		# Ensure required parameters are provided
		if 'control' not in command or 'value' not in command:
			raise ValueError('Missing required parameters for scriptCockpitState: control and value must be provided')

		control = command['control']
		condition = command.get('condition', '=') # Default to '='
		value = command['value']
		duration = command.get('duration', 0) # Default to 0 seconds (immediate)
		resolution = command.get('resolution', 5)

		# Throw an exception if the control doesn't exist in the control mapping.
		if not self.dbe.controlExists(control):
			raise ValueError(f'Control "{control}" does not exist in the control mapping.  Make sure to use the full control name, including the module name.')

		# Throw an exception if anything but int, float, or str are passed.
		if not isinstance(value, (int, float, str)):
			raise TypeError('Only int, float, or str are supported for scriptCockpitState values')

		valueType = 'str' if isinstance(value, str) else 'num' # NOTE Don't call this variable 'type' or it will override the built-in type function, and calls to type(value) will give unexpected error messages.  Ask me how I know.

		displayDuration = f' for {duration} sec' if duration else ''
		description = descriptions.get(control.split('/')[1], {}).get('description', control)
		self.updateOutput(f'Wait for cockpit state:\t{description} ({control}) {condition} {value}{displayDuration}... ', flush=True)
		self.sendToOverlay(f'Wait: {description} {condition} {value}{displayDuration}... ', flush=True)
		controlState = None
		#self.updateOutput('\n')
		#self.updateOutput(f'scriptCockpitState, control: {control}, condition: {condition}, value: {value}, duration: {duration}')

		stateStartTime = None
		skipped = False
		self.setWaiting(True)
		while not self.stopFlag.is_set():
			if self.takeSkipRequest():
				skipped = True
				break
			stateCurrentTime = time.time()

			conditionMet = False
			if not self.config['debug']:
				controlState = self.readControlState(control)
				result = self._evaluateCondition(controlState, condition, value, valueType, resolution=resolution)
				if result is None:
					# Value not yet readable (e.g. empty display, or DCS didn't answer); try again.
					QtWidgets.QApplication.processEvents() # Keep Skip Wait clickable: a value that never arrives is when it's needed most.
					time.sleep(0.01)
					continue
				conditionMet = result

			if conditionMet or self.config['debug']:
				# If we don't have a timer already running, start one.
				if not stateStartTime:
					stateStartTime = time.time()
				# Check the elapsed time from when we started the timer.
				stateElapsedTime = stateCurrentTime - stateStartTime
				# If the elapsed time is greater than the duration, then the condition has been met for the required amount of time.  Break out of the loop.
				#self.updateOutput('stateElapsedTime', stateElapsedTime)
				if stateElapsedTime >= duration:
					break
			else:
				# Not meeting condition, so delete the timer.
				stateStartTime = None

			QtWidgets.QApplication.processEvents()
			time.sleep(0.01)  # Sleep for a short time to save CPU cycles.

		self.setWaiting(bool(self.loopStack))
		if skipped:
			self.updateOutput('Skipped by user', flush=True)
			self.sendToOverlay('Skipped by user', flush=True)
			return
		self.updateOutput(f'Condition met', flush=True)
		self.sendToOverlay('Condition met', flush=True)

	def readTelemetryNumber(self, functionName):
		"""A LoGet* function's number from DCS, or None in debug mode or if DCS didn't answer."""
		if self.config['debug']:
			return None
		value = self.dbe.queryTelemetry(functionName, timeout=0.5)
		return value if isinstance(value, (int, float)) and not isinstance(value, bool) else None

	def handleScriptTimer(self, command, timers):
		cmd = command['cmd'] # 'scriptTimerStart' or 'scriptTimerEnd'
		name = command['name']
		duration = command.get('duration', None) # 'end' action will not have a duration.

		if cmd == 'scriptTimerStart':
			timer = newScriptTimer(duration, self.readTelemetryNumber('LoGetModelTime'), time.time())
			missionStart = self.readTelemetryNumber('LoGetMissionStartTime') if timer['gameStart'] is not None else None
			# The cockpit clock shows mission time, so say when the timer ends by it.
			timer['endClock'] = missionStart + timer['gameStart'] + duration if missionStart is not None else None
			timers[name] = timer
			ends = f" (ends at {formatClock(timer['endClock'])} in-game)" if timer['endClock'] is not None else ''
			self.updateOutput(f'Start timer:\t{name}, {duration} sec{ends}', flush=True)
			self.sendToOverlay(f'Start timer: {name}, {duration} sec{ends}', flush=True)
		elif cmd == 'scriptTimerEnd':
			timer = timers[name]
			remainingSeconds = timer['duration'] - scriptTimerElapsed(timer, self.readTelemetryNumber('LoGetModelTime'), time.time())
			notes = []
			if timer.get('endClock') is not None:
				notes.append(f"ends at {formatClock(timer['endClock'])} in-game")
			acceleration = self.readTelemetryNumber('LoGetModelTimeAcceleration') if timer['gameStart'] is not None else None
			if acceleration and acceleration > 1 and remainingSeconds > 0:
				notes.append(f'about {self.getSecToMin(round(remainingSeconds / acceleration))} at {acceleration:g}x')
			remainingTime = self.getSecToMin(max(0, round(remainingSeconds))) + (f" ({'; '.join(notes)})" if notes else '')
			self.updateOutput(f'Waiting for timer:\t{name}, {remainingTime} remaining... ', flush=True)
			self.sendToOverlay(f'Waiting for timer: {name}, {remainingTime} remaining... ', flush=True)
			nextGameTimeRead = time.time()
			self.setWaiting(True)
			while not self.stopFlag.is_set():
				if self.takeSkipRequest():
					self.updateOutput('Timer skipped by user', flush=True)
					self.sendToOverlay('Timer skipped by user', flush=True)
					break
				currentTime = time.time()
				gameTime = None
				if timer['gameStart'] is not None and currentTime >= nextGameTimeRead:
					gameTime = self.readTelemetryNumber('LoGetModelTime')
					# Read a few times a second; after a missed answer, wait longer so a dropped connection doesn't keep stalling the UI.
					nextGameTimeRead = time.time() + (0.25 if gameTime is not None else 5)
				if scriptTimerElapsed(timer, gameTime, time.time()) >= timer['duration']:
					self.updateOutput(f'Timer done', flush=True)
					self.sendToOverlay('Timer done', flush=True)
					break

				QtWidgets.QApplication.processEvents()
				time.sleep(0.01)  # Sleep for a short time to save CPU cycles.
			self.setWaiting(bool(self.loopStack))
