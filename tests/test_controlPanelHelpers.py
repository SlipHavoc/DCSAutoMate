"""Unit tests for helpers in DCSControlPanel."""

import json
import os
import sys

import pytest


# Ensure repo root is importable.
repoRoot = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if repoRoot not in sys.path:
	sys.path.insert(0, repoRoot)


# Import may pull in PySide6 at module import time.  Skip the whole module if
# PySide6 isn't available in the test environment.
pytest.importorskip('PySide6')

from DCSControlPanel import changedRefs, controlsForModule, formatSnapshotValue, moduleNamesForDropdown, parsePositionLabels, snapshotReport # noqa: E402
from network.DCSDirectManager import DCSDirectManager # noqa: E402


def reverseTranslate(control, nativeValue):
	return DCSDirectManager._reverseTranslateValue(None, control, nativeValue)


# C-130J controls from a cold-and-dark vs. preflighted snapshot (EXT PWR/APU switch is a 3-position discrete on argLim [-1, 1]).
C130_INDEX = {
	'C-130J-30/ENGINE_APU_CTRL.ext_elec': {'description': 'External Power/APU Switch', 'type': 'discrete', 'arg': 467, 'argLim': [-1.0, 1.0], 'positions': 3, 'step': 1.0},
	'C-130J-30/ENGINE_APU_CTRL.battery': {'description': 'Battery Switch', 'type': 'discrete', 'arg': 371, 'argLim': [0.0, 1.0], 'positions': 2, 'step': 1.0},
	'C-130J-30/VOLUME_MANAGER.int_vol': {'description': 'Pilot INT Volume Knob', 'type': 'continuous', 'arg': 205, 'argLim': [0.0, 1.0]},
}
C130_BEFORE = {'C-130J-30/ENGINE_APU_CTRL.ext_elec': 0.0, 'C-130J-30/ENGINE_APU_CTRL.battery': 1.0, 'C-130J-30/VOLUME_MANAGER.int_vol': 0.0}
C130_AFTER = {'C-130J-30/ENGINE_APU_CTRL.ext_elec': 1.0, 'C-130J-30/ENGINE_APU_CTRL.battery': 1.0, 'C-130J-30/VOLUME_MANAGER.int_vol': 0.80000001}


def test_changedRefsIgnoresFloatNoise():
	assert changedRefs({'a': 0.5, 'b': 0.0, 'c': 0.25}, {'a': 0.50000001, 'b': 1.0, 'c': 0.2}) == ['b', 'c']


def test_changedRefsComparesText():
	"""Loadout CLSIDs are text: a new weapon on a station, or one appearing on an empty station, is a change."""
	before = {'CLSID.5': '', 'CLSID.6': '{M299}', 'CLSID.7': '{M299}', 'count.5': 0}
	after = {'CLSID.5': '{AN_APG_78}', 'CLSID.6': '{M299}', 'CLSID.7': '{M261}', 'CLSID.8': '{M261}', 'count.5': 1}
	assert changedRefs(before, after) == ['CLSID.5', 'CLSID.7', 'CLSID.8', 'count.5']


def test_changedRefsMissingNumberStillCountsAsZero():
	assert changedRefs({'a': 0.0}, {'b': 0.0}) == []


# Telemetry refs mixed into a mapped snapshot, e.g. the AH-64D Longbow added from the rearming screen.
TELEMETRY_BEFORE = {**C130_BEFORE, 'telemetry/LoGetPayloadInfo.Stations.5.CLSID': '', 'telemetry/LoGetEngineInfo.RPM.left': 0.0}
TELEMETRY_AFTER = {**C130_BEFORE, 'telemetry/LoGetPayloadInfo.Stations.5.CLSID': '{AN_APG_78}', 'telemetry/LoGetEngineInfo.RPM.left': 62.5}

def test_snapshotReportShowsTelemetryByItsScriptRef():
	report = snapshotReport(TELEMETRY_BEFORE, TELEMETRY_AFTER, C130_INDEX, reverseTranslate, 'C-130J-30', False, '10:00:00', '10:05:00', includeSnapshots=True)
	assert report['changes'] == [
		{'control': 'telemetry/LoGetEngineInfo.RPM.left', 'description': 'Engine RPM, left (%)', 'arg': None, 'before': 0.0, 'after': 62.5, 'scriptBefore': 0.0, 'scriptAfter': 62.5},
		{'control': 'telemetry/LoGetPayloadInfo.Stations.5.CLSID', 'description': 'LoGetPayloadInfo.Stations.5.CLSID', 'arg': None, 'before': '', 'after': '{AN_APG_78}', 'scriptBefore': '', 'scriptAfter': '{AN_APG_78}'},
	]
	assert report['afterSnapshot']['telemetry/LoGetPayloadInfo.Stations.5.CLSID'] == '{AN_APG_78}'
	assert report['afterSnapshot']['ENGINE_APU_CTRL.battery'] == 1.0
	json.dumps(report)


