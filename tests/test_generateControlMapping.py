"""Unit tests for tools/generateControlMapping.py."""
import os
import sys

import pytest


# Add the mapping-scripts/ directory to sys.path so we can import the generator module.
TOOLS_DIR = os.path.normpath(os.path.join(os.path.dirname(__file__), '..', 'tools', 'mapping-scripts'))
if TOOLS_DIR not in sys.path:
	sys.path.insert(0, TOOLS_DIR)

import generateControlMapping as gcm


# ─── Tests ───────────────────────────────────────────────────────────────────



def test_buildCommandReverseStillPrefersBaseNames():
	"""Regression: clickable-element command-id resolution should still prefer
	base names over `_ITER`/`_AXIS`/`_EXT` siblings even after the synthesis
	pass was added."""
	tables = {
		't_commands': {
			'Foo': 3001,
			'Foo_ITER': 3002,
		},
	}
	perTable, globalUnique = gcm.buildCommandReverse(tables)
	assert perTable['t_commands'][3001] == 'Foo'
	assert perTable['t_commands'][3002] == 'Foo_ITER'
	assert globalUnique[3001] == 'Foo'
	# 3002 has no non-suffixed name, so it does not appear in globalUnique.
	assert 3002 not in globalUnique

# ─── annotateIndicatorArgLim tests ───────────────────────────────────────────

def test_annotateIndicatorArgLimAddsFieldWhenArgShared():
	"""Controls whose arg appears in argToGaugeInput get indicatorArgLim set."""
	controls = {
		'AUTOPILOT.PPR_K': {
			'description': 'Autopilot K button',
			'type': 'discrete',
			'deviceId': 33,
			'commandId': 3005,
			'arg': 330,
			'argLim': [0.0, 1.0],
			'step': 1.0,
			'positions': 2,
		},
	}
	argToGaugeInput = {330: [0.0, 0.3]}
	count = gcm.annotateIndicatorArgLim(controls, argToGaugeInput)
	assert count == 1
	assert controls['AUTOPILOT.PPR_K']['indicatorArgLim'] == [0.0, 0.3]


def test_annotateIndicatorArgLimNoChangeWhenArgNotShared():
	"""Controls whose arg is not in argToGaugeInput are left untouched."""
	controls = {
		'FUEL_INTERFACE.FuelQtySelSw': {
			'description': 'Fuel selector',
			'type': 'discrete',
			'deviceId': 4,
			'commandId': 3005,
			'arg': 158,
			'argLim': [0.0, 0.5],
			'step': 0.1,
			'positions': 6,
		},
	}
	argToGaugeInput = {330: [0.0, 0.3]}  # different arg
	count = gcm.annotateIndicatorArgLim(controls, argToGaugeInput)
	assert count == 0
	assert 'indicatorArgLim' not in controls['FUEL_INTERFACE.FuelQtySelSw']


def test_annotateIndicatorArgLimSkipsReadOnlyControls():
	"""Read-only (gauge-only) controls have no 'type' field and are skipped."""
	controls = {
		'arg.330': {
			'description': 'PPR_button_K',
			'arg': 330,
			# no 'type' key — this is a gauge-only control
		},
	}
	argToGaugeInput = {330: [0.0, 0.3]}
	count = gcm.annotateIndicatorArgLim(controls, argToGaugeInput)
	assert count == 0
	assert 'indicatorArgLim' not in controls['arg.330']


def test_annotateIndicatorArgLimEqualRangesStillAnnotates():
	"""When gaugeInput == argLim the field is still emitted (ranges are equal
	but the roles remain distinct: send vs. read)."""
	controls = {
		'DEVICE.SomeSwitch': {
			'description': 'Some switch',
			'type': 'discrete',
			'deviceId': 5,
			'commandId': 3010,
			'arg': 200,
			'argLim': [0.0, 1.0],
			'step': 1.0,
			'positions': 2,
		},
	}
	argToGaugeInput = {200: [0.0, 1.0]}  # equal ranges
	count = gcm.annotateIndicatorArgLim(controls, argToGaugeInput)
	assert count == 1
	assert controls['DEVICE.SomeSwitch']['indicatorArgLim'] == [0.0, 1.0]


