# Return a Dictionary of script titles and their corresponding function names.  This is a list of scripts that users will be selecting from.  The module may have other utility functions that will not be run directly by the users.
def getScriptFunctions():
	return {
		'Cold Start, Ground, Day, With HMD': 'ColdStartGroundDayWithHmd',
		'Cold Start, Ground, Day, No HMD': 'ColdStartGroundDayNoHmd',
		'Cold Start, Ground, Night, With HMD': 'ColdStartGroundNightWithHmd',
		'Cold Start, Ground, Night, No HMD': 'ColdStartGroundNightNoHmd',
		'Cold Start, Carrier, Day, With HMD': 'ColdStartCarrierDayWithHmd',
		'Cold Start, Carrier, Day, No HMD': 'ColdStartCarrierDayNoHmd',
		'Cold Start, Carrier, Night, With HMD': 'ColdStartCarrierNightWithHmd',
		'Cold Start, Carrier, Night, No HMD': 'ColdStartCarrierNightNoHmd',
		'Hot Start, Ground, Day, With HMD': 'HotStartGroundDayWithHmd',
		'Hot Start, Ground, Day, No HMD': 'HotStartGroundDayNoHmd',
		'Hot Start, Ground, Night, With HMD': 'HotStartGroundNightWithHmd',
		'Hot Start, Ground, Night, No HMD': 'HotStartGroundNightNoHmd',
		'Hot Start, Carrier, Day, With HMD': 'HotStartCarrierDayWithHmd',
		'Hot Start, Carrier, Day, No HMD': 'HotStartCarrierDayNoHmd',
		'Hot Start, Carrier, Night, With HMD': 'HotStartCarrierNightWithHmd',
		'Hot Start, Carrier, Night, No HMD': 'HotStartCarrierNightNoHmd',
		'Air Start, Day': 'AirStartDay',
		'Air Start, Night': 'AirStartNight',
		'Shutdown': 'Shutdown',
		#'Flashpoint Levant Waypoints': 'FlashpointLevantWaypoints',
		#'Test': 'Test',
	}

def getInfo():
	return """ATTENTION: You must remap "Throttle (Left) - IDLE" to LAlt+Home, and "Throttle (Left) - OFF" to LAlt+End.  This is because pyWinAuto doesn't support RAlt or RCtrl."""

# Returns 0-65535 scaled by multiple (0-1), eg for 50% call int16(0.5)
def int16(mult = 1):
	int16 = 65535
	return int(mult * int16)

def Test(config):
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
	
	pushSeqCmd(dt, 'IFEI_UP_BTN', 1)
	pushSeqCmd(4.3, 'IFEI_UP_BTN', 0)

	return seq

def ColdStartGroundDayWithHmd(config):
	return ColdStart(config, groundStart = True, dayStart = True, hmd = True)

def ColdStartGroundDayNoHmd(config):
	return ColdStart(config, groundStart = True, dayStart = True, hmd = False)

def ColdStartGroundNightWithHmd(config):
	return ColdStart(config, groundStart = True, dayStart = False, hmd = True)

def ColdStartGroundNightNoHmd(config):
	return ColdStart(config, groundStart = True, dayStart = False, hmd = False)

def ColdStartCarrierDayWithHmd(config):
	return ColdStart(config, groundStart = False, dayStart = True, hmd = True)

def ColdStartCarrierDayNoHmd(config):
	return ColdStart(config, groundStart = False, dayStart = True, hmd = False)

def ColdStartCarrierNightWithHmd(config):
	return ColdStart(config, groundStart = False, dayStart = False, hmd = True)

def ColdStartCarrierNightNoHmd(config):
	return ColdStart(config, groundStart = False, dayStart = False, hmd = False)

def HotStartGroundDayWithHmd(config):
	return HotStart(config, groundStart = True, dayStart = True, hmd = True)

def HotStartGroundDayNoHmd(config):
	return HotStart(config, groundStart = True, dayStart = True, hmd = False)

def HotStartGroundNightWithHmd(config):
	return HotStart(config, groundStart = True, dayStart = False, hmd = True)

def HotStartGroundNightNoHmd(config):
	return HotStart(config, groundStart = True, dayStart = False, hmd = False)

def HotStartCarrierDayWithHmd(config):
	return HotStart(config, groundStart = False, dayStart = True, hmd = True)

def HotStartCarrierDayNoHmd(config):
	return HotStart(config, groundStart = False, dayStart = True, hmd = False)

def HotStartCarrierNightWithHmd(config):
	return HotStart(config, groundStart = False, dayStart = False, hmd = True)

def HotStartCarrierNightNoHmd(config):
	return HotStart(config, groundStart = False, dayStart = False, hmd = False)

def AirStartDay(config):
	return AirStart(config, dayStart = True)

def AirStartNight(config):
	return AirStart(config, dayStart = False)


