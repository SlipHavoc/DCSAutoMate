"""Tests for utils.SettingsManager — config logic, path detection, settings round-trips."""
import json
import os
import sys
from unittest.mock import patch, MagicMock

import pytest

# Stub PySide6 so the module can be imported without Qt installed in CI.
sys.modules.setdefault('PySide6', type(sys)('PySide6'))
_qtw = type(sys)('PySide6.QtWidgets')
_qtw.QMessageBox = MagicMock()
sys.modules.setdefault('PySide6.QtWidgets', _qtw)

from utils.SettingsManager import SettingsManager, describeResolvedPath, readHookSettings, HOOK_SETTINGS_DEFAULTS


@pytest.fixture
def manager(tempConfigDir, monkeypatch):
	"""Create a SettingsManager that uses temp files so nothing real is touched."""
	monkeypatch.setattr(SettingsManager, 'CONFIG_FILE', tempConfigDir['configFile'])
	monkeypatch.setattr(SettingsManager, 'SETTINGS_FILE', tempConfigDir['settingsFile'])
	# Prevent detectSavedGamesPath and detectDCSInstallPath from touching the real filesystem.
	monkeypatch.setattr(SettingsManager, 'detectSavedGamesPath', lambda self, p: '')
	monkeypatch.setattr(SettingsManager, 'detectDCSInstallPath', lambda self, p: '')
	return SettingsManager()


# -----------------------------------------------------------------------
# getDefaultConfig
# -----------------------------------------------------------------------

class TestGetDefaultConfig:
	def test_returnsDict(self, manager):
		cfg = manager.getDefaultConfig()
		assert isinstance(cfg, dict)

	def test_hasExpectedKeys(self, manager):
		cfg = manager.getDefaultConfig()
		expectedKeys = [
			'debug', 'enableNetworkLogging', 'udpUiWireLogEnabled',
			'disableSpeech', 'ttsVoiceId', 'ttsRate', 'ttsVolume',
			'inGameOverlayHotkey', 'dcsWindowUseTitle',
			'dcsExePathOverride', 'dcsWindowTitleOverride', 'dcsSavedGamesOverride',
		]
		for key in expectedKeys:
			assert key in cfg, f'Missing expected key: {key}'

	def test_defaultDebugIsFalse(self, manager):
		assert manager.getDefaultConfig()['debug'] is False


# -----------------------------------------------------------------------
# loadConfig / saveConfig round-trip
# -----------------------------------------------------------------------

class TestLoadSaveConfig:
	def test_createsDefaultFile(self, manager, tempConfigDir):
		"""loadConfig should create the config file if it doesn't exist."""
		assert os.path.isfile(tempConfigDir['configFile'])

	def test_loadedConfigHasDefaults(self, manager):
		defaults = manager.getDefaultConfig()
		for key, value in defaults.items():
			assert key in manager.config

	def test_saveAndReload(self, manager, tempConfigDir, monkeypatch):
		"""After saving a changed value, reloading should see the change."""
		manager.config['ttsVolume'] = 99
		manager.saveConfig(manager.config)

		# Create a fresh manager pointing at the same files.
		monkeypatch.setattr(SettingsManager, 'CONFIG_FILE', tempConfigDir['configFile'])
		monkeypatch.setattr(SettingsManager, 'SETTINGS_FILE', tempConfigDir['settingsFile'])
		monkeypatch.setattr(SettingsManager, 'detectSavedGamesPath', lambda self, p: '')
		monkeypatch.setattr(SettingsManager, 'detectDCSInstallPath', lambda self, p: '')
		mgr2 = SettingsManager()
		assert mgr2.config['ttsVolume'] == 99


# -----------------------------------------------------------------------
# Override paths use Windows separators
# -----------------------------------------------------------------------