def test_annotateIndicatorArgLimMultiElementEmitsIndicatorPositions():
	"""A >2-element gaugeInput emits indicatorPositions, not indicatorArgLim."""
	controls = {
		'DEVICE.RotorPitch': {
			'description': 'Rotor pitch',
			'type': 'discrete',
			'deviceId': 6,
			'commandId': 3020,
			'arg': 36,
			'argLim': [1.0, 15.0],
			'step': 1.0,
			'positions': 15,
		},
	}
	stopValues = [1.0, 2.0, 3.0, 5.0, 8.0, 15.0]  # non-linear scale
	argToGaugeInput = {36: stopValues}
	count = gcm.annotateIndicatorArgLim(controls, argToGaugeInput)
	assert count == 1
	assert controls['DEVICE.RotorPitch']['indicatorPositions'] == stopValues
	assert 'indicatorArgLim' not in controls['DEVICE.RotorPitch']


def test_annotateIndicatorArgLimSingleElementEmitsNeither():
	"""A 1-element gaugeInput is excluded by the len>=2 guard before annotation."""
	controls = {
		'DEVICE.FixedLight': {
			'description': 'Fixed indicator',
			'type': 'discrete',
			'deviceId': 7,
			'commandId': 3030,
			'arg': 50,
			'argLim': [0.0, 1.0],
			'step': 1.0,
			'positions': 2,
		},
	}
	# 1-element inputs are excluded by len>=2 in argToGaugeInput build,
	# so this arg never reaches annotateIndicatorArgLim.
	argToGaugeInput = {}  # as it would be after filtering
	count = gcm.annotateIndicatorArgLim(controls, argToGaugeInput)
	assert count == 0
	assert 'indicatorArgLim' not in controls['DEVICE.FixedLight']
	assert 'indicatorPositions' not in controls['DEVICE.FixedLight']


# ─── processRawCommands ────────────────────────────────────────────────────────

# Common fixture data for processRawCommands tests.
# Device 78 = JESTER_WHEEL (F-4E style: table keyed by device name).
# Device 87 = GEORGE_AI (AH-64D style: table keyed by *_commands name via deviceTableMap).
_DEVICES = {'JESTER_WHEEL': 78, 'GEORGE_AI': 87}
_DEVICE_TABLE_MAP = {87: 'george_commands'}  # int keys, as main() produces
_COMMAND_TABLES = {
	'JESTER_WHEEL': {
		'JESTER_COMMAND_EJECT': 3128,
		'JESTER_COMMAND_IDLE': 3129,
	},
	'george_commands': {
		'ShowHideMenu': 3001,
		'HatUp': 3002,
	},
}


def test_processRawCommandsAllUnbound():
	"""All commands in a pure-AI-crew table (no element bindings) are emitted as raw."""
	# No element commands → all table entries should become raw.
	elements = {}
	result = gcm.processRawCommands(_COMMAND_TABLES, _DEVICE_TABLE_MAP, _DEVICES, elements, {})
	assert 'JESTER_WHEEL.JESTER_COMMAND_EJECT' in result
	assert result['JESTER_WHEEL.JESTER_COMMAND_EJECT'] == {
		'description': 'JESTER_COMMAND_EJECT',
		'type': 'raw',
		'deviceId': 78,
		'commandId': 3128,
	}
	assert 'JESTER_WHEEL.JESTER_COMMAND_IDLE' in result
	assert 'GEORGE_AI.ShowHideMenu' in result
	assert 'GEORGE_AI.HatUp' in result
	assert len(result) == 4


def test_processRawCommandsSkipsBoundCommands():
	"""Commands that appear in a clickable element are NOT emitted as raw."""
	# JESTER_COMMAND_EJECT (device 78, cmd 3128) is bound to an element.
	elements = {'elem_eject': {'device': 78, 'action': [3128]}}
	result = gcm.processRawCommands(_COMMAND_TABLES, _DEVICE_TABLE_MAP, _DEVICES, elements, {})
	assert 'JESTER_WHEEL.JESTER_COMMAND_EJECT' not in result
	assert 'JESTER_WHEEL.JESTER_COMMAND_IDLE' in result  # unbound → emitted


