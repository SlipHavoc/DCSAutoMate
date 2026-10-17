"""Tests for engine.ScriptManager — module discovery and loading."""
import os
import sys

import pytest

# Stub PySide6
sys.modules.setdefault('PySide6', type(sys)('PySide6'))

projectRoot = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if projectRoot not in sys.path:
	sys.path.insert(0, projectRoot)

from engine.ScriptManager import ScriptManager
from engine.SequenceHelper import SequenceHelper


@pytest.fixture
def sm():
	return ScriptManager()


class TestGetModules:
	def test_getModuleGivesTheScriptModuleWithItsOptionalAutoSelect(self, sm):
		assert callable(sm.getModule('C-130J').autoSelect)
		assert not hasattr(sm.getModule('A-10C_2'), 'autoSelect')

	def test_returnsNonEmptyList(self, sm):
		modules = sm.getModules()
		assert isinstance(modules, list)
		assert len(modules) > 0

	def test_containsKnownModule(self, sm):
		modules = sm.getModules()
		# A-10C_2 should always exist
		assert 'A-10C_2' in modules

	def test_doesNotIncludeInit(self, sm):
		modules = sm.getModules()
		assert '__init__' not in modules

	def test_matchesFilesOnDisk(self, sm):
		"""Every returned module should correspond to a .py file."""
		modules = sm.getModules()
		for mod in modules:
			assert os.path.isfile(os.path.join(sm.SCRIPT_PATH, f'{mod}.py'))


class TestGetScriptData:
	def test_returnsDict(self, sm):
		data = sm.getScriptData('A-10C_2')
		assert isinstance(data, dict)

	def test_hasModuleName(self, sm):
		data = sm.getScriptData('A-10C_2')
		assert 'moduleName' in data
		assert data['moduleName'] == 'A-10C_2'

	def test_hasScriptsList(self, sm):
		data = sm.getScriptData('A-10C_2')
		assert 'scripts' in data
		assert isinstance(data['scripts'], list)
		assert len(data['scripts']) > 0

	def test_nonexistentModuleReturnsEmpty(self, sm):
		data = sm.getScriptData('NONEXISTENT_MODULE_12345')
		assert data == {'scripts': []}


class TestGetScriptVars:
	def test_returnsVarsDict(self, sm):
		data = sm.getScriptData('A-10C_2')
		# The first script should be 'Cold Start' which has 'time' var
		v = sm.getScriptVars(data, 'Cold Start')
		assert isinstance(v, dict)
		assert 'time' in v

	def test_nonexistentScriptReturnsEmpty(self, sm):
		data = sm.getScriptData('A-10C_2')
		v = sm.getScriptVars(data, 'NONEXISTENT_SCRIPT')
		assert v == {}


class TestLoadScriptFunction:
	def test_returnsCallable(self, sm):
		func, mod = sm.loadScriptFunction('A-10C_2', 'Cold Start')
		assert callable(func)
		assert mod is not None

	def test_nonexistentScriptReturnsNone(self, sm):
		func, mod = sm.loadScriptFunction('A-10C_2', 'NONEXISTENT_SCRIPT')
		assert func is None
		assert mod is None

	def test_loadedFunctionProducesSequence(self, sm):
		"""The loaded function should produce a non-empty sequence when called."""
		func, mod = sm.loadScriptFunction('A-10C_2', 'Cold Start')
		config = {'debug': True}
		helper = SequenceHelper(config)
		seq = func(config, {'time': 'day'}, helper)
		assert isinstance(seq, list)
		assert len(seq) > 0
