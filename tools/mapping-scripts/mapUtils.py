"""Shared dispatch runner for per-module map_*.py scripts.

This module is part of the explicit helper-handler architecture described in
.agent/research/2026-05-13-explicit-helper-handlers-plan.md.  Each DCS module
has a corresponding tools/map_<module>.py that defines HELPER_MAP — a dict
mapping every Lua helper function name seen in that module's nativeExtraction
to a Python archetype callable or STRUCTURAL_FALLBACK.

runMapping() is the main entry point.  Per-module scripts call it with their
HELPER_MAP.  It validates that every tagged helper has an entry (failing loudly
if not), then runs the full control-mapping pipeline using the same logic as
generateControlMapping.py.

Architecture note:
  STRUCTURAL_FALLBACK (None) delegates element processing to the existing
  structural dispatch chain in generateControlMapping.processElements().
  Explicit archetype functions (simpleDiscrete, continuousAxis, springloadedTumb,
  iffRelativeKnob, relativeAxis, buttonOrAxis) are defined in this module and
  cover every helper seen in the UH-1H pilot.  New modules add their helpers to
  their own HELPER_MAP, mapping each to an archetype or STRUCTURAL_FALLBACK.
"""

import json
import os
import sys

from commandVariants import inferDeviceTableMapByEvidence
from generateControlMapping import (
	buildDeviceTableMap,
	buildCommandReverse,
	classifyType,
	computeStepAndPositions,
	detectBinaryToggle,
	detectBtnPulseCounter,
	detectDualCommandRotary,
	detectIFFMultipositionSpring,
	detectPdpSpecial,
	detectSpringloadedSwitch,
	detectWheel,
	makeCanonicalName,
	processElements,
	processIndicators,
	processGaugesAndLamps,
	processRawCommands,
	annotateIndicatorArgLim,
	preserveExistingSendProtocol,
)

# Sentinel value for HELPER_MAP entries that should use structural dispatch.
STRUCTURAL_FALLBACK = None


# ─── Context class ────────────────────────────────────────────────────────────

class _Ctx:
	"""Per-arg-group context passed to archetype functions.

	Carries the information needed to build canonical names and control
	metadata without each archetype function needing direct access to the
	shared lookup tables.
	"""
	__slots__ = (
		'deviceId', 'elemKey', 'multipleArgGroups',
		'_devNameById', '_deviceTableMap', '_perTableReverse', '_globalUnique',
		'_hint', '_hintKey', '_crewAccess',
	)

	def __init__(self, elemKey, deviceId, devNameById, deviceTableMap,
				perTableReverse, globalUnique, multipleArgGroups,
				hint, hintKey, crewAccess):
		self.elemKey = elemKey
		self.deviceId = deviceId
		self.multipleArgGroups = multipleArgGroups
		self._devNameById = devNameById
		self._deviceTableMap = deviceTableMap
		self._perTableReverse = perTableReverse
		self._globalUnique = globalUnique
		self._hint = hint
		self._hintKey = hintKey
		self._crewAccess = crewAccess

	def canonical(self, commandId, arg):
		"""Build the canonical name for (deviceId, commandId).

		Appends _arg<N> suffix when the element has multiple arg groups and the
		element key appears in the canonical — same logic as the structural
		dispatch in generateControlMapping.processElements().
		"""
		name = makeCanonicalName(
			self.deviceId, commandId, self._devNameById,
			self._deviceTableMap, self._perTableReverse, self._globalUnique,
			elementKey=self.elemKey,
		)
		if self.multipleArgGroups and self.elemKey in name:
			name = f'{name}_arg{arg}'
		return name

	def meta(self):
		"""Return description, hintKey, and crewAccess fields for a control entry."""
		fields = {'description': self._hint}
		if self._hintKey:
			fields['hintKey'] = self._hintKey
		if self._crewAccess is not None:
			fields['crewAccess'] = self._crewAccess
		return fields


# ─── Archetype functions ──────────────────────────────────────────────────────
#
# Each archetype takes (elem, indices, ctx) and returns {canonical: control}
# or None if the element shape is unexpected.
#
# All archetype functions are designed to produce output identical to the
# corresponding branch in generateControlMapping.processElements().  Output
# parity is verified by diffing map_<module>.py against generateControlMapping.py
# on the same extraction data.
#
# Signature: archetypeFn(elem, indices, ctx) -> dict | None


def binaryToggle(elem, indices, ctx):
	"""Handles `animated_guard_switch` — a 2-position cover/guard toggle.

	Two TUMB sub-controls share the same arg + commandId with symmetric ±argValue.
	The argValue magnitude is the per-frame animation delta (e.g. 0.01 across [0,1]),
	NOT a multi-position step.  Emit a 2-position discrete with step = full range.

	Suitable for: animated_guard_switch.
	"""
	i = indices[0]
	actions = elem.get('action', [])
	argLims = elem.get('argLim', [])
	args = elem.get('arg', [])

	actionId = actions[i] if i < len(actions) else 0
	if not actionId:
		return None

	arg = args[i] if i < len(args) else 0
	lim = argLims[i] if i < len(argLims) else [0.0, 1.0]
	argLim = [round(lim[0], 6), round(lim[1], 6)] if isinstance(lim, list) and len(lim) == 2 else [0.0, 1.0]
	step = round(argLim[1] - argLim[0], 6)

	canonical = ctx.canonical(actionId, arg)
	control = {
		**ctx.meta(),
		'type': 'discrete',
		'deviceId': ctx.deviceId,
		'commandId': actionId,
		'argLim': argLim,
		'step': step,
		'positions': 2,
	}
	if arg != 0:
		control['arg'] = arg
	control['elementName'] = ctx.elemKey
	return {canonical: control}


