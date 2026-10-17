#!/usr/bin/env python
"""Generate canonical control mapping from nativeExtraction JSON.

Reads a nativeExtraction JSON file (from per-module extraction scripts)
and produces:

  config/controlMappings/<moduleName>.json

Each control is keyed by a canonical identifier derived verbatim from the DCS
Lua sources:
  cmd-backed element  → '<deviceName>.<cmdName>'  (e.g. 'APU.ControlSw')
  positionMap element → '<deviceName>.<firstCmdName>'
  cmd-missing element → '<deviceName>.cmd_<cmdId>'
  gauge / lamp        → 'arg.<N>'
  indicator field     → 'ind.<indicationId>.<fieldName>'

Scripts reference these canonical names directly (see ARCHITECTURE.md,
*Naming Policy*).  There is no runtime alias layer.

The generator overwrites the live mapping in place.  Before writing, it reads
the existing file (when explicitly passed via --existing) so that manual
`sendProtocol` overrides survive regeneration — see preserveExistingSendProtocol().

Usage:
	python generateControlMapping.py [extractionFile] [--module-name NAME] [--existing FILE]
	--module-name: Override output module name (default: from extraction JSON)
	--existing:    Existing mapping for sendProtocol-override preservation
	               (defaults to the output path so in-place regeneration
	               preserves overrides automatically).
"""

import argparse
import json
import os
import re
import sys

from commandVariants import inferDeviceTableMapByEvidence


# ─── Device ↔ command table matching ─────────────────────────────────────────

def normalizeForMatch(name, stripSuffixes=None):
	"""Lowercase, strip given suffixes, remove underscores."""
	result = name.lower()
	for suffix in (stripSuffixes or []):
		result = result.replace(suffix, '')
	return result.replace('_', '')


# Known DCS command table abbreviation → expanded device name form.
TABLE_ABBREV = {
	'ctrl': 'control',
	'hydro': 'hydraulic',
	'antsel': 'antennaselector',
	'mpd': 'mfd',
}


def expandTableAbbreviations(tableNorm):
	"""Expand known abbreviations in a normalized table name."""
	for abbr, expansion in TABLE_ABBREV.items():
		if tableNorm == abbr or tableNorm.startswith(abbr):
			return expansion + tableNorm[len(abbr):]
	return tableNorm


def buildDeviceTableMap(devices, commandTables):
	"""Map each device ID to its best-matching command table name.

	Uses name similarity between device names and table names.
	Multiple devices can share a table (e.g. MDI_LEFT and MDI_RIGHT → MDI_commands).
	Returns {deviceId: tableName} for matched devices.
	"""
	devNameById = {v: k for k, v in devices.items()}
	tableNames = list(commandTables.keys())

	tableNorms = {t: normalizeForMatch(t, ['_commands']) for t in tableNames}
	tableExpanded = {t: expandTableAbbreviations(n) for t, n in tableNorms.items()}

	deviceTableMap = {}

	for devId in sorted(devNameById):
		devName = devNameById[devId]
		devNorm = normalizeForMatch(devName, ['_interface', '_mechanics'])

		bestMatch = None
		bestScore = 0

		for tableName in tableNames:
			tableNorm = tableNorms[tableName]
			tableExp = tableExpanded[tableName]
			score = 0

			# Exact match (after normalization or abbreviation expansion).
			if devNorm == tableNorm or devNorm == tableExp:
				score = 2.0
			# Prefix: device starts with table base.
			elif devNorm.startswith(tableNorm) and len(tableNorm) >= 3:
				score = 1.0 + len(tableNorm) / len(devNorm)
			elif devNorm.startswith(tableExp) and len(tableExp) >= 3:
				score = 1.0 + len(tableExp) / len(devNorm)
			# Prefix: table starts with device base.
			elif tableNorm.startswith(devNorm) and len(devNorm) >= 3:
				score = 1.0 + len(devNorm) / len(tableNorm)
			elif tableExp.startswith(devNorm) and len(devNorm) >= 3:
				score = 1.0 + len(devNorm) / len(tableExp)

			if score > bestScore:
				bestScore = score
				bestMatch = tableName

		if bestMatch and bestScore >= 1.0:
			deviceTableMap[devId] = bestMatch

	return deviceTableMap


# ─── Command name resolution ─────────────────────────────────────────────────

def buildCommandReverse(commandTables):
	"""Build reverse lookup tables.

	Returns:
	  perTable: {tableName: {commandId: commandName}}
	  globalUnique: {commandId: commandName} — only for IDs unique across all tables
	"""
	perTable = {}
	globalAll = {}
	for tableName, cmds in commandTables.items():
		rev = {}
		for cmdName, cmdId in cmds.items():
			# Prefer base names over _EXT/_AXIS/_ITER variants.
			if cmdId in rev:
				existing = rev[cmdId]
				if any(existing.endswith(s) for s in ('_EXT', '_AXIS', '_ITER')):
					rev[cmdId] = cmdName
			else:
				rev[cmdId] = cmdName

			if cmdId not in globalAll:
				globalAll[cmdId] = set()
			globalAll[cmdId].add(cmdName)
		perTable[tableName] = rev

	# Global unique: commandIds that resolve to exactly one base name.
	globalUnique = {}
	for cmdId, names in globalAll.items():
		baseNames = {n for n in names if not any(n.endswith(s) for s in ('_EXT', '_AXIS', '_ITER'))}
		if len(baseNames) == 1:
			globalUnique[cmdId] = next(iter(baseNames))

	return perTable, globalUnique


def resolveCommandName(deviceId, commandId, deviceTableMap, perTableReverse, globalUnique):
	"""Resolve (deviceId, commandId) → (command name, table name).

	Strategy:
	1. Look up in the device's matched command table.
	2. If no match, try global unique lookup (table name is None).
	3. Return (None, None) if ambiguous (caller falls back to hint text).
	"""
	tableName = deviceTableMap.get(deviceId)
	if tableName and tableName in perTableReverse:
		name = perTableReverse[tableName].get(commandId)
		if name:
			return name, tableName

	return globalUnique.get(commandId), None


def makeCanonicalName(deviceId, commandId, devNameById, deviceTableMap, perTableReverse, globalUnique, elementKey=None):
	"""Build the canonical key '<deviceName>.<cmdName>' for a cmd-backed control.

	Falls back to '<deviceName>.cmd_<id>' when the cmd name cannot be resolved
	from command_defs. Device name uses 'dev<id>' if no entry exists.

	When the resolved command name comes from the legacy 'device_commands'
	shared table - the ED convention (Mi-8MTV2) where every device routes
	through one global `device_commands` table indexed by button number with
	no per-device semantic meaning - the element key carries far more
	information than 'Button_<N>' does.  In that case we substitute the
	element key verbatim (preserving any hyphens DCS uses) so the canonical
	preserves the panel/control identifier DCS itself uses, and we avoid
	collisions when several elements share one button-id (e.g. the four
	clickable hotspots making up a wiper rotary switch).

	This substitution does NOT fire for device-specific tables that happen
	to contain Button_N entries (e.g. AV-8B's `mpcd_l_commands.Button_01`),
	where the device + button number is a meaningful identifier on its own.
	"""
	devName = devNameById.get(deviceId, f'dev{deviceId}')
	cmdName, tableName = resolveCommandName(deviceId, commandId, deviceTableMap, perTableReverse, globalUnique)
	if cmdName and tableName == 'device_commands' and elementKey:
		cmdName = elementKey
	if cmdName:
		return f'{devName}.{cmdName}'
	return f'{devName}.cmd_{commandId}'


# ─── Element processing ──────────────────────────────────────────────────────

def classifyType(controlClass, isRelative):
	"""Map controlClass + relative flag to unified type.

	Only LEV/MOVABLE_LEV controlClasses become continuous/relative — their
	'relative' flag selects which.  All other controlClasses (including
	TUMB rotary selectors with relative=true, like the Mi-24P Jadro radio
	dials) are emitted as 'discrete' with a computed step.  This matches
	the Mi-24P dedicated generator's behavior (live-validated at
	1002/30/162); treating TUMB+relative as 'relative' type breaks script
	expectations in consumers that key off `type == 'discrete'`.
	"""
	if controlClass in ('LEV', 'MOVABLE_LEV'):
		return 'relative' if isRelative else 'continuous'
	return 'discrete'

def computeStepAndPositions(argLim, argValue):
	"""Compute step size and position count for a discrete control."""
	rng = argLim[1] - argLim[0]
	if rng <= 0:
		return 1.0, 2

	step = abs(argValue) if argValue and argValue != 0 else rng
	if step <= 0 or step > rng:
		return round(rng, 6), 2

	positions = round(rng / step) + 1
	return round(step, 6), max(positions, 2)


def isPositionMapElement(elem, argGroupIndices):
	"""Detect if sub-controls at these indices form a springloaded positionMap.

	Returns True when 2+ sub-controls on the same arg have DIFFERENT action
	IDs (classic multi-command springloaded switch).

	Elements where 2+ sub-controls on the same arg share a SINGLE action ID
	(with opposing-signed argValues, e.g. cmd 3005 called with -1 and +1)
	are NOT positionMaps — the single command itself handles both directions
	via its argValue parameter, so these collapse to a plain discrete control
	with argLim, step, and positions computed from the argValue magnitudes.
	This is the "uniform-arithmetic-collapse" behavior that matches what the
	Mi-24P dedicated generator produced before migration to the shared
	generator (live-validated at 1002/30/162).
	"""
	if len(argGroupIndices) < 2:
		return False

	actions = {elem['action'][i] for i in argGroupIndices}
	return len(actions) >= 2


