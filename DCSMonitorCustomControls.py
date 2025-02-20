import random

class DCSMonitorCustomControls:
	def __init__(self):
		self.messages = {
			'noData': 'No data available.',
		}

	def formatTimeHHMMSS(self, seconds):
		hours = seconds // 3600
		seconds %= 3600
		minutes = seconds // 60
		seconds %= 60
		return f"{hours:02}:{minutes:02}:{seconds:02}"

	def getMissionSecs(self, data):
		try:
			missionStartTime = data['LoGetMissionStartTime']
			missionElapsedTime = data['LoGetModelTime']
			missionTimeSecs = round(missionStartTime + missionElapsedTime)
			outputValue = missionTimeSecs
		except Exception as e:
			# If we have any exceptions, it's prabably a key error, meaning we don't have these data fields yet.
			outputValue = 0

		return outputValue

	def getFuelFlowFracPerSec(self, data):
		try:
			# Get the number of seconds since last update, and the number of seconds elapsed between then and now.  Get the fuel remaining frac at the last update, and the fuel remaining frac now.  Fuel flow frac per sec = (fuel at last update - fuel remaining now) / seconds elapsed.

			# Initialize prevMissionSecs if it doesn't exist.
			if not hasattr(self, 'prevMissionSecs'):
				self.prevMissionSecs = 0

			# Initialize prevFuelRemainingFrac if it doesn't exist.
			if not hasattr(self, 'prevFuelRemainingFrac'):
				self.prevFuelRemainingFrac = 0

			# Initialize fuelFlowFracPerSec if it doesn't exist.
			if not hasattr(self, 'fuelFlowFracPerSec'):
				self.fuelFlowFracPerSec = 0

			missionSecs = self.getMissionSecs(data)
			fuelRemainingFrac = data['LoGetEngineInfo']['fuel_internal'] + data['LoGetEngineInfo']['fuel_external']

			if self.prevMissionSecs and self.prevFuelRemainingFrac and missionSecs and missionSecs != self.prevMissionSecs:
				#print('\nin getFuelFlowFracPerSec')
				#print('self.prevMissionSecs', self.prevMissionSecs)
				#print('self.prevFuelRemainingFrac', self.prevFuelRemainingFrac)
				#print('missionSecs', missionSecs)
				#print('fuelRemainingFrac', fuelRemainingFrac)

				#fuelFlowFracPerSec = (self.prevFuelRemainingFrac - fuelRemainingFrac) / (missionSecs - self.prevMissionSecs)
				fuelFractionBurned = self.prevFuelRemainingFrac - fuelRemainingFrac
				#print('fuelFractionBurned', fuelFractionBurned)
				secsElapsed = missionSecs - self.prevMissionSecs
				#print('secsElapsed', secsElapsed)
				fuelFlowFracPerSec = fuelFractionBurned / secsElapsed
				#print('fuelFlowFracPerSec', fuelFlowFracPerSec)
				outputValue = fuelFlowFracPerSec
			else:
				outputValue = self.fuelFlowFracPerSec

			if missionSecs and missionSecs != self.prevMissionSecs:
				# Update prevMissionSecs and prevFuelRemainingFrac for the next tick.
				self.prevMissionSecs = missionSecs
				self.prevFuelRemainingFrac = fuelRemainingFrac
				self.fuelFlowFracPerSec = fuelFlowFracPerSec

			return outputValue
		except Exception as e:
			return 0

	###########################################################################
	###########################################################################
	###########################################################################
	###########################################################################
	###########################################################################

	def getCustomControls(self):
		# Return a dictionary of custom controls.  These will be sorted alphabetically by key in the Controls list.
		return {
			'CustomControls/Test': self.getTest,
			'CustomControls/FuelEfficiencyNmiPer1000Lbs': self.getFuelEfficiencyNmiPer1000Lbs,
			'CustomControls/FuelEfficiencyKmPer1000Kg': self.getFuelEfficiencyKmPer1000Kg,
			'CustomControls/FuelEfficiencyNmiPer1Pct': self.getFuelEfficiencyNmiPer1Pct,
			'CustomControls/FuelEfficiencyKmPer1Pct': self.getFuelEfficiencyKmPer1Pct,
			'CustomControls/FuelFlowLbsPerHour': self.getFuelFlowLbsPerHour,
			'CustomControls/FuelFlowKgPerHour': self.getFuelFlowKgPerHour,
			'CustomControls/FuelFlowPctPerHour': self.getFuelFlowPctPerHour,
			'CustomControls/FuelTimeRemaining': self.getFuelTimeRemaining,
			'CustomControls/FuelPctRemaining': self.getFuelPctRemaining,
			'CustomControls/MissionTime': self.getMissionTime,
			'CustomControls/M2000C_PcnDisplayDigits': self.getM2000C_PcnDisplayDigits,
		}

	def getTest(self, data):
		#return ('CustomControls/Test', 'Test description', 'Test value')
		randNum = random.randint(0, 100)
		return ('CustomControls/Test', 'Test description', 'Test value ' + str(randNum))

	def getFuelFlowLbsPerHour(self, data):
		try:
			fuelFlow = data['LoGetEngineInfo']['FuelConsumption']['left'] + data['LoGetEngineInfo']['FuelConsumption']['right'] # kg/sec
			fuelFlowLbsPerHour = fuelFlow * 2.20462 * 3600
			outputValue = round(fuelFlowLbsPerHour, 2)
		except Exception as e:
			# If we have any exceptions, it's prabably a key error, meaning we don't have these data fields yet.
			outputValue = e

		return ('CustomControls/FuelFlowLbsPerHour', 'Fuel flow lbs/hr', outputValue)

	def getFuelFlowKgPerHour(self, data):
		try:
			fuelFlow = data['LoGetEngineInfo']['FuelConsumption']['left'] + data['LoGetEngineInfo']['FuelConsumption']['right'] # kg/sec
			fuelFlowKgPerHour = fuelFlow * 3600
			outputValue = round(fuelFlowKgPerHour, 2)
		except Exception as e:
			# If we have any exceptions, it's prabably a key error, meaning we don't have these data fields yet.
			outputValue = e

		return ('CustomControls/FuelFlowKgPerHour', 'Fuel flow kg/hr', outputValue)

	def getFuelFlowPctPerHour(self, data):
		try:
			fuelFlowFracPerSec = self.getFuelFlowFracPerSec(data)
			fuelFlowFracPerHour = fuelFlowFracPerSec * 3600
			outputValue = round(fuelFlowFracPerHour * 100, 2)
		except Exception as e:
			# If we have any exceptions, it's prabably a key error, meaning we don't have these data fields yet.
			outputValue = e

		return ('CustomControls/FuelFlowPctPerHour', 'Fuel flow %/hr', outputValue)

	def getFuelEfficiencyNmiPer1000Lbs(self, data):
		outputValue = self.messages['noData']
		try:
			airspeedTAS = data['LoGetTrueAirSpeed'] # m/s

			# Calculate fuel efficiency in nautical miles per 1000 pounds of fuel.
			fuelFlow = data['LoGetEngineInfo']['FuelConsumption']['left'] + data['LoGetEngineInfo']['FuelConsumption']['right'] # kg/sec
			fuelFlowLbsPerHour = fuelFlow * 2.20462 * 3600
			airspeedTASKts = airspeedTAS * 1.94384
			if fuelFlowLbsPerHour == 0:
				fuelEfficiency = 'divByZero'
			else:
				fuelEfficiency = round(airspeedTASKts / (fuelFlowLbsPerHour / 1000), 2)
			outputValue = fuelEfficiency

		except Exception as e:
			# If we have any exceptions, it's prabably a key error, meaning we don't have these data fields yet.
			outputValue = e

		return ('CustomControls/FuelEfficiencyNmiPer1000Lbs', 'Fuel efficiency nmi/1000 lbs', outputValue)

	def getFuelEfficiencyKmPer1000Kg(self, data):
		try:
			airspeedTAS = data['LoGetTrueAirSpeed'] # m/s

			# Calculate fuel efficiency in km per 1000 kg of fuel.
			fuelFlow = data['LoGetEngineInfo']['FuelConsumption']['left'] + data['LoGetEngineInfo']['FuelConsumption']['right'] # kg/sec
			fuelFlowKgPerHour = fuelFlow * 3600
			if fuelFlowKgPerHour == 0:
				fuelEfficiency = 'divByZero'
			else:
				fuelEfficiency = round(airspeedTAS / (fuelFlowKgPerHour / 1000), 2)
			outputValue = fuelEfficiency
		except Exception as e:
			# If we have any exceptions, it's prabably a key error, meaning we don't have these data fields yet.
			outputValue = e

		return ('CustomControls/FuelEfficiencyKmPer1000Kg', 'Fuel efficiency km/1000 kg', outputValue)

	def getFuelEfficiencyNmiPer1Pct(self, data):
		try:
			airspeedTAS = data['LoGetTrueAirSpeed'] # m/s
			airspeedTASKts = airspeedTAS * 1.94384

			# Calculate fuel efficiency as a percentage of fuel flow.
			fuelFlowFracPerSec = self.getFuelFlowFracPerSec(data)
			fuelFlowFracPerHour = fuelFlowFracPerSec * 3600
			if fuelFlowFracPerHour == 0:
				fuelEfficiency = 'divByZero'
			else:
				fuelEfficiency = round(airspeedTASKts / (fuelFlowFracPerHour * 100), 2)
			outputValue = fuelEfficiency
		except Exception as e:
			# If we have any exceptions, it's prabably a key error, meaning we don't have these data fields yet.
			outputValue = e

		return ('CustomControls/FuelEfficiencyNmiPer1Pct', 'Fuel efficiency nmi/1%', outputValue)

	def getFuelEfficiencyKmPer1Pct(self, data):
		try:
			airspeedTAS = data['LoGetTrueAirSpeed'] # m/s
			airspeedTASKph = airspeedTAS * 3.6

			# Calculate fuel efficiency as a percentage of fuel flow.
			fuelFlowFracPerSec = self.getFuelFlowFracPerSec(data)
			fuelFlowFracPerHour = fuelFlowFracPerSec * 3600
			if fuelFlowFracPerHour == 0:
				fuelEfficiency = 'divByZero'
			else:
				fuelEfficiency = round(airspeedTASKph / (fuelFlowFracPerHour * 100), 2)
			outputValue = fuelEfficiency
		except Exception as e:
			# If we have any exceptions, it's prabably a key error, meaning we don't have these data fields yet.
			outputValue = e

		return ('CustomControls/FuelEfficiencyKmPer1Pct', 'Fuel efficiency km/1%', outputValue)

	def getFuelTimeRemaining(self, data):
		try:
			fuelRemainingFrac = data['LoGetEngineInfo']['fuel_internal'] + data['LoGetEngineInfo']['fuel_external'] # Fractional (0.0 to 1.0)
			fuelFlowFracPerSec = self.getFuelFlowFracPerSec(data)
			secsRemaining = round(fuelRemainingFrac / fuelFlowFracPerSec)
			outputValue = self.formatTimeHHMMSS(secsRemaining)
		except Exception as e:
			# If we have any exceptions, it's prabably a key error, meaning we don't have these data fields yet.
			outputValue = e

		return ('CustomControls/FuelTimeRemaining', 'Fuel time remaining HH:MM:SS', outputValue)

	def getFuelPctRemaining(self, data):
		try:
			fuelRemainingFrac = data['LoGetEngineInfo']['fuel_internal'] + data['LoGetEngineInfo']['fuel_external'] # Fractional (0.0 to 1.0)
			outputValue = round(fuelRemainingFrac * 100, 2)
		except Exception as e:
			# If we have any exceptions, it's prabably a key error, meaning we don't have these data fields yet.
			outputValue = e

		return ('CustomControls/FuelPctRemaining', 'Fuel pct remaining', outputValue)

	def getMissionTime(self, data):
		try:
			missionStartTime = data['LoGetMissionStartTime']
			missionElapsedTime = data['LoGetModelTime']
			missionTimeSeconds = round(missionStartTime + missionElapsedTime)
			missionTimeString = self.formatTimeHHMMSS(missionTimeSeconds)
			outputValue = missionTimeString
		except Exception as e:
			# If we have any exceptions, it's prabably a key error, meaning we don't have these data fields yet.
			outputValue = e

		return ('CustomControls/MissionTime', 'Mission time HH:MM:SS', outputValue)

	def getM2000C_PcnDisplayDigits(self, data, dcsBiosManager):
		'''
		Reads the PCN display segments (M-2000C/PCN_DISP_[L|R]_x_y) from 'data' and returns the digits shown.
		'''
		# Segments 0-6 are the 7 segments of the digit, and segment 7 is the decimal point.
		digitLookup = {
			' ': [0, 0, 0, 0, 0, 0, 0],
			'0': [2, 2, 2, 2, 2, 2, 0],
			'1': [0, 0, 0, 2, 2, 0, 0],
			'2': [2, 0, 2, 2, 0, 2, 2],
			'3': [0, 0, 2, 2, 2, 2, 2],
			'4': [0, 2, 0, 2, 2, 0, 2],
			'5': [0, 2, 2, 0, 2, 2, 2],
			'6': [2, 2, 2, 0, 2, 2, 2],
			'7': [0, 0, 2, 2, 2, 0, 0],
			'8': [2, 2, 2, 2, 2, 2, 2],
			'9': [0, 2, 2, 2, 2, 2, 2],
		}

		def findDigit(segments):
			decimalOn = (segments[7] == 2)
			digitSegments = segments[:7]
			for digit, pattern in digitLookup.items():
				if pattern == digitSegments:
					return ('.' + digit) if decimalOn else digit
			return '?'

		displayString = ''
		# There are 6 digits on the left and 7 on the right.
		for digitIndex in range(1, 6):
			try:
				segValues = []
				controlNames = [f'M-2000C/PCN_DISP_L_{digitIndex}_{segIndex}' for segIndex in range(8)]
				# getControlState returns a list of tuples, one for each control passed, so we need to extract the third element of each tuple.
				segValues = [seg[2] for seg in dcsBiosManager.getControlState(controlNames)]
				#print(f'digit {digitIndex}', segValues)
				# Now look up the matching digit for the segment values.
				displayString += findDigit(segValues)
			except KeyError:
				displayString += '?'

		displayString += '|'

		for digitIndex in range(1, 7):
			try:
				segValues = []
				controlNames = [f'M-2000C/PCN_DISP_R_{digitIndex}_{segIndex}' for segIndex in range(8)]
				# getControlState returns a list of tuples, one for each control passed, so we need to extract the third element of each tuple.
				segValues = [seg[2] for seg in dcsBiosManager.getControlState(controlNames)]
				#print(f'digit {digitIndex}', segValues)
				# Now look up the matching digit for the segment values.
				displayString += findDigit(segValues)
			except KeyError:
				displayString += '?'

		return ('CustomControls/M2000C_PcnDisplayDigits', 'M-2000C PCN display digits', displayString)
