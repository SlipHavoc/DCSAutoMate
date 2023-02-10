# Return a Dictionary of script titles and their corresponding function names.  This is a list of scripts that users will be selecting from.  The module may have other utility functions that will not be run directly by the users.
def getScriptFunctions():
	return {
		'Cold Start Ground (day)': 'ColdStartGroundDay',
		'Cold Start Ground (night)': 'ColdStartGroundNight',
		'Cold Start Carrier (day)': 'ColdStartCarrierDay',
		'Cold Start Carrier (night)': 'ColdStartCarrierNight',
		'Flashpoint Levant Waypoints': 'FlashpointLevantWaypoints',
	}

def getInfo():
	return """ATTENTION: You must remap "Throttle (Left) - IDLE" to LAlt+Home.  This is because pyWinAuto doesn't support RAlt or RCtrl."""

# Returns 0-65535 scaled by multiple (0-1), eg for 50% call int16(0.5)
def int16(mult = 1):
	int16 = 65535
	return int(mult * int16)

def ColdStartGroundDay(config):
	return ColdStart(groundStart = True, dayStart = True)

def ColdStartCarrierDay(config):
	return ColdStart(groundStart = False, dayStart = True)

def ColdStartGroundNight(config):
	return ColdStart(groundStart = True, dayStart = False)

def ColdStartCarrierNight(config):
	return ColdStart(groundStart = False, dayStart = False)

