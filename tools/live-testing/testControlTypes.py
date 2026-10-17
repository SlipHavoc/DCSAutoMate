#!/usr/bin/env python3
"""
Test script for systematically testing how DCS handles different control types
using native DCS values (not DCS BIOS values).

This is an interactive test — it sends commands one at a time and queries the resulting
cockpit state, pausing for visual confirmation in DCS between each test.

All output (including your typed responses) is automatically logged to a timestamped file.

Prerequisites:
- DCS running with an F/A-18C cold start mission (both engines off, battery off).
- DCSAutoMateExport.lua active (port 7780).

Usage:
	python testControlTypes.py               # Run all tests interactively
	python testControlTypes.py --test N      # Run only test N (1-based)
	python testControlTypes.py --test N M    # Run tests N and M
	python testControlTypes.py --list        # List all tests
"""

import socket
import time
import sys
import json
import os
from datetime import datetime

host = '127.0.0.1'
port = 7780
timeout = 5.0


# ---- Auto-logging ----

class TeeWriter:
	"""Duplicates writes to both a stream and a log file."""
	def __init__(self, stream, logFile):
		self.stream = stream
		self.logFile = logFile

	def write(self, data):
		self.stream.write(data)
		self.logFile.write(data)
		self.logFile.flush()

	def flush(self):
		self.stream.flush()
		self.logFile.flush()

	def readline(self):
		if hasattr(self.stream, 'readline'):
			return self.stream.readline()
		return ''

originalInput = input

def loggingInput(prompt=''):
	"""Replacement for input() that logs both the prompt and the response."""
	response = originalInput(prompt)
	# The prompt was already written to stdout (and thus logged) by input().
	# Log the user's response to the log file only (it already appeared on screen).
	if hasattr(sys.stdout, 'logFile'):
		sys.stdout.logFile.write(response + '\n')
		sys.stdout.logFile.flush()
	return response

def setupLogging(testNumbers):
	"""Set up tee logging to a timestamped file. Returns the log file path."""
	toolsDir = os.path.dirname(os.path.abspath(__file__))
	timestamp = datetime.now().strftime('%Y-%m-%d_%H%M%S')
	if testNumbers:
		testSuffix = '_tests_' + '_'.join(str(n) for n in testNumbers)
	else:
		testSuffix = '_all'
	logFileName = f'testControlTypes_{timestamp}{testSuffix}.log'
	logPath = os.path.join(toolsDir, logFileName)
	logFile = open(logPath, 'w', encoding='utf-8')
	sys.stdout = TeeWriter(sys.__stdout__, logFile)
	return logPath


# ---- Connection helpers ----

def connect():
	"""Connect to the DCS export script."""
	try:
		sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		sock.settimeout(timeout)
		sock.connect((host, port))
		return sock
	except (ConnectionRefusedError, socket.timeout) as e:
		print(f'Could not connect to DCS at {host}:{port} — {e}')
		print('Make sure DCS is running with a mission loaded and DCSAutoMateExport.lua is active.')
		return None

def send(sock, cmd):
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
	return buf.decode('utf-8').strip()

def query(sock, arg, label=''):
	"""Query an argument value from device 0 (mainpanel). Returns the float value as string."""
	response = send(sock, f'Q:0:{arg}')
	if response.startswith('R:'):
		val = response.split(':')[-1]
		if label:
			print(f'    Q:0:{arg} → {val}  ({label})')
		return val
	else:
		print(f'    Q:0:{arg} → ERROR: {response}')
		return None

def click(sock, dev, cmd, val, label=''):
	"""Send a performClickableAction command (C:). Returns OK/error."""
	command = f'C:{dev}:{cmd}:{val}'
	response = send(sock, command)
	status = 'OK' if response == 'OK' else f'FAIL: {response}'
	if label:
		print(f'    {command}  ({label}) → {status}')
	else:
		print(f'    {command} → {status}')
	return response == 'OK'

def setCmd(sock, dev, cmd, val, label=''):
	"""Send a SetCommand (S:). Returns OK/error."""
	command = f'S:{dev}:{cmd}:{val}'
	response = send(sock, command)
	status = 'OK' if response == 'OK' else f'FAIL: {response}'
	if label:
		print(f'    {command}  ({label}) → {status}')
	else:
		print(f'    {command} → {status}')
	return response == 'OK'

