#!/usr/bin/env python3
"""Diagnostic: send a series of values to a single DCS control and report arg movement.

Looks up the control in the module's control mapping JSON to get deviceId,
commandId, arg, argLim, sendProtocol, and incValue.  Prints before/after/delta
for each test value so you can see exactly how the cockpit arg responds.

Usage:
    python tools/live-testing/diagControl.py <control-name> [options]

Examples:
    python tools/live-testing/diagControl.py GEAR_INTERFACE.EmergParkHandleOnOff
    python tools/live-testing/diagControl.py HUD.HUD_SymbRejectSw_ITER --values "-1 -0.5 0 0.5 1"
    python tools/live-testing/diagControl.py INTERCOM.RWR_Volume_EXT --protocol S
    python tools/live-testing/diagControl.py --device 14 --command 3001 --arg 200 --values "0 0.5 1"
"""

import argparse, json, socket, sys, time
sys.path.insert(0, '.')
sys.path.insert(0, 'tools/validation-scripts')
from validateControlMapping import queryArg, performClickableAction, setCommand, sendCmd

HOST, PORT = '127.0.0.1', 7780
DEFAULT_SETTLE = 0.3
DEFAULT_VALUES = [-1.0, -0.5, -0.25, -0.1, -0.05, 0.0, 0.05, 0.1, 0.25, 0.5, 1.0]


def main():
	parser = argparse.ArgumentParser(description='Test a single DCS control with a series of values.')
	parser.add_argument('name', nargs='?', help='Control name (e.g. GEAR_INTERFACE.EmergParkHandleOnOff)')
	parser.add_argument('--module', default='FA-18C_hornet', help='Module name for mapping lookup (default: FA-18C_hornet)')
	parser.add_argument('--device', type=int, help='Override device ID')
	parser.add_argument('--command', type=int, help='Override command ID')
	parser.add_argument('--arg', type=int, help='Override arg number')
	parser.add_argument('--protocol', choices=['C', 'S'], help='Override send protocol (C=PerformClickableAction, S=SetCommand)')
	parser.add_argument('--values', help='Space-separated test values (default: spread of -1..1)')
	parser.add_argument('--settle', type=float, default=DEFAULT_SETTLE, help=f'Settle time in seconds (default: {DEFAULT_SETTLE})')
	args = parser.parse_args()

	deviceId = args.device
	commandId = args.command
	argNum = args.arg
	protocol = args.protocol

	if args.name:
		mapFile = f'config/controlMappings/{args.module}.json'
		with open(mapFile, encoding='utf-8') as f:
			mapping = json.load(f)
		ctrl = mapping['controls'].get(args.name)
		if ctrl is None:
			print(f'ERROR: "{args.name}" not found in {mapFile}', file=sys.stderr)
			sys.exit(1)
		deviceId = deviceId if deviceId is not None else ctrl.get('deviceId')
		commandId = commandId if commandId is not None else ctrl.get('commandId')
		argNum = argNum if argNum is not None else ctrl.get('arg')
		if protocol is None:
			protocol = ctrl.get('sendProtocol', 'C')
		print(f'Control:     {args.name}')
		print(f'Type:        {ctrl.get("type")}')
		print(f'sendProtocol:{ctrl.get("sendProtocol", "(default C)")}')
		print(f'argLim:      {ctrl.get("argLim")}')
		print(f'incValue:    {ctrl.get("incValue")}')
	else:
		if deviceId is None or commandId is None or argNum is None:
			parser.error('Supply a control name, or all of --device/--command/--arg.')
		if protocol is None:
			protocol = 'S'

	if deviceId is None or commandId is None or argNum is None:
		print(f'ERROR: incomplete control info — deviceId={deviceId} commandId={commandId} arg={argNum}', file=sys.stderr)
		sys.exit(1)

	print(f'Device: {deviceId}  Command: {commandId}  Arg: {argNum}  Protocol: {protocol}')

	testValues = [float(v) for v in args.values.split()] if args.values else DEFAULT_VALUES
	if protocol == 'C':
		sendFn = performClickableAction
	else:
		# For S: protocol, include argNum so the Lua handler also calls
		# set_argument_value (required for defineSetCommandTumb controls).
		sendFn = lambda sock, dev, cmd, val: sendCmd(sock, f'S:{dev}:{cmd}:{val}:{argNum}')

	sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	sock.connect((HOST, PORT))
	sock.settimeout(5.0)

	initial = queryArg(sock, argNum)
	print(f'\nInitial arg {argNum}: {initial:.6f}')
	print(f'\n{"value_sent":>12}  {"before":>10}  {"after":>10}  {"delta":>11}')
	print('-' * 50)

	for v in testValues:
		time.sleep(args.settle)
		before = queryArg(sock, argNum)
		sendFn(sock, deviceId, commandId, v)
		time.sleep(args.settle)
		after = queryArg(sock, argNum)
		print(f'{v:>12.4f}  {before:>10.6f}  {after:>10.6f}  {after - before:>+11.6f}')

	# Try to restore to the initial value.
	time.sleep(args.settle)
	final = queryArg(sock, argNum)
	if final != initial:
		print(f'\nRestoring to initial ({initial:.6f})...')
		sendFn(sock, deviceId, commandId, initial)
		time.sleep(args.settle)
		print(f'After restore: {queryArg(sock, argNum):.6f}')

	sock.close()
	print('\nDone.')


if __name__ == '__main__':
	main()