# Some settings change depending on whether you're starting from the ground or from a carrier.
def ColdStart(groundStart = True, dayStart = True):
	seq = []
	seqTime = 0
	dt = 0.3
	
	def pushSeqCmd(dt, cmd, arg, msg = ''):
		nonlocal seq, seqTime
		seqTime += dt
		seq.append({
			'time': round(seqTime, 2),
			'cmd': cmd,
			'arg': arg,
			'msg': msg,
		})
		
	def getLastSeqTime():
		nonlocal seq
		return float(seq[len(seq) - 1]['time'])

	canopyCloseTime = 9
	apuStartTime = 15
	engineCrankTime = 7 # Seconds until engine is at 15% after setting crank switch.
	engineStartTime = 35 # Seconds until engine is fully started after moving throttle to idle.
	insAlignTime = 1 * 60 + 55 # 1m55s
	
	pushSeqCmd(0, '', '', "Running Cold Start sequence")
	pushSeqCmd(dt, '', '', "WARNING - Uses non-standard key bindings.")
	
	pushSeqCmd(dt, 'BATTERY_SW', 2, 'BATT switch - On')
	
	if dayStart:
		pushSeqCmd(dt, 'CONSOLES_DIMMER', int16())
		pushSeqCmd(dt, 'INST_PNL_DIMMER', int16())
	else:
		pushSeqCmd(dt, 'CONSOLES_DIMMER', int16(0.5))
		pushSeqCmd(dt, 'INST_PNL_DIMMER', int16(0.5))
		pushSeqCmd(dt, 'COCKKPIT_LIGHT_MODE_SW', 1) # NOTE misspelling 0 = DAY (default), 1 = NITE, 2 = NVG
	
	apuTimerStart = getLastSeqTime()
	#pushSeqCmd(dt, '', '', "Starting APU ("+str(apuStartTime)+"s)")
	pushSeqCmd(dt, 'APU_CONTROL_SW', 1, 'APU switch - On')
	
	canopyTimerStart = getLastSeqTime()
	#pushSeqCmd(dt, '', '', "CANOPY - CLOSE")
	pushSeqCmd(dt, 'CANOPY_SW', 0)
	canopyTimerEnd = canopyCloseTime - (getLastSeqTime() - canopyTimerStart)
	pushSeqCmd(canopyTimerEnd, 'CANOPY_SW', 1, 'Canopy closed') # Turn off canopy switch 8 seconds later.
	
	apuTimerEnd = apuStartTime - (getLastSeqTime() - apuTimerStart)
	pushSeqCmd(apuTimerEnd, '', '', "APU started")

	#pushSeqCmd(dt, '', '', "LEFT DDI - ON")
	if dayStart:
		pushSeqCmd(dt, 'LEFT_DDI_BRT_SELECT', 2) # DAY
	else:
		pushSeqCmd(dt, 'LEFT_DDI_BRT_SELECT', 1) # NIGHT
	
	#pushSeqCmd(dt, '', '', "RIGHT DDI - ON")
	if dayStart:
		pushSeqCmd(dt, 'RIGHT_DDI_BRT_SELECT', 2) # DAY
	else:
		pushSeqCmd(dt, 'RIGHT_DDI_BRT_SELECT', 1) # NIGHT
	
	#pushSeqCmd(dt, '', '', "HUD - ON")
	if dayStart:
		pushSeqCmd(dt, 'HUD_SYM_BRT', int16())
	else:
		pushSeqCmd(dt, 'HUD_SYM_BRT', int16(0.5))
		pushSeqCmd(dt, 'HUD_SYM_BRT_SELECT', 0) # 0 = NIGHT, 1 = DAY

	#pushSeqCmd(dt, '', '', "AMPCD - ON")
	if dayStart:
		pushSeqCmd(dt, 'AMPCD_BRT_CTL', int16())
	else:
		pushSeqCmd(dt, 'AMPCD_BRT_CTL', int16(0.5))
	
	#pushSeqCmd(dt, '', '', "UFC BRIGHTNESS - MAX")
	if dayStart:
		pushSeqCmd(dt, 'UFC_BRT', int16())
	else:
		pushSeqCmd(dt, 'UFC_BRT', int16(0.5))

	# IFEI brightness
	if dayStart:
		pushSeqCmd(dt, 'IFEI', int16()) # IFEI brightness to max
	else:
		pushSeqCmd(dt, 'IFEI', 1000) # IFEI brightness to min

	pushSeqCmd(dt, 'UFC_COMM1_VOL', int16(0.8), 'COMM 1 vol - 80%')
	pushSeqCmd(dt, 'UFC_COMM2_VOL', int16(0.8), 'COMM 2 vol - 80%')
	
	# RIGHT ENGINE
	rightEngineCrankTimerStart = getLastSeqTime()
	#pushSeqCmd(dt, '', '', "RIGHT ENGINE - START (40s)")
	#pushSeqCmd(dt, '', '', "ENG CRANK SWITCH - R")
	pushSeqCmd(dt, 'ENGINE_CRANK_SW', 2) # Right
	rightEngineCrankTimerEnd = engineCrankTime - (getLastSeqTime() - rightEngineCrankTimerStart)
	pushSeqCmd(rightEngineCrankTimerEnd, '', '', "Right engine at 15%, right throttle to IDLE")
	pushSeqCmd(dt, 'scriptKeyboard', '{VK_RSHIFT down}{VK_HOME}{VK_RSHIFT up}')
	rightEngineStartTimerStart = getLastSeqTime()
	rightEngineStartTimerEnd = engineStartTime - (getLastSeqTime() - rightEngineStartTimerStart)
	pushSeqCmd(rightEngineStartTimerEnd, '', '', 'Right engine started')
	pushSeqCmd(dt, 'ENGINE_CRANK_SW', 1, 'Engine Crank switch - Off')
	# END RIGHT ENGINE
	
	#pushSeqCmd(dt, '', '', "HMD knob - ON")
	if dayStart:
		pushSeqCmd(dt, 'HMD_OFF_BRT', int16())
	else:
		pushSeqCmd(dt, 'HMD_OFF_BRT', int16(0.5))
	
	#pushSeqCmd(dt, '', '', "BLEED AIR KNOB - CYCLE THRU OFF TO NORM")
	pushSeqCmd(dt, 'BLEED_AIR_KNOB', 3)
	pushSeqCmd(dt, 'BLEED_AIR_KNOB', 0)
	pushSeqCmd(dt, 'BLEED_AIR_KNOB', 1)
	pushSeqCmd(dt, 'BLEED_AIR_KNOB', 2)

	maxRadAlt = int(int16() * 3 + 8194) # Just over 3 full turns of the knob from 0 to max.
	#pushSeqCmd(dt, '', '', "RADAR ALTIMETER - ON, SET TO 50 FT")
	pushSeqCmd(dt, 'RADALT_HEIGHT', '-'+str(maxRadAlt)) # All the way off
	pushSeqCmd(dt, 'RADALT_HEIGHT', '+'+str(int16(0.28))) # Turn knob up 28% of one turn to get 50 ft.

	#pushSeqCmd(dt, '', '', "RADAR KNOB - OPR")
	pushSeqCmd(dt, 'RADAR_SW', 2)
	#pushSeqCmd(dt, '', '', "FCS RESET BUTTON - PUSH")
	pushSeqCmd(dt, 'FCS_RESET_BTN', 1) # Press
	pushSeqCmd(dt, 'FCS_RESET_BTN', 0) # Release
	
	#pushSeqCmd(dt, '', '', "FLAP SWITCH - HALF")
	pushSeqCmd(dt, 'FLAP_SW', 1)
	#pushSeqCmd(dt, '', '', "T/O TRIM BUTTON - PRESS UNTIL TRIM ADVISORY DISPLAYED")
	pushSeqCmd(dt, 'TO_TRIM_BTN', 1)
	pushSeqCmd(dt, 'TO_TRIM_BTN', 0)
	
	#pushSeqCmd(dt, '', '', "STANDBY ATTITUDE REFERENCE INDICATOR - UNCAGE")
	pushSeqCmd(dt, 'SAI_SET', '-100')
	pushSeqCmd(dt, 'SAI_SET', '+100')
	
	#pushSeqCmd(dt, '', '', "ATT SWITCH - STBY")
	pushSeqCmd(dt, 'HUD_ATT_SW', 0)
	#pushSeqCmd(dt, '', '', "ATT SWITCH - AUTO")
	pushSeqCmd(dt, 'HUD_ATT_SW', 1)
	#pushSeqCmd(dt, '', '', "OBOGS CONTROL SWITCH - ON")
	pushSeqCmd(dt, 'OBOGS_SW', 1)
	
	#pushSeqCmd(dt, '', '', "HMD - AUTOSTART ALIGN")
	#pushSeqCmd(1, {check_condition = F18_AD_HMD_ALIGN)

	if groundStart:
		#pushSeqCmd(dt, '', '', 'HOOK BYPASS switch - FIELD')
		pushSeqCmd(dt, 'HOOK_BYPASS_SW', 1)
		pushSeqCmd(dt, 'ANTI-SKID switch - ON', 1)
		pushSeqCmd(dt, 'ANTI_SKID_SW', 1)
	else:
		#pushSeqCmd(dt, '', '', 'HOOK BYPASS switch - CARRIER')
		pushSeqCmd(dt, 'HOOK_BYPASS_SW', 0)
		pushSeqCmd(dt, 'ANTI-SKID switch - OFF', 1)
		pushSeqCmd(dt, 'ANTI_SKID_SW', 0)

	#pushSeqCmd(dt, '', '', "HUD ALT SWITCH - RDR")
	pushSeqCmd(dt, 'HUD_ALT_SW', 0)
	#pushSeqCmd(dt, '', '', "IR COOL SWITCH - NORM")
	pushSeqCmd(dt, 'IR_COOL_SW', 1)
	#pushSeqCmd(dt, '', '', "DISPENSER SWITCH - ON")
	pushSeqCmd(dt, 'CMSD_DISPENSE_SW', 1)
	#pushSeqCmd(dt, '', '', "ECM - REC")
	pushSeqCmd(dt, 'ECM_MODE_SW', 3)
	#pushSeqCmd(dt, '', '', "RWR POWER - ON")
	pushSeqCmd(dt, 'RWR_POWER_BTN', 1)

	# BEGIN INS START ALIGN
	insAlignTimerStart = getLastSeqTime()
	if groundStart:
		#pushSeqCmd(dt, '', '', "INS KNOB - GND")
		pushSeqCmd(dt, 'INS_SW', 2)
	else:
		#pushSeqCmd(dt, '', '', "INS KNOB - CV")
		pushSeqCmd(dt, 'INS_SW', 1)
	#pushSeqCmd(dt, '', '', "WAITING FOR INS ALIGN")
	pushSeqCmd(dt, 'AMPCD_PB_19', 1) # STD HDG OSB
	pushSeqCmd(dt, 'AMPCD_PB_19', 0) # release
	# END INS START ALIGN

	# After the AMPCD (center MFD) powers on, set it to night mode if doing night start.
	if dayStart:
		pass
	else:
		pushSeqCmd(dt, 'AMPCD_NIGHT_DAY', 0) # Press
		pushSeqCmd(dt, 'AMPCD_NIGHT_DAY', 1) # Release

	# LEFT ENGINE
	leftEngineCrankTimerStart = getLastSeqTime()
	#pushSeqCmd(dt, '', '', "LEFT ENGINE - START (40s)")
	#pushSeqCmd(dt, '', '', "ENG CRANK SWITCH - L")
	pushSeqCmd(dt, 'ENGINE_CRANK_SW', 0) # Left
	leftEngineCrankTimerEnd = engineCrankTime - (getLastSeqTime() - leftEngineCrankTimerStart)
	pushSeqCmd(leftEngineCrankTimerEnd, '', '', "Left engine at 15%, left throttle to IDLE")
	pushSeqCmd(dt, 'scriptKeyboard', '{VK_LMENU down}{VK_HOME}{VK_LMENU up}', 'ATTENTION: You must remap Throttle (Left) - IDLE to LAlt+Home') # FIXME pyWinAuto doesn't support RAlt or RCtrl.
	leftEngineStartTimerStart = getLastSeqTime()
	leftEngineStartTimerEnd = engineStartTime - (getLastSeqTime() - leftEngineStartTimerStart)
	pushSeqCmd(leftEngineStartTimerEnd, '', '', 'Left engine started')
	pushSeqCmd(dt, 'ENGINE_CRANK_SW', 1, 'Engine Crank switch - Off')
	# END LEFT ENGINE
	
	# Shut down APU
	pushSeqCmd(dt, 'APU_CONTROL_SW', 0, 'APU switch - Off')
	
	# BIT STOP
	#pushSeqCmd(dt, '', '', "BIT FORMAT - STOP OSB")
	pushSeqCmd(dt, 'RIGHT_DDI_PB_10', 1) # BIT page STOP OSB
	pushSeqCmd(dt, 'RIGHT_DDI_PB_10', 0) # release
	
	# Dispenser mode MAN 1 and RWR to HUD
	#pushSeqCmd(dt, '', '', "DISPENSER MODE - MAN 1")
	pushSeqCmd(dt, 'RIGHT_DDI_PB_18', 1) # MENU OSB
	pushSeqCmd(dt, 'RIGHT_DDI_PB_18', 0) # release
	pushSeqCmd(dt, 'RIGHT_DDI_PB_17', 1) # EW OSB
	pushSeqCmd(dt, 'RIGHT_DDI_PB_17', 0) # release
	pushSeqCmd(dt, 'RIGHT_DDI_PB_08', 1) # ALE-47 OSB
	pushSeqCmd(dt, 'RIGHT_DDI_PB_08', 0) # release
	pushSeqCmd(dt, 'RIGHT_DDI_PB_19', 1) # MODE OSB
	pushSeqCmd(dt, 'RIGHT_DDI_PB_19', 0) # release
	#pushSeqCmd(dt, '', '', "RWR display to HUD")
	pushSeqCmd(dt, 'RIGHT_DDI_PB_14', 1) # HUD OSB
	pushSeqCmd(dt, 'RIGHT_DDI_PB_14', 0) # release
	
	# RWR show on SA page
	#pushSeqCmd(dt, '', '', "SA page show RWR")
	pushSeqCmd(dt, 'RIGHT_DDI_PB_18', 1) # MENU OSB
	pushSeqCmd(dt, 'RIGHT_DDI_PB_18', 0) # release
	pushSeqCmd(dt, 'RIGHT_DDI_PB_13', 1) # SA OSB
	pushSeqCmd(dt, 'RIGHT_DDI_PB_13', 0) # release
	pushSeqCmd(dt, 'RIGHT_DDI_PB_05', 1) # SENSR OSB
	pushSeqCmd(dt, 'RIGHT_DDI_PB_05', 0) # release
	pushSeqCmd(dt, 'RIGHT_DDI_PB_07', 1) # RWR OSB
	pushSeqCmd(dt, 'RIGHT_DDI_PB_07', 0) # release
	pushSeqCmd(dt, 'RIGHT_DDI_PB_10', 1) # SA OSB
	pushSeqCmd(dt, 'RIGHT_DDI_PB_10', 0) # release
	
	# Go to FCS page
	##pushSeqCmd(dt, '', '', "Return to FCS page")
	#pushSeqCmd(dt, 'RIGHT_DDI_PB_18', 1) # MENU OSB
	#pushSeqCmd(dt, 'RIGHT_DDI_PB_18', 0) # release
	#pushSeqCmd(dt, 'RIGHT_DDI_PB_18', 1) # MENU OSB
	#pushSeqCmd(dt, 'RIGHT_DDI_PB_18', 0) # release
	#pushSeqCmd(dt, 'RIGHT_DDI_PB_15', 1) # FCS OSB
	#pushSeqCmd(dt, 'RIGHT_DDI_PB_15', 0) # release

	# Prepare for HMD align
	#pushSeqCmd(dt, '', '', "Align HMD")
	pushSeqCmd(dt, 'RIGHT_DDI_PB_18', 1) # MENU OSB
	pushSeqCmd(dt, 'RIGHT_DDI_PB_18', 0) # release
	pushSeqCmd(dt, 'RIGHT_DDI_PB_18', 1) # MENU OSB
	pushSeqCmd(dt, 'RIGHT_DDI_PB_18', 0) # release
	pushSeqCmd(dt, 'RIGHT_DDI_PB_08', 1) # BIT OSB
	pushSeqCmd(dt, 'RIGHT_DDI_PB_08', 0) # release
	pushSeqCmd(dt, 'RIGHT_DDI_PB_11', 1) # DISPLAYS OSB
	pushSeqCmd(dt, 'RIGHT_DDI_PB_11', 0) # release
	pushSeqCmd(dt, 'RIGHT_DDI_PB_11', 1) # HMD OSB
	pushSeqCmd(dt, 'RIGHT_DDI_PB_11', 0) # release
	pushSeqCmd(8, '', '', "HMD test complete")
	pushSeqCmd(dt, 'RIGHT_DDI_PB_10', 1) # STOP OSB
	pushSeqCmd(dt, 'RIGHT_DDI_PB_10', 0) # release
	pushSeqCmd(dt, 'RIGHT_DDI_PB_18', 1) # MENU OSB
	pushSeqCmd(dt, 'RIGHT_DDI_PB_18', 0) # release
	pushSeqCmd(dt, 'RIGHT_DDI_PB_18', 1) # MENU OSB
	pushSeqCmd(dt, 'RIGHT_DDI_PB_18', 0) # release
	pushSeqCmd(dt, 'RIGHT_DDI_PB_03', 1) # HMD OSB
	pushSeqCmd(dt, 'RIGHT_DDI_PB_03', 0) # release
	pushSeqCmd(dt, 'RIGHT_DDI_PB_20', 1) # ALIGN OSB
	pushSeqCmd(dt, 'RIGHT_DDI_PB_20', 0) # release
	pushSeqCmd(dt, 'scriptSpeech', 'Press and hold uncage to align.  Press and release uncage to go to next mode, use T D C to align.  Unbox align O S B when complete.')

	#pushSeqCmd(dt, '', '', "SET BINGO FUEL - 3000 LBS")
	for i in range(30):
		pushSeqCmd(dt, 'IFEI_UP_BTN', 1)
		pushSeqCmd(dt, 'IFEI_UP_BTN', 0)
	
	#pushSeqCmd(dt, '', '', "IFF - ON")
	pushSeqCmd(dt, 'UFC_IFF', 1) # UFC IFF button
	pushSeqCmd(dt, 'UFC_IFF', 0) # release
	pushSeqCmd(dt, 'UFC_ONOFF', 1) # UFC ON/OFF button
	pushSeqCmd(1, 'UFC_ONOFF', 0) # release after 1 second

	#pushSeqCmd(dt, '', '', "DATALINK - Link 4 ON")
	pushSeqCmd(dt, 'UFC_DL', 1) # UFC D/L button
	pushSeqCmd(dt, 'UFC_DL', 0) # release
	pushSeqCmd(dt, 'UFC_ONOFF', 1) # UFC ON/OFF button
	pushSeqCmd(1, 'UFC_ONOFF', 0) # release after 1 second
	#pushSeqCmd(dt, '', '', "DATALINK - Link 16 ON")
	pushSeqCmd(dt, 'UFC_DL', 1) # UFC D/L button, press again to go to the second D/L page
	pushSeqCmd(dt, 'UFC_DL', 0) # release
	pushSeqCmd(dt, 'UFC_ONOFF', 1) # UFC ON/OFF button
	pushSeqCmd(1, 'UFC_ONOFF', 0) # release after 1 second

	# Trigger the INS alignment check after the correct time (total process time minus the difference between now and when the process started).
	insAlignTimerEnd = insAlignTime - (getLastSeqTime() - insAlignTimerStart)
	pushSeqCmd(insAlignTimerEnd, '', '', "INS ALIGNMENT - READY")
	#pushSeqCmd(dt, '', '', "INS KNOB - IFA")
	pushSeqCmd(dt, 'INS_SW', 4)
	
	# NOTE Should be done after INS alignement is complete.
	#pushSeqCmd(dt, '', '', "AMPCD GAIN - DOWN TO MIN FOR VR")
	pushSeqCmd(dt, 'AMPCD_GAIN_SW', 0) # Down
	pushSeqCmd(3, 'AMPCD_GAIN_SW', 1) # Center after 3 seconds
	
	#pushSeqCmd(dt, '', '', "PARK BRK HANDLE - FULLY STOWED")
	pushSeqCmd(dt, 'EMERGENCY_PARKING_BRAKE_ROTATE', 2)
	pushSeqCmd(dt, 'EMERGENCY_PARKING_BRAKE_PULL', 1)
	pushSeqCmd(dt, 'EMERGENCY_PARKING_BRAKE_ROTATE', 0)
	
	#pushSeqCmd(dt, '', '', "EJECTION SEAT SAFE/ARM HANDLE - ARM")
	pushSeqCmd(dt, 'EJECTION_SEAT_ARMED', 0)
	
	return seq

