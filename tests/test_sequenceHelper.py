"""Tests for engine.SequenceHelper — pure-logic functions."""
import os
import sys
from unittest.mock import patch

import pytest

# Stub out heavyweight dependencies that SequenceHelper imports at module level
# but that we don't need for pure-logic tests.
sys.modules.setdefault('PySide6', type(sys)('PySide6'))
sys.modules.setdefault('PySide6.QtWidgets', type(sys)('PySide6.QtWidgets'))

from engine.SequenceHelper import SequenceHelper


@pytest.fixture
def helper():
	"""Create a SequenceHelper with a minimal config and no real dependencies."""
	config = {
		'dcsSavedGamesPath': '',
		'udpUiWireLogEnabled': False,
		'udpBiosWireLogEnabled': False,
	}
	return SequenceHelper(config)


# -----------------------------------------------------------------------
# mgrsTruncate
# -----------------------------------------------------------------------

class TestMgrsTruncate:
	def test_truncateTo6(self, helper):
		result = helper.mgrsTruncate('37TGG2906959063', 6)
		assert result == '37TGG290590'

	def test_truncateTo8(self, helper):
		result = helper.mgrsTruncate('37TGG2906959063', 8)
		assert result == '37TGG29065906'

	def test_truncateTo10_noChange(self, helper):
		"""When requesting 10 digits and input already has 10, return as-is."""
		result = helper.mgrsTruncate('37TGG2906959063', 10)
		assert result == '37TGG2906959063'

	def test_requestMorePrecisionThanAvailable(self, helper):
		"""If the requested precision >= available precision, return original."""
		result = helper.mgrsTruncate('37TGG290590', 10)
		assert result == '37TGG290590'

	def test_emptyString(self, helper):
		assert helper.mgrsTruncate('', 6) == ''

	def test_noneInput(self, helper):
		assert helper.mgrsTruncate(None, 6) == ''

	def test_invalidFormat(self, helper):
		"""Non-MGRS strings should be returned as-is."""
		assert helper.mgrsTruncate('not-mgrs', 6) == 'NOT-MGRS'

	def test_oddDigitCount(self, helper):
		"""If the numeric portion has an odd number of digits, return as-is."""
		assert helper.mgrsTruncate('37TGG12345', 6) == '37TGG12345'

	def test_lowercaseNormalized(self, helper):
		"""Input should be uppercased."""
		result = helper.mgrsTruncate('37tgg2906959063', 6)
		assert result == '37TGG290590'

	def test_spacesStripped(self, helper):
		result = helper.mgrsTruncate('37T GG 29069 59063', 8)
		assert result == '37TGG29065906'

	def test_singleDigitZone(self, helper):
		result = helper.mgrsTruncate('4QFJ1234556789', 6)
		assert result == '4QFJ123567'


# -----------------------------------------------------------------------
# _parseKeyValueMessage
# -----------------------------------------------------------------------

class TestParseKeyValueMessage:
	def test_basicParsing(self, helper):
		msg = 'DCSAUTOMATE_UI;event=log;text=hello world;'
		result = helper._parseKeyValueMessage(msg)
		assert result['_type'] == 'DCSAUTOMATE_UI'
		assert result['event'] == 'log'
		assert result['text'] == 'hello world'

	def test_noSemicolons(self, helper):
		result = helper._parseKeyValueMessage('PLAIN_MESSAGE')
		assert result['_type'] == 'PLAIN_MESSAGE'

	def test_emptyValue(self, helper):
		result = helper._parseKeyValueMessage('TYPE;key=;other=val')
		assert result['key'] == ''
		assert result['other'] == 'val'

	def test_equalsInValue(self, helper):
		"""The value may itself contain '=' characters."""
		result = helper._parseKeyValueMessage('T;data=a=b=c')
		assert result['data'] == 'a=b=c'

	def test_trailingSemicolon(self, helper):
		result = helper._parseKeyValueMessage('T;k=v;')
		assert result['k'] == 'v'


# -----------------------------------------------------------------------
# getScratchpadData (with mocked file I/O)
# -----------------------------------------------------------------------