# Some settings change depending on whether you're starting from the ground or from a carrier.
def ColdStart(config, groundStart = True, dayStart = True, hmd = True):
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

	apuStartTime = 15
	engineCrankTime = 7 # Seconds until engine is at 15% after setting crank switch.
	engineStartTime = 35 # Seconds until engine is fully started after moving throttle to idle.
	insAlignTime = 1 * 60 + 55 # 1m55s
	
	pushSeqCmd(0, '', '', "Running Cold Start sequence")
	pushSeqCmd(dt, 'scriptSpeech', "Warning, uses non standard key bindings.")
	
	pushSeqCmd(dt, 'BATTERY_SW', 2, 'BATT switch - On')
	
	# Exterior light switch ... OFF
	pushSeqCmd(dt, 'THROTTLE_EXT_L_SW', 0) # 0 = OFF, 1 = ON
	# Other lights
	if dayStart:
		pushSeqCmd(dt, 'CONSOLES_DIMMER', int16())
		pushSeqCmd(dt, 'INST_PNL_DIMMER', int16())
	else:
		pushSeqCmd(dt, 'CONSOLES_DIMMER', int16(0.5))
		pushSeqCmd(dt, 'INST_PNL_DIMMER', int16(0.5))
	
	# Start APU
	apuTimerStart = getLastSeqTime()
	pushSeqCmd(dt, 'APU_CONTROL_SW', 1, 'APU switch - On')
	
	# Close canopy while waiting for APU
	pushSeqCmd(dt, 'CANOPY_SW', 0)
	pushSeqCmd(9, 'CANOPY_SW', 1) # Turn off canopy switch 9 seconds later.
	
	apuTimerEnd = apuStartTime - (getLastSeqTime() - apuTimerStart)
	pushSeqCmd(apuTimerEnd, '', '', "APU started")
	# APU started

	# All MFDs on
	if dayStart:
		pushSeqCmd(dt, 'LEFT_DDI_BRT_SELECT', 2) # DAY
		pushSeqCmd(dt, 'RIGHT_DDI_BRT_SELECT', 2) # DAY
		pushSeqCmd(dt, 'AMPCD_BRT_CTL', int16())
	else:
		pushSeqCmd(dt, 'LEFT_DDI_BRT_SELECT', 1) # NIGHT
		pushSeqCmd(dt, 'RIGHT_DDI_BRT_SELECT', 1) # NIGHT
		pushSeqCmd(dt, 'AMPCD_BRT_CTL', int16(0.5))
	
	# HUD, UFC, IFEI brightness
	if dayStart:
		pushSeqCmd(dt, 'HUD_SYM_BRT', int16())
		pushSeqCmd(dt, 'HUD_SYM_BRT_SELECT', 1) # 0 = NIGHT, 1 = DAY
		pushSeqCmd(dt, 'UFC_BRT', int16())
		pushSeqCmd(dt, 'IFEI', int16()) # IFEI brightness to max
	else:
		pushSeqCmd(dt, 'HUD_SYM_BRT', int16(0.5))
		pushSeqCmd(dt, 'HUD_SYM_BRT_SELECT', 0) # 0 = NIGHT, 1 = DAY
		pushSeqCmd(dt, 'UFC_BRT', int16(0.5))
		pushSeqCmd(dt, 'IFEI', 1000) # IFEI brightness to min

	# Radio volume
	pushSeqCmd(dt, 'UFC_COMM1_VOL', int16(0.8), 'COMM 1 vol - 80%')
	pushSeqCmd(dt, 'UFC_COMM2_VOL', int16(0.8), 'COMM 2 vol - 80%')
	
	# RIGHT ENGINE
	pushSeqCmd(dt, 'ENGINE_CRANK_SW', 2) # Right
	pushSeqCmd(7, '', '', "Right engine at 15%, right throttle to IDLE")
	pushSeqCmd(dt, 'scriptKeyboard', '{VK_RSHIFT down}')
	pushSeqCmd(dt, 'scriptKeyboard', '{VK_HOME}')
	pushSeqCmd(dt, 'scriptKeyboard', '{VK_RSHIFT up}')
	pushSeqCmd(35, '', '', 'Right engine started')
	pushSeqCmd(dt, 'ENGINE_CRANK_SW', 1, 'Engine Crank switch - Off')
	# END RIGHT ENGINE

	# FIXME The engine monitor instrument doesn't pick up the cockpit lighting mode switch position unless it's set after the right engine starts.
	if dayStart:
		pushSeqCmd(dt, 'COCKKPIT_LIGHT_MODE_SW', 0) # NOTE misspelling 0 = DAY (default), 1 = NITE, 2 = NVG
	else:
		pushSeqCmd(dt, 'COCKKPIT_LIGHT_MODE_SW', 1) # NOTE misspelling 0 = DAY (default), 1 = NITE, 2 = NVG
	
	# HMD knob - ON
	if hmd:
		if dayStart:
			pushSeqCmd(dt, 'HMD_OFF_BRT', int16())
		else:
			pushSeqCmd(dt, 'HMD_OFF_BRT', int16(0.5))
	
	# BLEED AIR KNOB - CYCLE THRU OFF TO NORM
	pushSeqCmd(dt, 'BLEED_AIR_KNOB', 3)
	pushSeqCmd(dt, 'BLEED_AIR_KNOB', 0)
	pushSeqCmd(dt, 'BLEED_AIR_KNOB', 1)
	pushSeqCmd(dt, 'BLEED_AIR_KNOB', 2)

	# RADAR ALTIMETER - ON, SET TO 50 FT
	maxRadAlt = int(int16() * 3 + 8194) # Just over 3 full turns of the knob from 0 to max.
	pushSeqCmd(dt, 'RADALT_HEIGHT', '-'+str(maxRadAlt)) # All the way off
	pushSeqCmd(dt, 'RADALT_HEIGHT', '+'+str(int16(0.28))) # Turn knob up 28% of one turn to get 50 ft.

	# RADAR KNOB - OPR
	pushSeqCmd(dt, 'RADAR_SW', 2)
	# FCS RESET BUTTON - PUSH
	pushSeqCmd(dt, 'FCS_RESET_BTN', 1) # Press
	pushSeqCmd(dt, 'FCS_RESET_BTN', 0) # Release
	
	# FLAP SWITCH - HALF
	pushSeqCmd(dt, 'FLAP_SW', 1)
	# T/O TRIM BUTTON - PRESS UNTIL TRIM ADVISORY DISPLAYED (only momentary press actually necessary??)
	pushSeqCmd(dt, 'TO_TRIM_BTN', 1)
	pushSeqCmd(dt, 'TO_TRIM_BTN', 0)
	
	# STANDBY ATTITUDE REFERENCE INDICATOR - UNCAGE
	pushSeqCmd(dt, 'SAI_SET', '-100')
	pushSeqCmd(dt, 'SAI_SET', '+100')
	
	# ATT SWITCH - STBY
	pushSeqCmd(dt, 'HUD_ATT_SW', 0)
	# ATT SWITCH - AUTO
	pushSeqCmd(dt, 'HUD_ATT_SW', 1)
	# OBOGS CONTROL SWITCH - ON
	pushSeqCmd(dt, 'OBOGS_SW', 1)
	
	if groundStart:
		# HOOK BYPASS switch - FIELD
		pushSeqCmd(dt, 'HOOK_BYPASS_SW', 1)
		pushSeqCmd(dt, 'ANTI-SKID switch - ON', 1)
		pushSeqCmd(dt, 'ANTI_SKID_SW', 1)
	else:
		# HOOK BYPASS switch - CARRIER
		pushSeqCmd(dt, 'HOOK_BYPASS_SW', 0)
		pushSeqCmd(dt, 'ANTI-SKID switch - OFF', 1)
		pushSeqCmd(dt, 'ANTI_SKID_SW', 0)

	# HUD ALT SWITCH - RDR
	pushSeqCmd(dt, 'HUD_ALT_SW', 0)
	# IR COOL SWITCH - NORM
	pushSeqCmd(dt, 'IR_COOL_SW', 1)
	# DISPENSER SWITCH - ON
	pushSeqCmd(dt, 'CMSD_DISPENSE_SW', 1)
	# ECM - REC
	pushSeqCmd(dt, 'ECM_MODE_SW', 3)
	# RWR POWER - ON
	pushSeqCmd(dt, 'RWR_POWER_BTN', 1)

	# BEGIN INS START ALIGN
	insAlignTimerStart = getLastSeqTime()
	if groundStart:
		# INS KNOB - GND
		pushSeqCmd(dt, 'INS_SW', 2)
	else:
		# INS KNOB - CV
		pushSeqCmd(dt, 'INS_SW', 1)
	# Select stored heading alignment.
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
	pushSeqCmd(dt, 'ENGINE_CRANK_SW', 0) # Left
	pushSeqCmd(7, '', '', "Left engine at 15%, left throttle to IDLE")
	pushSeqCmd(dt, 'scriptKeyboard', '{VK_LMENU down}', 'ATTENTION: You must remap Throttle (Left) - IDLE to LAlt+Home') # FIXME pyWinAuto doesn't support RAlt or RCtrl.
	pushSeqCmd(dt, 'scriptKeyboard', '{VK_HOME}', 'ATTENTION: You must remap Throttle (Left) - IDLE to LAlt+Home') # FIXME pyWinAuto doesn't support RAlt or RCtrl.
	pushSeqCmd(dt, 'scriptKeyboard', '{VK_LMENU up}', 'ATTENTION: You must remap Throttle (Left) - IDLE to LAlt+Home') # FIXME pyWinAuto doesn't support RAlt or RCtrl.
	pushSeqCmd(35, '', '', 'Left engine started')
	pushSeqCmd(dt, 'ENGINE_CRANK_SW', 1, 'Engine Crank switch - Off')
	# END LEFT ENGINE
	
	# Shut down APU
	pushSeqCmd(dt, 'APU_CONTROL_SW', 0, 'APU switch - Off')
	
	# BIT STOP
	# We start on the BIT page by default, but just in case the user hits a button, select it manually.
	pushSeqCmd(dt, 'RIGHT_DDI_PB_18', 1) # MENU OSB
	pushSeqCmd(dt, 'RIGHT_DDI_PB_18', 0) # release
	pushSeqCmd(dt, 'RIGHT_DDI_PB_18', 1) # MENU OSB
	pushSeqCmd(dt, 'RIGHT_DDI_PB_18', 0) # release
	pushSeqCmd(dt, 'RIGHT_DDI_PB_08', 1) # BIT OSB
	pushSeqCmd(dt, 'RIGHT_DDI_PB_08', 0) # release
	pushSeqCmd(dt, 'RIGHT_DDI_PB_10', 1) # BIT page STOP OSB
	pushSeqCmd(dt, 'RIGHT_DDI_PB_10', 0) # release
	
	# EW page...
	# Dispenser mode MAN 1
	pushSeqCmd(dt, 'RIGHT_DDI_PB_18', 1) # MENU OSB
	pushSeqCmd(dt, 'RIGHT_DDI_PB_18', 0) # release
	pushSeqCmd(dt, 'RIGHT_DDI_PB_17', 1) # EW OSB
	pushSeqCmd(dt, 'RIGHT_DDI_PB_17', 0) # release
	pushSeqCmd(dt, 'RIGHT_DDI_PB_08', 1) # ALE-47 OSB
	pushSeqCmd(dt, 'RIGHT_DDI_PB_08', 0) # release
	pushSeqCmd(dt, 'RIGHT_DDI_PB_19', 1) # MODE OSB
	pushSeqCmd(dt, 'RIGHT_DDI_PB_19', 0) # release
	# RWR display to HUD
	pushSeqCmd(dt, 'RIGHT_DDI_PB_14', 1) # HUD OSB
	pushSeqCmd(dt, 'RIGHT_DDI_PB_14', 0) # release
	
	# RWR show on SA page
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
	#pushSeqCmd(dt, 'RIGHT_DDI_PB_18', 1) # MENU OSB
	#pushSeqCmd(dt, 'RIGHT_DDI_PB_18', 0) # release
	#pushSeqCmd(dt, 'RIGHT_DDI_PB_18', 1) # MENU OSB
	#pushSeqCmd(dt, 'RIGHT_DDI_PB_18', 0) # release
	#pushSeqCmd(dt, 'RIGHT_DDI_PB_15', 1) # FCS OSB
	#pushSeqCmd(dt, 'RIGHT_DDI_PB_15', 0) # release

	if hmd:
		# Prepare for HMD align
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

	# SET BINGO FUEL - 3000 LBS
	pushSeqCmd(dt, 'IFEI_UP_BTN', 1)
	pushSeqCmd(4.25, 'IFEI_UP_BTN', 0) # Release after 4.25 seconds to get 3000 lbs.
	
	# IFF - ON
	pushSeqCmd(dt, 'UFC_IFF', 1) # UFC IFF button
	pushSeqCmd(dt, 'UFC_IFF', 0) # release
	pushSeqCmd(dt, 'UFC_ONOFF', 1) # UFC ON/OFF button
	pushSeqCmd(1, 'UFC_ONOFF', 0) # release after 1 second

	#DATALINK - Link 4 ON
	pushSeqCmd(dt, 'UFC_DL', 1) # UFC D/L button
	pushSeqCmd(dt, 'UFC_DL', 0) # release
	pushSeqCmd(dt, 'UFC_ONOFF', 1) # UFC ON/OFF button
	pushSeqCmd(1, 'UFC_ONOFF', 0) # release after 1 second
	# DATALINK - Link 16 ON
	pushSeqCmd(dt, 'UFC_DL', 1) # UFC D/L button, press again to go to the second D/L page
	pushSeqCmd(dt, 'UFC_DL', 0) # release
	pushSeqCmd(dt, 'UFC_ONOFF', 1) # UFC ON/OFF button
	pushSeqCmd(1, 'UFC_ONOFF', 0) # release after 1 second

	# Trigger the INS alignment check after the correct time (total process time minus the difference between now and when the process started).
	insAlignTimerEnd = insAlignTime - (getLastSeqTime() - insAlignTimerStart)
	pushSeqCmd(insAlignTimerEnd, '', '', "INS ALIGNMENT - READY")
	#INS KNOB - IFA
	pushSeqCmd(dt, 'INS_SW', 4)
	
	# AMPCD GAIN - DOWN TO MIN FOR VR
	# NOTE Should be done after INS alignement is complete.
	pushSeqCmd(dt, 'AMPCD_GAIN_SW', 0) # Down
	pushSeqCmd(3, 'AMPCD_GAIN_SW', 1) # Center after 3 seconds
	
	# Show local time in HUD
	# IMPORTANT If you are doing a CV alignment, this must be done either before starting alignment, or after alignment is complete and INS knob is set to IFA.  That is because when doing a CV alignment, PB 17 says MAN instead of TIMEUFC, and if pressed, it turns off the STD HDG.  We'll do this on the center MFD because it will already have the HSI on it for the alignment.
	pushSeqCmd(dt, 'AMPCD_PB_17', 1) # TIMEUFC OSB
	pushSeqCmd(dt, 'AMPCD_PB_17', 0) # release
	pushSeqCmd(dt, 'UFC_OS5', 1) # LTOD OSB
	pushSeqCmd(dt, 'UFC_OS5', 0) # release
	pushSeqCmd(dt, 'AMPCD_PB_17', 1) # TIMEUFC OSB
	pushSeqCmd(dt, 'AMPCD_PB_17', 0) # release
	
	# Put left MFD on STORES page (it should already be on the TAC menu)
	pushSeqCmd(dt, 'LEFT_DDI_PB_05', 1) # STORES OSB
	pushSeqCmd(dt, 'LEFT_DDI_PB_05', 0) # release

	# PARK BRK HANDLE - FULLY STOWED
	pushSeqCmd(dt, 'EMERGENCY_PARKING_BRAKE_ROTATE', 2)
	pushSeqCmd(dt, 'EMERGENCY_PARKING_BRAKE_PULL', 1)
	pushSeqCmd(dt, 'EMERGENCY_PARKING_BRAKE_ROTATE', 0)

	# MASTER ARM - ARM
	pushSeqCmd(dt, 'MASTER_ARM_SW', 1)
	
	# EJECTION SEAT SAFE/ARM HANDLE - ARM
	pushSeqCmd(dt, 'EJECTION_SEAT_ARMED', 0)
	
	return seq


