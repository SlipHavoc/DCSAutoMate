"""Tests for tools/validateControlMapping.py — value translation and comparison logic."""
import os
import sys
from unittest.mock import patch, call

import pytest

projectRoot = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if projectRoot not in sys.path:
	sys.path.insert(0, projectRoot)
toolsDir = os.path.join(projectRoot, 'tools', 'validation-scripts')
if toolsDir not in sys.path:
	sys.path.insert(0, toolsDir)

from validateControlMapping import (
	translateToNative,
	reverseTranslateFromNative,
	valuesMatch,
	testDiscrete,
	testDiscreteIndicator,
	testControl,
	parseIndication,
)


# ---------------------------------------------------------------------------
# translateToNative
# ---------------------------------------------------------------------------

class TestTranslateToNative:
	def test_discrete_position_0(self):
		control = {'type': 'discrete', 'argLim': [0.0, 1.0], 'step': 0.5, 'positions': 3}
		assert translateToNative(control, 0) == pytest.approx(0.0)

	def test_discrete_position_1(self):
		control = {'type': 'discrete', 'argLim': [0.0, 1.0], 'step': 0.5, 'positions': 3}
		assert translateToNative(control, 1) == pytest.approx(0.5)

	def test_discrete_position_2(self):
		control = {'type': 'discrete', 'argLim': [0.0, 1.0], 'step': 0.5, 'positions': 3}
		assert translateToNative(control, 2) == pytest.approx(1.0)

	def test_discrete_negative_base(self):
		"""Discrete with argLim starting below zero."""
		control = {'type': 'discrete', 'argLim': [-1.0, 1.0], 'step': 1.0, 'positions': 3}
		assert translateToNative(control, 0) == pytest.approx(-1.0)
		assert translateToNative(control, 1) == pytest.approx(0.0)
		assert translateToNative(control, 2) == pytest.approx(1.0)

	def test_discrete_non_unit_range(self):
		"""Discrete where range is not [0,1] — identity function would fail."""
		control = {'type': 'discrete', 'argLim': [0.2, 0.8], 'step': 0.3, 'positions': 3}
		assert translateToNative(control, 0) == pytest.approx(0.2)
		assert translateToNative(control, 1) == pytest.approx(0.5)
		assert translateToNative(control, 2) == pytest.approx(0.8)

	def test_continuous_0_percent(self):
		control = {'type': 'continuous', 'argLim': [0.0, 1.0]}
		assert translateToNative(control, 0.0) == pytest.approx(0.0)

	def test_continuous_50_percent(self):
		control = {'type': 'continuous', 'argLim': [0.0, 1.0]}
		assert translateToNative(control, 0.5) == pytest.approx(0.5)

	def test_continuous_100_percent(self):
		control = {'type': 'continuous', 'argLim': [0.0, 1.0]}
		assert translateToNative(control, 1.0) == pytest.approx(1.0)

	def test_continuous_non_unit_range(self):
		"""Continuous where range is not [0,1] — identity function would fail."""
		control = {'type': 'continuous', 'argLim': [0.3, 0.7]}
		assert translateToNative(control, 0.0) == pytest.approx(0.3)
		assert translateToNative(control, 0.5) == pytest.approx(0.5)
		assert translateToNative(control, 1.0) == pytest.approx(0.7)

	def test_continuous_clamped_above(self):
		control = {'type': 'continuous', 'argLim': [0.0, 1.0]}
		assert translateToNative(control, 1.5) == pytest.approx(1.0)

	def test_continuous_clamped_below(self):
		control = {'type': 'continuous', 'argLim': [0.0, 1.0]}
		assert translateToNative(control, -0.5) == pytest.approx(0.0)

	def test_relative_passthrough(self):
		control = {'type': 'relative'}
		assert translateToNative(control, 0.1) == pytest.approx(0.1)
		assert translateToNative(control, -0.75) == pytest.approx(-0.75)


# ---------------------------------------------------------------------------
# reverseTranslateFromNative
# ---------------------------------------------------------------------------