def queryIndication(sock, indicationId):
	"""Query a display indication (T:). Returns raw response string."""
	response = send(sock, f'T:{indicationId}')
	if response.startswith('D:'):
		# Trim the 'D:id:' prefix to get the data.
		parts = response.split(':', 2)
		if len(parts) >= 3:
			return parts[2]
	return response


# ---- UI helpers ----

def pause(msg='Press Enter to continue...'):
	"""Pause for user to observe the cockpit. Returns the user's response text."""
	response = loggingInput(f'  >> {msg} ').strip().lower()
	return response

def isRepeat(response):
	"""Check if a pause() response is a repeat request."""
	return response in ('r', 'rpt', 'repeat')

def countdown(seconds, label=''):
	"""Print a visible countdown so the user can switch to DCS."""
	if label:
		print(f'  >> {label}')
	for i in range(seconds, 0, -1):
		print(f'  >> Starting in {i}...', end='\r')
		time.sleep(1)
	print(f'  >> GO!              ')

def header(testNum, title, description):
	"""Print a test header."""
	print(f'\n{"=" * 70}')
	print(f'TEST {testNum}: {title}')
	print(f'  {description}')
	print(f'{"=" * 70}')
	countdown(5, 'Switch to DCS now!')


# ---- Observe helpers ----

def observeControl(sock, arg, label, positions):
	"""Ask user to move a control to each position, read and record the arg value each time.
	For non-springloaded controls that stay in position."""
	results = {}
	for pos in positions:
		loggingInput(f'  >> Set {label} to {pos}, then press Enter. ')
		time.sleep(0.5)
		val = query(sock, arg, f'{label} in {pos} position')
		results[pos] = val
	print(f'\n    Summary for {label} (arg {arg}):')
	for pos, val in results.items():
		print(f'      {pos:>20s} → arg = {val}')
	return results

def observeHeld(sock, args, label, positions):
	"""For springloaded controls: countdown, user holds during countdown, auto-read at end.
	args can be a single int or a list of ints to read multiple args."""
	if isinstance(args, int):
		args = [args]
	results = {}
	for pos in positions:
		while True:
			print(f'\n    Next: hold {label} to "{pos}"')
			countdown(5, f'HOLD {label} to "{pos}" NOW!')
			vals = {}
			for arg in args:
				val = query(sock, arg, f'{label} in {pos}')
				vals[arg] = val
			response = loggingInput(f'  >> Note (or r to repeat this position, Enter to continue): ').strip().lower()
			if isRepeat(response):
				print('  >> Repeating this position...')
				continue
			results[pos] = vals
			break
	print(f'\n    Summary for {label} (args {args}):')
	for pos, vals in results.items():
		valStr = ', '.join(f'arg {a} = {v}' for a, v in vals.items())
		print(f'      {pos:>25s} → {valStr}')
	return results


# ---- Observe Tests (Tests 1-5) ----

def test01_observeSwitches(sock):
	"""Observe: read DCS arg values for manually positioned switches."""
	header(1, 'Observe Switch Values', 'Manually move switches and record DCS arg values.')
	print('  This test does NOT send any commands.')
	print('  You will be asked to manually move each control to specific positions.')
	print('  After each position, the script reads the arg value from DCS.')

	print('\n  --- BATTERY_SW (arg 404) ---')
	print('  Native: default_3_position_tumb, 3 positions')
	observeControl(sock, 404, 'BATTERY_SW', ['ON (up/forward)', 'OFF (middle)', 'ORIDE (down/aft)'])

	print('\n  --- FLAP_SW (arg 234) ---')
	print('  Native: default_3_position_tumb, 3 positions')
	observeControl(sock, 234, 'FLAP_SW', ['FULL (down)', 'HALF (middle)', 'AUTO (up)'])

	print('\n  --- INS_SW (arg 443) ---')
	print('  Native: multiposition_switch_cl, 8 positions')
	observeControl(sock, 443, 'INS_SW', ['OFF', 'CV', 'GND', 'NAV', 'IFA', 'GYRO', 'GB', 'TEST'])

	print('\n  --- ENGINE_CRANK_SW (arg 377) ---')
	print('  Native: springloaded_3_pos_tumb2 — springs back to center')
	print('  Hold each position during the countdown; value is read when countdown ends.')
	observeHeld(sock, 377, 'ENGINE_CRANK_SW', ['LEFT', 'OFF (release)', 'RIGHT'])

	pause('Review the arg value mappings above.')


