import os
import datetime
import inspect
import argparse # Command line parameters.
import sys
import subprocess
import threading
import socket
from PySide6 import QtWidgets, QtCore, QtGui
import traceback
from pprint import pprint

from network.UdpWireLogger import UdpWireLogger

class UiRemoteControlBridge(QtCore.QObject):
	messageReceived = QtCore.Signal(str)


# Import the classes from the renamed files
from network.DCSDirectManager import DCSDirectManager
from network.DCSAutoMateExportManager import DCSAutoMateExportManager
from engine.DCSSeqExecute import DCSSeqExecute
from engine.autoSelectRules import AutoSelectContext, applyModuleAutoSelect, autoSelectReport, classifyPosition, isEngineRunning, timeOfDay
from utils.SettingsManager import SettingsManager, describeResolvedPath, readHookSettings, HOOK_SETTINGS_DEFAULTS
from engine.ScriptManager import ScriptManager
from utils.TTSManager import TTSManager
from engine.SequenceHelper import SequenceHelper
from utils.DcsScriptsInstaller import DcsScriptsInstaller
from utils.controlReference import controlReferencePaths, updateControlReference
from utils.dcsVersion import dcsInstallDir, dcsUpdateNotice, readCheckedDcsVersion, readInstalledDcsVersion
from utils.version import APP_VERSION


###############################################################################
###############################################################################
###############################################################################

