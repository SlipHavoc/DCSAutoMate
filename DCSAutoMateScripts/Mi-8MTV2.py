# Return a Dictionary of script titles and their corresponding function names.  This is a list of scripts that users will be selecting from.  The module may have other utility functions that will not be run directly by the users.
def getScriptFunctions():
	return {
		'Cold Start, day, unarmed': 'ColdStartDayUnarmed',
		'Cold Start, night, unarmed': 'ColdStartNightUnarmed',
		'Cold Start, day, armed': 'ColdStartDayArmed',
		'Cold Start, night, armed': 'ColdStartNightArmed',
		#'Test': 'Test',
	}

def getInfo():
	return """ATTENTION: You must remap "Throttle Levers - UP" to LCtrl+Home and "Throttle Levers - DOWN" to LCtrl+End.  This is because pyWinAuto doesn't support RAlt or RCtrl."""

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
	
	# Test code here...

	return seq

def ColdStartDayUnarmed(config):
	return ColdStart(config, dayStart = True, armed = False)

def ColdStartNightUnarmed(config):
	return ColdStart(config, dayStart = False, armed = False)

def ColdStartDayArmed(config):
	return ColdStart(config, dayStart = True, armed = True)

def ColdStartNightArmed(config):
	return ColdStart(config, dayStart = False, armed = True)