# Adds waypoints with the HSI DATA screen.
def FlashpointLevantWaypoints(config):
	import re # Needed for regular expression split.
	seq = []
	seqTime = 0
	dt = 0.3
	
	def pushSeqCmd(dt, cmd, arg, msg = ''):
		nonlocal seq, seqTime
		seqTime += dt
		seq.append({
			'time': round(seqTime, 2),
			'cmd': cmd,
			'arg': arg,
			'msg': msg,
		})
		
	def getLastSeqTime():
		nonlocal seq
		return float(seq[len(seq) - 1]['time'])

	def pressRelease(button):
		nonlocal seq
		pushSeqCmd(dt, button, 1) # Press
		pushSeqCmd(dt, button, 0) # Release

	def stripNonNumeric(string):
		nonNumeric = re.compile(r'[^\d.]+')
		return nonNumeric.sub('', string)

	# Parses ddm string with the following format: "N 36°21.0739', E 36°17.0249'"
	def parseDDMToListOLD(ddm):
		#example: ddm = "N 36°21.0739', E 36°17.0249'"
		ddmList = []
		accumulator = ''
		# Iterate through the ddm string one character at a time.  We'll accumulate numbers until we hit a delimiter, then append the accumulator to the List and start getting the next number.
		for char in ddm:
			# If it's a cardinal direction, add that to the list, and blank the accumulator.
			if char in 'NESW':
				ddmList.append(char)
				accumulator = ''
			# If it's a number, add it to the accumulator.
			elif char in '01234567890':
				accumulator += char
			# If it's a DDM delimiter, dump the accumulator to the list, then blank the accumulator.
			elif char in "°.'":
				ddmList.append(accumulator)
				accumulator = ''
			# If it's a comma, blank the accumulator
			elif char == ',':
				accumulator = ''
			# If it's anything else (e.g. a space), blank the accumulator.
			else:
				accumulator = ''
		# End result should be ['N', '36', '21', '0739', 'E', '36', '17', '0249']
		return ddmList

	# Pass in "N 36°21.0739', E 36°17.0249'" or "N 36 21 0739 E 36 17 0249"
	# Returns ['N', '36', '21', '0739', 'E', '36', '17', '0249']
	def ddmStringToList(ddm):
		ddm = re.sub(r"[°.',]", ' ', ddm) # Replace all delimiters with spaces.
		return ddm.split() # Then split the string on whitespace and we have the result.
	
	# Pass in "N 36°21'44.37\", E 36°17'14.99\"" or "N 36 21 44.37 E 36 17 14.99"
	# Returns ['N', '36', '21', '44', '37', 'E', '36', '17', '14', '99']
	def dmsStringToList(dms):
		dms = re.sub(r"[°'.\",]", ' ', dms) # Replace all delimiters with spaces.
		return dms.split() # Then split the string on whitespace and we have the result.

	# Presses the keys necessary to enter the waypoint.
	# Starting state: Desired waypoint number selected, in HSI DATA page, with PRECISE boxed.
	def ddmInput(ddmList):
		# Enter the Northing.
		# Northing direction
		pressRelease(ufcKeys[ddmList[0]])
		# Degrees
		for key in ddmList[1]:
			pressRelease(ufcKeys[key])
		# Minutes
		for key in ddmList[2]:
			pressRelease(ufcKeys[key])
		# Enter
		pressRelease(ufcKeys['ENT'])
		# Seconds
		for key in ddmList[3]:
			pressRelease(ufcKeys[key])
		# Enter
		pressRelease(ufcKeys['ENT'])

		# Enter the Easting.
		# Easting direction
		pressRelease(ufcKeys[ddmList[4]])
		# Degrees
		for key in ddmList[5].zfill(3): # Pad easting degrees with zeros to 3 digits before iterating.
			pressRelease(ufcKeys[key])
		# Minutes
		for key in ddmList[6]:
			pressRelease(ufcKeys[key])
		# Enter
		pressRelease(ufcKeys['ENT'])
		# Seconds
		for key in ddmList[7]:
			pressRelease(ufcKeys[key])
		# Enter
		pressRelease(ufcKeys['ENT'])
	
	ufcKeys = {
		'N': 'UFC_2',
		'S': 'UFC_8',
		'E': 'UFC_6',
		'W': 'UFC_4',
		'0': 'UFC_0',
		'1': 'UFC_1',
		'2': 'UFC_2',
		'3': 'UFC_3',
		'4': 'UFC_4',
		'5': 'UFC_5',
		'6': 'UFC_6',
		'7': 'UFC_7',
		'8': 'UFC_8',
		'9': 'UFC_9',
		'ENT': 'UFC_ENT',
		'OSB1': 'UFC_OS1',
		'OSB2': 'UFC_OS2',
		'OSB3': 'UFC_OS3',
		'OSB4': 'UFC_OS4',
		'OSB5': 'UFC_OS5',
	}

	# Must start with WP0 selected, not in TAC menu, PRECISE not boxed.
	pressRelease('RIGHT_DDI_PB_18') # MENU OSB
	pressRelease('RIGHT_DDI_PB_18') # MENU OSB
	pressRelease('RIGHT_DDI_PB_02') # HSI OSB
	pressRelease('RIGHT_DDI_PB_10') # DATA OSB
	pressRelease('RIGHT_DDI_PB_19') # PRECISE OSB
	pressRelease('RIGHT_DDI_PB_12') # Up Arrow OSB, changes to waypoint 1
	pressRelease('RIGHT_DDI_PB_12') # Up Arrow OSB, changes to waypoint 2
	pressRelease('RIGHT_DDI_PB_12') # Up Arrow OSB, changes to waypoint 3
	pressRelease('RIGHT_DDI_PB_05') # UFC OSB
	pressRelease('UFC_OS1') # UFC POSN OSB

	wp = "N 36°21.0739', E 36°17.0249'"
	# Convert the wp string into a list with all its elements.
	ddmList = ddmStringToList(wp)
	# Enter the waypoint into the HSI.
	ddmInput(ddmList)

	pressRelease('RIGHT_DDI_PB_10') # HSI OSB

	return seq


"""	
Hatay:
DMS: N 36°21'44.37", E 36°17'14.99"
DDM: N 36°21.0739', E 36°17.0249'
MGRS: 37 S BA 56624 27553
77m, 253ft

Incirlik:
DMS: N 37°00'07.37", E 35°25'33.91"
DDM: N 37°00.0122', E 35°25.0565'
MGRS: 36 S YF 15875 97851
N/S (m): 221207, E/W (m): -35240
58m, 191ft

Taftanaz:
DMS: N 35°58'26.77", E 36°46'53.19"
DDM: N 35°58.0446', E 36°46.0886'
MGRS: 37 S BV 99965 83351
N/S (m): 103485, E/W (m): 82766
311m, 1020ft

Abu al-Duhur:
DMS: N 35°43'56.30", E 37°06'14.85"
DDM: N 35°43.9384', E 37°06.2477'
MGRS: 37 S CV 28543 55914
N/S (m): 76048, E/W (m): 111344
250m, 820ft
"""