def simpleDiscrete(elem, indices, ctx):
	"""Handles BTN/TUMB single-step controls using indices[0] as the primary sub-control.

	Suitable for: default_button, default_2_position_button, default_2_position_tumb,
	default_3_position_tumb, default_1_position_tumb, multiposition_switch,
	multiposition_switch_limited, multiposition_tumb_limited, default_2_position_cover.

	For multi-index groups (e.g. two TUMB sub-controls with different commandIds and
	argLim spanning multiple steps), detectDualCommandRotary is checked first — these
	use the inc-side (positive argValue) commandId, matching the structural dualRotary
	path in processElements().
	"""
	# Dual-command rotary: two TUMB sub-controls, different commandIds, symmetric ±argValue,
	# argLim spanning more than one step.  Use the inc-side commandId.
	if len(indices) >= 2:
		dualRotary = detectDualCommandRotary(elem, indices)
		if dualRotary:
			incIdx, _decIdx = dualRotary
			actions = elem.get('action', [])
			argValues = elem.get('argValue', [])
			argLims = elem.get('argLim', [])
			args = elem.get('arg', [])
			incCmdId = actions[incIdx]
			incValue = abs(round(argValues[incIdx], 6))
			lim = argLims[incIdx]
			argLim = [round(lim[0], 6), round(lim[1], 6)]
			rng = argLim[1] - argLim[0]
			positions = round(rng / incValue) + 1 if incValue > 0 else 2
			arg = args[incIdx] if incIdx < len(args) else 0
			canonical = ctx.canonical(incCmdId, arg)
			control = {
				**ctx.meta(),
				'type': 'discrete',
				'deviceId': ctx.deviceId,
				'commandId': incCmdId,
				'argLim': argLim,
				'step': incValue,
				'positions': positions,
			}
			if arg != 0:
				control['arg'] = arg
			control['elementName'] = ctx.elemKey
			return {canonical: control}

	i = indices[0]
	actions = elem.get('action', [])
	argValues = elem.get('argValue', [])
	argLims = elem.get('argLim', [])
	args = elem.get('arg', [])
	classes = elem.get('controlClass', [])
	classesVr = elem.get('classVr', [])

	actionId = actions[i] if i < len(actions) else 0
	if not actionId:
		return None

	arg = args[i] if i < len(args) else 0
	lim = argLims[i] if i < len(argLims) else [0.0, 1.0]
	argLim = [round(lim[0], 6), round(lim[1], 6)] if isinstance(lim, list) and len(lim) == 2 else [0.0, 1.0]
	argValue = argValues[i] if i < len(argValues) else None
	step, positions = computeStepAndPositions(argLim, argValue)

	# classVr = MULTY_TUMB on a LEV sub-control means discrete + sendProtocol S.
	controlClass = classes[i] if i < len(classes) else 'BTN'
	vrClass = classesVr[i] if i < len(classesVr) else None
	sendProtocol = 'S' if (vrClass == 'MULTY_TUMB' and controlClass == 'LEV') else None

	canonical = ctx.canonical(actionId, arg)
	control = {
		**ctx.meta(),
		'type': 'discrete',
		'deviceId': ctx.deviceId,
		'commandId': actionId,
	}
	if arg != 0:
		control['arg'] = arg
	control['argLim'] = argLim
	control['step'] = step
	control['positions'] = positions
	if sendProtocol:
		control['sendProtocol'] = sendProtocol
	control['elementName'] = ctx.elemKey
	return {canonical: control}


def incrementalTumb(elem, indices, ctx):
	"""Handles sign-driven incremental TUMB pairs (C-130J multiswitch_stop: APU and engine start selectors).

	Both sub-controls share one commandId and send ±step deltas; the device only honours the sign,
	so each send moves exactly one position.  argLim/step/positions are kept as reference metadata.
	"""
	result = simpleDiscrete(elem, indices, ctx)
	if not result:
		return None
	canonical, control = next(iter(result.items()))
	step = control['step']
	control['type'] = 'relative'
	control['sendProtocol'] = 'C'
	control['incrementValue'] = step
	control['decrementValue'] = -step
	return {canonical: control}


def continuousAxis(elem, indices, ctx):
	"""Handles LEV axis controls (default_axis, default_axis_limited).

	Produces type=continuous for non-relative axes and type=relative (with
	sendProtocol=C) for relative axes, matching classifyType('LEV', isRelative)
	in the structural else branch.  Most elements are non-relative, but a subset
	of default_axis / default_axis_limited elements have relative=True.
	"""
	i = indices[0]
	actions = elem.get('action', [])
	argLims = elem.get('argLim', [])
	args = elem.get('arg', [])
	relatives = elem.get('relative', [])

	actionId = actions[i] if i < len(actions) else 0
	if not actionId:
		return None

	arg = args[i] if i < len(args) else 0
	lim = argLims[i] if i < len(argLims) else [0.0, 1.0]
	argLim = [round(lim[0], 6), round(lim[1], 6)] if isinstance(lim, list) and len(lim) == 2 else [0.0, 1.0]
	isRelative = relatives[i] if i < len(relatives) else False
	controlType = classifyType('LEV', isRelative)

	canonical = ctx.canonical(actionId, arg)
	control = {
		**ctx.meta(),
		'type': controlType,
		'deviceId': ctx.deviceId,
		'commandId': actionId,
	}
	if arg != 0:
		control['arg'] = arg
	control['argLim'] = argLim
	if controlType == 'relative':
		control['sendProtocol'] = 'C'
	control['elementName'] = ctx.elemKey
	return {canonical: control}