def test02_observeCanopy(sock):
	"""Observe: read canopy switch and position arg values."""
	header(2, 'Observe Canopy', 'Manually move canopy switch and record arg values.')
	print('  This test does NOT send any commands.')
	print('  CANOPY_SW arg 453 = switch position, arg 181 = canopy physical position.')
	print('  The switch is springloaded — hold it during the countdown.')
	print('  The canopy itself moves slowly; position arg 181 shows its travel.')

	print('\n  --- CANOPY_SW (arg 453) + CANOPY_POS (arg 181) ---')
	observeHeld(sock, [453, 181], 'CANOPY_SW', ['CLOSE (hold down)', 'HOLD (release)', 'OPEN (hold up)'])

	print('\n  Now wait for canopy to finish moving...')
	loggingInput('  >> When canopy has stopped moving, press Enter. ')
	time.sleep(0.5)
	query(sock, 453, 'switch final')
	query(sock, 181, 'canopy position final')

	pause('Review canopy values above.')


def test03_observePot(sock):
	"""Observe: read CONSOLES_DIMMER arg value at various knob positions."""
	header(3, 'Observe Potentiometer', 'Manually turn CONSOLES_DIMMER and record arg values.')
	print('  This test does NOT send any commands.')
	print('  Turn the CONSOLES_DIMMER knob on the right console.')
	print('  Battery must be ON for console lights to work.')

	print('\n  --- CONSOLES_DIMMER (arg 413) ---')
	observeControl(sock, 413, 'CONSOLES_DIMMER', ['Full CCW (off)', 'About 25%', 'About 50%', 'About 75%', 'Full CW (max)'])

	pause('Review potentiometer values above.')


def test04_observeRadalt(sock):
	"""Observe: read RADALT_HEIGHT arg value at various knob positions."""
	header(4, 'Observe Radar Altimeter Knob', 'Manually turn RADALT_HEIGHT and record arg values.')
	print('  This test does NOT send any commands.')
	print('  Turn the radar altimeter SET knob (lower left panel).')

	print('\n  --- RADALT_HEIGHT (arg 291) ---')
	observeControl(sock, 291, 'RADALT_HEIGHT', ['Full CCW (min)', 'About 25%', 'About 50%', 'About 75%', 'Full CW (max)'])

	pause('Review rotary values above.')


def test05_observeSpringloaded(sock):
	"""Observe: read springloaded switch values while held and after release."""
	header(5, 'Observe Springloaded Switches', 'Read values while held and after release.')
	print('  This test does NOT send any commands.')
	print('  Hold the switch in the indicated direction during the countdown.')
	print('  The value is read automatically when the countdown ends.')

	print('\n  --- AMPCD_NIGHT_DAY (arg 177) ---')
	observeHeld(sock, 177, 'AMPCD_NIGHT_DAY', ['NGT (hold down)', 'Released (center)', 'DAY (hold up)'])

	print('\n  --- AMPCD_GAIN_SW (arg 180) ---')
	observeHeld(sock, 180, 'AMPCD_GAIN_SW', ['DOWN (hold)', 'Released (center)', 'UP (hold)'])

	pause('Review springloaded values above.')


# ---- Native Command Tests (Tests 6-11) ----

def test06_insNativeValues(sock):
	"""Command: INS_SW with native float values (0.0, 0.1, ..., 0.7)."""
	header(6, 'INS_SW with Native Float Values',
		'Test if native arg values (0.0, 0.1, 0.2, ...) work via C:')
	print('  Native positions: OFF=0.0, CV=0.1, GND=0.2, NAV=0.3, IFA=0.4, GYRO=0.5, GB=0.6, TEST=0.7')
	print('  performClickableAction sets ABSOLUTE position.')
	print('  Device 44, cmd 3001, arg 443.')

	val = query(sock, 443, 'initial position')

	# --- Test A ---
	while True:
		print('\n  --- Test A: Native float values via C: ---')
		nativePositions = [
			(0.0, 'OFF'),
			(0.1, 'CV'),
			(0.2, 'GND'),
			(0.3, 'NAV'),
			(0.4, 'IFA'),
			(0.5, 'GYRO'),
			(0.6, 'GB'),
			(0.7, 'TEST'),
		]
		for nativeVal, label in nativePositions:
			click(sock, 44, 3001, nativeVal, f'native {nativeVal} ({label})')
			time.sleep(1.0)
			query(sock, 443, f'arg after {nativeVal}')
		response = pause('Did the INS switch move through all 8 positions?')
		if not isRepeat(response):
			break

	# --- Test B ---
	while True:
		print('\n  --- Test B: Jump to specific positions out of order ---')
		click(sock, 44, 3001, 0.5, 'jump to GYRO (0.5)')
		time.sleep(1.0)
		query(sock, 443, 'after jump to 0.5')
		response = pause('Is INS on GYRO?')
		if isRepeat(response):
			continue

		click(sock, 44, 3001, 0.1, 'jump to CV (0.1)')
		time.sleep(1.0)
		query(sock, 443, 'after jump to 0.1')
		response = pause('Is INS on CV?')
		if isRepeat(response):
			continue

		click(sock, 44, 3001, 0.0, 'reset to OFF (0.0)')
		time.sleep(1.0)
		query(sock, 443, 'after reset to 0.0')
		break

	# --- Test C ---
	while True:
		print('\n  --- Test C: Out-of-range float values ---')
		click(sock, 44, 3001, 0.15, 'val 0.15 — between CV and GND')
		time.sleep(1.0)
		query(sock, 443, 'arg after 0.15 — does it snap to nearest?')
		response = pause('Where did the switch land? (between CV and GND)')
		if isRepeat(response):
			continue

		click(sock, 44, 3001, 0.85, 'val 0.85 — beyond TEST (0.7)')
		time.sleep(1.0)
		query(sock, 443, 'arg after 0.85 — clamped or passed through?')
		response = pause('Where did the switch land? (beyond max)')
		if isRepeat(response):
			continue

		# Reset.
		click(sock, 44, 3001, 0.0, 'reset to OFF')
		time.sleep(1.0)
		break


