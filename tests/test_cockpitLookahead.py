"""Unit tests for engine.cockpitLookahead.mayStillNeedCockpit().

Each test pauses a small live script at a yield and asks whether it can still need the cockpit: a keyboard command, or a read of an ind. (display text) control, which DCS only updates while the cockpit is shown.
Answering True when unsure is always allowed; answering False while such a step is still reachable is the bug to avoid.
"""
import os
import sys

projectRoot = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if projectRoot not in sys.path:
	sys.path.insert(0, projectRoot)

from engine.cockpitLookahead import mayStillNeedCockpit, mayStillUseCommsMenu


def push(*args, **kwargs):
	pass


def moduleLevelKeyboardHelper():
	push(0.3, 'scriptKeyboard', 'home')


def moduleLevelPlainHelper():
	push(0.3, 'UFC.KbdSw1', 1)


def pausedAt(generatorFunction, yieldsToPass=1):
	generator = generatorFunction()
	for _ in range(yieldsToPass):
		next(generator)
	return generator


def test_keyboardLaterInFunctionIsStillReachable():
	def script():
		push(0.3, 'UFC.KbdSw1', 1)
		yield
		push(0.3, 'scriptKeyboard', 'home')
	assert mayStillNeedCockpit(pausedAt(script)) is True


def test_keyboardOnlyBeforePauseIsDone():
	def script():
		push(0.3, 'scriptKeyboard', 'home')
		yield
		push(0.3, 'UFC.KbdSw1', 1)
		yield
		push(0.3, 'UFC.KbdSw2', 1)
	assert mayStillNeedCockpit(pausedAt(script)) is False


def test_keyboardEarlierInEnclosingLoopCanRunAgain():
	def script():
		for _ in range(3):
			push(0.3, 'scriptKeyboard', 'home')
			yield
			push(0.3, 'UFC.KbdSw1', 1)
	assert mayStillNeedCockpit(pausedAt(script)) is True


def test_keyboardInBranchAfterPauseCountsEvenIfNotTaken():
	def script():
		yield
		if False:
			push(0.3, 'scriptKeyboard', 'home')
	assert mayStillNeedCockpit(pausedAt(script)) is True


def test_nestedHelperWithKeyboardCalledLater():
	def script():
		def startEngine():
			push(0.3, 'scriptKeyboard', 'RShift down')
			push(0.3, 'scriptKeyboard', 'home')
			push(0.3, 'scriptKeyboard', 'RShift up')
		startEngine()
		yield
		startEngine()
	assert mayStillNeedCockpit(pausedAt(script)) is True


def test_nestedHelperWithKeyboardNotCalledAgain():
	def script():
		def startEngine():
			push(0.3, 'scriptKeyboard', 'home')
		def pressButton(name):
			push(0.3, name, 1)
		startEngine()
		yield
		pressButton('UFC.KbdSw1')
	assert mayStillNeedCockpit(pausedAt(script)) is False


def test_helperCallingKeyboardHelperIsFollowed():
	def script():
		def startEngine():
			push(0.3, 'scriptKeyboard', 'home')
		def startBothEngines():
			startEngine()
			startEngine()
		yield
		startBothEngines()
	assert mayStillNeedCockpit(pausedAt(script)) is True


def test_moduleLevelHelpersAreFollowed():
	def withKeyboard():
		yield
		moduleLevelKeyboardHelper()

	def withoutKeyboard():
		yield
		moduleLevelPlainHelper()
	assert mayStillNeedCockpit(pausedAt(withKeyboard)) is True
	assert mayStillNeedCockpit(pausedAt(withoutKeyboard)) is False


def test_keyboardPassedAsArgumentToHelperCounts():
	def script():
		def pressKey(cmd, key):
			push(0.3, cmd, key)
		yield
		pressKey('scriptKeyboard', 'home')
	assert mayStillNeedCockpit(pausedAt(script)) is True


def test_indirectKeyboardNameMakesAnswerUnsure():
	"""A 'scriptKeyboard' held in a variable can't be traced, so the answer must stay True."""
	def script():
		keyboardCmd = 'scriptKeyboard'
		push(0.3, keyboardCmd, 'home')
		yield
		push(0.3, keyboardCmd, 'end')
	assert mayStillNeedCockpit(pausedAt(script)) is True


def test_pausedInsideYieldFromChecksRestOfOuterScript():
	def script():
		def checkHelmet():
			yield
			push(0.3, 'UFC.KbdSw1', 1)
		yield from checkHelmet()
		push(0.3, 'scriptKeyboard', 'home')
	assert mayStillNeedCockpit(pausedAt(script)) is True


def test_pausedInsideYieldFromChecksRestOfInnerHelper():
	def script():
		def checkHelmet():
			yield
			push(0.3, 'scriptKeyboard', 'home')
		yield from checkHelmet()
		push(0.3, 'UFC.KbdSw1', 1)
	assert mayStillNeedCockpit(pausedAt(script)) is True


def test_pausedInsideYieldFromWithNoKeyboardLeft():
	def script():
		push(0.3, 'scriptKeyboard', 'home')
		def checkHelmet():
			yield
			push(0.3, 'UFC.KbdSw1', 1)
		yield from checkHelmet()
		push(0.3, 'UFC.KbdSw2', 1)
	assert mayStillNeedCockpit(pausedAt(script)) is False


def test_laterWaitOnDisplayTextNeedsCockpit():
	def script():
		yield
		push(0.3, 'scriptCockpitState', control='A-10C_2/ind.3.AlignTime', value='4.0')
	assert mayStillNeedCockpit(pausedAt(script)) is True


def test_laterReadOfDisplayTextNeedsCockpit():
	class helper:
		@staticmethod
		def read(control, default=None):
			return default

	def script():
		yield
		helper.read('ind.5.txt_RPM_R', default=0)
	assert mayStillNeedCockpit(pausedAt(script)) is True


def test_argAndTelemetryWaitsDoNotNeedCockpit():
	def script():
		push(0.3, 'scriptCockpitState', control='A-10C_2/ind.3.AlignTime', value='4.0')
		yield
		push(0.3, 'scriptCockpitState', control='A-10C_2/arg.APU_RPM', value=0.83)
		push(0.3, 'scriptCockpitState', control='telemetry/LoGetEngineInfo.RPM.left', condition='>=', value=15)
	assert mayStillNeedCockpit(pausedAt(script)) is False


def test_displayTextNameInVariableMakesAnswerUnsure():
	def script():
		alignControl = 'A-10C_2/ind.3.AlignTime'
		yield
		push(0.3, 'scriptCockpitState', control=alignControl, value='4.0')
	assert mayStillNeedCockpit(pausedAt(script)) is True


def test_commsMenuCommandLaterIsStillReachable():
	def script():
		push(0.3, 'scriptSimCommand', 'iCommandLeftEngineStart')
		yield
		push(0.3, 'scriptSimCommand', 'ICommandMenuItem8')
	assert mayStillUseCommsMenu(pausedAt(script)) is True
	assert mayStillNeedCockpit(pausedAt(script)) is False


def test_commsMenuCommandOnlyBeforePauseIsDone():
	def script():
		push(0.3, 'scriptSimCommand', 'ICommandMenuItem12')
		push(0.3, 'scriptKeyboard', 'home')
		yield
		push(0.3, 'scriptSimCommand', 'iCommandLeftEngineStop')
	assert mayStillUseCommsMenu(pausedAt(script)) is False