def springloadedTumb(elem, indices, ctx):
	"""Handles springloaded center-return switches (2- or 3-position).

	Suitable for: default_springloaded_switch, default_springloaded_3pos_switch.

	Delegates to detectSpringloadedSwitch which merges the two complementary
	sub-controls (one with argLim covering the lower half, one covering the upper
	half) into a single control spanning the full merged argLim.  The number of
	positions is (mergedRange / step) + 1, same formula the structural dispatch uses.
	This means default_springloaded_3pos_switch reliably produces 3 positions
	regardless of how the individual sub-control argLims are written.
	"""
	result = detectSpringloadedSwitch(elem, indices)
	if not result:
		return None
	decIdx, incIdx, mergedArgLim, step, positions = result

	actions = elem.get('action', [])
	args = elem.get('arg', [])

	actionId = actions[decIdx] if decIdx < len(actions) else 0
	if not actionId:
		return None

	arg = args[decIdx] if decIdx < len(args) else 0
	canonical = ctx.canonical(actionId, arg)
	control = {
		**ctx.meta(),
		'type': 'discrete',
		'deviceId': ctx.deviceId,
		'commandId': actionId,
		'argLim': mergedArgLim,
		'step': step,
		'positions': positions,
	}
	if arg != 0:
		control['arg'] = arg
	control['elementName'] = ctx.elemKey
	return {canonical: control}


def twoCommandSpringloaded(elem, indices, ctx):
	"""Handles 3-position springloaded switches that use two different commandIds.

	Suitable for: springloaded_3_pos_tumb, springloaded_3_pos_tumb2,
	default_button_tumb_v2 (FA-18C), default_button_tumb (A-10C canopy),
	and any module-specific variant that produces two sub-controls at the same
	arg with complementary argLims and DIFFERENT commands for the dec and inc
	directions.

	Contrast with springloadedTumb, which handles the same-commandId variant
	(default_springloaded_switch / default_springloaded_3pos_switch).

	Produces type=discrete, positions=3, and a positionMap array with null at
	the center position, matching the structural dispatch output for these
	elements (the null entry represents the spring-back neutral position that
	requires no command).

	positionMap `value` fields use the argLim endpoint as the absolute cockpit
	target (matching buildPositionMap in generateControlMapping): the negative
	delta sub-control contributes argLim[0] and the positive delta contributes
	argLim[1].  This differs from argValue only when argValue magnitude < range
	(e.g. A-10C canopy: argValue=±0.5, argLim=[0,0.5]/[0.5,1] → values 0/1).
	"""
	if len(indices) != 2:
		return None

	actions = elem.get('action', [])
	argValues = elem.get('argValue', [])
	argLims = elem.get('argLim', [])
	args = elem.get('arg', [])

	i0, i1 = indices
	cmd0 = actions[i0] if i0 < len(actions) else 0
	cmd1 = actions[i1] if i1 < len(actions) else 0
	if not cmd0 or not cmd1:
		return None

	val0 = argValues[i0] if i0 < len(argValues) else 0.0
	val1 = argValues[i1] if i1 < len(argValues) else 0.0

	# Identify dec (lower argValue) and inc (higher argValue) sub-elements.
	if val0 <= val1:
		decIdx, incIdx = i0, i1
	else:
		decIdx, incIdx = i1, i0

	decCmd = actions[decIdx]
	incCmd = actions[incIdx]
	decArgVal = argValues[decIdx] if decIdx < len(argValues) else 0.0
	incArgVal = argValues[incIdx] if incIdx < len(argValues) else 0.0

	# Use argLim endpoint as absolute target (matching buildPositionMap logic):
	# negative delta → lower bound of decIdx's argLim; positive → upper bound.
	decArgLim = argLims[decIdx] if decIdx < len(argLims) else None
	incArgLim = argLims[incIdx] if incIdx < len(argLims) else None
	if decArgVal != 0 and isinstance(decArgLim, list) and len(decArgLim) == 2 and decArgLim[0] != decArgLim[1]:
		decTarget = round(decArgLim[0], 6)
	else:
		decTarget = round(decArgVal, 6)
	if incArgVal != 0 and isinstance(incArgLim, list) and len(incArgLim) == 2 and incArgLim[0] != incArgLim[1]:
		incTarget = round(incArgLim[1], 6)
	else:
		incTarget = round(incArgVal, 6)

	arg = args[decIdx] if decIdx < len(args) else 0
	canonical = ctx.canonical(decCmd, arg)
	control = {
		**ctx.meta(),
		'type': 'discrete',
		'positions': 3,
		'positionMap': [
			{'deviceId': ctx.deviceId, 'commandId': decCmd, 'value': decTarget},
			None,
			{'deviceId': ctx.deviceId, 'commandId': incCmd, 'value': incTarget},
		],
	}
	if arg != 0:
		control['arg'] = arg
	control['elementName'] = ctx.elemKey
	return {canonical: control}


