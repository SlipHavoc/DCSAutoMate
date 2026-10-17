#!/usr/bin/env python3
"""Test the three PDP circuit-breaker sequences:
  1. CB in:          send 0.6, release (0.0)  → expect readback 0.6
  2. CB out:         send 0.9, release (0.0) quickly  → expect readback 1.0 (no collar)
  3. CB out+collar:  send 0.9, wait > collar threshold, release (0.0)  → expect readback 0.8

Usage:
    python tools/live-testing/testPdpCB.py
    python tools/live-testing/testPdpCB.py PDP1.2B14 --module CH-47Fbl1 --collar-wait 5.5
"""

import argparse, json, socket, sys, time
sys.path.insert(0, '.')
sys.path.insert(0, 'tools/validation-scripts')
from validateControlMapping import queryArg, performClickableAction

HOST, PORT = '127.0.0.1', 7780
SETTLE = 0.5  # seconds between send and readback


def checkStep(label, got, expected):
	ok = abs(got - expected) < 0.01
	status = 'PASS' if ok else 'FAIL'
	print(f'  {status}  {label}: expected {expected:.3f}, got {got:.6f}')
	return ok


def testCB(sock, deviceId, commandId, argNum, collarWait):
	allPass = True

	# --- Step 1: CB in (send 0.6, quick release) ---
	print('\nStep 1: CB in  (send 0.6, release 0.0)')
	performClickableAction(sock, deviceId, commandId, 0.6)
	time.sleep(SETTLE)
	v1 = queryArg(sock, argNum)
	print(f'  After send 0.6: {v1:.6f}')
	performClickableAction(sock, deviceId, commandId, 0.0)
	time.sleep(SETTLE)
	v1r = queryArg(sock, argNum)
	print(f'  After release:  {v1r:.6f}')
	allPass &= checkStep('CB in readback', v1r, 0.6)

	# --- Step 2: CB out, no collar (send 0.9, quick release) ---
	print('\nStep 2: CB out, no collar  (send 0.9, release 0.0 quickly)')
	performClickableAction(sock, deviceId, commandId, 0.9)
	time.sleep(SETTLE)
	v2 = queryArg(sock, argNum)
	print(f'  After send 0.9: {v2:.6f}')
	performClickableAction(sock, deviceId, commandId, 0.0)
	time.sleep(SETTLE)
	v2r = queryArg(sock, argNum)
	print(f'  After release:  {v2r:.6f}')
	allPass &= checkStep('CB out readback (no collar)', v2r, 1.0)

	# Push in again to reset for step 3.
	performClickableAction(sock, deviceId, commandId, 0.6)
	time.sleep(SETTLE)
	performClickableAction(sock, deviceId, commandId, 0.0)
	time.sleep(SETTLE)

	# --- Step 3: CB out + collar (send 0.9, wait > threshold, then release) ---
	print(f'\nStep 3: CB out + collar  (send 0.9, wait {collarWait}s, release 0.0)')
	performClickableAction(sock, deviceId, commandId, 0.9)
	time.sleep(SETTLE)
	v3 = queryArg(sock, argNum)
	print(f'  After send 0.9: {v3:.6f}')
	print(f'  Waiting {collarWait}s for collar timer...')
	time.sleep(collarWait)
	v3w = queryArg(sock, argNum)
	print(f'  After wait:     {v3w:.6f}')
	performClickableAction(sock, deviceId, commandId, 0.0)
	time.sleep(SETTLE)
	v3r = queryArg(sock, argNum)
	print(f'  After release:  {v3r:.6f}')
	allPass &= checkStep('CB out+collar readback', v3r, 0.8)

	return allPass


def main():
	parser = argparse.ArgumentParser(description='Test PDP circuit-breaker CB in / CB out / CB out+collar sequences.')
	parser.add_argument('name', nargs='?', default='PDP2.2A08', help='Control name (default: PDP2.2A08)')
	parser.add_argument('--module', default='CH-47Fbl1', help='Module name (default: CH-47Fbl1)')
	parser.add_argument('--collar-wait', type=float, default=5.5, help='Seconds to hold 0.9 before releasing in collar test (default: 5.5)')
	args = parser.parse_args()

	mapFile = f'config/controlMappings/{args.module}.json'
	with open(mapFile, encoding='utf-8') as f:
		mapping = json.load(f)
	ctrl = mapping['controls'].get(args.name)
	if ctrl is None:
		print(f'ERROR: "{args.name}" not found in {mapFile}', file=sys.stderr)
		sys.exit(1)

	deviceId = ctrl['deviceId']
	commandId = ctrl['commandId']
	argNum = ctrl['arg']

	print(f'Control:  {args.name}')
	print(f'Device:   {deviceId}  Command: {commandId}  Arg: {argNum}')

	sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	sock.connect((HOST, PORT))
	sock.settimeout(10.0)

	initial = queryArg(sock, argNum)
	print(f'Initial:  {initial:.6f}')

	allPass = testCB(sock, deviceId, commandId, argNum, args.collar_wait)

	# Restore to initial state.
	print(f'\nRestoring to initial ({initial:.6f})...')
	performClickableAction(sock, deviceId, commandId, initial if initial < 0.5 else 0.9)
	time.sleep(SETTLE)
	performClickableAction(sock, deviceId, commandId, 0.0)
	time.sleep(SETTLE)
	final = queryArg(sock, argNum)
	print(f'After restore: {final:.6f}')

	sock.close()
	print(f'\n{"ALL PASS" if allPass else "SOME FAILURES"}')
	sys.exit(0 if allPass else 1)


if __name__ == '__main__':
	main()