def detectRotaryWithMomentary(elem, argGroupIndices):
	"""Detect a multi-position rotary latch combined with momentary button(s) on the same arg.

	This pattern appears in DCS clickabledata as several sub-controls that share
	one arg: a TUMB latch with a fine step that covers several positions, plus
	one or more BTN entries that are momentary (non-zero stopAction) extending
	the arg range above or below the latch's own limits.  The canonical example
	is the F-16C FUEL QTY SEL knob: TUMB on commandId 3005 with argValue 0.1
	covering arg 158 in [0.1, 0.5] (NORM/RSVR/INT WING/EXT WING/EXT CTR), plus
	BTN on commandId 3006 with negative argValue that drives the arg to 0.0
	(TEST, momentary).  The correct model is a single 6-position rotary using
	the latch's (deviceId, commandId) with positions 0.0–0.5.

	Returns (latchIdx, extendLow, extendHigh) if the pattern matches, else None.
	The latch must be a proper multi-position rotary (step < range), otherwise
	this returns None and the caller falls back to the positionMap path which
	handles classic 3-position springloaded switches.
	"""
	if len(argGroupIndices) < 2:
		return None

	stops = elem.get('stopAction', [])
	classes = elem.get('controlClass', [])
	argValues = elem.get('argValue', [])
	argLims = elem.get('argLim', [])

	latchIndices = []
	momentaryIndices = []
	for i in argGroupIndices:
		stop = stops[i] if i < len(stops) else 0
		if stop == 0:
			latchIndices.append(i)
		else:
			momentaryIndices.append(i)

	if not latchIndices or not momentaryIndices:
		return None

	# Prefer a TUMB/MULTY_TUMB latch — these are the real rotary-style entries.
	latchIdx = None
	for i in latchIndices:
		cls = classes[i] if i < len(classes) else ''
		if cls in ('TUMB', 'MULTY_TUMB'):
			latchIdx = i
			break
	if latchIdx is None:
		return None

	lim = argLims[latchIdx] if latchIdx < len(argLims) else None
	val = argValues[latchIdx] if latchIdx < len(argValues) else None
	if not isinstance(lim, list) or len(lim) != 2:
		return None
	if val is None or val == 0:
		return None

	rng = lim[1] - lim[0]
	step = abs(val)
	# Require a multi-position rotary (more than 2 latched positions).  This
	# excludes the classic 3-position springloaded switch (2-position latch +
	# 1 momentary) which the existing positionMap path already handles well.
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

	return latchIdx, extendLow, extendHigh


def detectWheel(elem, argGroupIndices):
	"""Detect a 2-button increment/decrement wheel sharing one (arg, command).

	This is the `radio_wheel_1` pattern in DCS clickabledata: two TUMB sub-
	controls with `relative=true`, both bound to the same arg AND the same
	device+command, with symmetric ±step argValues.  Each sub-control is one
	rotational click direction (CW / CCW).  The arg cycles through positions
	in [argLim[0], argLim[1]] with step magnitude |argValue|.

	Examples:
		Mi-8MT  R-863 PTR-APP-LVR-SEL{1..4}, JADRO-1A PTR-ADDSECPLT-LVR-DIG{3,4,6,12}
		Mi-24P  JADRO-01-PTR (Jadro-1I Frequency)

	Different DCS modules wire these wheels to different runtime handlers:
	some interpret a sent value as the new absolute arg, others as a delta
	to add.  Sending the literal ±argValue declared by the cockpit click
	produces the correct one-step rotation in EITHER case (because that is
	what the cockpit click itself sends).  Treating the wheel as a discrete
	control with absolute targets only works for the absolute-set variant
	and breaks for the relative-add variant.

	Returns (incIdx, decIdx) when the pattern matches, else None.
	"""
	if len(argGroupIndices) != 2:
		return None

	actions = elem.get('action', [])
	classes = elem.get('controlClass', [])
	relatives = elem.get('relative', [])
	argValues = elem.get('argValue', [])
	argLims = elem.get('argLim', [])

	i0, i1 = argGroupIndices

	# Both must be TUMB.
	for i in (i0, i1):
		if (classes[i] if i < len(classes) else '') != 'TUMB':
			return None

	# Both must be relative.
	for i in (i0, i1):
		if not (relatives[i] if i < len(relatives) else False):
			return None

	# argValues must be symmetric and non-zero.
	# Note: both same-command wheels (radio_wheel_1 pattern, Mi-8/Mi-24) and
	# different-command wheels (radio_wheel pattern, A-10C) are accepted here.
	# The relative=true check above is the primary discriminator.
	v0 = argValues[i0] if i0 < len(argValues) else 0
	v1 = argValues[i1] if i1 < len(argValues) else 0
	if not v0 or not v1:
		return None
	if abs(v0 + v1) > 1e-9:
		return None
	if abs(abs(v0) - abs(v1)) > 1e-9:
		return None

	# argLims must match (same cycle range).
	lim0 = argLims[i0] if i0 < len(argLims) else None
	lim1 = argLims[i1] if i1 < len(argLims) else None
	if not (isinstance(lim0, list) and isinstance(lim1, list) and len(lim0) == 2 and len(lim1) == 2):
		return None
	if abs(lim0[0] - lim1[0]) > 1e-9 or abs(lim0[1] - lim1[1]) > 1e-9:
		return None

	# Identify which sub-control is increment (positive argValue) vs decrement.
	if v0 > 0:
		return i0, i1
	return i1, i0


def detectBinaryToggle(elem, argGroupIndices):
	"""Detect a 2-position toggle switch (cover / guard / `animated_guard_switch`).

	The DCS clickabledata helper `animated_guard_switch` (which wraps
	`default_2_position_tumb`) emits TWO TUMB sub-controls bound to the same
	arg and the same (deviceId, commandId), with symmetric ±argValue.  The
	argValue magnitude is the per-frame animation delta (typically 0.01 across
	an argLim of [0, 1]), NOT a multi-position step.  Each cockpit click
	toggles the switch between its two endpoints — DCS's command handler
	treats the click as a binary set, not a step.

	Without this detection these elements fall through to the simple-control
	path, where computeStepAndPositions divides the range by |argValue| and
	produces a bogus 101-position discrete (live-observed on Ka-50 covers:
	e.g. CPT_MECH.AVAR_GEAR_COVER_PTR previously emitted 101 positions with
	step 0.01).

	Detection is keyed off the `helper` field added by extract_*.py via
	extractUtils.installHelperTagger — a structural heuristic alone (TUMB+TUMB
	on same arg+command with symmetric ±argValue) cannot distinguish covers
	from real multi-position rotaries built by `multiposition_switch`, which
	have an identical shape but legitimately span many positions.

	Returns True when the pattern matches, else False.  Caller emits a
	2-position discrete with step = (argLim[1] - argLim[0]) and the shared
	(deviceId, commandId).
	"""
	if elem.get('helper') != 'animated_guard_switch':
		return False

	if len(argGroupIndices) != 2:
		return False

	classes = elem.get('controlClass', [])
	actions = elem.get('action', [])
	argLims = elem.get('argLim', [])

	i0, i1 = argGroupIndices

	# Sanity-check the structural shape we expect from animated_guard_switch.
	for i in (i0, i1):
		if (classes[i] if i < len(classes) else '') != 'TUMB':
			return False
	if actions[i0] != actions[i1]:
		return False

	lim0 = argLims[i0] if i0 < len(argLims) else None
	lim1 = argLims[i1] if i1 < len(argLims) else None
	if not (isinstance(lim0, list) and isinstance(lim1, list) and len(lim0) == 2 and len(lim1) == 2):
		return False
	if abs(lim0[0] - lim1[0]) > 1e-9 or abs(lim0[1] - lim1[1]) > 1e-9:
		return False

	return True


def detectPdpSpecial(elem, argGroupIndices):
	"""Detect a PDP circuit breaker element (CH-47F `pdp_special` helper pattern).

	The `pdp_special` clickabledata helper creates two BTN sub-controls sharing
	the same arg and commandId, both with stop_action set and use_release_message=true.
	argValues are NOT symmetric: sub-control 0 has the larger value (the pull-out
	trigger, e.g. 0.9) and sub-control 1 has the smaller value (the push-in stable
	position, e.g. 0.6).

	The three stable arg states are:
	  - 0.6  CB pushed in  (send argValue[1] = 0.6, readback 0.6)
	  - 1.0  CB pulled out (send argValue[0] = 0.9 + release 0.0 quickly, readback 1.0)
	  - 0.8  CB out+collar (send 0.9, hold >5s, release 0.0, readback 0.8)

	positionMap emits two entries:
	  pos 0: sendValue=argValue[pushIdx], readbackValue=argValue[pushIdx]  (push in)
	  pos 1: sendValue=argValue[pullIdx], readbackValue=argLim[1]          (pull out)

	Collar is omitted from the positionMap — it is a script-level timed operation.

	Returns (pullIdx, pushIdx) when the pattern matches, else None.
	"""
	if elem.get('helper') != 'pdp_special':
		return None

	if len(argGroupIndices) != 2:
		return None

	classes = elem.get('controlClass', [])
	actions = elem.get('action', [])
	argValues = elem.get('argValue', [])
	stops = elem.get('stopAction', [])

	i0, i1 = argGroupIndices

	# Both must be BTN.
	for i in (i0, i1):
		if (classes[i] if i < len(classes) else '') != 'BTN':
			return None

	# Both must share the same command.
	if actions[i0] != actions[i1]:
		return None

	# Both must have a non-zero stopAction.
	for i in (i0, i1):
		if (stops[i] if i < len(stops) else 0) == 0:
			return None

	v0 = argValues[i0] if i0 < len(argValues) else None
	v1 = argValues[i1] if i1 < len(argValues) else None
	if v0 is None or v1 is None or v0 == v1:
		return None

	# pullIdx has the larger argValue (e.g. 0.9 → pulls CB out).
	# pushIdx has the smaller argValue (e.g. 0.6 → pushes CB in, stable readback).
	if v0 > v1:
		return i0, i1  # (pullIdx, pushIdx)
	return i1, i0