def iffRelativeKnob(elem, indices, ctx):
	"""Handles IFF_multiposition_spring_switch (UH-1H delta-step knob variant).

	Two BTN sub-controls with the same commandId, NO stopAction, and ±1 delta
	argValues.  The C++ device interprets ±1 as advance/retreat one step.
	Modeled as type=relative with sendProtocol=C so scripts send ±1 directly.

	Contrast with btnPulseCounter, which handles the A-10C variant of
	IFF_multiposition_spring_switch that DOES have a stopAction and is modeled
	as type=relative, wheel=True (matching the detectBtnPulseCounter path in
	the structural dispatch).
	"""
	result = detectIFFMultipositionSpring(elem, indices)
	if not result:
		return None
	incIdx, decIdx = result

	actions = elem.get('action', [])
	argValues = elem.get('argValue', [])
	args = elem.get('arg', [])

	actionId = actions[incIdx] if incIdx < len(actions) else 0
	if not actionId:
		return None

	incValue = round(argValues[incIdx], 6) if incIdx < len(argValues) else 1.0
	arg = args[incIdx] if incIdx < len(args) else 0
	canonical = ctx.canonical(actionId, arg)
	control = {
		**ctx.meta(),
		'type': 'relative',
		'deviceId': ctx.deviceId,
		'commandId': actionId,
		'argLim': [-1.0, 1.0],
		'incValue': incValue,
		'sendProtocol': 'C',
	}
	if arg != 0:
		control['arg'] = arg
	control['elementName'] = ctx.elemKey
	return {canonical: control}


def btnPulseCounter(elem, indices, ctx):
	"""Handles IFF_multiposition_spring_switch (A-10C BTN pulse-counter variant).

	Two BTN sub-controls with the SAME commandId, SAME argLims, symmetric
	±argValues, and a non-zero stopAction on at least one sub-control.  Each
	click sends a delta (e.g. −0.1 to advance one step, +0.1 to retreat) and
	DCS springs the arg back to zero.  Multiple clicks accumulate position.

	Modeled identically to radio_wheel (type=relative, wheel=True) because the
	script layer treats both the same way: send the incrementValue/decrementValue
	once per click.  argLim comes from the incIdx sub-control's argLim and
	reflects the full range of the underlying arg.

	Contrast with iffRelativeKnob, which handles the UH-1H variant that has
	no stopAction and uses detectIFFMultipositionSpring instead.
	"""
	result = detectBtnPulseCounter(elem, indices)
	if not result:
		return None
	incIdx, decIdx = result

	actions = elem.get('action', [])
	argValues = elem.get('argValue', [])
	argLims = elem.get('argLim', [])
	args = elem.get('arg', [])

	actionId = actions[incIdx] if incIdx < len(actions) else 0
	if not actionId:
		return None

	incValue = round(argValues[incIdx], 6) if incIdx < len(argValues) else -0.1
	decValue = round(argValues[decIdx], 6) if decIdx < len(argValues) else 0.1
	lim = argLims[incIdx] if incIdx < len(argLims) else [0.0, 1.0]
	argLim = [round(lim[0], 6), round(lim[1], 6)] if isinstance(lim, list) and len(lim) == 2 else [0.0, 1.0]
	arg = args[incIdx] if incIdx < len(args) else 0

	canonical = ctx.canonical(actionId, arg)
	control = {
		**ctx.meta(),
		'type': 'relative',
		'wheel': True,
		'deviceId': ctx.deviceId,
		'commandId': actionId,
		'argLim': argLim,
		'incrementValue': incValue,
		'decrementValue': decValue,
	}
	if arg != 0:
		control['arg'] = arg
	control['elementName'] = ctx.elemKey
	return {canonical: control}


def pdpSpecial(elem, indices, ctx):
	"""Handles pdp_special (CH-47F PDP circuit-breaker push/pull pattern).

	Two BTN sub-controls sharing the same commandId, each with a stopAction.
	ArgValues are asymmetric: pullIdx has the larger value (e.g. 0.9, triggers
	the pull-out transient) and pushIdx has the smaller value (e.g. 0.6, the
	stable push-in readback).

	Produces type=discrete with a 2-entry positionMap using sendValue/readbackValue
	fields (unlike the standard positionMap value= fields used by binaryToggle etc.):
	  pos 0: send pushVal, readback pushVal    (CB pushed in)
	  pos 1: send pullVal, readback argLim[1]  (CB pulled out; device snaps to 1.0)
	"""
	result = detectPdpSpecial(elem, indices)
	if not result:
		return None
	pullIdx, pushIdx = result

	actions = elem.get('action', [])
	argValues = elem.get('argValue', [])
	argLims = elem.get('argLim', [])
	args = elem.get('arg', [])

	actionId = actions[pullIdx] if pullIdx < len(actions) else 0
	if not actionId:
		return None

	pushVal = round(argValues[pushIdx], 6) if pushIdx < len(argValues) else 0.6
	pullSendVal = round(argValues[pullIdx], 6) if pullIdx < len(argValues) else 0.9
	lim = argLims[pullIdx] if pullIdx < len(argLims) else None
	pullReadbackVal = round(lim[1], 6) if isinstance(lim, list) and len(lim) == 2 else 1.0
	arg = args[pullIdx] if pullIdx < len(args) else 0

	posMap = [
		{
			'deviceId': ctx.deviceId,
			'commandId': actionId,
			'sendValue': pushVal,
			'readbackValue': pushVal,
		},
		{
			'deviceId': ctx.deviceId,
			'commandId': actionId,
			'sendValue': pullSendVal,
			'readbackValue': pullReadbackVal,
		},
	]

	canonical = ctx.canonical(actionId, arg)
	control = {
		**ctx.meta(),
		'type': 'discrete',
		'positions': 2,
		'positionMap': posMap,
	}
	if arg != 0:
		control['arg'] = arg
	control['elementName'] = ctx.elemKey
	return {canonical: control}


