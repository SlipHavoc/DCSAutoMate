#!/usr/bin/env python3
"""Validate a control mapping by testing every control against a running DCS instance.

Connects to DCS via TCP (DCSAutoMateExport.lua must be running), iterates through
all controls in the specified module's controlMappings JSON, and smoke-tests each
one by sending commands and verifying the arg value changes as expected.

Prerequisites:
	- DCS running with a mission loaded (hot start recommended).
	- Active pause enabled (simulation runs but aircraft stays put).
	- DCSAutoMateExport.lua active (installed in DCS Saved Games Scripts).

Usage:
	python tools/validateControlMapping.py --module AH-64D_BLK_II
	python tools/validateControlMapping.py --module FA-18C_hornet --delay 0.1
	python tools/validateControlMapping.py --module Mi-24P --only batterySw,generatorLeft
	python tools/validateControlMapping.py --module AH-64D_BLK_II --skip ejectSeatArm
"""

import argparse
import json
import os
import signal
import socket
import sys
import time

HOST = '127.0.0.1'
PORT = 7780
TIMEOUT = 3.0
TOLERANCE = 0.02        # For float comparisons (pass/fail, range checks).
STABLE_TOLERANCE = 0.0  # Exact-match tolerance for stability detection; DCS arg values are bit-identical at rest.
STABLE_POLL_INTERVAL = 0.05  # Seconds between polls when waiting for animation to settle.
STABLE_MAX_WAIT = 3.0  # Maximum seconds to wait for an arg to stabilize.

DEBUG = False  # Set by --debug flag; prints per-step send/receive traces.


# ---- TCP Communication ----

def connect(host=HOST, port=PORT, timeout=TIMEOUT):
	"""Connect to the DCS export script. Returns a socket."""
	sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	sock.settimeout(timeout)
	sock.connect((host, port))
	return sock


def sendCmd(sock, cmd):
	"""Send a command and return the response line."""
	sock.sendall((cmd + '\n').encode('utf-8'))
	buf = b''
	while True:
		try:
			chunk = sock.recv(4096)
			if not chunk:
				break
			buf += chunk
			if b'\n' in buf:
				break
		except socket.timeout:
			break
	return buf.decode('utf-8').strip().split('\n')[0].strip()


def queryArg(sock, arg):
	"""Query an argument value. Returns float or None."""
	response = sendCmd(sock, f'Q:0:{arg}')
	result = None
	if response.startswith('R:'):
		parts = response.split(':')
		if len(parts) >= 4:
			try:
				result = float(parts[3])
			except ValueError:
				pass
	if DEBUG:
		print(f'    READ  arg={arg} -> {result}')
	return result


def queryIndication(sock, indicationId):
	"""Query an indication. Returns parsed dict or None."""
	response = sendCmd(sock, f'T:{indicationId}')
	if response.startswith('D:'):
		# Format: D:<id>:<json-encoded-string>
		colonPos = response.index(':', 2)
		rawText = response[colonPos + 1:]
		if rawText and rawText != 'null':
			# The Lua export JSON-encodes the indication text, so newlines
			# are escaped as \n (literal backslash-n). Decode to get real newlines.
			try:
				decoded = json.loads(rawText)
			except (json.JSONDecodeError, ValueError):
				decoded = rawText
			return parseIndication(decoded)
	return None


def queryModuleName(sock):
	"""Query the current module name. Returns string or None."""
	response = sendCmd(sock, 'I')
	if response.startswith('I:'):
		return response[2:]
	return None


def performClickableAction(sock, deviceId, commandId, value):
	"""Send a C: command (performClickableAction)."""
	if DEBUG:
		print(f'    SEND C:{deviceId}:{commandId}:{value}')
	return sendCmd(sock, f'C:{deviceId}:{commandId}:{value}')


def setCommand(sock, deviceId, commandId, value, arg=None):
	"""Send an S: command (SetCommand). Includes :arg when provided for defineSetCommandTumb controls."""
	msg = f'S:{deviceId}:{commandId}:{value}'
	if arg is not None:
		msg += f':{arg}'
	return sendCmd(sock, msg)


def parseIndication(rawText):
	"""Parse a DCS list_indication() result into a key-value dict."""
	fields = {}
	lines = rawText.strip().split('\n')
	i = 0
	while i < len(lines):
		line = lines[i].strip()
		if line.startswith('-') and len(line) > 3:
			i += 1
			continue
		if i + 1 < len(lines):
			key = line
			value = lines[i + 1].strip()
			if not value.startswith('-'):
				fields[key] = value
				i += 2
				continue
		i += 1
	return fields


def waitForStable(sock, arg, delay, tolerance=STABLE_TOLERANCE, maxWait=STABLE_MAX_WAIT):
	"""Wait for an arg value to stop changing (animation complete).

	First waits the base delay, then polls until the value stabilizes or
	maxWait is exceeded. Returns the final stable value, or None on read error.
	"""
	time.sleep(delay)
	value = queryArg(sock, arg)
	if value is None:
		return None
	elapsed = delay
	while elapsed < maxWait:
		time.sleep(STABLE_POLL_INTERVAL)
		elapsed += STABLE_POLL_INTERVAL
		newValue = queryArg(sock, arg)
		if newValue is None:
			return value
		if abs(newValue - value) <= tolerance:
			return newValue
		value = newValue
	return value