def test07_dimmerNativeValues(sock):
	"""Command: CONSOLES_DIMMER with native float values via C: and S:."""
	header(7, 'CONSOLES_DIMMER with Native Values',
		'Test native-scale floats (0.0 - 1.0) via both C: and S:')
	print('  Native arg range: 0.0 (off) to 1.0 (max).')
	print('  SetCommand does NOT work for this control. performClickableAction does.')
	print('  Device 9, cmd 3001, arg 413.')

	# Battery on for lights.
	click(sock, 3, 3001, 1, 'battery on')
	time.sleep(1.0)

	val = query(sock, 413, 'initial position')

	# --- Test A ---
	while True:
		print('\n  --- Test A: Native float values via C: (performClickableAction) ---')
		for nativeVal in [0.0, 0.25, 0.5, 0.75, 1.0]:
			click(sock, 9, 3001, nativeVal, f'C: native {nativeVal}')
			time.sleep(1.0)
			query(sock, 413, f'arg after C: {nativeVal}')
		response = pause('Did console lights step through off → 25% → 50% → 75% → max?')
		if not isRepeat(response):
			break

	# --- Test B ---
	while True:
		print('\n  --- Test B: C: reset to 0 then specific values ---')
		click(sock, 9, 3001, 0.0, 'C: reset to 0')
		time.sleep(1.0)
		query(sock, 413, 'arg after C: 0.0')
		response = pause('Console lights off?')
		if isRepeat(response):
			continue

		click(sock, 9, 3001, 0.5, 'C: set to 0.5')
		time.sleep(1.0)
		query(sock, 413, 'arg after C: 0.5')
		response = pause('Console lights at half?')
		if not isRepeat(response):
			break

	# --- Test C ---
	while True:
		print('\n  --- Test C: S: (SetCommand) with native step values ---')
		print('  First reset via C: to 0.')
		click(sock, 9, 3001, 0.0, 'C: reset to 0')
		time.sleep(1.0)
		query(sock, 413, 'arg after C: reset')

		setCmd(sock, 9, 3001, 0.15, 'S: step +0.15 (native step size)')
		time.sleep(1.0)
		query(sock, 413, 'arg after S: +0.15')
		setCmd(sock, 9, 3001, 0.15, 'S: another step +0.15')
		time.sleep(1.0)
		query(sock, 413, 'arg after S: another +0.15')
		response = pause('Did SetCommand do anything with native step values?')
		if not isRepeat(response):
			break

	# --- Test D ---
	while True:
		print('\n  --- Test D: S: with negative step ---')
		setCmd(sock, 9, 3001, -0.15, 'S: step -0.15')
		time.sleep(1.0)
		query(sock, 413, 'arg after S: -0.15')
		response = pause('Did SetCommand step backwards?')
		if not isRepeat(response):
			break

	# --- Test E ---
	while True:
		print('\n  --- Test E: C: out-of-range behavior ---')
		click(sock, 9, 3001, 1.5, 'C: val 1.5 — beyond max')
		time.sleep(1.0)
		query(sock, 413, 'arg after C: 1.5 — clamped to 1.0?')
		click(sock, 9, 3001, -0.5, 'C: val -0.5 — below min')
		time.sleep(1.0)
		query(sock, 413, 'arg after C: -0.5 — clamped to 0.0?')
		response = pause('Did clamping work correctly?')
		if not isRepeat(response):
			break

	# Reset.
	click(sock, 9, 3001, 0.0, 'C: reset to 0')
	time.sleep(1.0)