def detectBtnPulseCounter(elem, argGroupIndices):
	"""Detect a BTN-class pulse-advance counter (IFF_multiposition_spring_switch pattern).

	Some DCS clickabledata elements implement a multi-position rotary using
	`class_type.BTN` (not TUMB) with a stop_action on the advance direction.
	The canonical example is the A-10C IFF Code selector:
	  - index 0 (left-click  / Z_top):    argValue −0.1, stop_action=cmd, stop_value=0.0
	  - index 1 (right-click / Z_bottom): argValue +0.1, no stop_action
	The C++ device treats any negative sent value as "advance one step" and any
	positive value as "retreat one step" — the magnitude beyond ±step is ignored.
	Arg holds stable position (0.0, 0.1, 0.2, …) between clicks; sending the
	stop_value (0.0) leaves the arg unchanged.

	This is structurally a relative wheel: each click moves one notch, there is
	no absolute-seek mechanism.  We model it identically to the radio_wheel
	pattern (type=relative, wheel=True) with incValue (negative, advances arg)
	and decValue (positive, retreats arg).  Both directions use the same commandId.

	Returns (incIdx, decIdx) when the pattern matches, else None.
	incIdx is the sub-control with the negative argValue (the advance direction).
	"""
	if len(argGroupIndices) != 2:
		return None

	classes = elem.get('controlClass', [])
	actions = elem.get('action', [])
	argValues = elem.get('argValue', [])
	argLims = elem.get('argLim', [])
	stops = elem.get('stopAction', [])

	i0, i1 = argGroupIndices

	# Both must be BTN class.
	for i in (i0, i1):
		if (classes[i] if i < len(classes) else '') != 'BTN':
			return None

	# Both must use the same command (single-command pulse counter).
	if actions[i0] != actions[i1]:
		return None

	# At least one sub-control must have a non-zero stopAction (the spring-return).
	hasStop = any((stops[i] if i < len(stops) else 0) != 0 for i in (i0, i1))
	if not hasStop:
		return None

	# argValues must be symmetric and non-zero.
	v0 = argValues[i0] if i0 < len(argValues) else 0
	v1 = argValues[i1] if i1 < len(argValues) else 0
	if not v0 or not v1:
		return None
	if abs(v0 + v1) > 1e-9:
		return None
	if abs(abs(v0) - abs(v1)) > 1e-9:
		return None

	# argLims must match and be non-trivial (span more than one step).
	lim0 = argLims[i0] if i0 < len(argLims) else None
	lim1 = argLims[i1] if i1 < len(argLims) else None
	if not (isinstance(lim0, list) and isinstance(lim1, list)
			and len(lim0) == 2 and len(lim1) == 2):
		return None
	if abs(lim0[0] - lim1[0]) > 1e-9 or abs(lim0[1] - lim1[1]) > 1e-9:
		return None
	step = abs(v0)
	rng = abs(lim0[1] - lim0[0])
	if rng <= step + 1e-9:
		return None

	# A springloaded rocker (animated_rocker / rocker pattern) has a centered
	# argLim spanning negative to positive (e.g. [-1, 1]).  Genuine pulse
	# counters always start at 0 or above.  Exclude rockers here so they fall
	# through to the simple discrete path which models them correctly as a
	# 3-position control with values [-1, 0, +1].
	if lim0[0] < -1e-9:
		return None

	# Determine the increment direction.  Two distinct conventions exist:
	#
	# 1. Pulse-counter (A-10C IFF pattern): the advance sub-control has a
	#    stop_action; the retreat sub-control does not.  The C++ handler treats
	#    a negative sent value as "advance one step", so incIdx = negative argValue.
	#
	# 2. Direct-delta (DragChuteHandle pattern): BOTH sub-controls have a
	#    stop_action (use_release_message on both sides).  The C++ handler adds
	#    the sent value directly to the arg, so increment = toward argLim[1] =
	#    positive argValue.
	i0HasStop = (stops[i0] if i0 < len(stops) else 0) != 0
	i1HasStop = (stops[i1] if i1 < len(stops) else 0) != 0
	bothHaveStop = i0HasStop and i1HasStop
	if bothHaveStop:
		# Direct-delta: positive argValue = increment (toward argLim[1]).
		if v0 > 0:
			return i0, i1
		return i1, i0
	# Pulse-counter: negative argValue = advance = increment.
	if v0 < 0:
		return i0, i1
	return i1, i0


def detectIFFMultipositionSpring(elem, argGroupIndices):
	"""Detect a BTN-class delta-step knob (UH-1H IFF_multiposition_spring_switch variant).

	The UH-1H version of `IFF_multiposition_spring_switch` uses ±1 as delta
	command values and has asymmetric animation argLims ({-1,0}/{0,1}), which
	causes detectBtnPulseCounter to reject it (argLims don't match; lim[0] < 0).
	This function handles only that variant, identified by the helper tag.

	The C++ device interprets +1 as "advance one step" and -1 as "retreat one
	step" on the CODE / WIPERS knob.  The actual arg position range is encoded in
	the C++ device (not in the Lua), so we cannot derive step or argLim from
	the clickabledata.  We model this as `type=relative` with `sendProtocol=C`
	so the script sends ±1.0 directly and the validator uses testRelative
	(direction-only check) rather than testWheel (which needs the exact step).

	Returns (incIdx, decIdx) when the pattern matches, else None.
	incIdx is the sub-control with the positive argValue (increment direction).
	"""
	if elem.get('helper') != 'IFF_multiposition_spring_switch':
		return None
	if len(argGroupIndices) != 2:
		return None

	classes = elem.get('controlClass', [])
	actions = elem.get('action', [])
	argValues = elem.get('argValue', [])

	i0, i1 = argGroupIndices

	# Both must be BTN class.
	for i in (i0, i1):
		if (classes[i] if i < len(classes) else '') != 'BTN':
			return None

	# Both must use the same command.
	if actions[i0] != actions[i1]:
		return None

	# argValues must be symmetric and non-zero.
	v0 = argValues[i0] if i0 < len(argValues) else 0
	v1 = argValues[i1] if i1 < len(argValues) else 0
	if not v0 or not v1:
		return None
	if abs(v0 + v1) > 1e-9:
		return None

	# incIdx is the sub-control with the positive argValue (increment direction).
	if v0 > 0:
		return i0, i1
	return i1, i0


def detectSpringloadedSwitch(elem, argGroupIndices):
	"""Detect a springloaded 3-position switch (default_springloaded_switch /
	default_springloaded_3pos_switch helper).

	Both helpers produce two sub-controls with the same commandId, complementary
	argLims ([a, mid] and [mid, b]), and symmetric argValues around 0.  The center
	position (mid, typically 0.0) is the natural resting state; the two extremes are
	the spring-activated positions.

	The structural checks are applied even when the helper tag is present, as a
	safety net against future modules where the same function name produces a
	different extraction structure.

	Returns (decIdx, incIdx, mergedArgLim, step, positions) on match, else None.
	decIdx has argValue < 0; incIdx has argValue > 0.
	"""
	if elem.get('helper') not in ('default_springloaded_switch', 'default_springloaded_3pos_switch', 'default_springloaded_switch2'):
		return None
	if len(argGroupIndices) != 2:
		return None

	actions = elem.get('action', [])
	argValues = elem.get('argValue', [])
	argLims = elem.get('argLim', [])

	i0, i1 = argGroupIndices

	# Both sub-controls must use the same command.
	a0 = actions[i0] if i0 < len(actions) else 0
	a1 = actions[i1] if i1 < len(actions) else 0
	if not a0 or a0 != a1:
		return None

	# argValues must be symmetric and non-zero.
	v0 = argValues[i0] if i0 < len(argValues) else 0.0
	v1 = argValues[i1] if i1 < len(argValues) else 0.0
	if not v0 or not v1 or abs(v0 + v1) > 1e-9:
		return None

	# argLims must be complementary: lim0[1] == lim1[0] (shared midpoint).
	lim0 = argLims[i0] if i0 < len(argLims) else None
	lim1 = argLims[i1] if i1 < len(argLims) else None
	if not (isinstance(lim0, list) and len(lim0) == 2 and isinstance(lim1, list) and len(lim1) == 2):
		return None
	if abs(lim0[1] - lim1[0]) > 1e-9:
		return None

	mergedLow = round(min(lim0[0], lim1[0]), 6)
	mergedHigh = round(max(lim0[1], lim1[1]), 6)
	mergedArgLim = [mergedLow, mergedHigh]
	step = round(abs(v0), 6)
	positions = round((mergedHigh - mergedLow) / step) + 1

	# decIdx has argValue < 0; incIdx has argValue > 0.
	if v0 < 0:
		return i0, i1, mergedArgLim, step, positions
	return i1, i0, mergedArgLim, step, positions