# ---- Value Translation ----

def translateToNative(control, scriptValue):
	"""Convert a script-convention value to native DCS float.

	Discrete: position index → argLim[0] + step * index
	Continuous: 0.0-1.0 proportion → argLim[0] + proportion * range
	Relative: passthrough
	"""
	controlType = control.get('type', '')
	argLim = control.get('argLim', [0.0, 1.0])

	if controlType == 'discrete':
		step = control.get('step', 1.0)
		return round(argLim[0] + step * float(scriptValue), 10)
	elif controlType == 'continuous':
		proportion = max(0.0, min(1.0, float(scriptValue)))
		return argLim[0] + proportion * (argLim[1] - argLim[0])
	elif controlType == 'relative':
		return float(scriptValue)
	elif controlType == 'toggle':
		return 1.0
	return float(scriptValue)


def reverseTranslateFromNative(control, nativeValue):
	"""Convert a native DCS float back to script-convention value.

	Discrete: native float → position index
	Continuous: native float → 0.0-1.0 proportion
	Read-only: passthrough
	"""
	controlType = control.get('type', '')
	argLim = control.get('argLim', [0.0, 1.0])

	if controlType == 'discrete':
		step = control.get('step', 1.0)
		if step == 0:
			return 0
		return round((nativeValue - argLim[0]) / step)
	elif controlType == 'continuous':
		span = argLim[1] - argLim[0]
		if span == 0:
			return 0.0
		return (nativeValue - argLim[0]) / span
	elif controlType == 'toggle':
		return 1 if abs(nativeValue - argLim[1]) < abs(nativeValue - argLim[0]) else 0
	return nativeValue


def valuesMatch(expected, actual, tolerance=TOLERANCE):
	"""Compare two float values within tolerance."""
	if expected is None or actual is None:
		return False
	return abs(float(expected) - float(actual)) <= tolerance


# ---- Control Testing ----

def testDiscrete(sock, name, control, delay):
	"""Test a discrete control, waiting for animation to settle at each position."""
	arg = control.get('arg')
	deviceId = control.get('deviceId')
	commandId = control.get('commandId')
	positions = control.get('positions', 2)
	step = control.get('step', 1.0)
	argLim = control.get('argLim', [0.0, 1.0])

	if arg is None or deviceId is None or commandId is None:
		return 'skip', 'Missing arg, deviceId, or commandId'

	# Read initial state.
	initialNative = queryArg(sock, arg)
	if initialNative is None:
		return 'error', f'Could not read arg {arg}'

	failures = []

	# Choose send function based on sendProtocol.
	sendProtocol = control.get('sendProtocol', 'C')
	if sendProtocol == 'S':
		sendFn = lambda v: setCommand(sock, deviceId, commandId, v, arg=arg)
	else:
		sendFn = lambda v: performClickableAction(sock, deviceId, commandId, v)

	# Step through all positions.
	for pos in range(positions):
		expectedNative = argLim[0] + step * pos
		nativeValue = translateToNative(control, pos)
		sendFn(nativeValue)
		actualNative = waitForStable(sock, arg, delay)
		if actualNative is None:
			failures.append(f'pos {pos}: read failed')
		elif not valuesMatch(expectedNative, actualNative):
			failures.append(f'pos {pos}: expected {expectedNative:.4f}, got {actualNative:.4f}')

	# Return to initial native arg value.  Read first and skip the send if the
	# arg is already there — toggle-style controls (e.g. animated_guard_switch)
	# flip on every command, so sending initialNative when we're already at
	# initialNative would leave the control in the wrong state.
	currentNative = queryArg(sock, arg)
	if currentNative is None or not valuesMatch(currentNative, initialNative):
		sendFn(initialNative)
		waitForStable(sock, arg, delay)

	if failures:
		return 'fail', '; '.join(failures)
	return 'pass', f'{positions} positions OK'