def test_snapshotReportForRawScanShowsTelemetryToo():
	report = snapshotReport({322: 0.0, 'telemetry/LoGetTrueAirSpeed': 0.0}, {322: 0.5, 'telemetry/LoGetTrueAirSpeed': 20.0}, {}, reverseTranslate, None, True, '10:00:00', '10:05:00', includeSnapshots=True)
	assert report['changes'] == [
		{'arg': 322, 'before': 0.0, 'after': 0.5},
		{'control': 'telemetry/LoGetTrueAirSpeed', 'description': 'True airspeed (m/s)', 'arg': None, 'before': 0.0, 'after': 20.0, 'scriptBefore': 0.0, 'scriptAfter': 20.0},
	]
	assert report['afterSnapshot'] == {'322': 0.5, 'telemetry/LoGetTrueAirSpeed': 20.0}


def test_formatSnapshotValue():
	assert [formatSnapshotValue(v) for v in (None, 0.5, 2, '{AN_APG_78}', '')] == ['', '0.5000', '2.0000', '{AN_APG_78}', '""']


def test_snapshotReportListsChangedControlsWithRawAndScriptValues():
	report = snapshotReport(C130_BEFORE, C130_AFTER, C130_INDEX, reverseTranslate, 'C-130J-30', False, '10:00:00', '10:05:00')
	assert report['module'] == 'C-130J-30'
	assert report['changes'] == [
		{'control': 'ENGINE_APU_CTRL.ext_elec', 'description': 'External Power/APU Switch', 'arg': 467, 'before': 0.0, 'after': 1.0, 'scriptBefore': 1, 'scriptAfter': 2},
		{'control': 'VOLUME_MANAGER.int_vol', 'description': 'Pilot INT Volume Knob', 'arg': 205, 'before': 0.0, 'after': 0.8, 'scriptBefore': 0.0, 'scriptAfter': 0.8},
	]
	assert 'beforeSnapshot' not in report
	json.dumps(report)


def test_snapshotReportCanIncludeBothFullSnapshots():
	report = snapshotReport(C130_BEFORE, C130_AFTER, C130_INDEX, reverseTranslate, 'C-130J-30', False, '10:00:00', '10:05:00', includeSnapshots=True)
	assert report['beforeSnapshot'].get('ENGINE_APU_CTRL.battery') == 1.0
	assert report['afterSnapshot'].get('VOLUME_MANAGER.int_vol') == 0.8
	assert (report['beforeTakenAt'], report['afterTakenAt']) == ('10:00:00', '10:05:00')


def test_snapshotReportForRawScanHasArgsOnly():
	report = snapshotReport({322: 0.0, 371: 1.0}, {322: 0.5, 371: 1.0}, {}, reverseTranslate, None, True, '10:00:00', '10:05:00', includeSnapshots=True)
	assert report['changes'] == [{'arg': 322, 'before': 0.0, 'after': 0.5}]
	assert report['afterSnapshot'] == {'322': 0.5, '371': 1.0}
	json.dumps(report)


def test_telemetryIsFirstInModuleList():
	assert moduleNamesForDropdown({'FA-18C_hornet': {}, 'A-10C': {}}) == ['telemetry', 'A-10C', 'FA-18C_hornet']


def test_telemetryModuleListsCatalogueWithDescriptions():
	controls = controlsForModule({}, 'telemetry')
	assert controls['LoGetEngineInfo.RPM.right']['description'] == 'Engine RPM, right (%)'
	assert controls['LoGetEngineInfo.RPM.right']['category'] == 'Telemetry'
	assert 'LoGetPayloadInfo.CurrentStation' in controls


def test_normalModuleListsItsMappedControls():
	mappings = {'A-10C': {'controls': {'AHCP.PNT-TMB-AHCP-TGP': {'description': 'TGP'}}}}
	assert controlsForModule(mappings, 'A-10C') == {'AHCP.PNT-TMB-AHCP-TGP': {'description': 'TGP'}}
	assert controlsForModule(mappings, 'Unknown') == {}


def test_parsePositionLabelsGeneric():
	# Description is ignored; labels are always 'Pos N'.
	desc = 'Landing Gear Control Handle, UP/DOWN/EMERG DOWN'
	labels = parsePositionLabels(desc, 3)
	assert labels == ['Pos 0', 'Pos 1', 'Pos 2']


def test_parsePositionLabelsTwo():
	labels = parsePositionLabels('Some Switch, ON/OFF', 2)
	assert labels == ['Pos 0', 'Pos 1']


def test_parsePositionLabelsNoComma():
	labels = parsePositionLabels('Plain description without labels', 2)
	assert labels == ['Pos 0', 'Pos 1']


def test_parsePositionLabelsEmptyDescription():
	labels = parsePositionLabels('', 4)
	assert labels == ['Pos 0', 'Pos 1', 'Pos 2', 'Pos 3']


def test_parsePositionLabelsZeroPositions():
	# Guard against bad data — must return at least one label.
	labels = parsePositionLabels('No labels here', 0)
	assert labels == ['Pos 0']


def test_parsePositionLabelsNonePositions():
	labels = parsePositionLabels('Anything', None)
	assert labels == ['Pos 0']


def test_parsePositionLabelsManyPositions():
	desc = 'FUEL QTY SEL Knob, TEST/NORM/RSVR/INT WING/EXT WING/EXT CTR'
	labels = parsePositionLabels(desc, 6)
	assert labels == ['Pos 0', 'Pos 1', 'Pos 2', 'Pos 3', 'Pos 4', 'Pos 5']