def wheelControl(elem, indices, ctx):
	"""Handles radio_wheel_1 / radio_wheel: increment/decrement encoder wheel.

	Two TUMB sub-controls with relative=True, symmetric ±step argValues, matching
	argLims.  Same commandId (radio_wheel_1 Mi-8/Mi-24 pattern) or different
	commandIds (radio_wheel A-10C pattern).

	Produces type=relative, wheel=True with incrementValue/decrementValue and
	optional displayArgs.  Matches the 'wheel' branch in
	generateControlMapping.processElements().
	"""
	result = detectWheel(elem, indices)
	if not result:
		return None
	incIdx, decIdx = result

	actions = elem.get('action', [])
	argValues = elem.get('argValue', [])
	argLims = elem.get('argLim', [])
	args = elem.get('arg', [])

	actionId = actions[incIdx] if incIdx < len(actions) else 0
	decActionId = actions[decIdx] if decIdx < len(actions) else 0
	if not actionId:
		return None

	incValue = round(argValues[incIdx], 6) if incIdx < len(argValues) else 0.1
	decValue = round(argValues[decIdx], 6) if decIdx < len(argValues) else -0.1
	lim = argLims[incIdx] if incIdx < len(argLims) else [0.0, 1.0]
	argLim = [round(lim[0], 6), round(lim[1], 6)] if isinstance(lim, list) and len(lim) == 2 else [0.0, 1.0]
	arg = args[incIdx] if incIdx < len(args) else 0

	canonical = ctx.canonical(actionId, arg)
	control = {
		**ctx.meta(),
		'type': 'relative',
		'wheel': True,
		'deviceId': ctx.deviceId,
		'commandId': actionId,
		'argLim': argLim,
		'incrementValue': incValue,
		'decrementValue': decValue,
	}
	if decActionId != actionId:
		control['decrementCommandId'] = decActionId
	if arg != 0:
		control['arg'] = arg

	slaveAnim = elem.get('slaveAnimation') or []
	hasDisplayArgs = False
	if incIdx < len(slaveAnim):
		chain = slaveAnim[incIdx]
		if chain and chain != [arg]:
			control['displayArgs'] = list(chain)
			hasDisplayArgs = True

	dispScale = 1.0
	if hasDisplayArgs:
		slaveArgLim = elem.get('slaveArgLim') or []
		slaveArgScale = elem.get('slaveArgScale') or []
		if incIdx < len(slaveArgLim) and slaveArgLim[incIdx]:
			dispLim = slaveArgLim[incIdx][0]
			if dispLim is not None:
				control['argLim'] = [round(dispLim[0], 6), round(dispLim[1], 6)]
		if incIdx < len(slaveArgScale) and slaveArgScale[incIdx]:
			s = slaveArgScale[incIdx][0]
			if s is not None:
				dispScale = s

	if abs(dispScale - 1.0) > 1e-9:
		control['step'] = round(abs(incValue) * dispScale, 6)

	animSpeedList = elem.get('animationSpeed') or []
	if incIdx < len(animSpeedList) and animSpeedList[incIdx]:
		speed = animSpeedList[incIdx]
		if speed > 0:
			displayStep = abs(incValue) * dispScale
			settleDelay = round(displayStep / speed, 3)
			if settleDelay > 0:
				control['settleDelay'] = settleDelay

	control['elementName'] = ctx.elemKey
	return {canonical: control}


def relativeAxis(elem, indices, ctx):
	"""Handles a relative LEV axis (e.g. multiposition_switch_axis).

	A single LEV sub-control with relative=True; the C++ device adds the sent
	value as a delta.  Scripts send a signed click count and DCS advances the
	arg by that many steps.  Modeled as type=relative with sendProtocol=C,
	matching classifyType('LEV', True) in the structural dispatch.
	"""
	i = indices[0]
	actions = elem.get('action', [])
	argLims = elem.get('argLim', [])
	args = elem.get('arg', [])

	actionId = actions[i] if i < len(actions) else 0
	if not actionId:
		return None

	arg = args[i] if i < len(args) else 0
	lim = argLims[i] if i < len(argLims) else [0.0, 1.0]
	argLim = [round(lim[0], 6), round(lim[1], 6)] if isinstance(lim, list) and len(lim) == 2 else [0.0, 1.0]

	canonical = ctx.canonical(actionId, arg)
	control = {
		**ctx.meta(),
		'type': 'relative',
		'deviceId': ctx.deviceId,
		'commandId': actionId,
	}
	if arg != 0:
		control['arg'] = arg
	control['argLim'] = argLim
	control['sendProtocol'] = 'C'
	control['elementName'] = ctx.elemKey
	return {canonical: control}