def testDiscreteIndicator(sock, name, control, delay):
	"""Test an indicator-range discrete control using a forward then backward sweep.

	For controls annotated with indicatorArgLim or indicatorPositions the send
	arg and readback arg are the same slot but use different value scales, so
	we cannot compute an expected readback from the sent value.  Instead we
	check that commanding each position produces some change in the arg.

	We sweep forward (pos 0 → N-1) then backward (pos N-2 → 0).  The last
	position (turnaround) is tested only once in the forward pass; a failure
	there is an overall failure.  For all other positions, a position only
	counts as failed if it showed no change in both directions.  A read error
	at any point is a hard failure.
	"""
	arg = control.get('arg')
	deviceId = control.get('deviceId')
	commandId = control.get('commandId')
	positions = control.get('positions', 2)

	if arg is None or deviceId is None or commandId is None:
		return 'skip', 'Missing arg, deviceId, or commandId'

	# results maps pos -> 'success' | float (the stuck value when unchanged in both directions)
	results = {pos: None for pos in range(positions)}

	def sweepStep(pos):
		preNative = queryArg(sock, arg)
		if preNative is None:
			return None, None, f'pos {pos}: pre-send read failed'
		nativeValue = translateToNative(control, pos)
		performClickableAction(sock, deviceId, commandId, nativeValue)
		postNative = waitForStable(sock, arg, delay)
		if postNative is None:
			return None, None, f'pos {pos}: post-send read failed'
		return preNative != postNative, postNative, None

	for pos in range(positions):
		changed, postNative, errMsg = sweepStep(pos)
		if changed is None:
			return 'error', errMsg
		results[pos] = 'success' if changed else postNative

	for pos in range(positions - 2, -1, -1):
		changed, postNative, errMsg = sweepStep(pos)
		if changed is None:
			return 'error', errMsg
		if changed:
			results[pos] = 'success'
		elif results[pos] != 'success':
			results[pos] = postNative

	failures = [pos for pos, r in results.items() if r != 'success']
	if failures:
		posStr = ', '.join(f'pos {p}: arg stuck at {results[p]:.4f}' for p in sorted(failures))
		return 'fail', f'{posStr} (indicator-range; check manually)'
	return 'pass', f'{positions} positions OK (indicator-range; exact value not verified)'


def testDiscretePositionMap(sock, name, control, delay):
	"""Test a positionMap discrete control. Returns (status, details)."""
	arg = control.get('arg')
	posMap = control.get('positionMap', [])

	if arg is None:
		return 'skip', 'Missing arg'
	if not posMap:
		return 'skip', 'Empty positionMap'

	# Read initial state.
	initialNative = queryArg(sock, arg)
	if initialNative is None:
		return 'error', f'Could not read arg {arg}'

	failures = []

	# Find the null/center index for releasing.
	centerIdx = None
	for i, entry in enumerate(posMap):
		if entry is None:
			centerIdx = i
			break

	# Test each non-null position.
	for i, entry in enumerate(posMap):
		if entry is None:
			continue
		if 'deviceId' not in entry or 'commandId' not in entry:
			# Value-only sentinel: exists for display/readback but cannot be
			# commanded via this control (e.g. pos 2 of a _SwB_EXT where pos 2
			# requires a different _SwA_EXT command).  Skip without failing.
			continue

		deviceId = entry['deviceId']
		commandId = entry['commandId']
		# pdp_special entries use sendValue/readbackValue to distinguish the
		# trigger value sent (e.g. 0.9) from the stable arg after the device
		# snaps (e.g. 1.0).  Plain entries use 'value' for both.
		sendValue = entry.get('sendValue', entry.get('value'))
		readbackValue = entry.get('readbackValue', entry.get('value'))

		# Read pre-action state.
		preNative = queryArg(sock, arg)

		# Send the command.
		performClickableAction(sock, deviceId, commandId, sendValue)
		postNative = waitForStable(sock, arg, delay)
		if postNative is None:
			failures.append(f'pos {i}: read failed after send')
		elif valuesMatch(preNative, postNative) and not valuesMatch(preNative, readbackValue):
			# Arg didn't change AND wasn't already at the expected readback — failure.
			failures.append(f'pos {i}: arg unchanged at {postNative:.4f}')

		# Release (send 0 to all commands for this position).
		performClickableAction(sock, deviceId, commandId, 0.0)
		waitForStable(sock, arg, delay)

	# Restore to initial state.  For pdp_special entries sendValue != readbackValue,
	# so find the entry whose readbackValue matches initialNative and send its
	# sendValue.  For plain entries value == sendValue == readbackValue.
	currentNative = queryArg(sock, arg)
	if currentNative is not None and not valuesMatch(currentNative, initialNative):
		restoreSend = initialNative
		for entry in posMap:
			if entry is None or 'commandId' not in entry:
				continue
			rb = entry.get('readbackValue', entry.get('value'))
			sv = entry.get('sendValue', entry.get('value'))
			if rb is not None and valuesMatch(rb, initialNative):
				restoreSend = sv
				break
		firstEntry = next((e for e in posMap if e and 'commandId' in e), None)
		if firstEntry:
			performClickableAction(sock, firstEntry['deviceId'], firstEntry['commandId'], restoreSend)
			waitForStable(sock, arg, delay)
			performClickableAction(sock, firstEntry['deviceId'], firstEntry['commandId'], 0.0)
			waitForStable(sock, arg, delay)

	if failures:
		return 'fail', '; '.join(failures)
	return 'pass', f'{sum(1 for e in posMap if e is not None)} positions OK'


