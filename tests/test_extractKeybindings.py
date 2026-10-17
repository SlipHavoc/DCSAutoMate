"""Unit tests for extractKeybindings() in tools/extraction-scripts/extractUtils.py."""
import os
import sys

import pytest

EXTRACTION_DIR = os.path.normpath(os.path.join(os.path.dirname(__file__), '..', 'tools', 'extraction-scripts'))
if EXTRACTION_DIR not in sys.path:
	sys.path.insert(0, EXTRACTION_DIR)

from extractUtils import extractKeybindings


def writeFile(path, text):
	path.parent.mkdir(parents=True, exist_ok=True)
	path.write_text(text, encoding='utf-8')


@pytest.fixture
def inputDir(tmp_path):
	"""A minimal module layout: Cockpit/Scripts defs plus an Input/<profile> tree."""
	writeFile(tmp_path / 'Cockpit' / 'Scripts' / 'devices.lua', 'devices = {}\ndevices.ENGINE = 3\ndevices.ELEC = 1\n')
	writeFile(tmp_path / 'Cockpit' / 'Scripts' / 'command_defs.lua', 'device_commands = { Button_18 = 3018, Button_19 = 3019, Axis_1 = 3100 }\n')
	header = 'local cockpit = folder.."../../../Cockpit/Scripts/"\ndofile(cockpit.."devices.lua")\ndofile(cockpit.."command_defs.lua")\n'
	startEngine = "{down = device_commands.Button_18, up = device_commands.Button_18, cockpit_device_id = devices.ENGINE, value_down = 1.0, value_up = 0.0, name = _('Start-up engine'), category = _('Collective')},\n"
	writeFile(tmp_path / 'Input' / 'Heli' / 'keyboard' / 'default.lua', header + (
		'local res = external_profile("Config/Input/Aircrafts/common_keyboard_binding.lua")\n'
		'join(res.keyCommands, {\n'
		"{down = iCommandViewCockpit, name = _('Cockpit view'), category = _('View')},\n"
		+ startEngine +
		"{down = device_commands.Button_19, cockpit_device_id = devices.ELEC, value_down = 0.02, name = _('CB Prox. warn.'), category = _('Circuit breakers')},\n"
		'})\n'
		'return res\n'
	))
	writeFile(tmp_path / 'Input' / 'Heli' / 'joystick' / 'default.lua', header + (
		'return {\n'
		'keyCommands = {\n' + startEngine + '},\n'
		'axisCommands = {\n'
		"{action = device_commands.Axis_1, cockpit_device_id = devices.ENGINE, name = _('Throttle')},\n"
		"{action = iCommandPlaneRoll, name = _('Roll')},\n"
		'},\n'
		'}\n'
	))
	# Hardware-specific presets are not default.lua and must be ignored.
	writeFile(tmp_path / 'Input' / 'Heli' / 'joystick' / 'Some Stick.lua', header + 'return { keyCommands = {' + startEngine.replace('Start-up engine', 'Preset only') + '} }\n')
	return tmp_path / 'Input'


def test_extractKeybindingsKeepsOnlyCockpitDeviceBindings(inputDir):
	bindings, failures = extractKeybindings(str(inputDir))
	assert failures == []
	names = sorted(b['name'] for b in bindings)
	assert names == ['CB Prox. warn.', 'Start-up engine', 'Throttle']


def test_extractKeybindingsReturnsDeviceCommandAndValues(inputDir):
	bindings, _ = extractKeybindings(str(inputDir))
	start = next(b for b in bindings if b['name'] == 'Start-up engine')
	assert start['deviceId'] == 3
	assert start['down'] == 3018
	assert start['up'] == 3018
	assert start['valueDown'] == 1.0
	assert start['valueUp'] == 0.0
	assert start['kind'] == 'key'
	assert start['category'] == 'Collective'
	breaker = next(b for b in bindings if b['name'] == 'CB Prox. warn.')
	assert breaker['deviceId'] == 1
	assert breaker['down'] == 3019
	assert breaker['valueDown'] == 0.02
	assert 'up' not in breaker


def test_extractKeybindingsReturnsAxisBindings(inputDir):
	bindings, _ = extractKeybindings(str(inputDir))
	throttle = next(b for b in bindings if b['name'] == 'Throttle')
	assert throttle['kind'] == 'axis'
	assert throttle['deviceId'] == 3
	assert throttle['action'] == 3100


def test_extractKeybindingsMergesDuplicatesAcrossFiles(inputDir):
	bindings, _ = extractKeybindings(str(inputDir))
	starts = [b for b in bindings if b['name'] == 'Start-up engine']
	assert len(starts) == 1
	assert starts[0]['sources'] == ['Heli/joystick', 'Heli/keyboard']


def test_extractKeybindingsReportsFailingFileAndContinues(inputDir):
	writeFile(inputDir / 'Broken' / 'keyboard' / 'default.lua', 'return { keyCommands = { undefinedFunction() } }\n')
	bindings, failures = extractKeybindings(str(inputDir))
	assert len(failures) == 1
	assert failures[0][0] == 'Broken/keyboard'
	assert 'undefinedFunction' in failures[0][1]
	assert 'Start-up engine' in {b['name'] for b in bindings}


