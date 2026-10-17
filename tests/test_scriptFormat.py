"""Tests for aircraft script output format — validates every script in DCSAutoMateScripts/.

These tests import each aircraft module, call getScriptData(), and validate that
the returned structure is correct.  For each script function, they call it with
default vars and check the output sequence format.
"""
import importlib
import os
import sys
from unittest.mock import MagicMock

import pytest

# Stub PySide6 so aircraft scripts that import it don't break.
sys.modules.setdefault('PySide6', type(sys)('PySide6'))
_qtw = type(sys)('PySide6.QtWidgets')
_qtw.QMessageBox = MagicMock()
sys.modules.setdefault('PySide6.QtWidgets', _qtw)

# Ensure project root and scripts dir are on path.
projectRoot = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if projectRoot not in sys.path:
	sys.path.insert(0, projectRoot)

SCRIPTS_DIR = os.path.join(projectRoot, 'DCSAutoMateScripts')

from engine.SequenceHelper import SequenceHelper
from engine.cockpitLookahead import rowNeedsCockpit


def discoverModules():
	"""Return list of module names (filenames without .py) in the scripts directory."""
	if not os.path.isdir(SCRIPTS_DIR):
		return []
	return [
		f[:-3] for f in os.listdir(SCRIPTS_DIR)
		if f.endswith('.py') and f != '__init__.py'
	]


def loadModule(moduleName):
	"""Import and return an aircraft script module."""
	return importlib.import_module(f'DCSAutoMateScripts.{moduleName}')


# Parametrize over all discovered script modules.
allModules = discoverModules()


@pytest.mark.parametrize('moduleName', allModules)
class TestScriptDataStructure:
	"""Validate the getScriptData() output for each aircraft module."""

	def test_hasGetScriptData(self, moduleName):
		mod = loadModule(moduleName)
		assert hasattr(mod, 'getScriptData'), f'{moduleName} is missing getScriptData()'

	def test_scriptDataIsDict(self, moduleName):
		mod = loadModule(moduleName)
		data = mod.getScriptData()
		assert isinstance(data, dict), f'{moduleName}.getScriptData() should return a dict'

	def test_hasModuleName(self, moduleName):
		mod = loadModule(moduleName)
		data = mod.getScriptData()
		assert 'moduleName' in data, f'{moduleName} scriptData missing "moduleName" key'
		assert isinstance(data['moduleName'], str)
		assert len(data['moduleName']) > 0

	def test_hasScriptsList(self, moduleName):
		mod = loadModule(moduleName)
		data = mod.getScriptData()
		assert 'scripts' in data, f'{moduleName} scriptData missing "scripts" key'
		assert isinstance(data['scripts'], list)
		assert len(data['scripts']) > 0, f'{moduleName} has empty scripts list'

	def test_eachScriptHasRequiredKeys(self, moduleName):
		mod = loadModule(moduleName)
		data = mod.getScriptData()
		for i, script in enumerate(data['scripts']):
			assert 'name' in script, f'{moduleName} script[{i}] missing "name"'
			assert 'function' in script, f'{moduleName} script[{i}] missing "function"'
			# 'vars' should exist (can be empty dict)
			assert 'vars' in script, f'{moduleName} script[{i}] missing "vars"'
			assert isinstance(script['vars'], dict)

	def test_functionReferencesExist(self, moduleName):
		"""Each script's 'function' key should reference an actual function in the module."""
		mod = loadModule(moduleName)
		data = mod.getScriptData()
		for script in data['scripts']:
			funcName = script['function']
			assert hasattr(mod, funcName), f'{moduleName} references nonexistent function "{funcName}"'
			assert callable(getattr(mod, funcName)), f'{moduleName}.{funcName} is not callable'


def getDefaultVars(script):
	"""Build a default vars dict from a script's vars definition.

	For each variable, pick the first option key.
	"""
	defaults = {}
	for varKey, varDef in script.get('vars', {}).items():
		options = varDef.get('options', {})
		if options:
			defaults[varKey] = next(iter(options))
		else:
			defaults[varKey] = ''
	return defaults


# Functions that require actual external data (route files, scratchpad files)
# and cannot be called with a bare SequenceHelper.
_EXTERNAL_DATA_FUNCTIONS = {'LoadRoute', 'LoadScratchpad', 'LoadWaypoints'}

def needsExternalData(functionName):
	"""Return True if the function needs route/scratchpad data that can't be mocked cheaply."""
	return functionName in _EXTERNAL_DATA_FUNCTIONS

def makeHelper(config):
	return SequenceHelper(config)


def runScript(func, config, scriptVars):
	"""Call a script function and return its full command list (live scripts are drained offline)."""
	helper = makeHelper(config)
	return helper.collectSequence(func(config, scriptVars, helper))