class TestReverseTranslateFromNative:
	def test_discrete_position_0(self):
		control = {'type': 'discrete', 'argLim': [0.0, 1.0], 'step': 0.5}
		assert reverseTranslateFromNative(control, 0.0) == 0

	def test_discrete_position_1(self):
		control = {'type': 'discrete', 'argLim': [0.0, 1.0], 'step': 0.5}
		assert reverseTranslateFromNative(control, 0.5) == 1

	def test_discrete_position_2(self):
		control = {'type': 'discrete', 'argLim': [0.0, 1.0], 'step': 0.5}
		assert reverseTranslateFromNative(control, 1.0) == 2

	def test_discrete_negative_base(self):
		control = {'type': 'discrete', 'argLim': [-1.0, 1.0], 'step': 1.0}
		assert reverseTranslateFromNative(control, -1.0) == 0
		assert reverseTranslateFromNative(control, 0.0) == 1
		assert reverseTranslateFromNative(control, 1.0) == 2

	def test_discrete_non_unit_range(self):
		"""Non [0,1] range — identity would fail."""
		control = {'type': 'discrete', 'argLim': [0.2, 0.8], 'step': 0.3}
		assert reverseTranslateFromNative(control, 0.2) == 0
		assert reverseTranslateFromNative(control, 0.5) == 1
		assert reverseTranslateFromNative(control, 0.8) == 2

	def test_discrete_zero_step(self):
		control = {'type': 'discrete', 'argLim': [0.0, 1.0], 'step': 0.0}
		assert reverseTranslateFromNative(control, 0.5) == 0

	def test_continuous_0_percent(self):
		control = {'type': 'continuous', 'argLim': [0.0, 1.0]}
		assert reverseTranslateFromNative(control, 0.0) == pytest.approx(0.0)

	def test_continuous_50_percent(self):
		control = {'type': 'continuous', 'argLim': [0.0, 1.0]}
		assert reverseTranslateFromNative(control, 0.5) == pytest.approx(0.5)

	def test_continuous_100_percent(self):
		control = {'type': 'continuous', 'argLim': [0.0, 1.0]}
		assert reverseTranslateFromNative(control, 1.0) == pytest.approx(1.0)

	def test_continuous_non_unit_range(self):
		"""Non [0,1] range — identity would fail."""
		control = {'type': 'continuous', 'argLim': [0.3, 0.7]}
		assert reverseTranslateFromNative(control, 0.3) == pytest.approx(0.0)
		assert reverseTranslateFromNative(control, 0.5) == pytest.approx(0.5)
		assert reverseTranslateFromNative(control, 0.7) == pytest.approx(1.0)

	def test_continuous_zero_span(self):
		control = {'type': 'continuous', 'argLim': [0.5, 0.5]}
		assert reverseTranslateFromNative(control, 0.5) == pytest.approx(0.0)

	def test_readonly_passthrough(self):
		control = {}  # No type = read-only.
		assert reverseTranslateFromNative(control, 0.42) == pytest.approx(0.42)


# ---------------------------------------------------------------------------
# Round-trip: translate → reverse should be identity
# ---------------------------------------------------------------------------

class TestRoundTrip:
	def test_discrete_round_trip(self):
		control = {'type': 'discrete', 'argLim': [-1.0, 1.0], 'step': 1.0, 'positions': 3}
		for pos in range(3):
			native = translateToNative(control, pos)
			backToScript = reverseTranslateFromNative(control, native)
			assert backToScript == pos

	def test_discrete_round_trip_non_unit_range(self):
		"""Non [0,1] range round-trip."""
		control = {'type': 'discrete', 'argLim': [0.2, 0.8], 'step': 0.3, 'positions': 3}
		for pos in range(3):
			native = translateToNative(control, pos)
			backToScript = reverseTranslateFromNative(control, native)
			assert backToScript == pos

	def test_continuous_round_trip(self):
		control = {'type': 'continuous', 'argLim': [0.0, 1.0]}
		for proportion in [0.0, 0.25, 0.5, 0.75, 1.0]:
			native = translateToNative(control, proportion)
			backToScript = reverseTranslateFromNative(control, native)
			assert backToScript == pytest.approx(proportion)

	def test_continuous_round_trip_non_unit_range(self):
		"""Non [0,1] range round-trip."""
		control = {'type': 'continuous', 'argLim': [0.3, 0.7]}
		for proportion in [0.0, 0.25, 0.5, 0.75, 1.0]:
			native = translateToNative(control, proportion)
			backToScript = reverseTranslateFromNative(control, native)
			assert backToScript == pytest.approx(proportion)


# ---------------------------------------------------------------------------
# valuesMatch
# ---------------------------------------------------------------------------

class TestValuesMatch:
	def test_exact_match(self):
		assert valuesMatch(1.0, 1.0) is True

	def test_within_tolerance(self):
		assert valuesMatch(0.5, 0.51, tolerance=0.02) is True

	def test_outside_tolerance(self):
		assert valuesMatch(0.5, 0.53, tolerance=0.02) is False

	def test_none_expected(self):
		assert valuesMatch(None, 0.5) is False

	def test_none_actual(self):
		assert valuesMatch(0.5, None) is False

	def test_both_none(self):
		assert valuesMatch(None, None) is False

	def test_zero_tolerance(self):
		assert valuesMatch(0.5, 0.5, tolerance=0.0) is True
		assert valuesMatch(0.5, 0.500001, tolerance=0.0) is False