def rotaryWithMomentary(elem, indices, ctx):
	"""Handles a multi-position rotary latch with momentary BTN extension(s).

	Pattern: a TUMB sub-control with step < range (the latch) plus one or more
	BTN sub-controls with stopAction set (momentary) that extend the rotary
	range by one step below (extendLow) or above (extendHigh) the latch's argLim.

	Emits a single discrete control with a positionMap covering all latch
	positions plus each momentary-extended position, all using the latch's
	commandId.  Matches the 'rotary+momentary' branch in
	generateControlMapping.processElements().

	Example: AH-64D wiper_multiposition_spring_switch — TUMB covering OFF/LO/HI
	(argLim=[-0.1,0.2], step=0.1) + BTN for PARK (momentary, argValue=-0.1,
	extendLow=True) → lowBound=-0.2, 5 positions [-0.2,-0.1,0.0,0.1,0.2].
	"""
	stops = elem.get('stopAction', [])
	classes = elem.get('controlClass', [])
	argValues = elem.get('argValue', [])
	argLims = elem.get('argLim', [])
	actions = elem.get('action', [])
	args = elem.get('arg', [])

	# Separate the TUMB latch (stopAction absent or 0) from momentary BTNs.
	latchIdx = None
	momentaryIndices = []
	for i in indices:
		stop = stops[i] if i < len(stops) else 0
		cls = classes[i] if i < len(classes) else ''
		if stop == 0 and cls in ('TUMB', 'MULTY_TUMB'):
			latchIdx = i
		else:
			momentaryIndices.append(i)

	if latchIdx is None or not momentaryIndices:
		return None

	lim = argLims[latchIdx] if latchIdx < len(argLims) else None
	val = argValues[latchIdx] if latchIdx < len(argValues) else None
	if not isinstance(lim, list) or len(lim) != 2:
		return None
	if val is None or val == 0:
		return None

	step = round(abs(val), 6)
	rng = lim[1] - lim[0]
	# Require multiple latched positions (step < range) to distinguish from a
	# classic 2-position toggle that would fall to the simpleDiscrete path.
	if step <= 0 or step >= rng - 1e-9:
		return None

	extendLow = any(
		(argValues[mi] if mi < len(argValues) else 0) < 0
		for mi in momentaryIndices
	)
	extendHigh = any(
		(argValues[mi] if mi < len(argValues) else 0) > 0
		for mi in momentaryIndices
	)

	lowBound = round(lim[0] - step, 6) if extendLow else round(lim[0], 6)
	highBound = round(lim[1] + step, 6) if extendHigh else round(lim[1], 6)
	numPositions = round((highBound - lowBound) / step) + 1

	actionId = actions[latchIdx] if latchIdx < len(actions) else 0
	if not actionId:
		return None

	arg = args[latchIdx] if latchIdx < len(args) else 0
	posMap = []
	for p in range(numPositions):
		v = round(lowBound + p * step, 6)
		posMap.append({
			'deviceId': ctx.deviceId,
			'commandId': actionId,
			'value': v,
		})

	canonical = ctx.canonical(actionId, arg)
	control = {
		**ctx.meta(),
		'type': 'discrete',
		'positions': numPositions,
		'positionMap': posMap,
	}
	if arg != 0:
		control['arg'] = arg
	control['elementName'] = ctx.elemKey
	return {canonical: control}


def buttonOrAxis(elem, indices, ctx):
	"""Handles default_button_axis / intercom_rotate_tumb (mixed BTN+LEV or TUMB+LEV).

	When this element is processed, the dispatch loop groups sub-controls by arg,
	so this archetype is called ONCE per arg group.  It inspects the control class
	of indices[0] and delegates:
	  BTN/TUMB → simpleDiscrete  (momentary button or discrete switch)
	  LEV       → continuousAxis  (continuous axis)
	"""
	classes = elem.get('controlClass', [])
	i = indices[0]
	cls = classes[i] if i < len(classes) else 'BTN'
	if cls in ('LEV', 'MOVABLE_LEV'):
		return continuousAxis(elem, indices, ctx)
	return simpleDiscrete(elem, indices, ctx)


def wheelOrDiscrete(elem, indices, ctx):
	"""Handles helpers that can be either a wheel or a plain discrete per-element.

	Suitable for multiposition_switch_1_side and similar helpers where most
	instances are non-relative TUMB discrete rotaries but a small number are
	relative TUMB wheels (e.g. A-10C VHF preset selectors).

	Tries wheelControl first; if detectWheel does not match (element is not
	relative), falls through to simpleDiscrete.
	"""
	result = wheelControl(elem, indices, ctx)
	if result is not None:
		return result
	return simpleDiscrete(elem, indices, ctx)


def wheelOrContinuous(elem, indices, ctx):
	"""Handles helpers with two arg groups: a TUMB wheel and a relative LEV axis.

	Suitable for radio_wheel_double (Mi-8 Jadro-1A frequency selector):
	  - TUMB+TUMB group (relative=True, same cmd): detectWheel matches → wheel.
	  - LEV group (relative=True, different cmd): detectWheel fails (not TUMB)
	    → falls through to continuousAxis → type=relative, sendProtocol=C.

	Tries wheelControl first; if detectWheel does not match, falls through to
	continuousAxis.
	"""
	result = wheelControl(elem, indices, ctx)
	if result is not None:
		return result
	return continuousAxis(elem, indices, ctx)


# ─── Archetype dispatch ───────────────────────────────────────────────────────

