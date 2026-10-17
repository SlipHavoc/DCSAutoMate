"""In-game window layout: monitorLayout() in the Hook places every widget for the window's size, run here through lupa."""
import os
import re

import lupa
import pytest

projectRoot = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
HOOK_FILE = os.path.join(projectRoot, 'Scripts', 'Hooks', 'DCSAutoMateHook.lua')


@pytest.fixture(scope='module')
def monitorLayout():
	"""The pure layout function, cut from the Hook between its marker comments (the rest of the Hook needs DCS)."""
	with open(HOOK_FILE, encoding='utf-8') as f:
		source = f.read()
	match = re.search(r'-- monitorLayout: begin\n(.*?)-- monitorLayout: end', source.replace('\r\n', '\n'), re.S)
	assert match, 'monitorLayout markers not found in the Hook'
	lua = lupa.LuaRuntime(unpack_returned_tuples=True)
	function = lua.execute(match.group(1) + '\nreturn monitorLayout')
	def layout(clientW, clientH, varCount):
		result = function(clientW, clientH, varCount)
		return {key: (tuple(value.values()) if lupa.lua_type(value) == 'table' else value) for key, value in result.items()}
	return layout


def test_defaultWindowKeepsTheOriginalLayout(monitorLayout):
	"""460 wide, as the window opens: the same places the fixed layout used, with Start, Skip Wait and Stop sharing the button row."""
	layout = monitorLayout(460, 360, 3)
	assert layout['autoSelect'] == (0, 0, 460, 20)
	assert layout['moduleCombo'] == (0, 24, 460, 20)
	assert layout['scriptCombo'] == (0, 48, 460, 20)
	assert layout['varsGrid'] == (0, 72, 460, 92) # Header 20 + 3 rows of 24.
	assert layout['startButton'] == (0, 176, 142, 20)
	assert layout['skipWaitButton'] == (146, 176, 142, 20)
	assert layout['stopButton'] == (292, 176, 142, 20)
	assert layout['copyButton'] == (438, 176, 22, 20)
	assert (layout['varColumnWidth'], layout['valueColumnWidth']) == (150, 310)


def test_widerTallerWindowStretchesControlsAndFillsWithOutput(monitorLayout):
	layout = monitorLayout(700, 500, 3)
	for name in ('autoSelect', 'moduleCombo', 'scriptCombo', 'varsGrid', 'varsGridBackground', 'outputText', 'notConnected'):
		assert layout[name][2] == 700, name
	assert layout['valueColumnWidth'] == 550
	x, y, w, h = layout['outputText']
	assert y + h == 500
	startX, _, startW, _ = layout['startButton']
	skipX, _, skipW, _ = layout['skipWaitButton']
	stopX, _, stopW, _ = layout['stopButton']
	copyX, _, copyW, _ = layout['copyButton']
	assert startW == skipW == stopW > 142
	assert startX + startW + 4 == skipX and skipX + skipW + 4 == stopX and stopX + stopW + 4 == copyX and copyX + copyW == 700


def test_shortWindowKeepsAMinimumOutputHeight(monitorLayout):
	layout = monitorLayout(460, 150, 5)
	x, y, w, h = layout['outputText']
	assert h == 100
	assert layout['minClientHeight'] == y + 100
	assert monitorLayout(460, 360, 5)['minClientHeight'] == layout['minClientHeight']


def test_narrowWindowNeverGoesBelowMinimumWidth(monitorLayout):
	layout = monitorLayout(200, 360, 1)
	assert layout['autoSelect'][2] == 300
	assert layout['valueColumnWidth'] == 150
