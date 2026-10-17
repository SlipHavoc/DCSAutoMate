import threading

from engine.autoSelectRules import isEngineRunning
from network.BaseMulticastReceiver import BaseMulticastReceiver


class DCSAutoMateExportManager(BaseMulticastReceiver):
	"""
	Manages the export of data from DCS (Digital Combat Simulator) and processes it for display or further use.

	Attributes:
		config: Configuration settings for the manager.
		lock: A threading lock to ensure thread-safe operations.
		dataStorage: A dictionary to store key/value pairs of data exported from DCS.
		outputSocket: The UDP socket used to receive data from DCS.
		messages: A dictionary containing messages for different states (e.g., no data, error).
		outputString: A string to store the formatted output data.

	Methods:
		parseData(data): Parses the received data and returns it as a dictionary.
		parseValue(value): Parses individual values from the data.
		formatTimeHHMMSS(seconds): Formats time in seconds to HH:MM:SS format.
		buildOutputString(): Builds a formatted string from the stored data.
		start(): Starts the continuous data update thread.
		stop(): Stops the continuous data update thread.
	"""

	def __init__(self, config):
		self.dataStorage = {}  # Dict to store key/value pairs of data exported from DCS.
		self.messages = {
			'noData': 'No data to show.',
			'error': 'Error',
		}

		# Initialize parent with multicast settings
		super().__init__(
			config=config,
			portConfigKey='dcsAutoMateUdpPort',
			defaultPort=6121,
			multicastGroup='239.255.61.21',
			bufferSize=16384,  # Needs to be large enough for largest UDP packet from DCSAutoMateExport.lua
			loopDelay=0.1,  # We get data every second, so 100ms polling is plenty
		)

	def parseData(self, data):
		decodedData = data.decode('utf-8')
		dcsData = {}
		for item in decodedData.split(';'):
			if '=' in item:
				key, value = item.split('=', 1)
				keys = key.split('.')
				tempDict = dcsData
				for k in keys[:-1]:
					tempDict = tempDict.setdefault(k, {})
				tempDict[keys[-1]] = self.parseValue(value)
		return dcsData

	def parseValue(self, value):
		try:
			return float(value) if '.' in value else int(value)
		except ValueError:
			if value.lower() == 'true':
				return True
			elif value.lower() == 'false':
				return False
			return value

	def formatTimeHHMMSS(self, seconds):
		h = seconds // 3600
		m = (seconds % 3600) // 60
		s = seconds % 60
		return f'{int(h):02}:{int(m):02}:{int(s):02}'

	def _processData(self, data, addr):
		"""Process received DCS data packet (called by base class)."""
		parsedData = self.parseData(data)
		with self.lock:
			self.dataStorage = parsedData
		self.outputString = self.buildOutputString()

	def _onBlockingError(self):
		"""Called when not receiving data."""
		self.outputString = self.messages['noData']

	def _onError(self, e):
		"""Called on receive error."""
		from PySide6 import QtWidgets
		self.outputString = self.messages['error']
		msg = QtWidgets.QMessageBox()
		msg.setIcon(QtWidgets.QMessageBox.Critical)
		msg.setWindowTitle('Error')
		msg.setText(f'Error while receiving DCSAutoMateExport data: {e}\nPlease restart DCSAutoMate.')
		msg.exec()

	def buildOutputString(self):
		#print('inBuildOutputString', self.dataStorage)
		outputString = ''
		try:
			altMSL = self.dataStorage['LoGetAltitudeAboveSeaLevel']
			altAGL = self.dataStorage['LoGetAltitudeAboveGroundLevel']
			altRadar = self.dataStorage['LoGetRadarAltimeter']
			altObj = self.dataStorage['LoGetHeightWithObjects']
			airspeedTAS = self.dataStorage['LoGetTrueAirSpeed']
			airspeedIAS = self.dataStorage['LoGetIndicatedAirSpeed']

			missionStartTime = self.dataStorage['LoGetMissionStartTime']
			missionElapsedTime = self.dataStorage['LoGetModelTime']
			missionTimeSeconds = missionStartTime + missionElapsedTime
			missionTimeString = self.formatTimeHHMMSS(missionTimeSeconds)

			moduleName = self.dataStorage['LoGetSelfData']['Name']

			outputString += f"Aircraft: {moduleName}\n"

			outputString += f"Mission time: {missionTimeString}\n"
			if missionTimeString >= '06:00:00' and missionTimeString <= '20:00:00':
				outputString += "It's between 0600 and 2000, probably daytime.\n"
			else:
				outputString += "It's between 2000 and 0600, probably nighttime.\n"

			if altAGL < 5:
				outputString += "You're probably on the ground.\n"
			elif altAGL - altMSL < 2 and altMSL > 15 and altMSL < 25 and airspeedTAS < 40:
				outputString += "You're probably on the carrier deck.\n"
			else:
				outputString += "You're probably in the air.\n"

			if isEngineRunning(self.dataStorage.get('LoGetEngineInfo')):
				outputString += "Engine is running.\n"
			else:
				outputString += "Engine is off.\n"

			if moduleName == 'AH-64D_BLK_II':
				longbowEquipped = False
				for stationId, stationData in self.dataStorage['LoGetPayloadInfo']['Stations'].items():
					if stationData['CLSID'] == '{AN_APG_78}' and stationData['count'] > 0:
						longbowEquipped = True
						break
				if longbowEquipped:
					outputString += "Longbow radar equipped.\n"
				else:
					outputString += "Longbow radar not equipped.\n"

		except Exception as e:
			# If we have any exceptions, it's prabably a key error, meaning we don't have these data fields yet, so show "no data".
			outputString = self.messages['noData']

		# Trim the last newline character if it exists
		outputString = outputString.rstrip('\n')
		return outputString
