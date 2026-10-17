"""Tests for network.DCSDirectManager — TCP-based DCS communication manager."""
import json
import os
import socket
import sys
import threading
import time
from unittest.mock import patch, MagicMock

import pytest

# Stub PySide6 before importing the module under test.
sys.modules.setdefault('PySide6', type(sys)('PySide6'))
_qtw = type(sys)('PySide6.QtWidgets')
_qtw.QMessageBox = MagicMock()
_qtw.QApplication = MagicMock()
sys.modules.setdefault('PySide6.QtWidgets', _qtw)
sys.modules.setdefault('PySide6.QtCore', type(sys)('PySide6.QtCore'))

projectRoot = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if projectRoot not in sys.path:
	sys.path.insert(0, projectRoot)

from network.DCSDirectManager import DCSDirectManager, flattenTelemetry, parseTelemetryRef, telemetryValueAt


# ---------------------------------------------------------------------------
# Sample unified control mapping data
# ---------------------------------------------------------------------------

SAMPLE_CONTROL_MAPPING = {
	'moduleName': 'TestModule',
	'controls': {
		'battSw': {
			'type': 'discrete',
			'deviceId': 3,
			'commandId': 3001,
			'arg': 404,
			'argLim': [-1.0, 1.0],
			'step': 1.0,
			'positions': 3,
			'description': 'Battery Switch, ON/OFF/ORIDE',
			'category': 'Electrical Power Panel',
		},
		'apuControlSw': {
			'type': 'discrete',
			'deviceId': 3,
			'commandId': 3002,
			'arg': 377,
			'argLim': [0.0, 1.0],
			'step': 1.0,
			'positions': 2,
			'description': 'APU Control Switch',
			'category': 'Auxiliary Power Unit Panel',
		},
		'ampcdOffBrightness': {
			'type': 'continuous',
			'deviceId': 37,
			'commandId': 3001,
			'arg': 174,
			'argLim': [0.0, 1.0],
			'description': 'AMPCD Brightness Control',
			'category': 'AMPCD',
		},
		'canopyPos': {
			'arg': 181,
			'description': 'Canopy Position',
			'category': 'Internal Canopy Switch',
		},
		'apuReadyLt': {
			'arg': 376,
			'description': 'APU Ready Light (green)',
			'category': 'Auxiliary Power Unit Panel',
		},
		'txtRpmL': {
			'indicationId': 5,
			'fieldName': 'txt_RPM_L',
			'description': 'RPM_L',
			'category': 'Integrated Fuel/Engine Indicator (IFEI)',
		},
	},
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def makeDirectManager(tmpPath, controlMappingData=None):
	"""Build a DCSDirectManager with sample mapping data, without connecting.

	Creates the controlMappings directory with a sample mapping file,
	and returns a manager instance that is NOT started (no TCP connection).
	"""
	mappingData = controlMappingData if controlMappingData else SAMPLE_CONTROL_MAPPING
	moduleName = mappingData.get('moduleName', 'TestModule')

	config = {
		'dcsDirectHost': '127.0.0.1',
		'dcsDirectPort': 0,  # Don't actually try to connect.
	}

	# Patch the mapping loader to return our test data directly.
	with patch.object(DCSDirectManager, '_loadControlMapping') as mockLoad:
		mockLoad.return_value = {moduleName: mappingData}
		mgr = DCSDirectManager(config)

	return mgr


class MockTcpServer:
	"""A simple TCP server for testing the DCSDirectManager connection."""

	def __init__(self, responses=None):
		self.responses = responses or {}  # {requestPrefix: responseString}
		self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		self.server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
		self.server.bind(('127.0.0.1', 0))
		self.port = self.server.getsockname()[1]
		self.server.listen(1)
		self.server.settimeout(5.0)
		self.running = True
		self.receivedCommands = []
		self.thread = threading.Thread(target=self._serve, daemon=True)
		self.thread.start()

	def _serve(self):
		try:
			conn, addr = self.server.accept()
			conn.settimeout(1.0)
			buf = ''
			while self.running:
				try:
					data = conn.recv(4096)
					if not data:
						break
					buf += data.decode('utf-8')
					while '\n' in buf:
						line, buf = buf.split('\n', 1)
						self.receivedCommands.append(line)
						# Check if we have a response for this command.
						for prefix, response in self.responses.items():
							if line.startswith(prefix):
								conn.sendall((response + '\n').encode('utf-8'))
								break
				except socket.timeout:
					continue
				except Exception:
					break
			conn.close()
		except Exception:
			pass

	def stop(self):
		self.running = False
		try:
			self.server.close()
		except Exception:
			pass
		self.thread.join(timeout=2.0)


# ---------------------------------------------------------------------------
# Tests: Mapping Loading
# ---------------------------------------------------------------------------

class TestMappingLoading:
	def test_loadMappingFromFile(self, tmp_path):
		mgr = makeDirectManager(tmp_path)
		assert 'TestModule' in mgr.controlMappings
		assert mgr.controlMappings['TestModule']['controls']['battSw']['deviceId'] == 3

	def test_controlIndexBuilt(self, tmp_path):
		mgr = makeDirectManager(tmp_path)
		assert 'TestModule/battSw' in mgr.controlIndex
		assert 'TestModule/canopyPos' in mgr.controlIndex
		assert 'TestModule/txtRpmL' in mgr.controlIndex

	def test_descriptionsBuilt(self, tmp_path):
		mgr = makeDirectManager(tmp_path)
		descriptions = mgr.getDescriptions('TestModule')
		assert 'battSw' in descriptions
		assert descriptions['battSw']['description'] == 'Battery Switch, ON/OFF/ORIDE'
		assert descriptions['battSw']['category'] == 'Electrical Power Panel'

	def test_getDescriptionSingle(self, tmp_path):
		mgr = makeDirectManager(tmp_path)
		desc = mgr.getDescription('battSw')
		assert desc is not None
		assert desc['description'] == 'Battery Switch, ON/OFF/ORIDE'

	def test_emptyMappingsDir(self, tmp_path):
		"""Manager should work even with no mapping files."""
		config = {'dcsDirectHost': '127.0.0.1', 'dcsDirectPort': 0}
		with patch.object(DCSDirectManager, '_loadControlMapping', return_value={}):
			mgr = DCSDirectManager(config)
		assert mgr.controlMappings == {}
		assert mgr.controlIndex == {}

	def test_mismatchedFilenameSkipped(self, tmp_path):
		"""Files whose name doesn't match their moduleName should be skipped."""
		mappingsDir = tmp_path / 'config' / 'controlMappings'
		mappingsDir.mkdir(parents=True)

		# Write a correctly named mapping file.
		correctData = {'moduleName': 'TestModule', 'controls': {'battSw': {'deviceId': 3, 'commandId': 3001, 'type': 'discrete', 'description': 'Battery'}}}
		with open(mappingsDir / 'TestModule.json', 'w') as f:
			json.dump(correctData, f)

		# Write a misnamed file with the same moduleName (simulates _old_bios or backup).
		badData = {'moduleName': 'TestModule', 'controls': {'oldName': {'deviceId': 99, 'commandId': 9999, 'type': 'discrete', 'description': 'Old'}}}
		with open(mappingsDir / 'TestModule_old_bios.json', 'w') as f:
			json.dump(badData, f)

		# Create a manager that loads from our temp directory.
		config = {'dcsDirectHost': '127.0.0.1', 'dcsDirectPort': 0}
		realDir = str(mappingsDir)
		def patchedLoad(self):
			mappings = {}
			for filename in os.listdir(realDir):
				if not filename.endswith('.json'):
					continue
				if filename.endswith('_nameMap.json'):
					continue
				filepath = os.path.join(realDir, filename)
				with open(filepath, 'r', encoding='utf-8') as f:
					data = json.load(f)
				moduleName = data.get('moduleName', filename.replace('.json', ''))
				expectedFilename = f'{moduleName}.json'
				if filename != expectedFilename:
					continue
				mappings[moduleName] = data
			return mappings

		with patch.object(DCSDirectManager, '_loadControlMapping', patchedLoad):
			mgr = DCSDirectManager(config)

		assert 'TestModule' in mgr.controlMappings
		assert 'battSw' in mgr.controlMappings['TestModule']['controls']
		assert 'oldName' not in mgr.controlMappings['TestModule']['controls']


# ---------------------------------------------------------------------------
# Tests: Control Lookup
# ---------------------------------------------------------------------------

class TestControlLookup:
	def test_controlExists(self, tmp_path):
		mgr = makeDirectManager(tmp_path)
		assert mgr.controlExists('TestModule/battSw')
		assert mgr.controlExists('TestModule/canopyPos')
		assert not mgr.controlExists('TestModule/nonexistent')

	def test_controlExistsBareNameSearch(self, tmp_path):
		"""controlExists should also find controls by bare name across modules."""
		mgr = makeDirectManager(tmp_path)
		# Bare name search (no module prefix) should check all modules.
		assert mgr.controlExists('TestModule/battSw')

	def test_lookupControl(self, tmp_path):
		mgr = makeDirectManager(tmp_path)
		ctrl = mgr._lookupControl('battSw')
		assert ctrl is not None
		assert ctrl['deviceId'] == 3
		assert ctrl['commandId'] == 3001
		assert ctrl['arg'] == 404

	def test_lookupControlNotFound(self, tmp_path):
		mgr = makeDirectManager(tmp_path)
		assert mgr._lookupControl('nonexistent') is None

	def test_lookupControlReadOnly(self, tmp_path):
		mgr = makeDirectManager(tmp_path)
		ctrl = mgr._lookupControl('canopyPos')
		assert ctrl is not None
		assert ctrl['arg'] == 181

	def test_lookupControlIndication(self, tmp_path):
		mgr = makeDirectManager(tmp_path)
		ctrl = mgr._lookupControl('txtRpmL')
		assert ctrl is not None
		assert ctrl['indicationId'] == 5
		assert ctrl['fieldName'] == 'txt_RPM_L'


# ---------------------------------------------------------------------------
# Tests: Indication Parsing
# ---------------------------------------------------------------------------

class TestIndicationParsing:
	def test_parseSimpleIndication(self):
		raw = '-----------------------------------------\ntxt_RPM_L\n 63\n-----------------------------------------\ntxt_RPM_R\n 64\n'
		# JSON-encode it as the Lua script would.
		jsonEncoded = json.dumps(raw)
		result = DCSDirectManager._parseIndication(jsonEncoded)
		assert result['txt_RPM_L'] == '63'
		assert result['txt_RPM_R'] == '64'

	def test_parseEmptyIndication(self):
		result = DCSDirectManager._parseIndication(json.dumps(''))
		assert result == {}

	def test_parseNullIndication(self):
		result = DCSDirectManager._parseIndication('null')
		assert result == {}

	def test_parseAlreadyDict(self):
		"""If somehow the value is already a dict, return it as-is."""
		result = DCSDirectManager._parseIndication(json.dumps({'key': 'val'}))
		assert result == {'key': 'val'}

	def test_parseMultipleFields(self):
		raw = '-----------------------------------------\ntxt_FUEL_UP\n  8200\n-----------------------------------------\ntxt_FUEL_DOWN\n  7500\n-----------------------------------------\ntxt_RPM_L\n 63\n'
		result = DCSDirectManager._parseIndication(json.dumps(raw))
		assert result['txt_FUEL_UP'] == '8200'
		assert result['txt_FUEL_DOWN'] == '7500'
		assert result['txt_RPM_L'] == '63'

	def test_parseWithHierarchyMarkers(self):
		"""DCS list_indication() can include 'children are {' and '}' hierarchy markers."""
		raw = (
			'-----------------------------------------\n'
			'UFC_MainDummy\n'
			'\n'
			'children are {\n'
			'-----------------------------------------\n'
			'UFC_mask\n'
			'\n'
			'children are {\n'
			'-----------------------------------------\n'
			'UFC_OptionDisplay1\n'
			'\n'
			'-----------------------------------------\n'
			'UFC_Comm1Display\n'
			' 251.000\n'
			'-----------------------------------------\n'
			'UFC_Comm2Display\n'
			' 127.500\n'
			'}\n'
			'}\n'
		)
		result = DCSDirectManager._parseIndication(json.dumps(raw))
		assert 'children are {' not in result
		assert '}' not in result
		assert result['UFC_OptionDisplay1'] == ''
		assert result['UFC_Comm1Display'] == '251.000'
		assert result['UFC_Comm2Display'] == '127.500'


# ---------------------------------------------------------------------------
# Tests: Response Processing
# ---------------------------------------------------------------------------

class TestResponseProcessing:
	def test_processQueryResponse(self, tmp_path):
		mgr = makeDirectManager(tmp_path)
		mgr._processResponse('R:0:181:0.75')
		assert mgr.pendingResponses.get('Q:0:181') == '0.75'

	def test_processSubscriptionUpdate(self, tmp_path):
		mgr = makeDirectManager(tmp_path)
		mgr._processResponse('U:0:376:1.0')
		assert mgr.pendingResponses.get('W:0:376') == '1.0'

	def test_processIndicationResponse(self, tmp_path):
		mgr = makeDirectManager(tmp_path)
		mgr._processResponse('D:5:{"txt_RPM_L": "63"}')
		assert mgr.pendingResponses.get('T:5') == '{"txt_RPM_L": "63"}'

	def test_processModuleResponse(self, tmp_path):
		mgr = makeDirectManager(tmp_path)
		mgr._processResponse('I:FA-18C_hornet')
		assert mgr.pendingResponses.get('I') == 'FA-18C_hornet'

	def test_processEngineResponse(self, tmp_path):
		mgr = makeDirectManager(tmp_path)
		mgr._processResponse('E:{"RPM":{"left":63,"right":64}}')
		assert mgr.pendingResponses.get('E') == '{"RPM":{"left":63,"right":64}}'

	def test_processResponseSetsEvent(self, tmp_path):
		mgr = makeDirectManager(tmp_path)
		event = threading.Event()
		mgr.responseEvents['Q:0:181'] = event
		mgr._processResponse('R:0:181:0.5')
		assert event.is_set()

	def test_processEmptyLine(self, tmp_path):
		mgr = makeDirectManager(tmp_path)
		# Should not crash.
		mgr._processResponse('')

	def test_processTelemetryResponseKeepsColonsInJson(self, tmp_path):
		mgr = makeDirectManager(tmp_path)
		mgr._processResponse('G:LoGetEngineInfo:{"RPM":{"left":63,"right":64}}')
		assert mgr.pendingResponses.get('G:LoGetEngineInfo') == '{"RPM":{"left":63,"right":64}}'


# ---------------------------------------------------------------------------
# Tests: telemetry/ controls (LoGet* functions via the G: query)
# ---------------------------------------------------------------------------

ENGINE_INFO = {'RPM': {'left': 62.5, 'right': 64.25}, 'fuel_internal': 4900.0}
PAYLOAD_INFO = {'CurrentStation': 0, 'Stations': [{'count': 1, 'weapon': {'level1': 4}}, {'count': 0, 'weapon': {'level1': 0}}]}


def startTelemetryServer(responses):
	server = MockTcpServer(responses={f'G:{name}': f'G:{name}:{json.dumps(value)}' for name, value in responses.items()})
	config = {'dcsDirectHost': '127.0.0.1', 'dcsDirectPort': server.port}
	with patch.object(DCSDirectManager, '_loadControlMapping', return_value={'TestModule': SAMPLE_CONTROL_MAPPING}):
		mgr = DCSDirectManager(config)
	mgr.start()
	time.sleep(0.5)
	return server, mgr


class TestTelemetryControls:
	def test_flattenGivesTheRefsScriptsUse(self):
		assert flattenTelemetry('LoGetPayloadInfo', PAYLOAD_INFO) == {
			'telemetry/LoGetPayloadInfo.CurrentStation': 0,
			'telemetry/LoGetPayloadInfo.Stations.1.count': 1,
			'telemetry/LoGetPayloadInfo.Stations.1.weapon.level1': 4,
			'telemetry/LoGetPayloadInfo.Stations.2.count': 0,
			'telemetry/LoGetPayloadInfo.Stations.2.weapon.level1': 0,
		}

	def test_flattenKeepsTextAndStationsKeyedByNumber(self):
		stations = {'Stations': {'5': {'CLSID': '{AN_APG_78}', 'count': 1}}}
		assert flattenTelemetry('LoGetPayloadInfo', stations) == {'telemetry/LoGetPayloadInfo.Stations.5.CLSID': '{AN_APG_78}', 'telemetry/LoGetPayloadInfo.Stations.5.count': 1}

	def test_flattenSingleValueFunction(self):
		assert flattenTelemetry('LoGetTrueAirSpeed', 51.5) == {'telemetry/LoGetTrueAirSpeed': 51.5}
		assert flattenTelemetry('LoGetTrueAirSpeed', None) == {}

	def test_everyFlattenedRefCanBeRead(self):
		for ref, value in flattenTelemetry('LoGetPayloadInfo', PAYLOAD_INFO).items():
			functionName, path = parseTelemetryRef(ref)
			assert telemetryValueAt(PAYLOAD_INFO, path) == value

	def test_snapshotSkipsMissionTimeAndFunctionsDcsDidntAnswer(self, tmp_path):
		mgr = makeDirectManager(tmp_path)
		queried = []
		def queryTelemetry(functionName, timeout=1.0):
			queried.append(functionName)
			return {'LoGetEngineInfo': ENGINE_INFO, 'LoGetTrueAirSpeed': 51.5}.get(functionName)
		mgr.queryTelemetry = queryTelemetry
		snapshot = mgr.snapshotTelemetry()
		assert 'LoGetModelTime' not in queried
		assert 'LoGetPayloadInfo' in queried
		assert snapshot == {**flattenTelemetry('LoGetEngineInfo', ENGINE_INFO), 'telemetry/LoGetTrueAirSpeed': 51.5}

	def test_snapshotSkipsFlightModelDataButHasNewDcs2930Functions(self, tmp_path):
		"""LoGetFMData changes every frame, so only its master flag is listed, and the snapshot leaves it out."""
		mgr = makeDirectManager(tmp_path)
		queried = []
		mgr.queryTelemetry = lambda functionName, timeout=1.0: queried.append(functionName)
		mgr.snapshotTelemetry()
		assert 'LoGetFMData' not in queried
		assert {'LoGetPlayerSeat', 'LoGetModelTimeAcceleration', 'LoGetNetIsRunning', 'LoGetTrackIsReading'} <= set(queried)

	def test_newDcs2930FunctionsAreListedWithDescriptions(self, tmp_path):
		mgr = makeDirectManager(tmp_path)
		for name in ('LoGetPlayerSeat', 'LoGetModelTimeAcceleration', 'LoGetNetIsRunning', 'LoGetTrackIsReading', 'LoGetFMData.master'):
			assert mgr.getControl(f'telemetry/{name}')['description'] != name

	def test_telemetryRefsExist(self, tmp_path):
		mgr = makeDirectManager(tmp_path)
		assert mgr.controlExists('telemetry/LoGetEngineInfo.RPM.right')
		assert mgr.controlExists('telemetry/LoGetPayloadInfo.Stations.1.count')
		assert mgr.controlExists('telemetry/LoGetTrueAirSpeed')

	def test_nonLoGetTelemetryRefsDoNotExist(self, tmp_path):
		mgr = makeDirectManager(tmp_path)
		assert not mgr.controlExists('telemetry/os.exit')
		assert not mgr.controlExists('telemetry/LoSetCommand.x')
		assert not mgr.controlExists('telemetry/')

	def test_readNestedValue(self):
		server, mgr = startTelemetryServer({'LoGetEngineInfo': ENGINE_INFO})
		try:
			result = mgr.getControlState('telemetry/LoGetEngineInfo.RPM.right')
			assert result[0][0] == 'telemetry/LoGetEngineInfo.RPM.right'
			assert result[0][2] == 64.25
		finally:
			mgr.stop()
			server.stop()

	def test_listIndexesAreOneBasedLikeLua(self):
		server, mgr = startTelemetryServer({'LoGetPayloadInfo': PAYLOAD_INFO})
		try:
			assert mgr.getControlState('telemetry/LoGetPayloadInfo.Stations.1.count')[0][2] == 1
			assert mgr.getControlState('telemetry/LoGetPayloadInfo.Stations.2.count')[0][2] == 0
		finally:
			mgr.stop()
			server.stop()

	def test_missingPathReadsAsNone(self):
		server, mgr = startTelemetryServer({'LoGetEngineInfo': ENGINE_INFO})
		try:
			assert mgr.getControlState('telemetry/LoGetEngineInfo.RPM.center')[0][2] is None
			assert mgr.getControlState('telemetry/LoGetEngineInfo.RPM.left.more')[0][2] is None
		finally:
			mgr.stop()
			server.stop()

	def test_catalogueDescriptionIsUsed(self, tmp_path):
		mgr = makeDirectManager(tmp_path)
		assert 'RPM' in mgr.getControl('telemetry/LoGetEngineInfo.RPM.right')['description']
		assert mgr.getControl('telemetry/LoGetPayloadInfo.Stations.1.count')['description'] == 'LoGetPayloadInfo.Stations.1.count'
		assert mgr.getControl('TestModule/battSw')['deviceId'] == 3
		assert mgr.getControl('telemetry/notLoGet') is None

	def test_pollQueriesEachFunctionOnce(self):
		server, mgr = startTelemetryServer({'LoGetEngineInfo': ENGINE_INFO})
		try:
			results = mgr.pollControlStates(['telemetry/LoGetEngineInfo.RPM.left', 'telemetry/LoGetEngineInfo.RPM.right', 'telemetry/LoGetEngineInfo.fuel_internal'])
			assert {r[0]: r[2] for r in results} == {
				'telemetry/LoGetEngineInfo.RPM.left': 62.5,
				'telemetry/LoGetEngineInfo.RPM.right': 64.25,
				'telemetry/LoGetEngineInfo.fuel_internal': 4900.0,
			}
			assert [c for c in server.receivedCommands if c.startswith('G:')] == ['G:LoGetEngineInfo']
		finally:
			mgr.stop()
			server.stop()


# ---------------------------------------------------------------------------
# Tests: Send Commands
# ---------------------------------------------------------------------------

class TestSendCommands:
	def test_sendControlDiscreteSwitch(self, tmp_path):
		mgr = makeDirectManager(tmp_path)
		mgr.connected = True
		mgr.socket = MagicMock()
		result = mgr.sendControl('battSw', 2)
		assert result is True
		# Position 2: argLim[0] + step * 2 = -1.0 + 1.0 * 2 = 1.0.
		call = mgr.socket.sendall.call_args[0][0].decode('utf-8')
		assert 'C:3:3001:1.0' in call

	def test_sendControlContinuous(self, tmp_path):
		mgr = makeDirectManager(tmp_path)
		mgr.connected = True
		mgr.socket = MagicMock()
		result = mgr.sendControl('ampcdOffBrightness', 0.5)
		assert result is True
		call = mgr.socket.sendall.call_args[0][0].decode('utf-8')
		assert 'C:37:3001:0.5' in call

	def test_sendControlNotFound(self, tmp_path):
		mgr = makeDirectManager(tmp_path)
		mgr.connected = True
		mgr.socket = MagicMock()
		result = mgr.sendControl('nonexistent', 1)
		assert result is False
		mgr.socket.sendall.assert_not_called()

	def test_sendControlWithModulePrefix(self, tmp_path):
		"""sendControl should handle 'module/control' format from DCSSeqExecute."""
		mgr = makeDirectManager(tmp_path)
		mgr.connected = True
		mgr.socket = MagicMock()
		result = mgr.sendControl('TestModule/battSw', 2)
		assert result is True
		call = mgr.socket.sendall.call_args[0][0].decode('utf-8')
		assert 'C:3:3001:1.0' in call

	def test_sendCommandNotConnected(self, tmp_path):
		mgr = makeDirectManager(tmp_path)
		result = mgr.sendCommand(3, 3001, 1)
		assert result is False

	def test_sendSimCommandWithoutValue(self, tmp_path):
		mgr = makeDirectManager(tmp_path)
		mgr.connected = True
		mgr.socket = MagicMock()
		assert mgr.sendSimCommand(312) is True
		assert mgr.socket.sendall.call_args[0][0].decode('utf-8') == 'L:312\n'

	def test_sendSimCommandWithValue(self, tmp_path):
		mgr = makeDirectManager(tmp_path)
		mgr.connected = True
		mgr.socket = MagicMock()
		assert mgr.sendSimCommand(3, 0.25) is True
		assert mgr.socket.sendall.call_args[0][0].decode('utf-8') == 'L:3:0.25\n'

	def test_sendSimCommandNotConnected(self, tmp_path):
		mgr = makeDirectManager(tmp_path)
		assert mgr.sendSimCommand(312) is False

	def test_sendSimCommandHoldWithStop(self, tmp_path):
		mgr = makeDirectManager(tmp_path)
		mgr.connected = True
		mgr.socket = MagicMock()
		assert mgr.sendSimCommandHold(632, 2, 839) is True
		assert mgr.socket.sendall.call_args[0][0].decode('utf-8') == 'H:632:2:839\n'

	def test_sendSimCommandHoldWithoutStop(self, tmp_path):
		mgr = makeDirectManager(tmp_path)
		mgr.connected = True
		mgr.socket = MagicMock()
		assert mgr.sendSimCommandHold(632, 1.5) is True
		assert mgr.socket.sendall.call_args[0][0].decode('utf-8') == 'H:632:1.5\n'

	@pytest.mark.parametrize('args, kwargs, expected', [
		((2004, 30), {'value': 0.7}, 'H:2004:30::0.7'),
		((2004, None), {'value': -0.25}, 'H:2004:0::-0.25'), # None seconds: until released, sent as 0.
		((632, None, 839), {}, 'H:632:0:839:'),
	])
	def test_sendSimCommandHoldWithValueOrUntilReleased(self, tmp_path, args, kwargs, expected):
		mgr = makeDirectManager(tmp_path)
		mgr.connected = True
		mgr.socket = MagicMock()
		assert mgr.sendSimCommandHold(*args, **kwargs) is True
		assert mgr.socket.sendall.call_args[0][0].decode('utf-8') == expected + '\n'

	def test_releaseSimCommandHold(self, tmp_path):
		mgr = makeDirectManager(tmp_path)
		mgr.connected = True
		mgr.socket = MagicMock()
		assert mgr.releaseSimCommandHold(2004) is True
		assert mgr.socket.sendall.call_args[0][0].decode('utf-8') == 'H:2004:release\n'

	def test_sendControlReadOnlyFails(self, tmp_path):
		"""Sending to a read-only control (no type) should return False."""
		mgr = makeDirectManager(tmp_path)
		mgr.connected = True
		mgr.socket = MagicMock()
		result = mgr.sendControl('canopyPos', 0)
		assert result is False


# ---------------------------------------------------------------------------
# Tests: TCP Connection (integration-ish with mock server)
# ---------------------------------------------------------------------------

class TestTcpConnection:
	def test_connectAndQuery(self):
		"""Test connecting to a mock TCP server and querying an arg value."""
		server = MockTcpServer(responses={
			'Q:0:181': 'R:0:181:0.75',
		})
		try:
			config = {
				'dcsDirectHost': '127.0.0.1',
				'dcsDirectPort': server.port,
			}
			with patch.object(DCSDirectManager, '_loadControlMapping', return_value={'TestModule': SAMPLE_CONTROL_MAPPING}):
				mgr = DCSDirectManager(config)
			mgr.start()

			# Give it time to connect.
			time.sleep(0.5)
			assert mgr.connected

			# Query an argument value.
			value = mgr.queryArgumentValue(181, device=0, timeout=2.0)
			assert value == 0.75

			mgr.stop()
		finally:
			server.stop()

	def test_connectAndSendCommand(self):
		"""Test sending a command to a mock TCP server."""
		server = MockTcpServer()
		try:
			config = {
				'dcsDirectHost': '127.0.0.1',
				'dcsDirectPort': server.port,
			}
			with patch.object(DCSDirectManager, '_loadControlMapping', return_value={'TestModule': SAMPLE_CONTROL_MAPPING}):
				mgr = DCSDirectManager(config)
			mgr.start()
			time.sleep(0.5)

			mgr.sendCommand(3, 3001, 2)
			time.sleep(0.3)

			assert 'C:3:3001:2' in server.receivedCommands

			mgr.stop()
		finally:
			server.stop()

	def test_connectAndGetModuleId(self):
		"""Test querying module identification."""
		server = MockTcpServer(responses={
			'I': 'I:FA-18C_hornet',
		})
		try:
			config = {
				'dcsDirectHost': '127.0.0.1',
				'dcsDirectPort': server.port,
			}
			with patch.object(DCSDirectManager, '_loadControlMapping', return_value={'TestModule': SAMPLE_CONTROL_MAPPING}):
				mgr = DCSDirectManager(config)
			mgr.start()
			time.sleep(0.5)

			moduleName = mgr.queryModuleName(timeout=2.0)
			assert moduleName == 'FA-18C_hornet'

			mgr.stop()
		finally:
			server.stop()

	def test_queryTimeout(self, tmp_path):
		"""Test that queries time out gracefully when not connected."""
		mgr = makeDirectManager(tmp_path)
		# Not connected, should return None quickly.
		value = mgr.queryArgumentValue(181, timeout=0.1)
		assert value is None

	def test_startStop(self, tmp_path):
		"""Test start/stop lifecycle."""
		mgr = makeDirectManager(tmp_path)
		mgr.start()
		assert mgr.thread is not None
		assert mgr.thread.is_alive()
		mgr.stop()
		time.sleep(0.5)
		assert not mgr.thread.is_alive()


# ---------------------------------------------------------------------------
# Tests: getControlState compatibility
# ---------------------------------------------------------------------------

class TestGetControlState:
	def test_getControlStateMetadata(self):
		"""Test MetadataStart/_ACFT_NAME returns module name."""
		server = MockTcpServer(responses={'I': 'I:FA-18C_hornet'})
		try:
			config = {'dcsDirectHost': '127.0.0.1', 'dcsDirectPort': server.port}
			with patch.object(DCSDirectManager, '_loadControlMapping', return_value={'TestModule': SAMPLE_CONTROL_MAPPING}):
				mgr = DCSDirectManager(config)
			mgr.start()
			time.sleep(0.5)

			result = mgr.getControlState('MetadataStart/_ACFT_NAME')
			assert len(result) == 1
			assert result[0][0] == 'MetadataStart/_ACFT_NAME'
			assert result[0][2] == 'FA-18C_hornet'

			mgr.stop()
		finally:
			server.stop()

	def test_getControlStateArgument(self):
		"""Test querying an argument-based control."""
		server = MockTcpServer(responses={'Q:0:181': 'R:0:181:0.0'})
		try:
			config = {'dcsDirectHost': '127.0.0.1', 'dcsDirectPort': server.port}
			with patch.object(DCSDirectManager, '_loadControlMapping', return_value={'TestModule': SAMPLE_CONTROL_MAPPING}):
				mgr = DCSDirectManager(config)
			mgr.start()
			time.sleep(0.5)

			result = mgr.getControlState('TestModule/canopyPos')
			assert len(result) == 1
			assert result[0][2] == 0.0

			mgr.stop()
		finally:
			server.stop()

	def test_getControlStateNotFound(self, tmp_path):
		"""Test querying a non-existent control returns empty list."""
		mgr = makeDirectManager(tmp_path)
		result = mgr.getControlState('TestModule/nonexistent')
		assert result == []

	def test_getControlStateList(self, tmp_path):
		"""Test passing a list of controls."""
		mgr = makeDirectManager(tmp_path)
		# Not connected, so all queries will fail — but should not crash.
		result = mgr.getControlState(['TestModule/canopyPos', 'TestModule/apuReadyLt'])
		assert isinstance(result, list)

	def test_getControlStateIndication(self):
		"""Test querying an indication-based control (display text like IFEI RPM)."""
		indicationRaw = '\n-----------------------------------------\ntxt_RPM_L\n 63\n-----------------------------------------\ntxt_RPM_R\n 64\n'
		import json
		encodedIndication = json.dumps(indicationRaw)
		server = MockTcpServer(responses={'T:5': f'D:5:{encodedIndication}'})
		try:
			config = {'dcsDirectHost': '127.0.0.1', 'dcsDirectPort': server.port}
			with patch.object(DCSDirectManager, '_loadControlMapping', return_value={'TestModule': SAMPLE_CONTROL_MAPPING}):
				mgr = DCSDirectManager(config)
			mgr.start()
			time.sleep(0.5)

			result = mgr.getControlState('TestModule/txtRpmL')
			assert len(result) == 1
			assert result[0][0] == 'TestModule/txtRpmL'
			assert result[0][2] == '63'

			mgr.stop()
		finally:
			server.stop()

	def test_getControlStateIndicationEmpty(self):
		"""Test querying an indication-based control when display is unpowered (null)."""
		server = MockTcpServer(responses={'T:5': 'D:5:null'})
		try:
			config = {'dcsDirectHost': '127.0.0.1', 'dcsDirectPort': server.port}
			with patch.object(DCSDirectManager, '_loadControlMapping', return_value={'TestModule': SAMPLE_CONTROL_MAPPING}):
				mgr = DCSDirectManager(config)
			mgr.start()
			time.sleep(0.5)

			result = mgr.getControlState('TestModule/txtRpmL')
			assert len(result) == 1
			assert result[0][2] == ''

			mgr.stop()
		finally:
			server.stop()


# ---------------------------------------------------------------------------
# Tests: Value Translation
# ---------------------------------------------------------------------------

# Sample unified mapping with various control types for translation tests.
NATIVE_CONTROL_MAPPING = {
	'moduleName': 'NativeTestModule',
	'controls': {
		'battSw': {
			'type': 'discrete',
			'deviceId': 3,
			'commandId': 3001,
			'arg': 404,
			'argLim': [-1.0, 1.0],
			'step': 1.0,
			'positions': 3,
			'description': 'Battery Switch, ON/OFF/ORIDE',
			'category': 'Electrical Power Panel',
		},
		'insSwitchChange': {
			'type': 'discrete',
			'deviceId': 44,
			'commandId': 3001,
			'arg': 443,
			'argLim': [0.0, 0.7],
			'step': 0.1,
			'positions': 8,
			'description': 'INS Switch, OFF/CV/GND/NAV/IFA/GYRO/GB/TEST',
			'category': 'Sensor Panel',
		},
		'ampcdOffBrightness': {
			'type': 'continuous',
			'deviceId': 37,
			'commandId': 3001,
			'arg': 174,
			'argLim': [0.0, 1.0],
			'description': 'AMPCD Brightness Control',
			'category': 'AMPCD',
		},
		'brtKnob': {
			'type': 'continuous',
			'deviceId': 58,
			'commandId': 3001,
			'arg': 136,
			'argLim': [0.0, 0.75],
			'description': 'HMD OFF/BRT Knob',
			'category': 'Test',
		},
		'toggleSw': {
			'type': 'discrete',
			'deviceId': 3,
			'commandId': 3003,
			'arg': 405,
			'argLim': [0.0, 1.0],
			'step': 1.0,
			'positions': 2,
			'description': 'Test Toggle Switch',
			'category': 'Test',
		},
		'pushBtn': {
			'type': 'discrete',
			'deviceId': 25,
			'commandId': 3010,
			'arg': 120,
			'argLim': [0.0, 1.0],
			'step': 1.0,
			'positions': 2,
			'description': 'Test Push Button',
			'category': 'Test',
		},
		'id2163aSetMinAlt': {
			'type': 'relative',
			'deviceId': 5,
			'commandId': 3009,
			'arg': 200,
			'description': 'Radar Altimeter Height Knob',
			'category': 'Instruments',
		},
		'engineCrankLSw': {
			'type': 'discrete',
			'deviceId': 6,
			'arg': 375,
			'argLim': [-1.0, 1.0],
			'step': 1.0,
			'positions': 3,
			'description': 'Engine Crank Switch',
			'category': 'Engine',
			'positionMap': [
				{'deviceId': 6, 'commandId': 3012, 'value': -1.0},
				None,
				{'deviceId': 6, 'commandId': 3013, 'value': 1.0},
			],
		},
		'readOnlyArg': {
			'arg': 999,
			'description': 'Read-only argument',
			'category': 'Test',
		},
		'jesterEject': {
			'type': 'raw',
			'deviceId': 78,
			'commandId': 3128,
			'description': 'JESTER_COMMAND_EJECT',
		},
	},
}


class TestValueTranslation:
	"""Tests for script↔native value translation."""

	# ---- _translateValue ----

	def test_translateDiscretePos0(self, tmp_path):
		"""3-pos discrete position 0 → native -1.0."""
		mgr = makeDirectManager(tmp_path, NATIVE_CONTROL_MAPPING)
		ctrl = mgr._lookupControl('battSw')
		assert mgr._translateValue(ctrl, 0) == -1.0

	def test_translateDiscretePos1(self, tmp_path):
		"""3-pos discrete position 1 → native 0.0."""
		mgr = makeDirectManager(tmp_path, NATIVE_CONTROL_MAPPING)
		ctrl = mgr._lookupControl('battSw')
		assert mgr._translateValue(ctrl, 1) == 0.0

	def test_translateDiscretePos2(self, tmp_path):
		"""3-pos discrete position 2 → native 1.0."""
		mgr = makeDirectManager(tmp_path, NATIVE_CONTROL_MAPPING)
		ctrl = mgr._lookupControl('battSw')
		assert mgr._translateValue(ctrl, 2) == 1.0

	def test_translateMultiPosDiscrete(self, tmp_path):
		"""8-pos discrete (insSwitchChange) position 3 → native 0.3."""
		mgr = makeDirectManager(tmp_path, NATIVE_CONTROL_MAPPING)
		ctrl = mgr._lookupControl('insSwitchChange')
		result = mgr._translateValue(ctrl, 3)
		assert abs(result - 0.3) < 1e-9

	def test_translateMultiPosDiscreteMax(self, tmp_path):
		"""8-pos discrete (insSwitchChange) position 7 → native 0.7."""
		mgr = makeDirectManager(tmp_path, NATIVE_CONTROL_MAPPING)
		ctrl = mgr._lookupControl('insSwitchChange')
		result = mgr._translateValue(ctrl, 7)
		assert abs(result - 0.7) < 1e-9

	def test_translateContinuousMid(self, tmp_path):
		"""Continuous 0.5 → native 0.5 for [0,1] range (proportional)."""
		mgr = makeDirectManager(tmp_path, NATIVE_CONTROL_MAPPING)
		ctrl = mgr._lookupControl('ampcdOffBrightness')
		assert mgr._translateValue(ctrl, 0.5) == 0.5

	def test_translateContinuousClamp(self, tmp_path):
		"""Continuous values outside 0.0-1.0 are clamped."""
		mgr = makeDirectManager(tmp_path, NATIVE_CONTROL_MAPPING)
		ctrl = mgr._lookupControl('ampcdOffBrightness')
		assert mgr._translateValue(ctrl, -0.5) == 0.0
		assert mgr._translateValue(ctrl, 1.5) == 1.0

	def test_translateContinuousNonUnitRange(self, tmp_path):
		"""Continuous 0.5 → native 0.375 for [0, 0.75] range (50% of range)."""
		mgr = makeDirectManager(tmp_path, NATIVE_CONTROL_MAPPING)
		ctrl = mgr._lookupControl('brtKnob')
		assert abs(mgr._translateValue(ctrl, 0.5) - 0.375) < 1e-9
		assert mgr._translateValue(ctrl, 0.0) == 0.0
		assert mgr._translateValue(ctrl, 1.0) == 0.75

	def test_translateToggle(self, tmp_path):
		"""Toggle switch: position 0 → 0.0, position 1 → 1.0."""
		mgr = makeDirectManager(tmp_path, NATIVE_CONTROL_MAPPING)
		ctrl = mgr._lookupControl('toggleSw')
		assert mgr._translateValue(ctrl, 0) == 0.0
		assert mgr._translateValue(ctrl, 1) == 1.0

	def test_translateRelativePassthrough(self, tmp_path):
		"""Relative type: value passes through as float."""
		mgr = makeDirectManager(tmp_path, NATIVE_CONTROL_MAPPING)
		ctrl = mgr._lookupControl('id2163aSetMinAlt')
		assert mgr._translateValue(ctrl, 0.5) == 0.5
		assert mgr._translateValue(ctrl, -0.3) == -0.3

	# ---- _reverseTranslateValue ----

	def test_reverseTranslate3PosDiscrete(self, tmp_path):
		"""Native -1.0/0.0/1.0 → position 0/1/2."""
		mgr = makeDirectManager(tmp_path, NATIVE_CONTROL_MAPPING)
		ctrl = mgr._lookupControl('battSw')
		assert mgr._reverseTranslateValue(ctrl, -1.0) == 0
		assert mgr._reverseTranslateValue(ctrl, 0.0) == 1
		assert mgr._reverseTranslateValue(ctrl, 1.0) == 2

	def test_reverseTranslate3PosSpringCenter(self, tmp_path):
		"""positionMap with None center entry: native 0.0 → position 1, not 0."""
		mgr = makeDirectManager(tmp_path, NATIVE_CONTROL_MAPPING)
		ctrl = mgr._lookupControl('engineCrankLSw')
		assert mgr._reverseTranslateValue(ctrl, -1.0) == 0
		assert mgr._reverseTranslateValue(ctrl, 0.0) == 1
		assert mgr._reverseTranslateValue(ctrl, 1.0) == 2

	def test_reverseTranslateMultiPos(self, tmp_path):
		"""Native 0.3 → position 3 for 8-pos discrete."""
		mgr = makeDirectManager(tmp_path, NATIVE_CONTROL_MAPPING)
		ctrl = mgr._lookupControl('insSwitchChange')
		assert mgr._reverseTranslateValue(ctrl, 0.3) == 3

	def test_reverseTranslateContinuous(self, tmp_path):
		"""Continuous: native 0.5 → proportional 0.5 for [0,1] range."""
		mgr = makeDirectManager(tmp_path, NATIVE_CONTROL_MAPPING)
		ctrl = mgr._lookupControl('ampcdOffBrightness')
		assert mgr._reverseTranslateValue(ctrl, 0.5) == 0.5

	def test_reverseTranslateContinuousNonUnitRange(self, tmp_path):
		"""Continuous: native 0.375 → proportional 0.5 for [0, 0.75] range."""
		mgr = makeDirectManager(tmp_path, NATIVE_CONTROL_MAPPING)
		ctrl = mgr._lookupControl('brtKnob')
		assert abs(mgr._reverseTranslateValue(ctrl, 0.375) - 0.5) < 1e-9
		assert mgr._reverseTranslateValue(ctrl, 0.0) == 0.0
		assert mgr._reverseTranslateValue(ctrl, 0.75) == 1.0

	def test_reverseTranslateDiscreteIndicatorArgLim(self, tmp_path):
		"""indicatorArgLim overrides argLim for readback on discrete controls.

		Ka-50 autopilot buttons: argLim=[0,1] is the press/release command
		range, but the autopilot writes 0.0 (off) or 0.1 (mode active) back
		to the same arg.  With plain argLim+step the 0.1 rounds to position 0;
		indicatorArgLim=[0, 0.1] gives step=0.1 so 0.1 → position 1.
		Values above the indicator range are clamped to the max position.
		"""
		mgr = makeDirectManager(tmp_path, NATIVE_CONTROL_MAPPING)
		ctrl = {
			'type': 'discrete',
			'argLim': [0.0, 1.0],
			'step': 1.0,
			'positions': 2,
			'indicatorArgLim': [0.0, 0.1],
		}
		assert mgr._reverseTranslateValue(ctrl, 0.0) == 0   # off
		assert mgr._reverseTranslateValue(ctrl, 0.1) == 1   # mode active
		assert mgr._reverseTranslateValue(ctrl, 0.2) == 1   # clamped to max
		assert mgr._reverseTranslateValue(ctrl, 0.3) == 1   # clamped to max

	def test_reverseTranslateDiscreteIndicatorPositionsExactMatch(self, tmp_path):
		"""indicatorPositions returns the index of an exactly matching stop-value."""
		mgr = makeDirectManager(tmp_path, NATIVE_CONTROL_MAPPING)
		ctrl = {
			'type': 'discrete',
			'argLim': [1.0, 15.0],
			'step': 1.0,
			'positions': 6,
			'indicatorPositions': [1.0, 3.0, 5.0, 8.0, 12.0, 15.0],
		}
		assert mgr._reverseTranslateValue(ctrl, 1.0) == 0
		assert mgr._reverseTranslateValue(ctrl, 3.0) == 1
		assert mgr._reverseTranslateValue(ctrl, 15.0) == 5

	def test_reverseTranslateDiscreteIndicatorPositionsNearestValue(self, tmp_path):
		"""indicatorPositions returns the index of the nearest stop-value."""
		mgr = makeDirectManager(tmp_path, NATIVE_CONTROL_MAPPING)
		ctrl = {
			'type': 'discrete',
			'argLim': [1.0, 15.0],
			'step': 1.0,
			'positions': 4,
			'indicatorPositions': [1.0, 5.0, 10.0, 15.0],
		}
		assert mgr._reverseTranslateValue(ctrl, 4.0) == 1   # nearer to 5.0 (dist 1) than 1.0 (dist 3)
		assert mgr._reverseTranslateValue(ctrl, 7.0) == 1   # nearer to 5.0 (dist 2) than 10.0 (dist 3)
		assert mgr._reverseTranslateValue(ctrl, 7.6) == 2   # nearer to 10.0 (dist 2.4) than 5.0 (dist 2.6)

	def test_reverseTranslateDiscreteIndicatorPositionsOutOfRange(self, tmp_path):
		"""indicatorPositions clamps values beyond the stop list to the nearest edge."""
		mgr = makeDirectManager(tmp_path, NATIVE_CONTROL_MAPPING)
		ctrl = {
			'type': 'discrete',
			'argLim': [0.0, 10.0],
			'step': 1.0,
			'positions': 3,
			'indicatorPositions': [2.0, 5.0, 8.0],
		}
		assert mgr._reverseTranslateValue(ctrl, 0.0) == 0   # below range → first
		assert mgr._reverseTranslateValue(ctrl, 99.0) == 2  # above range → last

	def test_reverseTranslateReadOnly(self, tmp_path):
		"""Read-only control (no type): returns native value as-is."""
		mgr = makeDirectManager(tmp_path, NATIVE_CONTROL_MAPPING)
		ctrl = mgr._lookupControl('readOnlyArg')
		assert mgr._reverseTranslateValue(ctrl, 0.75) == 0.75

	# ---- Integration: sendControl with translation ----

	def test_sendControlTranslatedDiscrete(self, tmp_path):
		"""sendControl translates position 2 → native 1.0 for TCP command."""
		mgr = makeDirectManager(tmp_path, NATIVE_CONTROL_MAPPING)
		mgr.connected = True
		mgr.socket = MagicMock()
		result = mgr.sendControl('battSw', 2)
		assert result is True
		call = mgr.socket.sendall.call_args[0][0].decode('utf-8')
		assert 'C:3:3001:1.0' in call

	def test_sendControlTranslatedContinuous(self, tmp_path):
		"""sendControl sends native float for continuous control."""
		mgr = makeDirectManager(tmp_path, NATIVE_CONTROL_MAPPING)
		mgr.connected = True
		mgr.socket = MagicMock()
		result = mgr.sendControl('ampcdOffBrightness', 0.75)
		assert result is True
		call = mgr.socket.sendall.call_args[0][0].decode('utf-8')
		assert 'C:37:3001:0.75' in call

	def test_sendControlRelativeUsesSetCommand(self, tmp_path):
		"""sendControl uses S: (SetCommand) for relative controls."""
		mgr = makeDirectManager(tmp_path, NATIVE_CONTROL_MAPPING)
		mgr.connected = True
		mgr.socket = MagicMock()
		result = mgr.sendControl('id2163aSetMinAlt', 0.5)
		assert result is True
		call = mgr.socket.sendall.call_args[0][0].decode('utf-8')
		assert 'S:5:3009:0.5' in call

	def test_sendControlReadOnlyFails(self, tmp_path):
		"""sendControl returns False for read-only controls."""
		mgr = makeDirectManager(tmp_path, NATIVE_CONTROL_MAPPING)
		mgr.connected = True
		mgr.socket = MagicMock()
		result = mgr.sendControl('readOnlyArg', 0)
		assert result is False

	def test_sendControlRawPassesThroughValue(self, tmp_path):
		"""Raw control bypasses translation — caller-supplied value is sent as-is."""
		mgr = makeDirectManager(tmp_path, NATIVE_CONTROL_MAPPING)
		mgr.connected = True
		mgr.socket = MagicMock()
		result = mgr.sendControl('jesterEject', 1)
		assert result is True
		call = mgr.socket.sendall.call_args[0][0].decode('utf-8')
		assert 'C:78:3128:1' in call

	def test_sendControlRawPassesThroughFloat(self, tmp_path):
		"""Raw control passes an arbitrary float value through unchanged (no scaling)."""
		mgr = makeDirectManager(tmp_path, NATIVE_CONTROL_MAPPING)
		mgr.connected = True
		mgr.socket = MagicMock()
		result = mgr.sendControl('jesterEject', 0.75)
		assert result is True
		call = mgr.socket.sendall.call_args[0][0].decode('utf-8')
		assert 'C:78:3128:0.75' in call

	# ---- positionMap controls ----

	def test_sendControlPositionMapLeft(self, tmp_path):
		"""positionMap control: position 0 sends only the target press command."""
		mgr = makeDirectManager(tmp_path, NATIVE_CONTROL_MAPPING)
		mgr.connected = True
		mgr.socket = MagicMock()
		result = mgr.sendControl('engineCrankLSw', 0)
		assert result is True
		# Should send exactly one command: press left (3012:-1.0). No auto-releasing.
		calls = [c[0][0].decode('utf-8').strip() for c in mgr.socket.sendall.call_args_list]
		assert len(calls) == 1
		assert 'C:6:3012:-1.0' in calls[0]

	def test_sendControlPositionMapCenter(self, tmp_path):
		"""positionMap control: position 1 (center/null) releases all buttons."""
		mgr = makeDirectManager(tmp_path, NATIVE_CONTROL_MAPPING)
		mgr.connected = True
		mgr.socket = MagicMock()
		result = mgr.sendControl('engineCrankLSw', 1)
		assert result is True
		calls = [c[0][0].decode('utf-8').strip() for c in mgr.socket.sendall.call_args_list]
		# Should release both commands but not press any.
		assert any('C:6:3012:0.0' in c or 'C:6:3013:0.0' in c for c in calls)
		# Should not press any button (center is null).
		assert not any('-1.0' in c or '1.0\n' in c for c in calls if ':0.0' not in c)


# ---------------------------------------------------------------------------
# Sample mapping for snapshot tests (includes wheel control for displayArgs)
# ---------------------------------------------------------------------------

SNAPSHOT_TEST_MAPPING = {
	'moduleName': 'TestModule',
	'controls': {
		'battSw': {
			'type': 'discrete',
			'deviceId': 3,
			'commandId': 3001,
			'arg': 404,
			'argLim': [-1.0, 1.0],
			'step': 1.0,
			'positions': 3,
			'description': 'Battery Switch',
			'category': 'Electrical',
		},
		'apuControlSw': {
			'type': 'discrete',
			'deviceId': 3,
			'commandId': 3002,
			'arg': 377,
			'argLim': [0.0, 1.0],
			'step': 1.0,
			'positions': 2,
			'description': 'APU Control Switch',
			'category': 'APU',
		},
		'canopyPos': {
			'arg': 181,
			'description': 'Canopy Position',
			'category': 'Canopy',
		},
		'txtRpmL': {
			'indicationId': 5,
			'fieldName': 'txt_RPM_L',
			'description': 'RPM_L',
			'category': 'Engine',
		},
		'radioTuner': {
			'type': 'discrete',
			'deviceId': 10,
			'commandId': 1001,
			'arg': 555,
			'argLim': [0.0, 1.0],
			'step': 0.1,
			'positions': 11,
			'description': 'Radio Tuner Wheel',
			'category': 'Radio',
			'wheel': True,
			'displayArgs': [600, 601],
			'incrementValue': 0.1,
			'decrementValue': -0.1,
		},
	},
}


# ---------------------------------------------------------------------------
# Tests: bulkQueryArgs
# ---------------------------------------------------------------------------

class TestBulkQueryArgs:
	def test_bulkQueryArgsSuccess(self, tmp_path):
		"""bulkQueryArgs sends BULKQ:[json] and parses BULKR:{json} response."""
		mgr = makeDirectManager(tmp_path)
		server = MockTcpServer({'BULKQ:': 'BULKR:{"404":0.5,"377":1.0}'})
		mgr.port = server.port
		mgr.start()
		time.sleep(0.2)

		result = mgr.bulkQueryArgs([404, 377], timeout=2.0)
		mgr.stop()
		server.stop()

		assert result is not None
		assert result[404] == pytest.approx(0.5)
		assert result[377] == pytest.approx(1.0)

	def test_bulkQueryArgsReturnsIntKeys(self, tmp_path):
		"""bulkQueryArgs returns int keys, not string keys."""
		mgr = makeDirectManager(tmp_path)
		server = MockTcpServer({'BULKQ:': 'BULKR:{"42":0.25}'})
		mgr.port = server.port
		mgr.start()
		time.sleep(0.2)

		result = mgr.bulkQueryArgs([42], timeout=2.0)
		mgr.stop()
		server.stop()

		assert result is not None
		assert 42 in result
		assert '42' not in result

	def test_bulkQueryArgsTimeout(self, tmp_path):
		"""bulkQueryArgs returns None when no response arrives in time."""
		mgr = makeDirectManager(tmp_path)
		server = MockTcpServer({})  # No responses.
		mgr.port = server.port
		mgr.start()
		time.sleep(0.2)

		result = mgr.bulkQueryArgs([404], timeout=0.3)
		mgr.stop()
		server.stop()

		assert result is None

	def test_bulkQueryArgsNotConnected(self, tmp_path):
		"""bulkQueryArgs returns None when not connected to DCS."""
		mgr = makeDirectManager(tmp_path)
		# Not started — no socket.
		result = mgr.bulkQueryArgs([404], timeout=0.1)
		assert result is None


# ---------------------------------------------------------------------------
# Tests: snapshotCockpitState
# ---------------------------------------------------------------------------

class TestSnapshotCockpitState:
	def _makeSnapshotMgr(self, tmp_path):
		"""Build a manager with the snapshot test mapping, mock bulkQueryArgs."""
		mgr = makeDirectManager(tmp_path, SNAPSHOT_TEST_MAPPING)
		return mgr

	def test_snapshotMapsArgToCanonicalName(self, tmp_path):
		"""snapshotCockpitState maps arg numbers back to 'module/canonical' refs."""
		mgr = self._makeSnapshotMgr(tmp_path)
		# Return known values for all args in the mapping.
		knownValues = {404: 0.0, 377: 1.0, 181: 0.5, 600: 0.3}
		mgr.bulkQueryArgs = lambda argList, timeout=10.0: {a: knownValues[a] for a in argList if a in knownValues}

		result = mgr.snapshotCockpitState('TestModule')

		assert result is not None
		assert result['TestModule/battSw'] == pytest.approx(0.0)
		assert result['TestModule/apuControlSw'] == pytest.approx(1.0)
		assert result['TestModule/canopyPos'] == pytest.approx(0.5)

	def test_snapshotExcludesIndicationOnlyControls(self, tmp_path):
		"""snapshotCockpitState excludes controls with no arg field (indication-only)."""
		mgr = self._makeSnapshotMgr(tmp_path)
		mgr.bulkQueryArgs = lambda argList, timeout=10.0: {a: 0.0 for a in argList}

		result = mgr.snapshotCockpitState('TestModule')

		assert 'TestModule/txtRpmL' not in result

	def test_snapshotUsesDisplayArgsForWheelControls(self, tmp_path):
		"""snapshotCockpitState uses displayArgs[0] for wheel controls, not arg."""
		mgr = self._makeSnapshotMgr(tmp_path)
		capturedArgs = []

		def mockBulk(argList, timeout=10.0):
			capturedArgs.extend(argList)
			# Return 0.3 for displayArgs[0] = 600, nothing for arg 555.
			return {a: 0.3 for a in argList if a == 600}

		mgr.bulkQueryArgs = mockBulk
		result = mgr.snapshotCockpitState('TestModule')

		# Should have requested 600 (displayArgs[0]), not 555 (wheel's own arg).
		assert 600 in capturedArgs
		assert 555 not in capturedArgs
		assert result.get('TestModule/radioTuner') == pytest.approx(0.3)

	def test_snapshotReturnsNoneOnTimeout(self, tmp_path):
		"""snapshotCockpitState returns None when bulkQueryArgs times out."""
		mgr = self._makeSnapshotMgr(tmp_path)
		mgr.bulkQueryArgs = lambda argList, timeout=10.0: None

		result = mgr.snapshotCockpitState('TestModule')
		assert result is None

	def test_snapshotAllModulesWhenNoneSpecified(self, tmp_path):
		"""snapshotCockpitState covers all loaded modules when moduleName is None."""
		extraMapping = {
			'moduleName': 'OtherModule',
			'controls': {
				'fuelSw': {'type': 'discrete', 'deviceId': 1, 'commandId': 1, 'arg': 999, 'argLim': [0.0, 1.0], 'step': 1.0, 'positions': 2, 'description': 'Fuel Switch', 'category': 'Fuel'},
			},
		}
		config = {'dcsDirectHost': '127.0.0.1', 'dcsDirectPort': 0}
		with patch.object(DCSDirectManager, '_loadControlMapping') as mockLoad:
			mockLoad.return_value = {
				'TestModule': SNAPSHOT_TEST_MAPPING,
				'OtherModule': extraMapping,
			}
			mgr = DCSDirectManager(config)

		capturedArgs = []

		def mockBulk(argList, timeout=10.0):
			capturedArgs.extend(argList)
			return {a: 0.0 for a in argList}

		mgr.bulkQueryArgs = mockBulk
		result = mgr.snapshotCockpitState()

		assert 404 in capturedArgs   # TestModule/battSw
		assert 999 in capturedArgs   # OtherModule/fuelSw
		assert 'TestModule/battSw' in result
		assert 'OtherModule/fuelSw' in result

	def test_snapshotEmptyForUnknownModule(self, tmp_path):
		"""snapshotCockpitState returns empty dict for a module not in mappings."""
		mgr = self._makeSnapshotMgr(tmp_path)
		result = mgr.snapshotCockpitState('NonExistentModule')
		assert result == {}


# ---------------------------------------------------------------------------
# Tests: rawScanSnapshot
# ---------------------------------------------------------------------------

class TestRawScanSnapshot:
	def test_rawScanSuccess(self, tmp_path):
		"""rawScanSnapshot sends BULKQ:scan:N and parses BULKR:{json} response."""
		mgr = makeDirectManager(tmp_path)
		server = MockTcpServer({'BULKQ:scan:': 'BULKR:{"0":0.0,"42":0.5,"100":1.0}'})
		mgr.port = server.port
		mgr.start()
		time.sleep(0.2)

		result = mgr.rawScanSnapshot(maxArg=999, timeout=2.0)
		mgr.stop()
		server.stop()

		assert result is not None
		assert result[0] == pytest.approx(0.0)
		assert result[42] == pytest.approx(0.5)
		assert result[100] == pytest.approx(1.0)

	def test_rawScanReturnsIntKeys(self, tmp_path):
		"""rawScanSnapshot returns int keys."""
		mgr = makeDirectManager(tmp_path)
		server = MockTcpServer({'BULKQ:scan:': 'BULKR:{"7":0.75}'})
		mgr.port = server.port
		mgr.start()
		time.sleep(0.2)

		result = mgr.rawScanSnapshot(timeout=2.0)
		mgr.stop()
		server.stop()

		assert result is not None
		assert 7 in result
		assert '7' not in result

	def test_rawScanTimeout(self, tmp_path):
		"""rawScanSnapshot returns None when no response arrives in time."""
		mgr = makeDirectManager(tmp_path)
		server = MockTcpServer({})
		mgr.port = server.port
		mgr.start()
		time.sleep(0.2)

		result = mgr.rawScanSnapshot(timeout=0.3)
		mgr.stop()
		server.stop()

		assert result is None

	def test_rawScanSendsCorrectCommand(self, tmp_path):
		"""rawScanSnapshot sends BULKQ:scan:N with the specified maxArg."""
		mgr = makeDirectManager(tmp_path)
		server = MockTcpServer({'BULKQ:scan:': 'BULKR:{}'})
		mgr.port = server.port
		mgr.start()
		time.sleep(0.2)

		mgr.rawScanSnapshot(maxArg=500, timeout=2.0)
		mgr.stop()
		server.stop()

		assert any('BULKQ:scan:500' in cmd for cmd in server.receivedCommands)