def _buildControls(elements, helperMap, deviceTableMap, perTableReverse, globalUnique, devNameById, devices):
	"""Dispatch elements to archetype functions or structural fallback.

	Elements whose helper field maps to a non-None callable in helperMap use the
	archetype function.  All other elements (untagged or STRUCTURAL_FALLBACK) are
	passed to processElements() from generateControlMapping.

	Returns (controls dict, warnings list), same shape as processElements().
	"""
	# Partition: archetype-dispatched vs. structural fallback.
	archetypeElems = {}
	fallbackElems = {}
	for elemKey, elem in elements.items():
		helper = elem.get('helper')
		if helper and helperMap.get(helper) is not None:
			archetypeElems[elemKey] = elem
		else:
			fallbackElems[elemKey] = elem

	# Process structural-fallback elements (untagged inline tables and any
	# STRUCTURAL_FALLBACK-mapped helpers).
	controls, warnings = processElements(
		fallbackElems, deviceTableMap, perTableReverse, globalUnique, devNameById, devices,
	)
	fallbackCanonicals = set(controls.keys())

	# Process archetype-dispatched elements.
	canonicalElemKeys = {}
	for elemKey, elem in archetypeElems.items():
		helper = elem.get('helper')
		archetypeFn = helperMap[helper]
		deviceId = elem.get('device')
		args = elem.get('arg', [])
		actions = elem.get('action', [])
		hint = elem.get('hint', '')
		hintKey = elem.get('hintKey', '')
		crewAccess = elem.get('crewAccess')

		# Group sub-controls by arg number, same as processElements() does.
		argGroups = {}
		for i, arg in enumerate(args):
			if i >= len(actions):
				break
			argGroups.setdefault(arg, []).append(i)

		# Some Lua helpers (e.g. multiswitch_stop, base_btn_cycle3) do not store
		# an arg in the returned table, so args=[] and the loop above produces
		# nothing. Fall back to a single group at arg=0 covering all action indices
		# so the element is not silently dropped.
		if not argGroups and actions:
			argGroups = {0: list(range(len(actions)))}

		multipleArgGroups = len(argGroups) > 1

		for arg, indices in argGroups.items():
			ctx = _Ctx(
				elemKey, deviceId, devNameById, deviceTableMap,
				perTableReverse, globalUnique, multipleArgGroups,
				hint, hintKey, crewAccess,
			)
			result = archetypeFn(elem, indices, ctx)
			if not result:
				continue
			for canonical, control in result.items():
				if canonical in fallbackCanonicals:
					warnings.append(
						f'Archetype/fallback collision: {canonical!r} from {elemKey!r} '
						f'conflicts with a structural-fallback-derived canonical; kept fallback entry.'
					)
					continue
				existing = canonicalElemKeys.get(canonical)
				if existing is not None:
					# Alphabetically-first elemKey wins, matching processElements() tie-break.
					if elemKey < existing:
						controls[canonical] = control
						canonicalElemKeys[canonical] = elemKey
						warnings.append(f'Canonical collision: {canonical!r} — replaced with {elemKey!r}')
					else:
						warnings.append(f'Canonical collision: {canonical!r} — kept {existing!r}')
				else:
					controls[canonical] = control
					canonicalElemKeys[canonical] = elemKey

	return controls, warnings