def test08_flapNativeAbsolute(sock):
	"""Command: FLAP_SW absolute positioning with native values (-1, 0, 1)."""
	header(8, 'FLAP_SW Native Absolute Values',
		'Confirm 3-pos tumb absolute positioning with -1, 0, 1')
	print('  Native positions: FULL=-1, HALF=0, AUTO=1.')
	print('  performClickableAction sets ABSOLUTE position.')
	print('  Device 2, cmd 3007, arg 234.')

	query(sock, 234, 'initial position')

	# --- Test A ---
	while True:
		print('\n  --- Test A: Explicit absolute positioning ---')
		click(sock, 2, 3007, -1, 'C: -1 (FULL down)')
		time.sleep(1.0)
		query(sock, 234, 'arg after C: -1')
		response = pause('Flaps at FULL (down)?')
		if isRepeat(response):
			continue

		click(sock, 2, 3007, 0, 'C: 0 (HALF middle)')
		time.sleep(1.0)
		query(sock, 234, 'arg after C: 0')
		response = pause('Flaps at HALF (middle)?')
		if isRepeat(response):
			continue

		click(sock, 2, 3007, 1, 'C: 1 (AUTO up)')
		time.sleep(1.0)
		query(sock, 234, 'arg after C: 1')
		response = pause('Flaps at AUTO (up)?')
		if not isRepeat(response):
			break

	# --- Test B ---
	while True:
		print('\n  --- Test B: Jump directly (non-sequential) ---')
		click(sock, 2, 3007, -1, 'C: -1 (start at FULL)')
		time.sleep(1.0)
		query(sock, 234, 'at FULL')

		click(sock, 2, 3007, 1, 'C: 1 (jump to AUTO, skipping HALF)')
		time.sleep(1.0)
		query(sock, 234, 'after jumping -1 → 1')
		response = pause('Did flaps jump from FULL directly to AUTO?')
		if isRepeat(response):
			continue

		click(sock, 2, 3007, 0, 'C: 0 (back to HALF)')
		time.sleep(1.0)
		query(sock, 234, 'after jumping 1 → 0')
		response = pause('Did flaps jump from AUTO directly to HALF?')
		if not isRepeat(response):
			break

	# --- Test C ---
	while True:
		print('\n  --- Test C: Out-of-range values ---')
		click(sock, 2, 3007, 2, 'C: 2 — beyond max (1)')
		time.sleep(1.0)
		query(sock, 234, 'arg after C: 2 — clamped to 1?')
		click(sock, 2, 3007, -2, 'C: -2 — below min (-1)')
		time.sleep(1.0)
		query(sock, 234, 'arg after C: -2 — clamped to -1?')
		response = pause('Did clamping work? (2→AUTO, -2→FULL)')
		if not isRepeat(response):
			break