class TestOverridePathSeparators:
	"""Qt file dialogs return forward slashes; the config should show backslashes like other Windows programs."""

	def _newManager(self, tempConfigDir, monkeypatch):
		monkeypatch.setattr(SettingsManager, 'CONFIG_FILE', tempConfigDir['configFile'])
		monkeypatch.setattr(SettingsManager, 'SETTINGS_FILE', tempConfigDir['settingsFile'])
		monkeypatch.setattr(SettingsManager, 'detectSavedGamesPath', lambda self, p: '')
		monkeypatch.setattr(SettingsManager, 'detectDCSInstallPath', lambda self, p: '')
		return SettingsManager()

	def test_loadConvertsForwardSlashOverrides(self, tempConfigDir, monkeypatch):
		with open(tempConfigDir['configFile'], 'w') as f:
			json.dump({
				'dcsSavedGamesOverride': 'C:/Users/Pilot/Saved Games/DCS',
				'dcsExePathOverride': 'D:/Games/DCS World/bin-mt/DCS.exe',
			}, f)
		mgr = self._newManager(tempConfigDir, monkeypatch)
		assert mgr.config['dcsSavedGamesOverride'] == r'C:\Users\Pilot\Saved Games\DCS'
		assert mgr.config['dcsExePathOverride'] == r'D:\Games\DCS World\bin-mt\DCS.exe'

	def test_saveWritesBackslashOverrides(self, tempConfigDir, monkeypatch):
		mgr = self._newManager(tempConfigDir, monkeypatch)
		mgr.saveConfig({
			'dcsSavedGamesOverride': 'C:/Users/Pilot/Saved Games/DCS.openbeta/',
			'dcsExePathOverride': 'D:/Games/DCS World/bin/DCS.exe',
		})
		with open(tempConfigDir['configFile']) as f:
			saved = json.load(f)
		assert saved['dcsSavedGamesOverride'] == r'C:\Users\Pilot\Saved Games\DCS.openbeta'
		assert saved['dcsExePathOverride'] == r'D:\Games\DCS World\bin\DCS.exe'

	def test_envVarIsKeptUnexpanded(self, tempConfigDir, monkeypatch):
		mgr = self._newManager(tempConfigDir, monkeypatch)
		mgr.saveConfig({'dcsSavedGamesOverride': '%USERPROFILE%/Saved Games/DCS'})
		assert mgr.config['dcsSavedGamesOverride'] == r'%USERPROFILE%\Saved Games\DCS'

	def test_emptyOverrideStaysEmpty(self, tempConfigDir, monkeypatch):
		mgr = self._newManager(tempConfigDir, monkeypatch)
		mgr.saveConfig({'dcsSavedGamesOverride': '', 'dcsExePathOverride': ''})
		assert mgr.config['dcsSavedGamesOverride'] == ''
		assert mgr.config['dcsExePathOverride'] == ''


# -----------------------------------------------------------------------
# describeResolvedPath — the gray status line under each path field
# -----------------------------------------------------------------------

class TestDescribeResolvedPath:
	exePath = r'C:\Games\DCS World\bin-mt\DCS.exe'

	def test_detectedWithoutOverride(self):
		assert describeResolvedPath('', self.exePath) == rf'Detected: {self.exePath}'

	def test_notDetected(self):
		assert describeResolvedPath('', '') == 'Not detected'

	def test_ambiguousDetection(self):
		path = r'C:\Users\Pilot\Saved Games\DCS'
		assert describeResolvedPath('', path, ambiguous=True) == rf'More than one detected; using: {path}'

	def test_overrideInUseShowsExpandedPath(self, monkeypatch):
		monkeypatch.setenv('USERPROFILE', r'C:\Users\Pilot')
		assert describeResolvedPath(r'%USERPROFILE%\Saved Games\DCS', r'C:\Users\Pilot\Saved Games\DCS') == r'Using: C:\Users\Pilot\Saved Games\DCS'

	def test_overrideMatchIsCaseInsensitive(self):
		assert describeResolvedPath(r'c:\games\dcs world\bin-mt\dcs.exe', self.exePath) == rf'Using: {self.exePath}'

	def test_missingOverrideFallsBackToDetected(self):
		"""detectDCSInstallPath falls back to the registry when the override doesn't exist."""
		assert describeResolvedPath(r'D:\Missing\DCS.exe', self.exePath) == rf'Override not found; using detected: {self.exePath}'

	def test_missingOverrideWithNoFallback(self):
		assert describeResolvedPath(r'D:\Missing\Saved Games', '') == 'Override not found'


# -----------------------------------------------------------------------
# readHookSettings
# -----------------------------------------------------------------------