def test_processRawCommandsSkipsExistingControls():
	"""Commands already in existingControls are not duplicated."""
	elements = {}
	existing = {'JESTER_WHEEL.JESTER_COMMAND_EJECT': {'type': 'discrete', 'deviceId': 78, 'commandId': 3128}}
	result = gcm.processRawCommands(_COMMAND_TABLES, _DEVICE_TABLE_MAP, _DEVICES, elements, existing)
	assert 'JESTER_WHEEL.JESTER_COMMAND_EJECT' not in result
	assert 'JESTER_WHEEL.JESTER_COMMAND_IDLE' in result


def test_processRawCommandsDeviceTableMapStyle():
	"""george_commands table resolves device via deviceTableMap (AH-64D style)."""
	elements = {}
	result = gcm.processRawCommands(_COMMAND_TABLES, _DEVICE_TABLE_MAP, _DEVICES, elements, {})
	assert 'GEORGE_AI.ShowHideMenu' in result
	assert result['GEORGE_AI.ShowHideMenu']['deviceId'] == 87
	assert result['GEORGE_AI.ShowHideMenu']['commandId'] == 3001
	assert result['GEORGE_AI.ShowHideMenu']['type'] == 'raw'


def test_processRawCommandsUnknownTableSkipped():
	"""A command table with no matching device is silently skipped."""
	commandTables = {'orphan_commands': {'DoSomething': 9999}}
	result = gcm.processRawCommands(commandTables, {}, _DEVICES, {}, {})
	assert result == {}


# ─── processRawCommands with keybindings ───────────────────────────────────────

# UH-1H style: one generic table shared by every device.
_KB_DEVICES = {'ELEC_INTERFACE': 1, 'ENGINE_INTERFACE': 3}
_KB_DEVICE_TABLE_MAP = {1: 'device_commands', 3: 'device_commands'}
_KB_COMMAND_TABLES = {'device_commands': {'Button_18': 3018, 'Button_19': 3019}}


def _startBinding():
	return {'kind': 'key', 'deviceId': 3, 'down': 3018, 'up': 3018, 'valueDown': 1.0, 'valueUp': 0.0, 'name': 'Start-up engine'}


def test_processRawCommandsKeybindingsEmitOnlyBoundPairs():
	"""With keybindings, raw entries come from bound (device, command) pairs, named after the device's table."""
	result = gcm.processRawCommands(_KB_COMMAND_TABLES, _KB_DEVICE_TABLE_MAP, _KB_DEVICES, {}, {}, keybindings=[_startBinding()])
	assert result == {
		'ENGINE_INTERFACE.Button_18': {
			'description': 'Start-up engine',
			'type': 'raw',
			'deviceId': 3,
			'commandId': 3018,
			'bindings': [{'name': 'Start-up engine', 'valueDown': 1.0, 'valueUp': 0.0}],
		},
	}


def test_processRawCommandsKeybindingsSkipClickablePairs():
	"""A bound pair that is also a clickable element is not emitted as raw."""
	elements = {'START-PTR': {'device': 3, 'action': [3018]}}
	breaker = {'kind': 'key', 'deviceId': 1, 'down': 3018, 'valueDown': 0.02, 'name': 'CB Prox. warn.'}
	result = gcm.processRawCommands(_KB_COMMAND_TABLES, _KB_DEVICE_TABLE_MAP, _KB_DEVICES, elements, {}, keybindings=[_startBinding(), breaker])
	assert list(result) == ['ELEC_INTERFACE.Button_18']


def test_processRawCommandsKeybindingsSkipExistingControls():
	existing = {'ENGINE_INTERFACE.Button_18': {'type': 'discrete', 'deviceId': 3, 'commandId': 3018}}
	result = gcm.processRawCommands(_KB_COMMAND_TABLES, _KB_DEVICE_TABLE_MAP, _KB_DEVICES, {}, existing, keybindings=[_startBinding()])
	assert result == {}


def test_processRawCommandsKeybindingsGroupSeveralBindingsOnOnePair():
	"""Bindings that share a pair (e.g. circuit breakers told apart by value) become one entry listing each binding."""
	bindings = [
		{'kind': 'key', 'deviceId': 1, 'down': 3018, 'valueDown': 0.0, 'name': 'CB IFF APX 1'},
		{'kind': 'key', 'deviceId': 1, 'down': 3018, 'valueDown': 0.02, 'name': 'CB Prox. warn.'},
	]
	result = gcm.processRawCommands(_KB_COMMAND_TABLES, _KB_DEVICE_TABLE_MAP, _KB_DEVICES, {}, {}, keybindings=bindings)
	entry = result['ELEC_INTERFACE.Button_18']
	assert entry['description'] == 'CB IFF APX 1 (+1 more)'
	assert entry['bindings'] == [{'name': 'CB IFF APX 1', 'valueDown': 0.0}, {'name': 'CB Prox. warn.', 'valueDown': 0.02}]


