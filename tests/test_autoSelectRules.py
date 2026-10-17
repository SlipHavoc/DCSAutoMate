"""Unit tests for engine.autoSelectRules — decisions Auto Select makes from telemetry."""
import importlib
import os
import sys
import types

import pytest

projectRoot = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if projectRoot not in sys.path:
	sys.path.insert(0, projectRoot)

from engine.autoSelectRules import AutoSelectContext, applyModuleAutoSelect, autoSelectReport, classifyPosition, isEngineRunning, timeOfDay


def test_positionClassification():
	assert classifyPosition(altAGL=1.2, altMSL=40.0, trueAirSpeed=0.0) == 'ground'
	assert classifyPosition(altAGL=18.5, altMSL=18.9, trueAirSpeed=0.0) == 'carrier' # Deck height over the sea.
	assert classifyPosition(altAGL=18.5, altMSL=18.9, trueAirSpeed=60.0) == 'air' # Flying low over the sea.
	assert classifyPosition(altAGL=1200.0, altMSL=1500.0, trueAirSpeed=150.0) == 'air'


def test_timeOfDayIsDayFrom0600To2000():
	assert timeOfDay(6 * 3600) == 'day'
	assert timeOfDay(20 * 3600) == 'day'
	assert timeOfDay(5 * 3600 + 3599) == 'night'
	assert timeOfDay(20 * 3600 + 1) == 'night'
	assert timeOfDay(24 * 3600 + 12 * 3600) == 'day' # Mission times past midnight wrap around.


def test_contextRemembersWhatTheHookRead():
	context, _ = fakeContext('Cold Start', {'arg.PLT_HelmetMountedKit': 0.5})
	context.read('arg.PLT_HelmetMountedKit', 'arg.missing')
	assert context.reads == {'arg.PLT_HelmetMountedKit': 0.5, 'arg.missing': None}


def reportFor(**changes):
	"""An FA-18C hot spawn on the ground at 14:32:05 with JHMCS, with changes for each test."""
	facts = {
		'aircraft': 'FA-18C_hornet',
		'scriptFile': 'FA-18C',
		'altAGL': 1.23,
		'altMSL': 40.0,
		'trueAirSpeed': 0.0,
		'engineInfo': {'RPM': {'left': 65.24, 'right': 64.8}},
		'clockSeconds': 14 * 3600 + 32 * 60 + 5,
		'script': 'Hot Start',
		'hookReads': {'arg.PLT_HelmetMountedKit': 0.0},
		'hookResult': {'vars': {'hmd': 'withJhmcs'}},
		'setVars': ['time: Day', 'hmd: withJhmcs'],
		'unsetVars': [],
	}
	facts.update(changes)
	return autoSelectReport(**facts)


def test_reportShowsWhatWasDetectedAndWhy():
	assert reportFor() == [
		'Auto Select:',
		'  Aircraft: FA-18C_hornet (FA-18C scripts)',
		'  Position: on the ground (AGL 1.2 m; under 5 m is the ground)',
		'  Engines: running (RPM left 65.2, right 64.8; over 0.05 is running)',
		'  Mission time: 14:32:05, so day (06:00 to 20:00)',
		'  Script: Hot Start',
		'  FA-18C autoSelect read arg.PLT_HelmetMountedKit = 0, and set hmd = withJhmcs',
		'  Set: time: Day, hmd: withJhmcs',
	]


def test_reportExplainsCarrierAirAndEnginesOff():
	carrier = reportFor(altAGL=18.5, altMSL=18.9, engineInfo={'RPM': {'left': 0.0, 'right': 0.0}}, script='Cold Start')
	assert '  Position: on a carrier deck (AGL 18.5 m, MSL 18.9 m, TAS 0.0 m/s; deck is 15 to 25 m MSL under 40 m/s)' in carrier
	assert '  Engines: off (RPM left 0.0, right 0.0; over 0.05 is running)' in carrier
	air = reportFor(altAGL=1200.0, altMSL=1500.0, trueAirSpeed=150.0, script='Air Start')
	assert '  Position: in the air (AGL 1200.0 m, TAS 150.0 m/s)' in air