# Some settings change depending on whether you're starting from the ground or from a carrier.
def HotStart(config, groundStart = True, dayStart = True, hmd = True):
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

	pushSeqCmd(0, '', '', "Running Hot Start sequence")
	
	# Exterior light switch ... OFF
	pushSeqCmd(dt, 'THROTTLE_EXT_L_SW', 0) # 0 = OFF, 1 = ON
	# Other lights
	if dayStart:
		pushSeqCmd(dt, 'CONSOLES_DIMMER', int16())
		pushSeqCmd(dt, 'INST_PNL_DIMMER', int16())
	else:
		pushSeqCmd(dt, 'CONSOLES_DIMMER', int16(0.5))
		pushSeqCmd(dt, 'INST_PNL_DIMMER', int16(0.5))
		pushSeqCmd(dt, 'COCKKPIT_LIGHT_MODE_SW', 1) # NOTE misspelling 0 = DAY (default), 1 = NITE, 2 = NVG
	
	# All MFDs on
	if dayStart:
		pushSeqCmd(dt, 'LEFT_DDI_BRT_SELECT', 2) # DAY
		pushSeqCmd(dt, 'RIGHT_DDI_BRT_SELECT', 2) # DAY
		pushSeqCmd(dt, 'AMPCD_BRT_CTL', int16())
	else:
		pushSeqCmd(dt, 'LEFT_DDI_BRT_SELECT', 1) # NIGHT
		pushSeqCmd(dt, 'RIGHT_DDI_BRT_SELECT', 1) # NIGHT
		pushSeqCmd(dt, 'AMPCD_BRT_CTL', int16(0.5))
	
	# HUD, UFC, IFEI brightness
	if dayStart:
		pushSeqCmd(dt, 'HUD_SYM_BRT', int16())
		pushSeqCmd(dt, 'HUD_SYM_BRT_SELECT', 1) # 0 = NIGHT, 1 = DAY
		pushSeqCmd(dt, 'UFC_BRT', int16())
		pushSeqCmd(dt, 'IFEI', int16()) # IFEI brightness to max
	else:
		pushSeqCmd(dt, 'HUD_SYM_BRT', int16(0.5))
		pushSeqCmd(dt, 'HUD_SYM_BRT_SELECT', 0) # 0 = NIGHT, 1 = DAY
		pushSeqCmd(dt, 'UFC_BRT', int16(0.5))
		pushSeqCmd(dt, 'IFEI', 1000) # IFEI brightness to min

	# Radio volume
	pushSeqCmd(dt, 'UFC_COMM1_VOL', int16(0.8), 'COMM 1 vol - 80%')
	pushSeqCmd(dt, 'UFC_COMM2_VOL', int16(0.8), 'COMM 2 vol - 80%')

	# HMD knob - ON
	if hmd:
		if dayStart:
			pushSeqCmd(dt, 'HMD_OFF_BRT', int16())
		else:
			pushSeqCmd(dt, 'HMD_OFF_BRT', int16(0.5))

	# RADAR ALTIMETER - ON, SET TO 50 FT
	maxRadAlt = int(int16() * 3 + 8194) # Just over 3 full turns of the knob from 0 to max.
	pushSeqCmd(dt, 'RADALT_HEIGHT', '-'+str(maxRadAlt)) # All the way off
	pushSeqCmd(dt, 'RADALT_HEIGHT', '+'+str(int16(0.28))) # Turn knob up 28% of one turn to get 50 ft.

	# FLAP SWITCH - HALF
	pushSeqCmd(dt, 'FLAP_SW', 1)
	# T/O TRIM BUTTON - PRESS UNTIL TRIM ADVISORY DISPLAYED
	pushSeqCmd(dt, 'TO_TRIM_BTN', 1)
	pushSeqCmd(dt, 'TO_TRIM_BTN', 0)
	
	if groundStart:
		# HOOK BYPASS switch - FIELD
		pushSeqCmd(dt, 'HOOK_BYPASS_SW', 1)
		pushSeqCmd(dt, 'ANTI-SKID switch - ON', 1)
		pushSeqCmd(dt, 'ANTI_SKID_SW', 1)
	else:
		# HOOK BYPASS switch - CARRIER
		pushSeqCmd(dt, 'HOOK_BYPASS_SW', 0)
		pushSeqCmd(dt, 'ANTI-SKID switch - OFF', 1)
		pushSeqCmd(dt, 'ANTI_SKID_SW', 0)

	# HUD ALT SWITCH - RDR
	pushSeqCmd(dt, 'HUD_ALT_SW', 0)
	# IR COOL SWITCH - NORM
	pushSeqCmd(dt, 'IR_COOL_SW', 1)
	# DISPENSER SWITCH - ON
	pushSeqCmd(dt, 'CMSD_DISPENSE_SW', 1)
	# ECM - REC
	pushSeqCmd(dt, 'ECM_MODE_SW', 3)
	# RWR POWER - ON
	pushSeqCmd(dt, 'RWR_POWER_BTN', 1)

	# After the AMPCD (center MFD) powers on, set it to night mode if doing night start.
	if dayStart:
		pushSeqCmd(dt, 'AMPCD_NIGHT_DAY', 2) # Press
		pushSeqCmd(dt, 'AMPCD_NIGHT_DAY', 1) # Release
	else:
		pushSeqCmd(dt, 'AMPCD_NIGHT_DAY', 0) # Press
		pushSeqCmd(dt, 'AMPCD_NIGHT_DAY', 1) # Release

	# EW page...
	# Dispenser mode MAN 1
	pushSeqCmd(dt, 'RIGHT_DDI_PB_18', 1) # MENU OSB
	pushSeqCmd(dt, 'RIGHT_DDI_PB_18', 0) # release
	pushSeqCmd(dt, 'RIGHT_DDI_PB_17', 1) # EW OSB
	pushSeqCmd(dt, 'RIGHT_DDI_PB_17', 0) # release
	pushSeqCmd(15, '', '', 'Waiting for ALE-47 Self test to complete')
	pushSeqCmd(dt, 'RIGHT_DDI_PB_08', 1) # ALE-47 OSB
	pushSeqCmd(dt, 'RIGHT_DDI_PB_08', 0) # release
	pushSeqCmd(dt, 'RIGHT_DDI_PB_19', 1) # MODE OSB
	pushSeqCmd(dt, 'RIGHT_DDI_PB_19', 0) # release
	# RWR display to HUD
	pushSeqCmd(dt, 'RIGHT_DDI_PB_14', 1) # HUD OSB
	pushSeqCmd(dt, 'RIGHT_DDI_PB_14', 0) # release
	
	# RWR show on SA page
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

	# Show local time in HUD
	pushSeqCmd(dt, 'RIGHT_DDI_PB_18', 1) # MENU OSB
	pushSeqCmd(dt, 'RIGHT_DDI_PB_18', 0) # release
	pushSeqCmd(dt, 'RIGHT_DDI_PB_18', 1) # MENU OSB
	pushSeqCmd(dt, 'RIGHT_DDI_PB_18', 0) # release
	pushSeqCmd(dt, 'RIGHT_DDI_PB_02', 1) # HSI OSB
	pushSeqCmd(dt, 'RIGHT_DDI_PB_02', 0) # release
	pushSeqCmd(dt, 'RIGHT_DDI_PB_17', 1) # TIMEUFC OSB
	pushSeqCmd(dt, 'RIGHT_DDI_PB_17', 0) # release
	pushSeqCmd(dt, 'UFC_OS5', 1) # LTOD OSB
	pushSeqCmd(dt, 'UFC_OS5', 0) # release
	pushSeqCmd(dt, 'RIGHT_DDI_PB_17', 1) # TIMEUFC OSB
	pushSeqCmd(dt, 'RIGHT_DDI_PB_17', 0) # release
	
	#if hmd:
	#	# Prepare for HMD align
	#	pushSeqCmd(dt, 'RIGHT_DDI_PB_18', 1) # MENU OSB
	#	pushSeqCmd(dt, 'RIGHT_DDI_PB_18', 0) # release
	#	pushSeqCmd(dt, 'RIGHT_DDI_PB_18', 1) # MENU OSB
	#	pushSeqCmd(dt, 'RIGHT_DDI_PB_18', 0) # release
	#	pushSeqCmd(dt, 'RIGHT_DDI_PB_08', 1) # BIT OSB
	#	pushSeqCmd(dt, 'RIGHT_DDI_PB_08', 0) # release
	#	pushSeqCmd(dt, 'RIGHT_DDI_PB_11', 1) # DISPLAYS OSB
	#	pushSeqCmd(dt, 'RIGHT_DDI_PB_11', 0) # release
	#	pushSeqCmd(dt, 'RIGHT_DDI_PB_11', 1) # HMD OSB
	#	pushSeqCmd(dt, 'RIGHT_DDI_PB_11', 0) # release
	#	pushSeqCmd(8, '', '', "HMD test complete")
	#	pushSeqCmd(dt, 'RIGHT_DDI_PB_10', 1) # STOP OSB
	#	pushSeqCmd(dt, 'RIGHT_DDI_PB_10', 0) # release
	#	pushSeqCmd(dt, 'RIGHT_DDI_PB_18', 1) # MENU OSB
	#	pushSeqCmd(dt, 'RIGHT_DDI_PB_18', 0) # release
	#	pushSeqCmd(dt, 'RIGHT_DDI_PB_18', 1) # MENU OSB
	#	pushSeqCmd(dt, 'RIGHT_DDI_PB_18', 0) # release
	#	pushSeqCmd(dt, 'RIGHT_DDI_PB_03', 1) # HMD OSB
	#	pushSeqCmd(dt, 'RIGHT_DDI_PB_03', 0) # release
	#	pushSeqCmd(dt, 'RIGHT_DDI_PB_20', 1) # ALIGN OSB
	#	pushSeqCmd(dt, 'RIGHT_DDI_PB_20', 0) # release
	#	pushSeqCmd(dt, 'scriptSpeech', 'Press and hold uncage to align.  Press and release uncage to go to next mode, use T D C to align.  Unbox align O S B when complete.')

	# SET BINGO FUEL - 3000 LBS
	pushSeqCmd(dt, 'IFEI_UP_BTN', 1)
	pushSeqCmd(4.25, 'IFEI_UP_BTN', 0) # Release after 4.25 seconds to get 3000 lbs.
	
	# DATALINK - Link 4 ON
	pushSeqCmd(dt, 'UFC_DL', 1) # UFC D/L button
	pushSeqCmd(dt, 'UFC_DL', 0) # release
	pushSeqCmd(dt, 'UFC_ONOFF', 1) # UFC ON/OFF button
	pushSeqCmd(1, 'UFC_ONOFF', 0) # release after 1 second
	# DATALINK - Link 16 ON
	pushSeqCmd(dt, 'UFC_DL', 1) # UFC D/L button, press again to go to the second D/L page
	pushSeqCmd(dt, 'UFC_DL', 0) # release
	pushSeqCmd(dt, 'UFC_ONOFF', 1) # UFC ON/OFF button
	pushSeqCmd(1, 'UFC_ONOFF', 0) # release after 1 second

	# NOTE Should be done after INS alignement is complete.
	# AMPCD GAIN - DOWN TO MIN FOR VR
	pushSeqCmd(dt, 'AMPCD_GAIN_SW', 0) # Down
	pushSeqCmd(3, 'AMPCD_GAIN_SW', 1) # Center after 3 seconds

	# MASTER ARM - ARM
	pushSeqCmd(dt, 'MASTER_ARM_SW', 1)
	
	return seq