class TestReadHookSettings:
	def test_missingFileGivesDefaults(self, tmp_path):
		assert readHookSettings(str(tmp_path / 'nope.lua')) == HOOK_SETTINGS_DEFAULTS

	def test_emptyPathGivesDefaults(self):
		assert readHookSettings('') == HOOK_SETTINGS_DEFAULTS

	def test_defaultsMatchTheSettingsFileAFreshInstallWrites(self):
		"""The Settings window can open before the DCS scripts are installed; it must show what the install will write, or saving turns logging on."""
		shipped = os.path.join(os.path.dirname(__file__), '..', 'Scripts', 'DCSAutoMate', 'DCSAutoMateHookSettings.lua')
		assert readHookSettings('') == readHookSettings(shipped)

	def test_loggingIsOffByDefault(self):
		assert not any(readHookSettings('').values())

	def test_readsEachFlag(self, tmp_path):
		path = tmp_path / 'DCSAutoMateHookSettings.lua'
		path.write_text(
			'return {\n'
			'\tisHookLogFileEnabled = false,\n'
			'\tisDebugLoggingEnabled = true,\n'
			'\tisUiWireLoggingEnabled = false,\n'
			'}\n',
			encoding='utf-8',
		)
		assert readHookSettings(str(path)) == {
			'isHookLogFileEnabled': False,
			'isDebugLoggingEnabled': True,
			'isUiWireLoggingEnabled': False,
		}

	def test_readErrorPropagates(self, tmp_path):
		"""A path that exists but can't be read must raise, not silently become defaults."""
		with pytest.raises(OSError):
			readHookSettings(str(tmp_path))


# -----------------------------------------------------------------------
# loadSettings / updateLastUsed / getters round-trip
# -----------------------------------------------------------------------

class TestSettings:
	def test_defaultLastUsedModuleEmpty(self, manager):
		assert manager.getLastUsedModule() == ''

	def test_updateAndGetModule(self, manager):
		manager.updateLastUsed('FA-18C', 'Cold Start', {'time': 'day'})
		assert manager.getLastUsedModule() == 'FA-18C'

	def test_updateAndGetScriptName(self, manager):
		manager.updateLastUsed('FA-18C', 'Cold Start', {'time': 'day'})
		assert manager.getLastUsedScriptName('FA-18C') == 'Cold Start'

	def test_updateAndGetVars(self, manager):
		manager.updateLastUsed('FA-18C', 'Cold Start', {'time': 'night'})
		v = manager.getLastUsedVars('FA-18C', 'Cold Start')
		assert v == {'time': 'night'}

	def test_multipleModules(self, manager):
		manager.updateLastUsed('FA-18C', 'Cold Start', {'time': 'day'})
		manager.updateLastUsed('A-10C_2', 'Hot Start', {'time': 'night'})
		# Last module should be the most recent
		assert manager.getLastUsedModule() == 'A-10C_2'
		# But FA-18C data should still be there.
		assert manager.getLastUsedScriptName('FA-18C') == 'Cold Start'

	def test_multipleScriptsPerModule(self, manager):
		manager.updateLastUsed('FA-18C', 'Cold Start', {'time': 'day'})
		manager.updateLastUsed('FA-18C', 'Hot Start', {'time': 'night'})
		# Last script for the module should be Hot Start.
		assert manager.getLastUsedScriptName('FA-18C') == 'Hot Start'
		# But Cold Start vars should still be stored.
		assert manager.getLastUsedVars('FA-18C', 'Cold Start') == {'time': 'day'}


# -----------------------------------------------------------------------
# Routes round-trip
# -----------------------------------------------------------------------

