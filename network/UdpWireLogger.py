import datetime
import threading


class UdpWireLogger:
	def __init__(self, config=None):
		self.config = config if isinstance(config, dict) else {}
		self._lock = threading.Lock()
		self.logFilePath = 'DCSAutoMateLog.txt'

	def logUiTx(self, addr, data):
		self._log(
			category = 'UI',
			direction = 'TX',
			addr = addr,
			data = data,
			enabledKey = 'udpUiWireLogEnabled',
			filterKey = 'udpUiWireLogFilter',
			maxCharsKey = 'udpUiWireLogMaxChars',
		)

	def logUiRx(self, addr, data):
		self._log(
			category = 'UI',
			direction = 'RX',
			addr = addr,
			data = data,
			enabledKey = 'udpUiWireLogEnabled',
			filterKey = 'udpUiWireLogFilter',
			maxCharsKey = 'udpUiWireLogMaxChars',
		)

	def logBiosRx(self, addr, data):
		self._log(
			category = 'BIOS',
			direction = 'RX',
			addr = addr,
			data = data,
			enabledKey = 'udpBiosWireLogEnabled',
			filterKey = None,
			maxCharsKey = 'udpBiosWireLogMaxChars',
		)

	def _log(self, category, direction, addr, data, enabledKey, filterKey, maxCharsKey):
		try:
			if not bool(self.config.get(enabledKey, False)):
				return

			text = ''
			byteCount = None
			if isinstance(data, (bytes, bytearray)):
				byteCount = len(data)
				text = data.decode('utf-8', errors='replace')
			else:
				text = str(data)

			if filterKey:
				udpWireLogFilter = str(self.config.get(filterKey, 'ui') or '').lower()
				if udpWireLogFilter != 'all':
					if not (text.startswith('DCSAUTOMATE_UI;') or text.startswith('DCSAUTOMATE_COORD_CONVERT;')):
						return

			text = text.replace('\r', '\\r').replace('\n', '\\n')

			udpWireLogMaxChars = int(self.config.get(maxCharsKey, 0) or 0)
			if udpWireLogMaxChars and len(text) > udpWireLogMaxChars:
				text = text[:udpWireLogMaxChars] + '...(truncated)'

			addrText = ''
			if isinstance(addr, tuple) and len(addr) >= 2:
				addrText = f' {addr[0]}:{addr[1]}'

			sizeText = ''
			if byteCount is not None:
				sizeText = f' bytes={byteCount}'

			timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
			line = f'{timestamp} - [UDP {category} {direction}]{addrText}{sizeText} {text}\n'
			with self._lock:
				with open(self.logFilePath, 'a', encoding = 'utf-8') as logFile:
					logFile.write(line)
		except Exception:
			pass