def AirStart(config, dayStart = True, hmd = True):
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

	pushSeqCmd(0, '', '', "Running Air Start sequence")
	
	# Exterior light switch ... OFF
	pushSeqCmd(dt, 'THROTTLE_EXT_L_SW', 0) # 0 = OFF, 1 = ON
	# Other lights
	if dayStart:
		pushSeqCmd(dt, 'CONSOLES_DIMMER', int16())
		pushSeqCmd(dt, 'INST_PNL_DIMMER', int16())
	else:
		pushSeqCmd(dt, 'CONSOLES_DIMMER', int16(0.5))
		pushSeqCmd(dt, 'INST_PNL_DIMMER', int16(0.5))
	
	# All MFDs on
	if dayStart:
		pushSeqCmd(dt, 'AMPCD_BRT_CTL', int16())
	else:
		pushSeqCmd(dt, 'AMPCD_BRT_CTL', int16(0.5))
	
	# HUD, UFC, IFEI brightness
	if dayStart:
		pushSeqCmd(dt, 'HUD_SYM_BRT', int16())
		pushSeqCmd(dt, 'HUD_SYM_BRT_SELECT', 1) # 0 = NIGHT, 1 = DAY
		pushSeqCmd(dt, 'UFC_BRT', int16())
		pushSeqCmd(dt, 'IFEI', int16()) # IFEI brightness to max
	else:
		pushSeqCmd(dt, 'HUD_SYM_BRT', int16(0.5))
		pushSeqCmd(dt, 'HUD_SYM_BRT_SELECT', 0) # 0 = NIGHT, 1 = DAY
		pushSeqCmd(dt, 'UFC_BRT', int16(0.5))
		pushSeqCmd(dt, 'IFEI', 1000) # IFEI brightness to min

	# Radio volume
	pushSeqCmd(dt, 'UFC_COMM1_VOL', int16(0.8), 'COMM 1 vol - 80%')
	pushSeqCmd(dt, 'UFC_COMM2_VOL', int16(0.8), 'COMM 2 vol - 80%')
	
	# FIXME The engine monitor instrument doesn't pick up the cockpit lighting mode switch position unless it's set after the right engine starts.
	if dayStart:
		pushSeqCmd(dt, 'COCKKPIT_LIGHT_MODE_SW', 0) # NOTE misspelling 0 = DAY (default), 1 = NITE, 2 = NVG
	else:
		pushSeqCmd(dt, 'COCKKPIT_LIGHT_MODE_SW', 1) # NOTE misspelling 0 = DAY (default), 1 = NITE, 2 = NVG
	
	# HMD knob - ON
	if hmd:
		if dayStart:
			pushSeqCmd(dt, 'HMD_OFF_BRT', int16())
		else:
			pushSeqCmd(dt, 'HMD_OFF_BRT', int16(0.5))
	
	# RADAR ALTIMETER - ON, SET TO 50 FT
	maxRadAlt = int(int16() * 3 + 8194) # Just over 3 full turns of the knob from 0 to max.
	pushSeqCmd(dt, 'RADALT_HEIGHT', '-'+str(maxRadAlt)) # All the way off
	pushSeqCmd(dt, 'RADALT_HEIGHT', '+'+str(int16(0.28))) # Turn knob up 28% of one turn to get 50 ft.

	# HUD ALT SWITCH - RDR
	pushSeqCmd(dt, 'HUD_ALT_SW', 0)
	# IR COOL SWITCH - NORM
	pushSeqCmd(dt, 'IR_COOL_SW', 1)
	# DISPENSER SWITCH - ON
	pushSeqCmd(dt, 'CMSD_DISPENSE_SW', 1)
	# ECM - REC
	pushSeqCmd(dt, 'ECM_MODE_SW', 3)
	# RWR POWER - ON
	pushSeqCmd(dt, 'RWR_POWER_BTN', 1)

	# EW page...
	# Dispenser mode MAN 1
	pushSeqCmd(dt, 'RIGHT_DDI_PB_18', 1) # MENU OSB
	pushSeqCmd(dt, 'RIGHT_DDI_PB_18', 0) # release
	pushSeqCmd(dt, 'RIGHT_DDI_PB_17', 1) # EW OSB
	pushSeqCmd(dt, 'RIGHT_DDI_PB_17', 0) # release
	pushSeqCmd(dt, 'RIGHT_DDI_PB_08', 1) # ALE-47 OSB
	pushSeqCmd(dt, 'RIGHT_DDI_PB_08', 0) # release
	pushSeqCmd(dt, 'RIGHT_DDI_PB_19', 1) # MODE OSB
	pushSeqCmd(dt, 'RIGHT_DDI_PB_19', 0) # release
	
	# RWR show on SA page
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
	#pushSeqCmd(dt, 'RIGHT_DDI_PB_18', 1) # MENU OSB
	#pushSeqCmd(dt, 'RIGHT_DDI_PB_18', 0) # release
	#pushSeqCmd(dt, 'RIGHT_DDI_PB_18', 1) # MENU OSB
	#pushSeqCmd(dt, 'RIGHT_DDI_PB_18', 0) # release
	#pushSeqCmd(dt, 'RIGHT_DDI_PB_15', 1) # FCS OSB
	#pushSeqCmd(dt, 'RIGHT_DDI_PB_15', 0) # release

	# SET BINGO FUEL - 3000 LBS
	pushSeqCmd(dt, 'IFEI_UP_BTN', 1)
	pushSeqCmd(4.25, 'IFEI_UP_BTN', 0) # Release after 4.25 seconds to get 3000 lbs.
	
	#DATALINK - Link 4 ON
	pushSeqCmd(dt, 'UFC_DL', 1) # UFC D/L button
	pushSeqCmd(dt, 'UFC_DL', 0) # release
	pushSeqCmd(dt, 'UFC_ONOFF', 1) # UFC ON/OFF button
	pushSeqCmd(1, 'UFC_ONOFF', 0) # release after 1 second
	
	# AMPCD GAIN - DOWN TO MIN FOR VR
	# NOTE Should be done after INS alignement is complete.
	pushSeqCmd(dt, 'AMPCD_GAIN_SW', 0) # Down
	pushSeqCmd(3, 'AMPCD_GAIN_SW', 1) # Center after 3 seconds
	
	# Show local time in HUD
	# IMPORTANT If you are doing a CV alignment, this must be done either before starting alignment, or after alignment is complete and INS knob is set to IFA.  That is because when doing a CV alignment, PB 17 says MAN instead of TIMEUFC, and if pressed, it turns off the STD HDG.  We'll do this on the center MFD because it will already have the HSI on it for the alignment.
	pushSeqCmd(dt, 'AMPCD_PB_17', 1) # TIMEUFC OSB
	pushSeqCmd(dt, 'AMPCD_PB_17', 0) # release
	pushSeqCmd(dt, 'UFC_OS5', 1) # LTOD OSB
	pushSeqCmd(dt, 'UFC_OS5', 0) # release
	pushSeqCmd(dt, 'AMPCD_PB_17', 1) # TIMEUFC OSB
	pushSeqCmd(dt, 'AMPCD_PB_17', 0) # release
	
	# MASTER ARM - ARM
	pushSeqCmd(dt, 'MASTER_ARM_SW', 1)

	# EJECTION SEAT SAFE/ARM HANDLE - ARM
	pushSeqCmd(dt, 'EJECTION_SEAT_ARMED', 0)

	return seq