def test_reportShowsTheHooksChoiceReasonAndUnsetVars():
	report = reportFor(script='Cold Start with Preflight', hookReads={}, hookResult={'script': 'Cold Start with Preflight', 'reason': 'battery, generators and APU are on'}, unsetVars=['apu'])
	assert '  FA-18C autoSelect chose Cold Start with Preflight (battery, generators and APU are on)' in report
	assert '  Not set, please choose: apu' in report


def test_reportWithoutHookOrMissionTime():
	report = reportFor(clockSeconds=None, hookReads={}, hookResult={})
	assert '  Mission time: unknown, so time of day not set' in report
	assert not any('autoSelect' in line for line in report)


def fakeContext(script, cockpit):
	"""A context over a fake cockpit; records each batch of controls read."""
	batches = []
	def readControls(controls):
		batches.append(list(controls))
		return {c: cockpit[c] for c in controls if c in cockpit}
	context = AutoSelectContext(script, telemetry={}, readControls=readControls)
	return context, batches


def test_contextReadsControlsInOneBatchAndFillsMissingWithNone():
	context, batches = fakeContext('Cold Start', {'SYS.battery': 1})
	assert context.read('SYS.battery', 'SYS.gen_1') == {'SYS.battery': 1, 'SYS.gen_1': None}
	assert batches == [['SYS.battery', 'SYS.gen_1']]


def test_moduleWithoutAutoSelectChangesNothing():
	context, _ = fakeContext('Cold Start', {})
	assert applyModuleAutoSelect(types.ModuleType('noHook'), context) == {}


def test_moduleAutoSelectResultIsReturned():
	module = types.ModuleType('withHook')
	module.autoSelect = lambda context: {'script': f'{context.script} with Preflight'}
	context, _ = fakeContext('Cold Start', {})
	assert applyModuleAutoSelect(module, context) == {'script': 'Cold Start with Preflight'}


def test_moduleAutoSelectReturningNothingChangesNothing():
	module = types.ModuleType('returnsNone')
	module.autoSelect = lambda context: None
	context, _ = fakeContext('Cold Start', {})
	assert applyModuleAutoSelect(module, context) == {}


# C-130J: values from DCSControlPanel snapshots, cold and dark vs. a "preflight complete" spawn.
C130_PREFLIGHTED = {
	'ENGINE_APU_CTRL.battery': 1,
	'ENGINE_APU_CTRL.gen_1': 1,
	'ENGINE_APU_CTRL.gen_2': 1,
	'ENGINE_APU_CTRL.gen_3': 1,
	'ENGINE_APU_CTRL.gen_4': 1,
	'ENGINE_APU_CTRL.ext_elec': 2, # APU
}
C130_COLD_AND_DARK = {**{name: 0 for name in C130_PREFLIGHTED}, 'ENGINE_APU_CTRL.ext_elec': 1} # OFF

def c130():
	return importlib.import_module('DCSAutoMateScripts.C-130J')


def test_c130PreflightedSpawnPicksColdStartWithPreflight():
	context, _ = fakeContext('Cold Start', C130_PREFLIGHTED)
	assert c130().autoSelect(context) == {'script': 'Cold Start with Preflight'}


def test_c130ColdAndDarkKeepsColdStart():
	context, _ = fakeContext('Cold Start', C130_COLD_AND_DARK)
	assert c130().autoSelect(context) == {}


def test_c130PartlyPoweredKeepsColdStart():
	"""A player part way through a manual start may have the battery on but not the rest."""
	context, _ = fakeContext('Cold Start', {**C130_PREFLIGHTED, 'ENGINE_APU_CTRL.gen_3': 0})
	assert c130().autoSelect(context) == {}


def test_c130NoAnswerFromDcsKeepsColdStart():
	context, _ = fakeContext('Cold Start', {})
	assert c130().autoSelect(context) == {}


def test_c130OnlyChecksWhenColdStartWasPicked():
	context, batches = fakeContext('Hot Start', C130_PREFLIGHTED)
	assert c130().autoSelect(context) == {}
	assert batches == []


