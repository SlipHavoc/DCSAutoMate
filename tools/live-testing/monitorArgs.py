"""Monitor cockpit argument values in real-time.

Connects directly to the DCSAutoMateExport.lua TCP server and polls
specified args, printing their values whenever they change.

Usage:
	python tools/monitorArgs.py [arg1] [arg2] ...

Example:
	python tools/monitorArgs.py 619 620
"""

import socket
import sys
import time

HOST = '127.0.0.1'
PORT = 7780
POLL_INTERVAL = 0.05  # 50ms = 20 Hz


def queryArg(sock, arg):
	"""Send a Q: query and return the value."""
	msg = f'Q:0:{arg}\n'
	sock.sendall(msg.encode())
	# Read response.
	data = b''
	while b'\n' not in data:
		chunk = sock.recv(1024)
		if not chunk:
			raise ConnectionError('Connection lost')
		data += chunk
	# Take only the first complete line (ignore trailing data from other responses).
	line = data.decode().split('\n')[0].strip()
	# Response format: R:device:arg:value
	if line.startswith('R:'):
		parts = line.split(':')
		if len(parts) >= 4:
			try:
				return float(parts[3])
			except ValueError:
				return None
	return None


def main():
	args = [int(a) for a in sys.argv[1:]] if len(sys.argv) > 1 else [619, 620]

	print(f'Connecting to DCS at {HOST}:{PORT}...')
	sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	sock.connect((HOST, PORT))
	sock.settimeout(2.0)
	print(f'Connected. Monitoring args: {args}')
	print(f'Press Ctrl+C to stop.\n')

	# Print header.
	header = 'Time     | ' + ' | '.join(f'arg {a:>5}' for a in args)
	print(header)
	print('-' * len(header))

	lastValues = {}
	startTime = time.time()

	try:
		while True:
			values = {}
			for arg in args:
				try:
					values[arg] = queryArg(sock, arg)
				except socket.timeout:
					values[arg] = None

			# Only print when something changed.
			changed = any(values.get(a) != lastValues.get(a) for a in args)
			if changed:
				elapsed = time.time() - startTime
				parts = []
				for a in args:
					v = values.get(a)
					if v is not None:
						parts.append(f'{v:>10.4f}')
					else:
						parts.append(f'{"N/A":>10}')
				print(f'{elapsed:7.2f}s | ' + ' | '.join(parts))
				lastValues = values.copy()

			time.sleep(POLL_INTERVAL)
	except KeyboardInterrupt:
		print('\nStopped.')
	finally:
		sock.close()


if __name__ == '__main__':
	main()