# ---------------------------------------------------------------------------
# parseIndication
# ---------------------------------------------------------------------------

class TestParseIndication:
	def test_standard_indication(self):
		raw = '-----------------------------------------\ntxt_RPM_L\n 63\n-----------------------------------------\ntxt_RPM_R\n 64\n'
		result = parseIndication(raw)
		assert result == {'txt_RPM_L': '63', 'txt_RPM_R': '64'}

	def test_empty_string(self):
		assert parseIndication('') == {}

	def test_single_field(self):
		raw = '-----------------------------------------\nfieldName\nfieldValue\n'
		result = parseIndication(raw)
		assert result == {'fieldName': 'fieldValue'}


# ---------------------------------------------------------------------------
# testDiscreteIndicator
# ---------------------------------------------------------------------------

INDICATOR_CONTROL = {
	'type': 'discrete',
	'deviceId': 10,
	'commandId': 3001,
	'arg': 330,
	'argLim': [0.0, 1.0],
	'step': 1.0,
	'positions': 2,
	'indicatorArgLim': [0.0, 0.3],
}

class TestDiscreteIndicator:
	def test_all_positions_changed_returns_pass(self):
		"""All positions produce a changed arg value in the forward+backward sweep → 'pass'."""
		# N=2: forward pos0→success, pos1(turnaround)→success; backward pos0→success.
		with patch('validateControlMapping.queryArg', side_effect=[0.0, 0.3, 0.0]) as mockQuery, \
		     patch('validateControlMapping.waitForStable', side_effect=[0.3, 0.0, 0.3]) as mockWait, \
		     patch('validateControlMapping.performClickableAction') as mockClick:
			status, detail = testDiscreteIndicator(None, 'TEST.Control', INDICATOR_CONTROL, 0.1)
		assert status == 'pass'
		assert 'indicator-range' in detail
		assert mockClick.call_count == 3

	def test_unchanged_in_both_directions_returns_fail(self):
		"""A position unchanged in both forward and backward passes → 'fail'."""
		# N=2: fwd pos0 unchanged, fwd pos1(turnaround) changed, bwd pos0 still unchanged.
		with patch('validateControlMapping.queryArg', side_effect=[0.0, 0.0, 0.3]) as mockQuery, \
		     patch('validateControlMapping.waitForStable', side_effect=[0.0, 0.3, 0.3]) as mockWait, \
		     patch('validateControlMapping.performClickableAction'):
			status, detail = testDiscreteIndicator(None, 'TEST.Control', INDICATOR_CONTROL, 0.1)
		assert status == 'fail'
		assert 'pos 0' in detail
		assert 'stuck' in detail

	def test_unchanged_forward_but_changed_backward_returns_pass(self):
		"""A position unchanged in the forward pass but changed in the backward pass → 'pass'."""
		# N=2: fwd pos0 unchanged→fail, fwd pos1(turnaround) changed→success, bwd pos0 changed→success.
		with patch('validateControlMapping.queryArg', side_effect=[0.0, 0.0, 0.3]) as mockQuery, \
		     patch('validateControlMapping.waitForStable', side_effect=[0.0, 0.3, 0.0]) as mockWait, \
		     patch('validateControlMapping.performClickableAction'):
			status, detail = testDiscreteIndicator(None, 'TEST.Control', INDICATOR_CONTROL, 0.1)
		assert status == 'pass'

	def test_read_error_returns_error_immediately(self):
		"""A None from queryArg is a hard failure that aborts immediately."""
		with patch('validateControlMapping.queryArg', side_effect=[None]) as mockQuery, \
		     patch('validateControlMapping.waitForStable') as mockWait, \
		     patch('validateControlMapping.performClickableAction') as mockClick:
			status, detail = testDiscreteIndicator(None, 'TEST.Control', INDICATOR_CONTROL, 0.1)
		assert status == 'error'
		assert 'pos 0' in detail
		assert 'pre-send read failed' in detail
		mockWait.assert_not_called()
		mockClick.assert_not_called()

	def test_missing_fields_returns_skip(self):
		"""Missing commandId → 'skip'."""
		ctrl = {k: v for k, v in INDICATOR_CONTROL.items() if k != 'commandId'}
		with patch('validateControlMapping.queryArg'), \
		     patch('validateControlMapping.waitForStable'), \
		     patch('validateControlMapping.performClickableAction'):
			status, detail = testDiscreteIndicator(None, 'TEST.Control', ctrl, 0.1)
		assert status == 'skip'


