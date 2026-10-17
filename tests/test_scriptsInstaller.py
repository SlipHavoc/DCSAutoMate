"""Tests for utils.DcsScriptsInstaller — path detection and installation checks."""
import os
import sys
from unittest.mock import MagicMock

import pytest

# Stub PySide6 so the module can be imported without Qt installed in CI.
sys.modules.setdefault('PySide6', type(sys)('PySide6'))
_qtw = type(sys)('PySide6.QtWidgets')
_qtw.QMessageBox = MagicMock()
sys.modules.setdefault('PySide6.QtWidgets', _qtw)

from utils.DcsScriptsInstaller import DcsScriptsInstaller


# -----------------------------------------------------------------------
# getExistingDcsSavedGamesFolders
# -----------------------------------------------------------------------

class TestGetExistingDcsSavedGamesFolders:
	def test_overrideExistsReturnsSingleEntry(self, tmp_path):
		"""When override path exists, returns [('Override', path)]."""
		config = {'dcsSavedGamesOverride': str(tmp_path)}
		result = DcsScriptsInstaller.getExistingDcsSavedGamesFolders(config)
		assert len(result) == 1
		assert result[0][0] == 'Override'
		assert result[0][1] == str(tmp_path)

	def test_overrideMissingFallsThrough(self, tmp_path, monkeypatch):
		"""When override doesn't exist, falls through to standard scan."""
		dcsDir = tmp_path / 'Saved Games' / 'DCS'
		dcsDir.mkdir(parents=True)

		monkeypatch.setenv('USERPROFILE', str(tmp_path))

		config = {'dcsSavedGamesOverride': '/nonexistent/path'}
		result = DcsScriptsInstaller.getExistingDcsSavedGamesFolders(config)
		assert len(result) == 1
		assert result[0][0] == 'DCS'

	def test_bothFoldersExist(self, tmp_path, monkeypatch):
		"""When both DCS and DCS.openbeta exist, returns both."""
		(tmp_path / 'Saved Games' / 'DCS').mkdir(parents=True)
		(tmp_path / 'Saved Games' / 'DCS.openbeta').mkdir(parents=True)

		monkeypatch.setenv('USERPROFILE', str(tmp_path))

		config = {'dcsSavedGamesOverride': ''}
		result = DcsScriptsInstaller.getExistingDcsSavedGamesFolders(config)
		names = [name for name, _ in result]
		assert 'DCS' in names
		assert 'DCS.openbeta' in names
		assert len(result) == 2

	def test_onlyDcsExists(self, tmp_path, monkeypatch):
		"""When only DCS exists, returns one entry."""
		(tmp_path / 'Saved Games' / 'DCS').mkdir(parents=True)

		monkeypatch.setenv('USERPROFILE', str(tmp_path))

		config = {'dcsSavedGamesOverride': ''}
		result = DcsScriptsInstaller.getExistingDcsSavedGamesFolders(config)
		assert len(result) == 1
		assert result[0][0] == 'DCS'

	def test_neitherExistsNoOverride(self, tmp_path, monkeypatch):
		"""When neither folder exists and no override is set, returns empty list."""
		monkeypatch.setenv('USERPROFILE', str(tmp_path))

		config = {'dcsSavedGamesOverride': ''}
		result = DcsScriptsInstaller.getExistingDcsSavedGamesFolders(config)
		assert result == []

	def test_emptyConfigHandled(self, tmp_path, monkeypatch):
		"""Passing empty or None config should not crash."""
		monkeypatch.setenv('USERPROFILE', str(tmp_path))
		result = DcsScriptsInstaller.getExistingDcsSavedGamesFolders({})
		assert isinstance(result, list)
		result2 = DcsScriptsInstaller.getExistingDcsSavedGamesFolders(None)
		assert isinstance(result2, list)

	def test_overrideWithEnvVar(self, tmp_path, monkeypatch):
		"""Override containing %USERPROFILE% should be expanded."""
		dcsDir = tmp_path / 'Saved Games' / 'DCS'
		dcsDir.mkdir(parents=True)

		monkeypatch.setenv('USERPROFILE', str(tmp_path))

		config = {'dcsSavedGamesOverride': '%USERPROFILE%\\Saved Games\\DCS'}
		result = DcsScriptsInstaller.getExistingDcsSavedGamesFolders(config)
		assert len(result) == 1
		assert result[0][0] == 'Override'
		assert result[0][1] == str(dcsDir)