def test09_springloadedCommand(sock):
	"""Command: press/release springloaded switches programmatically."""
	header(9, 'Springloaded Switches via Commands',
		'Verify we can press/release springloaded controls programmatically.')
	print('  springloaded_3_pos_tumb creates TWO BTN-class buttons (cmd1=negative, cmd2=positive).')
	print('  Each button takes value 1 to press, 0 to release. The arg_value/arg_lim in the')
	print('  element definition control where the arg moves — NOT the value we send.')
	print()
	print('  ENGINE_CRANK (dev 12): cmd 3002=LEFT(btn), cmd 3003=RIGHT(btn), arg 377')
	print('  CANOPY_SW (dev 7): cmd 3002=CLOSE(btn), cmd 3001=OPEN(btn), arg 453')
	print('  AMPCD_NIGHT_DAY (dev 37, cmd 3002): custom AMPCD_switch, uses -1/0/1 directly')

	# --- Test A: ENGINE_CRANK ---
	while True:
		print('\n  --- Test A: ENGINE_CRANK_SW — two-button springloaded ---')
		print('  cmd 3002 = EngineCrankLSw (LEFT button), arg_value = -1')
		print('  cmd 3003 = EngineCrankRSw (RIGHT button), arg_value = 1')
		print('  Theory: send value matching arg_value to press (-1 for left, 1 for right)')
		query(sock, 377, 'initial position')

		print('\n  Press LEFT with val -1 (matching arg_value):')
		click(sock, 12, 3002, -1, 'LEFT press with -1')
		time.sleep(1.0)
		query(sock, 377, 'arg after LEFT -1')
		response = pause('Is crank switch held LEFT?')
		if isRepeat(response):
			click(sock, 12, 3002, 0, 'release')
			time.sleep(1.0)
			continue

		print('\n  Release LEFT (val 0):')
		click(sock, 12, 3002, 0, 'LEFT release')
		time.sleep(1.0)
		query(sock, 377, 'arg after release')

		print('\n  Fallback: try LEFT with val 1 (standard BTN press):')
		click(sock, 12, 3002, 1, 'LEFT press with 1')
		time.sleep(1.0)
		query(sock, 377, 'arg after LEFT 1')
		response = pause('Did LEFT work with val 1? (already failed last run)')
		if isRepeat(response):
			click(sock, 12, 3002, 0, 'release')
			time.sleep(1.0)
			continue

		click(sock, 12, 3002, 0, 'release')
		time.sleep(1.0)

		print('\n  Press RIGHT with val 1 (matching arg_value):')
		click(sock, 12, 3003, 1, 'RIGHT press with 1')
		time.sleep(1.0)
		query(sock, 377, 'arg after RIGHT 1')
		response = pause('Is crank switch held RIGHT? (already confirmed)')
		if isRepeat(response):
			click(sock, 12, 3003, 0, 'release')
			time.sleep(1.0)
			continue

		click(sock, 12, 3003, 0, 'RIGHT release')
		time.sleep(1.0)
		query(sock, 377, 'arg after release')
		break

	# --- Test B: CANOPY_SW ---
	while True:
		print('\n  --- Test B: CANOPY_SW — two-button springloaded ---')
		print('  cmd 3002 = CanopySwitchClose (CLOSE button), arg_value = -1')
		print('  cmd 3001 = CanopySwitchOpen (OPEN button), arg_value = 1')
		print('  Theory: send value matching arg_value to press')
		query(sock, 453, 'switch initial')
		query(sock, 181, 'canopy position')

		print('\n  Open canopy (cmd 3001, val 1 — matching arg_value):')
		click(sock, 7, 3001, 1, 'OPEN press with 1')
		time.sleep(2.0)
		query(sock, 453, 'switch while held open')
		query(sock, 181, 'canopy moving?')
		response = pause('Is canopy opening? (already confirmed)')
		if isRepeat(response):
			click(sock, 7, 3001, 0, 'OPEN release')
			time.sleep(1.0)
			continue

		print('\n  Release (cmd 3001, val 0):')
		click(sock, 7, 3001, 0, 'OPEN release')
		time.sleep(1.0)
		query(sock, 453, 'switch after release')
		query(sock, 181, 'canopy position')
		response = pause('Let canopy open a bit, then continue.')
		if isRepeat(response):
			continue

		print('\n  Close canopy with val -1 (matching arg_value):')
		click(sock, 7, 3002, -1, 'CLOSE press with -1')
		time.sleep(2.0)
		query(sock, 453, 'switch while held close')
		query(sock, 181, 'canopy moving back?')
		response = pause('Is canopy closing?')
		if isRepeat(response):
			click(sock, 7, 3002, 0, 'CLOSE release')
			time.sleep(1.0)
			continue

		print('\n  Release (cmd 3002, val 0):')
		click(sock, 7, 3002, 0, 'CLOSE release')
		time.sleep(1.0)
		query(sock, 453, 'switch after release')
		query(sock, 181, 'canopy position')

		print('\n  Fallback: try Close with val 1 (standard BTN):')
		click(sock, 7, 3002, 1, 'CLOSE press with 1')
		time.sleep(2.0)
		query(sock, 453, 'switch while held close')
		query(sock, 181, 'canopy moving?')
		response = pause('Did CLOSE work with val 1? (already failed last run)')
		if isRepeat(response):
			click(sock, 7, 3002, 0, 'CLOSE release')
			time.sleep(1.0)
			continue

		click(sock, 7, 3002, 0, 'CLOSE release')
		time.sleep(1.0)
		query(sock, 453, 'switch after release')
		query(sock, 181, 'canopy final position')
		break

	# --- Test C: AMPCD_NIGHT_DAY ---
	while True:
		print('\n  --- Test C: AMPCD_NIGHT_DAY (custom AMPCD_switch, single cmd 3002) ---')
		print('  This is NOT springloaded_3_pos_tumb — uses custom AMPCD_switch_positive/negative.')
		print('  Takes -1/0/1 directly on a single command. Already confirmed working.')
		query(sock, 177, 'initial')

		click(sock, 37, 3002, -1, 'C: -1 (NGT press)')
		time.sleep(1.0)
		query(sock, 177, 'while held NGT')
		response = pause('AMPCD switch held to NIGHT?')
		if isRepeat(response):
			click(sock, 37, 3002, 0, 'C: 0 (release)')
			time.sleep(1.0)
			continue

		click(sock, 37, 3002, 0, 'C: 0 (release)')
		time.sleep(1.0)
		query(sock, 177, 'after release')
		response = pause('Did it spring back to center?')
		if isRepeat(response):
			continue

		click(sock, 37, 3002, 1, 'C: 1 (DAY press)')
		time.sleep(1.0)
		query(sock, 177, 'while held DAY')
		response = pause('AMPCD switch held to DAY?')
		if isRepeat(response):
			click(sock, 37, 3002, 0, 'C: 0 (release)')
			time.sleep(1.0)
			continue

		click(sock, 37, 3002, 0, 'C: 0 (release)')
		time.sleep(1.0)
		query(sock, 177, 'after release')
		break