def Shutdown(config):
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
	
	pushSeqCmd(0, '', '', "Running Shutdown sequence")
	
	# EJECTION SEAT SAFE/ARM HANDLE - SAFE
	pushSeqCmd(dt, 'EJECTION_SEAT_ARMED', 1)

	# OBOGS CONTROL SWITCH - OFF
	pushSeqCmd(dt, 'OBOGS_SW', 0)

	# FLAP SWITCH - FULL
	pushSeqCmd(dt, 'FLAP_SW', 0)

	# T/O TRIM BUTTON - PRESS UNTIL TRIM ADVISORY DISPLAYED
	pushSeqCmd(dt, 'TO_TRIM_BTN', 1)
	pushSeqCmd(dt, 'TO_TRIM_BTN', 0)

	# PARK BRK HANDLE - ON
	pushSeqCmd(dt, 'EMERGENCY_PARKING_BRAKE_ROTATE', 1)
	pushSeqCmd(dt, 'EMERGENCY_PARKING_BRAKE_PULL', 0)
	
	# INS KNOB - OFF
	pushSeqCmd(dt, 'INS_SW', 0)

	# STANDBY ATTITUDE REFERENCE INDICATOR - CAGE
	pushSeqCmd(dt, 'SAI_CAGE', '1') # Pull knob.
	pushSeqCmd(dt, 'SAI_SET', '+100') # Rotate CW slightly to hold.

	# RADAR KNOB - OFF
	pushSeqCmd(dt, 'RADAR_SW', 0)

	#RADAR ALTIMETER - OFF
	maxRadAlt = int(int16() * 3 + 8194) # Just over 3 full turns of the knob from 0 to max.
	pushSeqCmd(dt, 'RADALT_HEIGHT', '-'+str(maxRadAlt)) # All the way off
	
	# HUD ALT SWITCH - BARO
	pushSeqCmd(dt, 'HUD_ALT_SW', 1)

	# IR COOL SWITCH - OFF
	pushSeqCmd(dt, 'IR_COOL_SW', 0)

	# DISPENSER SWITCH - OFF
	pushSeqCmd(dt, 'CMSD_DISPENSE_SW', 0)
	# ECM - OFF
	pushSeqCmd(dt, 'ECM_MODE_SW', 0)

	# CANOPY - OPEN
	pushSeqCmd(dt, 'CANOPY_SW', 2)
	pushSeqCmd(9, 'CANOPY_SW', 1, 'Canopy closed') # Turn off canopy switch 9 seconds later.

	# Left engine off
	pushSeqCmd(dt, 'scriptKeyboard', '{VK_LMENU down}{VK_END}{VK_LMENU up}', 'ATTENTION: You must remap Throttle (Left) - OFF to LAlt+End') # FIXME pyWinAuto doesn't support RAlt or RCtrl.

	# MFDs - OFF
	pushSeqCmd(dt, 'LEFT_DDI_BRT_SELECT', 0)
	pushSeqCmd(dt, 'RIGHT_DDI_BRT_SELECT', 0)
	pushSeqCmd(dt, 'AMPCD_BRT_CTL', 0)
	
	# HUD - OFF
	pushSeqCmd(dt, 'HUD_SYM_BRT', 0)
	pushSeqCmd(dt, 'HUD_SYM_BRT_SELECT', 1) # 0 = NIGHT, 1 = DAY

	# UFC BRIGHTNESS - OFF
	pushSeqCmd(dt, 'UFC_BRT', 0)

	# HMD knob - OFF
	pushSeqCmd(dt, 'HMD_OFF_BRT', 0)

	# Right engine off
	pushSeqCmd(dt, 'scriptKeyboard', '{VK_RSHIFT down}{VK_END}{VK_RSHIFT up}')
	
	# Exterior lights off
	pushSeqCmd(dt, 'FORMATION_DIMMER', 0)
	pushSeqCmd(dt, 'POSITION_DIMMER', 0)
	pushSeqCmd(dt, 'STROBE_SW', 0)
	pushSeqCmd(dt, 'LDG_TAXI_SW', 0)

	# Interior lights off
	pushSeqCmd(dt, 'COCKKPIT_LIGHT_MODE_SW', 0) # NOTE misspelling 0 = DAY (default), 1 = NITE, 2 = NVG
	pushSeqCmd(dt, 'CONSOLES_DIMMER', 0)
	pushSeqCmd(dt, 'INST_PNL_DIMMER', 0)
	pushSeqCmd(dt, 'FLOOD_DIMMER', 0)
	pushSeqCmd(dt, 'CHART_DIMMER', 0)

	pushSeqCmd(dt, 'BATTERY_SW', 1, 'BATT switch - OFF')

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

	# Pass in "N 36°21.0739', E 36°17.0249'" or "N 36 21 0739 E 36 17 0249, 77 m"
	# Returns ['N', '36', '21', '0739', 'E', '36', '17', '0249', '77', 'm']
	def ddmStringToList(ddm):
		ddm = re.sub(r"[°.',]", ' ', ddm) # Replace all delimiters with spaces.
		#print(ddm.split());quit()
		return ddm.split() # Then split the string on contiguous whitespace and we have the result.
	
	# Pass in "N 36°21'44.37\", E 36°17'14.99\"" or "N 36 21 44.37 E 36 17 14.99, 77 m"
	# Returns ['N', '36', '21', '44', '37', 'E', '36', '17', '14', '99', '77', 'm']
	def dmsStringToList(dms):
		dms = re.sub(r"[°'.\",]", ' ', dms) # Replace all delimiters with spaces.
		return dms.split() # Then split the string on contiguous whitespace and we have the result.

	# Presses the keys necessary to enter the waypoint.
	# Starting state: Go to HSI page, select desired waypoint, press DATA OSB, PRECISE boxed.
	def ddmInput(ddmList):
		# Select UFC OSB to prepare for data entry.
		pressRelease('RIGHT_DDI_PB_05') # UFC OSB
		
		# Select POSN for lat/long entry.
		pressRelease('UFC_OS1') # UFC POSN OSB
		
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

		# Enter the altitude.
		pressRelease(ufcKeys['OSB3'])
		# If units is 'm', select MTRS
		if ddmList[9] == 'm':
			pressRelease(ufcKeys['OSB2'])
		# Else select FEET.
		else:
			pressRelease(ufcKeys['OSB1'])
		# Altitude
		for key in ddmList[8]:
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
	for i in range(10):
		pressRelease('RIGHT_DDI_PB_12') # Up Arrow OSB, increments waypoint number
	
	# Waypoints will be entered starting with the first one as waypoint 10.
	waypoints = [
		"N 37°00.0122', E 35°25.0565', 58 m", # Incirlik
		"N 36°21.0739', E 36°17.0249', 77 m", # Hatay
		"N 35°43.9384', E 37°06.2477', 250 m", # Abu al-Duhur
		"N 35°24.1140', E 35°57.0247', 29 m", # Bassel Al-Assad
	]

	for waypoint in waypoints:	
		# Convert the wp string into a list with all its elements.
		ddmList = ddmStringToList(waypoint)
		# Enter the waypoint into the HSI.
		ddmInput(ddmList)
		# Select next waypoint.
		pressRelease('RIGHT_DDI_PB_12') # Up Arrow OSB, increments waypoint number

	pressRelease('RIGHT_DDI_PB_10') # HSI OSB

	return seq
