"""One-shot probe: cycle IFF CODE selector (arg199) forward and back to find all positions."""
import socket, time, sys
sys.path.insert(0, '.')
sys.path.insert(0, 'tools/validation-scripts')
from validateControlMapping import queryArg, performClickableAction

HOST, PORT = '127.0.0.1', 7780
DEVICE = 22
CMD = 3007
ARG = 199
SETTLE = 0.6

sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.connect((HOST, PORT))
sock.settimeout(5.0)

print(f'Initial arg {ARG}: {queryArg(sock, ARG):.6f}')
print()
print(f'{"send_val":>10}  {"before":>10}  {"after":>10}  {"delta":>10}')
print('-' * 48)

def probe(label, val):
	time.sleep(SETTLE)
	before = queryArg(sock, ARG)
	performClickableAction(sock, DEVICE, CMD, val)
	time.sleep(SETTLE)
	after = queryArg(sock, ARG)
	print(f'{label:>10}  {before:>10.6f}  {after:>10.6f}  {after-before:>+10.6f}')

# Cycle forward (left-click = +1) five times
for i in range(5):
	probe(f'+1 (#{i+1})', 1)

print()
# Cycle back (right-click = -1) five times
for i in range(5):
	probe(f'-1 (#{i+1})', -1)

sock.close()
print('\nDone.')