def ColdStart(config, dayStart = True, armed = False):
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

	pushSeqCmd(0, '', '', "Running Cold Start sequence")
	pushSeqCmd(dt, 'scriptSpeech', "Warning, uses non standard key bindings.")
	pushSeqCmd(dt, '', '', 'Set collective full down.')
	pushSeqCmd(dt, 'scriptSpeech', 'Set collective full down.')

	#pushSeqCmd(dt, '', '', "RADIO/ICS SWITCH - ICS (allows rearming)")
	pushSeqCmd(dt, 'SPU7_L_ICS', 1)
	
	#pushSeqCmd(dt, '', '', "LEFT COCKPIT WINDOW - CLOSE")
	pushSeqCmd(dt, 'BLST_L_OPEN', 0)

	# Power levers and throttle
	#pushSeqCmd(dt, '', '', "ENGINE POWER LEVERS - AUTO")
	# Throttles down twice first to make sure they're at min.
	pushSeqCmd(dt, 'scriptKeyboard', '{VK_LCONTROL down}{END down}{END up}{VK_LCONTROL up}')
	pushSeqCmd(dt, 'scriptKeyboard', '{VK_LCONTROL down}{END down}{END up}{VK_LCONTROL up}')
	# Then throttles up once to set to auto.
	pushSeqCmd(dt, 'scriptKeyboard', '{VK_LCONTROL down}{HOME down}{HOME up}{VK_LCONTROL up}')
	
	# Twist grip to min (DECR)
	#pushSeqCmd(dt, '', '', "THROTTLE - MINIMUM (LEFT)")
	pushSeqCmd(dt, 'scriptKeyboard', '{PGDN down}')
	pushSeqCmd(2, 'scriptKeyboard', '{PGDN up}') # Hold down for 2 seconds
	# Collective full down.
	#pushSeqCmd(dt, '', '', "COLLECTIVE - FULL DOWN")
	pushSeqCmd(dt, 'scriptKeyboard', '{VK_SUBTRACT down}')
	pushSeqCmd(2, 'scriptKeyboard', '{VK_SUBTRACT up}') # Hold down for 2 seconds
	
	#pushSeqCmd(dt, '', '', "ROTOR BRAKE - OFF")
	pushSeqCmd(dt, 'ENG_RTR_BRAKE', 0)

	#pushSeqCmd(dt, '', '', "BATTERY 1 - ON")
	pushSeqCmd(dt, 'BATT1_SWITCH', 1)
	#pushSeqCmd(dt, '', '', "BATTERY 2 - ON")
	pushSeqCmd(dt, 'BATT2_SWITCH', 1)
	#pushSeqCmd(dt, '', '', "115V INVERTER - AUTO (down)")
	pushSeqCmd(dt, 'INV_115V_SWITCH', 0)

	if not dayStart:
		# Dome lights.
		pushSeqCmd(dt, 'LGHT_L_CEIL', 2) # 0 = White, 1 = Off, 2 = Red
		pushSeqCmd(dt, 'LGHT_R_CEIL', 2) # 0 = White, 1 = Off, 2 = Red
		# Left red light knobs.
		pushSeqCmd(dt, 'L_RED_LGHT_1', int16())
		pushSeqCmd(dt, 'L_RED_LGHT_2', int16())
		# Right red light knobs.
		pushSeqCmd(dt, 'R_RED_LGHT_1', int16())
		pushSeqCmd(dt, 'R_RED_LGHT_2', int16())
		# Center red light knobs.
		pushSeqCmd(dt, 'C_RED_LGHT_1', int16())
		pushSeqCmd(dt, 'C_RED_LGHT_2', int16())
		# 5.5V lights (radar altimeter and other instruments)
		# Switch
		pushSeqCmd(dt, 'LGHT_5_5V', 1)
		# Brightness
		pushSeqCmd(dt, 'LGHT_55V', int16())
		# ANNUC switch - NIGHT
		pushSeqCmd(dt, 'SAS_TRANS', 1)


	#pushSeqCmd(dt, '', '', "DC VOLTMETER SELECTOR - BATT BUS")
	pushSeqCmd(dt, 'DC_VOLT_SEL', 4)

	#pushSeqCmd(dt, '', '', "CIRCUIT BREAKER GROUP 4 - ON")
	pushSeqCmd(dt, 'AZS_GRP_BTN4', 1)
	pushSeqCmd(dt, 'AZS_GRP_BTN4', 0)

	#pushSeqCmd(dt, '', '', "CIRCUIT BREAKER GROUP 5 - ON")
	pushSeqCmd(dt, 'AZS_GRP_BTN5', 1)
	pushSeqCmd(dt, 'AZS_GRP_BTN5', 0)

	#pushSeqCmd(dt, '', '', "CIRCUIT BREAKER GROUP 6 - ON")
	pushSeqCmd(dt, 'AZS_GRP_BTN6', 1)
	pushSeqCmd(dt, 'AZS_GRP_BTN6', 0)

	#pushSeqCmd(dt, '', '', "CIRCUIT BREAKER GROUP 7 - ON")
	pushSeqCmd(dt, 'AZS_GRP_BTN7', 1)
	pushSeqCmd(dt, 'AZS_GRP_BTN7', 0)

	#pushSeqCmd(dt, '', '', "CIRCUIT BREAKER GROUP 8 - ON")
	pushSeqCmd(dt, 'AZS_GRP_BTN8', 1)
	pushSeqCmd(dt, 'AZS_GRP_BTN8', 0)

	#pushSeqCmd(dt, '', '', "CIRCUIT BREAKER GROUP 9 - ON")
	pushSeqCmd(dt, 'AZS_GRP_BTN9', 1)
	pushSeqCmd(dt, 'AZS_GRP_BTN9', 0)

	#pushSeqCmd(dt, '', '', "FIRE EXTINGUISHER - ON")
	pushSeqCmd(dt, 'DCHARGE_FIRE_DETECT_TEST', 1)

	#pushSeqCmd(dt, '', '', "FUEL METER - TOTAL")
	pushSeqCmd(dt, 'FUEL_METER_SWITCH', 1)

	#pushSeqCmd(dt, '', '', "LEFT SHUTOFF VALVE - ON")
	pushSeqCmd(dt, 'FUEL_LEFT_COVER', 1) # switch cover
	pushSeqCmd(dt, 'FUEL_LEFT_SHUTOFF', 1) # switch
	pushSeqCmd(dt, 'FUEL_LEFT_COVER', 0) # switch cover

	#pushSeqCmd(dt, '', '', "RIGHT SHUTOFF VALVE - ON")
	pushSeqCmd(dt, 'FUEL_RIGHT_COVER', 1) # switch cover
	pushSeqCmd(dt, 'FUEL_RIGTH_SHUTOFF', 1) # switch # NOTE Spelling error in command, "FUEL_RIGTH_SHUTOFF" is the correct spelling for the command.
	pushSeqCmd(dt, 'FUEL_RIGHT_COVER', 0) # switch cover

	#pushSeqCmd(dt, '', '', "SERVICE TANK PUMP - ON")
	pushSeqCmd(dt, 'FUEL_FEED_PUMP', 1)
	#pushSeqCmd(dt, '', '', "LEFT TANK PUMP - ON")
	pushSeqCmd(dt, 'FUEL_LEFT_PUMP', 1)
	#pushSeqCmd(dt, '', '', "RIGHT TANK PUMP - ON")
	pushSeqCmd(dt, 'FUEL_RIGTH_PUMP', 1) # NOTE Spelling error in command, "FUEL_RIGTH_PUMP" is the correct spelling for the command.
	
	# R-828 radio
	#pushSeqCmd(dt, '', '', "R-828 RADIO POWER - ON")
	pushSeqCmd(dt, 'R828_PWR', 1)

	# APU
	#pushSeqCmd(dt, '', '', "STARTING APU (28 SEC)")
	#pushSeqCmd(dt, '', '', "APU START MODE - START")
	pushSeqCmd(dt, 'APU_START_MODE', 2)
	#pushSeqCmd(dt, '', '', "APU START BUTTON - HOLD FOR 3 SEC")
	pushSeqCmd(dt, 'APU_START', 1) # Press
	pushSeqCmd(3, 'APU_START', 0) # Release after 3 seconds
	pushSeqCmd(20, '', '', 'APU STARTED')

	# Left engine
	#pushSeqCmd(dt, '', '', "STARTING LEFT ENGINE (61 SEC)")
	#pushSeqCmd(dt, '', '', "ENGINE START MODE - START")
	pushSeqCmd(dt, 'ENG_START_MODE', 2)
	#pushSeqCmd(dt, '', '', "ENGINE SELECTOR SWITCH - LEFT")
	pushSeqCmd(dt, 'ENG_SEL', 0)
	#pushSeqCmd(dt, '', '', "ENGINE START BUTTON - HOLD FOR 3 SEC")
	pushSeqCmd(dt, 'ENG_START', 1) # Press
	pushSeqCmd(3, 'ENG_START', 0) # Release after 3 seconds
	#pushSeqCmd(dt, '', '', "LEFT ENGINE FUEL SHUTOFF LEVER - OPEN")
	pushSeqCmd(dt, 'ENG_LEFT_STOP', 1)
	pushSeqCmd(55, '', '', "LEFT ENGINE - STARTED")

	# Right engine
	#pushSeqCmd(dt, '', '', "STARTING RIGHT ENGINE (61 SEC)")
	#pushSeqCmd(dt, '', '', "ENGINE SELECTOR SWITCH - RIGHT")
	pushSeqCmd(dt, 'ENG_SEL', 2)
	#pushSeqCmd(dt, '', '', "ENGINE START BUTTON - HOLD FOR 3 SEC")
	pushSeqCmd(dt, 'ENG_START', 1) # Press
	pushSeqCmd(3, 'ENG_START', 0) # Release after 3 seconds
	#pushSeqCmd(dt, '', '', "RIGHT ENGINE FUEL SHUTOFF LEVER - OPEN")
	pushSeqCmd(dt, 'ENG_RIGHT_STOP', 1)
	pushSeqCmd(55, '', '', "RIGHT ENGINE - STARTED")

	# Engines started, selector to neutral
	#pushSeqCmd(dt, '', '', "ENGINE SELECTOR SWITCH - CENTER")
	pushSeqCmd(dt, 'ENG_SEL', 1)
	
	# Twist grip to max (INCR)
	#pushSeqCmd(dt, '', '', "THROTTLE - MAXIMUM (RIGHT)")
	pushSeqCmd(dt, 'scriptKeyboard', '{PGUP down}')
	pushSeqCmd(2, 'scriptKeyboard', '{PGUP up}') # Hold down for 2 seconds
	#pushSeqCmd(dt, '', '', "ALLOW RPM TO STABILIZE (10 SEC)")
	pushSeqCmd(10, '', '', "RPM STABILIZED")

	# Generators and Rectifiers
	#pushSeqCmd(dt, '', '', "TURN ON GENERATORS")
	#pushSeqCmd(dt, '', '', "GENERATOR 1 - ON")
	pushSeqCmd(dt, 'GEN1_SWITCH', 1)
	#pushSeqCmd(dt, '', '', "GENERATOR 2 - ON")
	pushSeqCmd(dt, 'GEN2_SWITCH', 1)
	#pushSeqCmd(dt, '', '', "RECTIFIER 1 - ON")
	pushSeqCmd(dt, 'RECT1_SWITCH', 1)
	#pushSeqCmd(dt, '', '', "RECTIFIER 2 - ON")
	pushSeqCmd(dt, 'RECT2_SWITCH', 1)
	#pushSeqCmd(dt, '', '', "RECTIFIER 3 - ON")
	pushSeqCmd(dt, 'RECT3_SWITCH', 1)
	#pushSeqCmd(dt, '', '', "DC VOLTMETER SELECTOR - RECT BUS")
	pushSeqCmd(dt, 'DC_VOLT_SEL', 5)
	#pushSeqCmd(dt, '', '', "AC VOLTMETER SELECTOR - 115V")
	pushSeqCmd(dt, 'AC_VOLT_SEL', 10)

	#pushSeqCmd(dt, '', '', "36V INVERTER - AUTO (down)")
	pushSeqCmd(dt, 'INV_36V_SWITCH', 0)

	#pushSeqCmd(dt, '', '', "APU STOP")
	pushSeqCmd(dt, 'APU_STOP', 1) # Press
	pushSeqCmd(dt, 'APU_STOP', 0) # Release

	#Pilot's triangular panel
	#pushSeqCmd(dt, '', '', "LEFT ATT IND - ON")
	pushSeqCmd(dt, 'ADI_L_ATT_PWR', 1)
	#pushSeqCmd(dt, '', '', "GYRO CUT OUT - ON")
	pushSeqCmd(dt, 'ADI_VK53_PWR', 1)
	#pushSeqCmd(dt, '', '', "PITCH LIM SYS - ON")
	pushSeqCmd(dt, 'SPUU52_PWR', 1)
	#pushSeqCmd(dt, '', '', "AUDIO WARN - ON")
	pushSeqCmd(dt, 'RI65_PWR', 1)

	#Copilot's triangular panel
	#pushSeqCmd(dt, '', '', "DOPP - ON")
	pushSeqCmd(dt, 'DPL_PWR', 1)
	#pushSeqCmd(dt, '', '', "COMP SYS - ON")
	pushSeqCmd(dt, 'GMC_PWR', 1)
	#pushSeqCmd(dt, '', '', "RIGHT ATT IND - ON")
	pushSeqCmd(dt, 'ADI_R_ATT_PWR', 1)
	#pushSeqCmd(dt, '', '', "COMM RADIO - ON")
	pushSeqCmd(dt, 'JAD1A_PWR', 1)

	# Other
	#pushSeqCmd(dt, '', '', "RADAR ALTIMETER - ON")
	pushSeqCmd(dt, 'RADAR_ALT_PWR', 1)
	#pushSeqCmd(dt, '', '', "FLASHER - ON")
	pushSeqCmd(dt, 'SAS_FLASH', 1)
	#pushSeqCmd(dt, '', '', "AUTOPILOT ROLL/PITCH CHANNEL - ON")
	pushSeqCmd(dt, 'AUTOPILOT_PITCH_ROLL_ON', 1) # Press
	pushSeqCmd(dt, 'AUTOPILOT_PITCH_ROLL_ON', 0) # Release

	# UV-26 countermeasures system
	#pushSeqCmd(dt, '', '', "UV-26 POWER - ON")
	pushSeqCmd(dt, 'CMD_PWR', 1)
	#pushSeqCmd(dt, '', '', "UV-26 DISPENSER - BOTH")
	pushSeqCmd(dt, 'CMD_FLARE_SEL', 1)
	#pushSeqCmd(dt, '', '', "UV-26 RESET TO DEFAULT PROGRAM (110)")
	pushSeqCmd(dt, 'UV26_RST', 1) # Press
	pushSeqCmd(dt, 'UV26_RST', 0) # Release
	# Set "411" (4 flares, 1 second apart)...
	# Press "Num Of Sequences" button 3x.
	for i in range(3): # Press and release 3 times
		pushSeqCmd(dt, 'UV26_SEQ', 1) # Press
		pushSeqCmd(dt, 'UV26_SEQ', 0) # Release
	# "Num In Sequence" is already set to 1.
	#pushSeqCmd(dt, 'CMD_FLARE_NUM', 1) # Press
	#pushSeqCmd(dt, 'CMD_FLARE_NUM', 0) # Release
	# Press "Dispense Interval" button 1x.
	pushSeqCmd(dt, 'CMD_INTERVAL', 1) # Press
	pushSeqCmd(dt, 'CMD_INTERVAL', 0) # Release

	# Fans
	#pushSeqCmd(dt, '', '', "PILOT'S FAN - ON")
	pushSeqCmd(dt, 'CPIT_AIR_L_FAN', 1)
	#pushSeqCmd(dt, '', '', "COPILOT'S FAN - ON")
	pushSeqCmd(dt, 'CPIT_AIR_R_FAN', 1)

	# Reset G-meter
	pushSeqCmd(dt, 'ACC_RST', 1) # Press
	pushSeqCmd(dt, 'ACC_RST', 0) # Release

	if armed:
		# CB Group 1 - ON
		pushSeqCmd(dt, 'AZS_GRP_BTN1', 1)
		pushSeqCmd(dt, 'AZS_GRP_BTN1', 0)
		# CB Group 2 - ON
		pushSeqCmd(dt, 'AZS_GRP_BTN2', 1)
		pushSeqCmd(dt, 'AZS_GRP_BTN2', 0)
		# CB Group 3 - ON
		pushSeqCmd(dt, 'AZS_GRP_BTN3', 1)
		pushSeqCmd(dt, 'AZS_GRP_BTN3', 0)
		# Main Switch - ON
		pushSeqCmd(dt, 'WPN_RS_GUV_SEL', 1)
		# Master Arm - ON
		pushSeqCmd(dt, 'WPN_ARM', 1)
		
		# Arm rocket systems...
		# UPK/PKT/RS switch - RS
		pushSeqCmd(dt, 'WPN_SEL', 0)
		# Push and hold FIRE TEST UNIT ARM button for 4 seconds.
		pushSeqCmd(dt, 'WPN_PUS_ARM', 1)
		pushSeqCmd(4, 'WPN_PUS_ARM', 0) # Release after 4 seconds.
		# UPK/PKT/RS switch - PKT (default)
		pushSeqCmd(dt, 'WPN_SEL', 1)

		# Set sight depression to red index marker.
		pushSeqCmd(dt, 'SGHT_KNOB', 17427)

	#pushSeqCmd(dt, '', '', "Manual steps remaining:")
	#pushSeqCmd(dt, '', '', "Lights ... As needed")
	#pushSeqCmd(dt, '', '', "Radios ... As needed")
	#pushSeqCmd(dt, '', '', "Navigation ... As needed")
	#pushSeqCmd(dt, '', '', "Altimeter ... Set to match QFE (airfield elevation) or QNH (sea level altitude) as desired")
	pushSeqCmd(dt, 'scriptSpeech', "Manual steps remaining: Set lights.  Tune radios.  Set doppler navigation.  Set altimeter to Q F E or Q N H.")

	return seq