# ---------------------------------------------------------------------------
# testControl dispatch for indicator controls
# ---------------------------------------------------------------------------

class TestControlDispatch:
	def test_indicatorArgLim_routes_to_testDiscreteIndicator(self):
		"""indicatorArgLim control routes to testDiscreteIndicator, not testDiscrete."""
		with patch('validateControlMapping.testDiscreteIndicator', return_value=('pass', 'ok')) as mockFn, \
		     patch('validateControlMapping.testDiscrete') as mockStd:
			status, detail = testControl(None, 'TEST.Control', INDICATOR_CONTROL, 0.1)
		assert status == 'pass'
		mockFn.assert_called_once()
		mockStd.assert_not_called()

	def test_indicatorPositions_routes_to_testDiscreteIndicator(self):
		"""indicatorPositions control routes to testDiscreteIndicator, not testDiscrete."""
		ctrl = {k: v for k, v in INDICATOR_CONTROL.items() if k != 'indicatorArgLim'}
		ctrl['indicatorPositions'] = [0.0, 0.3, 0.6]
		with patch('validateControlMapping.testDiscreteIndicator', return_value=('pass', 'ok')) as mockFn, \
		     patch('validateControlMapping.testDiscrete') as mockStd:
			status, detail = testControl(None, 'TEST.Control', ctrl, 0.1)
		mockFn.assert_called_once()
		mockStd.assert_not_called()

	def test_plain_discrete_routes_to_testDiscrete(self):
		"""Plain discrete control (no indicator fields) routes to testDiscrete."""
		ctrl = {k: v for k, v in INDICATOR_CONTROL.items() if k not in ('indicatorArgLim',)}
		with patch('validateControlMapping.testDiscrete', return_value=('pass', 'ok')) as mockFn, \
		     patch('validateControlMapping.testDiscreteIndicator') as mockInd:
			status, detail = testControl(None, 'TEST.Control', ctrl, 0.1)
		mockFn.assert_called_once()
		mockInd.assert_not_called()

	def test_arg_neg1_returns_skip(self):
		"""Controls with arg=-1 (pure encoder, no readable position) are skipped."""
		ctrl = {'type': 'discrete', 'deviceId': 48, 'commandId': 3007, 'arg': -1, 'argLim': [-1.0, 1.0], 'positions': 3}
		status, detail = testControl(None, 'TEST.Control', ctrl, 0.1)
		assert status == 'skip'
		assert '-1' in detail


# ---------------------------------------------------------------------------
# testDiscrete restore behaviour
# ---------------------------------------------------------------------------

DISCRETE_CONTROL = {'type': 'discrete', 'deviceId': 4, 'commandId': 3001, 'arg': 290, 'argLim': [0.0, 1.0], 'step': 1.0, 'positions': 2}

class TestDiscreteRestore:
	def test_restore_skipped_when_already_at_initial_state(self):
		"""If the arg already equals initialNative after the sweep, restore send is skipped.

		This is the toggle-guard regression test: toggle controls flip on every
		command, so sending initialNative when already there would flip the state
		wrong.  The fix reads the arg first and skips the send if it already matches.
		"""
		# queryArg calls: [initial=1.0, guard-check=1.0]  — guard matches, no restore.
		# waitForStable calls: [pos0 actual=0.0, pos1 actual=1.0]
		with patch('validateControlMapping.queryArg', side_effect=[1.0, 1.0]) as mockQuery, \
		     patch('validateControlMapping.waitForStable', side_effect=[0.0, 1.0]) as mockWait, \
		     patch('validateControlMapping.performClickableAction') as mockClick:
			status, detail = testDiscrete(None, 'TEST.Control', DISCRETE_CONTROL, 0.1)
		assert status == 'pass'
		# Two position sends only — no restore send.
		assert mockClick.call_count == 2

	def test_restore_sent_when_not_at_initial_state(self):
		"""If the arg does not match initialNative after the sweep, restore is sent."""
		# queryArg calls: [initial=1.0, guard-check=0.0]  — mismatch, restore sent.
		# waitForStable calls: [pos0 actual=0.0, pos1 actual=0.0 (fail), restore wait=1.0]
		with patch('validateControlMapping.queryArg', side_effect=[1.0, 0.0]) as mockQuery, \
		     patch('validateControlMapping.waitForStable', side_effect=[0.0, 0.0, 1.0]) as mockWait, \
		     patch('validateControlMapping.performClickableAction') as mockClick:
			status, detail = testDiscrete(None, 'TEST.Control', DISCRETE_CONTROL, 0.1)
		assert status == 'fail'  # pos 1 didn't reach 1.0
		# Two position sends + one restore send.
		assert mockClick.call_count == 3