class TestRoutes:
	def test_defaultRouteIsNone(self, manager):
		m, r = manager.getLastUsedRoute('FA-18C', 'Cold Start')
		assert m is None
		assert r is None

	def test_updateAndGetRoute(self, manager):
		manager.updateLastUsed('FA-18C', 'Cold Start', {})
		manager.updateLastUsedRoute('FA-18C', 'Cold Start', 'Caucasus', 'Route 1')
		m, r = manager.getLastUsedRoute('FA-18C', 'Cold Start')
		assert m == 'Caucasus'
		assert r == 'Route 1'

	def test_routePerScript(self, manager):
		"""Routes should be stored per-script, not per-module."""
		manager.updateLastUsed('FA-18C', 'Cold Start', {})
		manager.updateLastUsed('FA-18C', 'Hot Start', {})
		manager.updateLastUsedRoute('FA-18C', 'Cold Start', 'Caucasus', 'Route A')
		manager.updateLastUsedRoute('FA-18C', 'Hot Start', 'Syria', 'Route B')
		m1, r1 = manager.getLastUsedRoute('FA-18C', 'Cold Start')
		m2, r2 = manager.getLastUsedRoute('FA-18C', 'Hot Start')
		assert (m1, r1) == ('Caucasus', 'Route A')
		assert (m2, r2) == ('Syria', 'Route B')

	def test_emptyModuleNameSkips(self, manager):
		"""updateLastUsedRoute should do nothing when moduleName is empty."""
		manager.updateLastUsedRoute('', 'Cold Start', 'Caucasus', 'Route 1')
		# Should not crash, and nothing stored.


# -----------------------------------------------------------------------
# detectSavedGamesPath
# -----------------------------------------------------------------------

