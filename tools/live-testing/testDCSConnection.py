#!/usr/bin/env python3
"""
Test client for DCSAutoMateExport.lua.

Connects to DCS via TCP and tests the direct communication protocol.
Run this while DCS is running with a mission loaded and the export script active.

Usage:
	python testDCSConnection.py                  # Run interactive mode
	python testDCSConnection.py --test           # Run automated test sequence
	python testDCSConnection.py --cmd "C:3:3001:1"  # Send a single command
"""

import socket
import time
import sys
import json

host = '127.0.0.1'
port = 7780
timeout = 5.0

def connect():
	"""Connect to the DCS export script. Returns a socket or None."""
	try:
		sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		sock.settimeout(timeout)
		sock.connect((host, port))
		return sock
	except (ConnectionRefusedError, socket.timeout) as e:
		print(f'Could not connect to DCS at {host}:{port} — {e}')
		print('Make sure DCS is running with a mission loaded and DCSAutoMateExport.lua is active.')
		return None

def sendCmd(sock, cmd):
	"""Send a command and return the response line."""
	sock.sendall((cmd + '\n').encode('utf-8'))
	# Read response.
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
	response = buf.decode('utf-8').strip()
	return response

def testIdentification(sock):
	"""Test module identification query."""
	print('\n--- Module Identification ---')
	response = sendCmd(sock, 'I')
	print(f'  Response: {response}')
	if response.startswith('I:'):
		moduleName = response[2:]
		print(f'  Module: {moduleName}')
		return True
	else:
		print('  FAILED: unexpected response')
		return False

def testQuery(sock, device, arg, label=''):
	"""Test an on-demand state query."""
	cmd = f'Q:{device}:{arg}'
	response = sendCmd(sock, cmd)
	if response.startswith('R:'):
		val = response.split(':')[-1]
		prefix = f'  {label}: ' if label else '  '
		print(f'{prefix}{cmd} → {val}')
		return val
	else:
		print(f'  Query {cmd} failed: {response}')
		return None

def testEngineInfo(sock):
	"""Test engine info query."""
	print('\n--- Engine Info ---')
	response = sendCmd(sock, 'E')
	if response.startswith('E:'):
		data = response[2:]
		if data != 'null':
			try:
				info = json.loads(data)
				print(f'  Engine data received: {json.dumps(info, indent=2)[:500]}')
			except json.JSONDecodeError:
				print(f'  Raw engine data: {data[:200]}')
		else:
			print('  No engine data available (engines off?)')
		return True
	else:
		print(f'  FAILED: {response}')
		return False

def testCommand(sock, device, command, value, label=''):
	"""Test sending a cockpit command."""
	cmd = f'C:{device}:{command}:{value}'
	response = sendCmd(sock, cmd)
	prefix = f'  {label}: ' if label else '  '
	print(f'{prefix}{cmd} → {response}')
	return response == 'OK'

def testSetCommand(sock, device, command, value, label=''):
	"""Test sending a SetCommand (for potentiometers/axes)."""
	cmd = f'S:{device}:{command}:{value}'
	response = sendCmd(sock, cmd)
	prefix = f'  {label}: ' if label else '  '
	print(f'{prefix}{cmd} → {response}')
	return response == 'OK'

def testSubscription(sock, device, arg, interval=0.1, duration=1.0, label=''):
	"""Test subscribing to an argument and reading updates."""
	prefix = f'  {label}: ' if label else '  '

	# Subscribe.
	subCmd = f'W:{device}:{arg}:{interval}'
	response = sendCmd(sock, subCmd)
	if response != 'OK':
		print(f'{prefix}Subscribe failed: {response}')
		return False

	print(f'{prefix}Subscribed to {device}:{arg}, listening for {duration}s...')

	# Listen for updates.
	buf = b''
	startTime = time.time()
	updates = []
	sock.settimeout(interval * 2)
	while time.time() - startTime < duration:
		try:
			chunk = sock.recv(4096)
			if chunk:
				buf += chunk
				while b'\n' in buf:
					line, buf = buf.split(b'\n', 1)
					decoded = line.decode('utf-8').strip()
					if decoded.startswith('U:'):
						updates.append(decoded)
		except socket.timeout:
			continue

	# Unsubscribe.
	sock.settimeout(timeout)
	unsubCmd = f'X:{device}:{arg}'
	sendCmd(sock, unsubCmd)

	print(f'{prefix}Received {len(updates)} updates')
	for u in updates[:5]:
		print(f'{prefix}  {u}')
	if len(updates) > 5:
		print(f'{prefix}  ... ({len(updates) - 5} more)')

	return len(updates) > 0