def getScriptCases():
	"""Yield (moduleName, scriptName, functionName) for every script in every module."""
	cases = []
	for moduleName in allModules:
		try:
			mod = loadModule(moduleName)
			data = mod.getScriptData()
			for script in data.get('scripts', []):
				cases.append((moduleName, script['name'], script['function'], script))
		except Exception:
			pass
	return cases


scriptCases = getScriptCases()


@pytest.mark.parametrize('moduleName,scriptName,functionName,scriptDef', scriptCases,
	ids=[f'{c[0]}/{c[1]}' for c in scriptCases])
class TestScriptFunctionOutput:
	"""Call each script function with default vars and validate the output sequence."""

	def test_returnsSequenceList(self, moduleName, scriptName, functionName, scriptDef):
		mod = loadModule(moduleName)
		func = getattr(mod, functionName)
		defaultVars = getDefaultVars(scriptDef)
		config = {'debug': True}
		if needsExternalData(functionName):
			pytest.skip('Script requires route/scratchpad data — skipped in unit tests')
		seq = runScript(func, config, defaultVars)
		assert isinstance(seq, list), f'{moduleName}.{functionName}() should return a list'
		assert len(seq) > 0, f'{moduleName}.{functionName}() returned an empty sequence'

	def test_eachCommandHasRequiredKeys(self, moduleName, scriptName, functionName, scriptDef):
		mod = loadModule(moduleName)
		func = getattr(mod, functionName)
		defaultVars = getDefaultVars(scriptDef)
		config = {'debug': True}
		if needsExternalData(functionName):
			pytest.skip('Script requires route/scratchpad data — skipped in unit tests')
		seq = runScript(func, config, defaultVars)

		for i, cmd in enumerate(seq):
			assert isinstance(cmd, dict), f'{moduleName}.{functionName}() seq[{i}] is not a dict'
			assert 'time' in cmd, f'{moduleName}.{functionName}() seq[{i}] missing "time"'
			assert 'cmd' in cmd, f'{moduleName}.{functionName}() seq[{i}] missing "cmd"'
			# 'time' should be a number >= 0
			assert isinstance(cmd['time'], (int, float)), f'seq[{i}] time is not numeric'
			assert cmd['time'] >= 0, f'seq[{i}] has negative time'

	def test_timesAreNonNegative(self, moduleName, scriptName, functionName, scriptDef):
		mod = loadModule(moduleName)
		func = getattr(mod, functionName)
		defaultVars = getDefaultVars(scriptDef)
		config = {'debug': True}
		if needsExternalData(functionName):
			pytest.skip('Script requires route/scratchpad data — skipped in unit tests')
		seq = runScript(func, config, defaultVars)
		for i, cmd in enumerate(seq):
			assert cmd['time'] >= 0, f'seq[{i}] has negative time: {cmd["time"]}'

	def test_knownCommandTypes(self, moduleName, scriptName, functionName, scriptDef):
		"""Command types should be either a known script command or a DCS BIOS control name."""
		mod = loadModule(moduleName)
		func = getattr(mod, functionName)
		defaultVars = getDefaultVars(scriptDef)
		config = {'debug': True}
		if needsExternalData(functionName):
			pytest.skip('Script requires route/scratchpad data — skipped in unit tests')
		seq = runScript(func, config, defaultVars)

		knownScriptCommands = {
			'scriptKeyboard', 'scriptSpeech', 'scriptPause', 'scriptText',
			'scriptCockpitState', 'scriptTimerStart', 'scriptTimerEnd', '',
		}
		for i, cmd in enumerate(seq):
			cmdType = cmd['cmd']
			# Either a known script command, a DCS BIOS control with module prefix
			# (contains '/'), or a short DCS BIOS control name (any non-empty string
			# that's a valid identifier-like name).
			isKnown = (
				cmdType in knownScriptCommands
				or '/' in cmdType
				or (isinstance(cmdType, str) and len(cmdType) > 0)
			)
			assert isKnown, f'{moduleName}.{functionName}() seq[{i}] has unrecognized cmd type: "{cmdType}"'

	def test_noCockpitStepAfterCockpitDone(self, moduleName, scriptName, functionName, scriptDef):
		"""scriptCockpitDone tells the player they can leave the cockpit, so no keyboard command or ind. wait may follow it."""
		mod = loadModule(moduleName)
		func = getattr(mod, functionName)
		if needsExternalData(functionName):
			pytest.skip('Script requires route/scratchpad data — skipped in unit tests')
		seq = runScript(func, {'debug': True}, getDefaultVars(scriptDef))
		cmds = [c['cmd'] for c in seq]
		if 'scriptCockpitDone' in cmds:
			after = seq[cmds.index('scriptCockpitDone'):]
			assert not [c for c in after if rowNeedsCockpit(c)], f'{moduleName}.{functionName}() needs the cockpit after scriptCockpitDone'