def test10_batteryNativeAbsolute(sock):
	"""Command: BATTERY_SW absolute positioning with native -1, 0, 1."""
	header(10, 'BATTERY_SW Native Absolute Values',
		'Verify 3-pos absolute positioning with -1, 0, 1')
	print('  Native positions: ON(up/forward)=1, OFF(middle)=0, ORIDE(down/aft)=-1.')
	print('  Device 3, cmd 3001, arg 404.')

	query(sock, 404, 'initial position')

	# --- Test A ---
	while True:
		print('\n  --- Test A: Native absolute values ---')
		click(sock, 3, 3001, 1, 'C: 1 (ON, up/forward)')
		time.sleep(1.0)
		query(sock, 404, 'arg after C: 1')
		response = pause('Battery ON?')
		if isRepeat(response):
			continue

		click(sock, 3, 3001, 0, 'C: 0 (OFF, middle)')
		time.sleep(1.0)
		query(sock, 404, 'arg after C: 0')
		response = pause('Battery OFF?')
		if isRepeat(response):
			continue

		click(sock, 3, 3001, -1, 'C: -1 (ORIDE, down/aft)')
		time.sleep(1.0)
		query(sock, 404, 'arg after C: -1')
		response = pause('Battery ORIDE?')
		if not isRepeat(response):
			break

	# --- Test B ---
	while True:
		print('\n  --- Test B: Jump test — skip positions ---')
		click(sock, 3, 3001, 1, 'C: 1 (ON)')
		time.sleep(1.0)
		click(sock, 3, 3001, -1, 'C: -1 (jump ON → ORIDE)')
		time.sleep(1.0)
		query(sock, 404, 'arg after 1 → -1 jump')
		response = pause('Did battery jump from ON directly to ORIDE?')
		if not isRepeat(response):
			break

	# Reset.
	click(sock, 3, 3001, 0, 'C: 0 (reset to OFF)')
	time.sleep(1.0)