def detectDualCommandRotary(elem, argGroupIndices):
	"""Detect a multi-position rotary whose .action was overridden.

	A handful of DCS clickabledata elements declare a multi-position rotary
	(via `multiposition_switch` or `default_3_position_tumb`) and then
	override `.action = {cmdA, cmdB}` so each direction has its own command.
	Examples on the Ka-50: PVI-SWITCH-PTR (NAV Master modes, 7 pos), PVR-MODE-PTR
	(Weapon system mode selector, 5 pos), GYRO-MAG-MAN-HEADING-PTR (3 pos),
	UV26-BOARD-PTR (3 pos), FIREEXT-PTR (3 pos).

	After the override the structural shape is: 2 TUMB sub-controls, same
	arg, DIFFERENT actions, symmetric ±argValue, argLim spanning more than
	one step (i.e. the rotary has 3+ positions).  The .action override is
	purely for keybinding ergonomics — both commands have identical
	"set arg = value" handlers (confirmed against the Ka-50 keyboard input
	file, which binds absolute-value sets to a single one of the two
	commands across all positions).  So we can model this as a normal
	multi-position discrete using the inc-side (positive argValue) command.

	The argLim-spans-multiple-steps test is the discriminator vs. legitimate
	2-command springloaded switches whose argLim only spans ±|argValue|
	(those continue to be handled by the existing positionMap path).

	Returns (incIdx, decIdx) when the pattern matches, else None.
	"""
	if len(argGroupIndices) != 2:
		return None

	classes = elem.get('controlClass', [])
	actions = elem.get('action', [])
	argValues = elem.get('argValue', [])
	argLims = elem.get('argLim', [])
	relatives = elem.get('relative', [])

	i0, i1 = argGroupIndices

	for i in (i0, i1):
		if (classes[i] if i < len(classes) else '') != 'TUMB':
			return None

	# Different commands per direction (the override pattern).
	if actions[i0] == actions[i1]:
		return None

	# Relative encoder wheels (radio_wheel pattern: relative=true, different
	# commands per direction) are handled by detectWheel, not here.
	for i in (i0, i1):
		if relatives[i] if i < len(relatives) else False:
			return None

	v0 = argValues[i0] if i0 < len(argValues) else 0
	v1 = argValues[i1] if i1 < len(argValues) else 0
	if not v0 or not v1:
		return None
	if abs(v0 + v1) > 1e-9:
		return None

	# argLim must span more than one step in either direction — this is what
	# distinguishes a multi-position rotary from a 2-command springloaded
	# switch (which only spans ±|argValue|).
	step = abs(v0)
	lim0 = argLims[i0] if i0 < len(argLims) else None
	lim1 = argLims[i1] if i1 < len(argLims) else None
	if not (isinstance(lim0, list) and isinstance(lim1, list)
			and len(lim0) == 2 and len(lim1) == 2):
		return None
	rng0 = abs(lim0[1] - lim0[0])
	rng1 = abs(lim1[1] - lim1[0])
	if rng0 <= step + 1e-9 or rng1 <= step + 1e-9:
		return None

	if v0 > 0:
		return i0, i1
	return i1, i0


def buildPositionMap(elem, argGroupIndices):
	"""Build a positionMap list for a springloaded switch.

	Returns a 3-entry list: [negative, null (center), positive], sorted by argValue.

	The stored `value` is the absolute cockpit-arg target for that position
	(i.e. the matching endpoint of `arg_lim` for that sub-control), NOT the
	per-click `arg_value` delta.  For the common symmetric shape
	`arg_value={-1,1}`/`arg_lim={{-1,0},{0,1}}` these coincide (±1).  For
	asymmetric shapes — e.g. A-10C canopy `arg_value={-0.5,0.5}` /
	`arg_lim={{0,0.5},{0.5,1.0}}` — they differ, and the absolute endpoint
	(0.0 / 1.0) is what `performClickableAction` needs to actually drive the
	cockpit arg to the latched position.
	"""
	deviceId = elem['device']
	argValues = elem.get('argValue', [])
	argLims = elem.get('argLim', [])

	entries = []
	for i in argGroupIndices:
		action = elem['action'][i]
		argValue = argValues[i] if i < len(argValues) else (1.0 if i > 0 else -1.0)
		argLim = argLims[i] if i < len(argLims) else None
		# Pick the argLim endpoint that matches the sign of argValue:
		# positive delta → upper bound (latched-up target),
		# negative delta → lower bound (latched-down target).
		# Fall back to argValue when argLim is missing/zero-width or when
		# argValue is exactly 0 (no latch direction signal — e.g. A-10C
		# yaw-trim BTN+LEV hybrid where both sub-controls have argValue=0).
		if argValue != 0 and argLim and len(argLim) == 2 and argLim[0] != argLim[1]:
			target = argLim[1] if argValue > 0 else argLim[0]
		else:
			target = argValue
		entries.append((action, argValue, target))

	entries.sort(key=lambda x: x[1])

	posMap = []
	for action, argValue, target in entries:
		posMap.append({
			'deviceId': deviceId,
			'commandId': action,
			'value': round(target, 6),
		})

	# Insert null center for 2-entry maps.
	if len(posMap) == 2:
		posMap.insert(1, None)

	return posMap