# FA-18C: arg 909 PLT_HelmetMountedKit, from DCSControlPanel snapshots of each Mission Editor helmet option.
def fa18():
	return importlib.import_module('DCSAutoMateScripts.FA-18C')


def test_fa18JhmcsSetsWithJhmcs():
	context, _ = fakeContext('Cold Start', {'arg.PLT_HelmetMountedKit': 0.0})
	assert fa18().autoSelect(context) == {'vars': {'hmd': 'withJhmcs'}}


def test_fa18NvgOrNoHelmetDeviceSetsNoJhmcs():
	for kit in (1.0, 0.5):
		context, _ = fakeContext('Hot Start', {'arg.PLT_HelmetMountedKit': kit})
		assert fa18().autoSelect(context) == {'vars': {'hmd': 'noJhmcs'}}


def test_fa18NoAnswerFromDcsLeavesHmdAlone():
	context, _ = fakeContext('Cold Start', {})
	assert fa18().autoSelect(context) == {}


# F-16C: same arg 909 values as the FA-18C (snapshots of each Mission Editor helmet option).
def f16():
	return importlib.import_module('DCSAutoMateScripts.F-16C')


def test_f16JhmcsSetsWithJhmcs():
	context, _ = fakeContext('Cold Start', {'arg.PLT_HelmetMountedKit': 0.0})
	assert f16().autoSelect(context) == {'vars': {'hmd': 'withJhmcs'}}


def test_f16NvgOrNoHelmetDeviceSetsNoJhmcs():
	for kit in (1.0, 0.5):
		context, _ = fakeContext('Cold Start', {'arg.PLT_HelmetMountedKit': kit})
		assert f16().autoSelect(context) == {'vars': {'hmd': 'noJhmcs'}}


def test_f16NoAnswerFromDcsLeavesHmdAlone():
	context, _ = fakeContext('Cold Start', {})
	assert f16().autoSelect(context) == {}


# AH-64D: the Longbow radar is in the loadout (LoGetPayloadInfo), not the cockpit, and can be added from the rearming screen during start-up.
LONGBOW = {'CLSID': '{AN_APG_78}', 'count': 1}
HELLFIRE_RACK = {'CLSID': '{M299_4xAGM_114L}', 'count': 4}
EMPTY_STATION = {'CLSID': '', 'count': 0}

def ah64():
	return importlib.import_module('DCSAutoMateScripts.AH-64D')


def telemetryContext(script, payload):
	return AutoSelectContext(script, telemetry={'LoGetPayloadInfo': payload}, readControls=lambda controls: {})


def test_ah64LongbowFoundInStationsKeyedByNumber():
	"""The UDP telemetry decodes Stations as a dict keyed by station number."""
	assert ah64().longbowEquipped({'1': HELLFIRE_RACK, '2': EMPTY_STATION, '5': LONGBOW}) is True
	assert ah64().longbowEquipped({'1': HELLFIRE_RACK, '2': EMPTY_STATION}) is False


def test_ah64LongbowFoundInStationsList():
	"""A G: query can decode Stations as a JSON array."""
	assert ah64().longbowEquipped([HELLFIRE_RACK, LONGBOW]) is True
	assert ah64().longbowEquipped([HELLFIRE_RACK, EMPTY_STATION]) is False


def test_ah64LongbowWithZeroCountIsNotEquipped():
	assert ah64().longbowEquipped({'5': {'CLSID': '{AN_APG_78}', 'count': 0}}) is False


def test_ah64UnreadableStationsIsUnknown():
	for stations in (None, 0, 'Stations'):
		assert ah64().longbowEquipped(stations) is None


def test_ah64AutoSelectSetsRadarFromSpawnLoadout():
	context = telemetryContext('Cold Start', {'Stations': {'1': HELLFIRE_RACK, '5': LONGBOW}})
	assert ah64().autoSelect(context) == {'vars': {'radar': 'equipped'}, 'reason': 'Longbow radar in the loadout'}


def test_ah64AutoSelectWithoutRadarChecksAgainAtEnd():
	"""Also overrides a saved 'equipped' choice left over from an earlier flight."""
	context = telemetryContext('Hot Start', {'Stations': {'1': HELLFIRE_RACK}})
	assert ah64().autoSelect(context) == {'vars': {'radar': 'detect'}, 'reason': 'no Longbow radar in the loadout yet'}


