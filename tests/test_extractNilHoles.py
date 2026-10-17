"""Lua array tables with nil holes (e.g. `relative = {nil, true}`) must keep
their per-sub-control alignment through extraction.

Regression: the Mi-24P RADAR-ALTIMETER-KNOB-PTR declares `relative = {nil, true}`.
luaTableToList stopped at the first nil, so `relative` was dropped entirely and
the endless knob (arg 30) was mapped as 'continuous' instead of 'relative'.
"""
import glob
import importlib
import os
import sys

import lupa
import pytest
from lupa import lua51

EXTRACTION_DIR = os.path.normpath(os.path.join(os.path.dirname(__file__), '..', 'tools', 'extraction-scripts'))
if EXTRACTION_DIR not in sys.path:
	sys.path.insert(0, EXTRACTION_DIR)

from extractUtils import luaTableToList

EXTRACTOR_MODULES = sorted(
	os.path.splitext(os.path.basename(p))[0]
	for p in glob.glob(os.path.join(EXTRACTION_DIR, 'extract_*.py'))
)


def evalLua(expr):
	return lupa.LuaRuntime().eval(expr)


class TestLuaTableToList:
	def test_plainArray(self):
		assert luaTableToList(evalLua('{1, 2, 3}')) == [1, 2, 3]

	def test_leadingNilIsPreserved(self):
		assert luaTableToList(evalLua('{nil, true}')) == [None, True]

	def test_interiorNilsArePreserved(self):
		assert luaTableToList(evalLua('{nil, nil, -0.1}')) == [None, None, -0.1]
		assert luaTableToList(evalLua('{1, nil, 3}')) == [1, None, 3]

	def test_nestedTables(self):
		assert luaTableToList(evalLua('{{0, 1}, {nil, 2}}')) == [[0, 1], [None, 2]]

	def test_emptyAndNone(self):
		assert luaTableToList(evalLua('{}')) == []
		assert luaTableToList(None) == []

	def test_hashOnlyTableHasNoArrayPart(self):
		assert luaTableToList(evalLua('{a = 1, b = 2}')) == []

	def test_lua51RuntimeHoles(self):
		lua = lua51.LuaRuntime()
		assert luaTableToList(lua.eval('{nil, true}')) == [None, True]


ELEMENTS_LUA = '''
elements = {
	KNOB = {
		class = {0, 2}, hint = 'knob', device = 12,
		action = {3002, 3001}, stop_action = {3002, 0},
		arg = {31, 30}, arg_value = {1.0, 0.05}, arg_lim = {{0.0, 1.0}, {0.0, 1.0}},
		gain = {1.0, 0.05}, relative = {nil, true}, use_release_message = {true, false},
	},
	SPRING = {
		class = {0, 0}, hint = 'spring', device = 5,
		action = {3001, 3002}, stop_action = {nil, 3002},
		arg = {10, 10}, arg_value = {-1.0, 1.0}, arg_lim = {{-1.0, 0.0}, {0.0, 1.0}},
		gain = {nil, 0.1},
	},
	MIRROR = {
		class = {0, nil, 2}, hint = 'mirror', device = 24,
		action = {3010, 3010, 3013}, arg = {nil, nil, 10},
		arg_value = {1.0, -1.0, 0.0}, arg_lim = {{0.0, 1.0}, {0.0, 1.0}, {0.0, 1.0}},
	},
}
'''


@pytest.mark.parametrize('moduleName', EXTRACTOR_MODULES)
class TestExtractElementsAlignment:
	@pytest.fixture
	def extracted(self, moduleName):
		module = importlib.import_module(moduleName)
		lua = lupa.LuaRuntime()
		lua.execute(ELEMENTS_LUA)
		return module.extractElements(lua)

	def test_leadingNilRelativeKeepsLevSubControlRelative(self, extracted):
		assert extracted['KNOB']['relative'] == [False, True]

	def test_leadingNilStopActionKeepsAlignment(self, extracted):
		assert extracted['SPRING']['stopAction'] == [0, 3002]

	def test_leadingNilGainKeepsAlignment(self, extracted):
		assert extracted['SPRING']['gain'] == [None, 0.1]

	def test_nilArgBecomesNoArgZero(self, extracted):
		assert extracted['MIRROR']['arg'] == [0, 0, 10]

	def test_nilClassKeepsAlignment(self, extracted):
		assert extracted['MIRROR']['controlClass'] == ['BTN', None, 'LEV']

	def test_fullyPopulatedListsUnchanged(self, extracted):
		knob = extracted['KNOB']
		assert knob['action'] == [3002, 3001]
		assert knob['stopAction'] == [3002, 0]
		assert knob['gain'] == [1.0, 0.05]
		assert knob['controlClass'] == ['BTN', 'LEV']
