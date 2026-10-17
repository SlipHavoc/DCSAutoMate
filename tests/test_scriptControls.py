"""Every control a script sends must exist in its module's control mapping.

Runs each script function with default vars (route/scratchpad scripts get fixed waypoints
covering all four hemispheres) and checks every control name in the resulting sequence
against config/controlMappings/<moduleName>.json, the same lookup the app does at run time.
"""
import importlib
import json
import os
import sys
from unittest.mock import MagicMock

import pytest

sys.modules.setdefault('PySide6', type(sys)('PySide6'))
_qtw = type(sys)('PySide6.QtWidgets')
_qtw.QMessageBox = MagicMock()
sys.modules.setdefault('PySide6.QtWidgets', _qtw)

projectRoot = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if projectRoot not in sys.path:
	sys.path.insert(0, projectRoot)

from engine.SequenceHelper import SequenceHelper
from network.DCSDirectManager import TELEMETRY_MODULE, parseTelemetryRef

SCRIPTS_DIR = os.path.join(projectRoot, 'DCSAutoMateScripts')
MAPPINGS_DIR = os.path.join(projectRoot, 'config', 'controlMappings')
CONTROL_KEY_COMMANDS = ('scriptCockpitState', 'scriptLoopUntilStart', 'scriptLoopUntilEnd')


def makeWaypoint(lat, lon, altFeet, ddmMinutes=None):
	"""ddmMinutes=(latMin, lonMin) overrides the DDM minutes, as a scratchpad file's short values (e.g. 46.08) would."""
	def ddm(value):
		deg = int(abs(value))
		return {'deg': -deg if value < 0 else deg, 'min': (abs(value) - deg) * 60.0}

	def dms(value):
		deg = int(abs(value))
		minutesTotal = (abs(value) - deg) * 60.0
		return {'deg': -deg if value < 0 else deg, 'min': int(minutesTotal), 'sec': (minutesTotal - int(minutesTotal)) * 60.0}

	latLonDDM = {'lat': ddm(lat), 'lon': ddm(lon)}
	if ddmMinutes:
		latLonDDM['lat']['min'], latLonDDM['lon']['min'] = ddmMinutes
	return {
		'altMeters': altFeet / 3.28084,
		'altFeet': altFeet,
		'groundAltMeters': 100.0,
		'groundAltFeet': 328.084,
		'latLonDD': {'lat': {'deg': lat}, 'lon': {'deg': lon}},
		'latLonDDM': latLonDDM,
		'latLonDMS': {'lat': dms(lat), 'lon': dms(lon)},
		'mgrs10': '37TGG2906959063',
		'mgrs6': '37TGG290590',
		'mgrs8': '37TGG29065906',
		'env': '',
		'error': '',
	}


# Caucasus (N/E), Nevada (N/W), Falklands (S/W), northern Australia (S/E), and a scratchpad-style N 43 05.5 / E 040 46.08.
TEST_WAYPOINTS = [
	makeWaypoint(42.0502, 41.7680, 5000),
	makeWaypoint(36.2358, -115.0343, 12000),
	makeWaypoint(-51.8231, -58.4471, 3000),
	makeWaypoint(-12.4102, 130.8779, 800),
	makeWaypoint(43.091667, 40.768, 1500, ddmMinutes=(5.5, 46.08)),
]


class FixedDataHelper(SequenceHelper):
	"""SequenceHelper whose route and scratchpad sources return TEST_WAYPOINTS."""

	def getRouteData(self, routeFile, routeName):
		return {'map': 'Test', 'route': 'Test', 'waypoints': [dict(w) for w in TEST_WAYPOINTS]}

	def getScratchpadData(self, filename):
		return [dict(w) for w in TEST_WAYPOINTS]


def defaultVars(script):
	defaults = {}
	for key, varDef in script.get('vars', {}).items():
		options = varDef.get('options') or {}
		defaults[key] = varDef.get('default', next(iter(options), ''))
	return defaults


def varVariants(script):
	"""Default vars, plus one variant per non-default option value (one var changed at a time)."""
	defaults = defaultVars(script)
	variants = [('defaults', defaults)]
	for key, varDef in script.get('vars', {}).items():
		for option in varDef.get('options') or {}:
			if option != defaults[key]:
				variants.append((f'{key}={option}', {**defaults, key: option}))
	return variants


def sequenceControls(sequence):
	for command in sequence:
		cmd = command.get('cmd', '')
		if cmd in CONTROL_KEY_COMMANDS:
			control = command.get('control')
		elif cmd and not cmd.startswith('script'):
			control = cmd
		else:
			continue
		if control:
			yield control


