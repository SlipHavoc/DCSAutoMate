import json
import os
from PySide6 import QtWidgets

HOOK_SETTINGS_DEFAULTS = {
	'isHookLogFileEnabled': False,
	'isDebugLoggingEnabled': False,
	'isUiWireLoggingEnabled': False,
}


def describeResolvedPath(overridePath, resolvedPath, ambiguous=False):
	"""Status text shown under a path field in the Settings window."""
	if overridePath:
		expandedOverride = os.path.normcase(os.path.normpath(os.path.expandvars(overridePath)))
		if resolvedPath and os.path.normcase(resolvedPath) == expandedOverride:
			return f'Using: {resolvedPath}'
		if resolvedPath:
			return f'Override not found; using detected: {resolvedPath}'
		return 'Override not found'
	if not resolvedPath:
		return 'Not detected'
	if ambiguous:
		return f'More than one detected; using: {resolvedPath}'
	return f'Detected: {resolvedPath}'


def readHookSettings(path):
	"""Read the hook's logging flags.  A missing file gives defaults; read errors propagate."""
	if not path or not os.path.exists(path):
		return dict(HOOK_SETTINGS_DEFAULTS)
	with open(path, 'r', encoding='utf-8') as f:
		content = f.read()
	return {key: f'{key} = true' in content for key in HOOK_SETTINGS_DEFAULTS}