def runMapping(moduleName, helperMap, existingFile='auto', extractionName=None):
	"""Run the full control-mapping pipeline for one DCS module.

	Args:
		moduleName:     DCS internal module name, e.g. 'AH-64D_BLK_II'.  The
		                output is written to config/controlMappings/<moduleName>.json
		                and the 'moduleName' field in the JSON is set to this value.
		helperMap:      Dict {helperFunctionName: callable | None}.  Every Lua
		                helper name tagged in the extraction MUST have an entry.
		                Use STRUCTURAL_FALLBACK (None) for helpers where the
		                existing structural dispatch chain is correct.  An unknown
		                helper causes an error exit so new helpers are never
		                silently misclassified.
		existingFile:   Path to the existing controlMappings JSON for sendProtocol
		                override preservation.  Pass None to skip preservation.
		                'auto' (default) resolves to the output path so in-place
		                regeneration preserves overrides automatically.
		extractionName: Install-directory name used to locate the extraction file,
		                e.g. 'AH-64D' when moduleName is 'AH-64D_BLK_II'.
		                Defaults to moduleName when the two names are the same.
	"""
	inputName = extractionName or moduleName
	extractionPath = os.path.join('config', 'nativeExtractions', f'{inputName}.json')
	with open(extractionPath, encoding='utf-8') as f:
		extraction = json.load(f)

	devices = extraction.get('devices', {})
	commandTables = extraction.get('commandTables', {})
	elements = extraction.get('elements', {})
	indicators = extraction.get('indicators', [])
	gaugesAndLamps = extraction.get('gaugesAndLamps', [])
	devNameById = {v: k for k, v in devices.items()}

	# Step 0: Validate that every tagged helper has an entry in helperMap.
	# An unregistered helper means generation would silently fall through to
	# structural inference (potentially wrong).  Fail loudly instead.
	seenHelpers = {e.get('helper') for e in elements.values() if e.get('helper')}
	unhandledHelpers = seenHelpers - set(helperMap.keys())
	if unhandledHelpers:
		print(f'ERROR: {moduleName}: helpers not registered in HELPER_MAP:')
		for helper in sorted(unhandledHelpers):
			count = sum(1 for e in elements.values() if e.get('helper') == helper)
			print(f'  {helper!r}: {count} element(s)')
		scriptName = f'map_{moduleName.replace("-", "")}.py'
		print(f'Add these entries to HELPER_MAP in tools/{scriptName}.')
		sys.exit(1)

	# Step 1: Match devices to command tables (same logic as generateControlMapping.py).
	deterministicMap = {int(k): v for k, v in (extraction.get('deviceTableMap') or {}).items()}
	deviceTableMap = dict(deterministicMap)
	sourceCounts = {'deterministic': len(deterministicMap), 'nameSim': 0, 'evidence': 0}

	nameSimMap = buildDeviceTableMap(devices, commandTables)
	for devId, tblName in nameSimMap.items():
		if devId not in deviceTableMap:
			deviceTableMap[devId] = tblName
			sourceCounts['nameSim'] += 1

	evidenceMap = inferDeviceTableMapByEvidence(elements, commandTables, devNameById)
	for devId, tblName in evidenceMap.items():
		if devId not in deviceTableMap:
			deviceTableMap[devId] = tblName
			sourceCounts['evidence'] += 1

	perTableReverse, globalUnique = buildCommandReverse(commandTables)

	unmatchedDevices = set(devNameById.keys()) - set(deviceTableMap.keys())
	print(
		f'Device-table matching: {len(deviceTableMap)}/{len(devNameById)} devices matched '
		f'(deterministic={sourceCounts["deterministic"]}, '
		f'name-similarity={sourceCounts["nameSim"]}, '
		f'evidence={sourceCounts["evidence"]})'
	)
	if unmatchedDevices:
		for devId in sorted(unmatchedDevices):
			print(f'  Unmatched: device {devId} ({devNameById.get(devId, "?")})')

	# Build argToGaugeInput before processing elements so controls whose send arg
	# is shared with a gauge/lamp can be annotated with indicatorArgLim.
	argToGaugeInput = {
		g['arg']: g['input']
		for g in gaugesAndLamps
		if isinstance(g.get('input'), list) and len(g['input']) >= 2
	}

	# Step 2: Process elements into controls.
	# Elements with a non-None archetype in helperMap use explicit dispatch;
	# all others (untagged or STRUCTURAL_FALLBACK) use the structural chain.
	controls, warnings = _buildControls(
		elements, helperMap, deviceTableMap, perTableReverse, globalUnique, devNameById, devices,
	)

	indicatorArgLimCount = annotateIndicatorArgLim(controls, argToGaugeInput)
	if indicatorArgLimCount:
		print(f'indicatorArgLim: {indicatorArgLimCount} controls annotated (send/read arg shared)')

	rawControls = processRawCommands(commandTables, deviceTableMap, devices, elements, controls, extraction.get('keybindings'), extraction.get('listenedCommands'))
	controls.update(rawControls)
	if rawControls:
		print(f'Raw controls: {len(rawControls)} unbound commands emitted (type=raw)')

	# Step 3: Process indicators into read-only entries.
	indicatorControls = processIndicators(indicators)
	for canonical, ctrl in indicatorControls.items():
		if canonical in controls:
			existing = controls[canonical]
			if 'indicationId' not in existing:
				existing['indicationId'] = ctrl['indicationId']
				existing['fieldName'] = ctrl['fieldName']
		else:
			controls[canonical] = ctrl

	# Step 3b: Process gauges and lamps into read-only entries.
	gaugeControls = processGaugesAndLamps(gaugesAndLamps)
	elementArgs = {
		ctrl.get('arg')
		for ctrl in controls.values()
		if ctrl.get('arg') is not None and 'type' in ctrl
	}
	gaugeSkipped = 0
	for canonical, ctrl in gaugeControls.items():
		if ctrl.get('arg') in elementArgs or canonical in controls:
			gaugeSkipped += 1
			continue
		controls[canonical] = ctrl

	print(
		f'Gauges/lamps: {len(gaugeControls)} extracted, {gaugeSkipped} skipped (arg overlap), '
		f'{len(gaugeControls) - gaugeSkipped} merged'
	)

	# Step 4: Preserve explicit sendProtocol overrides from existing mapping.
	outFile = os.path.join('config', 'controlMappings', f'{moduleName}.json')
	resolvedExisting = outFile if existingFile == 'auto' else existingFile
	preservedCount = preserveExistingSendProtocol(controls, resolvedExisting, moduleName)
	if preservedCount:
		print(f'Preserved {preservedCount} sendProtocol overrides from {resolvedExisting}')

	# Step 5: Write output (alphabetically sorted, matching generateControlMapping.py).
	sortedControls = dict(sorted(controls.items()))
	output = {'moduleName': moduleName, 'controls': sortedControls}

	os.makedirs(os.path.dirname(outFile), exist_ok=True)
	with open(outFile, 'w', encoding='utf-8') as f:
		json.dump(output, f, indent='\t', ensure_ascii=False, sort_keys=True)

	# Step 6: Print summary.
	typeCounts = {}
	commandable = 0
	readable = 0
	readOnly = 0
	hasPositionMap = 0
	for ctrl in controls.values():
		t = ctrl.get('type', 'read-only')
		typeCounts[t] = typeCounts.get(t, 0) + 1
		if 'type' in ctrl:
			commandable += 1
		if 'arg' in ctrl or 'indicationId' in ctrl:
			readable += 1
		if 'type' not in ctrl:
			readOnly += 1
		if 'positionMap' in ctrl:
			hasPositionMap += 1

	print(f'\nModule: {moduleName}')
	print(f'Total controls: {len(controls)}')
	print(f'  Commandable: {commandable}')
	print(f'  Readable: {readable}')
	print(f'  Read-only: {readOnly}')
	print(f'  With positionMap: {hasPositionMap}')
	print('Types:')
	for t, c in sorted(typeCounts.items()):
		print(f'  {t}: {c}')

	if warnings:
		print(f'\nWarnings ({len(warnings)}):')
		for w in warnings:
			print(f'  {w}')

	posMapControls = [(name, ctrl) for name, ctrl in sortedControls.items() if 'positionMap' in ctrl]
	if posMapControls:
		print(f'\nReview: {len(posMapControls)} positionMap controls (multiple commands on same arg):')
		for name, ctrl in posMapControls:
			print(f'  {name}: {ctrl.get("description", "")}')

	print(f'\nOutput: {outFile}')
