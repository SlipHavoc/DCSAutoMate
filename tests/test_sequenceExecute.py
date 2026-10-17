"""Integration tests for engine.DCSSeqExecute — command execution engine.

Tests verify that execute() correctly dispatches DCS BIOS commands, keyboard
input, speech, text output, cockpit state waiting, and timers.  Most tests run
in debug mode to avoid real socket/window/keyboard dependencies.
"""
import sys
import threading
import time
from unittest.mock import MagicMock, patch

import pytest

# Stub PySide6 before importing the module under test.
# Use setdefault to get the existing module (or create it), then ensure QApplication is set.
sys.modules.setdefault('PySide6', type(sys)('PySide6'))
_qtw = sys.modules.setdefault('PySide6.QtWidgets', type(sys)('PySide6.QtWidgets'))
_qtw.QMessageBox = MagicMock()
_qtw.QApplication = MagicMock()

from engine.DCSSeqExecute import DCSSeqExecute, formatClock, formatDuration, newScriptTimer, scriptTimerElapsed, telemetryFunctionsWaitedOn


@pytest.mark.parametrize('seconds,expected', [
	(0, '0s'),
	(12.4, '12s'),
	(59.6, '1m00s'),
	(225, '3m45s'),
	(605, '10m05s'),
	(3725, '1h02m05s'),
])
def test_formatDuration(seconds, expected):
	assert formatDuration(seconds) == expected


# ---------------------------------------------------------------------------
# Mock descriptions — used by getDescriptions
# ---------------------------------------------------------------------------