class TestGetScratchpadData:
	def test_parseSingleWaypoint(self, helper, scratchpadDir):
		"""Parse a single scratchpad entry with DMS/DDM/MGRS/altitude."""
		helper.config['dcsSavedGamesPath'] = str(scratchpadDir.parent)
		waypoints = helper.getScratchpadData('test.txt')
		assert len(waypoints) == 1

		wp = waypoints[0]
		# Check lat/lon DD computed from DMS
		assert abs(wp['latLonDD']['lat']['deg'] - 42.050247) < 0.001
		assert abs(wp['latLonDD']['lon']['deg'] - 41.767456) < 0.001

		# Check MGRS 10-digit
		assert wp['mgrs10'] == '37TGG2906959063'
		# Check MGRS truncations
		assert wp['mgrs6'] == '37TGG290590'
		assert wp['mgrs8'] == '37TGG29065906'

		# Check altitude
		assert wp['altMeters'] == 5.0
		assert wp['altFeet'] == 16.0

	def test_emptyFilename(self, helper):
		assert helper.getScratchpadData('') == []
		assert helper.getScratchpadData(None) == []

	def test_missingFile(self, helper, scratchpadDir):
		helper.config['dcsSavedGamesPath'] = str(scratchpadDir.parent)
		assert helper.getScratchpadData('nonexistent.txt') == []

	def test_multipleWaypoints(self, helper, tmp_path):
		"""Two waypoint blocks should both be parsed."""
		spDir = tmp_path / 'Scratchpad'
		spDir.mkdir()
		content = (
			'DMS: N  42\u00b003\'00.89", E 041\u00b046\'04.84"\n'
			'DDM: N  42\u00b003.0150\', E 041\u00b046.0808\'\n'
			'MGRS: 37 T GG 29069 59063\n'
			'N/S (m): -305405, E/W (m): 626345\n'
			'5m, 16ft\n'
			'\n'
			'DMS: S  10\u00b020\'30.00", W 020\u00b040\'50.00"\n'
			'DDM: S  10\u00b020.5000\', W 020\u00b040.8333\'\n'
			'MGRS: 33 M XA 12345 67890\n'
			'N/S (m): 100000, E/W (m): 200000\n'
			'100m, 328ft\n'
		)
		(spDir / 'multi.txt').write_text(content, encoding='utf-8')
		helper.config['dcsSavedGamesPath'] = str(tmp_path)
		waypoints = helper.getScratchpadData('multi.txt')
		assert len(waypoints) == 2
		# Second waypoint should have negative lat (S hemisphere)
		assert waypoints[1]['latLonDD']['lat']['deg'] < 0
		# Second waypoint should have negative lon (W hemisphere)
		assert waypoints[1]['latLonDD']['lon']['deg'] < 0


# -----------------------------------------------------------------------
# _luaTableGet
# -----------------------------------------------------------------------

class TestLuaTableGet:
	def test_validKey(self, helper):
		table = {'a': 1, 'b': 2}
		assert helper._luaTableGet(table, 'a') == 1

	def test_missingKey(self, helper):
		table = {'a': 1}
		assert helper._luaTableGet(table, 'z', 'default') == 'default'

	def test_noneValue(self, helper):
		table = {'a': None}
		assert helper._luaTableGet(table, 'a', 42) == 42


# -----------------------------------------------------------------------
# Live scripts: queued commands, live reads, offline collection
# -----------------------------------------------------------------------

class TestTakeQueued:
	def test_returnsOnlyCommandsAddedSinceLastTake(self, helper):
		seq = []
		pushSeqCmd = helper.makePushSeqCmd(seq)
		pushSeqCmd(0, 'first', 1)
		assert [c['cmd'] for c in helper.takeQueued()] == ['first']
		pushSeqCmd(0, 'second', 1)
		pushSeqCmd(0, 'third', 1)
		assert [c['cmd'] for c in helper.takeQueued()] == ['second', 'third']
		assert helper.takeQueued() == []

	def test_newPushSeqCmdStartsAFreshQueue(self, helper):
		helper.makePushSeqCmd([])(0, 'oldScript', 1)
		pushSeqCmd = helper.makePushSeqCmd([])
		pushSeqCmd(0, 'newScript', 1)
		assert [c['cmd'] for c in helper.takeQueued()] == ['newScript']


class TestRead:
	def test_returnsValueFromInstalledReader(self, helper):
		helper.setControlReader(lambda control: {'Mod/arg.helmet': 0.5}[control])
		assert helper.read('Mod/arg.helmet') == 0.5

	def test_unreadableValueReturnsDefault(self, helper):
		helper.setControlReader(lambda control: None)
		assert helper.read('Mod/arg.helmet', default=1.0) == 1.0

	def test_unreadableValueWithoutDefaultRaises(self, helper):
		helper.setControlReader(lambda control: None)
		with pytest.raises(RuntimeError, match='Mod/arg.helmet'):
			helper.read('Mod/arg.helmet')

	def test_noReaderUsesDefaultOrRaises(self, helper):
		assert helper.read('Mod/arg.helmet', default=0) == 0
		with pytest.raises(RuntimeError, match='Mod/arg.helmet'):
			helper.read('Mod/arg.helmet')

	def test_zeroIsAValueNotMissing(self, helper):
		helper.setControlReader(lambda control: 0)
		assert helper.read('Mod/arg.helmet', default=1.0) == 0


class TestCollectSequence:
	def test_listIsReturnedUnchanged(self, helper):
		seq = [{'time': 0, 'cmd': 'a'}]
		assert helper.collectSequence(seq) is seq

	def test_generatorIsDrainedInOrder(self, helper):
		def liveScript():
			seq = []
			pushSeqCmd = helper.makePushSeqCmd(seq)
			pushSeqCmd(0, 'beforeYield', 1)
			yield
			pushSeqCmd(0, 'afterYield', 1)
			yield
			pushSeqCmd(0, 'atEnd', 1)
			return seq
		assert [c['cmd'] for c in helper.collectSequence(liveScript())] == ['beforeYield', 'afterYield', 'atEnd']