def unresolvedControls(sequence, controls):
	"""Control refs in the sequence that are neither well-formed telemetry refs nor in the module's mapping."""
	unresolved = set()
	for ref in sequenceControls(sequence):
		if ref.startswith(f'{TELEMETRY_MODULE}/'):
			if parseTelemetryRef(ref) is None:
				unresolved.add(ref)
		elif ref.split('/', 1)[-1] not in controls:
			unresolved.add(ref.split('/', 1)[-1])
	return sorted(unresolved)


def test_unresolvedControlsAcceptsTelemetryAndRejectsMalformedOrUnknown():
	sequence = [
		{'cmd': 'scriptCockpitState', 'control': 'telemetry/LoGetEngineInfo.RPM.right', 'value': 15},
		{'cmd': 'scriptCockpitState', 'control': 'telemetry/EngineInfo.RPM', 'value': 15},
		{'cmd': 'UFC.KbdSw1', 'arg': 1},
		{'cmd': 'FA-18C_hornet/NOT.A_CONTROL', 'arg': 1},
	]
	assert unresolvedControls(sequence, {'UFC.KbdSw1': {}}) == ['NOT.A_CONTROL', 'telemetry/EngineInfo.RPM']


def scriptCases():
	cases = []
	for fileName in sorted(os.listdir(SCRIPTS_DIR)):
		if not fileName.endswith('.py') or fileName == '__init__.py':
			continue
		moduleFile = fileName[:-3]
		scriptData = importlib.import_module(f'DCSAutoMateScripts.{moduleFile}').getScriptData()
		for script in scriptData['scripts']:
			for variantName, scriptVars in varVariants(script):
				cases.append(pytest.param(moduleFile, scriptData['moduleName'], script, scriptVars, id=f'{moduleFile}/{script["name"]}/{variantName}'))
	return cases


@pytest.mark.parametrize('moduleFile,moduleName,script,scriptVars', scriptCases())
def test_scriptControlsExistInMapping(moduleFile, moduleName, script, scriptVars):
	mappingPath = os.path.join(MAPPINGS_DIR, f'{moduleName}.json')
	if not os.path.isfile(mappingPath):
		pytest.skip(f'no control mapping for {moduleName}')
	with open(mappingPath, encoding='utf-8') as f:
		controls = json.load(f)['controls']
	config = {'debug': True}
	scriptFunction = getattr(importlib.import_module(f'DCSAutoMateScripts.{moduleFile}'), script['function'])
	helper = FixedDataHelper(config)
	sequence = helper.collectSequence(scriptFunction(config, dict(scriptVars), helper))
	assert unresolvedControls(sequence, controls) == []


def pressedControls(sequence):
	"""Controls in press order, taking only the press (value 1) of each press/release pair."""
	return [c['cmd'] for c in sequence if c.get('arg') == 1 and c.get('cmd', '').startswith('UFC.')]


@pytest.mark.parametrize('functionName', ['LoadRoute', 'LoadScratchpad'])
def test_f16cWaypointEntryTypesUnsignedDegreesAfterHemisphereKey(functionName):
	"""The hemisphere key carries the sign, so W 115 deg 02.058 min must type W, 1, 1, 5, 0, 2, 0, 5, 8.

	Minutes are typed to 0.001 min, rounded, with the fraction padded on the right (46.08 is 46.080, not 46.008).
	"""
	f16 = importlib.import_module('DCSAutoMateScripts.F-16C')
	script = next(s for s in f16.getScriptData()['scripts'] if s['function'] == functionName)
	config = {'debug': True}
	helper = FixedDataHelper(config)
	pressed = pressedControls(helper.collectSequence(getattr(f16, functionName)(config, defaultVars(script), helper)))
	digits = ['UFC.DIG0_M_SEL', 'UFC.DIG1_T_ILS', 'UFC.DIG2_ALOW', 'UFC.DIG3', 'UFC.DIG4_STPT', 'UFC.DIG5_CRUS', 'UFC.DIG6_TIME', 'UFC.DIG7_MARK', 'UFC.DIG8_FIX', 'UFC.DIG9_A_CAL']
	westLongitude = ['UFC.DIG4_STPT'] + [digits[int(d)] for d in '11502058'] + ['UFC.ENTR']
	southLatitude = ['UFC.DIG8_FIX'] + [digits[int(d)] for d in '5149386'] + ['UFC.ENTR']
	shortEastLongitude = ['UFC.DIG6_TIME'] + [digits[int(d)] for d in '04046080'] + ['UFC.ENTR']
	shortNorthLatitude = ['UFC.DIG2_ALOW'] + [digits[int(d)] for d in '4305500'] + ['UFC.ENTR']
	for expected in (westLongitude, southLatitude, shortEastLongitude, shortNorthLatitude):
		assert any(pressed[i:i + len(expected)] == expected for i in range(len(pressed))), expected