def test_ah64AutoSelectWithoutPayloadDataLeavesRadarAlone():
	for payload in (None, {}):
		assert ah64().autoSelect(telemetryContext('Cold Start', payload)) == {}


def runAh64Start(functionName, radar, stations):
	"""Run an AH-64D start script as the executor does, batch by batch; the fake loadout read answers with stations.

	Returns (batches, readsAtBatch): the command batches, and how many batches had already run at each loadout read.
	"""
	from engine.SequenceHelper import SequenceHelper
	helper = SequenceHelper({'dcsSavedGamesPath': '', 'udpUiWireLogEnabled': False, 'udpBiosWireLogEnabled': False})
	batches = []
	readsAtBatch = []
	def reader(control):
		assert control == 'telemetry/LoGetPayloadInfo.Stations'
		readsAtBatch.append(len(batches))
		return stations
	helper.setControlReader(reader)
	script = getattr(ah64(), functionName)({'debug': True}, {'time': 'day', 'radar': radar}, helper)
	for _ in script:
		batches.append(helper.takeQueued())
	batches.append(helper.takeQueued())
	return batches, readsAtBatch


def messages(batch):
	return [c.get('arg') if c['cmd'] == 'scriptSpeech' else c.get('msg') for c in batch if c['cmd'] in ('', 'scriptSpeech')]


def fcrPresses(batch):
	return [c['cmd'] for c in batch if c['cmd'].startswith('MFD_PLT_LEFT.') and c.get('arg') == 1]


FCR_ON_PRESSES = ['MFD_PLT_LEFT.FCR', 'MFD_PLT_LEFT.T6', 'MFD_PLT_LEFT.R6', 'MFD_PLT_LEFT.L4', 'MFD_PLT_LEFT.T6', 'MFD_PLT_LEFT.VID'] # FCR, UTIL, MMA PINNED, FCR BIT OVERRIDE, UTIL, back to VID.
FCR_REMINDER = 'No Longbow radar detected. Power on FCR if equipped, FCR page, util, MMA pinned, FCR bit override.'

@pytest.mark.parametrize('functionName', ['ColdStart', 'HotStart'])
def test_ah64StartChecksLoadoutInFinalBatchAndTurnsOnFcr(functionName):
	"""The loadout is read after all the cockpit setup has run, so a radar added during start-up is found."""
	batches, readsAtBatch = runAh64Start(functionName, 'detect', [HELLFIRE_RACK, LONGBOW])
	assert readsAtBatch == [len(batches) - 1]
	assert messages(batches[-1])[0] == 'Longbow radar detected, powering on.'
	assert fcrPresses(batches[-1]) == FCR_ON_PRESSES
	assert FCR_REMINDER not in [m for batch in batches for m in messages(batch)]


def test_ah64ColdStartTurnsOnFcrBeforeAlignmentWait():
	batches, _ = runAh64Start('ColdStart', 'detect', [LONGBOW])
	commands = [c['cmd'] for c in batches[-1]]
	assert commands.index('MFD_PLT_LEFT.VID') < commands.index('scriptTimerEnd')


@pytest.mark.parametrize('functionName', ['ColdStart', 'HotStart'])
@pytest.mark.parametrize('stations', [{'1': HELLFIRE_RACK}, None], ids=['noRadar', 'unreadable'])
def test_ah64StartWithoutDetectedRadarRemindsAndSkipsFcr(functionName, stations):
	batches, _ = runAh64Start(functionName, 'detect', stations)
	assert messages(batches[-1])[0] == FCR_REMINDER
	assert fcrPresses(batches[-1]) == []


def test_ah64StartTrustsRadarEquippedSetting():
	batches, readsAtBatch = runAh64Start('HotStart', 'equipped', None)
	assert readsAtBatch == []
	assert fcrPresses(batches[-1]) == FCR_ON_PRESSES


