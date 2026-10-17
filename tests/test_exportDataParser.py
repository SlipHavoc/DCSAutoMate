"""Tests for network.DCSAutoMateExportManager — text data parsing and formatting."""
import sys
from unittest.mock import MagicMock

import pytest

# Stub PySide6
sys.modules.setdefault('PySide6', type(sys)('PySide6'))
_qtw = type(sys)('PySide6.QtWidgets')
_qtw.QMessageBox = MagicMock()
sys.modules.setdefault('PySide6.QtWidgets', _qtw)

from network.DCSAutoMateExportManager import DCSAutoMateExportManager


def makeExportManager():
	"""Create an export manager without opening a real socket."""
	import threading
	mgr = DCSAutoMateExportManager.__new__(DCSAutoMateExportManager)
	mgr.config = {}
	mgr.dataStorage = {}
	mgr.messages = {
		'noData': 'No data to show.',
		'error': 'Error',
	}
	mgr.lock = threading.Lock()
	mgr.outputString = ''
	return mgr


# -----------------------------------------------------------------------
# parseData
# -----------------------------------------------------------------------

class TestParseData:
	def test_basicKeyValue(self):
		mgr = makeExportManager()
		data = b'altitude=1500;speed=300'
		result = mgr.parseData(data)
		assert result['altitude'] == 1500
		assert result['speed'] == 300

	def test_floatValues(self):
		mgr = makeExportManager()
		data = b'alt=1500.5;airspeed=230.0'
		result = mgr.parseData(data)
		assert result['alt'] == 1500.5
		assert result['airspeed'] == 230.0

	def test_nestedKeys(self):
		mgr = makeExportManager()
		data = b'LoGetSelfData.Name=FA-18C_hornet;LoGetEngineInfo.RPM.left=80'
		result = mgr.parseData(data)
		assert result['LoGetSelfData']['Name'] == 'FA-18C_hornet'
		assert result['LoGetEngineInfo']['RPM']['left'] == 80

	def test_stringValues(self):
		mgr = makeExportManager()
		data = b'moduleName=FA-18C_hornet'
		result = mgr.parseData(data)
		assert result['moduleName'] == 'FA-18C_hornet'

	def test_booleanValues(self):
		mgr = makeExportManager()
		data = b'active=true;paused=false'
		result = mgr.parseData(data)
		assert result['active'] is True
		assert result['paused'] is False

	def test_emptyData(self):
		mgr = makeExportManager()
		result = mgr.parseData(b'')
		assert result == {}

	def test_trailingSemicolon(self):
		mgr = makeExportManager()
		data = b'key=value;'
		result = mgr.parseData(data)
		assert result['key'] == 'value'

	def test_fullSampleData(self, sampleExportData):
		mgr = makeExportManager()
		result = mgr.parseData(sampleExportData)
		assert result['LoGetAltitudeAboveSeaLevel'] == 1500.5
		assert result['LoGetMissionStartTime'] == 21600
		assert result['LoGetSelfData']['Name'] == 'FA-18C_hornet'
		assert result['LoGetEngineInfo']['RPM']['left'] == 80


# -----------------------------------------------------------------------
# parseValue
# -----------------------------------------------------------------------

class TestParseValue:
	def test_int(self):
		mgr = makeExportManager()
		assert mgr.parseValue('42') == 42
		assert isinstance(mgr.parseValue('42'), int)

	def test_float(self):
		mgr = makeExportManager()
		assert mgr.parseValue('3.14') == 3.14
		assert isinstance(mgr.parseValue('3.14'), float)

	def test_trueString(self):
		mgr = makeExportManager()
		assert mgr.parseValue('true') is True
		assert mgr.parseValue('True') is True

	def test_falseString(self):
		mgr = makeExportManager()
		assert mgr.parseValue('false') is False

	def test_plainString(self):
		mgr = makeExportManager()
		assert mgr.parseValue('hello') == 'hello'

	def test_emptyString(self):
		mgr = makeExportManager()
		assert mgr.parseValue('') == ''


# -----------------------------------------------------------------------
# formatTimeHHMMSS
# -----------------------------------------------------------------------

class TestFormatTimeHHMMSS:
	def test_midnight(self):
		mgr = makeExportManager()
		assert mgr.formatTimeHHMMSS(0) == '00:00:00'

	def test_oneHourOneMinOneSecond(self):
		mgr = makeExportManager()
		assert mgr.formatTimeHHMMSS(3661) == '01:01:01'

	def test_midday(self):
		mgr = makeExportManager()
		assert mgr.formatTimeHHMMSS(43200) == '12:00:00'

	def test_endOfDay(self):
		mgr = makeExportManager()
		assert mgr.formatTimeHHMMSS(86399) == '23:59:59'

	def test_missionTime(self):
		"""Typical DCS mission start time (6:00 AM) + 5 minutes elapsed."""
		mgr = makeExportManager()
		missionStart = 21600  # 6:00 AM
		elapsed = 300  # 5 minutes
		assert mgr.formatTimeHHMMSS(missionStart + elapsed) == '06:05:00'


# -----------------------------------------------------------------------
# buildOutputString
# -----------------------------------------------------------------------

class TestBuildOutputString:
	def test_withFullData(self, sampleExportData):
		mgr = makeExportManager()
		mgr.dataStorage = mgr.parseData(sampleExportData)
		output = mgr.buildOutputString()
		assert 'FA-18C_hornet' in output
		assert 'Engine is running' in output

	def test_withNoData(self):
		mgr = makeExportManager()
		mgr.dataStorage = {}
		output = mgr.buildOutputString()
		assert output == 'No data to show.'

	def test_engineOff(self, sampleExportData):
		mgr = makeExportManager()
		mgr.dataStorage = mgr.parseData(sampleExportData)
		mgr.dataStorage['LoGetEngineInfo']['RPM']['left'] = 0
		output = mgr.buildOutputString()
		assert 'Engine is off' in output