def testContinuous(sock, name, control, delay):
	"""Test a continuous control at 5 positions, waiting for animation to settle."""
	arg = control.get('arg')
	deviceId = control.get('deviceId')
	commandId = control.get('commandId')
	argLim = control.get('argLim', [0.0, 1.0])

	if arg is None or deviceId is None or commandId is None:
		return 'skip', 'Missing arg, deviceId, or commandId'

	# Read initial state.
	initialNative = queryArg(sock, arg)
	if initialNative is None:
		return 'error', f'Could not read arg {arg}'

	failures = []
	actualValues = {}
	testPoints = [0.0, 0.25, 0.5, 0.75, 1.0]

	for proportion in testPoints:
		nativeValue = argLim[0] + proportion * (argLim[1] - argLim[0])
		performClickableAction(sock, deviceId, commandId, nativeValue)
		actualNative = waitForStable(sock, arg, delay)
		actualValues[proportion] = actualNative
		if actualNative is None:
			failures.append(f'{proportion:.0%}: read failed')
		elif not valuesMatch(nativeValue, actualNative):
			failures.append(f'{proportion:.0%}: expected {nativeValue:.4f}, got {actualNative:.4f}')

	# Return to initial value.
	performClickableAction(sock, deviceId, commandId, initialNative)
	waitForStable(sock, arg, delay)

	if failures:
		# Report actual range if control moved but didn't reach expected values.
		actuals = [v for v in actualValues.values() if v is not None]
		if len(actuals) >= 2:
			actualMin = min(actuals)
			actualMax = max(actuals)
			if actualMax > actualMin + TOLERANCE:
				return 'fail', f'{"; ".join(failures)} (actual range [{actualMin:.4f}, {actualMax:.4f}] vs expected [{argLim[0]}, {argLim[1]}])'
		return 'fail', '; '.join(failures)
	return 'pass', f'{len(testPoints)} positions OK'


def testWheel(sock, name, control, delay):
	"""Test a wheel control (radio_wheel / radio_wheel_1: 2-button increment/decrement rotary).

	Sends one increment click and verifies the arg advanced by +step (with
	wraparound from argLim[1] back to argLim[0]); then sends one decrement
	click and verifies the arg returned to its initial value.  Sending the
	literal cockpit-click value (incrementValue / decrementValue) works for
	both absolute-set and relative-add runtime handlers.

	Handles two patterns:
	  radio_wheel_1 (Mi-8/Mi-24): single commandId for both directions; the
	    pulse arg and display arg are the same.
	  radio_wheel (A-10C): separate commandId (increment) and decrementCommandId
	    (decrement); the display arg is displayArgs[0] when present and differs
	    from the pulse arg.
	"""
	arg = control.get('arg')
	deviceId = control.get('deviceId')
	commandId = control.get('commandId')
	argLim = control.get('argLim', [0.0, 1.0])
	incValue = control.get('incrementValue')
	decValue = control.get('decrementValue')

	if arg is None or deviceId is None or commandId is None or incValue is None or decValue is None:
		return 'skip', 'Missing arg/deviceId/commandId/incrementValue/decrementValue'

	# For radio_wheel (dual-command) elements the displayed state lives in
	# displayArgs[0]; fall back to arg for radio_wheel_1 (same-command) elements.
	displayArgs = control.get('displayArgs')
	readArg = displayArgs[0] if displayArgs else arg

	# For radio_wheel (dual-command) elements the decrement direction has its
	# own command; fall back to commandId for radio_wheel_1 elements.
	decCommandId = control.get('decrementCommandId', commandId)

	# 'step' overrides abs(incValue) when the display arg step differs from the
	# command value (e.g. FREQ-1 VHF knob: sends 0.1 but display arg moves 0.05).
	step = control.get('step', abs(incValue))
	if step <= 0:
		return 'skip', 'Zero step'
	rng = argLim[1] - argLim[0]
	positions = round(rng / step) + 1 if rng > 0 else 2

	initialNative = queryArg(sock, readArg)
	if initialNative is None:
		return 'error', f'Could not read arg {readArg}'

	def expectedAfterDelta(currentNative, delta):
		# Step from the empirically-read current position rather than computing
		# an absolute index from argLim[0].  This handles cases where the actual
		# cockpit position grid is offset from argLim[0] by a fraction of a step
		# (e.g. A-10C VHF FREQ-1: argLim is [0.125, 0.775] for visual rendering
		# but actual positions are at 0.150, 0.200, ... 0.750 -- half-step inset).
		# Wrap modulo the argLim range size, which is consistent regardless of
		# where the grid origin sits within argLim.
		newValue = currentNative + delta * step
		rng = argLim[1] - argLim[0]
		if rng > 0:
			eps = step * 0.1
			while newValue > argLim[1] + eps:
				newValue -= rng
			while newValue < argLim[0] - eps:
				newValue += rng
		return newValue

	failures = []

	# Use per-control settleDelay when the animation is slow (e.g. FREQ-4 VHF
	# radio knob takes ~0.5s to reach its final position).  Overrides the
	# global delay so waitForStable doesn't read an intermediate animation value.
	effectiveDelay = max(delay, control.get('settleDelay', 0.0))

	# Increment one step.
	performClickableAction(sock, deviceId, commandId, incValue)
	afterInc = waitForStable(sock, readArg, effectiveDelay)
	expectedInc = expectedAfterDelta(initialNative, +1)
	if afterInc is None:
		failures.append('inc: read failed')
	elif not valuesMatch(expectedInc, afterInc):
		failures.append(f'inc: expected {expectedInc:.4f}, got {afterInc:.4f}')

	# Decrement one step (back to start).
	performClickableAction(sock, deviceId, decCommandId, decValue)
	afterDec = waitForStable(sock, readArg, effectiveDelay)
	if afterDec is None:
		failures.append('dec: read failed')
	elif not valuesMatch(initialNative, afterDec):
		failures.append(f'dec: expected {initialNative:.4f}, got {afterDec:.4f}')

	if failures:
		return 'fail', '; '.join(failures)
	return 'pass', f'wheel OK ({positions} positions, step {step})'