# AH-64D waypoint entry: LoGetPlayerSeat is 0 in the back seat (pilot) and 1 in the front seat (CPG), checked in DCS 2.9.30.
WAYPOINT = {'mgrs8': '37T DK 1234 5678', 'altFeet': 120.0}

def runAh64Waypoints(functionName, seat, playerSeat):
	"""Run Load Route or Load Scratchpad with one waypoint; the fake DCS reports playerSeat (None = no answer).  Returns (commands, reads)."""
	from engine.SequenceHelper import SequenceHelper
	helper = SequenceHelper({'dcsSavedGamesPath': '', 'udpUiWireLogEnabled': False, 'udpBiosWireLogEnabled': False})
	helper.getRouteData = lambda routeFile, routeName: {'waypoints': [WAYPOINT]}
	helper.getScratchpadData = lambda fileName: [WAYPOINT]
	reads = []
	def reader(control):
		reads.append(control)
		return playerSeat
	helper.setControlReader(reader)
	scriptVars = {'routeFile': 'route.json', 'routeName': 'Route', 'scratchpadFile': 'scratchpad.txt', 'altitude': 'forceGround', 'seat': seat}
	return helper.collectSequence(getattr(ah64(), functionName)({'debug': True}, scriptVars, helper)), reads


def crewStations(commands):
	"""Which seats' KU and right MPD the commands press."""
	return {command['cmd'].split('.')[0].replace('MFD_', '').replace('_RIGHT', '').replace('KU_', '') for command in commands if command['cmd'].startswith(('KU_', 'MFD_'))}


@pytest.mark.parametrize('functionName', ['LoadRoute', 'LoadScratchpad'])
@pytest.mark.parametrize('playerSeat,station', [(0, 'PLT'), (1, 'CPG')])
def test_ah64WaypointEntryDetectsTheSeat(functionName, playerSeat, station):
	commands, reads = runAh64Waypoints(functionName, 'detect', playerSeat)
	assert reads == ['telemetry/LoGetPlayerSeat']
	assert crewStations(commands) == {station}


@pytest.mark.parametrize('functionName', ['LoadRoute', 'LoadScratchpad'])
def test_ah64WaypointEntryStopsIfTheSeatCantBeRead(functionName):
	"""E.g. a server that doesn't allow ownship export."""
	commands, _ = runAh64Waypoints(functionName, 'detect', None)
	assert crewStations(commands) == set()
	assert any('choose Pilot or Co-Pilot' in command.get('msg', '') for command in commands)


@pytest.mark.parametrize('functionName', ['LoadRoute', 'LoadScratchpad'])
@pytest.mark.parametrize('seat,station', [('pilot', 'PLT'), ('coPilot', 'CPG')])
def test_ah64WaypointEntryUsesTheChosenSeatWithoutAsking(functionName, seat, station):
	commands, reads = runAh64Waypoints(functionName, seat, 1 - ['pilot', 'coPilot'].index(seat))
	assert reads == []
	assert crewStations(commands) == {station}


def test_ah64SeatDefaultsToDetect():
	for script in ah64().getScriptData()['scripts']:
		if 'seat' in script['vars']:
			assert next(iter(script['vars']['seat']['options'])) == 'detect', script['name']


def test_coldEngineWithRpmNoiseIsNotRunning():
	"""C-101CC cold and dark reports left RPM wavering up to ~0.001%."""
	assert isEngineRunning({'RPM': {'left': 0.001, 'right': 0}}) is False


def test_idlingEngineIsRunning():
	assert isEngineRunning({'RPM': {'left': 0, 'right': 63.2}}) is True


def test_engineReportedAsFractionIsRunning():
	"""Some modules may report RPM as a 0-1 fraction rather than percent; idle is still well above the threshold."""
	assert isEngineRunning({'RPM': {'left': 0.21, 'right': 0.0}}) is True


def test_singleNumberRpm():
	assert isEngineRunning({'RPM': 45.0}) is True
	assert isEngineRunning({'RPM': 0.0005}) is False


def test_missingOrMalformedEngineInfo():
	assert isEngineRunning({}) is False
	assert isEngineRunning(None) is False
	assert isEngineRunning({'RPM': {'left': None, 'right': 'n/a'}}) is False