def test_processRawCommandsKeybindingsRecordOnlyThisCommandsValues():
	"""When down and up send different commands, each entry keeps only the value sent on its own command."""
	binding = {'kind': 'key', 'deviceId': 3, 'down': 3018, 'up': 3019, 'valueDown': 1.0, 'valueUp': 0.0, 'name': 'Split'}
	result = gcm.processRawCommands(_KB_COMMAND_TABLES, _KB_DEVICE_TABLE_MAP, _KB_DEVICES, {}, {}, keybindings=[binding])
	assert result['ENGINE_INTERFACE.Button_18']['bindings'] == [{'name': 'Split', 'valueDown': 1.0}]
	assert result['ENGINE_INTERFACE.Button_19']['bindings'] == [{'name': 'Split', 'valueUp': 0.0}]


def test_processRawCommandsKeybindingsAxisBinding():
	binding = {'kind': 'axis', 'deviceId': 3, 'action': 3019, 'name': 'Throttle'}
	result = gcm.processRawCommands(_KB_COMMAND_TABLES, _KB_DEVICE_TABLE_MAP, _KB_DEVICES, {}, {}, keybindings=[binding])
	assert result['ENGINE_INTERFACE.Button_19']['bindings'] == [{'name': 'Throttle', 'axis': True}]


def test_processRawCommandsKeybindingsUnnamedDeviceAndCommand():
	"""A device or command with no name in the Lua files falls back to dev<id> / cmd_<id>."""
	binding = {'kind': 'key', 'deviceId': 0, 'down': 3256, 'valueDown': 1.0, 'name': 'Flashlight'}
	result = gcm.processRawCommands(_KB_COMMAND_TABLES, _KB_DEVICE_TABLE_MAP, _KB_DEVICES, {}, {}, keybindings=[binding])
	assert list(result) == ['dev0.cmd_3256']
	assert result['dev0.cmd_3256']['deviceId'] == 0
	assert result['dev0.cmd_3256']['commandId'] == 3256


def test_processRawCommandsListenedCommandsAddUnboundPairs():
	"""Commands a scripted device listens for become raw entries even with no binding."""
	listened = [{'deviceId': 3, 'commandId': 3019}, {'deviceId': 3, 'commandId': 3500}]
	result = gcm.processRawCommands(_KB_COMMAND_TABLES, _KB_DEVICE_TABLE_MAP, _KB_DEVICES, {}, {}, keybindings=[], listenedCommands=listened)
	assert result == {
		'ENGINE_INTERFACE.Button_19': {'description': 'Button_19', 'type': 'raw', 'deviceId': 3, 'commandId': 3019},
		'ENGINE_INTERFACE.cmd_3500': {'description': 'cmd_3500', 'type': 'raw', 'deviceId': 3, 'commandId': 3500},
	}


def test_processRawCommandsListenedCommandsSkipSimCommandsAndClickablePairs():
	"""IDs below 3000 are DCS sim commands, not device commands; clickable pairs are already controls."""
	elements = {'START-PTR': {'device': 3, 'action': [3019]}}
	listened = [{'deviceId': 3, 'commandId': 68}, {'deviceId': 3, 'commandId': 3019}]
	result = gcm.processRawCommands(_KB_COMMAND_TABLES, _KB_DEVICE_TABLE_MAP, _KB_DEVICES, elements, {}, keybindings=[], listenedCommands=listened)
	assert result == {}


def test_processRawCommandsListenedCommandsKeepBindingEntry():
	"""A pair that is both bound and listened keeps the binding's description and values."""
	listened = [{'deviceId': 3, 'commandId': 3018}]
	result = gcm.processRawCommands(_KB_COMMAND_TABLES, _KB_DEVICE_TABLE_MAP, _KB_DEVICES, {}, {}, keybindings=[_startBinding()], listenedCommands=listened)
	assert result['ENGINE_INTERFACE.Button_18']['description'] == 'Start-up engine'
	assert len(result) == 1