def testRelative(sock, name, control, delay):
	"""Test a relative control with increment/decrement. Returns (status, details)."""
	arg = control.get('arg')
	deviceId = control.get('deviceId')
	commandId = control.get('commandId')

	if arg is None or deviceId is None or commandId is None:
		return 'skip', 'Missing arg, deviceId, or commandId'

	# Use the correct protocol for this control.
	sendProtocol = control.get('sendProtocol', 'S')
	if sendProtocol == 'C':
		sendFn = performClickableAction
	else:
		sendFn = setCommand

	# Read initial state.
	initialNative = queryArg(sock, arg)
	if initialNative is None:
		return 'error', f'Could not read arg {arg}'

	failures = []

	# Derive step from incValue (exact value from input files) or half argLim range as fallback.
	incValue = control.get('incValue')
	argLim = control.get('argLim', [-1.0, 1.0])
	step = incValue if incValue is not None else abs(argLim[1] - argLim[0]) / 2
	# If the initial value is at the ceiling, test decrement instead to avoid a false "no effect".
	if initialNative >= argLim[1]:
		testStep, restoreStep, dirLabel = -step, step, 'decrement'
	else:
		testStep, restoreStep, dirLabel = step, -step, 'increment'
	sendFn(sock, deviceId, commandId, testStep)
	afterMove = waitForStable(sock, arg, delay)
	if afterMove is None:
		failures.append(f'read failed after {dirLabel}')
	elif initialNative == afterMove:
		# Primary direction had no effect (control may be at the real range boundary).
		# Try the opposite direction before declaring failure.
		sendFn(sock, deviceId, commandId, restoreStep)
		afterOpposite = waitForStable(sock, arg, delay)
		if afterOpposite is not None and afterOpposite != initialNative:
			# Opposite direction worked -- undo and pass.
			sendFn(sock, deviceId, commandId, testStep)
			waitForStable(sock, arg, delay)
		else:
			failures.append(f'{dirLabel} had no effect (stayed at {afterMove:.4f})')

	else:
		# Primary direction worked -- restore.
		sendFn(sock, deviceId, commandId, restoreStep)
		waitForStable(sock, arg, delay)

	if failures:
		return 'fail', '; '.join(failures)
	return 'pass', 'increment/decrement OK'


def testReadOnlyArg(sock, name, control, delay):
	"""Test a read-only arg control. Returns (status, details)."""
	arg = control.get('arg')
	if arg is None:
		return 'skip', 'Missing arg'

	value = queryArg(sock, arg)
	if value is None:
		return 'error', f'Could not read arg {arg}'

	argLim = control.get('argLim')
	if argLim:
		if value < argLim[0] - TOLERANCE or value > argLim[1] + TOLERANCE:
			return 'fail', f'arg {arg} = {value:.4f}, outside range [{argLim[0]}, {argLim[1]}]'

	return 'pass', f'arg {arg} = {value:.4f}'


def testReadOnlyIndication(sock, name, control, delay, declaredFields=None):
	"""Test a read-only indication control. Returns (status, details).

	When ``declaredFields`` is provided it maps indicationId to the set of
	field names the extraction pipeline harvested from the DCS native Lua.
	If the requested field is declared there but not currently emitted by
	``list_indication()``, the result is reported as 'skip' rather than 'fail'
	— the field exists in the cockpit code, it is just not active right now
	(e.g. conditional text like ``txt_autopilot`` that only appears when the
	autopilot is engaged, or ``txt_ammo0`` which only appears when the gunner
	has ammo loaded).
	"""
	indicationId = control.get('indicationId')
	fieldName = control.get('fieldName')
	if indicationId is None or fieldName is None:
		return 'skip', 'Missing indicationId or fieldName'

	indication = queryIndication(sock, indicationId)
	if indication is None:
		return 'fail', f'indication {indicationId} returned None'

	if fieldName in indication:
		return 'pass', f'field "{fieldName}" = "{indication[fieldName]}"'

	fieldList = list(indication.keys())
	shown = fieldList[:5]
	suffix = f', ... ({len(fieldList)} total)' if len(fieldList) > 5 else ''

	if declaredFields is not None:
		declaredForInd = declaredFields.get(indicationId)
		if declaredForInd is not None and fieldName in declaredForInd:
			return 'skip', f'field "{fieldName}" declared in extraction but not currently emitted by indication {indicationId}'

	return 'fail', f'field "{fieldName}" not found in indication {indicationId} (fields: {shown}{suffix})'