def processElements(elements, deviceTableMap, perTableReverse, globalUnique, devNameById, devices):
	"""Process all extraction elements into canonical-keyed control entries.

	Emits '<deviceName>.<cmdName>' keys directly from DCS Lua identifiers —
	no camelCase, no suffix stripping, no deduplication.  Collisions (two
	elements producing the same canonical) are logged as warnings and
	resolved by keeping the entry whose source element key is alphabetically
	first — a stable, deterministic tie-break that survives Lua table
	iteration order changes across re-extractions.

	Returns (controls dict, warnings list).
	"""
	controls = {}
	warnings = []
	# Maps canonical → the elemKey that last won the write for that canonical.
	# Used by setControl() to apply the alphabetically-first-wins tie-break.
	canonicalElemKeys = {}

	def setControl(canonical, control, label=''):
		"""Write control to controls[canonical], keeping alphabetically-first elemKey."""
		existing = canonicalElemKeys.get(canonical)
		if existing is not None:
			if elemKey < existing:
				# New element key sorts earlier — replace existing entry.
				controls[canonical] = control
				canonicalElemKeys[canonical] = elemKey
				warnings.append(
					f'Canonical collision ({label}): {canonical!r} — '
					f'replaced {existing!r} with {elemKey!r}')
			else:
				# Existing entry already has the earlier key — keep it.
				warnings.append(
					f'Canonical collision ({label}): {canonical!r} — '
					f'kept {existing!r} over {elemKey!r}')
		else:
			controls[canonical] = control
			canonicalElemKeys[canonical] = elemKey

	for elemKey, elem in elements.items():
		deviceId = elem.get('device')
		actions = elem.get('action', [])
		args = elem.get('arg', [])
		argValues = elem.get('argValue', [])
		argLims = elem.get('argLim', [])
		classes = elem.get('controlClass', [])
		classesVr = elem.get('classVr', [])
		relatives = elem.get('relative', [])
		hint = elem.get('hint', '')
		hintKey = elem.get('hintKey', '')
		crewAccess = elem.get('crewAccess')
		hintFields = {'hintKey': hintKey} if hintKey else {}
		crewFields = {'crewAccess': crewAccess} if crewAccess is not None else {}

		if not actions or not args:
			continue

		# Group sub-controls by arg number.
		argGroups = {}
		for i, arg in enumerate(args):
			if i >= len(actions):
				break
			if arg not in argGroups:
				argGroups[arg] = []
			argGroups[arg].append(i)

		# When an element contains multiple arg groups (i.e. one clickable hotspot
		# drives more than one logical control - e.g. Mi-8 PTR-APP-BTN-ALTON is
		# both an autopilot button on left-mouse and a lamp intensity knob on
		# right-mouse, with different args), the element-key fallback in
		# makeCanonicalName would assign every group the same canonical and we
		# would lose all but one to "last write wins".  In that case, suffix
		# the canonical with the arg number to keep them distinct.
		multipleArgGroups = len(argGroups) > 1

		for arg, indices in argGroups.items():
			pdpSpecial = detectPdpSpecial(elem, indices)
			rotaryMatch = None if pdpSpecial else detectRotaryWithMomentary(elem, indices)
			wheelMatch = None if (pdpSpecial or rotaryMatch) else detectWheel(elem, indices)
			dualRotary = (
				None if (pdpSpecial or rotaryMatch or wheelMatch)
				else detectDualCommandRotary(elem, indices)
			)
			btnPulseCounter = (
				None if (pdpSpecial or rotaryMatch or wheelMatch or dualRotary)
				else detectBtnPulseCounter(elem, indices)
			)
			iffDeltaKnob = (
				None if (pdpSpecial or rotaryMatch or wheelMatch or dualRotary or btnPulseCounter)
				else detectIFFMultipositionSpring(elem, indices)
			)
			springloadedSwitch = (
				None if (pdpSpecial or rotaryMatch or wheelMatch or dualRotary or btnPulseCounter or iffDeltaKnob)
				else detectSpringloadedSwitch(elem, indices)
			)
			# wca_knob: tagged by installHelperTagger — LEV axis + springloaded BTN(s).
			wcaKnob = (
				not pdpSpecial and not rotaryMatch and not wheelMatch
				and not dualRotary and not btnPulseCounter and not iffDeltaKnob and not springloadedSwitch
				and elem.get('helper') == 'wca_knob'
			)
			binaryToggle = (
				not pdpSpecial and not rotaryMatch and not wheelMatch and not dualRotary
				and not btnPulseCounter and not iffDeltaKnob and not springloadedSwitch and not wcaKnob
				and detectBinaryToggle(elem, indices)
			)
			if pdpSpecial:
				# --- PDP circuit breaker (CH-47F pdp_special helper) ---
				# Two stable positions: in (push) and out (pull).
				# pos 0: send pushArgValue, readback pushArgValue (stable at that value).
				# pos 1: send pullArgValue (trigger), readback argLim[1] (device snaps up).
				# The collar state (0.8) is a timed script-level operation and is omitted.
				pullIdx, pushIdx = pdpSpecial
				actionId = actions[pullIdx]
				pushVal = round(argValues[pushIdx], 6)
				pullSendVal = round(argValues[pullIdx], 6)
				lim = argLims[pullIdx]
				pullReadbackVal = round(lim[1], 6) if isinstance(lim, list) and len(lim) == 2 else 1.0

				posMap = [
					{
						'deviceId': deviceId,
						'commandId': actionId,
						'sendValue': pushVal,
						'readbackValue': pushVal,
					},
					{
						'deviceId': deviceId,
						'commandId': actionId,
						'sendValue': pullSendVal,
						'readbackValue': pullReadbackVal,
					},
				]

				canonical = makeCanonicalName(deviceId, actionId, devNameById,
					deviceTableMap, perTableReverse, globalUnique, elementKey=elemKey)
				if multipleArgGroups and elemKey in canonical:
					canonical = f'{canonical}_arg{arg}'

				control = {
					'description': hint,
					**hintFields,
					**crewFields,
					'type': 'discrete',
					'positions': 2,
					'positionMap': posMap,
				}
				if arg != 0:
					control['arg'] = arg
				control['elementName'] = elemKey

				setControl(canonical, control, 'pdp_special')

			elif rotaryMatch:
				# --- Multi-position rotary latch + momentary button(s) ---
				# Emit a single discrete control with a positionMap that includes
				# one entry per rotary position (all using the latch's commandId),
				# extended by one step above/below the latch's argLim range for
				# each direction that has a momentary.  Example: F-16C FUEL QTY
				# SEL (TEST momentary at 0.0, plus 5 latched positions 0.1–0.5).
				latchIdx, extendLow, extendHigh = rotaryMatch
				actionId = actions[latchIdx]
				latchLim = argLims[latchIdx]
				step = round(abs(argValues[latchIdx]), 6)
				lowBound = round(latchLim[0] - step, 6) if extendLow else round(latchLim[0], 6)
				highBound = round(latchLim[1] + step, 6) if extendHigh else round(latchLim[1], 6)
				numPositions = round((highBound - lowBound) / step) + 1

				posMap = []
				for p in range(numPositions):
					v = round(lowBound + p * step, 6)
					posMap.append({
						'deviceId': deviceId,
						'commandId': actionId,
						'value': v,
					})

				canonical = makeCanonicalName(deviceId, actionId, devNameById,
					deviceTableMap, perTableReverse, globalUnique, elementKey=elemKey)
				if multipleArgGroups and elemKey in canonical:
					canonical = f'{canonical}_arg{arg}'

				control = {
					'description': hint,
					**hintFields,
					**crewFields,
					'type': 'discrete',
					'positions': numPositions,
					'positionMap': posMap,
				}
				if arg != 0:
					control['arg'] = arg
				control['elementName'] = elemKey

				setControl(canonical, control, 'rotary+momentary')

			elif wheelMatch:
				# --- Wheel control (increment/decrement encoder) ---
				# Handles two patterns:
				#   radio_wheel_1 (Mi-8/Mi-24): both directions share ONE command,
				#     argValue sign carries direction.
				#   radio_wheel (A-10C): each direction has its OWN command
				#     (Button_N up / Button_N+1 down), both with relative=true.
				# Both are modeled as 'relative': a click moves one notch; there
				# is no provision to seek to an absolute position.  Script value is
				# a signed integer click count: positive → CW (increment) clicks,
				# negative → CCW (decrement) clicks, 0 = no-op.  argLim is preserved
				# for documentation/readback so consumers know the cycle range.
				incIdx, decIdx = wheelMatch
				actionId = actions[incIdx]
				decActionId = actions[decIdx]
				incValue = round(argValues[incIdx], 6)
				decValue = round(argValues[decIdx], 6)
				lim = argLims[incIdx]
				argLim = [round(lim[0], 6), round(lim[1], 6)]

				canonical = makeCanonicalName(deviceId, actionId, devNameById,
					deviceTableMap, perTableReverse, globalUnique, elementKey=elemKey)
				if multipleArgGroups and elemKey in canonical:
					canonical = f'{canonical}_arg{arg}'

				control = {
					'description': hint,
					**hintFields,
					**crewFields,
					'type': 'relative',
					'wheel': True,
					'deviceId': deviceId,
					'commandId': actionId,
					'argLim': argLim,
					'incrementValue': incValue,
					'decrementValue': decValue,
				}
				# When each direction has its own command (radio_wheel pattern),
				# store the decrement command separately so the runtime can send
				# the correct command for each direction.
				if decActionId != actionId:
					control['decrementCommandId'] = decActionId
				if arg != 0:
					control['arg'] = arg

				# slave_animation couples the pulsed command arg to one or more
				# separate display args (digit-carry chain on multi-digit cockpit
				# displays, A-10C radio_wheel, etc.).  When present and distinct
				# from the pulse arg, expose as displayArgs = [master, slave, ...]
				# so consumers read the cockpit position from displayArgs[0]
				# instead of the pulse counter.
				slaveAnim = elem.get('slaveAnimation') or []
				hasDisplayArgs = False
				if incIdx < len(slaveAnim):
					chain = slaveAnim[incIdx]
					if chain and chain != [arg]:
						control['displayArgs'] = list(chain)
						hasDisplayArgs = True

				# When slaveArgLim is available (A-10C radio_wheel pattern) the
				# display arg has its own range distinct from the command arg's
				# hardcoded [0,1].  Override argLim with the display arg's range
				# so testWheel can compute position steps correctly.
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

				# Emit step when the display arg step differs from the command
				# value (e.g. FREQ-1: sends 0.1 but display arg moves 0.05).
				if abs(dispScale - 1.0) > 1e-9:
					control['step'] = round(abs(incValue) * dispScale, 6)

				# settleDelay: minimum time (seconds) to wait for the animation
				# to complete before reading back.  Derived from the element's
				# animation_speed and the display step size.
				animSpeedList = elem.get('animationSpeed') or []
				if incIdx < len(animSpeedList) and animSpeedList[incIdx]:
					speed = animSpeedList[incIdx]
					if speed > 0:
						displayStep = abs(incValue) * dispScale
						settleDelay = round(displayStep / speed, 3)
						if settleDelay > 0:
							control['settleDelay'] = settleDelay
				control['elementName'] = elemKey

				setControl(canonical, control, 'wheel')

			elif binaryToggle:
				# --- Binary toggle (cover / guard / `default_2_position_tumb`) ---
				# Two TUMB sub-controls share the same arg + (deviceId, commandId)
				# with symmetric ±argValue.  The argValue magnitude is the per-frame
				# animation delta (e.g. 0.01 across [0, 1]), not a step size.  Each
				# cockpit click toggles between the two endpoints.  Emit a
				# 2-position discrete with step = full range.
				i = indices[0]
				actionId = actions[i]
				lim = argLims[i]
				argLim = [round(lim[0], 6), round(lim[1], 6)]
				step = round(argLim[1] - argLim[0], 6)

				canonical = makeCanonicalName(deviceId, actionId, devNameById,
					deviceTableMap, perTableReverse, globalUnique, elementKey=elemKey)
				if multipleArgGroups and elemKey in canonical:
					canonical = f'{canonical}_arg{arg}'

				control = {
					'description': hint,
					**hintFields,
					**crewFields,
					'type': 'discrete',
					'deviceId': deviceId,
					'commandId': actionId,
					'argLim': argLim,
					'step': step,
					'positions': 2,
				}
				if arg != 0:
					control['arg'] = arg
				control['elementName'] = elemKey

				setControl(canonical, control, 'binary toggle')

			elif dualRotary:
				# --- Multi-position rotary with .action override ---
				# Both override commands have identical "set arg = value"
				# handlers (per the Ka-50 keyboard input file, which binds
				# absolute-value sets to a single one of the two commands
				# across all positions).  Emit as a normal multi-position
				# discrete using the inc-side (positive argValue) command;
				# scripts and DCSControlPanel will send absolute position
				# values exactly like for a non-overridden multiposition_switch.
				incIdx, _decIdx = dualRotary
				incCmdId = actions[incIdx]
				incValue = abs(round(argValues[incIdx], 6))
				lim = argLims[incIdx]
				argLim = [round(lim[0], 6), round(lim[1], 6)]
				rng = argLim[1] - argLim[0]
				positions = round(rng / incValue) + 1 if incValue > 0 else 2

				canonical = makeCanonicalName(deviceId, incCmdId, devNameById,
					deviceTableMap, perTableReverse, globalUnique, elementKey=elemKey)
				if multipleArgGroups and elemKey in canonical:
					canonical = f'{canonical}_arg{arg}'

				control = {
					'description': hint,
					**hintFields,
					**crewFields,
					'type': 'discrete',
					'deviceId': deviceId,
					'commandId': incCmdId,
					'argLim': argLim,
					'step': incValue,
					'positions': positions,
				}
				if arg != 0:
					control['arg'] = arg
				control['elementName'] = elemKey

				setControl(canonical, control, 'dual-command rotary')

			elif btnPulseCounter:
				# --- BTN pulse-advance counter (IFF_multiposition_spring_switch pattern) ---
				# The C++ device only accepts relative delta commands: negative
				# argValue (e.g. −0.1) advances one step; positive (e.g. +0.1)
				# retreats one step.  Same commandId for both directions.
				# Modeled identically to a radio_wheel (type=relative, wheel=True).
				incIdx, decIdx = btnPulseCounter
				actionId = actions[incIdx]
				incValue = round(argValues[incIdx], 6)  # negative (e.g. -0.1)
				decValue = round(argValues[decIdx], 6)  # positive (e.g. +0.1)
				lim = argLims[incIdx]
				argLim = [round(lim[0], 6), round(lim[1], 6)]

				canonical = makeCanonicalName(deviceId, actionId, devNameById,
					deviceTableMap, perTableReverse, globalUnique, elementKey=elemKey)
				if multipleArgGroups and elemKey in canonical:
					canonical = f'{canonical}_arg{arg}'

				control = {
					'description': hint,
					**hintFields,
					**crewFields,
					'type': 'relative',
					'wheel': True,
					'deviceId': deviceId,
					'commandId': actionId,
					'argLim': argLim,
					'incrementValue': incValue,
					'decrementValue': decValue,
				}
				if arg != 0:
					control['arg'] = arg
				control['elementName'] = elemKey

				setControl(canonical, control, 'btn-pulse-counter')

			elif iffDeltaKnob:
				# --- IFF_multiposition_spring_switch (UH-1H delta-step knob variant) ---
				# The C++ device treats ±1 as "advance/retreat one step" on the knob.
				# The actual arg position range/step is not in the Lua; the validator
				# uses testRelative (direction check only) rather than testWheel.
				# Scripts send ±1.0 directly (type=relative, sendProtocol=C).
				incIdx, decIdx = iffDeltaKnob
				actionId = actions[incIdx]
				incValue = round(argValues[incIdx], 6)  # positive (+1.0 = increment)

				canonical = makeCanonicalName(deviceId, actionId, devNameById,
					deviceTableMap, perTableReverse, globalUnique, elementKey=elemKey)
				if multipleArgGroups and elemKey in canonical:
					canonical = f'{canonical}_arg{arg}'

				control = {
					'description': hint,
					**hintFields,
					**crewFields,
					'type': 'relative',
					'deviceId': deviceId,
					'commandId': actionId,
					'argLim': [-1.0, 1.0],
					'incValue': incValue,
					'sendProtocol': 'C',
				}
				if arg != 0:
					control['arg'] = arg
				control['elementName'] = elemKey

				setControl(canonical, control, 'iff-delta-knob')

			elif springloadedSwitch:
				# --- Springloaded 3-position switch (default_springloaded_switch /
				# default_springloaded_3pos_switch helper) ---
				# A 3-position switch springloaded to center.  Send argValue -1.0 / 0.0 / 1.0
				# to the single shared command.  The merged argLim covers both halves of the
				# complementary argLims from the two sub-controls.
				decIdx, incIdx, mergedArgLim, step, positions = springloadedSwitch
				actionId = actions[decIdx]

				canonical = makeCanonicalName(deviceId, actionId, devNameById,
					deviceTableMap, perTableReverse, globalUnique, elementKey=elemKey)
				if multipleArgGroups and elemKey in canonical:
					canonical = f'{canonical}_arg{arg}'

				control = {
					'description': hint,
					**hintFields,
					**crewFields,
					'type': 'discrete',
					'deviceId': deviceId,
					'commandId': actionId,
					'argLim': mergedArgLim,
					'step': step,
					'positions': positions,
				}
				if arg != 0:
					control['arg'] = arg
				control['elementName'] = elemKey

				setControl(canonical, control, 'springloaded-switch')

			elif wcaKnob:
				# --- Continuous LEV axis with springloaded BTN(s) (wca_knob helper) ---
				# Detected via the 'helper' tag set by installHelperTagger — not a structural
				# heuristic, so no false positives from other LEV+BTN combinations.
				# Emits two controls per element:
				#   1. The LEV sub-control as a continuous axis (S: protocol, argLim = LEV range).
				#   2. Each unique BTN command as a separate momentary discrete control (C: protocol).
				# Example: F-15E wac_bklt_knob — LEV axis for brightness 0–0.75, plus a separate
				# wac_bklt_knob_reset button that momentarily drives the arg to 1.0 and springs
				# back to 0.75 automatically via DCS use_release_message.
				classes = elem.get('controlClass', [])
				relatives = elem.get('relative', [])
				levIdx = next(
					(i for i in indices if i < len(classes) and classes[i] == 'LEV'
					and not (relatives[i] if i < len(relatives) else False)),
					indices[0]
				)
				levActionId = actions[levIdx]
				levLim = argLims[levIdx] if levIdx < len(argLims) else [0.0, 1.0]
				levArgLim = [round(levLim[0], 6), round(levLim[1], 6)] if isinstance(levLim, list) and len(levLim) == 2 else [0.0, 1.0]

				levCanonical = makeCanonicalName(deviceId, levActionId, devNameById,
					deviceTableMap, perTableReverse, globalUnique, elementKey=elemKey)
				if multipleArgGroups and elemKey in levCanonical:
					levCanonical = f'{levCanonical}_arg{arg}'

				levControl = {
					'description': hint,
					**hintFields,
					**crewFields,
					'type': 'continuous',
					'deviceId': deviceId,
					'commandId': levActionId,
					'argLim': levArgLim,
					'sendProtocol': 'S',
				}
				if arg != 0:
					levControl['arg'] = arg
				levControl['elementName'] = elemKey

				setControl(levCanonical, levControl, 'lev+springloaded-btn (axis)')

				# Emit each unique BTN command as a separate momentary discrete control.
				seenBtnCmds = set()
				for i in indices:
					if i >= len(classes) or classes[i] != 'BTN':
						continue
					btnActionId = actions[i]
					if btnActionId in seenBtnCmds:
						continue
					seenBtnCmds.add(btnActionId)

					btnCanonical = makeCanonicalName(deviceId, btnActionId, devNameById,
						deviceTableMap, perTableReverse, globalUnique, elementKey=elemKey)
					if multipleArgGroups and elemKey in btnCanonical:
						btnCanonical = f'{btnCanonical}_arg{arg}'

					# Use the BTN's actual argLim from the Lua data (e.g. [0.75, 1.0] for the spring
					# zone).  This means Pos 0 = spring base (BRT) and Pos 1 = RESET, so clicking
					# Pos 0 from a script correctly restores the knob to BRT rather than to OFF.
					btnLim = argLims[i] if i < len(argLims) else None
					if isinstance(btnLim, list) and len(btnLim) == 2:
						btnArgLim = [round(btnLim[0], 6), round(btnLim[1], 6)]
					else:
						btnArgLim = [0.0, 1.0]
					btnStep = round(btnArgLim[1] - btnArgLim[0], 6)

					btnControl = {
						'description': hint,
						**hintFields,
						**crewFields,
						'type': 'discrete',
						'deviceId': deviceId,
						'commandId': btnActionId,
						'argLim': btnArgLim,
						'step': btnStep,
						'positions': 2,
					}
					if arg != 0:
						btnControl['arg'] = arg
					btnControl['elementName'] = elemKey

					setControl(btnCanonical, btnControl, 'lev+springloaded-btn (reset)')

			elif isPositionMapElement(elem, indices):
				# --- PositionMap control (springloaded multi-command switch) ---
				posMap = buildPositionMap(elem, indices)

				# Canonical from first positionMap entry's (deviceId, commandId).
				firstEntry = next((e for e in posMap if e), None)
				firstCmdId = firstEntry['commandId'] if firstEntry else actions[indices[0]]
				canonical = makeCanonicalName(deviceId, firstCmdId, devNameById,
					deviceTableMap, perTableReverse, globalUnique, elementKey=elemKey)
				if multipleArgGroups and elemKey in canonical:
					canonical = f'{canonical}_arg{arg}'

				control = {
					'description': hint,
					**hintFields,
					**crewFields,
					'type': 'discrete',
					'positions': len(posMap),
					'positionMap': posMap,
				}
				if arg != 0:
					control['arg'] = arg
				control['elementName'] = elemKey

				setControl(canonical, control, 'positionMap')

			else:
				# --- Simple control (same arg & action, or single sub-control) ---
				i = indices[0]
				actionId = actions[i]

				if actionId == 0:
					continue

				controlClass = classes[i] if i < len(classes) else 'BTN'
				isRelative = relatives[i] if i < len(relatives) else False
				controlType = classifyType(controlClass, isRelative)
				# class_vr = MULTY_TUMB on a LEV sub-element means the physical
				# control has discrete positions even though its main class is
				# LEV (mouse drag-axis).  DCS engine requires SetCommand +
				# set_argument_value (S: protocol) for these controls.
				vrClass = classesVr[i] if i < len(classesVr) else None
				sendProtocol = None
				if vrClass == 'MULTY_TUMB' and controlClass == 'LEV':
					controlType = 'discrete'
					sendProtocol = 'S'

				argLim = argLims[i] if i < len(argLims) else [0.0, 1.0]
				if isinstance(argLim, list) and len(argLim) == 2:
					argLim = [round(argLim[0], 6), round(argLim[1], 6)]
				else:
					argLim = [0.0, 1.0]

				argValue = argValues[i] if i < len(argValues) else None

				canonical = makeCanonicalName(deviceId, actionId, devNameById,
					deviceTableMap, perTableReverse, globalUnique, elementKey=elemKey)
				if multipleArgGroups and elemKey in canonical:
					canonical = f'{canonical}_arg{arg}'

				control = {
					'description': hint,
					**hintFields,
					**crewFields,
					'type': controlType,
					'deviceId': deviceId,
					'commandId': actionId,
				}

				if arg != 0:
					control['arg'] = arg

				if controlType == 'discrete':
					control['argLim'] = argLim
					step, positions = computeStepAndPositions(argLim, argValue)
					control['step'] = step
					control['positions'] = positions
					if sendProtocol:
						control['sendProtocol'] = sendProtocol
				elif controlType in ('continuous', 'relative'):
					control['argLim'] = argLim
					if controlType == 'relative':
						# Relative LEV drag-axes use performClickableAction (C:).
						# Without this override the runtime S: default is wrong
						# for mouse-drag knobs (altimeter settings, HSI, TACAN, etc.).
						control['sendProtocol'] = 'C'
				control['elementName'] = elemKey

				setControl(canonical, control)

	return controls, warnings


