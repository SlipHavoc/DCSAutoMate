"""Tests for utils.controlReference — the data behind docs/controlReference.html."""
import json
import os
import time

from utils.controlReference import buildControlReference, controlReferenceIsStale, controlRows


def rowFor(controls, name):
	return next(row for row in controlRows(controls) if row['name'] == name)


# Entries copied from config/controlMappings (C-130J-30, AH-64D_BLK_II, F-16C_50).
DISCRETE = {'arg': 1307, 'argLim': [0.0, 1.0], 'commandId': 3028, 'description': 'Aug Crew CNI-MU DEL Key', 'deviceId': 27, 'elementName': 'PNT_AUG_CNI_DEL_1307', 'positions': 2, 'step': 1.0, 'type': 'discrete'}
POSITION_MAP = {'arg': 610, 'crewAccess': [0], 'description': 'CMWS PWR Switch, OFF/ON/TEST(momentarily)', 'elementName': 'pnt_610', 'positionMap': [{'commandId': 3001, 'deviceId': 80, 'value': -1.0}, None, {'commandId': 3002, 'deviceId': 80, 'value': 1.0}], 'positions': 3, 'type': 'discrete'}
CONTINUOUS = {'arg': 70, 'argLim': [-1.0, 1.0], 'commandId': 3016, 'description': 'AFCS Turn Control Knob / Center Detent', 'deviceId': 52, 'elementName': 'PNT_AFCS_TURN_KNOB_70', 'type': 'continuous'}
RELATIVE = {'arg': 322, 'argLim': [0.0, 1.0], 'commandId': 3015, 'decrementValue': -0.5, 'description': 'APU Start Switch', 'deviceId': 2, 'elementName': 'PNT_APU_CONTROL_322', 'incrementValue': 0.5, 'positions': 3, 'sendProtocol': 'C', 'step': 0.5, 'type': 'relative'}
RAW = {'bindings': [{'name': 'Pressure Set Knob - CCW', 'valuePressed': -1.0}, {'name': 'Pressure Set Knob - CW', 'valuePressed': 1.0}], 'commandId': 3002, 'description': 'Pressure Set Knob - CCW (+1 more)', 'deviceId': 15, 'type': 'raw'}
RAW_DUPLICATE_BINDINGS = {'bindings': [{'name': 'Yoke - Autopilot Disconnect', 'valueDown': 1.0, 'valueUp': 0.0}, {'name': 'Yoke - Autopilot Disconnect', 'valueDown': 1.0, 'valueUp': 0.0}], 'commandId': 3017, 'description': 'Yoke - Autopilot Disconnect (+1 more)', 'deviceId': 52, 'type': 'raw'}
RAW_AXIS = {'bindings': [{'axis': True, 'name': 'ADI Pitch Trim Knob'}], 'commandId': 3002, 'description': 'ADI Pitch Trim Knob', 'deviceId': 50, 'type': 'raw'}
ARG_READ = {'arg': 124, 'description': 'ADI_Speed'}
INDICATOR = {'description': 'ccMFD_AH64 (all fields)', 'indicationId': 11}
INDICATOR_FIELD = {'description': '1', 'fieldName': '1', 'indicationId': 11}


def test_discreteValuesArePositionIndexes():
	row = rowFor({'AC_CNI.DEL': DISCRETE}, 'AC_CNI.DEL')
	assert row == {
		'name': 'AC_CNI.DEL',
		'description': 'Aug Crew CNI-MU DEL Key',
		'group': 'AC_CNI',
		'kind': 'control',
		'type': 'discrete',
		'values': '0 to 1',
		'details': 'arg 1307 · device 27 · command 3028 · arg range 0 to 1 · step 1 · PNT_AUG_CNI_DEL_1307',
	}