def testToggle(sock, name, control, delay):
	"""Test a toggle control — fires the command twice, verifies both state changes."""
	arg = control.get('arg')
	deviceId = control.get('deviceId')
	commandId = control.get('commandId')
	argLim = control.get('argLim', [0.0, 1.0])

	if arg is None or deviceId is None or commandId is None:
		return 'skip', 'Missing arg, deviceId, or commandId'

	sendFn = lambda v: performClickableAction(sock, deviceId, commandId, v)

	initial = queryArg(sock, arg)
	if initial is None:
		return 'error', f'Could not read arg {arg}'

	# Normalise to low state (argLim[0]) before testing.
	if not valuesMatch(initial, argLim[0]):
		sendFn(1.0)
		current = waitForStable(sock, arg, delay)
		if not valuesMatch(current, argLim[0]):
			return 'fail', f'Could not normalise to state 0 (got {current:.4f})'

	# Toggle 0→1.
	sendFn(1.0)
	after1 = waitForStable(sock, arg, delay)
	if not valuesMatch(after1, argLim[1]):
		return 'fail', f'0→1: expected {argLim[1]:.4f}, got {after1:.4f}'

	# Toggle 1→0.
	sendFn(1.0)
	after2 = waitForStable(sock, arg, delay)
	if not valuesMatch(after2, argLim[0]):
		return 'fail', f'1→0: expected {argLim[0]:.4f}, got {after2:.4f}'

	# Restore initial state if it was high (1).
	if not valuesMatch(initial, argLim[0]):
		sendFn(1.0)
		waitForStable(sock, arg, delay)

	return 'pass', 'toggle 0→1→0 OK'


def testControl(sock, name, control, delay, declaredFields=None):
	"""Route to the appropriate test function based on control type."""
	controlType = control.get('type', '')

	if control.get('arg') == -1:
		return 'skip', 'arg=-1 (pure encoder, no readable cockpit position)'

	if controlType == 'raw':
		return 'skip', 'type=raw (AI crew command; no known values to validate)'

	if controlType == 'discrete':
		if 'positionMap' in control:
			return testDiscretePositionMap(sock, name, control, delay)
		if 'indicatorArgLim' in control or 'indicatorPositions' in control:
			return testDiscreteIndicator(sock, name, control, delay)
		return testDiscrete(sock, name, control, delay)
	elif controlType == 'continuous':
		return testContinuous(sock, name, control, delay)
	elif controlType == 'relative':
		if control.get('wheel'):
			return testWheel(sock, name, control, delay)
		return testRelative(sock, name, control, delay)
	elif controlType == 'toggle':
		return testToggle(sock, name, control, delay)
	else:
		# Read-only.
		if 'indicationId' in control:
			return testReadOnlyIndication(sock, name, control, delay, declaredFields)
		elif 'arg' in control:
			return testReadOnlyArg(sock, name, control, delay)
		else:
			return 'skip', 'No type, arg, or indicationId'


# ---- Guard/Cover Handling ----

# Substrings searched (case-insensitive) in control names to identify guard /
# cover clickables that should be opened before testing.  'cvr' is the
# abbreviation used by the F-16C and Mi-24P modules.
#
# We match on name only (not description): descriptions are often shared
# between a cover control and the underlying switch (e.g. FA-18C fire handles
# `LENG_FireSw` and `LENG_FireSwCover` share a description mentioning "cover
# control"), so description-matching would cause the validator to "open" the
# underlying switch as well, pulling the fire handle.
GUARD_KEYWORDS = ('cover', 'guard', 'cvr')


def isGuardControl(name, control):
	"""Check if a control is a guard/cover that can be opened."""
	lower = name.lower()
	if not any(kw in lower for kw in GUARD_KEYWORDS):
		return False
	# Only actionable discrete controls with a type.
	if control.get('type') != 'discrete':
		return False
	if control.get('deviceId') is None or control.get('commandId') is None:
		return False
	return True