class SettingsManager:
	SETTINGS_FILE = os.path.join('config', 'DCSAutoMateSettings.json')
	CONFIG_FILE = os.path.join('config', 'DCSAutoMateConfig.json')
	PATH_OVERRIDE_KEYS = ('dcsExePathOverride', 'dcsSavedGamesOverride')

	def normalizePathOverrides(self, config):
		for key in self.PATH_OVERRIDE_KEYS:
			if config.get(key):
				config[key] = os.path.normpath(config[key])

	def __init__(self, parentWindow=None):
		self.parentWindow = parentWindow
		self.settings = self.loadSettings()
		# Internal attributes for saved-games ambiguity detection
		self._dcsSavedGamesOptions = []
		self._dcsSavedGamesAmbiguous = False
		self.config = self.loadConfig()

	def getDefaultConfig(self):
		return {
			'debug': False,
			'enableNetworkLogging': False,
			'udpUiWireLogEnabled': False,
			'udpUiWireLogFilter': 'ui',
			'udpUiWireLogMaxChars': 4000,
			'udpBiosWireLogEnabled': False,
			'udpBiosWireLogMaxChars': 200,
			'disableSpeech': False,
			'ttsVoiceId': 1,
			'ttsRate': 3,
			'ttsVolume': 75,
			'inGameOverlayHotkey': 'Ctrl+Shift+Z',
			'dcsWindowUseTitle': False,
			'dcsExePathOverride': '',
			'dcsWindowTitleOverride': '',
			'dcsSavedGamesOverride': ''
		}

	def loadConfig(self):
		config = self.getDefaultConfig()
		try:
			# If the config file doesn't exist, create it with the default config.
			if not os.path.isfile(self.CONFIG_FILE):
				with open(self.CONFIG_FILE, 'w') as file:
					file.write(json.dumps(config, indent=4))
		except Exception as e:
			if self.parentWindow:
				QtWidgets.QMessageBox.critical(self.parentWindow, "Error", f"Error writing default config to {self.CONFIG_FILE}: {e}.")

		try:
			with open(self.CONFIG_FILE) as file:
				loadedConfig = json.load(file)
				# Update default config with loaded values to ensure all keys exist
				config.update(loadedConfig)
		except Exception as e:
			if self.parentWindow:
				QtWidgets.QMessageBox.critical(self.parentWindow, "Error", f"Error loading config from {self.CONFIG_FILE}: {e}.\nPlease check the file for syntax errors, or delete it to create a new one.")

		# Backwards compatibility: if the legacy network logging flag exists but the new UI flag
		# was never written, treat enableNetworkLogging as the UI wire-log toggle.
		try:
			if isinstance(locals().get('loadedConfig', None), dict):
				if 'udpUiWireLogEnabled' not in loadedConfig:
					config['udpUiWireLogEnabled'] = bool(config.get('enableNetworkLogging', False))
		except Exception:
			pass

		self.normalizePathOverrides(config)

		# Detect DCS Saved Games path
		config['dcsSavedGamesPath'] = self.detectSavedGamesPath(config.get('dcsSavedGamesOverride', ''))
		# Preserve ambiguity metadata set by detectSavedGamesPath
		config['dcsSavedGamesOptions'] = getattr(self, '_dcsSavedGamesOptions', [])
		config['dcsSavedGamesAmbiguous'] = getattr(self, '_dcsSavedGamesAmbiguous', False)

		# Detect DCS Install path
		config['dcsExePath'] = self.detectDCSInstallPath(config.get('dcsExePathOverride', ''))

		return config

	def detectSavedGamesPath(self, overridePath):
		# Clear previous metadata
		self._dcsSavedGamesOptions = []
		self._dcsSavedGamesAmbiguous = False
		if overridePath:
			path = os.path.expandvars(overridePath)
			if os.path.exists(path):
				self._dcsSavedGamesOptions = [path]
				return path
			# If override provided but doesn't exist, return empty.
			return ''

		# Look in the default paths and collect all that exist.
		userProfile = os.environ.get('USERPROFILE', '')
		dcsSavedGamesPaths = [
			os.path.join(userProfile, 'Saved Games', 'DCS'),
			os.path.join(userProfile, 'Saved Games', 'DCS.openbeta'),
		]
		existing = []
		for path in dcsSavedGamesPaths:
			if os.path.exists(path):
				existing.append(path)

		if len(existing) == 1:
			self._dcsSavedGamesOptions = existing
			self._dcsSavedGamesAmbiguous = False
			return existing[0]
		elif len(existing) > 1:
			self._dcsSavedGamesOptions = existing
			self._dcsSavedGamesAmbiguous = True
			# Return the first existing path (to allow startup to proceed), but keep ambiguity flag set
			return existing[0]
		else:
			self._dcsSavedGamesOptions = []
			self._dcsSavedGamesAmbiguous = False
			return ''

	def detectDCSInstallPath(self, overridePath):
		if overridePath:
			if os.path.exists(overridePath):
				return overridePath

		import winreg
		try:
			# Try OpenBeta first
			key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Eagle Dynamics\DCS World OpenBeta")
			path, _ = winreg.QueryValueEx(key, "Path")
			# Check for bin-mt first (multithreading)
			exePath = os.path.join(path, "bin-mt", "DCS.exe")
			if os.path.exists(exePath):
				return exePath
			# Check for bin
			exePath = os.path.join(path, "bin", "DCS.exe")
			if os.path.exists(exePath):
				return exePath
		except:
			pass

		try:
			# Try Stable
			key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Eagle Dynamics\DCS World")
			path, _ = winreg.QueryValueEx(key, "Path")
			# Check for bin-mt first
			exePath = os.path.join(path, "bin-mt", "DCS.exe")
			if os.path.exists(exePath):
				return exePath
			# Check for bin
			exePath = os.path.join(path, "bin", "DCS.exe")
			if os.path.exists(exePath):
				return exePath
		except:
			pass

		return ''

	def saveConfig(self, newConfig):
		self.config.update(newConfig)
		self.normalizePathOverrides(self.config)

		# Re-detect paths based on new config
		self.config['dcsSavedGamesPath'] = self.detectSavedGamesPath(self.config.get('dcsSavedGamesOverride', ''))
		self.config['dcsExePath'] = self.detectDCSInstallPath(self.config.get('dcsExePathOverride', ''))
		# Preserve ambiguity metadata
		self.config['dcsSavedGamesOptions'] = getattr(self, '_dcsSavedGamesOptions', [])
		self.config['dcsSavedGamesAmbiguous'] = getattr(self, '_dcsSavedGamesAmbiguous', False)

		try:
			with open(self.CONFIG_FILE, 'w') as file:
				file.write(json.dumps(self.config, indent=4))
		except Exception as e:
			if self.parentWindow:
				QtWidgets.QMessageBox.critical(self.parentWindow, "Error", f"Error saving config: {e}")

	def loadSettings(self):
		settings = {
			'lastUsedModule': '',
			'lastUsedScripts': {},
		}
		try:
			if os.path.exists(self.SETTINGS_FILE):
				with open(self.SETTINGS_FILE, 'r') as f:
					settings = json.load(f)
		except Exception as e:
			if self.parentWindow:
				QtWidgets.QMessageBox.critical(self.parentWindow, "Error", f"Error loading settings from {self.SETTINGS_FILE}: {e}.\nPlease check the file for syntax errors, or delete it to create a new one.")
		return settings

	def saveSettings(self):
		try:
			with open(self.SETTINGS_FILE, 'w') as file:
				json.dump(self.settings, file, indent=4)
		except Exception as e:
			if self.parentWindow:
				QtWidgets.QMessageBox.critical(self.parentWindow, "Error", f"Error saving settings: {e}")

	def updateLastUsed(self, moduleName, scriptName, varsDict):
		self.settings['lastUsedModule'] = moduleName
		moduleData = self.settings['lastUsedScripts'].get(moduleName)
		if not isinstance(moduleData, dict):
			moduleData = {}
		moduleData['script'] = scriptName
		scriptsData = moduleData.get('scripts')
		if not isinstance(scriptsData, dict):
			scriptsData = {}
		moduleData['scripts'] = scriptsData
		scriptData = scriptsData.get(scriptName)
		if not isinstance(scriptData, dict):
			scriptData = {}
		scriptData['vars'] = varsDict
		scriptsData[scriptName] = scriptData
		if 'vars' in moduleData:
			del moduleData['vars']
		self.settings['lastUsedScripts'][moduleName] = moduleData

		self.saveSettings()

	def updateLastUsedRoute(self, moduleName, scriptName, mapName, routeName):
		if not moduleName or not scriptName:
			return
		moduleData = self.settings['lastUsedScripts'].get(moduleName)
		if not isinstance(moduleData, dict):
			moduleData = {
				'script': '',
				'scripts': {},
			}
		if not isinstance(moduleData.get('scripts'), dict):
			moduleData['scripts'] = {}
		scriptData = moduleData['scripts'].get(scriptName)
		if not isinstance(scriptData, dict):
			scriptData = {}
		scriptData['routes'] = {
			'map': mapName,
			'route': routeName,
		}
		moduleData['scripts'][scriptName] = scriptData
		if 'routes' in moduleData:
			del moduleData['routes']
		self.settings['lastUsedScripts'][moduleName] = moduleData

		if 'lastUsedRoutes' in self.settings:
			del self.settings['lastUsedRoutes']

		self.saveSettings()

	def getLastUsedRoute(self, moduleName, scriptName):
		moduleData = self.settings.get('lastUsedScripts', {}).get(moduleName)
		if not isinstance(moduleData, dict):
			return None, None

		scriptsData = moduleData.get('scripts')
		if isinstance(scriptsData, dict):
			scriptData = scriptsData.get(scriptName)
			if isinstance(scriptData, dict):
				routesData = scriptData.get('routes')
				if isinstance(routesData, dict):
					return routesData.get('map'), routesData.get('route')

		legacyRoutes = moduleData.get('routes')
		if isinstance(legacyRoutes, dict):
			return legacyRoutes.get('map'), legacyRoutes.get('route')

		return None, None

	def getLastUsedModule(self):
		return self.settings.get('lastUsedModule', '')

	def getLastUsedScriptName(self, moduleName):
		moduleData = self.settings['lastUsedScripts'].get(moduleName)
		if isinstance(moduleData, dict):
			return moduleData.get('script', '')
		return ''

	def getLastUsedVars(self, moduleName, scriptName):
		moduleData = self.settings['lastUsedScripts'].get(moduleName)
		if isinstance(moduleData, dict):
			scriptsData = moduleData.get('scripts')
			if isinstance(scriptsData, dict):
				scriptData = scriptsData.get(scriptName)
				if isinstance(scriptData, dict):
					varsData = scriptData.get('vars')
					if isinstance(varsData, dict):
						return varsData

			legacyVars = moduleData.get('vars')
			if moduleData.get('script') == scriptName and isinstance(legacyVars, dict):
				return legacyVars
		return {}
