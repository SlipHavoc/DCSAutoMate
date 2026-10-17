import socket
import struct
import threading
import time


class BaseMulticastReceiver:
	"""
	Base class for UDP multicast receivers with shared socket setup and thread lifecycle management.

	Subclasses must implement:
		_processData(self, data, addr): Process received data packet
		_onBlockingError(self): Called when no data is available (optional, default sets outputString)
		_onError(self, e): Called on receive error (optional, default shows error dialog)

	Attributes:
		config: Configuration dictionary
		lock: Threading lock for synchronized access to shared data
		outputString: Status string for display
		stopEvent: Threading Event for clean shutdown signaling
		thread: The receiver thread
		outputSocket: The UDP multicast socket
	"""

	def __init__(self, config, portConfigKey, defaultPort, multicastGroup, bufferSize=2048, loopDelay=0.02):
		"""
		Initialize the multicast receiver.

		Args:
			config: Configuration dictionary
			portConfigKey: Key to look up port number in config
			defaultPort: Default port if not in config
			multicastGroup: Multicast IP address to join
			bufferSize: UDP receive buffer size (default 2048)
			loopDelay: Delay between receive attempts in seconds (default 0.02 = 50Hz)
		"""
		self.config = config
		self.portConfigKey = portConfigKey
		self.defaultPort = defaultPort
		self.multicastGroup = multicastGroup
		self.bufferSize = bufferSize
		self.loopDelay = loopDelay

		self.lock = threading.Lock()
		self.stopEvent = threading.Event()
		self.thread = None
		self.outputString = ''
		self.blockingErrorThreshold = 10  # Number of consecutive blocking errors before "not receiving"

		self.outputSocket = self._createSocket()

	def _createSocket(self):
		"""Create and configure the UDP multicast socket."""
		udpIp = '0.0.0.0'
		udpPort = self.config.get(self.portConfigKey, self.defaultPort)

		sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
		sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
		sock.bind((udpIp, udpPort))

		group = socket.inet_aton(self.multicastGroup)
		mreq = struct.pack('4sL', group, socket.INADDR_ANY)
		sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)

		# Non-blocking so we can check stopEvent periodically
		sock.setblocking(False)

		return sock

	def _runLoop(self):
		"""Main receive loop. Runs in a separate thread."""
		blockingErrors = 0

		while not self.stopEvent.is_set():
			try:
				data, addr = self.outputSocket.recvfrom(self.bufferSize)
				self._processData(data, addr)
				blockingErrors = 0  # Reset on successful receive

			except BlockingIOError:
				# No data available right now
				blockingErrors += 1
				if blockingErrors > self.blockingErrorThreshold:
					self._onBlockingError()

			except OSError as e:
				# Socket was closed (expected during shutdown)
				if self.stopEvent.is_set():
					break
				# Unexpected OS error
				self._onError(e)
				break

			except Exception as e:
				self._onError(e)
				break

			# Use Event.wait() instead of time.sleep() for immediate wake on stop.
			# This returns True if the event is set (stop requested), False on timeout.
			if self.stopEvent.wait(timeout=self.loopDelay):
				break

	def _processData(self, data, addr):
		"""
		Process a received data packet. Subclasses must implement this.

		Args:
			data: Raw bytes received
			addr: Sender address tuple (ip, port)
		"""
		raise NotImplementedError('Subclasses must implement _processData()')

	def _onBlockingError(self):
		"""Called when not receiving data. Subclasses can override."""
		pass

	def _onError(self, e):
		"""Called on receive error. Subclasses can override to show error dialog."""
		pass

	def start(self):
		"""Start the receiver thread."""
		if self.thread and self.thread.is_alive():
			return  # Already running

		self.stopEvent.clear()
		self.thread = threading.Thread(target=self._runLoop)
		self.thread.daemon = True
		self.thread.start()

	def stop(self):
		"""Stop the receiver thread cleanly."""
		# Signal the thread to stop
		self.stopEvent.set()

		# Close the socket to unblock any pending recvfrom
		try:
			self.outputSocket.shutdown(socket.SHUT_RDWR)
		except Exception:
			pass
		try:
			self.outputSocket.close()
		except Exception:
			pass

		# Wait for thread to finish with reasonable timeout
		if self.thread:
			self.thread.join(timeout=1.0)
			if self.thread.is_alive():
				# Thread didn't stop in time, but we've done what we can.
				# The daemon flag ensures it won't block program exit.
				pass