class TestDetectSavedGamesPath:
	def test_overridePathUsedIfExists(self, tempConfigDir, monkeypatch):
		"""When an override path exists, it should be returned."""
		monkeypatch.setattr(SettingsManager, 'CONFIG_FILE', tempConfigDir['configFile'])
		monkeypatch.setattr(SettingsManager, 'SETTINGS_FILE', tempConfigDir['settingsFile'])
		monkeypatch.setattr(SettingsManager, 'detectDCSInstallPath', lambda self, p: '')

		overridePath = str(tempConfigDir['tmpPath'])
		mgr = SettingsManager.__new__(SettingsManager)
		mgr.parentWindow = None
		mgr._dcsSavedGamesOptions = []
		mgr._dcsSavedGamesAmbiguous = False

		result = mgr.detectSavedGamesPath(overridePath)
		assert result == overridePath

	def test_overridePathEmptyIfNotExists(self, tempConfigDir):
		mgr = SettingsManager.__new__(SettingsManager)
		mgr.parentWindow = None
		mgr._dcsSavedGamesOptions = []
		mgr._dcsSavedGamesAmbiguous = False

		result = mgr.detectSavedGamesPath('/nonexistent/path/that/does/not/exist')
		assert result == ''

	def test_noOverrideFallsBackToSavedGames(self, tmp_path, monkeypatch):
		"""With no override, it should scan the standard Saved Games paths."""
		dcsDir = tmp_path / 'Saved Games' / 'DCS'
		dcsDir.mkdir(parents=True)

		monkeypatch.setenv('USERPROFILE', str(tmp_path))

		mgr = SettingsManager.__new__(SettingsManager)
		mgr.parentWindow = None
		mgr._dcsSavedGamesOptions = []
		mgr._dcsSavedGamesAmbiguous = False

		result = mgr.detectSavedGamesPath('')
		assert result == str(dcsDir)

	def test_prefersPathWithBiosJson(self, tmp_path, monkeypatch):
		"""If both DCS and DCS.openbeta exist, returns the first (DCS), marks ambiguous."""
		dcsDir = tmp_path / 'Saved Games' / 'DCS'
		dcsDir.mkdir(parents=True)
		obDir = tmp_path / 'Saved Games' / 'DCS.openbeta'
		obDir.mkdir(parents=True)

		monkeypatch.setenv('USERPROFILE', str(tmp_path))

		mgr = SettingsManager.__new__(SettingsManager)
		mgr.parentWindow = None
		mgr._dcsSavedGamesOptions = []
		mgr._dcsSavedGamesAmbiguous = False

		result = mgr.detectSavedGamesPath('')
		assert result == str(dcsDir)
		assert mgr._dcsSavedGamesAmbiguous is True

	def test_bothExistBothHaveJson(self, tmp_path, monkeypatch):
		"""Both DCS and DCS.openbeta exist; first (DCS) is chosen, ambiguous=True."""
		dcsDir = tmp_path / 'Saved Games' / 'DCS'
		(dcsDir / 'Scripts' / 'DCS-BIOS' / 'doc' / 'json').mkdir(parents=True)
		obDir = tmp_path / 'Saved Games' / 'DCS.openbeta'
		(obDir / 'Scripts' / 'DCS-BIOS' / 'doc' / 'json').mkdir(parents=True)

		monkeypatch.setenv('USERPROFILE', str(tmp_path))

		mgr = SettingsManager.__new__(SettingsManager)
		mgr.parentWindow = None
		mgr._dcsSavedGamesOptions = []
		mgr._dcsSavedGamesAmbiguous = False

		result = mgr.detectSavedGamesPath('')
		assert result == str(dcsDir)
		assert mgr._dcsSavedGamesAmbiguous is True
		assert len(mgr._dcsSavedGamesOptions) == 2

	def test_bothExistNeitherHasJson(self, tmp_path, monkeypatch):
		"""Both folders exist — ambiguous, first chosen."""
		dcsDir = tmp_path / 'Saved Games' / 'DCS'
		dcsDir.mkdir(parents=True)
		obDir = tmp_path / 'Saved Games' / 'DCS.openbeta'
		obDir.mkdir(parents=True)

		monkeypatch.setenv('USERPROFILE', str(tmp_path))

		mgr = SettingsManager.__new__(SettingsManager)
		mgr.parentWindow = None
		mgr._dcsSavedGamesOptions = []
		mgr._dcsSavedGamesAmbiguous = False

		result = mgr.detectSavedGamesPath('')
		assert result == str(dcsDir)
		assert mgr._dcsSavedGamesAmbiguous is True
		assert len(mgr._dcsSavedGamesOptions) == 2

	def test_onlyOpenbetaExistsNoJson(self, tmp_path, monkeypatch):
		"""Only DCS.openbeta exists — no ambiguity, path returned."""
		obDir = tmp_path / 'Saved Games' / 'DCS.openbeta'
		obDir.mkdir(parents=True)

		monkeypatch.setenv('USERPROFILE', str(tmp_path))

		mgr = SettingsManager.__new__(SettingsManager)
		mgr.parentWindow = None
		mgr._dcsSavedGamesOptions = []
		mgr._dcsSavedGamesAmbiguous = False

		result = mgr.detectSavedGamesPath('')
		assert result == str(obDir)
		assert mgr._dcsSavedGamesAmbiguous is False

	def test_onlyOpenbetaExistsWithJson(self, tmp_path, monkeypatch):
		"""Only DCS.openbeta exists — no ambiguity, path returned."""
		obDir = tmp_path / 'Saved Games' / 'DCS.openbeta'
		(obDir / 'Scripts' / 'DCS-BIOS' / 'doc' / 'json').mkdir(parents=True)

		monkeypatch.setenv('USERPROFILE', str(tmp_path))

		mgr = SettingsManager.__new__(SettingsManager)
		mgr.parentWindow = None
		mgr._dcsSavedGamesOptions = []
		mgr._dcsSavedGamesAmbiguous = False

		result = mgr.detectSavedGamesPath('')
		assert result == str(obDir)
		assert mgr._dcsSavedGamesAmbiguous is False

	def test_neitherExistsNoOverride(self, tmp_path, monkeypatch):
		"""No folders and no override — returns empty, no ambiguity, no options."""
		monkeypatch.setenv('USERPROFILE', str(tmp_path))

		mgr = SettingsManager.__new__(SettingsManager)
		mgr.parentWindow = None
		mgr._dcsSavedGamesOptions = []
		mgr._dcsSavedGamesAmbiguous = False

		result = mgr.detectSavedGamesPath('')
		assert result == ''
		assert mgr._dcsSavedGamesAmbiguous is False
		assert mgr._dcsSavedGamesOptions == []

	def test_overrideWithEnvVarExpansion(self, tmp_path, monkeypatch):
		"""Override containing %USERPROFILE% should be expanded."""
		dcsDir = tmp_path / 'Saved Games' / 'DCS'
		dcsDir.mkdir(parents=True)

		monkeypatch.setenv('USERPROFILE', str(tmp_path))

		mgr = SettingsManager.__new__(SettingsManager)
		mgr.parentWindow = None
		mgr._dcsSavedGamesOptions = []
		mgr._dcsSavedGamesAmbiguous = False

		result = mgr.detectSavedGamesPath('%USERPROFILE%\\Saved Games\\DCS')
		assert result == str(dcsDir)

	def test_overrideWithUnexpandableEnvVar(self):
		"""Override with a nonexistent env var stays unexpanded, path won't exist → empty."""
		mgr = SettingsManager.__new__(SettingsManager)
		mgr.parentWindow = None
		mgr._dcsSavedGamesOptions = []
		mgr._dcsSavedGamesAmbiguous = False

		result = mgr.detectSavedGamesPath('%NONEXISTENT_ENV_VAR_12345%\\Saved Games\\DCS')
		assert result == ''

	def test_overrideExistsNoJson(self, tmp_path):
		"""Override path exists."""
		overridePath = str(tmp_path)

		mgr = SettingsManager.__new__(SettingsManager)
		mgr.parentWindow = None
		mgr._dcsSavedGamesOptions = []
		mgr._dcsSavedGamesAmbiguous = False

		result = mgr.detectSavedGamesPath(overridePath)
		assert result == overridePath

	def test_overrideExistsWithJson(self, tmp_path):
		"""Override path exists (content irrelevant — DCS-BIOS JSON no longer detected)."""
		jsonDir = tmp_path / 'Scripts' / 'DCS-BIOS' / 'doc' / 'json'
		jsonDir.mkdir(parents=True)

		overridePath = str(tmp_path)

		mgr = SettingsManager.__new__(SettingsManager)
		mgr.parentWindow = None
		mgr._dcsSavedGamesOptions = []
		mgr._dcsSavedGamesAmbiguous = False

		result = mgr.detectSavedGamesPath(overridePath)
		assert result == overridePath