class DCSAutoMateApp:
	def __init__(self, parent=None):
		self.uiRemoteControlStopFlag = threading.Event()
		self.uiRemoteControlThread = None

		# Initialize Managers early
		self.settingsManager = SettingsManager()
		self.config = self.settingsManager.config

		self.uiRemoteControlPort = self.config.get('uiRemoteControlPort', 7786)
		self.uiRemoteControlHost = '127.0.0.1'
		self.uiRemoteControlReplyPort = self.config.get('uiRemoteControlReplyPort', 7779)
		self.uiRemoteControlBridge = UiRemoteControlBridge()
		self.uiRemoteControlBridge.messageReceived.connect(self._handleUiRemoteControlMessage)

		self.updatingFromRemote = False # Initialize flag
		self.scriptRunning = False # Flag to track if a script is currently executing
		self.scriptPaused = False # Flag to track if script is paused
		self.resumeEvent = threading.Event()
		self.resumeEvent.set() # Default to running
		self.scriptWaiting = False # True while the script is in a wait that Skip Wait can end
		self.skipWaitEvent = threading.Event()
		self.logInitialized = False
		self.initializing = True  # Flag to prevent saving settings during initialization
		self.log('Starting DCSAutoMate...')

		# Initialize other Managers
		self.scriptManager = ScriptManager()
		self.udpWireLogger = UdpWireLogger(self.config)
		self.SeqHelperFunctions = SequenceHelper(self.config, self.settingsManager, self.log)

		self.ttsManager = TTSManager(self.config)

		# Create main window
		self.mainWindow = QtWidgets.QMainWindow(parent)
		self.settingsManager.parentWindow = self.mainWindow # Set parent window for error messages
		self.mainWindow.setWindowTitle(f'DCS AutoMate {APP_VERSION}')
		# Set window size for compact layout with fixed panels
		self.mainWindow.resize(1050, 700)  # Slightly wider to accommodate fixed panels
		self.mainWindow.setMinimumSize(950, 600)  # Minimum to fit both panels + output
		self.mainWindow.closeEvent = self.onClose

		# Create central widget and main layout with minimal spacing
		centralWidget = QtWidgets.QWidget()
		self.mainWindow.setCentralWidget(centralWidget)
		mainLayout = QtWidgets.QGridLayout(centralWidget)
		mainLayout.setSpacing(5)  # Minimal spacing between elements
		mainLayout.setContentsMargins(5, 5, 5, 5)  # Minimal margins

		# Create the menu bar with traditional structure
		menuBar = self.mainWindow.menuBar()

		# File menu
		fileMenu = menuBar.addMenu('File')
		fileMenu.addAction('Exit', self.mainWindow.close)

		# Tools menu
		toolsMenu = menuBar.addMenu('Tools')
		toolsMenu.addAction('Settings...', self.openConfigWindow)
		toolsMenu.addAction('Install/Update DCS Scripts...', self.installDcsScripts)
		toolsMenu.addAction('Open Program Folder', self.openProgramFolder)
		toolsMenu.addSeparator()

		# Help menu
		helpMenu = menuBar.addMenu('Help')
		helpMenu.addAction('Control Reference', self.openControlReference)
		self.refreshControlReference()

		# UDP wire logging is now scoped to our own sockets and controlled via config:
		# - udpUiWireLogEnabled for UI remote control UDP

		# Create a frame to hold the DBE status label and the real-time DCS data - pinned to right
		statusFrame = QtWidgets.QFrame()
		statusLayout = QtWidgets.QVBoxLayout(statusFrame)
		statusLayout.setSpacing(3)  # Minimal spacing
		statusLayout.setContentsMargins(3, 3, 3, 3)  # Minimal margins
		statusFrame.setFixedWidth(280)  # Fixed width for right panel
		mainLayout.addWidget(statusFrame, 0, 1, QtCore.Qt.AlignmentFlag.AlignTop | QtCore.Qt.AlignmentFlag.AlignRight)

		# Add a status label for the Cockpit State Manager
		self.DBEStatusLabel = QtWidgets.QLabel('')
		statusLayout.addWidget(self.DBEStatusLabel)

		# Add a GroupBox for real-time DCS data with compact styling
		self.realtimeDataFrame = QtWidgets.QGroupBox("Realtime DCS Data")
		realtimeLayout = QtWidgets.QVBoxLayout(self.realtimeDataFrame)
		realtimeLayout.setSpacing(2)
		realtimeLayout.setContentsMargins(5, 5, 5, 5)
		statusLayout.addWidget(self.realtimeDataFrame)

		# Create a label for displaying real-time data
		self.realtimeDataLabel = QtWidgets.QLabel("")
		self.realtimeDataLabel.setAlignment(QtCore.Qt.AlignmentFlag.AlignLeft | QtCore.Qt.AlignmentFlag.AlignTop)
		realtimeLayout.addWidget(self.realtimeDataLabel)

		# Create a frame to hold the main controls with compact layout - pinned to left
		mainFrame = QtWidgets.QFrame()
		mainFrameLayout = QtWidgets.QVBoxLayout(mainFrame)
		mainFrameLayout.setSpacing(3)  # Tight spacing between controls
		mainFrameLayout.setContentsMargins(3, 3, 3, 3)
		# Remove fixed width - let it auto-adjust to dropdown content
		mainLayout.addWidget(mainFrame, 0, 0, QtCore.Qt.AlignmentFlag.AlignTop | QtCore.Qt.AlignmentFlag.AlignLeft)

		# Auto Select button
		self.autoSelectButton = QtWidgets.QPushButton('Auto Select Script from Telemetry')
		self.autoSelectButton.clicked.connect(self.autoSelectScript)
		mainFrameLayout.addWidget(self.autoSelectButton)

		# Select script file control
		mainFrameLayout.addWidget(QtWidgets.QLabel('Select script file:'))
		self.moduleDropdown = QtWidgets.QComboBox()
		# Don't set fixed width yet - will be calculated after population
		self.moduleDropdown.currentIndexChanged.connect(self.onModuleChange)
		mainFrameLayout.addWidget(self.moduleDropdown)

		# Select script control
		mainFrameLayout.addWidget(QtWidgets.QLabel('Select script:'))
		self.scriptDropdown = QtWidgets.QComboBox()
		# Don't set fixed width yet - will be calculated after population
		self.scriptDropdown.currentIndexChanged.connect(self.onScriptChange)
		mainFrameLayout.addWidget(self.scriptDropdown)

		# Add a container for the script variables with minimal spacing
		self.varContainer = QtWidgets.QFrame()
		self.varContainerLayout = QtWidgets.QVBoxLayout(self.varContainer)
		self.varContainerLayout.setSpacing(2)  # Tight spacing between radio groups
		self.varContainerLayout.setContentsMargins(0, 5, 0, 5)  # Small top/bottom margins only
		# Set minimum size to accommodate 6 radio button groups
		self.varContainer.setMinimumHeight(150)
		mainFrameLayout.addWidget(self.varContainer)
		self.varControls = {}
		self.varControlTypes = {}
		self.varFrames = {}
		self.varLabels = {}
		self.varValueFrames = {}

		# Create a frame to hold the Start, Skip Wait and Stop buttons side by side.
		buttonFrame = QtWidgets.QFrame()
		buttonLayout = QtWidgets.QHBoxLayout(buttonFrame)
		buttonLayout.setSpacing(5)
		buttonLayout.setContentsMargins(0, 5, 0, 0)
		mainFrameLayout.addWidget(buttonFrame)

		self.startButton = QtWidgets.QPushButton('Start')
		self.startButton.clicked.connect(self.onStartPauseClick)
		self.startButton.setEnabled(False)
		buttonLayout.addWidget(self.startButton)

		self.skipWaitButton = QtWidgets.QPushButton('Skip Wait')
		self.skipWaitButton.setToolTip('End the current wait (cockpit state, loop, or timer) and go on to the next step')
		self.skipWaitButton.clicked.connect(self.skipWait)
		self.skipWaitButton.setEnabled(False)
		buttonLayout.addWidget(self.skipWaitButton)

		self.stopButton = QtWidgets.QPushButton('Stop')
		self.stopButton.clicked.connect(self.stopScript)
		self.stopButton.setEnabled(False)
		buttonLayout.addWidget(self.stopButton)

		# Create a frame to hold the output text box
		outputFrame = QtWidgets.QFrame()
		outputLayout = QtWidgets.QVBoxLayout(outputFrame)
		outputLayout.setSpacing(2)
		outputLayout.setContentsMargins(0, 5, 0, 0)
		mainLayout.addWidget(outputFrame, 1, 0, 1, 2)

		# Configure output box for wide text and many lines
		self.outputBox = QtWidgets.QTextEdit()
		self.outputBox.setReadOnly(True)
		self.outputBox.setFont(QtGui.QFont('Consolas', 9))  # Slightly smaller font for more content
		self.outputBox.setLineWrapMode(QtWidgets.QTextEdit.LineWrapMode.NoWrap)  # No wrapping for long lines
		# Set minimum size to show ~24 lines and wide enough for long output
		self.outputBox.setMinimumSize(850, 300)
		outputLayout.addWidget(self.outputBox)

		# Configure grid layout weights - output gets most space
		mainLayout.setRowStretch(0, 0)  # Controls take minimum space
		mainLayout.setRowStretch(1, 1)  # Output expands to fill available space
		mainLayout.setColumnStretch(0, 0)  # Left panel takes minimum space (fixed width)
		mainLayout.setColumnStretch(1, 0)  # Right panel takes minimum space (fixed width)

		# Add horizontal spacing between the fixed-width panels and center area
		mainLayout.setHorizontalSpacing(10)

		self.stopFlag = threading.Event()

		# Check for Saved Games folder ambiguity or missing path FIRST, before checking scripts.
		# This ensures users with multiple Saved Games folders (DCS/DCS.openbeta) or no detected folder
		# must resolve the path before we check if scripts are installed.
		self._checkSavedGamesAmbiguity()

		if not DcsScriptsInstaller.check_installed(self.config):
			box = QtWidgets.QMessageBox(self.mainWindow)
			box.setIcon(QtWidgets.QMessageBox.Icon.Question)
			box.setWindowTitle('Missing Scripts')
			box.setText('The DCSAutoMate scripts do not appear to be installed in your DCS Saved Games folder.\n\nDo you want to install them now?')
			yesButton = box.addButton('Yes', QtWidgets.QMessageBox.ButtonRole.AcceptRole)
			noLink = box.addButton('No', QtWidgets.QMessageBox.ButtonRole.RejectRole)
			box.setDefaultButton(noLink)
			box.exec()
			if box.clickedButton() == yesButton:
				self.installDcsScripts()

		self.onProgramStart()
		self.updateUIState()
		self.startUiRemoteControlListener()

	def startUiRemoteControlListener(self):
		if self.uiRemoteControlThread and self.uiRemoteControlThread.is_alive():
			return

		self.uiRemoteControlStopFlag.clear()
		self.uiRemoteControlSocket = None  # Will be set by thread
		self.uiRemoteControlThread = threading.Thread(target=self._uiRemoteControlThreadMain, daemon=True)
		self.uiRemoteControlThread.start()
		if not bool(self.config.get('udpUiWireLogEnabled', False)):
			self.log(f'UI remote control: Listening on UDP {self.uiRemoteControlHost}:{self.uiRemoteControlPort}')

	def stopUiRemoteControlListener(self):
		self.uiRemoteControlStopFlag.set()

		# Close socket to unblock any pending recv
		if hasattr(self, 'uiRemoteControlSocket') and self.uiRemoteControlSocket:
			try:
				self.uiRemoteControlSocket.close()
			except Exception:
				pass

		# Wait for thread with reasonable timeout
		if self.uiRemoteControlThread:
			self.uiRemoteControlThread.join(timeout=1.0)

	def _sendUiMessageToDcs(self, message):
		try:
			sendSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
			payload = str(message or '').encode('utf-8')
			addr = (self.uiRemoteControlHost, self.uiRemoteControlReplyPort)
			self.udpWireLogger.logUiTx(addr, payload)
			sendSocket.sendto(payload, addr)
			sendSocket.close()
		except Exception as e:
			self.log(f'UI remote control: Failed sending reply to DCS: {e}')

	def _encodePipeList(self, items):
		if not items:
			return ''
		cleanItems = []
		for item in items:
			text = str(item)
			text = text.replace('|', '/')
			text = text.replace(';', ',')
			text = text.replace('\n', ' ')
			text = text.replace('\r', ' ')
			cleanItems.append(text)
		return '|'.join(cleanItems)

	def _uiSendLog(self, text):
		text = str(text or '')
		text = text.replace(';', ',').replace('\n', ' ').replace('\r', ' ')
		self._sendUiMessageToDcs(f'DCSAUTOMATE_UI;event=log;text={text};')

	def _uiSendClear(self):
		self._sendUiMessageToDcs('DCSAUTOMATE_UI;event=clear;')

	def _uiSendScriptState(self):
		isRunning = getattr(self, 'scriptRunning', False)
		running = 'true' if isRunning else 'false'
		paused = 'true' if getattr(self, 'scriptPaused', False) else 'false'
		waiting = 'true' if isRunning and self.scriptWaiting else 'false'
		self._sendUiMessageToDcs(f'DCSAUTOMATE_UI;event=scriptState;running={running};paused={paused};waiting={waiting};')

	def _uiGetVarLabelsForOverlay(self, varNames, scriptVars, moduleName, scriptName):
		labels = []
		unsetVars = set(getattr(self, 'uiTelemetryUnsetVars', set()) or set())
		unsetVarsModule = getattr(self, 'uiTelemetryUnsetVarsModule', '')
		unsetVarsScript = getattr(self, 'uiTelemetryUnsetVarsScript', '')
		shouldMarkUnset = bool(unsetVars) and unsetVarsModule == moduleName and unsetVarsScript == scriptName
		for varName in varNames:
			varDefinition = scriptVars.get(varName) if isinstance(scriptVars, dict) else None
			label = varName
			if isinstance(varDefinition, dict):
				label = varDefinition.get('label', varName)
			if shouldMarkUnset and varName in unsetVars:
				label = f'{label} [set manually]'
			labels.append(label)
		return labels

	def _handleUiRemoteControlMessage(self, msg):
		msg = str(msg or '')
		if not msg.startswith('DCSAUTOMATE_UI;'):
			return

		fields = {}
		for part in msg.split(';'):
			if '=' in part:
				key, value = part.split('=', 1)
				fields[key] = value

		cmd = fields.get('cmd', '')
		if cmd == 'getModules':
			modules = self.modules if hasattr(self, 'modules') else self.scriptManager.getModules()
			selected = self.moduleDropdown.currentText() if hasattr(self, 'moduleDropdown') else ''
			items = self._encodePipeList(modules)
			selected = str(selected).replace(';', ',').replace('|', '/')
			self._sendUiMessageToDcs(f'DCSAUTOMATE_UI;event=modulesList;items={items};selected={selected};')

			# Sync running state
			self._uiSendScriptState()

		elif cmd == 'getScripts':
			moduleName = fields.get('module', '')
			if not moduleName:
				return
			scriptData = self.scriptManager.getScriptData(moduleName)
			scripts = [s.get('name', '') for s in scriptData.get('scripts', [])]
			selectedScript = self.scriptDropdown.currentText() if hasattr(self, 'scriptDropdown') else ''
			# Precompute to avoid complex expressions inside f-string (works on Python 3.9+)
			itemsEncoded = self._encodePipeList(scripts)
			selected = str(selectedScript).replace(';', ',').replace('|', '/')
			self._sendUiMessageToDcs(f'DCSAUTOMATE_UI;event=scriptsList;module={moduleName};items={itemsEncoded};selected={selected};')

		elif cmd == 'getVars':
			moduleName = fields.get('module', '')
			scriptName = fields.get('script', '')
			if not moduleName or not scriptName:
				return
			scriptData = self.scriptManager.getScriptData(moduleName)
			scriptVars = self.scriptManager.getScriptVars(scriptData, scriptName)
			varNames = list(scriptVars.keys())
			varLabels = self._uiGetVarLabelsForOverlay(varNames, scriptVars, moduleName, scriptName)
			varTypes = [scriptVars[v].get('type', 'dropdown') for v in varNames]
			self._sendUiMessageToDcs(f'DCSAUTOMATE_UI;event=varsList;module={moduleName};script={scriptName};items={self._encodePipeList(varNames)};labels={self._encodePipeList(varLabels)};types={self._encodePipeList(varTypes)};')

		elif cmd == 'getVarOptions':
			moduleName = fields.get('module', '')
			scriptName = fields.get('script', '')
			varName = fields.get('var', '')
			if not moduleName or not scriptName or not varName:
				return

			# Get current values from UI to resolve dependencies
			currentValues = {}
			if hasattr(self, 'varControls'):
				for vName in self.varControls:
					val = self.getVarValue(vName)
					if val is not None:
						currentValues[vName] = val

			# Override with any values passed in the request (e.g. from ingame selection)
			for key, val in fields.items():
				if key not in ('cmd', 'module', 'script', 'var'):
					currentValues[key] = val

			self._uiSendVarOptions(moduleName, scriptName, varName, currentValues)

		elif cmd == 'varSelection':
			# Handle varSelection from DCS (user clicked overlay)
			moduleName = fields.get('module', '')
			scriptName = fields.get('script', '')
			varName = fields.get('var', '')
			value = fields.get('selectedValue', '') # This is the value, not label

			if hasattr(self, 'moduleDropdown') and moduleName == self.moduleDropdown.currentText() and \
			   hasattr(self, 'scriptDropdown') and scriptName == self.scriptDropdown.currentText():
				if hasattr(self, 'varControls') and varName in self.varControls:
					self.updatingFromRemote = True
					try:
						self.setVarValueByName(varName, value)
						# Update dependents
						if hasattr(self, 'varDependents') and varName in self.varDependents:
							currentValues = {var: self.getVarValue(var) for var in self.varControls}
							for depVar in self.varDependents[varName]:
								self._uiSendVarOptions(self.moduleDropdown.currentText(), self.scriptDropdown.currentText(), depVar, currentValues)
					finally:
						self.updatingFromRemote = False

		elif cmd == 'valueChanged':
			type = fields.get('type', '')
			name = fields.get('name', '') # module name, script name, or var name
			value = fields.get('value', '')

			self.updatingFromRemote = True
			try:
				if type == 'module':
					if hasattr(self, 'moduleDropdown'):
						self.moduleDropdown.setCurrentText(value)
				elif type == 'script':
					if hasattr(self, 'scriptDropdown'):
						self.scriptDropdown.setCurrentText(value)
				elif type == 'var':
					if hasattr(self, 'varControls') and name in self.varControls:
						self.setVarValueByName(name, value)
						# Update dependents
						if hasattr(self, 'varDependents') and name in self.varDependents:
							currentValues = {var: self.getVarValue(var) for var in self.varControls}
							for depVar in self.varDependents[name]:
								self._uiSendVarOptions(self.moduleDropdown.currentText(), self.scriptDropdown.currentText(), depVar, currentValues)
			finally:
				self.updatingFromRemote = False

		elif cmd == 'autoSelectTelemetry':
			if hasattr(self, 'autoSelectButton') and self.autoSelectButton.isEnabled():
				self.log('UI remote control: Auto-selecting telemetry...')
				self.autoSelectScript()
			else:
				self._uiSendLog('Auto Select is disabled.')

		elif cmd == 'start':
			if self.startButton.isEnabled():
				self._uiSendLog('Starting script...')
				self.runScript()
			else:
				self._uiSendLog('Start is disabled (select module/script first).')
		elif cmd == 'pause':
			if self.scriptRunning and not self.scriptPaused:
				self._uiSendLog('Pausing script...')
				self.pauseScript()
		elif cmd == 'resume':
			if self.scriptRunning and self.scriptPaused:
				self._uiSendLog('Resuming script...')
				self.resumeScript()
		elif cmd == 'skipWait':
			self.skipWait()
		elif cmd == 'stop':
			if self.stopButton.isEnabled():
				self._uiSendLog('Stopping script...')
				self.stopScript()
			else:
				self._uiSendLog('Stop is disabled (no script running).')

	def _uiSendVarOptions(self, moduleName, scriptName, varName, currentValues):
		scriptData = self.scriptManager.getScriptData(moduleName)
		scriptVars = self.scriptManager.getScriptVars(scriptData, scriptName)
		varDefinition = scriptVars.get(varName)

		options = {}
		if isinstance(varDefinition, dict) and 'function' in varDefinition:
			functionName = varDefinition['function']
			params = varDefinition.get('params', [])
			resolvedParams = []
			for param in params:
				resolvedParams.append(currentValues.get(param, ''))
			try:
				dynamicOptions = getattr(self.SeqHelperFunctions, functionName)(*resolvedParams)
				options = {opt: opt for opt in dynamicOptions}
			except Exception as e:
				self.log(f'Error getting var options for {varName}: {e}')
				options = {}
		elif isinstance(varDefinition, dict) and 'options' in varDefinition:
			options = varDefinition.get('options', {})
		else:
			options = varDefinition if isinstance(varDefinition, dict) else {}

		optionPairs = []
		if isinstance(options, dict):
			for optionValue, optionLabel in options.items():
				optionPairs.append((optionValue, optionLabel))
		elif isinstance(options, (list, tuple)):
			for option in options:
				if isinstance(option, dict):
					optionLabel = option.get('label', option.get('value'))
					optionPairs.append((option.get('value'), optionLabel))
				else:
					optionPairs.append((option, option))

		values = [str(value) for value, _ in optionPairs]
		labels = [str(label) for _, label in optionPairs]

		# Determine selected value
		selectedValue = ''
		if varName in currentValues:
			selectedValue = str(currentValues[varName])

		items = self._encodePipeList(labels)
		vals = self._encodePipeList(values)
		selectedValue = selectedValue.replace(';', ',').replace('|', '/')

		self._sendUiMessageToDcs(f'DCSAUTOMATE_UI;event=varOptions;module={moduleName};script={scriptName};var={varName};items={items};values={vals};selected={selectedValue};')

	def _uiRemoteControlThreadMain(self):
		recvSocket = None
		try:
			recvSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
			recvSocket.bind((self.uiRemoteControlHost, self.uiRemoteControlPort))
			recvSocket.settimeout(0.5)
			self.uiRemoteControlSocket = recvSocket  # Store for clean shutdown
		except Exception as e:
			self.log(f'UI remote control: Failed to bind UDP {self.uiRemoteControlHost}:{self.uiRemoteControlPort}: {e}')
			return

		while not self.uiRemoteControlStopFlag.is_set():
			try:
				data, addr = recvSocket.recvfrom(8192)
				self.udpWireLogger.logUiRx(addr, data)
				msg = data.decode('utf-8', errors='replace')
				self.uiRemoteControlBridge.messageReceived.emit(msg)
			except socket.timeout:
				continue
			except OSError:
				# Socket was closed (expected during shutdown)
				if self.uiRemoteControlStopFlag.is_set():
					break
			except Exception as e:
				self.log(f'UI remote control: Receive error: {e}')
				break

		try:
			if recvSocket:
				recvSocket.close()
		except Exception:
			pass
		self.uiRemoteControlSocket = None

	def applyCommandLineArgs(self):
		# Initialize parser for command line arguments.
		parser = argparse.ArgumentParser(
			prog = 'DCSAutoMate',
			description = 'Sends scripted commands to DCS, allowing complete cockpit scripting and automation.',
		)
		parser.add_argument(
			'--debug',
			action = 'store_true', # Stores True if passed, otherwise False.
			help = "If passed, script will be run normally, but without actually sending any commands to DCS."
		)
		parser.add_argument(
			'--disableSpeech',
			action = 'store_true', # Stores True if passed, otherwise False.
			help = "If passed, text-to-speech commands in the script will not be executed."
		)
		parser.add_argument(
			'--dcsWindowUseTitle',
			action = 'store_true', # Stores True if passed, otherwise False.
			help = "If passed, will make DCSAutoMate look for the DCS window by title, instead of by exe path."
		)
		parser.add_argument(
			'--dcsWindowTitleOverride',
			action = 'store',
			help = "If passed, specifies the title of the DCS window to send commands to (default is \"Digital Combat Simulator\").  This title is case-insensitive and can appear anywhere in the full window title string."
		)
		parser.add_argument(
			'--dcsSavedGamesOverride',
			action = 'store',
			help = "If passed, specifies the full path to the DCS Saved Games folder.  Defaults to trying first %%USERPROFILE%%\\Saved Games\\DCS and then %%USERPROFILE%%\\Saved Games\\DCS.openbeta."
		)
		parser.add_argument(
			'--dcsExePathOverride',
			action = 'store',
			help = "If passed, specifies the full path to the DCS executable.  Defaults to auto-detection via registry."
		)

		args = parser.parse_args()

		if args.debug:
			self.config['debug'] = args.debug
		if args.disableSpeech:
			self.config['disableSpeech'] = args.disableSpeech
		if args.dcsWindowUseTitle:
			self.config['dcsWindowUseTitle'] = args.dcsWindowUseTitle
		if args.dcsWindowTitleOverride:
			self.config['dcsWindowTitleOverride'] = args.dcsWindowTitleOverride
		if args.dcsSavedGamesOverride:
			self.config['dcsSavedGamesOverride'] = args.dcsSavedGamesOverride
			# Re-detect path if override provided via CLI
			self.config['dcsSavedGamesPath'] = self.settingsManager.detectSavedGamesPath(args.dcsSavedGamesOverride)

		if args.dcsExePathOverride:
			self.config['dcsExePathOverride'] = args.dcsExePathOverride
			# Re-detect path if override provided via CLI
			self.config['dcsExePath'] = self.settingsManager.detectDCSInstallPath(args.dcsExePathOverride)

	def onProgramStart(self):
		# Apply command line arguments to config
		self.applyCommandLineArgs()

		# Start the DCS Direct Manager, which connects via TCP to communicate with DCS.
		self.dbe = DCSDirectManager(self.config)
		self.dbe.start()

		# Start the DCSAutoMateExport manager, which begins a thread to receive data from the DCSAutoMateExport.lua script.
		self.DAMExport = DCSAutoMateExportManager(self.config)
		self.DAMExport.start()

		# Get the list of modules (file names) from the script *.py files.
		self.modules = self.scriptManager.getModules()
		self.updateModulesDropdown(self.modules)

		lastUsedModule = self.settingsManager.getLastUsedModule()

		# Set the last used module, if any.
		if lastUsedModule and lastUsedModule in self.modules:
			# Try to find the index and set by index instead of text
			try:
				index = self.modules.index(lastUsedModule)
				self.moduleDropdown.setCurrentIndex(index)
			except ValueError:
				self.moduleDropdown.setCurrentText(lastUsedModule)
		else:
			self.moduleDropdown.setCurrentIndex(0)
		self.moduleName = self.moduleDropdown.currentText()

		self.onModuleChange()

		self.updateDataMonitoring()

		# The update check is a source-tree tool, so only remind when running from source.
		if not getattr(sys, 'frozen', False):
			notice = dcsUpdateNotice(readInstalledDcsVersion(dcsInstallDir(self.config.get('dcsExePath'))), readCheckedDcsVersion())
			if notice:
				self.updateOutput(notice + '\n')

		# Initialization complete - now allow settings to be saved
		self.initializing = False

	def _checkSavedGamesAmbiguity(self):
		try:
			# Check if no Saved Games folder was detected at all
			savedGamesPath = self.config.get('dcsSavedGamesPath', '')
			if not savedGamesPath:
				text = (
					'No DCS Saved Games folder was detected.\n\n'
					'DCSAutoMate looks for:\n'
					'  • %USERPROFILE%\\Saved Games\\DCS\n'
					'  • %USERPROFILE%\\Saved Games\\DCS.openbeta\n\n'
					'Please open Tools -> Settings and set the "DCS Saved Games folder path" to your DCS Saved Games folder.'
				)
				msg = QtWidgets.QMessageBox(self.mainWindow)
				msg.setWindowTitle('DCS Saved Games Folder Not Found')
				msg.setIcon(QtWidgets.QMessageBox.Icon.Warning)
				msg.setText(text)
				openBtn = msg.addButton('Open Settings', QtWidgets.QMessageBox.AcceptRole)
				msg.addButton('Ignore', QtWidgets.QMessageBox.RejectRole)
				msg.exec()
				if msg.clickedButton() == openBtn:
					self.openConfigWindow()
				return

			# Check if multiple Saved Games folders were detected (ambiguous)
			if self.config.get('dcsSavedGamesAmbiguous'):
				options = self.config.get('dcsSavedGamesOptions', []) or []
				text = 'Multiple DCS Saved Games folders were detected:\n\n'
				for p in options:
					text += f'{p}\n'
				text += '\nPlease open Tools -> Settings and set the "DCS Saved Games folder path" to the correct folder.'
				msg = QtWidgets.QMessageBox(self.mainWindow)
				msg.setWindowTitle('Select DCS Saved Games Folder')
				msg.setText(text)
				openBtn = msg.addButton('Open Settings', QtWidgets.QMessageBox.AcceptRole)
				msg.addButton('Ignore', QtWidgets.QMessageBox.RejectRole)
				msg.exec()
				if msg.clickedButton() == openBtn:
					self.openConfigWindow()

		except Exception as e:
			self.log(f'Error showing saved games ambiguity prompt: {e}')

	# Called when the program is closed.  Stops the cockpit state manager and closes the program.
	def onClose(self, event):
		self.stopUiRemoteControlListener()
		self.dbe.stop()  # Stop the DCSDirectManager
		self.DAMExport.stop()  # Stop the DCSAutoMateExportManager
		event.accept()  # Accept the close event

	def updateDataMonitoring(self):
		self.DBEStatusLabel.setText(self.dbe.outputString)
		self.realtimeDataLabel.setText(self.DAMExport.outputString)

		# Schedule next UI update
		QtCore.QTimer.singleShot(100, self.updateDataMonitoring)

	def adjustDropdownWidths(self):
		"""Calculate optimal width for dropdowns based on actual content."""
		fontMetrics = QtGui.QFontMetrics(QtWidgets.QApplication.font())
		maxWidth = 0

		# Check all items in both dropdowns to find the longest text
		for combo in [self.moduleDropdown, self.scriptDropdown]:
			for i in range(combo.count()):
				text = combo.itemText(i)
				width = fontMetrics.horizontalAdvance(text)
				maxWidth = max(maxWidth, width)

		# Add padding for dropdown arrow and margins
		optimalWidth = maxWidth + 50

		# Set both dropdowns to the same optimal width
		self.moduleDropdown.setFixedWidth(optimalWidth)
		self.scriptDropdown.setFixedWidth(optimalWidth)

	# Called when the module dropdown is changed.  Updates the script dropdown with the scripts from the selected module.
	def onModuleChange(self):
		# Get the new moduleName from the dropdown and set it in self.
		self.moduleName = self.moduleDropdown.currentText()

		# Load the script metadata for this module from the script file.
		self.scriptData = self.scriptManager.getScriptData(self.moduleName)

		# Block signals to prevent intermediate saves during population
		self.scriptDropdown.blockSignals(True)

		# Update the script dropdown with the data.
		self.updateScriptDropdown(self.scriptData)

		# Set the last used script, if any.
		lastUsedScriptName = self.settingsManager.getLastUsedScriptName(self.moduleName)
		scriptNames = [s['name'] for s in self.scriptData['scripts']]

		if lastUsedScriptName:
			if lastUsedScriptName in scriptNames:
				try:
					index = scriptNames.index(lastUsedScriptName)
					self.scriptDropdown.setCurrentIndex(index)
				except ValueError:
					self.scriptDropdown.setCurrentText(lastUsedScriptName)
			else:
				self.scriptDropdown.setCurrentIndex(0)
		else:
			self.scriptDropdown.setCurrentIndex(0)

		self.scriptDropdown.blockSignals(False)

		self.onScriptChange()

		if not getattr(self, 'updatingFromRemote', False):
			self._sendUiMessageToDcs(f'DCSAUTOMATE_UI;event=valueChanged;type=module;value={self.moduleName};')

	def onScriptChange(self):
		# Get the new scriptName from the dropdown and set it in self.
		self.scriptName = self.scriptDropdown.currentText()

		# Create the dropdowns and set them to some values based on the last used settings.
		self.scriptVars = self.scriptManager.getScriptVars(self.scriptData, self.scriptName)
		lastUsedVars = self.settingsManager.getLastUsedVars(self.moduleName, self.scriptName)
		if lastUsedVars:
			setScriptVars = lastUsedVars
		else:
			setScriptVars = {}
		self.updateScriptVarsDropdowns(self.scriptVars, setScriptVars)

		# Save the new state (script change or initial load)
		if not self.initializing:
			self.saveSettings()

		if not getattr(self, 'updatingFromRemote', False):
			self._sendUiMessageToDcs(f'DCSAUTOMATE_UI;event=valueChanged;type=script;value={self.scriptName};')

	def updateScriptVarsDropdowns(self, scriptVars, setScriptVars):
		# Clear existing controls
		while self.varContainerLayout.count():
			child = self.varContainerLayout.takeAt(0)
			if child.widget():
				child.widget().deleteLater()

		self.varControls.clear()
		self.varControlTypes.clear()
		self.varFrames.clear()
		self.varLabels.clear()
		self.varValueFrames.clear()
		self.varDependents = {}
		self.currentVarValues = {}

		# First pass: build dependents
		for varName, varDefinition in scriptVars.items():
			if isinstance(varDefinition, dict) and 'params' in varDefinition:
				for param in varDefinition['params']:
					if param in scriptVars:
						if param not in self.varDependents:
							self.varDependents[param] = []
						self.varDependents[param].append(varName)

		for varName, varDefinition in scriptVars.items():
			varLabelText = varName
			functionName = None
			params = []
			options = {}
			if isinstance(varDefinition, dict):
				varLabelText = varDefinition.get('label', varName)
				if 'function' in varDefinition:
					functionName = varDefinition['function']
				if 'params' in varDefinition:
					params = varDefinition['params']
				if 'options' in varDefinition:
					options = varDefinition['options']
			else:
				options = varDefinition if isinstance(varDefinition, dict) else {}

			# Get options
			if functionName:
				resolvedParams = []
				for param in params:
					if param in self.currentVarValues:
						resolvedParams.append(self.currentVarValues[param])
					else:
						resolvedParams.append(param)
				try:
					dynamicOptions = getattr(self.SeqHelperFunctions, functionName)(*resolvedParams)
					options = {opt: opt for opt in dynamicOptions}
				except Exception as e:
					print(f"Error calling {functionName}: {e}")
					options = {}

			optionPairs = []
			if isinstance(options, dict):
				for optionValue, optionLabel in options.items():
					optionPairs.append((optionValue, optionLabel))
			elif isinstance(options, (list, tuple)):
				for option in options:
					if isinstance(option, dict):
						optionValue = option.get('value')
						optionLabel = option.get('label', optionValue)
						optionPairs.append((optionValue, optionLabel))
					else:
						optionPairs.append((option, option))
			else:
				optionPairs = []

			frame = QtWidgets.QFrame()
			frameLayout = QtWidgets.QHBoxLayout(frame)
			frameLayout.setSpacing(8)
			frameLayout.setContentsMargins(0, 2, 0, 2)

			# Create label with fixed width for alignment
			label = QtWidgets.QLabel(f'{varLabelText}:')
			label.setMinimumWidth(120)
			frameLayout.addWidget(label)

			# Create a sub-frame for the control
			valueFrame = QtWidgets.QFrame()
			valueLayout = QtWidgets.QHBoxLayout(valueFrame)
			valueLayout.setContentsMargins(2, 0, 2, 0)
			valueLayout.setSpacing(5)
			frameLayout.addWidget(valueFrame)

			storedValue = setScriptVars.get(varName)
			if storedValue is None:
				storedValue = setScriptVars.get(varLabelText)

			varType = varDefinition.get('type', 'dropdown')
			if varType == 'text':
				lineEdit = QtWidgets.QLineEdit()
				lineEdit.setMinimumWidth(200)

				if storedValue is not None:
					lineEdit.setText(str(storedValue))
				else:
					defaultVal = varDefinition.get('default', '')
					lineEdit.setText(str(defaultVal))

				lineEdit.textChanged.connect(lambda text, vName=varName: self.onVarsValueChanged(vName))
				self.varControls[varName] = lineEdit
				valueLayout.addWidget(lineEdit)
				self.varControlTypes[varName] = 'text'
			else:
				combo = QtWidgets.QComboBox()
				combo.setMinimumWidth(200)
				for optionValue, optionLabel in optionPairs:
					combo.addItem(str(optionLabel), optionValue)

				if storedValue is not None:
					for i in range(combo.count()):
						if combo.itemData(i) == storedValue:
							combo.setCurrentIndex(i)
							break
				else:
					if combo.count() > 0:
						combo.setCurrentIndex(0)

				combo.currentIndexChanged.connect(lambda index, vName=varName: self.onVarsValueChanged(vName))
				self.varControls[varName] = combo
				valueLayout.addWidget(combo)
				self.varControlTypes[varName] = 'dropdown'

			self.varFrames[varName] = frame
			self.varLabels[varName] = label
			self.varValueFrames[varName] = valueFrame
			self.varContainerLayout.addWidget(frame)

			# Set current value
			self.currentVarValues[varName] = self.getVarValue(varName)

		# Add stretch at the end
		self.varContainerLayout.addStretch()
		self.updateUIState()

	def onVarsValueChanged(self, varName=None):
		# Reset style for any frame that has a selection (clears "unset" error highlight)
		if hasattr(self, 'varFrames'):
			for varKey, frame in self.varFrames.items():
				if self.getVarValue(varKey) is not None:
					frame.setStyleSheet("")

		# Update current values and dependents
		if varName:
			self.currentVarValues[varName] = self.getVarValue(varName)
			if varName in getattr(self, 'varDependents', {}):
				for depVar in self.varDependents[varName]:
					self.updateVarOptions(depVar)

		# Only save settings if we're not in initialization phase
		if not self.initializing:
			self.saveSettings()

			try:
				if varName and hasattr(self, 'varControls') and varName in self.varControls:
					control = self.varControls[varName]
					if isinstance(control, QtWidgets.QComboBox):
						index = control.currentIndex()
						if index >= 0:
							selectedLabel = str(control.itemText(index) or '')
							selectedValue = control.itemData(index)
						else:
							selectedLabel = ''
							selectedValue = None
					elif isinstance(control, QtWidgets.QLineEdit):
						selectedLabel = control.text()
						selectedValue = control.text()
					else:
						selectedLabel = ''
						selectedValue = None

					if selectedValue is not None and not getattr(self, 'updatingFromRemote', False):
						selectedLabel = selectedLabel.replace(';', ',').replace('|', '/')
						selectedValue = str(selectedValue).replace(';', ',').replace('|', '/')
						self._sendUiMessageToDcs(
							f'DCSAUTOMATE_UI;event=varSelection;module={self.moduleDropdown.currentText()};script={self.scriptDropdown.currentText()};var={varName};selected={selectedLabel};selectedLabel={selectedLabel};selectedValue={selectedValue};'
						)
			except Exception:
				pass

	def setVarValueByName(self, varName, value):
		if varName not in self.varControls:
			return
		control = self.varControls[varName]
		if isinstance(control, QtWidgets.QComboBox):
			for i in range(control.count()):
				if control.itemData(i) == value:
					control.setCurrentIndex(i)
					break
		elif isinstance(control, QtWidgets.QLineEdit):
			control.setText(str(value))

	def highlightWidget(self, widgetName, index=None):
		"""Highlights a specific UI widget based on name and optional index."""
		# Reset all highlights first
		self.moduleDropdown.setStyleSheet("")
		self.scriptDropdown.setStyleSheet("")
		self.startButton.setStyleSheet("")
		self.autoSelectButton.setStyleSheet("")
		for label in self.varLabels.values():
			label.setStyleSheet("")
		for frame in self.varValueFrames.values():
			frame.setStyleSheet("")

		style = "border: 2px solid red; border-radius: 4px;"

		if widgetName == "module":
			self.moduleDropdown.setStyleSheet(style)
		elif widgetName == "script":
			self.scriptDropdown.setStyleSheet(style)
		elif widgetName == "start":
			self.startButton.setStyleSheet(style)
		elif widgetName == "auto_select":
			self.autoSelectButton.setStyleSheet(style)
		elif widgetName == "var":
			# Highlight specific variable label
			if index is not None and 0 <= index < len(self.varControls):
				varName = list(self.varControls.keys())[index]
				if varName in self.varLabels:
					self.varLabels[varName].setStyleSheet(style)
		elif widgetName == "var_value":
			# Highlight specific variable values
			if index is not None and 0 <= index < len(self.varControls):
				varName = list(self.varControls.keys())[index]
				if varName in self.varValueFrames:
					self.varValueFrames[varName].setStyleSheet(style)

	def setVarValue(self, varIndex, valueIndex):
		"""Sets a variable value based on indices."""
		if 0 <= varIndex < len(self.varControls):
			varName = list(self.varControls.keys())[varIndex]
			control = self.varControls[varName]
			if isinstance(control, QtWidgets.QComboBox):
				if 0 <= valueIndex < control.count():
					control.setCurrentIndex(valueIndex)
			# For QLineEdit, valueIndex doesn't make sense, so we ignore it or treat it differently if needed.

	def getVarValue(self, varName):
		if varName not in self.varControls:
			return None
		control = self.varControls[varName]
		if isinstance(control, QtWidgets.QComboBox):
			index = control.currentIndex()
			if index >= 0:
				return control.itemData(index)
		elif isinstance(control, QtWidgets.QLineEdit):
			return control.text()
		return None

	def updateVarOptions(self, varName):
		if varName not in self.varControls or varName not in self.scriptVars:
			return
		varDefinition = self.scriptVars[varName]
		if not isinstance(varDefinition, dict) or 'function' not in varDefinition:
			return
		functionName = varDefinition['function']
		params = varDefinition.get('params', [])
		resolvedParams = []
		for param in params:
			if param in self.currentVarValues:
				resolvedParams.append(self.currentVarValues[param])
			else:
				resolvedParams.append(param)
		try:
			dynamicOptions = getattr(self.SeqHelperFunctions, functionName)(*resolvedParams)
			options = {opt: opt for opt in dynamicOptions}
		except Exception as e:
			print(f"Error calling {functionName}: {e}")
			options = {}

		# Update the control
		control = self.varControls[varName]
		currentValue = self.currentVarValues.get(varName)

		control.blockSignals(True)
		control.clear()

		optionPairs = []
		if isinstance(options, dict):
			for optionValue, optionLabel in options.items():
				optionPairs.append((optionValue, optionLabel))
		elif isinstance(options, (list, tuple)):
			for option in options:
				if isinstance(option, dict):
					optionValue = option.get('value')
					optionLabel = option.get('label', optionValue)
					optionPairs.append((optionValue, optionLabel))
				else:
					optionPairs.append((option, option))

		for optionValue, optionLabel in optionPairs:
			control.addItem(str(optionLabel), optionValue)

		# Restore selection if possible
		if currentValue is not None:
			index = control.findData(currentValue)
			if index >= 0:
				control.setCurrentIndex(index)
			else:
				if control.count() > 0:
					control.setCurrentIndex(0)
		else:
			if control.count() > 0:
				control.setCurrentIndex(0)

		control.blockSignals(False)

		# Update current value
		self.currentVarValues[varName] = self.getVarValue(varName)

	def autoSelectScript(self):
		self.uiTelemetryUnsetVars = set()
		self.uiTelemetryUnsetVarsModule = ''
		self.uiTelemetryUnsetVarsScript = ''

		data = self.DAMExport.dataStorage
		if not data:
			QtWidgets.QMessageBox.warning(self.mainWindow, "No Data", "No telemetry data received from DCS yet.\nPlease ensure DCS is running and the mission is loaded.")
			return False

		try:
			# 1. Identify Module
			dcsModuleName = data.get('LoGetSelfData', {}).get('Name')
			if not dcsModuleName:
				QtWidgets.QMessageBox.warning(self.mainWindow, "Unknown Module", "Could not determine the active DCS module from telemetry.")
				return False

			foundModuleFile = None

			# Helper to check if module matches
			def isModuleMatch(scriptData, dcsName):
				modName = scriptData.get('moduleName')
				if isinstance(modName, list):
					return dcsName in modName
				return modName == dcsName

			# Check current module first
			if self.moduleName:
				try:
					scriptData = self.scriptManager.getScriptData(self.moduleName)
					if isModuleMatch(scriptData, dcsModuleName):
						foundModuleFile = self.moduleName
				except:
					pass

			# If not current, search all modules
			if not foundModuleFile:
				for moduleFile in self.modules:
					try:
						scriptData = self.scriptManager.getScriptData(moduleFile)
						if isModuleMatch(scriptData, dcsModuleName):
							foundModuleFile = moduleFile
							break
					except:
						continue

			if foundModuleFile:
				self.moduleDropdown.setCurrentText(foundModuleFile)
			else:
				QtWidgets.QMessageBox.warning(self.mainWindow, "Module Not Found", f"No script file found for DCS module: {dcsModuleName}")
				return False

			# 2. Determine Script (Cold/Hot/Air)
			altAGL = data.get('LoGetAltitudeAboveGroundLevel', 0)
			altMSL = data.get('LoGetAltitudeAboveSeaLevel', 0)
			airspeedTAS = data.get('LoGetTrueAirSpeed', 0)

			engineRunning = isEngineRunning(data.get('LoGetEngineInfo', {}))

			position = classifyPosition(altAGL, altMSL, airspeedTAS)
			isAir = position == 'air'
			isCarrier = position == 'carrier'

			targetScriptName = "Cold Start"
			if isAir:
				targetScriptName = "Air Start"
			elif engineRunning:
				targetScriptName = "Hot Start"

			# The aircraft script can refine the choice from live cockpit state with an optional autoSelect(context).
			context = AutoSelectContext(targetScriptName, data, lambda controls: self.readControlsForAutoSelect(dcsModuleName, controls))
			hookResult = applyModuleAutoSelect(self.scriptManager.getModule(foundModuleFile), context)
			hookVars = hookResult.get('vars', {})
			if hookResult.get('script'):
				targetScriptName = hookResult['script']

			# Select the script — first try exact name match, then fall back to autoSelectHook.
			index = self.scriptDropdown.findText(targetScriptName)
			if index < 0:
				hookMatch = next((s for s in scriptData.get('scripts', []) if s.get('autoSelectHook') == targetScriptName), None)
				if hookMatch:
					index = self.scriptDropdown.findText(hookMatch['name'])
			if index >= 0:
				self.scriptDropdown.setCurrentIndex(index)

			# 3. Set Variables
			# Calculate desired values
			clockSeconds = None
			if 'LoGetMissionStartTime' in data and 'LoGetModelTime' in data:
				clockSeconds = data['LoGetMissionStartTime'] + data['LoGetModelTime']
			timeOfDayValue = timeOfDay(clockSeconds) if clockSeconds is not None else None
			timeOfDayLabel = timeOfDayValue.capitalize() if timeOfDayValue else None

			locationVar = "Ground"
			if isCarrier:
				locationVar = "Carrier"
			elif isAir:
				locationVar = "Air"
			locationVarValue = locationVar.lower()

			setVars = []
			unsetVars = []

			# Iterate over the generated controls
			for varName, control in self.varControls.items():
				# Reset style first
				if varName in self.varFrames:
					self.varFrames[varName].setStyleSheet("")

				desiredValue = None
				desiredLabel = None
				if varName in ('Time', 'time'):
					desiredValue = timeOfDayValue
					desiredLabel = timeOfDayLabel
				elif varName in ('Location', 'location'):
					desiredValue = locationVarValue
					desiredLabel = locationVar
				elif varName == 'Engines':
					desiredValue = "Hot" if engineRunning else "Cold"
				elif varName == 'Aircraft':
					desiredValue = dcsModuleName
				if varName in hookVars:
					desiredValue = hookVars[varName]
					desiredLabel = None

				success = False
				if desiredValue or desiredLabel:
					varType = self.varControlTypes.get(varName, 'radio')
					if varType == 'dropdown':
						for i in range(control.count()):
							itemData = control.itemData(i)
							itemText = control.itemText(i)
							if itemData == desiredValue or itemText == desiredLabel or itemText == desiredValue:
								control.setCurrentIndex(i)
								setVars.append(f"{varName}: {desiredLabel or desiredValue}")
								success = True
								break
					elif varType == 'text':
						control.setText(str(desiredValue or desiredLabel))
						setVars.append(f"{varName}: {desiredLabel or desiredValue}")
						success = True
					else:
						for btn in control.buttons():
							btnValue = btn.property('varValue')
							if btnValue is not None and btnValue == desiredValue:
								btn.setChecked(True)
								setVars.append(f"{varName}: {desiredLabel or desiredValue}")
								success = True
								break
							if btn.text() == desiredLabel or btn.text() == desiredValue:
								btn.setChecked(True)
								setVars.append(f"{varName}: {desiredLabel or desiredValue}")
								success = True
								break

				if not success:
					unsetVars.append(varName)
					# Highlight the frame for this variable
					if varName in self.varFrames:
						self.varFrames[varName].setStyleSheet("QFrame { border: 1px solid red; border-radius: 4px; }")

			self.uiTelemetryUnsetVars = set(unsetVars)
			self.uiTelemetryUnsetVarsModule = self.moduleDropdown.currentText()
			self.uiTelemetryUnsetVarsScript = self.scriptDropdown.currentText()

			report = autoSelectReport(dcsModuleName, foundModuleFile, altAGL, altMSL, airspeedTAS, data.get('LoGetEngineInfo', {}), clockSeconds, self.scriptDropdown.currentText(), context.reads, hookResult, setVars, unsetVars)
			self.updateOutput('\n'.join(report) + '\n', flush=True)
			for line in report:
				self._uiSendLog(line)

			return True

		except Exception as e:
			QtWidgets.QMessageBox.critical(self.mainWindow, "Auto Select Error", f"An error occurred: {e}\n{traceback.format_exc()}")
			return False

	def readControlsForAutoSelect(self, moduleName, controls):
		"""Batched live read for an aircraft script's autoSelect(): {control: value} for the controls DCS answered."""
		results = self.dbe.pollControlStates([f'{moduleName}/{control}' for control in controls])
		return {result[0].split('/', 1)[1]: result[2] for result in results}

	def getAircraftName(self):
		control = 'MetadataStart/_ACFT_NAME'
		aircraftName = self.dbe.getControlState(control)
		if aircraftName:
			return aircraftName[0][2].strip()
		else:
			return 'N/A'

	def getMissionTime(self):
		# Not yet implemented for DCSDirectManager.
		return 'N/A'

	def saveSettings(self):
		# Don't save if we don't have a valid module or script selected
		if not self.moduleName or not self.scriptName:
			return

		self.settingsManager.updateLastUsed(self.moduleName, self.scriptName, self.getSelectedVars())

	def openConfigWindow(self):
		configWindow = QtWidgets.QDialog(self.mainWindow)
		configWindow.setWindowTitle('Settings')
		configWindow.resize(700, 550)

		layout = QtWidgets.QVBoxLayout(configWindow)

		def hintLabel(text):
			label = QtWidgets.QLabel(text)
			label.setStyleSheet('color: gray; font-style: italic;')
			return label

		def fieldWithHint(fieldWidgets, hintText):
			# Keeps the gray hint tight under its field, which a separate form row wouldn't
			container = QtWidgets.QWidget()
			containerLayout = QtWidgets.QVBoxLayout(container)
			containerLayout.setContentsMargins(0, 0, 0, 0)
			containerLayout.setSpacing(0)
			row = QtWidgets.QHBoxLayout()
			for widget in fieldWidgets:
				row.addWidget(widget)
			containerLayout.addLayout(row)
			containerLayout.addWidget(hintLabel(hintText))
			return container

		def sliderWithValue(slider):
			container = QtWidgets.QWidget()
			containerLayout = QtWidgets.QHBoxLayout(container)
			containerLayout.setContentsMargins(0, 0, 0, 0)
			valueLabel = QtWidgets.QLabel(str(slider.value()))
			valueLabel.setMinimumWidth(QtGui.QFontMetrics(valueLabel.font()).horizontalAdvance('-100'))
			slider.valueChanged.connect(lambda v: valueLabel.setText(str(v)))
			containerLayout.addWidget(slider)
			containerLayout.addWidget(valueLabel)
			return container

		debugVar = QtWidgets.QCheckBox('Debug - Disables sending data to DCS')
		debugVar.setChecked(self.config.get('debug', False))
		layout.addWidget(debugVar)

		disableSpeechVar = QtWidgets.QCheckBox('Disable Text-to-Speech output')
		disableSpeechVar.setChecked(self.config.get('disableSpeech', False))
		layout.addWidget(disableSpeechVar)

		form = QtWidgets.QFormLayout()
		layout.addLayout(form)

		inGameOverlayHotkeyVar = QtWidgets.QLineEdit(self.config.get('inGameOverlayHotkey', 'Ctrl+Shift+Z'))
		inGameOverlayHotkeyVar.setPlaceholderText('Ctrl+Shift+Z')
		form.addRow('In-game overlay hotkey:', fieldWithHint([inGameOverlayHotkeyVar], 'Ctrl/Alt/Shift only; no LCtrl/RCtrl, etc.'))

		dcsExePathOverrideVar = QtWidgets.QLineEdit(self.config.get('dcsExePathOverride', ''))
		dcsExePathOverrideVar.setPlaceholderText('Default is to get the location from the registry')
		browseExeButton = QtWidgets.QPushButton('Browse')
		browseExeButton.clicked.connect(lambda: self.browseForFile(dcsExePathOverrideVar, "Executable files (*.exe)"))
		dcsExeHint = describeResolvedPath(self.config.get('dcsExePathOverride', ''), self.config.get('dcsExePath', ''))
		form.addRow('DCS executable path:', fieldWithHint([dcsExePathOverrideVar, browseExeButton], dcsExeHint))

		dcsWindowUseTitleVar = QtWidgets.QCheckBox('Find DCS window by window title (otherwise use exe path)')
		dcsWindowUseTitleVar.setChecked(self.config.get('dcsWindowUseTitle', False))
		form.addRow('', dcsWindowUseTitleVar)

		dcsWindowTitleOverrideVar = QtWidgets.QLineEdit(self.config.get('dcsWindowTitleOverride', ''))
		dcsWindowTitleOverrideVar.setPlaceholderText('Default is "Digital Combat Simulator"')
		form.addRow('DCS window title:', dcsWindowTitleOverrideVar)

		def _onUseTitleToggled(checked):
			dcsExePathOverrideVar.setEnabled(not checked)
			browseExeButton.setEnabled(not checked)
			dcsWindowTitleOverrideVar.setEnabled(checked)

		dcsWindowUseTitleVar.toggled.connect(_onUseTitleToggled)
		_onUseTitleToggled(dcsWindowUseTitleVar.isChecked())

		dcsSavedGamesOverrideVar = QtWidgets.QLineEdit(self.config.get('dcsSavedGamesOverride', ''))
		dcsSavedGamesOverrideVar.setPlaceholderText("Default is '%USERPROFILE%\\Saved Games\\DCS' or 'DCS.openbeta'")
		browseSavedGamesButton = QtWidgets.QPushButton('Browse')
		browseSavedGamesButton.clicked.connect(lambda: self.browseForDirectory(dcsSavedGamesOverrideVar))
		dcsSavedGamesHint = describeResolvedPath(
			self.config.get('dcsSavedGamesOverride', ''),
			self.config.get('dcsSavedGamesPath', ''),
			self.config.get('dcsSavedGamesAmbiguous', False),
		)
		form.addRow('DCS Saved Games folder path:', fieldWithHint([dcsSavedGamesOverrideVar, browseSavedGamesButton], dcsSavedGamesHint))

		# Get available TTS voices
		voiceNames = []
		try:
			import win32com.client
			speaker = win32com.client.Dispatch("SAPI.SpVoice")
			voices = speaker.GetVoices()
			voiceNames = [voice.GetAttribute("Name") for voice in voices]
		except Exception as e:
			print(f"Error enumerating TTS voices: {e}")
			voiceNames = ["MS David", "MS Hazel", "MS Zira"]  # Fallback defaults

		ttsGroup = QtWidgets.QGroupBox('Text-to-Speech')
		ttsForm = QtWidgets.QFormLayout(ttsGroup)
		layout.addWidget(ttsGroup)

		ttsVoiceCombo = QtWidgets.QComboBox()
		ttsVoiceCombo.addItems(voiceNames)
		ttsVoiceCombo.setCurrentIndex(min(self.config.get('ttsVoiceId', 1), len(voiceNames) - 1))
		ttsForm.addRow('Voice:', ttsVoiceCombo)

		ttsRateSlider = QtWidgets.QSlider(QtCore.Qt.Orientation.Horizontal)
		ttsRateSlider.setRange(-10, 10)
		ttsRateSlider.setValue(self.config.get('ttsRate', 3))
		ttsForm.addRow('Rate:', sliderWithValue(ttsRateSlider))

		ttsVolumeSlider = QtWidgets.QSlider(QtCore.Qt.Orientation.Horizontal)
		ttsVolumeSlider.setRange(0, 100)
		ttsVolumeSlider.setValue(self.config.get('ttsVolume', 75))
		ttsForm.addRow('Volume:', sliderWithValue(ttsVolumeSlider))

		previewButton = QtWidgets.QPushButton('Preview Voice')
		previewButton.clicked.connect(lambda: self.previewTTS(ttsVoiceCombo.currentIndex(), ttsRateSlider.value(), ttsVolumeSlider.value()))
		previewRow = QtWidgets.QWidget()
		previewRowLayout = QtWidgets.QHBoxLayout(previewRow)
		previewRowLayout.setContentsMargins(0, 0, 0, 0)
		previewRowLayout.addWidget(previewButton)
		previewRowLayout.addStretch()
		ttsForm.addRow('', previewRow)

		portsGroup = QtWidgets.QGroupBox('Network Communication Ports')
		portsForm = QtWidgets.QFormLayout(portsGroup)
		portsForm.setFieldGrowthPolicy(QtWidgets.QFormLayout.FieldGrowthPolicy.FieldsStayAtSizeHint)
		layout.addWidget(portsGroup)

		def portSpinBox(configKey, defaultPort):
			spinBox = QtWidgets.QSpinBox()
			spinBox.setRange(1, 65535)
			spinBox.setValue(int(self.config.get(configKey, defaultPort)))
			return spinBox

		uiRemoteControlPortVar = portSpinBox('uiRemoteControlPort', 7786)
		portsForm.addRow('UI Remote Control Port:', uiRemoteControlPortVar)
		uiRemoteControlReplyPortVar = portSpinBox('uiRemoteControlReplyPort', 7779)
		portsForm.addRow('UI Remote Control Reply Port:', uiRemoteControlReplyPortVar)
		dcsAutoMateUdpPortVar = portSpinBox('dcsAutoMateUdpPort', 6121)
		portsForm.addRow('DCS AutoMate UDP Port:', dcsAutoMateUdpPortVar)
		dcsDirectPortVar = portSpinBox('dcsDirectPort', 7780)
		portsForm.addRow('DCS Direct TCP Port:', dcsDirectPortVar)

		loggingGroup = QtWidgets.QGroupBox('Logging')
		loggingLayout = QtWidgets.QVBoxLayout(loggingGroup)
		layout.addWidget(loggingGroup)

		udpUiWireLogEnabledVar = QtWidgets.QCheckBox('Log in-game overlay network traffic in DCSAutoMate (DCSAutoMateLog.txt)')
		udpUiWireLogEnabledVar.setChecked(self.config.get('udpUiWireLogEnabled', False))
		loggingLayout.addWidget(udpUiWireLogEnabledVar)

		hookLogFileVar = QtWidgets.QCheckBox('Write DCS hook log file (Saved Games\\DCS\\Logs\\DCSAutoMateHook.log)')
		hookDebugLogVar = QtWidgets.QCheckBox('Include debug messages')
		hookUiWireLogVar = QtWidgets.QCheckBox('Log in-game overlay network traffic in DCS')

		hookSettingsPath = ''
		dcsSavedGamesPath = self.config.get('dcsSavedGamesPath', '')
		if dcsSavedGamesPath:
			hookSettingsPath = os.path.join(dcsSavedGamesPath, 'Scripts', 'DCSAutoMate', 'DCSAutoMateHookSettings.lua')
		try:
			hookSettings = readHookSettings(hookSettingsPath)
		except (OSError, UnicodeDecodeError) as e:
			hookSettings = dict(HOOK_SETTINGS_DEFAULTS)
			QtWidgets.QMessageBox.warning(
				self.mainWindow,
				'DCS Hook Settings Not Read',
				f'Could not read {hookSettingsPath}:\n{e}\n\nThe DCS hook logging options show default values.',
			)
		hookLogFileVar.setChecked(hookSettings['isHookLogFileEnabled'])
		hookDebugLogVar.setChecked(hookSettings['isDebugLoggingEnabled'])
		hookUiWireLogVar.setChecked(hookSettings['isUiWireLoggingEnabled'])

		loggingLayout.addWidget(hookLogFileVar)
		# The hook writes debug and wire messages to its log file, so they need it enabled
		hookLogOptions = QtWidgets.QWidget()
		hookLogOptionsLayout = QtWidgets.QVBoxLayout(hookLogOptions)
		hookLogOptionsLayout.setContentsMargins(20, 0, 0, 0)
		hookLogOptionsLayout.addWidget(hookDebugLogVar)
		hookLogOptionsLayout.addWidget(hookUiWireLogVar)
		loggingLayout.addWidget(hookLogOptions)
		hookLogFileVar.toggled.connect(hookLogOptions.setEnabled)
		hookLogOptions.setEnabled(hookLogFileVar.isChecked())

		# Buttons
		buttonFrame = QtWidgets.QFrame()
		buttonLayout = QtWidgets.QHBoxLayout(buttonFrame)
		layout.addWidget(buttonFrame)

		saveButton = QtWidgets.QPushButton('Save')
		saveButton.clicked.connect(lambda: self.saveConfig(
			debugVar,
			disableSpeechVar,
			ttsVoiceCombo,
			ttsRateSlider,
			ttsVolumeSlider,
			udpUiWireLogEnabledVar,
			uiRemoteControlPortVar,
			uiRemoteControlReplyPortVar,
			dcsAutoMateUdpPortVar,
			dcsDirectPortVar,
			inGameOverlayHotkeyVar,
			dcsWindowUseTitleVar,
			dcsExePathOverrideVar,
			dcsWindowTitleOverrideVar,
			dcsSavedGamesOverrideVar,
			hookLogFileVar,
			hookDebugLogVar,
			hookUiWireLogVar,
			configWindow
		))
		buttonLayout.addWidget(saveButton)

		cancelButton = QtWidgets.QPushButton('Cancel')
		cancelButton.clicked.connect(configWindow.reject)
		buttonLayout.addWidget(cancelButton)

		configWindow.exec()

	def browseForFile(self, lineEdit, fileFilter):
		fileName, _ = QtWidgets.QFileDialog.getOpenFileName(self.mainWindow, filter=fileFilter)
		if fileName:
			lineEdit.setText(QtCore.QDir.toNativeSeparators(fileName))

	def browseForDirectory(self, lineEdit):
		dirName = QtWidgets.QFileDialog.getExistingDirectory(self.mainWindow)
		if dirName:
			lineEdit.setText(QtCore.QDir.toNativeSeparators(dirName))

	def openProgramFolder(self):
		"""Open the program folder in Windows Explorer."""
		try:
			# Get the directory where the program is running
			if getattr(sys, 'frozen', False):
				# Running as exe
				programDir = os.path.dirname(sys.executable)
			else:
				# Running as script
				programDir = os.path.dirname(os.path.abspath(__file__))

			# Open folder in Windows Explorer (don't check exit code as Explorer can return non-zero even on success)
			subprocess.run(['explorer', programDir])
		except Exception as e:
			QtWidgets.QMessageBox.warning(self.mainWindow, "Error", f"Could not open program folder: {e}")

	def refreshControlReference(self):
		"""Rebuild the control reference page's data if a control mapping changed; returns False if it couldn't be built."""
		try:
			if updateControlReference():
				self.log('Rebuilt the control reference data from the control mappings.')
			return True
		except Exception as e:
			self.log(f'Could not build the control reference data: {e}')
			return False

	def openControlReference(self):
		if not self.refreshControlReference():
			QtWidgets.QMessageBox.warning(self.mainWindow, 'Error', 'Could not build the control reference data, see the log for details.')
			return
		QtGui.QDesktopServices.openUrl(QtCore.QUrl.fromLocalFile(controlReferencePaths()[2]))

	def installDcsScripts(self):
		hotkey = self.normalizeInGameOverlayHotkey(self.settingsManager.config.get('inGameOverlayHotkey', 'Ctrl+Shift+Z'))
		DcsScriptsInstaller.installFromUi(self.mainWindow, self.settingsManager.config, hotkey)

	def normalizeInGameOverlayHotkey(self, hotkeyText):
		text = str(hotkeyText or '').strip()
		if text == '':
			return 'Ctrl+Shift+Z'
		parts = [p.strip() for p in text.split('+') if p.strip() != '']
		normalizedParts = []
		for part in parts:
			key = str(part)
			keyLower = key.lower()
			if keyLower in ('lctrl', 'rctrl', 'ctrl', 'control'):
				key = 'Ctrl'
			elif keyLower in ('lshift', 'rshift', 'shift'):
				key = 'Shift'
			elif keyLower in ('lalt', 'ralt', 'alt'):
				key = 'Alt'
			elif len(key) == 1 and key.isalpha():
				key = key.upper()
			normalizedParts.append(key)

		uniqueParts = []
		seen = set()
		for part in normalizedParts:
			partLower = part.lower()
			if partLower in seen:
				continue
			seen.add(partLower)
			uniqueParts.append(part)
		return '+'.join(uniqueParts) if uniqueParts else 'Ctrl+Shift+Z'

	def writeHookSettingsFile(self, hookLogFile, hookDebugLog, hookUiWireLog):
		dcsSavedGamesPath = str(self.settingsManager.config.get('dcsSavedGamesPath') or '')
		if dcsSavedGamesPath == '' or not os.path.isdir(dcsSavedGamesPath):
			return
		settingsDir = os.path.join(dcsSavedGamesPath, 'Scripts', 'DCSAutoMate')
		try:
			os.makedirs(settingsDir, exist_ok=True)
			settingsPath = os.path.join(settingsDir, 'DCSAutoMateHookSettings.lua')
			hotkey = self.normalizeInGameOverlayHotkey(self.settingsManager.config.get('inGameOverlayHotkey', 'Ctrl+Shift+Z'))
			content = f"""return {{
	hotkeys = {{
		'{hotkey}',
	}},
	isHookLogFileEnabled = {str(hookLogFile).lower()},
	isDebugLoggingEnabled = {str(hookDebugLog).lower()},
	isUiWireLoggingEnabled = {str(hookUiWireLog).lower()},
	uiRemoteControlPort = {self.config.get('uiRemoteControlPort', 7786)},
	uiRemoteControlReplyPort = {self.config.get('uiRemoteControlReplyPort', 7779)},
}}
"""
			with open(settingsPath, 'w', encoding='utf-8') as f:
				f.write(content)
			exportSettingsPath = os.path.join(settingsDir, 'DCSAutoMateExportSettings.lua')
			exportContent = f"""return {{
	udpPort = {self.config.get('dcsAutoMateUdpPort', 6121)},
	tcpPort = {self.config.get('dcsDirectPort', 7780)},
}}
"""
			with open(exportSettingsPath, 'w', encoding='utf-8') as f:
				f.write(exportContent)
		except OSError as e:
			QtWidgets.QMessageBox.warning(
				self.mainWindow,
				'DCS Settings Not Saved',
				f'Could not write the DCS-side settings files in {settingsDir}:\n{e}\n\nThe DCS hook logging options and port settings were not updated in DCS.',
			)

	def saveConfig(self, debugVar, disableSpeechVar, ttsVoiceCombo, ttsRateSlider, ttsVolumeSlider, udpUiWireLogEnabledVar, uiRemoteControlPortVar, uiRemoteControlReplyPortVar, dcsAutoMateUdpPortVar, dcsDirectPortVar, inGameOverlayHotkeyVar, dcsWindowUseTitleVar, dcsExePathOverrideVar, dcsWindowTitleOverrideVar, dcsSavedGamesOverrideVar, hookLogFileVar, hookDebugLogVar, hookUiWireLogVar, configWindow):
		newConfig = {
			'debug': debugVar.isChecked(),
			'disableSpeech': disableSpeechVar.isChecked(),
			'ttsVoiceId': ttsVoiceCombo.currentIndex(),
			'ttsRate': ttsRateSlider.value(),
			'ttsVolume': ttsVolumeSlider.value(),
			'udpUiWireLogEnabled': udpUiWireLogEnabledVar.isChecked(),
			'enableNetworkLogging': udpUiWireLogEnabledVar.isChecked(),
			'uiRemoteControlPort': uiRemoteControlPortVar.value(),
			'uiRemoteControlReplyPort': uiRemoteControlReplyPortVar.value(),
			'dcsAutoMateUdpPort': dcsAutoMateUdpPortVar.value(),
			'dcsDirectPort': dcsDirectPortVar.value(),
			'inGameOverlayHotkey': self.normalizeInGameOverlayHotkey(inGameOverlayHotkeyVar.text()),
			'dcsWindowUseTitle': dcsWindowUseTitleVar.isChecked(),
			'dcsExePathOverride': dcsExePathOverrideVar.text(),
			'dcsWindowTitleOverride': dcsWindowTitleOverrideVar.text(),
			'dcsSavedGamesOverride': dcsSavedGamesOverrideVar.text()
		}

		self.settingsManager.saveConfig(newConfig)
		self.config = self.settingsManager.config
		self.ttsManager.updateSettings(self.config)  # Update TTS with new settings
		self.writeHookSettingsFile(hookLogFileVar.isChecked(), hookDebugLogVar.isChecked(), hookUiWireLogVar.isChecked())
		configWindow.accept()

	def previewTTS(self, voiceId, rate, volume):
		try:
			import win32com.client
			speaker = win32com.client.Dispatch("SAPI.SpVoice")
			voices = speaker.GetVoices()
			if voiceId < voices.Count:
				speaker.Voice = voices.Item(voiceId)
			speaker.Rate = rate
			speaker.Volume = volume
			speaker.Speak("This is a preview of the selected voice settings.", 0)  # Synchronous for preview
		except Exception as e:
			QtWidgets.QMessageBox.warning(self.mainWindow, "TTS Preview Error", f"Error previewing TTS: {e}")

	def updateUIState(self):
		isRunning = getattr(self, 'scriptRunning', False)
		isPaused = getattr(self, 'scriptPaused', False)
		moduleSelected = bool(self.moduleDropdown.currentText())
		scriptSelected = bool(self.scriptDropdown.currentText())

		self.moduleDropdown.setEnabled(not isRunning)
		self.scriptDropdown.setEnabled(not isRunning)
		self.autoSelectButton.setEnabled(not isRunning)

		if hasattr(self, 'varControls'):
			for control in self.varControls.values():
				control.setEnabled(not isRunning)

		if isRunning:
			self.startButton.setEnabled(True)
			self.startButton.setText('Resume' if isPaused else 'Pause')
			self.stopButton.setEnabled(True)
		else:
			self.startButton.setEnabled(moduleSelected and scriptSelected)
			self.startButton.setText('Start')
			self.stopButton.setEnabled(False)
		self.skipWaitButton.setEnabled(isRunning and self.scriptWaiting)

		# Send state to DCS Overlay
		self._uiSendScriptState()

	def updateModulesDropdown(self, modules):
		self.moduleDropdown.clear()
		self.moduleDropdown.addItems(modules)
		if modules:
			self.moduleDropdown.setCurrentIndex(0)
		self.adjustDropdownWidths()  # Adjust width after populating
		self.updateUIState()

	def updateScriptDropdown(self, scriptData):
		self.scriptDropdown.clear()
		scriptNames = [s['name'] for s in scriptData['scripts']]
		self.scriptDropdown.addItems(scriptNames)
		if scriptData['scripts']:
			self.scriptDropdown.setCurrentIndex(0)
		self.adjustDropdownWidths()  # Adjust width after populating
		self.updateUIState()

	def getSelectedVars(self):
		if self.varControls:
			result = {}
			for var in self.varControls:
				selectedValue = self.getVarValue(var)
				if selectedValue is not None:
					result[var] = selectedValue
			return result
		else:
			return {}

	def updateOutput(self, text, flush=False):
		if text != '':
			# Move cursor to end and insert text without automatic newline
			cursor = self.outputBox.textCursor()
			cursor.movePosition(QtGui.QTextCursor.MoveOperation.End)
			cursor.insertText(text)
			self.outputBox.setTextCursor(cursor)
			# Ensure the text box scrolls to show the new content
			self.outputBox.ensureCursorVisible()

		if flush:
			QtWidgets.QApplication.processEvents() # Forces the output textbox to update.

	def onStartPauseClick(self):
		if not self.scriptRunning:
			self.runScript()
		elif not self.scriptPaused:
			self.pauseScript()
		else:
			self.resumeScript()

	def pauseScript(self):
		if not self.scriptRunning or self.scriptPaused:
			return
		self.scriptPaused = True
		self.resumeEvent.clear()
		self.updateOutput('\n--- Script execution paused. ---\n', flush=True)
		self.updateUIState()

	def resumeScript(self):
		if not self.scriptRunning or not self.scriptPaused:
			return
		self.scriptPaused = False
		self.resumeEvent.set()
		self.updateOutput('\n--- Script execution resumed. ---\n', flush=True)
		self.updateUIState()

	def skipWait(self):
		if self.scriptRunning and self.scriptWaiting:
			self.skipWaitEvent.set()

	def onWaitStateChanged(self, waiting):
		self.scriptWaiting = waiting
		self.updateUIState()

	def runScript(self):
		self.saveSettings()
		self._uiSendClear()  # Clear the ingame overlay monitor text box
		moduleName = self.moduleDropdown.currentText()
		scriptName = self.scriptDropdown.currentText()
		vars = self.getSelectedVars()
		try:
			self.SeqHelperFunctions.setActiveModuleName(moduleName)
			self.SeqHelperFunctions.setActiveScriptName(scriptName)
			scriptFunction, module = self.scriptManager.loadScriptFunction(moduleName, scriptName)

			if not scriptFunction:
				raise Exception(f"Could not load script function for {scriptName}")

			# Runs the script function to get the sequence of commands, or a live script's generator.
			seq = scriptFunction(self.config, vars, self.SeqHelperFunctions)
			self.outputBox.clear()
			self.stopFlag.clear()

			self.scriptRunning = True
			self.scriptPaused = False
			self.resumeEvent.set()
			self.updateUIState()
			QtWidgets.QApplication.processEvents()

			scriptInfo = self.scriptManager.getScriptInfo(module)
			if scriptInfo:
				self.updateOutput(f'Script info: {scriptInfo}\n\n')
				self._uiSendLog(f'Script info: {scriptInfo}')

			seqExe = DCSSeqExecute(self.mainWindow, self.config, self.dbe, self.scriptData, vars, self.updateOutput, self.stopFlag, self.log, self.ttsManager, self._uiSendLog, self.resumeEvent, self.pauseScript, self.skipWaitEvent, self.onWaitStateChanged)
			seqExe.execute(seq, self.SeqHelperFunctions)
		except Exception as e:
			self.updateOutput('Error occurred:\n')
			self.updateOutput(traceback.format_exc())
			# The player may only be watching the in-game overlay, so tell them there too.
			self._uiSendLog(f'Script error: {type(e).__name__}: {e}')
			self._uiSendLog('See the desktop window for details.')
			self.ttsManager.speak('Script error.  Please check the desktop window.')
		finally:
			self.scriptRunning = False
			self.scriptPaused = False
			self.scriptWaiting = False
			self.skipWaitEvent.clear()
			self.resumeEvent.set() # Ensure any waiting threads are released
			self.updateUIState()

	def stopScript(self):
		self.stopFlag.set()
		self.resumeEvent.set() # Ensure we don't hang if paused
		self.updateUIState()

	def log(self, *args):
		logFilePath = 'DCSAutoMateLog.txt'
		if not self.logInitialized:
			# Initialize log file
			with open(logFilePath, 'w') as logFile:
				logFile.write('')  # Create an empty log file
			self.logInitialized = True

		# Get caller information
		frame = inspect.currentframe().f_back
		fileName = os.path.basename(frame.f_code.co_filename)
		lineNumber = frame.f_lineno

		# Create timestamp
		timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

		# Format log message
		message = ' '.join(map(str, args))

		# Write to log file
		with open(logFilePath, 'a') as logFile:
			logFile.write(f'{timestamp} - {fileName}:{lineNumber} - {message}\n')

###############################################################################
###############################################################################
###############################################################################

if __name__ == '__main__':
	# When running this program as an exe, we need to have its own path appended to the sys.path in order for it to find script files in the DCSAutoMateScripts subfolder.
	applicationPath = os.path.dirname(sys.executable)
	sys.path.append(applicationPath)

	app = QtWidgets.QApplication(sys.argv)
	dcsApp = DCSAutoMateApp()
	dcsApp.mainWindow.show()
	sys.exit(app.exec())