def test11_rotaryNativeCommands(sock):
	"""Command: RADALT_HEIGHT rotary — SetCommand steps and C: absolute."""
	header(11, 'RADALT_HEIGHT Rotary — Native Commands',
		'Verify SetCommand step behavior and direction for rotary encoder.')
	print('  From observe: full CCW=0.985, full CW=0.105 — INVERTED direction.')
	print('  SetCommand works for rotary encoders (relative steps).')
	print('  Testing: step sizes, direction mapping, and whether C: sets absolute position.')
	print('  Device 30, cmd 3002, arg 291.')

	# Battery on.
	click(sock, 3, 3001, 1, 'battery on')
	time.sleep(1.0)

	val = query(sock, 291, 'initial position')

	# --- Test A ---
	while True:
		print('\n  --- Test A: Reset to known position with large step ---')
		setCmd(sock, 30, 3002, 65535, 'S: 65535 — jump to one limit')
		time.sleep(1.0)
		query(sock, 291, 'arg at +65535 limit')

		setCmd(sock, 30, 3002, -65535, 'S: -65535 — jump to other limit')
		time.sleep(1.0)
		query(sock, 291, 'arg at -65535 limit')
		response = pause('Which direction is which? Check if knob is at min or max altitude.')
		if not isRepeat(response):
			break

	# --- Test B ---
	while True:
		print('\n  --- Test B: Small precise steps and verify direction ---')
		setCmd(sock, 30, 3002, -65535, 'S: -65535 — go to one limit first')
		time.sleep(1.0)
		startVal = query(sock, 291, 'starting position')

		setCmd(sock, 30, 3002, 0.05, 'S: +0.05 step')
		time.sleep(1.0)
		query(sock, 291, 'after +0.05')
		setCmd(sock, 30, 3002, 0.05, 'S: +0.05 step')
		time.sleep(1.0)
		query(sock, 291, 'after another +0.05')
		setCmd(sock, 30, 3002, 0.05, 'S: +0.05 step')
		time.sleep(1.0)
		query(sock, 291, 'after third +0.05')
		response = pause('Did arg change by consistent amounts? Which direction did the knob turn?')
		if not isRepeat(response):
			break

	# --- Test C ---
	while True:
		print('\n  --- Test C: performClickableAction for absolute positioning ---')
		click(sock, 30, 3002, 0.5, 'C: 0.5')
		time.sleep(1.0)
		query(sock, 291, 'arg after C: 0.5 — absolute or relative?')
		click(sock, 30, 3002, 0.0, 'C: 0.0')
		time.sleep(1.0)
		query(sock, 291, 'arg after C: 0.0')
		response = pause('Did C: set absolute position, or act as relative?')
		if not isRepeat(response):
			break


# ---- Test runner ----

allTests = [
	test01_observeSwitches,
	test02_observeCanopy,
	test03_observePot,
	test04_observeRadalt,
	test05_observeSpringloaded,
	test06_insNativeValues,
	test07_dimmerNativeValues,
	test08_flapNativeAbsolute,
	test09_springloadedCommand,
	test10_batteryNativeAbsolute,
	test11_rotaryNativeCommands,
]

def listTests():
	"""Print all available tests."""
	print('Available tests:')
	for i, test in enumerate(allTests, 1):
		doc = test.__doc__ or test.__name__
		title = doc.strip().split('\n')[0]
		print(f'  {i:2d}. {title}')

def runTests(testNumbers=None):
	"""Run specified tests (or all if None)."""
	logPath = setupLogging(testNumbers)

	print('DCSAutoMate — Control Type Tests')
	print('================================')
	print(f'Logging to: {logPath}')
	print(f'Connecting to {host}:{port}...')

	sock = connect()
	if not sock:
		return

	print('Connected!')
	print()
	print('INSTRUCTIONS:')
	print('  - Start DCS with F/A-18C cold start mission (engines off, battery off).')
	print('  - Watch the cockpit while each test runs.')
	print('  - Press Enter when prompted to proceed.')
	print('  - Type "r" at any prompt to repeat the current subtest.')
	print('  - All output is automatically saved to the log file.')
	print()

	tests = allTests if testNumbers is None else [allTests[n - 1] for n in testNumbers]

	for test in tests:
		try:
			test(sock)
		except Exception as e:
			print(f'\n  ERROR in test: {e}')
			import traceback
			traceback.print_exc()
			loggingInput('  >> Press Enter to continue to next test... ')

	print(f'\n{"=" * 70}')
	print('ALL TESTS COMPLETE')
	print(f'{"=" * 70}')
	print()
	print('Findings summary:')
	print('  - performClickableAction (C:) sets ABSOLUTE position for switches and pots.')
	print('  - SetCommand (S:) works for rotary encoders (relative steps), NOT for pots/axes.')
	print('  - Native values: 3-pos = -1/0/1, multipos = 0.0/0.1/.../0.7, pots = 0.0-1.0.')
	print('  - Springloaded: C: -1/0/1 for press/release on most switch types.')
	print('  - No clamping in performClickableAction — out-of-range values pass through.')

	sock.close()
	print('\nDisconnected.')
	print(f'Log saved to: {logPath}')


if __name__ == '__main__':
	if '--list' in sys.argv:
		listTests()
	elif '--test' in sys.argv:
		idx = sys.argv.index('--test')
		if idx + 1 < len(sys.argv):
			nums = [int(n) for n in sys.argv[idx + 1:] if n.isdigit()]
			if nums:
				runTests(nums)
			else:
				print('Usage: testControlTypes.py --test 1 2 3')
		else:
			print('Usage: testControlTypes.py --test 1 2 3')
	else:
		runTests()