# -----------------------------------------------------------------------
# Config propagation — loadConfig / saveConfig preserve metadata
# -----------------------------------------------------------------------

class TestConfigPropagation:
	def test_loadConfigPopulatesAllMetadataKeys(self, tmp_path, monkeypatch, tempConfigDir):
		"""loadConfig should set all saved-games metadata keys from detection."""
		dcsDir = tmp_path / 'Saved Games' / 'DCS'
		(dcsDir / 'Scripts' / 'DCS-BIOS' / 'doc' / 'json').mkdir(parents=True)

		monkeypatch.setenv('USERPROFILE', str(tmp_path))
		monkeypatch.setattr(SettingsManager, 'CONFIG_FILE', tempConfigDir['configFile'])
		monkeypatch.setattr(SettingsManager, 'SETTINGS_FILE', tempConfigDir['settingsFile'])
		monkeypatch.setattr(SettingsManager, 'detectDCSInstallPath', lambda self, p: '')

		mgr = SettingsManager()
		assert mgr.config['dcsSavedGamesPath'] == str(dcsDir)
		assert mgr.config['dcsSavedGamesOptions'] == [str(dcsDir)]
		assert mgr.config['dcsSavedGamesAmbiguous'] is False

	def test_saveConfigRedetectsOnOverrideChange(self, tmp_path, monkeypatch, tempConfigDir):
		"""saveConfig should re-run detection when the override changes."""
		dcsDir = tmp_path / 'Saved Games' / 'DCS'
		(dcsDir / 'Scripts' / 'DCS-BIOS' / 'doc' / 'json').mkdir(parents=True)
		obDir = tmp_path / 'Saved Games' / 'DCS.openbeta'
		obDir.mkdir(parents=True)

		monkeypatch.setenv('USERPROFILE', str(tmp_path))
		monkeypatch.setattr(SettingsManager, 'CONFIG_FILE', tempConfigDir['configFile'])
		monkeypatch.setattr(SettingsManager, 'SETTINGS_FILE', tempConfigDir['settingsFile'])
		monkeypatch.setattr(SettingsManager, 'detectDCSInstallPath', lambda self, p: '')

		mgr = SettingsManager()
		# Initially detects DCS (has JSON).
		assert mgr.config['dcsSavedGamesPath'] == str(dcsDir)

		# Now set override to DCS.openbeta and save.
		mgr.saveConfig({'dcsSavedGamesOverride': str(obDir)})
		assert mgr.config['dcsSavedGamesPath'] == str(obDir)