# ─── Indicator processing ────────────────────────────────────────────────────

def processIndicators(indicators):
	"""Read-only entries for indicator text fields. Canonical: ind.<id>.<field>."""
	controls = {}
	for ind in indicators:
		if ind.get('bake'):
			continue
		fields = ind.get('fields', [])
		if not fields:
			continue

		indicationId = ind['index']

		for fieldName in fields:
			# guid-N names are synthetic placeholders from our create_guid_string() mock —
			# they don't match the real GUID strings DCS assigns at runtime.  Skip them.
			if re.match(r'^guid-\d+$', fieldName):
				continue
			canonical = f'ind.{indicationId}.{fieldName}'
			controls[canonical] = {
				'description': fieldName,
				'indicationId': indicationId,
				'fieldName': fieldName,
			}

		# Aggregate entry: returns all non-empty fields joined by newline.
		cppClass = ind.get('cppClass', '')
		if '::' in cppClass:
			cppClass = cppClass.split('::')[-1]
		aggDescription = f'{cppClass} (all fields)' if cppClass else f'Indication {indicationId} (all fields)'
		controls[f'ind.{indicationId}'] = {
			'description': aggDescription,
			'indicationId': indicationId,
		}

	return controls


# ─── Shared-arg annotation ────────────────────────────────────────────────────