# -----------------------------------------------------------------------
# check_installed
# -----------------------------------------------------------------------

def _setupInstalledFolder(basePath):
	"""Create the minimum files that check_installed expects."""
	scriptsDir = basePath / 'Scripts'
	dcsAutoMateDir = scriptsDir / 'DCSAutoMate'
	dcsAutoMateDir.mkdir(parents=True)
	hooksDir = scriptsDir / 'Hooks'
	hooksDir.mkdir(parents=True)

	(dcsAutoMateDir / 'DCSAutoMateExport.lua').write_text('-- export', encoding='utf-8')
	(hooksDir / 'DCSAutoMateHook.lua').write_text('-- hook', encoding='utf-8')

	exportLua = scriptsDir / 'Export.lua'
	exportLua.write_text(
		r'dofile(lfs.writedir()..[[Scripts\DCSAutoMate\DCSAutoMateExport.lua]])' + '\n',
		encoding='utf-8',
	)
	return basePath


class TestCheckInstalled:
	def test_noFoldersFoundReturnsFalse(self, tmp_path, monkeypatch):
		"""When no Saved Games folders are found, check_installed returns False.

		If no folders can be located, the scripts are clearly not installed,
		so the Missing Scripts install prompt should appear.
		"""
		monkeypatch.setenv('USERPROFILE', str(tmp_path))
		config = {'dcsSavedGamesOverride': ''}
		assert DcsScriptsInstaller.check_installed(config) is False

	def test_folderExistsButScriptsMissing(self, tmp_path, monkeypatch):
		"""When a folder exists but scripts aren't installed, returns False."""
		dcsDir = tmp_path / 'Saved Games' / 'DCS'
		dcsDir.mkdir(parents=True)

		monkeypatch.setenv('USERPROFILE', str(tmp_path))

		config = {'dcsSavedGamesOverride': ''}
		assert DcsScriptsInstaller.check_installed(config) is False

	def test_fullyInstalledReturnsTrue(self, tmp_path, monkeypatch):
		"""When all scripts and Export.lua line are present, returns True."""
		dcsDir = tmp_path / 'Saved Games' / 'DCS'
		dcsDir.mkdir(parents=True)
		_setupInstalledFolder(dcsDir)

		monkeypatch.setenv('USERPROFILE', str(tmp_path))

		config = {'dcsSavedGamesOverride': ''}
		assert DcsScriptsInstaller.check_installed(config) is True

	def test_exportLuaMissingDofileReturnsFalse(self, tmp_path, monkeypatch):
		"""When Export.lua exists but lacks the dofile line, returns False."""
		dcsDir = tmp_path / 'Saved Games' / 'DCS'
		dcsDir.mkdir(parents=True)
		_setupInstalledFolder(dcsDir)

		# Overwrite Export.lua with content that lacks the dofile line.
		exportLua = dcsDir / 'Scripts' / 'Export.lua'
		exportLua.write_text('-- no dofile here\n', encoding='utf-8')

		monkeypatch.setenv('USERPROFILE', str(tmp_path))

		config = {'dcsSavedGamesOverride': ''}
		assert DcsScriptsInstaller.check_installed(config) is False

	def test_exportLuaMissingReturnsFalse(self, tmp_path, monkeypatch):
		"""When the hook and export script exist but Export.lua itself is missing, returns False."""
		dcsDir = tmp_path / 'Saved Games' / 'DCS'
		dcsDir.mkdir(parents=True)
		_setupInstalledFolder(dcsDir)

		# Remove Export.lua.
		(dcsDir / 'Scripts' / 'Export.lua').unlink()

		monkeypatch.setenv('USERPROFILE', str(tmp_path))

		config = {'dcsSavedGamesOverride': ''}
		assert DcsScriptsInstaller.check_installed(config) is False

	def test_overridePathUsedForCheck(self, tmp_path):
		"""check_installed should use the override path when provided."""
		_setupInstalledFolder(tmp_path)

		config = {'dcsSavedGamesOverride': str(tmp_path)}
		assert DcsScriptsInstaller.check_installed(config) is True

	def test_overridePathMissingScripts(self, tmp_path):
		"""Override path exists but has no scripts — returns False."""
		config = {'dcsSavedGamesOverride': str(tmp_path)}
		assert DcsScriptsInstaller.check_installed(config) is False