def test_extractKeybindingsExternalProfileLoadsModuleFile(inputDir):
	"""external_profile() on a module file loads it, as DCS does; DCS's own Config profiles stay empty."""
	writeFile(inputDir / 'Pilot' / 'joystick' / 'default.lua', (
		'local res = { keyCommands = {}, axisCommands = {}, forceFeedback = {} }\n'
		'local keyboard = external_profile(folder .. "../keyboard/default.lua")\n'
		'join(res.keyCommands, keyboard.keyCommands)\n'
		'local common = external_profile("Config/Input/Aircrafts/common_joystick_binding.lua")\n'
		'join(res.forceFeedback, common.forceFeedback)\n'
		'return res\n'
	))
	writeFile(inputDir / 'Pilot' / 'keyboard' / 'default.lua', (
		'local cockpit = folder.."../../../Cockpit/Scripts/"\n'
		'dofile(cockpit.."devices.lua")\ndofile(cockpit.."command_defs.lua")\n'
		"return { keyCommands = { {down = device_commands.Button_19, cockpit_device_id = devices.ELEC, value_down = 1.0, name = _('Pilot key')} } }\n"
	))
	bindings, failures = extractKeybindings(str(inputDir))
	assert failures == []
	pilotKey = next(b for b in bindings if b['name'] == 'Pilot key')
	assert pilotKey['sources'] == ['Pilot/joystick', 'Pilot/keyboard']


def test_extractKeybindingsAppliesExtraLuaSetup(inputDir):
	writeFile(inputDir / 'Custom' / 'keyboard' / 'default.lua', (
		'local cockpit = folder.."../../../Cockpit/Scripts/"\n'
		'dofile(cockpit.."devices.lua")\ndofile(cockpit.."command_defs.lua")\n'
		"return { keyCommands = { push_button('Custom press', device_commands.Button_19, devices.ELEC) } }\n"
	))
	extraSetup = 'function push_button(n, cmd, dev) return { down = cmd, cockpit_device_id = dev, value_down = 1.0, name = n } end'
	bindings, failures = extractKeybindings(str(inputDir), extraSetup)
	assert failures == []
	custom = next(b for b in bindings if b['name'] == 'Custom press')
	assert custom['down'] == 3019
	assert custom['sources'] == ['Custom/keyboard']


def test_extractKeybindingsUsesLua51StringEscapes(inputDir):
	"""DCS runs Lua 5.1, which reads unknown escapes like \\% as the bare character (Ka-50 profiles rely on it)."""
	writeFile(inputDir / 'Legacy' / 'keyboard' / 'default.lua', (
		"return { keyCommands = { {down = 3001, cockpit_device_id = 7, value_down = 1.0, name = 'Lights formation 10\\%'} } }\n"
	))
	bindings, failures = extractKeybindings(str(inputDir))
	assert failures == []
	assert 'Lights formation 10%' in {b['name'] for b in bindings}


def test_extractKeybindingsIgnoreFeaturesRemovesTaggedCommands(inputDir):
	writeFile(inputDir / 'Tagged' / 'keyboard' / 'default.lua', (
		'local res = { keyCommands = {\n'
		"{down = 3001, cockpit_device_id = 7, value_down = 1.0, name = 'Jiggle', features = {'Camera jiggle'}},\n"
		"{down = 3002, cockpit_device_id = 7, value_down = 1.0, name = 'Kept'},\n"
		'} }\n'
		"ignore_features(res.keyCommands, {'Camera jiggle'})\n"
		'return res\n'
	))
	bindings, failures = extractKeybindings(str(inputDir))
	assert failures == []
	names = {b['name'] for b in bindings}
	assert 'Kept' in names
	assert 'Jiggle' not in names


def test_extractKeybindingsExternalProfileRunsInOwnEnvironmentWithCallerFolder(inputDir):
	"""Like DCS, a file loaded by external_profile() gets its own globals and the caller's folder (OH-58D seat profiles)."""
	writeFile(inputDir / 'Core' / 'joystick' / 'default.lua', (
		'inputs = { keyCommands = { {down = 3001, cockpit_device_id = 7, value_down = 1.0, name = folder} } }\n'
		'return inputs\n'
	))
	writeFile(inputDir / 'Seat' / 'joystick' / 'default.lua', (
		'inputs = { keyCommands = {}, forceFeedback = {} }\n'
		'local core = external_profile(folder .. "../../Core/joystick/default.lua")\n'
		'join(inputs.keyCommands, core.keyCommands)\n'
		'join(inputs.forceFeedback, {})\n'
		'return inputs\n'
	))
	bindings, failures = extractKeybindings(str(inputDir))
	assert failures == []
	seatFolder = str(inputDir / 'Seat' / 'joystick').replace('\\', '/') + '/'
	seatBinding = next(b for b in bindings if 'Seat/joystick' in b['sources'])
	assert seatBinding['name'] == seatFolder


def test_extractKeybindingsAcceptsSingleProfileDirectory(inputDir):
	"""An InputProfiles entry can point straight at a folder holding keyboard/ and joystick/ (AJS37, C-101)."""
	profileDir = inputDir / 'Heli'
	bindings, failures = extractKeybindings(str(profileDir))
	assert failures == []
	start = next(b for b in bindings if b['name'] == 'Start-up engine')
	assert start['sources'] == ['joystick', 'keyboard']