def openGuards(sock, controls, delay):
	"""Open all guard/cover controls by setting them to their max position.

	Returns a list of (name, control) pairs that were opened, so they can be
	closed later if needed.
	"""
	guardNames = sorted(n for n, c in controls.items() if isGuardControl(n, c))
	if not guardNames:
		return []

	openDelay = max(delay, 0.3)  # Guards often animate slowly.
	opened = []
	print(f'Opening {len(guardNames)} guards/covers...')
	for name in guardNames:
		control = controls[name]
		argLim = control.get('argLim', [0.0, 1.0])
		deviceId = control.get('deviceId')
		commandId = control.get('commandId')
		# Open = max position.
		openValue = argLim[1]
		performClickableAction(sock, deviceId, commandId, openValue)
		opened.append((name, control))
	# Single wait after all commands, since they run in parallel in DCS.
	time.sleep(openDelay)

	# Verify they opened.
	verified = 0
	for name, control in opened:
		arg = control.get('arg')
		if arg is not None:
			actual = queryArg(sock, arg)
			argLim = control.get('argLim', [0.0, 1.0])
			if actual is not None and valuesMatch(argLim[1], actual):
				verified += 1
			else:
				print(f'  Warning: {name} may not have opened (arg {arg} = {actual})')
	print(f'  {verified}/{len(opened)} verified open.')
	print()
	return opened


def closeGuards(sock, opened, delay):
	"""Close previously opened guards by returning them to their min position."""
	if not opened:
		return
	closeDelay = max(delay, 0.3)
	for name, control in opened:
		argLim = control.get('argLim', [0.0, 1.0])
		deviceId = control.get('deviceId')
		commandId = control.get('commandId')
		performClickableAction(sock, deviceId, commandId, argLim[0])
	time.sleep(closeDelay)


# ---- Main ----

def loadControlMapping(moduleName):
	"""Load the control mapping JSON for a module."""
	repoRoot = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
	mappingPath = os.path.join(repoRoot, 'config', 'controlMappings', f'{moduleName}.json')
	if not os.path.exists(mappingPath):
		print(f'Error: Control mapping not found: {mappingPath}', file=sys.stderr)
		sys.exit(1)
	with open(mappingPath, 'r', encoding='utf-8') as f:
		return json.load(f)


def loadDeclaredIndicationFields(moduleName):
	"""Load the set of indication fields declared in the native extraction.

	Returns a dict mapping indicationId (int) to a set of field name strings.
	If the extraction file is not present, returns an empty dict; callers
	should treat a missing entry as "no declaration known."
	"""
	repoRoot = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
	extractionPath = os.path.join(repoRoot, 'config', 'nativeExtractions', f'{moduleName}.json')
	if not os.path.exists(extractionPath):
		return {}
	with open(extractionPath, 'r', encoding='utf-8') as f:
		extraction = json.load(f)
	declared = {}
	for ind in extraction.get('indicators', []):
		idx = ind.get('index')
		if idx is None:
			continue
		declared[idx] = set(ind.get('fields', []))
	return declared