def annotateIndicatorArgLim(controls, argToGaugeInput):
	"""Annotate commandable controls whose send arg is shared with a gauge/lamp.

	When a control's arg also appears in gaugesAndLamps, the same arg slot is
	used for both sending commands and reading back state.  The value read back
	is governed by the gauge's input (gaugeInput), not the element's argLim.

	For a 2-element gaugeInput [min, max], emits `indicatorArgLim` — consumed
	by `_reverseTranslateValue` with linear interpolation.

	For a >2-element gaugeInput [v0, v1, ..., vN], emits `indicatorPositions`
	— consumed by `_reverseTranslateValue` with nearest-value matching.  These
	are physical stop-values (e.g. non-linear gauge scales) rather than a
	simple range.

	Mutates `controls` in-place.  Returns the number of controls annotated.
	"""
	count = 0
	for ctrl in controls.values():
		arg = ctrl.get('arg')
		if arg is None or 'type' not in ctrl or arg not in argToGaugeInput:
			continue
		gaugeInput = argToGaugeInput[arg]
		if len(gaugeInput) == 2:
			ctrl['indicatorArgLim'] = gaugeInput
		else:
			ctrl['indicatorPositions'] = gaugeInput
		count += 1
	return count


# ─── Gauge / lamp processing ─────────────────────────────────────────────────

def processGaugesAndLamps(gaugesAndLamps):
	"""Read-only entries for gauges/lamps. Canonical: arg.<NAME>."""
	controls = {}
	for gauge in gaugesAndLamps:
		name = gauge['name']
		arg = gauge['arg']
		canonical = f'arg.{name}'
		controls[canonical] = {
			'description': name,
			'arg': arg,
		}

	return controls


# ─── Name map generation ─────────────────────────────────────────────────────


def preserveExistingSendProtocol(newControls, existingFile, moduleName):
	"""Preserve an explicit 'sendProtocol' from an existing mapping.

	Clickable-derived 'relative' controls get sendProtocol='C' by default
	(performClickableAction, matching the cockpit mouse-interaction path).
	Inferred '_ITER' siblings get no sendProtocol — they fall back to the
	runtime default of 'S' (SetCommand) for `relative` controls, which is
	what the keyboard / external-input path of the C++ device code expects.

	If a hand-curated mapping has set an explicit sendProtocol on any
	control (e.g. forcing 'S' on a clickable-derived relative, or 'C' on
	an inferred `_ITER` whose runtime default proved wrong), preserve it
	across regenerations.  Matches by (deviceId, commandId).

	Refuses to import overrides when the existing file's `moduleName` does
	not match the current generation's `moduleName` — `(deviceId, commandId)`
	is not unique across modules, so a foreign mapping accidentally written
	to our output path would otherwise silently graft its overrides onto
	unrelated controls.

	Returns the count of preserved overrides.
	"""
	if not existingFile or not os.path.exists(existingFile):
		return 0

	with open(existingFile, encoding='utf-8') as f:
		existing = json.load(f)

	existingModule = existing.get('moduleName')
	if existingModule and existingModule != moduleName:
		print(f'Skipping sendProtocol preservation: existing file moduleName '
			f'{existingModule!r} != current {moduleName!r}')
		return 0

	oldByDevCmd = {}
	for ctrl in existing.get('controls', {}).values():
		# Collect any manually-set override fields keyed by (deviceId, commandId).
		devId = ctrl.get('deviceId')
		cmdId = ctrl.get('commandId')
		if devId is None or cmdId is None:
			continue
		entry = {}
		for field in ('sendProtocol', 'validationSkip'):
			val = ctrl.get(field)
			if val is not None:
				entry[field] = val
		if entry:
			oldByDevCmd[(devId, cmdId)] = entry

	count = 0
	for ctrl in newControls.values():
		devId = ctrl.get('deviceId')
		cmdId = ctrl.get('commandId')
		if devId is None or cmdId is None:
			continue
		overrides = oldByDevCmd.get((devId, cmdId))
		if not overrides:
			continue
		for field, val in overrides.items():
			if ctrl.get(field) != val:
				ctrl[field] = val
				count += 1
	return count


# ─── Raw command processing ───────────────────────────────────────────────────

def processRawCommands(commandTables, deviceTableMap, devices, elements, existingControls, keybindings=None, listenedCommands=None):
	"""Emit type='raw' entries for commands with no physical element binding.

	When the extraction includes keybindings, raw entries are the (device, command)
	pairs that some key/axis binding sends, or that a scripted device listens for,
	but no clickable element does.  Otherwise falls back to every command-table
	entry with no element binding.

	Returns a new dict of controls (does not mutate existingControls).
	"""
	if keybindings is not None:
		return _rawCommandsFromKeybindings(keybindings, listenedCommands or [], commandTables, deviceTableMap, devices, elements, existingControls)

	devNameById = {v: k for k, v in devices.items()}

	# Build set of all (deviceId, commandId) pairs that appear in physical elements.
	elementCommands = set()
	for elem in elements.values():
		deviceId = elem.get('device')
		if deviceId is None:
			continue
		for cmdId in elem.get('action', []):
			elementCommands.add((deviceId, cmdId))

	# Build reverse deviceTableMap: tableName → [deviceId, ...]
	# deviceTableMap keys are already int (converted in main() from JSON string keys).
	tableToDeviceIds = {}
	for devId, tableName in deviceTableMap.items():
		tableToDeviceIds.setdefault(tableName, []).append(devId)

	controls = {}

	for tableName, commands in commandTables.items():
		# Find device IDs for this table.
		# Case 1 (F-4E style): tableName IS a device name (commandTables keyed by device name).
		# Case 2 (AH-64D/Mi-24P style): tableName is a *_commands global, look up via tableToDeviceIds.
		if tableName in devices:
			deviceIds = [devices[tableName]]
		elif tableName in tableToDeviceIds:
			deviceIds = tableToDeviceIds[tableName]
		else:
			continue

		for cmdName, cmdId in commands.items():
			# Determine which single deviceId this command should be bound to.
			if len(deviceIds) == 1:
				deviceId = deviceIds[0]
			else:
				# Heuristic matching: find best device ID for the command name, otherwise default to first.
				deviceId = deviceIds[0]
				cmdLower = cmdName.lower()
				sortedDevices = sorted([(d, devNameById[d].lower()) for d in deviceIds if d in devNameById], key=lambda x: len(x[1]), reverse=True)
				for d, devName in sortedDevices:
					if cmdLower.startswith(devName + '_') or cmdLower.startswith(devName):
						deviceId = d
						break
					parts = devName.split('_')
					if any(p in cmdLower for p in parts if len(p) > 3):
						deviceId = d
						break
				else:
					if 'arc51' in cmdLower:
						for d, devName in sortedDevices:
							if 'radio' in devName:
								deviceId = d
								break
					elif 'tacan' in cmdLower:
						for d, devName in sortedDevices:
							if 'tacan' in devName:
								deviceId = d
								break

			if (deviceId, cmdId) in elementCommands:
				continue  # Has a physical element — handled by processElements().

			deviceName = devNameById.get(deviceId, f'dev{deviceId}')
			canonical = f'{deviceName}.{cmdName}'
			if canonical in existingControls or canonical in controls:
				continue  # Element-derived entry took priority, or collision.
			controls[canonical] = {
				'description': cmdName,
				'type': 'raw',
				'deviceId': deviceId,
				'commandId': cmdId,
			}

	return controls