def test_positionMapListsEachPositionsCommand():
	row = rowFor({'CMWS.CMWS_PWR': POSITION_MAP}, 'CMWS.CMWS_PWR')
	assert row['values'] == '0 to 2'
	assert row['details'] == 'arg 610 · device 80 · position commands 0: 3001 = -1, 1: none, 2: 3002 = 1 · crew 0 · pnt_610'


def test_positionMapWithSendAndReadbackValues():
	"""CH-47F circuit breakers send one value per position and may read back a different one."""
	control = {'arg': 1, 'description': 'Breaker', 'positionMap': [{'commandId': 3006, 'deviceId': 20, 'readbackValue': 0, 'sendValue': 0}, {'commandId': 3006, 'deviceId': 20, 'readbackValue': 0.6, 'sendValue': 1}], 'positions': 2, 'type': 'discrete'}
	assert rowFor({'PDP1.1A06': control}, 'PDP1.1A06')['details'] == 'arg 1 · device 20 · position commands 0: 3006 = 0, 1: 3006 = 1 (reads 0.6)'


def test_bindingsWithOnlySomeValues():
	bindings = [{'name': 'Radar elevation down', 'valuePressed': -1.0, 'valueUp': 0.0}, {'name': 'Anti-Collision Lights switch', 'valueUp': -1.0}, {'name': 'Console Lights Control - Continuous Decrease'}]
	row = rowFor({'DEV.x': {'bindings': bindings, 'commandId': 1, 'deviceId': 2, 'type': 'raw'}}, 'DEV.x')
	assert row['values'] == 'Radar elevation down: -1, release 0, Anti-Collision Lights switch: release -1, Console Lights Control - Continuous Decrease'


def test_continuousValuesAreTheArgRange():
	row = rowFor({'AP_INTERFACE.cmd_3016': CONTINUOUS}, 'AP_INTERFACE.cmd_3016')
	assert row['values'] == '-1 to 1'
	assert row['details'] == 'arg 70 · device 52 · command 3016 · PNT_AFCS_TURN_KNOB_70'


def test_relativeValuesAreSteps():
	row = rowFor({'ENGINE_APU_CTRL.apu_selector': RELATIVE}, 'ENGINE_APU_CTRL.apu_selector')
	assert row['values'] == '+1 / -1'
	assert row['details'] == 'arg 322 · device 2 · command 3015 · arg range 0 to 1 · 3 positions · step 0.5 · increment 0.5 · decrement -0.5 · protocol C · PNT_APU_CONTROL_322'


def test_rawValuesComeFromTheBindings():
	controls = {'BARO_ALTIMETER.PressureSet_ITER': RAW, 'AP_INTERFACE.cmd_3017': RAW_DUPLICATE_BINDINGS, 'ADI.Button_2': RAW_AXIS}
	assert rowFor(controls, 'BARO_ALTIMETER.PressureSet_ITER')['values'] == 'Pressure Set Knob - CCW: -1, Pressure Set Knob - CW: 1'
	assert rowFor(controls, 'AP_INTERFACE.cmd_3017')['values'] == 'Yoke - Autopilot Disconnect: 1, release 0'
	assert rowFor(controls, 'ADI.Button_2')['values'] == 'ADI Pitch Trim Knob: axis'
	assert rowFor(controls, 'BARO_ALTIMETER.PressureSet_ITER')['details'] == 'device 15 · command 3002'


def test_argReadsAreGroupedTogether():
	row = rowFor({'arg.ADI_Speed': ARG_READ}, 'arg.ADI_Speed')
	assert (row['group'], row['kind'], row['type'], row['values'], row['details']) == ('arg', 'arg', 'arg (read only)', '', 'arg 124')


def test_displayFieldsAreGroupedByIndicatorName():
	controls = {'ind.11': INDICATOR, 'ind.11.1': INDICATOR_FIELD}
	whole = rowFor(controls, 'ind.11')
	field = rowFor(controls, 'ind.11.1')
	assert (whole['group'], whole['kind'], whole['type'], whole['details']) == ('ind.11 ccMFD_AH64', 'ind', 'display text', 'indicator 11')
	assert (field['group'], field['kind'], field['details']) == ('ind.11 ccMFD_AH64', 'ind', 'indicator 11 · field 1')