def main():
	parser = argparse.ArgumentParser(
		description='Validate a control mapping against a running DCS instance.',
		formatter_class=argparse.RawDescriptionHelpFormatter,
		epilog='Run with DCS in active pause on a hot-started aircraft.',
	)
	parser.add_argument('--module', required=True, help='Module name (e.g. AH-64D_BLK_II, FA-18C_hornet, Mi-24P)')
	parser.add_argument('--delay', type=float, default=0.08, help='Seconds to wait after each command (default: 0.08)')
	parser.add_argument('--skip', default='', help='Comma-separated control names to skip')
	parser.add_argument('--only', default='', help='Comma-separated control names to test (or a file containing comma- or newline-separated names)')
	parser.add_argument('--verbose', action='store_true', help='Print details for every control, not just failures')
	parser.add_argument('--debug', action='store_true', help='Print per-step send/receive traces for each control')
	parser.add_argument('--json-output', help='Write machine-readable results to this JSON file')
	parser.add_argument('--no-open-guards', action='store_true', help='Skip auto-opening guards/covers before testing')
	parser.add_argument('--host', default=HOST, help=f'DCS host (default: {HOST})')
	parser.add_argument('--port', type=int, default=PORT, help=f'DCS port (default: {PORT})')
	args = parser.parse_args()

	global DEBUG
	DEBUG = args.debug

	# Load control mapping.
	mapping = loadControlMapping(args.module)
	controls = mapping.get('controls', {})
	if not controls:
		print('Error: No controls found in mapping.', file=sys.stderr)
		sys.exit(1)

	# Load declared indication fields from the native extraction so that
	# fields which exist in the cockpit code but are not currently being
	# emitted (e.g. conditional text like txt_autopilot when AP is off)
	# can be reported as 'skip' instead of 'fail'.
	declaredFields = loadDeclaredIndicationFields(args.module)

	# Parse skip/only lists.
	skipSet = set(s.strip() for s in args.skip.split(',') if s.strip())
	if args.only and os.path.isfile(args.only):
		with open(args.only, encoding='utf-8') as f:
			rawOnly = f.read()
		onlySet = set(s.strip() for s in rawOnly.replace(',', '\n').splitlines() if s.strip())
	else:
		onlySet = set(s.strip() for s in args.only.split(',') if s.strip())

	# Filter controls.
	controlNames = sorted(controls.keys())
	if onlySet:
		controlNames = [n for n in controlNames if n in onlySet]
	controlNames = [n for n in controlNames if n not in skipSet]

	# Exclude type=raw controls — we don't know what values to send or expect.
	rawNames = set(n for n in controlNames if controls[n].get('type') == 'raw')
	controlNames = [n for n in controlNames if n not in rawNames]

	# Separate guard/cover controls so they are tested after the main loop,
	# when all covers are still open, not interleaved with other controls.
	guardNames = sorted(n for n in controlNames if isGuardControl(n, controls[n]))
	guardNameSet = set(guardNames)
	controlNames = [n for n in controlNames if n not in guardNameSet]

	print(f'Module: {args.module}')
	print(f'Controls to test: {len(controlNames)} of {len(controls)}')
	if rawNames:
		print(f'Excluded: {len(rawNames)} type=raw (AI crew commands; no values to validate)')
	print(f'Delay: {args.delay}s')
	print()

	# Connect to DCS.
	print(f'Connecting to DCS at {args.host}:{args.port}...')
	try:
		sock = connect(args.host, args.port, TIMEOUT)
	except (ConnectionRefusedError, socket.timeout, OSError) as e:
		print(f'Error: Could not connect — {e}', file=sys.stderr)
		print('Make sure DCS is running with a mission loaded and DCSAutoMateExport.lua is active.', file=sys.stderr)
		sys.exit(1)
	print('Connected.')

	# Verify module.
	dcsModule = queryModuleName(sock)
	if dcsModule:
		if dcsModule != args.module:
			print(f'Warning: DCS reports module "{dcsModule}", expected "{args.module}"', file=sys.stderr)
		else:
			print(f'Module confirmed: {dcsModule}')
	else:
		print('Warning: Could not query module name from DCS.', file=sys.stderr)
	print()

	# Open guards/covers before testing so guarded buttons are accessible.
	openedGuards = []
	if not args.no_open_guards:
		openedGuards = openGuards(sock, controls, args.delay)

	# Set up interrupt handler.
	interrupted = False
	def handleInterrupt(signum, frame):
		nonlocal interrupted
		interrupted = True
		print('\nInterrupted! Finishing current control...', file=sys.stderr)
	signal.signal(signal.SIGINT, handleInterrupt)

	# Run tests.
	results = []
	counts = {'pass': 0, 'fail': 0, 'skip': 0, 'error': 0}
	startTime = time.time()

	for i, name in enumerate(controlNames):
		if interrupted:
			# Mark remaining as skipped.
			for remaining in controlNames[i:]:
				results.append({'name': remaining, 'status': 'skip', 'details': 'Interrupted'})
				counts['skip'] += 1
			break

		control = controls[name]
		status, details = testControl(sock, name, control, args.delay, declaredFields)
		results.append({'name': name, 'status': status, 'details': details})
		counts[status] += 1

		# Progress output.
		if status == 'fail' or status == 'error':
			print(f'  [{status.upper():5}] {name}: {details}')
		elif args.verbose:
			print(f'  [{status.upper():5}] {name}: {details}')
		elif (i + 1) % 50 == 0:
			elapsed = time.time() - startTime
			print(f'  ... {i + 1}/{len(controlNames)} tested ({elapsed:.1f}s)')

	elapsed = time.time() - startTime

	# Test guard/cover controls now that the main loop is done and all covers
	# are still in their open state.
	if guardNames:
		print()
		print(f'Testing {len(guardNames)} guards/covers...')
		for name in guardNames:
			if interrupted:
				for remaining in guardNames[guardNames.index(name):]:
					results.append({'name': remaining, 'status': 'skip', 'details': 'Interrupted'})
					counts['skip'] += 1
				break
			control = controls[name]
			status, details = testControl(sock, name, control, args.delay, declaredFields)
			results.append({'name': name, 'status': status, 'details': details})
			counts[status] += 1
			if status == 'fail' or status == 'error':
				print(f'  [{status.upper():5}] {name}: {details}')
			elif args.verbose:
				print(f'  [{status.upper():5}] {name}: {details}')

	# Close guards that were opened.
	if openedGuards:
		print()
		print('Closing guards/covers...')
		closeGuards(sock, openedGuards, args.delay)

	sock.close()

	# Summary.
	print()
	print(f'Results ({elapsed:.1f}s):')
	print(f'  Pass:  {counts["pass"]}')
	print(f'  Fail:  {counts["fail"]}')
	print(f'  Skip:  {counts["skip"]}')
	print(f'  Error: {counts["error"]}')
	print(f'  Total: {len(results)}')

	# JSON output.
	if args.json_output:
		output = {
			'module': args.module,
			'timestamp': time.strftime('%Y-%m-%dT%H:%M:%S'),
			'delay': args.delay,
			'elapsed': round(elapsed, 1),
			'counts': counts,
			'results': results,
		}
		with open(args.json_output, 'w', encoding='utf-8') as f:
			json.dump(output, f, indent='\t', ensure_ascii=False)
		print(f'\nJSON results written to: {args.json_output}')

	# Exit code: 1 if any failures.
	sys.exit(1 if counts['fail'] > 0 else 0)


if __name__ == '__main__':
	main()