MOCK_DESCRIPTIONS = {
	'apuSw': {
		'description': 'APU Switch',
		'category': 'Systems',
	},
	'gearHandle': {
		'description': 'Gear Lever',
		'category': 'Systems',
	},
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def makeMockDbe():
	"""Create a mock DCSDirectManager with enough state for execute()."""
	dbe = MagicMock()
	dbe.getDescriptions.return_value = MOCK_DESCRIPTIONS
	dbe.controlExists.return_value = True
	dbe.getControlState.return_value = [('TestModule/apuSw', 'APU Switch', 1)]
	return dbe


def makeTestConfig(debug=True):
	"""Create a minimal config dict for testing."""
	return {
		'debug': debug,
		'dcsWindowUseTitle': True,
		'dcsWindowTitleOverride': '',
		'dcsBiosReceivePort': 7778,
	}


def makeExecutor(config=None, dbe=None, stopFlag=None, resumeEvent=None, pauseCallback=None, skipWaitEvent=None, waitStateCallback=None):
	"""Create a DCSSeqExecute instance with mocked dependencies.

	Returns (executor, outputLines, ttsManager, stopFlag).
	"""
	if config is None:
		config = makeTestConfig()
	if dbe is None:
		dbe = makeMockDbe()
	if stopFlag is None:
		stopFlag = threading.Event()

	output = []
	def captureOutput(text, flush=False):
		output.append(str(text))

	ttsManager = MagicMock()

	if resumeEvent is None:
		resumeEvent = threading.Event()
		resumeEvent.set()  # Running (not paused).

	executor = DCSSeqExecute(
		root=MagicMock(),
		config=config,
		dbe=dbe,
		scriptData={'moduleName': 'TestModule'},
		vars={},
		updateOutput=captureOutput,
		stopFlag=stopFlag,
		logFunc=MagicMock(),
		ttsManager=ttsManager,
		resumeEvent=resumeEvent,
		pauseCallback=pauseCallback,
		skipWaitEvent=skipWaitEvent,
		waitStateCallback=waitStateCallback,
	)

	return executor, output, ttsManager, stopFlag


# ---------------------------------------------------------------------------
# Debug-mode execution tests
# ---------------------------------------------------------------------------

class TestDebugExecution:
	def test_biosCommandInOutput(self):
		executor, output, _, _ = makeExecutor()
		seq = [
			{'time': 0, 'cmd': 'apuSw', 'arg': '1', 'msg': 'APU on'},
		]
		executor.execute(seq)
		joined = ''.join(output)
		assert 'APU Switch' in joined
		assert 'apuSw' in joined
		assert 'APU on' in joined

	def test_speechCallsTts(self):
		executor, output, ttsManager, _ = makeExecutor()
		seq = [
			{'time': 0, 'cmd': 'scriptSpeech', 'arg': 'Starting engines', 'msg': ''},
		]
		executor.execute(seq)
		ttsManager.speak.assert_any_call('Starting engines', asyncFlag=True)
		joined = ''.join(output)
		assert 'Speaking' in joined

	def test_keyboardCommandProcessed(self):
		executor, output, _, _ = makeExecutor()
		seq = [
			{'time': 0, 'cmd': 'scriptKeyboard', 'arg': 'a press', 'msg': ''},
		]
		executor.execute(seq)
		joined = ''.join(output)
		assert 'Keyboard command' in joined
		# After last keyboard command, counter is set to -1.
		assert executor.executedScriptKeyboardCommands == -1

	def test_textCommandInOutput(self):
		executor, output, _, _ = makeExecutor()
		seq = [
			{'time': 0, 'cmd': 'scriptText', 'arg': 'Custom message here', 'msg': ''},
		]
		executor.execute(seq)
		joined = ''.join(output)
		assert 'Custom message here' in joined

	def test_commandsRunInOrder(self):
		executor, output, _, _ = makeExecutor()
		seq = [
			{'time': 0, 'cmd': 'scriptText', 'arg': 'FIRST', 'msg': ''},
			{'time': 0, 'cmd': 'scriptText', 'arg': 'SECOND', 'msg': ''},
			{'time': 0, 'cmd': 'scriptText', 'arg': 'THIRD', 'msg': ''},
		]
		executor.execute(seq)
		joined = ''.join(output)
		assert joined.index('FIRST') < joined.index('SECOND') < joined.index('THIRD')

	def test_scriptCompleteInOutput(self):
		executor, output, ttsManager, _ = makeExecutor()
		seq = [
			{'time': 0, 'cmd': 'apuSw', 'arg': '1', 'msg': ''},
		]
		executor.execute(seq)
		joined = ''.join(output)
		assert 'Script complete' in joined
		ttsManager.speak.assert_any_call('Script complete', asyncFlag=False)

	def test_scriptCompleteShowsTotalTime(self):
		executor, output, _, _ = makeExecutor()
		clockReads = []
		def clock():
			clockReads.append(1)
			return 1000.0 if len(clockReads) == 1 else 1225.0
		with patch('engine.DCSSeqExecute.time.time', side_effect=clock):
			executor.execute([])
		assert 'Script complete (3m45s)\n' in ''.join(output)

	def test_debugModeMessage(self):
		executor, output, _, _ = makeExecutor()
		seq = [{'time': 0, 'cmd': 'scriptText', 'arg': 'x', 'msg': ''}]
		executor.execute(seq)
		joined = ''.join(output)
		assert 'DEBUG MODE' in joined

	def test_emptySequenceCompletes(self):
		executor, output, _, _ = makeExecutor()
		executor.execute([])
		joined = ''.join(output)
		assert 'Script complete' in joined


# ---------------------------------------------------------------------------
# Cockpit state tests (debug mode)
# ---------------------------------------------------------------------------

class TestCockpitStateDebug:
	def test_passesImmediatelyInDebug(self):
		"""In debug mode, cockpit state conditions pass immediately (duration=0)."""
		executor, output, _, _ = makeExecutor()
		seq = [
			{'time': 0, 'cmd': 'scriptCockpitState', 'control': 'TestModule/apuSw', 'condition': '=', 'value': 1, 'duration': 0, 'msg': ''},
			{'time': 0, 'cmd': 'scriptText', 'arg': 'AFTER_WAIT', 'msg': ''},
		]
		executor.execute(seq)
		joined = ''.join(output)
		assert 'Condition met' in joined
		assert 'AFTER_WAIT' in joined

	def test_cockpitStateWithDuration(self):
		"""In debug mode, even a non-zero duration passes because time advances."""
		executor, output, _, _ = makeExecutor()
		seq = [
			{'time': 0, 'cmd': 'scriptCockpitState', 'control': 'TestModule/apuSw', 'condition': '=', 'value': 1, 'duration': 0.02, 'msg': ''},
			{'time': 0, 'cmd': 'scriptText', 'arg': 'DONE', 'msg': ''},
		]
		executor.execute(seq)
		joined = ''.join(output)
		assert 'Condition met' in joined
		assert 'DONE' in joined


# ---------------------------------------------------------------------------
# Cockpit state tests (non-debug, mocked dbe)
# These tests execute sequences in non-debug mode, which requires the DCS
# window to be present.  They are skipped automatically when DCS is not running.
# ---------------------------------------------------------------------------

@pytest.mark.requires_dcs
class TestCockpitStateLive:
	def test_intConditionMet(self):
		"""Non-debug mode: int condition met immediately."""
		dbe = makeMockDbe()
		dbe.getControlState.return_value = [('TestModule/apuSw', 'APU Switch', 1)]
		config = makeTestConfig(debug=False)
		executor, output, _, _ = makeExecutor(config=config, dbe=dbe)
		seq = [
			{'time': 0, 'cmd': 'scriptCockpitState', 'control': 'TestModule/apuSw', 'condition': '=', 'value': 1, 'duration': 0, 'msg': ''},
			{'time': 0, 'cmd': 'scriptText', 'arg': 'DONE', 'msg': ''},
		]
		executor.execute(seq)
		joined = ''.join(output)
		assert 'Condition met' in joined
		assert 'DONE' in joined

	def test_emptyStringSkipsWithoutCrash(self):
		"""Non-debug mode: empty string from unpowered display doesn't crash, waits for valid value."""
		dbe = makeMockDbe()
		callCount = [0]
		def mockGetControlState(control):
			callCount[0] += 1
			if callCount[0] <= 3:
				return [('TestModule/txtRpmR', 'RPM_R', '')]
			return [('TestModule/txtRpmR', 'RPM_R', '63')]
		dbe.getControlState.side_effect = mockGetControlState
		config = makeTestConfig(debug=False)
		executor, output, _, _ = makeExecutor(config=config, dbe=dbe)
		seq = [
			{'time': 0, 'cmd': 'scriptCockpitState', 'control': 'TestModule/txtRpmR', 'condition': '>=', 'value': 15, 'duration': 0, 'msg': ''},
			{'time': 0, 'cmd': 'scriptText', 'arg': 'DONE', 'msg': ''},
		]
		executor.execute(seq)
		joined = ''.join(output)
		assert 'Condition met' in joined
		assert callCount[0] >= 4

	def test_unansweredReadRetriesWithoutCrash(self):
		"""Non-debug mode: a read DCS doesn't answer (e.g. a timeout on a laggy MP server) is retried, not an IndexError."""
		dbe = makeMockDbe()
		callCount = [0]
		def mockGetControlState(control):
			callCount[0] += 1
			if callCount[0] <= 2:
				return []
			return [('TestModule/apuSw', 'APU Switch', 1)]
		dbe.getControlState.side_effect = mockGetControlState
		config = makeTestConfig(debug=False)
		executor, output, _, _ = makeExecutor(config=config, dbe=dbe)
		seq = [
			{'time': 0, 'cmd': 'scriptCockpitState', 'control': 'TestModule/apuSw', 'condition': '>', 'value': 0, 'duration': 0, 'msg': ''},
			{'time': 0, 'cmd': 'scriptText', 'arg': 'DONE', 'msg': ''},
		]
		executor.execute(seq)
		joined = ''.join(output)
		assert 'Condition met' in joined
		assert 'DONE' in joined
		assert callCount[0] >= 3

	def test_unansweredReadDoesNotMeetStringCondition(self):
		"""An unanswered read is unreadable, not the string 'None', which would satisfy contains 'N'."""
		executor, _, _, _ = makeExecutor()
		assert executor._evaluateCondition(None, 'contains', 'N', 'str') is None

	def test_decimalStringConvertsToFloat(self):
		"""Non-debug mode: decimal string like '63.5' converts to float 63.5."""
		dbe = makeMockDbe()
		dbe.getControlState.return_value = [('TestModule/txtRpmR', 'RPM_R', '63.5')]
		config = makeTestConfig(debug=False)
		executor, output, _, _ = makeExecutor(config=config, dbe=dbe)
		seq = [
			{'time': 0, 'cmd': 'scriptCockpitState', 'control': 'TestModule/txtRpmR', 'condition': '>=', 'value': 63, 'duration': 0, 'msg': ''},
			{'time': 0, 'cmd': 'scriptText', 'arg': 'DONE', 'msg': ''},
		]
		executor.execute(seq)
		joined = ''.join(output)
		assert 'Condition met' in joined

	def test_floatValueCondition(self):
		"""Non-debug mode: float value like 0.0 in command matches against a continuous control."""
		dbe = makeMockDbe()
		dbe.getControlState.return_value = [('TestModule/apuSw', 'APU_SW', '0.0')]
		config = makeTestConfig(debug=False)
		executor, output, _, _ = makeExecutor(config=config, dbe=dbe)
		seq = [
			{'time': 0, 'cmd': 'scriptCockpitState', 'control': 'TestModule/apuSw', 'condition': '=', 'value': 0.0, 'duration': 0, 'msg': ''},
			{'time': 0, 'cmd': 'scriptText', 'arg': 'DONE', 'msg': ''},
		]
		executor.execute(seq)
		joined = ''.join(output)
		assert 'Condition met' in joined

	def test_floatValueNotMetThenMet(self):
		"""Non-debug mode: float value with <= condition, not met initially then met."""
		dbe = makeMockDbe()
		callCount = [0]
		def mockGetControlState(control):
			callCount[0] += 1
			if callCount[0] <= 3:
				return [('TestModule/apuSw', 'APU_SW', '0.98')]
			return [('TestModule/apuSw', 'APU_SW', '0.01')]
		dbe.getControlState.side_effect = mockGetControlState
		config = makeTestConfig(debug=False)
		executor, output, _, _ = makeExecutor(config=config, dbe=dbe)
		seq = [
			{'time': 0, 'cmd': 'scriptCockpitState', 'control': 'TestModule/apuSw', 'condition': '<=', 'value': 0.05, 'duration': 0, 'msg': ''},
			{'time': 0, 'cmd': 'scriptText', 'arg': 'DONE', 'msg': ''},
		]
		executor.execute(seq)
		joined = ''.join(output)
		assert 'Condition met' in joined
		assert callCount[0] >= 4

	def test_greaterThanCondition(self):
		"""Non-debug mode: >= condition with numeric value from indication."""
		dbe = makeMockDbe()
		dbe.getControlState.return_value = [('TestModule/txtRpmR', 'RPM_R', '64')]
		config = makeTestConfig(debug=False)
		executor, output, _, _ = makeExecutor(config=config, dbe=dbe)
		seq = [
			{'time': 0, 'cmd': 'scriptCockpitState', 'control': 'TestModule/txtRpmR', 'condition': '>=', 'value': 63, 'duration': 0, 'msg': ''},
			{'time': 0, 'cmd': 'scriptText', 'arg': 'DONE', 'msg': ''},
		]
		executor.execute(seq)
		joined = ''.join(output)
		assert 'Condition met' in joined

	def test_dcs32bitFloatPrecision(self):
		"""Default resolution=5 fires when DCS returns the 32-bit float artifact (0.89999997... for 0.9)."""
		dbe = makeMockDbe()
		dbe.getControlState.return_value = [('TestModule/canopyPos', 'Canopy Position', '0.89999997615814')]
		config = makeTestConfig(debug=False)
		executor, output, _, _ = makeExecutor(config=config, dbe=dbe)
		seq = [
			{'time': 0, 'cmd': 'scriptCockpitState', 'control': 'TestModule/canopyPos', 'condition': '>=', 'value': 0.9, 'duration': 0, 'msg': ''},
			{'time': 0, 'cmd': 'scriptText', 'arg': 'DONE', 'msg': ''},
		]
		executor.execute(seq)
		joined = ''.join(output)
		assert 'Condition met' in joined

	def test_customResolutionCoarser(self):
		"""resolution=3 also absorbs the 32-bit float artifact."""
		dbe = makeMockDbe()
		dbe.getControlState.return_value = [('TestModule/canopyPos', 'Canopy Position', '0.89999997615814')]
		config = makeTestConfig(debug=False)
		executor, output, _, _ = makeExecutor(config=config, dbe=dbe)
		seq = [
			{'time': 0, 'cmd': 'scriptCockpitState', 'control': 'TestModule/canopyPos', 'condition': '>=', 'value': 0.9, 'duration': 0, 'resolution': 3, 'msg': ''},
			{'time': 0, 'cmd': 'scriptText', 'arg': 'DONE', 'msg': ''},
		]
		executor.execute(seq)
		joined = ''.join(output)
		assert 'Condition met' in joined

	def test_customResolutionFiner(self):
		"""resolution=10 preserves the 32-bit artifact; the condition only fires once the actual target value arrives."""
		dbe = makeMockDbe()
		callCount = [0]
		def mockGetControlState(control):
			callCount[0] += 1
			if callCount[0] <= 3:
				return [('TestModule/canopyPos', 'Canopy Position', '0.89999997615814')]
			return [('TestModule/canopyPos', 'Canopy Position', '0.9')]
		dbe.getControlState.side_effect = mockGetControlState
		config = makeTestConfig(debug=False)
		executor, output, _, _ = makeExecutor(config=config, dbe=dbe)
		seq = [
			{'time': 0, 'cmd': 'scriptCockpitState', 'control': 'TestModule/canopyPos', 'condition': '>=', 'value': 0.9, 'duration': 0, 'resolution': 10, 'msg': ''},
			{'time': 0, 'cmd': 'scriptText', 'arg': 'DONE', 'msg': ''},
		]
		executor.execute(seq)
		joined = ''.join(output)
		assert 'Condition met' in joined
		assert callCount[0] >= 4  # The artifact value should not have triggered early.

	def test_conditionNotMetThenMet(self):
		"""Non-debug mode: condition not met initially, then met after a few polls."""
		dbe = makeMockDbe()
		callCount = [0]
		def mockGetControlState(control):
			callCount[0] += 1
			if callCount[0] <= 5:
				return [('TestModule/txtRpmR', 'RPM_R', '10')]
			return [('TestModule/txtRpmR', 'RPM_R', '20')]
		dbe.getControlState.side_effect = mockGetControlState
		config = makeTestConfig(debug=False)
		executor, output, _, _ = makeExecutor(config=config, dbe=dbe)
		seq = [
			{'time': 0, 'cmd': 'scriptCockpitState', 'control': 'TestModule/txtRpmR', 'condition': '>=', 'value': 15, 'duration': 0, 'msg': ''},
			{'time': 0, 'cmd': 'scriptText', 'arg': 'DONE', 'msg': ''},
		]
		executor.execute(seq)
		joined = ''.join(output)
		assert 'Condition met' in joined
		assert callCount[0] >= 6

	def test_strConditionMet(self):
		"""Non-debug mode: string equality condition."""
		dbe = makeMockDbe()
		dbe.getControlState.return_value = [('TestModule/ufcScratchpad', 'Scratchpad', 'HELLO')]
		config = makeTestConfig(debug=False)
		executor, output, _, _ = makeExecutor(config=config, dbe=dbe)
		seq = [
			{'time': 0, 'cmd': 'scriptCockpitState', 'control': 'TestModule/ufcScratchpad', 'condition': '=', 'value': 'HELLO', 'duration': 0, 'msg': ''},
			{'time': 0, 'cmd': 'scriptText', 'arg': 'DONE', 'msg': ''},
		]
		executor.execute(seq)
		joined = ''.join(output)
		assert 'Condition met' in joined


# ---------------------------------------------------------------------------
# Timer tests
# ---------------------------------------------------------------------------

class TestTimers:
	def test_timerStartAndEnd(self):
		"""Start a short timer, wait for it to end, then continue."""
		executor, output, _, _ = makeExecutor()
		seq = [
			{'time': 0, 'cmd': 'scriptTimerStart', 'name': 'test', 'duration': 0.03, 'arg': '', 'msg': ''},
			{'time': 0, 'cmd': 'scriptTimerEnd', 'name': 'test', 'arg': '', 'msg': ''},
			{'time': 0, 'cmd': 'scriptText', 'arg': 'AFTER_TIMER', 'msg': ''},
		]
		executor.execute(seq)
		joined = ''.join(output)
		assert 'Start timer' in joined
		assert 'Timer done' in joined
		assert 'AFTER_TIMER' in joined

	def test_debugModeTimesWithThePcClock(self):
		executor, _, _, _ = makeExecutor()
		executor.execute([
			{'time': 0, 'cmd': 'scriptTimerStart', 'name': 'test', 'duration': 0.03},
			{'time': 0, 'cmd': 'scriptTimerEnd', 'name': 'test'},
		])
		executor.dbe.queryTelemetry.assert_not_called()

	def test_timerFollowsAcceleratedGameTime(self):
		"""At 10x, a 3 s alignment timer is done after about 0.3 s, because the alignment is too."""
		started = time.time()
		def queryTelemetry(functionName, timeout=1.0):
			return {'LoGetModelTime': 100 + 10 * (time.time() - started), 'LoGetModelTimeAcceleration': 10, 'LoGetMissionStartTime': 14 * 3600}.get(functionName)
		dbe = makeMockDbe()
		dbe.queryTelemetry.side_effect = queryTelemetry
		executor, output, _, _ = makeExecutor(config=makeTestConfig(debug=False), dbe=dbe)
		with patch.object(DCSSeqExecute, 'getDcsWindow', return_value=MagicMock()):
			executor.execute([
				{'time': 0, 'cmd': 'scriptTimerStart', 'name': 'align', 'duration': 3},
				{'time': 0, 'cmd': 'scriptTimerEnd', 'name': 'align'},
			])
		assert time.time() - started < 1.5
		joined = ''.join(output)
		assert 'Timer done' in joined
		assert 'at 10x' in joined
		assert 'ends at 14:01:43 in-game' in joined # Mission start 14:00:00 + 100 s model time + 3 s.


# Pure timer clock: game (mission) time when DCS answers, so time acceleration and DCS pauses count.
def test_scriptTimerUsesGameTime():
	timer = newScriptTimer(60, gameTime=100.0, wallTime=1000.0)
	assert scriptTimerElapsed(timer, gameTime=140.0, wallTime=1010.0) == 40.0 # 4x for 10 s

def test_scriptTimerStopsWhileDcsIsPaused():
	timer = newScriptTimer(60, gameTime=100.0, wallTime=1000.0)
	assert scriptTimerElapsed(timer, gameTime=110.0, wallTime=1010.0) == 10.0
	assert scriptTimerElapsed(timer, gameTime=110.0, wallTime=1040.0) == 10.0

def test_scriptTimerCarriesOnWithThePcClockWhenGameTimeIsMissing():
	timer = newScriptTimer(60, gameTime=100.0, wallTime=1000.0)
	assert scriptTimerElapsed(timer, gameTime=140.0, wallTime=1010.0) == 40.0
	assert scriptTimerElapsed(timer, gameTime=None, wallTime=1012.0) == 42.0
	assert scriptTimerElapsed(timer, gameTime=150.0, wallTime=1013.0) == 50.0

def test_scriptTimerUsesThePcClockIfGameTimeWasMissingAtTheStart():
	timer = newScriptTimer(60, gameTime=None, wallTime=1000.0)
	assert scriptTimerElapsed(timer, gameTime=500.0, wallTime=1010.0) == 10.0


def test_formatClockWrapsPastMidnight():
	assert formatClock(14 * 3600 + 1 * 60 + 43) == '14:01:43'
	assert formatClock(24 * 3600 + 5 * 60) == '00:05:00'
	assert formatClock(59.6) == '00:01:00'


# ---------------------------------------------------------------------------
# Pause callback test
# ---------------------------------------------------------------------------

class TestPauseCallback:
	def test_pauseCallbackInvoked(self):
		"""The scriptPause command calls the pauseCallback."""
		pauseCallback = MagicMock()
		executor, output, _, _ = makeExecutor(pauseCallback=pauseCallback)
		seq = [
			{'time': 0, 'cmd': 'scriptPause', 'arg': '', 'msg': ''},
			{'time': 0, 'cmd': 'scriptText', 'arg': 'AFTER_PAUSE', 'msg': ''},
		]
		executor.execute(seq)
		pauseCallback.assert_called_once()
		joined = ''.join(output)
		assert 'AFTER_PAUSE' in joined


# ---------------------------------------------------------------------------
# Stop flag tests
# ---------------------------------------------------------------------------

class TestStopFlag:
	def test_stopMidExecution(self):
		"""Setting the stop flag should halt execution before all commands run."""
		stopFlag = threading.Event()
		output = []

		def captureAndStop(text, flush=False):
			output.append(str(text))
			if 'MARKER_ONE' in str(text):
				stopFlag.set()

		dbe = makeMockDbe()
		resumeEvent = threading.Event()
		resumeEvent.set()

		executor = DCSSeqExecute(
			root=MagicMock(),
			config=makeTestConfig(),
			dbe=dbe,
			scriptData={'moduleName': 'TestModule'},
			vars={},
			updateOutput=captureAndStop,
			stopFlag=stopFlag,
			logFunc=MagicMock(),
			ttsManager=MagicMock(),
			resumeEvent=resumeEvent,
		)

		seq = [
			{'time': 0, 'cmd': 'scriptText', 'arg': 'MARKER_ONE', 'msg': ''},
			{'time': 0, 'cmd': 'scriptText', 'arg': 'MARKER_TWO', 'msg': ''},
		]
		executor.execute(seq)
		joined = ''.join(output)
		assert 'MARKER_ONE' in joined
		assert 'MARKER_TWO' not in joined


# ---------------------------------------------------------------------------
# Validation tests
# ---------------------------------------------------------------------------

class TestValidation:
	def test_validSequencePasses(self):
		executor, output, _, _ = makeExecutor()
		seq = [
			{'time': 0, 'cmd': 'apuSw', 'arg': '1', 'msg': ''},
		]
		executor.execute(seq)
		joined = ''.join(output)
		assert 'Script validated' in joined

	def test_unknownControlWarns(self):
		"""A command with no matching description triggers a warning."""
		executor, output, _, _ = makeExecutor()
		seq = [
			{'time': 0, 'cmd': 'NONEXISTENT_CTRL', 'arg': '1', 'msg': ''},
		]
		executor.execute(seq)
		joined = ''.join(output)
		assert 'no description' in joined.lower() or 'not found' in joined.lower()

	def test_keyboardAfterCockpitDoneWarns(self):
		executor, output, _, _ = makeExecutor()
		seq = [
			{'time': 0, 'cmd': 'scriptCockpitDone'},
			{'time': 0, 'cmd': 'scriptKeyboard', 'arg': 'a', 'msg': ''},
		]
		executor.execute(seq)
		assert 'scriptKeyboard at row 1 needs the cockpit but comes after scriptCockpitDone at row 0' in ''.join(output)

	def test_cockpitDoneAloneIsValid(self):
		executor, output, _, _ = makeExecutor()
		seq = [
			{'time': 0, 'cmd': 'scriptKeyboard', 'arg': 'a', 'msg': ''},
			{'time': 0, 'cmd': 'scriptCockpitDone'},
		]
		executor.execute(seq)
		assert 'Script validated' in ''.join(output)

	def test_telemetryControlsValidate(self):
		executor, output, _, _ = makeExecutor()
		seq = [{'time': 0, 'cmd': 'scriptCockpitState', 'control': 'telemetry/LoGetEngineInfo.RPM.right', 'condition': '>=', 'value': 15}]
		executor.execute(seq)
		assert 'Script validated' in ''.join(output)

	def test_badTelemetryControlWarns(self):
		executor, output, _, _ = makeExecutor()
		seq = [{'time': 0, 'cmd': 'scriptCockpitState', 'control': 'telemetry/os.exit', 'value': 1}]
		executor.execute(seq)
		assert "Control 'telemetry/os.exit' not found" in ''.join(output)


class TestCockpitNeededSteps:
	"""Keyboard commands and ind. (display text) reads need the cockpit; the all-clear comes after the last of them."""

	def test_indicationWaitNeedsCockpitButArgWaitDoesNot(self):
		executor, output, _, _ = makeExecutor()
		seq = [
			{'time': 0, 'cmd': 'scriptCockpitState', 'control': 'TestModule/ind.3.AlignTime', 'value': '4.0'},
			{'time': 0, 'cmd': 'scriptText', 'arg': 'AFTER_ALIGN', 'msg': ''},
			{'time': 0, 'cmd': 'scriptCockpitState', 'control': 'TestModule/apuSw', 'value': 1},
			{'time': 0, 'cmd': 'scriptText', 'arg': 'END', 'msg': ''},
		]
		executor.execute(seq)
		joined = ''.join(output)
		assert joined.count('Stay in cockpit') == 1
		assert joined.index('Wait for cockpit state') < joined.index('OK to leave cockpit') < joined.index('AFTER_ALIGN')

	def test_argOnlyScriptNeverAsksToStay(self):
		executor, output, _, _ = makeExecutor()
		seq = [{'time': 0, 'cmd': 'scriptCockpitState', 'control': 'TestModule/apuSw', 'value': 1}]
		executor.execute(seq)
		joined = ''.join(output)
		assert 'Stay in cockpit' not in joined
		assert 'OK to leave cockpit' not in joined

	def test_keyboardInsideLoopHoldsAllClearUntilLoopEnds(self):
		"""The loop body can run again, so its keyboard command isn't the last one until the loop is finished."""
		readCount = [0]
		def getControlState(control):
			readCount[0] += 1
			return [(control, 'APU', 1 if readCount[0] >= 2 else 0)]
		dbe = makeMockDbe()
		dbe.getControlState.side_effect = getControlState
		executor, output, _, _ = makeExecutor(config=makeTestConfig(debug=False), dbe=dbe)
		executor.getDcsWindow = lambda: MagicMock()
		seq = [
			{'time': 0, 'cmd': 'scriptLoopUntilStart'},
			{'time': 0, 'cmd': 'scriptKeyboard', 'arg': 'a', 'msg': ''},
			{'time': 0, 'cmd': 'scriptLoopUntilEnd', 'control': 'TestModule/apuSw', 'condition': '=', 'value': 1},
			{'time': 0, 'cmd': 'scriptText', 'arg': 'AFTER_LOOP', 'msg': ''},
		]
		with patch('engine.DCSSeqExecute.pydirectinput') as directInput:
			directInput.press.return_value = True
			executor.execute(seq)
		joined = ''.join(output)
		assert joined.count('OK to leave cockpit') == 1
		assert joined.rindex('Keyboard command') < joined.index('OK to leave cockpit') < joined.index('AFTER_LOOP')

	def test_liveIndicationReadAfterAllClearPausesAndAsksPlayerToReturn(self):
		pauseCallback = MagicMock()
		executor, output, _, _ = makeExecutor(pauseCallback=pauseCallback)
		helper = makeHelper()

		def liveScript():
			pushSeqCmd = helper.makePushSeqCmd([])
			pushSeqCmd(0, 'scriptKeyboard', 'a')
			pushSeqCmd(0, 'scriptCockpitDone')
			yield
			rpmControl = 'ind.5.txt_RPM_R'
			helper.read(rpmControl, default=0)
			pushSeqCmd(0, 'scriptText', 'AFTER_READ')

		executor.execute(liveScript(), helper)
		joined = ''.join(output)
		pauseCallback.assert_called_once()
		assert joined.index('return to the cockpit') < joined.index('AFTER_READ')

	def test_indicationWaitAfterAllClearPausesAndAsksPlayerToReturn(self):
		pauseCallback = MagicMock()
		executor, output, _, _ = makeExecutor(pauseCallback=pauseCallback)
		seq = [
			{'time': 0, 'cmd': 'scriptKeyboard', 'arg': 'a', 'msg': ''},
			{'time': 0, 'cmd': 'scriptCockpitDone'},
			{'time': 0, 'cmd': 'scriptCockpitState', 'control': 'TestModule/ind.3.AlignTime', 'value': '4.0'},
			{'time': 0, 'cmd': 'scriptText', 'arg': 'AFTER_WAIT', 'msg': ''},
		]
		executor.execute(seq)
		joined = ''.join(output)
		pauseCallback.assert_called_once()
		assert joined.index('return to the cockpit') < joined.index('AFTER_WAIT')


# ---------------------------------------------------------------------------
# Comms menu warning tests
# ---------------------------------------------------------------------------

class TestCommsMenuSteps:
	"""The player's own comms menu use would throw off menu commands, so they're told not to use it until the last one has run."""

	def test_menuOnlyScriptWarnsThenClearsAfterLastMenuCommand(self):
		executor, output, _, _ = makeExecutor()
		seq = [
			{'time': 0, 'cmd': 'scriptSimCommand', 'arg': 'ICommandMenuItem12', 'msg': ''},
			{'time': 0, 'cmd': 'scriptSimCommand', 'arg': 972, 'msg': ''}, # ICommandMenuItem7
			{'time': 0, 'cmd': 'scriptText', 'arg': 'AFTER_MENU', 'msg': ''},
		]
		executor.execute(seq)
		joined = ''.join(output)
		assert 'Stay in cockpit' not in joined
		assert joined.count("Don't use comms menu until told") == 1
		assert joined.index("Don't use comms menu") < joined.index('ICommandMenuItem12 (977)') < joined.index('Sim command:\t972') < joined.index('OK to use comms menu') < joined.index('AFTER_MENU')

	def test_keyboardAndMenuGiveOneCombinedWarningAndSeparateAllClears(self):
		executor, output, ttsManager, _ = makeExecutor()
		seq = [
			{'time': 0, 'cmd': 'scriptSimCommand', 'arg': 'ICommandMenuItem12', 'msg': ''},
			{'time': 0, 'cmd': 'scriptText', 'arg': 'AFTER_MENU', 'msg': ''},
			{'time': 0, 'cmd': 'scriptKeyboard', 'arg': 'a', 'msg': ''},
			{'time': 0, 'cmd': 'scriptText', 'arg': 'AFTER_KEYBOARD', 'msg': ''},
		]
		executor.execute(seq)
		joined = ''.join(output)
		spoken = [c[0][0] for c in ttsManager.speak.call_args_list]
		assert spoken[0] == "Stay in cockpit and don't use comms menu until told it's OK."
		assert not any(s in ("Stay in cockpit until told it's OK to leave.", "Don't use comms menu until told it's OK.") for s in spoken)
		assert joined.index('OK to use comms menu') < joined.index('AFTER_MENU') < joined.index('OK to leave cockpit') < joined.index('AFTER_KEYBOARD')

	def test_otherSimCommandsDoNotWarn(self):
		executor, output, _, _ = makeExecutor()
		seq = [{'time': 0, 'cmd': 'scriptSimCommand', 'arg': 'iCommandLeftEngineStart', 'msg': ''}]
		executor.execute(seq)
		assert 'comms menu' not in ''.join(output)

	def test_liveScriptHoldsAllClearUntilLaterMenuCommand(self):
		executor, output, _, _ = makeExecutor()
		helper = makeHelper()

		def liveScript():
			pushSeqCmd = helper.makePushSeqCmd([])
			pushSeqCmd(0, 'scriptSimCommand', 'ICommandMenuItem12')
			yield
			pushSeqCmd(0, 'scriptText', 'MIDDLE')
			yield
			pushSeqCmd(0, 'scriptSimCommand', 'ICommandMenuItem8')
			pushSeqCmd(0, 'scriptText', 'END')

		executor.execute(liveScript(), helper)
		joined = ''.join(output)
		assert joined.count("Don't use comms menu until told") == 1
		assert joined.count('OK to use comms menu') == 1
		assert joined.index('MIDDLE') < joined.index('ICommandMenuItem8 (973)') < joined.index('OK to use comms menu') < joined.index('END')


# ---------------------------------------------------------------------------
# Non-debug execution tests
# ---------------------------------------------------------------------------

class TestNonDebugBiosSend:
	def test_biosCommandSentViaDbe(self):
		"""In non-debug mode, DCS commands are sent via dbe.sendControl()."""
		config = makeTestConfig(debug=False)
		executor, output, _, _ = makeExecutor(config=config)

		executor.getDcsWindow = lambda: MagicMock()

		seq = [
			{'time': 0, 'cmd': 'apuSw', 'arg': '1', 'msg': ''},
		]
		executor.execute(seq)

		executor.dbe.sendControl.assert_called_once_with('apuSw', '1', 'TestModule')

	def test_multipleCommandsSentInOrder(self):
		"""Multiple DCS commands are sent via dbe.sendControl() in sequence."""
		config = makeTestConfig(debug=False)
		executor, output, _, _ = makeExecutor(config=config)

		executor.getDcsWindow = lambda: MagicMock()

		seq = [
			{'time': 0, 'cmd': 'apuSw', 'arg': '1', 'msg': ''},
			{'time': 0, 'cmd': 'gearHandle', 'arg': '0', 'msg': ''},
		]
		executor.execute(seq)

		assert executor.dbe.sendControl.call_count == 2
		calls = executor.dbe.sendControl.call_args_list
		assert calls[0][0] == ('apuSw', '1', 'TestModule')
		assert calls[1][0] == ('gearHandle', '0', 'TestModule')


# ---------------------------------------------------------------------------
# scriptSimCommand (LoSetCommand) tests
# ---------------------------------------------------------------------------

class TestSimCommand:
	def test_simCommandSentViaDbe(self):
		executor, output, _, _ = makeExecutor(config=makeTestConfig(debug=False))
		executor.getDcsWindow = lambda: MagicMock()
		seq = [
			{'time': 0, 'cmd': 'scriptSimCommand', 'arg': 312, 'msg': 'Right throttle IDLE'},
			{'time': 0, 'cmd': 'scriptSimCommand', 'arg': 3, 'value': 0.25, 'msg': ''},
		]
		executor.execute(seq)
		assert executor.dbe.sendSimCommand.call_args_list[0][0] == (312, None)
		assert executor.dbe.sendSimCommand.call_args_list[1][0] == (3, 0.25)
		executor.dbe.sendControl.assert_not_called()

	def test_simCommandNotSentInDebug(self):
		executor, output, _, _ = makeExecutor()
		seq = [{'time': 0, 'cmd': 'scriptSimCommand', 'arg': 312, 'msg': ''}]
		executor.execute(seq)
		executor.dbe.sendSimCommand.assert_not_called()
		assert 'Sim command:\t312' in ''.join(output)

	def test_simCommandIsNotAKeyboardCommand(self):
		executor, output, _, _ = makeExecutor()
		seq = [{'time': 0, 'cmd': 'scriptSimCommand', 'arg': 312, 'msg': ''}]
		executor.execute(seq)
		joined = ''.join(output)
		assert 'Stay in cockpit' not in joined
		assert 'Script validated' in joined

	def test_simCommandNameSentAsItsNumber(self):
		executor, output, _, _ = makeExecutor(config=makeTestConfig(debug=False))
		executor.getDcsWindow = lambda: MagicMock()
		seq = [{'time': 0, 'cmd': 'scriptSimCommand', 'arg': 'iCommandPlaneCollectiveDecrease', 'msg': ''}]
		executor.execute(seq)
		assert executor.dbe.sendSimCommand.call_args_list[0][0] == (632, None)
		assert 'Sim command:\tiCommandPlaneCollectiveDecrease (632)' in ''.join(output)

	def test_unknownSimCommandNameFailsValidation(self):
		executor, output, _, _ = makeExecutor(config=makeTestConfig(debug=False))
		seq = [{'time': 0, 'cmd': 'scriptSimCommand', 'arg': 'iCommandNoSuchThing', 'msg': ''}]
		executor.execute(seq)
		assert "scriptSimCommand 'iCommandNoSuchThing' is not a known iCommand name" in ''.join(output)
		executor.dbe.sendSimCommand.assert_not_called()

	def test_nonIntegerSimCommandFailsValidation(self):
		executor, output, _, _ = makeExecutor()
		seq = [{'time': 0, 'cmd': 'scriptSimCommand', 'arg': 3.5, 'msg': ''}]
		executor.execute(seq)
		assert 'scriptSimCommand needs an iCommand number or name, got 3.5' in ''.join(output)

	def test_heldSimCommandSentAsHoldWithStop(self):
		executor, output, _, _ = makeExecutor(config=makeTestConfig(debug=False))
		executor.getDcsWindow = lambda: MagicMock()
		seq = [{'time': 0, 'cmd': 'scriptSimCommand', 'arg': 'iCommandPlaneCollectiveDecrease', 'hold': 2, 'stop': 'iCommandPlaneCollectiveStop', 'msg': ''}]
		executor.execute(seq)
		assert executor.dbe.sendSimCommandHold.call_args_list[0][0] == (632, 2, 839)
		executor.dbe.sendSimCommand.assert_not_called()
		assert 'Script validated' in ''.join(output)

	def test_heldSimCommandWithoutStop(self):
		executor, output, _, _ = makeExecutor(config=makeTestConfig(debug=False))
		executor.getDcsWindow = lambda: MagicMock()
		seq = [{'time': 0, 'cmd': 'scriptSimCommand', 'arg': 632, 'hold': 1.5, 'msg': ''}]
		executor.execute(seq)
		assert executor.dbe.sendSimCommandHold.call_args_list[0][0] == (632, 1.5, None)

	def test_heldSimCommandNotSentInDebug(self):
		executor, output, _, _ = makeExecutor()
		seq = [{'time': 0, 'cmd': 'scriptSimCommand', 'arg': 632, 'hold': 2, 'stop': 839, 'msg': ''}]
		executor.execute(seq)
		executor.dbe.sendSimCommandHold.assert_not_called()
		assert 'Sim command:\t632 held 2s, then 839' in ''.join(output)

	@pytest.mark.parametrize('extra, expected', [
		({'hold': 0}, 'scriptSimCommand hold must be a positive number of seconds, got 0'),
		({'hold': 'long'}, "scriptSimCommand hold must be a positive number of seconds, got 'long'"),
		({'hold': False}, 'scriptSimCommand hold must be a positive number of seconds, got False'),
		({'hold': 2, 'stop': 'iCommandNoSuchStop'}, "scriptSimCommand stop 'iCommandNoSuchStop' is not a known iCommand"),
		({'stop': 839}, 'scriptSimCommand stop needs hold'),
		({'release': True, 'hold': 2}, "scriptSimCommand release can't be combined with hold, stop or value"),
		({'release': True, 'value': 0.5}, "scriptSimCommand release can't be combined with hold, stop or value"),
		({'release': 'yes'}, "scriptSimCommand release must be True, got 'yes'"),
	])
	def test_badHoldOptionsFailValidation(self, extra, expected):
		executor, output, _, _ = makeExecutor(config=makeTestConfig(debug=False))
		seq = [{'time': 0, 'cmd': 'scriptSimCommand', 'arg': 632, 'msg': '', **extra}]
		executor.execute(seq)
		assert expected in ''.join(output)
		executor.dbe.sendSimCommandHold.assert_not_called()
		executor.dbe.releaseSimCommandHold.assert_not_called()


# ---------------------------------------------------------------------------
# Held values: hold an axis at a value, for some seconds or until a release step.  Whatever the script still holds is released when it ends.
# ---------------------------------------------------------------------------

def makeLiveExecutor(stopFlag=None):
	executor, output, _, stopFlag = makeExecutor(config=makeTestConfig(debug=False), stopFlag=stopFlag)
	executor.getDcsWindow = lambda: MagicMock()
	return executor, output, stopFlag


def holdCalls(dbe):
	"""The holds and releases sent to DCS, in order."""
	return [(name, call.args, call.kwargs) for name, call in ((c[0], c) for c in dbe.method_calls) if name in ('sendSimCommandHold', 'releaseSimCommandHold')]


class TestHeldValues:
	def test_holdWithValueForSeconds(self):
		executor, output, _ = makeLiveExecutor()
		executor.execute([{'time': 0, 'cmd': 'scriptSimCommand', 'arg': 'iCommandPlaneThrustCommon', 'value': 0.7, 'hold': 30, 'msg': ''}])
		assert holdCalls(executor.dbe)[0] == ('sendSimCommandHold', (2004, 30, None), {'value': 0.7})
		assert 'Sim command:\tiCommandPlaneThrustCommon (2004) 0.7 held 30s' in ''.join(output)
		assert 'Script validated' in ''.join(output)

	def test_holdUntilReleasedThenRelease(self):
		executor, output, _ = makeLiveExecutor()
		executor.execute([
			{'time': 0, 'cmd': 'scriptSimCommand', 'arg': 'iCommandPlaneThrustCommon', 'value': 0.7, 'hold': True, 'msg': 'Throttles to GND IDLE'},
			{'time': 0, 'cmd': 'scriptText', 'arg': 'ENGINES STARTING', 'msg': ''},
			{'time': 0, 'cmd': 'scriptSimCommand', 'arg': 'iCommandPlaneThrustCommon', 'release': True, 'msg': ''},
			{'time': 0, 'cmd': 'scriptText', 'arg': 'AFTER', 'msg': ''},
		])
		assert holdCalls(executor.dbe) == [
			('sendSimCommandHold', (2004, None, None), {'value': 0.7}),
			('releaseSimCommandHold', (2004,), {}), # Released once, by its step, not again at the end.
		]
		joined = ''.join(output)
		assert 'iCommandPlaneThrustCommon (2004) 0.7 held until released' in joined
		assert 'iCommandPlaneThrustCommon (2004) released' in joined

	def test_holdStillRunningIsReleasedWhenTheScriptEnds(self):
		executor, output, _ = makeLiveExecutor()
		executor.execute([
			{'time': 0, 'cmd': 'scriptSimCommand', 'arg': 2004, 'value': 0.7, 'hold': True, 'msg': ''},
			{'time': 0, 'cmd': 'scriptSimCommand', 'arg': 632, 'hold': 20, 'stop': 839, 'msg': ''},
		])
		releases = [args for name, args, _ in holdCalls(executor.dbe) if name == 'releaseSimCommandHold']
		assert sorted(releases) == [(632,), (2004,)]
		joined = ''.join(output)
		assert joined.index('Released held simulator commands') < joined.index('Script complete')

	def test_holdIsReleasedWhenTheScriptIsStopped(self):
		stopFlag = threading.Event()
		executor, output, _ = makeLiveExecutor(stopFlag=stopFlag)
		executor.updateOutput = lambda text, flush=False: (output.append(str(text)), 'MARKER' in str(text) and stopFlag.set())
		executor.execute([
			{'time': 0, 'cmd': 'scriptSimCommand', 'arg': 2004, 'value': 0.7, 'hold': True, 'msg': ''},
			{'time': 0, 'cmd': 'scriptText', 'arg': 'MARKER', 'msg': ''},
			{'time': 0, 'cmd': 'scriptText', 'arg': 'NEVER', 'msg': ''},
		])
		assert 'NEVER' not in ''.join(output)
		executor.dbe.releaseSimCommandHold.assert_called_once_with(2004)

	def test_holdIsReleasedWhenAStepRaises(self):
		executor, output, _ = makeLiveExecutor()
		executor.dbe.controlExists.side_effect = lambda control: control != 'TestModule/missing'
		with pytest.raises(ValueError):
			executor.execute([
				{'time': 0, 'cmd': 'scriptSimCommand', 'arg': 2004, 'value': 0.7, 'hold': True, 'msg': ''},
				{'time': 0, 'cmd': 'scriptCockpitState', 'control': 'TestModule/missing', 'value': 1, 'msg': ''},
			])
		executor.dbe.releaseSimCommandHold.assert_called_once_with(2004)

	def test_debugModeSendsNothing(self):
		executor, output, _, _ = makeExecutor()
		executor.execute([
			{'time': 0, 'cmd': 'scriptSimCommand', 'arg': 2004, 'value': 0.7, 'hold': True, 'msg': ''},
			{'time': 0, 'cmd': 'scriptSimCommand', 'arg': 2004, 'release': True, 'msg': ''},
		])
		assert holdCalls(executor.dbe) == []
		assert '2004 0.7 held until released' in ''.join(output)

	def test_blockedServerDoesNotPromptForARelease(self):
		executor, output, _, pauseCallback = makeTelemetryExecutor({'LoGetSelfData': {'Name': 'C-130J-30'}})
		executor.execute([
			{'time': 0, 'cmd': 'scriptSimCommand', 'arg': 2004, 'value': 0.7, 'hold': True, 'msg': 'Throttles to GND IDLE'},
			{'time': 0, 'cmd': 'scriptSimCommand', 'arg': 2004, 'release': True, 'msg': ''},
		])
		joined = ''.join(output)
		assert joined.count('Do it yourself') == 1
		assert 'Do it yourself: Throttles to GND IDLE' in joined


# ---------------------------------------------------------------------------
# scriptLoopUntilStart / scriptLoopUntilEnd tests
# ---------------------------------------------------------------------------

class TestLoopUntil:
	def test_preTestSkipsBodyWhenAlreadyMet(self):
		"""Start marker with a condition already satisfied: body is skipped."""
		dbe = makeMockDbe()
		dbe.getControlState.return_value = [('TestModule/apuSw', 'APU', 1)]
		config = makeTestConfig(debug=False)
		executor, output, _, _ = makeExecutor(config=config, dbe=dbe)
		executor.getDcsWindow = lambda: MagicMock()
		seq = [
			{'time': 0, 'cmd': 'scriptLoopUntilStart', 'control': 'TestModule/apuSw', 'condition': '=', 'value': 1},
			{'time': 0, 'cmd': 'apuSw', 'arg': '1', 'msg': 'BODY'},
			{'time': 0, 'cmd': 'scriptLoopUntilEnd'},
			{'time': 0, 'cmd': 'scriptText', 'arg': 'AFTER_LOOP', 'msg': ''},
		]
		executor.execute(seq)
		# Body command should NOT have been sent (skipped by pre-test).
		executor.dbe.sendControl.assert_not_called()
		assert 'AFTER_LOOP' in ''.join(output)

	def test_unansweredPreTestReadRunsBody(self):
		"""Start marker whose read DCS doesn't answer: the condition can't be known met, so the body runs."""
		readings = iter([[], [('TestModule/apuSw', 'APU', 1)]])
		dbe = makeMockDbe()
		dbe.getControlState.side_effect = lambda control: next(readings)
		config = makeTestConfig(debug=False)
		executor, output, _, _ = makeExecutor(config=config, dbe=dbe)
		executor.getDcsWindow = lambda: MagicMock()
		seq = [
			{'time': 0, 'cmd': 'scriptLoopUntilStart', 'control': 'TestModule/apuSw', 'condition': '=', 'value': 1},
			{'time': 0, 'cmd': 'apuSw', 'arg': '1', 'msg': ''},
			{'time': 0, 'cmd': 'scriptLoopUntilEnd'},
			{'time': 0, 'cmd': 'scriptText', 'arg': 'AFTER_LOOP', 'msg': ''},
		]
		executor.execute(seq)
		executor.dbe.sendControl.assert_called_once_with('apuSw', '1', 'TestModule')
		assert 'AFTER_LOOP' in ''.join(output)

	def test_unansweredEndReadRepeatsBody(self):
		"""End marker whose read DCS doesn't answer counts as not met, so the body runs again."""
		readings = iter([[], [('TestModule/apuSw', 'APU', 1)]])
		dbe = makeMockDbe()
		dbe.getControlState.side_effect = lambda control: next(readings)
		config = makeTestConfig(debug=False)
		executor, output, _, _ = makeExecutor(config=config, dbe=dbe)
		executor.getDcsWindow = lambda: MagicMock()
		seq = [
			{'time': 0, 'cmd': 'scriptLoopUntilStart'},
			{'time': 0, 'cmd': 'apuSw', 'arg': '1', 'msg': ''},
			{'time': 0, 'cmd': 'scriptLoopUntilEnd', 'control': 'TestModule/apuSw', 'condition': '=', 'value': 1},
			{'time': 0, 'cmd': 'scriptText', 'arg': 'AFTER_LOOP', 'msg': ''},
		]
		executor.execute(seq)
		assert executor.dbe.sendControl.call_count == 2
		assert 'AFTER_LOOP' in ''.join(output)

	def test_postTestExecutesBodyAtLeastOnce(self):
		"""End marker with condition (do-while): body always runs at least once."""
		callCount = [0]
		def mockGetControlState(control):
			callCount[0] += 1
			# Already-met from the start, but End-only means no pre-test.
			return [('TestModule/apuSw', 'APU', 1)]
		dbe = makeMockDbe()
		dbe.getControlState.side_effect = mockGetControlState
		config = makeTestConfig(debug=False)
		executor, output, _, _ = makeExecutor(config=config, dbe=dbe)
		executor.getDcsWindow = lambda: MagicMock()
		seq = [
			{'time': 0, 'cmd': 'scriptLoopUntilStart'},
			{'time': 0, 'cmd': 'apuSw', 'arg': '1', 'msg': ''},
			{'time': 0, 'cmd': 'scriptLoopUntilEnd', 'control': 'TestModule/apuSw', 'condition': '=', 'value': 1},
			{'time': 0, 'cmd': 'scriptText', 'arg': 'AFTER_LOOP', 'msg': ''},
		]
		executor.execute(seq)
		# Body sent exactly once (loop exits at first End check).
		executor.dbe.sendControl.assert_called_once_with('apuSw', '1', 'TestModule')
		assert 'AFTER_LOOP' in ''.join(output)

	def test_multipleIterationsUntilConditionMet(self):
		"""Loop iterates until the polled value flips to the target."""
		callCount = [0]
		def mockGetControlState(control):
			callCount[0] += 1
			# First two End checks return 0, third returns 1.
			return [('TestModule/apuSw', 'APU', 1 if callCount[0] >= 3 else 0)]
		dbe = makeMockDbe()
		dbe.getControlState.side_effect = mockGetControlState
		config = makeTestConfig(debug=False)
		executor, output, _, _ = makeExecutor(config=config, dbe=dbe)
		executor.getDcsWindow = lambda: MagicMock()
		seq = [
			{'time': 0, 'cmd': 'scriptLoopUntilStart'},
			{'time': 0, 'cmd': 'apuSw', 'arg': '1', 'msg': ''},
			{'time': 0, 'cmd': 'scriptLoopUntilEnd', 'control': 'TestModule/apuSw', 'condition': '=', 'value': 1},
			{'time': 0, 'cmd': 'scriptText', 'arg': 'AFTER_LOOP', 'msg': ''},
		]
		executor.execute(seq)
		# Body should have been sent multiple times.
		assert executor.dbe.sendControl.call_count >= 2
		assert 'AFTER_LOOP' in ''.join(output)

	def test_maxIterationsExceeded(self):
		"""Loop bails out when maxIterations is reached even if condition never met."""
		dbe = makeMockDbe()
		# Always returns 0 — condition (= 1) never met.
		dbe.getControlState.return_value = [('TestModule/apuSw', 'APU', 0)]
		config = makeTestConfig(debug=False)
		executor, output, _, _ = makeExecutor(config=config, dbe=dbe)
		executor.getDcsWindow = lambda: MagicMock()
		seq = [
			{'time': 0, 'cmd': 'scriptLoopUntilStart', 'maxIterations': 3},
			{'time': 0, 'cmd': 'apuSw', 'arg': '1', 'msg': ''},
			{'time': 0, 'cmd': 'scriptLoopUntilEnd', 'control': 'TestModule/apuSw', 'condition': '=', 'value': 1},
			{'time': 0, 'cmd': 'scriptText', 'arg': 'AFTER_LOOP', 'msg': ''},
		]
		executor.execute(seq)
		joined = ''.join(output)
		assert 'max iterations' in joined.lower()
		assert 'AFTER_LOOP' in joined
		# Body sent exactly maxIterations times.
		assert executor.dbe.sendControl.call_count == 3

	def test_timeoutExceeded(self):
		"""Loop bails out when timeout is reached."""
		dbe = makeMockDbe()
		dbe.getControlState.return_value = [('TestModule/apuSw', 'APU', 0)]
		config = makeTestConfig(debug=False)
		executor, output, _, _ = makeExecutor(config=config, dbe=dbe)
		executor.getDcsWindow = lambda: MagicMock()
		seq = [
			{'time': 0, 'cmd': 'scriptLoopUntilStart', 'timeout': 0.05},
			{'time': 0, 'cmd': 'apuSw', 'arg': '1', 'msg': ''},
			{'time': 0, 'cmd': 'scriptLoopUntilEnd', 'control': 'TestModule/apuSw', 'condition': '=', 'value': 1},
			{'time': 0, 'cmd': 'scriptText', 'arg': 'AFTER_LOOP', 'msg': ''},
		]
		executor.execute(seq)
		joined = ''.join(output)
		assert 'timeout' in joined.lower()
		assert 'AFTER_LOOP' in joined

	def test_endMarkerOverridesStartCondition(self):
		"""When both Start and End specify a control/condition, End wins on the recheck."""
		dbe = makeMockDbe()
		# Start condition (apuSw == 0) is NOT met (so body runs); End condition
		# (apuSw == 1) IS met immediately, so loop exits after one iteration.
		dbe.getControlState.return_value = [('TestModule/apuSw', 'APU', 1)]
		config = makeTestConfig(debug=False)
		executor, output, _, _ = makeExecutor(config=config, dbe=dbe)
		executor.getDcsWindow = lambda: MagicMock()
		seq = [
			{'time': 0, 'cmd': 'scriptLoopUntilStart', 'control': 'TestModule/apuSw', 'condition': '=', 'value': 0},
			{'time': 0, 'cmd': 'apuSw', 'arg': '1', 'msg': ''},
			{'time': 0, 'cmd': 'scriptLoopUntilEnd', 'control': 'TestModule/apuSw', 'condition': '=', 'value': 1},
			{'time': 0, 'cmd': 'scriptText', 'arg': 'AFTER_LOOP', 'msg': ''},
		]
		executor.execute(seq)
		# Body ran (Start condition not met), End condition met → exit.
		executor.dbe.sendControl.assert_called_once_with('apuSw', '1', 'TestModule')
		assert 'AFTER_LOOP' in ''.join(output)

	def test_nestedLoops(self):
		"""Nested scriptLoopUntil blocks each track their own state."""
		executor, output, _, _ = makeExecutor() # debug mode: each loop exits after 1 iter
		seq = [
			{'time': 0, 'cmd': 'scriptLoopUntilStart'},
			{'time': 0, 'cmd': 'scriptText', 'arg': 'OUTER', 'msg': ''},
			{'time': 0, 'cmd': 'scriptLoopUntilStart'},
			{'time': 0, 'cmd': 'scriptText', 'arg': 'INNER', 'msg': ''},
			{'time': 0, 'cmd': 'scriptLoopUntilEnd'},
			{'time': 0, 'cmd': 'scriptLoopUntilEnd'},
			{'time': 0, 'cmd': 'scriptText', 'arg': 'AFTER', 'msg': ''},
		]
		executor.execute(seq)
		joined = ''.join(output)
		# All three texts should appear in order.
		assert joined.index('OUTER') < joined.index('INNER') < joined.index('AFTER')

	def test_mismatchedMarkersAborts(self):
		"""scriptLoopUntilEnd without a matching Start aborts execution."""
		executor, output, _, _ = makeExecutor()
		seq = [
			{'time': 0, 'cmd': 'scriptText', 'arg': 'BEFORE', 'msg': ''},
			{'time': 0, 'cmd': 'scriptLoopUntilEnd'},
			{'time': 0, 'cmd': 'scriptText', 'arg': 'AFTER', 'msg': ''},
		]
		executor.execute(seq)
		joined = ''.join(output)
		# AFTER should not have been reached because the engine aborts.
		assert 'AFTER' not in joined or 'no matching' in joined.lower()

	def test_unmatchedStartAborts(self):
		"""scriptLoopUntilStart without a matching End aborts execution."""
		executor, output, _, _ = makeExecutor()
		seq = [
			{'time': 0, 'cmd': 'scriptLoopUntilStart'},
			{'time': 0, 'cmd': 'scriptText', 'arg': 'BODY', 'msg': ''},
		]
		executor.execute(seq)
		joined = ''.join(output)
		assert 'no matching' in joined.lower() or 'BODY' not in joined


# ---------------------------------------------------------------------------
# Live scripts (generator functions that yield between batches of commands)
# ---------------------------------------------------------------------------

def makeHelper():
	from engine.SequenceHelper import SequenceHelper
	return SequenceHelper({'dcsSavedGamesPath': '', 'udpUiWireLogEnabled': False, 'udpBiosWireLogEnabled': False})


class TestLiveScripts:
	def test_commandsBeforeYieldRunBeforeScriptResumes(self):
		executor, output, _, _ = makeExecutor()
		helper = makeHelper()
		outputAtResume = []

		def liveScript():
			pushSeqCmd = helper.makePushSeqCmd([])
			pushSeqCmd(0, 'scriptText', 'FIRST_BATCH')
			yield
			outputAtResume.append(''.join(output))
			pushSeqCmd(0, 'scriptText', 'SECOND_BATCH')

		executor.execute(liveScript(), helper)
		joined = ''.join(output)
		assert 'FIRST_BATCH' in outputAtResume[0]
		assert 'SECOND_BATCH' not in outputAtResume[0]
		assert joined.index('FIRST_BATCH') < joined.index('SECOND_BATCH') < joined.index('Script complete')

	def test_readAfterYieldSeesEffectOfEarlierCommands(self):
		cockpit = {'TestModule/apuSw': 0}
		dbe = makeMockDbe()
		dbe.sendControl.side_effect = lambda cmd, arg, moduleName: cockpit.update({f'{moduleName}/{cmd}': arg})
		dbe.getControlState.side_effect = lambda control: [(control, 'APU Switch', cockpit[control])]
		executor, output, _, _ = makeExecutor(config=makeTestConfig(debug=False), dbe=dbe)
		executor.getDcsWindow = lambda: MagicMock()
		helper = makeHelper()

		def liveScript():
			pushSeqCmd = helper.makePushSeqCmd([])
			pushSeqCmd(0, 'apuSw', 1)
			yield
			if helper.read('apuSw') == 1:
				pushSeqCmd(0, 'scriptText', 'APU_WAS_ON')
			else:
				pushSeqCmd(0, 'scriptText', 'APU_WAS_OFF')

		executor.execute(liveScript(), helper)
		joined = ''.join(output)
		assert 'APU_WAS_ON' in joined
		assert 'APU_WAS_OFF' not in joined

	def test_readOfUnknownControlRaises(self):
		dbe = makeMockDbe()
		dbe.controlExists.return_value = False
		executor, _, _, _ = makeExecutor(dbe=dbe)
		helper = makeHelper()

		def liveScript():
			helper.makePushSeqCmd([])
			yield
			helper.read('noSuchControl', default=0)

		with pytest.raises(ValueError, match='noSuchControl'):
			executor.execute(liveScript(), helper)

	def test_stopClosesScriptWithoutResumingIt(self):
		stopFlag = threading.Event()
		executor, output, _, _ = makeExecutor(stopFlag=stopFlag)
		helper = makeHelper()
		events = []

		def liveScript():
			pushSeqCmd = helper.makePushSeqCmd([])
			try:
				pushSeqCmd(0, 'scriptText', 'FIRST_BATCH')
				yield
				events.append('resumed')
			finally:
				events.append('closed')

		executor.updateOutput = lambda text, flush=False: (output.append(str(text)), stopFlag.set() if 'FIRST_BATCH' in str(text) else None)
		executor.execute(liveScript(), helper)
		assert events == ['closed']

	def test_errorInScriptPropagatesAfterEarlierBatchesRan(self):
		executor, output, _, _ = makeExecutor()
		helper = makeHelper()

		def liveScript():
			pushSeqCmd = helper.makePushSeqCmd([])
			pushSeqCmd(0, 'scriptText', 'FIRST_BATCH')
			yield
			raise ValueError('script bug')

		with pytest.raises(ValueError, match='script bug'):
			executor.execute(liveScript(), helper)
		assert 'FIRST_BATCH' in ''.join(output)

	def test_unknownControlInLaterBatchWarns(self):
		executor, output, _, _ = makeExecutor()
		helper = makeHelper()

		def liveScript():
			pushSeqCmd = helper.makePushSeqCmd([])
			pushSeqCmd(0, 'apuSw', 1)
			yield
			pushSeqCmd(0, 'NONEXISTENT_CTRL', 1)

		executor.execute(liveScript(), helper)
		assert "'NONEXISTENT_CTRL' not found" in ''.join(output)

	def test_keyboardWarningGivenOnceAndAllClearAfterLastKeyboardCommand(self):
		executor, output, ttsManager, _ = makeExecutor()
		helper = makeHelper()

		def liveScript():
			pushSeqCmd = helper.makePushSeqCmd([])
			pushSeqCmd(0, 'scriptKeyboard', 'a')
			yield
			pushSeqCmd(0, 'scriptText', 'BEFORE_B')
			pushSeqCmd(0, 'scriptKeyboard', 'b')
			pushSeqCmd(0, 'scriptText', 'AFTER_B')

		executor.execute(liveScript(), helper)
		joined = ''.join(output)
		assert joined.count('Stay in cockpit') == 1
		assert joined.count('OK to leave cockpit') == 1
		assert joined.index('BEFORE_B') < joined.index('OK to leave cockpit') < joined.index('AFTER_B')

	def test_finalBatchWithoutKeyboardAnnouncesAtItsStart(self):
		executor, output, _, _ = makeExecutor()
		helper = makeHelper()

		def liveScript():
			pushSeqCmd = helper.makePushSeqCmd([])
			keyboardCommand = 'scriptKeyboard' # Held in a variable, so the lookahead can't rule out more keyboard commands.
			pushSeqCmd(0, keyboardCommand, 'a')
			yield
			pushSeqCmd(0, 'scriptText', 'MIDDLE')
			yield
			pushSeqCmd(0, 'scriptText', 'LONG_TAIL')

		executor.execute(liveScript(), helper)
		joined = ''.join(output)
		assert joined.index('MIDDLE') < joined.index('OK to leave cockpit') < joined.index('LONG_TAIL')

	def test_lookaheadAnnouncesBeforeLaterBatches(self):
		executor, output, _, _ = makeExecutor()
		helper = makeHelper()

		def liveScript():
			pushSeqCmd = helper.makePushSeqCmd([])
			pushSeqCmd(0, 'scriptKeyboard', 'a')
			yield
			pushSeqCmd(0, 'scriptText', 'MIDDLE')
			yield
			pushSeqCmd(0, 'scriptText', 'END')

		executor.execute(liveScript(), helper)
		joined = ''.join(output)
		assert joined.index('OK to leave cockpit') < joined.index('MIDDLE')

	def test_noAllClearWhileKeyboardIsStillReachable(self):
		executor, output, _, _ = makeExecutor()
		helper = makeHelper()

		def liveScript():
			pushSeqCmd = helper.makePushSeqCmd([])
			pushSeqCmd(0, 'scriptKeyboard', 'a')
			yield
			pushSeqCmd(0, 'scriptText', 'MIDDLE')
			pushSeqCmd(0, 'scriptKeyboard', 'b')

		executor.execute(liveScript(), helper)
		joined = ''.join(output)
		assert joined.index('MIDDLE') < joined.index('OK to leave cockpit')

	def test_cockpitDoneMarkerAnnouncesAllClear(self):
		executor, output, _, _ = makeExecutor()
		helper = makeHelper()

		def liveScript():
			pushSeqCmd = helper.makePushSeqCmd([])
			keyboardCommand = 'scriptKeyboard' # Held in a variable, so only the marker can say it's done.
			pushSeqCmd(0, keyboardCommand, 'a')
			pushSeqCmd(0, 'scriptCockpitDone')
			yield
			pushSeqCmd(0, 'scriptText', 'MIDDLE')
			yield
			pushSeqCmd(0, 'scriptText', 'END')

		executor.execute(liveScript(), helper)
		joined = ''.join(output)
		assert joined.count('OK to leave cockpit') == 1
		assert joined.index('OK to leave cockpit') < joined.index('MIDDLE')

	def test_keyboardAfterAllClearPausesAndAsksPlayerToReturn(self):
		pauseCallback = MagicMock()
		executor, output, _, _ = makeExecutor(pauseCallback=pauseCallback)
		helper = makeHelper()

		def liveScript():
			pushSeqCmd = helper.makePushSeqCmd([])
			pushSeqCmd(0, 'scriptKeyboard', 'a')
			pushSeqCmd(0, 'scriptCockpitDone')
			yield
			keyboardCommand = 'scriptKeyboard'
			pushSeqCmd(0, keyboardCommand, 'b')
			pushSeqCmd(0, 'scriptText', 'AFTER_B')

		executor.execute(liveScript(), helper)
		joined = ''.join(output)
		pauseCallback.assert_called_once()
		assert 'return to the cockpit' in joined
		assert joined.index('return to the cockpit') < joined.index('AFTER_B')
		assert joined.count('Keyboard command') >= 2

	def test_timerSpansBatches(self):
		executor, output, _, _ = makeExecutor()
		helper = makeHelper()

		def liveScript():
			pushSeqCmd = helper.makePushSeqCmd([])
			pushSeqCmd(0, 'scriptTimerStart', name='wait', duration=0)
			yield
			pushSeqCmd(0, 'scriptTimerEnd', name='wait')
			pushSeqCmd(0, 'scriptText', 'AFTER_TIMER')

		executor.execute(liveScript(), helper)
		assert 'AFTER_TIMER' in ''.join(output)


# ---------------------------------------------------------------------------
# Telemetry check: on a server that blocks ownship export, DCS sends no LoGet* data, so a wait on it never finishes.
# ---------------------------------------------------------------------------

def test_telemetryFunctionsWaitedOn():
	seq = [
		{'time': 0, 'cmd': 'scriptCockpitState', 'control': 'telemetry/LoGetEngineInfo.RPM.right', 'value': 15},
		{'time': 0, 'cmd': 'scriptCockpitState', 'control': 'TestModule/apuSw', 'value': 1},
		{'time': 0, 'cmd': 'scriptLoopUntilStart', 'control': 'telemetry/LoGetVerticalVelocity', 'value': 0},
		{'time': 0, 'cmd': 'scriptLoopUntilEnd', 'control': 'telemetry/LoGetEngineInfo.RPM.left', 'value': 15},
		{'time': 0, 'cmd': 'scriptLoopUntilEnd'},
		{'time': 0, 'cmd': 'scriptText', 'arg': 'telemetry/LoGetModelTime'},
		{'time': 0, 'cmd': 'scriptCockpitState', 'control': 'telemetry/os.exit', 'value': 1},
	]
	assert telemetryFunctionsWaitedOn(seq) == ['LoGetEngineInfo', 'LoGetVerticalVelocity']


ENGINE_RPM_WAIT = {'time': 0, 'cmd': 'scriptCockpitState', 'control': 'telemetry/LoGetEngineInfo.RPM.right', 'condition': '=', 'value': 1, 'msg': ''}


def makeTelemetryExecutor(answers, debug=False):
	"""Non-debug executor whose DCS answers the LoGet* functions in answers and nothing else."""
	dbe = makeMockDbe()
	dbe.queryTelemetry.side_effect = lambda functionName, timeout=1.0: answers.get(functionName)
	pauseCallback = MagicMock()
	executor, output, ttsManager, _ = makeExecutor(config=makeTestConfig(debug=debug), dbe=dbe, pauseCallback=pauseCallback)
	executor.getDcsWindow = lambda: MagicMock()
	return executor, output, ttsManager, pauseCallback


class TestTelemetryCheck:
	def test_missingTelemetryWarnsAndPausesBeforeTheWait(self):
		executor, output, ttsManager, pauseCallback = makeTelemetryExecutor({})
		executor.execute([ENGINE_RPM_WAIT, {'time': 0, 'cmd': 'scriptText', 'arg': 'AFTER', 'msg': ''}])
		joined = ''.join(output)
		pauseCallback.assert_called_once()
		assert 'No telemetry from DCS for LoGetEngineInfo' in joined
		assert joined.index('No telemetry from DCS') < joined.index('Wait for cockpit state')
		assert any('no telemetry' in str(call).lower() for call in ttsManager.speak.call_args_list)

	def test_telemetryPresentRunsWithoutPausing(self):
		executor, output, _, pauseCallback = makeTelemetryExecutor({'LoGetEngineInfo': {'RPM': {'right': 65}}})
		executor.execute([ENGINE_RPM_WAIT, {'time': 0, 'cmd': 'scriptText', 'arg': 'AFTER', 'msg': ''}])
		pauseCallback.assert_not_called()
		assert 'No telemetry' not in ''.join(output)
		assert 'AFTER' in ''.join(output)

	def test_debugModeDoesNotAskDcs(self):
		executor, output, _, pauseCallback = makeTelemetryExecutor({}, debug=True)
		executor.execute([ENGINE_RPM_WAIT])
		executor.dbe.queryTelemetry.assert_not_called()
		pauseCallback.assert_not_called()

	def test_cockpitWaitsDontNeedTelemetry(self):
		executor, output, _, pauseCallback = makeTelemetryExecutor({})
		executor.execute([{'time': 0, 'cmd': 'scriptCockpitState', 'control': 'TestModule/apuSw', 'condition': '=', 'value': 1, 'msg': ''}])
		executor.dbe.queryTelemetry.assert_not_called()
		pauseCallback.assert_not_called()

	def test_liveScriptWarnsOncePerFunction(self):
		executor, output, _, pauseCallback = makeTelemetryExecutor({})
		helper = makeHelper()

		def liveScript():
			pushSeqCmd = helper.makePushSeqCmd([])
			pushSeqCmd(0, 'scriptCockpitState', control='telemetry/LoGetEngineInfo.RPM.right', condition='=', value=1)
			yield
			pushSeqCmd(0, 'scriptCockpitState', control='telemetry/LoGetEngineInfo.RPM.left', condition='=', value=1)

		executor.execute(liveScript(), helper)
		pauseCallback.assert_called_once()
		assert ''.join(output).count('No telemetry from DCS') == 1


# ---------------------------------------------------------------------------
# Skip Wait: the player can end a wait that would never finish (or that they don't want to sit through).
# ---------------------------------------------------------------------------

def runSkipping(dbe, seq):
	"""Run seq without debug mode, clicking Skip Wait as soon as each wait starts.  A 3 s safety stop makes a skip that doesn't work fail rather than hang.  Returns (output, waitStates)."""
	skipWaitEvent = threading.Event()
	waitStates = []
	def waitStateCallback(waiting):
		waitStates.append(waiting)
		if waiting:
			skipWaitEvent.set()
	executor, output, _, stopFlag = makeExecutor(config=makeTestConfig(debug=False), dbe=dbe, skipWaitEvent=skipWaitEvent, waitStateCallback=waitStateCallback)
	executor.getDcsWindow = lambda: MagicMock()
	safetyStop = threading.Timer(3, stopFlag.set)
	safetyStop.start()
	try:
		executor.execute(seq)
	finally:
		safetyStop.cancel()
	return ''.join(output), waitStates


class TestSkipWait:
	def test_skipEndsCockpitStateWait(self):
		dbe = makeMockDbe()
		dbe.getControlState.return_value = [('TestModule/apuSw', 'APU Switch', 0)]
		joined, waitStates = runSkipping(dbe, [
			{'time': 0, 'cmd': 'scriptCockpitState', 'control': 'TestModule/apuSw', 'condition': '=', 'value': 1, 'msg': ''},
			{'time': 0, 'cmd': 'scriptText', 'arg': 'AFTER', 'msg': ''},
		])
		assert 'Skipped by user' in joined
		assert 'Condition met' not in joined
		assert 'AFTER' in joined
		assert waitStates == [True, False]

	def test_skipEndsTimerWait(self):
		joined, waitStates = runSkipping(makeMockDbe(), [
			{'time': 0, 'cmd': 'scriptTimerStart', 'name': 'align', 'duration': 60},
			{'time': 0, 'cmd': 'scriptTimerEnd', 'name': 'align'},
			{'time': 0, 'cmd': 'scriptText', 'arg': 'AFTER_TIMER', 'msg': ''},
		])
		assert 'Timer skipped by user' in joined
		assert 'AFTER_TIMER' in joined
		assert waitStates == [True, False]

	def test_skipEndsLoopUntil(self):
		dbe = makeMockDbe()
		dbe.getControlState.return_value = [('TestModule/apuSw', 'APU', 0)]
		joined, waitStates = runSkipping(dbe, [
			{'time': 0, 'cmd': 'scriptLoopUntilStart'},
			{'time': 0, 'cmd': 'apuSw', 'arg': '1', 'msg': ''},
			{'time': 0, 'cmd': 'scriptLoopUntilEnd', 'control': 'TestModule/apuSw', 'condition': '=', 'value': 1},
			{'time': 0, 'cmd': 'scriptText', 'arg': 'AFTER_LOOP', 'msg': ''},
		])
		assert 'Loop end: skipped by user' in joined
		assert 'AFTER_LOOP' in joined
		assert waitStates == [True, False]

	def test_skipClickedBeforeTheWaitIsIgnored(self):
		"""A click that lands just after a wait ended mustn't skip the next one."""
		readings = iter([0, 0, 1])
		dbe = makeMockDbe()
		dbe.getControlState.side_effect = lambda control: [(control, 'APU Switch', next(readings, 1))]
		skipWaitEvent = threading.Event()
		skipWaitEvent.set()
		executor, output, _, _ = makeExecutor(config=makeTestConfig(debug=False), dbe=dbe, skipWaitEvent=skipWaitEvent)
		executor.getDcsWindow = lambda: MagicMock()
		executor.execute([{'time': 0, 'cmd': 'scriptCockpitState', 'control': 'TestModule/apuSw', 'condition': '=', 'value': 1, 'msg': ''}])
		joined = ''.join(output)
		assert 'Condition met' in joined
		assert 'Skipped' not in joined

# ---------------------------------------------------------------------------
# Sim commands on a server that blocks ownship export: DCS ignores LoSetCommand from clients, so the player does each step by hand.
# ---------------------------------------------------------------------------

BLOCKED_SELF_DATA = {'Name': 'FA-18C_hornet', 'Coalition': 'Enemies', 'UnitName': 'Havoc 1-1'} # What a blocking server leaves in LoGetSelfData.
OPEN_SELF_DATA = dict(BLOCKED_SELF_DATA, LatLongAlt={'Lat': 43.5, 'Long': 43.6, 'Alt': 431.8}, Pitch=0.0, Bank=0.0)
THROTTLE_IDLE = {'time': 0, 'cmd': 'scriptSimCommand', 'arg': 'iCommandRightEngineStart', 'msg': 'Right throttle IDLE'}


class TestSimCommandsBlocked:
	def test_blockedServerWarnsAtStartAndPromptsAtTheStep(self):
		executor, output, ttsManager, pauseCallback = makeTelemetryExecutor({'LoGetSelfData': BLOCKED_SELF_DATA})
		executor.execute([THROTTLE_IDLE, {'time': 0, 'cmd': 'scriptText', 'arg': 'AFTER', 'msg': ''}])
		joined = ''.join(output)
		assert 'blocks simulator commands' in joined
		assert 'Do it yourself: Right throttle IDLE' in joined
		assert joined.index('blocks simulator commands') < joined.index('Sim command:') < joined.index('Do it yourself') < joined.index('AFTER')
		assert pauseCallback.call_count == 2 # At the start, then at the step.
		assert any('Right throttle IDLE' in str(call) for call in ttsManager.speak.call_args_list)
		executor.dbe.sendSimCommand.assert_called_once_with(312, None) # Still sent, in case the check is wrong.

	def test_openServerSendsWithoutPrompting(self):
		executor, output, _, pauseCallback = makeTelemetryExecutor({'LoGetSelfData': OPEN_SELF_DATA})
		executor.execute([THROTTLE_IDLE])
		joined = ''.join(output)
		assert 'blocks simulator commands' not in joined
		assert 'Do it yourself' not in joined
		pauseCallback.assert_not_called()
		executor.dbe.sendSimCommand.assert_called_once_with(312, None)

	def test_noAnswerFromDcsIsNotTakenAsBlocked(self):
		executor, output, _, pauseCallback = makeTelemetryExecutor({})
		executor.execute([THROTTLE_IDLE])
		assert 'blocks simulator commands' not in ''.join(output)
		pauseCallback.assert_not_called()

	def test_stepWithoutMessagePromptsWithTheCommandName(self):
		executor, output, _, _ = makeTelemetryExecutor({'LoGetSelfData': BLOCKED_SELF_DATA})
		executor.execute([{'time': 0, 'cmd': 'scriptSimCommand', 'arg': 'iCommandRightEngineStart', 'msg': ''}])
		assert 'Do it yourself: iCommandRightEngineStart' in ''.join(output)

	def test_scriptWithoutSimCommandsDoesNotAsk(self):
		executor, _, _, _ = makeTelemetryExecutor({'LoGetSelfData': BLOCKED_SELF_DATA})
		executor.execute([{'time': 0, 'cmd': 'scriptText', 'arg': 'HI', 'msg': ''}])
		executor.dbe.queryTelemetry.assert_not_called()

	def test_debugModeDoesNotAsk(self):
		executor, output, _, pauseCallback = makeTelemetryExecutor({'LoGetSelfData': BLOCKED_SELF_DATA}, debug=True)
		executor.execute([THROTTLE_IDLE])
		executor.dbe.queryTelemetry.assert_not_called()
		pauseCallback.assert_not_called()

	def test_liveScriptWarnsAtStartOnce(self):
		executor, output, _, pauseCallback = makeTelemetryExecutor({'LoGetSelfData': BLOCKED_SELF_DATA})
		helper = makeHelper()

		def liveScript():
			pushSeqCmd = helper.makePushSeqCmd([])
			pushSeqCmd(0, 'scriptSimCommand', 'iCommandRightEngineStart', 'Right throttle IDLE')
			yield
			pushSeqCmd(0, 'scriptSimCommand', 'iCommandLeftEngineStart', 'Left throttle IDLE')

		executor.execute(liveScript(), helper)
		joined = ''.join(output)
		assert joined.count('blocks simulator commands') == 1
		assert joined.count('Do it yourself') == 2
		assert pauseCallback.call_count == 3