def test_unknownFieldsStillShowUp():
	row = rowFor({'DEV.new': {'description': 'New', 'type': 'discrete', 'positions': 2, 'futureField': [1, 2]}}, 'DEV.new')
	assert row['details'] == 'futureField [1, 2]'


def writeMapping(mappingsDir, moduleName, controls):
	with open(os.path.join(mappingsDir, f'{moduleName}.json'), 'w', encoding='utf-8') as f:
		json.dump({'moduleName': moduleName, 'controls': controls}, f)


def loadDataFile(path, prefix):
	"""The data files are JavaScript, so the page can load them from disk; strip the assignment to get the JSON back."""
	with open(path, encoding='utf-8') as f:
		text = f.read()
	assert text.startswith(prefix) and text.endswith(';\n')
	return json.loads(text[len(prefix):-2])


def test_buildWritesModuleListAndOneDataFilePerModule(tmp_path):
	mappingsDir = tmp_path / 'controlMappings'
	outputDir = tmp_path / 'controlData'
	mappingsDir.mkdir()
	writeMapping(mappingsDir, 'C-130J-30', {'AC_CNI.DEL': DISCRETE, 'arg.ADI_Speed': ARG_READ})
	writeMapping(mappingsDir, 'AH-64D_BLK_II', {'ind.11': INDICATOR, 'ind.11.1': INDICATOR_FIELD})
	(mappingsDir / 'AH-64D_BLK_II_nameMap.json').write_text('{}', encoding='utf-8')
	(mappingsDir / 'Wrong.json').write_text(json.dumps({'moduleName': 'Other', 'controls': {}}), encoding='utf-8')

	assert buildControlReference(str(mappingsDir), str(outputDir)) == ['AH-64D_BLK_II', 'C-130J-30']

	modules = loadDataFile(outputDir / 'modules.js', 'window.controlReferenceModules = ')
	assert modules == [{'name': 'AH-64D_BLK_II', 'count': 2}, {'name': 'C-130J-30', 'count': 2}]
	rows = loadDataFile(outputDir / 'C-130J-30.js', 'window.controlReferenceData["C-130J-30"] = ')
	assert rows == controlRows({'AC_CNI.DEL': DISCRETE, 'arg.ADI_Speed': ARG_READ})


def test_staleUntilBuiltThenStaleAgainWhenMappingsChange(tmp_path):
	mappingsDir = tmp_path / 'controlMappings'
	outputDir = tmp_path / 'controlData'
	mappingsDir.mkdir()
	writeMapping(mappingsDir, 'Mod', {'DEV.x': DISCRETE})
	assert controlReferenceIsStale(str(mappingsDir), str(outputDir))
	buildControlReference(str(mappingsDir), str(outputDir))
	assert not controlReferenceIsStale(str(mappingsDir), str(outputDir))

	later = time.time() + 10
	os.utime(mappingsDir / 'Mod.json', (later, later))
	assert controlReferenceIsStale(str(mappingsDir), str(outputDir))
	buildControlReference(str(mappingsDir), str(outputDir))
	assert not controlReferenceIsStale(str(mappingsDir), str(outputDir))

	writeMapping(mappingsDir, 'NewMod', {'DEV.x': DISCRETE})
	os.utime(mappingsDir / 'NewMod.json', (time.time() - 100, time.time() - 100)) # An older file copied in still counts.
	assert controlReferenceIsStale(str(mappingsDir), str(outputDir))
	buildControlReference(str(mappingsDir), str(outputDir))

	(mappingsDir / 'NewMod.json').unlink()
	assert controlReferenceIsStale(str(mappingsDir), str(outputDir))
	buildControlReference(str(mappingsDir), str(outputDir))
	assert not (outputDir / 'NewMod.js').exists()