def runAutomatedTest():
	"""Run a full automated test sequence for the F/A-18C."""
	print('DCSAutoMate Direct Connection Test')
	print('==================================')
	print(f'Connecting to {host}:{port}...')

	sock = connect()
	if not sock:
		return False

	print('Connected!')
	results = []

	# Test 1: Module identification.
	results.append(('Identification', testIdentification(sock)))

	# Test 2: State queries.
	print('\n--- State Queries (F/A-18C) ---')
	# Canopy position: device 7, arg 38 (may vary — this tests the mechanism).
	testQuery(sock, 7, 38, 'Canopy position')
	# Battery switch: device 3, arg 404.
	testQuery(sock, 3, 404, 'Battery switch')
	results.append(('State queries', True))

	# Test 3: Engine info.
	results.append(('Engine info', testEngineInfo(sock)))

	# Test 4: Subscription.
	print('\n--- Subscription Test ---')
	results.append(('Subscription', testSubscription(sock, 3, 404, 0.1, 1.0, 'Battery switch')))

	# Test 5: Command sending (battery switch — toggling is safe).
	print('\n--- Command Test (Battery Switch) ---')
	print('  NOTE: This will move the battery switch in the cockpit!')
	# Read current value.
	currentVal = testQuery(sock, 3, 404, 'Current battery position')
	# Send a step command.
	results.append(('Command send', testCommand(sock, 3, 3001, 1, 'Step battery switch up')))
	time.sleep(0.3)
	# Read new value.
	newVal = testQuery(sock, 3, 404, 'New battery position')
	if currentVal != newVal:
		print('  Battery switch moved successfully!')
	else:
		print('  Battery switch position unchanged (may already be at limit)')
	# Step it back.
	testCommand(sock, 3, 3001, -1, 'Step battery switch back')

	# Summary.
	print('\n--- Results ---')
	allPassed = True
	for name, passed in results:
		status = 'PASS' if passed else 'FAIL'
		print(f'  {status}: {name}')
		if not passed:
			allPassed = False

	sock.close()
	return allPassed

def runInteractive():
	"""Run interactive mode — type commands manually."""
	print('DCSAutoMate Direct Connection — Interactive Mode')
	print(f'Connecting to {host}:{port}...')

	sock = connect()
	if not sock:
		return

	print('Connected! Type commands (e.g., I, Q:3:404, C:3:3001:1). Type "quit" to exit.')
	print()

	while True:
		try:
			cmd = input('> ').strip()
		except (EOFError, KeyboardInterrupt):
			break

		if cmd.lower() in ('quit', 'exit', 'q'):
			break

		if not cmd:
			continue

		response = sendCmd(sock, cmd)
		print(f'  {response}')

	sock.close()
	print('Disconnected.')

def runSingleCommand(cmd):
	"""Send a single command and print the response."""
	sock = connect()
	if not sock:
		return

	response = sendCmd(sock, cmd)
	print(response)
	sock.close()

if __name__ == '__main__':
	if '--test' in sys.argv:
		success = runAutomatedTest()
		sys.exit(0 if success else 1)
	elif '--cmd' in sys.argv:
		idx = sys.argv.index('--cmd')
		if idx + 1 < len(sys.argv):
			runSingleCommand(sys.argv[idx + 1])
		else:
			print('Usage: testDCSConnection.py --cmd "C:3:3001:1"')
	else:
		runInteractive()