_bindingValueFields = (('down', 'valueDown'), ('up', 'valueUp'), ('pressed', 'valuePressed'))

# DCS device command IDs start at 3000; lower IDs are simulator-level iCommands.
_firstDeviceCommandId = 3000


def _rawCommandsFromKeybindings(keybindings, listenedCommands, commandTables, deviceTableMap, devices, elements, existingControls):
	"""Raw entries for bound or listened (device, command) pairs with no clickable element."""
	devNameById = {v: k for k, v in devices.items()}
	perTableReverse, globalUnique = buildCommandReverse(commandTables)
	elementCommands = {(e.get('device'), cmdId) for e in elements.values() for cmdId in e.get('action', [])}
	existingPairs = {(c.get('deviceId'), c.get('commandId')) for c in existingControls.values()}

	bindingsByPair = {}
	for binding in keybindings:
		deviceId = binding['deviceId']
		if binding['kind'] == 'axis':
			bindingsByPair.setdefault((deviceId, binding['action']), []).append({'name': binding.get('name', ''), 'axis': True})
			continue
		perCommand = {}
		for commandField, valueField in _bindingValueFields:
			if commandField in binding:
				values = perCommand.setdefault(binding[commandField], {'name': binding.get('name', '')})
				if valueField in binding:
					values[valueField] = binding[valueField]
		for cmdId, values in perCommand.items():
			bindingsByPair.setdefault((deviceId, cmdId), []).append(values)
	for entry in listenedCommands:
		if entry['commandId'] >= _firstDeviceCommandId:
			bindingsByPair.setdefault((entry['deviceId'], entry['commandId']), [])

	controls = {}
	for (deviceId, cmdId), bindings in bindingsByPair.items():
		if (deviceId, cmdId) in elementCommands or (deviceId, cmdId) in existingPairs:
			continue
		tableName = deviceTableMap.get(deviceId)
		cmdName = perTableReverse.get(tableName, {}).get(cmdId) or globalUnique.get(cmdId) or f'cmd_{cmdId}'
		canonical = f'{devNameById.get(deviceId, f"dev{deviceId}")}.{cmdName}'
		if canonical in existingControls or canonical in controls:
			continue
		control = {'type': 'raw', 'deviceId': deviceId, 'commandId': cmdId}
		if not bindings:
			control['description'] = cmdName
		else:
			control['description'] = bindings[0]['name'] if len(bindings) == 1 else f'{bindings[0]["name"]} (+{len(bindings) - 1} more)'
			control['bindings'] = bindings
		controls[canonical] = control

	return controls


# ─── Main ────────────────────────────────────────────────────────────────────

def main():
	parser = argparse.ArgumentParser(description='Generate canonical control mapping from nativeExtraction JSON.')
	parser.add_argument('extractionFile', help='Path to nativeExtraction JSON file (e.g. config/nativeExtractions/Ka-50_3.json).')
	parser.add_argument('--module-name', help='Override output module name (default: from extraction JSON).')
	parser.add_argument('--existing', help='Existing control mapping for sendProtocol override preservation. Defaults to the output path.')
	args = parser.parse_args()

	with open(args.extractionFile, encoding='utf-8') as f:
		extraction = json.load(f)

	moduleName = args.module_name or extraction.get('module', 'unknown')

	devices = extraction.get('devices', {})
	commandTables = extraction.get('commandTables', {})
	elements = extraction.get('elements', {})
	indicators = extraction.get('indicators', [])
	devNameById = {v: k for k, v in devices.items()}

	# Step 1: Match devices to command tables.
	# Preferred source: deterministic mapping captured at extraction time by
	# tools/extractUtils.py (proxies `*_commands` + `elements` globals during
	# clickabledata.lua execution to record exactly which table each
	# element's cmd came from).  Fall back to name-similarity and evidence-
	# based heuristics for devices the extractor could not resolve
	# (e.g. devices driven only by Input/*/default.lua, or indicator-only
	# devices, or modules extracted before deterministic capture was added).
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

	# Report device-table matching.
	unmatchedDevices = set(devNameById.keys()) - set(deviceTableMap.keys())
	print(f'Device-table matching: {len(deviceTableMap)}/{len(devNameById)} devices matched '
	      f'(deterministic={sourceCounts["deterministic"]}, '
	      f'name-similarity={sourceCounts["nameSim"]}, '
	      f'evidence={sourceCounts["evidence"]})')
	if unmatchedDevices:
		for devId in sorted(unmatchedDevices):
			print(f'  Unmatched: device {devId} ({devNameById.get(devId, "?")})')

	# Build gauge-input lookup before processing elements so commandable controls
	# whose send arg is shared with a gauge/lamp can be annotated with
	# indicatorArgLim — the readable range for that arg, which may differ from
	# the commandable argLim.
	gaugesAndLamps = extraction.get('gaugesAndLamps', [])
	argToGaugeInput = {
		g['arg']: g['input']
		for g in gaugesAndLamps
		if isinstance(g.get('input'), list) and len(g['input']) >= 2
	}

	# Step 2: Process elements into controls.
	controls, warnings = processElements(elements, deviceTableMap, perTableReverse, globalUnique, devNameById, devices)

	# Annotate commandable controls whose arg is also present as a gauge/lamp.
	# When send and read share the same arg slot, the value you read back is
	# governed by gaugeInput, not argLim.  indicatorArgLim carries that range
	# so consumers (e.g. _reverseTranslateValue) use the correct range.
	indicatorArgLimCount = annotateIndicatorArgLim(controls, argToGaugeInput)
	if indicatorArgLimCount:
		print(f'indicatorArgLim: {indicatorArgLimCount} controls annotated (send/read arg shared)')

	# Step 2b: Emit raw entries for unbound commands (AI crew, _ITER/_AXIS/_EXT siblings, etc.)
	rawControls = processRawCommands(commandTables, deviceTableMap, devices, elements, controls, extraction.get('keybindings'), extraction.get('listenedCommands'))
	controls.update(rawControls)
	if rawControls:
		print(f'Raw controls: {len(rawControls)} unbound commands emitted (type=raw)')

	# Step 3: Process indicators into read-only entries.
	indicatorControls = processIndicators(indicators)

	# Merge indicator controls.  If a canonical 'ind.<id>.<field>' collides
	# with a commandable control (rare), attach the indication fields to it.
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

	# Merge gauge controls — skip if arg already covered by a commandable element.
	elementArgs = set()
	for ctrl in controls.values():
		if ctrl.get('arg') is not None and 'type' in ctrl:
			elementArgs.add(ctrl['arg'])

	gaugeSkipped = 0
	for canonical, ctrl in gaugeControls.items():
		if ctrl.get('arg') in elementArgs:
			gaugeSkipped += 1
			continue
		if canonical in controls:
			gaugeSkipped += 1
			continue
		controls[canonical] = ctrl

	print(f'Gauges/lamps: {len(gaugeControls)} extracted, {gaugeSkipped} skipped (arg overlap), {len(gaugeControls) - gaugeSkipped} merged')

	# Step 3c: Preserve explicit sendProtocol overrides from existing mapping.
	preservedCount = preserveExistingSendProtocol(controls, args.existing, moduleName)
	if preservedCount:
		print(f'Preserved {preservedCount} sendProtocol overrides from {args.existing}')

	# Step 4: Build output (sorted alphabetically by control name).
	sortedControls = dict(sorted(controls.items()))

	output = {
		'moduleName': moduleName,
		'controls': sortedControls,
	}

	outDir = os.path.join('config', 'controlMappings')
	os.makedirs(outDir, exist_ok=True)

	outFile = os.path.join(outDir, f'{moduleName}.json')
	with open(outFile, 'w', encoding='utf-8') as f:
		json.dump(output, f, indent='\t', ensure_ascii=False, sort_keys=True)

	# Step 6: Print summary.
	typeCounts = {}
	commandable = 0
	readable = 0
	readOnly = 0
	hasPositionMap = 0
	for name, ctrl in controls.items():
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
	print(f'Types:')
	for t, c in sorted(typeCounts.items()):
		print(f'  {t}: {c}')

	if warnings:
		print(f'\nWarnings ({len(warnings)}):')
		for w in warnings:
			print(f'  {w}')

	# Flag positionMap controls for human review.
	posMapControls = [(name, ctrl) for name, ctrl in sortedControls.items() if 'positionMap' in ctrl]
	if posMapControls:
		print(f'\nReview: {len(posMapControls)} positionMap controls (multiple commands on same arg):')
		for name, ctrl in posMapControls:
			desc = ctrl.get('description', '')
			print(f'  {name}: {desc}')

	print(f'\nOutput: {outFile}')


if __name__ == '__main__':
	main()
