# Return a Dictionary of script data.  The 'scripts' key is a list of scripts that users will be selecting from.  Each script has an associated 'function', which is the name of the function in this file that will be called to generate the command sequence, and a dictionary of 'vars' that the user will be prompted to choose from before running the script, and will be passed into the sequence generating function.
def getScriptData():
	return {
		'scripts': [
			{
				'name': 'Cold Start',
				'function': 'ColdStart',
				'vars': {
					'Time': ['Day', 'Night'],
					'Weapons': ['Armed', 'Unarmed'],
				},
			},
			{
				'name': 'Hot Start',
				'function': 'HotStart',
				'vars': {
					'Time': ['Day', 'Night'],
					'Weapons': ['Armed', 'Unarmed'],
				},
			},
			{
				'name': 'Shutdown',
				'function': 'Shutdown',
				'vars': {},
			},
			#{
			#	'name': 'Test',
			#	'function': 'Test',
			#	'vars': {
			#		'Time': ['Day', 'Night'],
			#		'Weapons': ['Armed', 'Unarmed'],
			#	},
			#},
		],
	}

def getInfo():
	return ''

# Returns 0-65535 scaled by multiple (0-1), eg for 50% call int16(0.5)
def int16(mult = 1):
	int16 = 65535
	return int(mult * int16)

def Test(config, vars):
	seq = []
	seqTime = 0
	dt = 0.3

	def pushSeqCmd(dt, cmd, *args, **kwargs):
		nonlocal seq, seqTime

		if len(args):
			seq.append({
				'time': round(dt, 2),
				'cmd': cmd,
				'arg': args[0],
				'msg': args[1] if len(args) > 1 else '',
			})
		else:
			step = {
				'time': round(dt, 2),
				'cmd': cmd,
			}
			for key in kwargs:
				step[key] = kwargs[key]
			seq.append(step)

	# Test code here...

	return seq


def ColdStart(config, vars):
	seq = []
	seqTime = 0
	dt = 0.3

	def pushSeqCmd(dt, cmd, *args, **kwargs):
		nonlocal seq, seqTime

		if len(args):
			seq.append({
				'time': round(dt, 2),
				'cmd': cmd,
				'arg': args[0],
				'msg': args[1] if len(args) > 1 else '',
			})
		else:
			step = {
				'time': round(dt, 2),
				'cmd': cmd,
			}
			for key in kwargs:
				step[key] = kwargs[key]
			seq.append(step)

	pushSeqCmd(0, '', '', "Running Cold Start sequence")
	pushSeqCmd(dt, '', '', 'Set collective full down.')
	pushSeqCmd(dt, 'scriptSpeech', 'Set collective full down.')

	# RADIO/ICS SWITCH - ICS (allows rearming)
	pushSeqCmd(dt, 'SPU7_L_ICS', 1)

	# LEFT COCKPIT WINDOW - CLOSE
	pushSeqCmd(dt, 'BLST_L_OPEN', 1)

	# Power levers and throttle
	# ENGINE POWER LEVERS - AUTO
	# Throttles down twice first to make sure they're at min.
	pushSeqCmd(dt, 'scriptKeyboard', 'RCtrl down')
	pushSeqCmd(dt, 'scriptKeyboard', 'end')
	pushSeqCmd(dt, 'scriptKeyboard', 'end')
	pushSeqCmd(dt, 'scriptKeyboard', 'RCtrl up')
	# Then throttles up once to set to auto.
	pushSeqCmd(dt, 'scriptKeyboard', 'RCtrl down')
	pushSeqCmd(dt, 'scriptKeyboard', 'home')
	pushSeqCmd(dt, 'scriptKeyboard', 'RCtrl up')

	# Twist grip to min (DECR)
	# THROTTLE - MINIMUM (LEFT)
	pushSeqCmd(dt, 'scriptKeyboard', 'pgdn down')
	pushSeqCmd(2, 'scriptKeyboard', 'pgdn up') # Hold down for 2 seconds
	# Collective full down.
	# COLLECTIVE - FULL DOWN
	pushSeqCmd(dt, 'scriptKeyboard', 'subtract down') # Numpad -
	pushSeqCmd(2, 'scriptKeyboard', 'subtract up') # Hold down for 2 seconds

	# ROTOR BRAKE - OFF
	pushSeqCmd(dt, 'ENG_RTR_BRAKE', 0)

	# BATTERY 1 - ON
	pushSeqCmd(dt, 'BATT1_SWITCH', 1)
	# BATTERY 2 - ON
	pushSeqCmd(dt, 'BATT2_SWITCH', 1)
	# 115V INVERTER - AUTO (down)
	pushSeqCmd(dt, 'INV_115V_SWITCH', 0)

	if vars.get('Time') != 'Day':
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
		# Gunsight brightness
		pushSeqCmd(dt, 'SGT_BRIGHT', int16(0.2))

	# DC VOLTMETER SELECTOR - BATT BUS
	pushSeqCmd(dt, 'DC_VOLT_SEL', 4)

	# CIRCUIT BREAKER GROUP 4 - ON
	pushSeqCmd(dt, 'AZS_GRP_BTN4', 1)
	pushSeqCmd(dt, 'AZS_GRP_BTN4', 0)

	# CIRCUIT BREAKER GROUP 5 - ON
	pushSeqCmd(dt, 'AZS_GRP_BTN5', 1)
	pushSeqCmd(dt, 'AZS_GRP_BTN5', 0)

	# CIRCUIT BREAKER GROUP 6 - ON
	pushSeqCmd(dt, 'AZS_GRP_BTN6', 1)
	pushSeqCmd(dt, 'AZS_GRP_BTN6', 0)

	# CIRCUIT BREAKER GROUP 7 - ON
	pushSeqCmd(dt, 'AZS_GRP_BTN7', 1)
	pushSeqCmd(dt, 'AZS_GRP_BTN7', 0)

	# CIRCUIT BREAKER GROUP 8 - ON
	pushSeqCmd(dt, 'AZS_GRP_BTN8', 1)
	pushSeqCmd(dt, 'AZS_GRP_BTN8', 0)

	# CIRCUIT BREAKER GROUP 9 - ON
	pushSeqCmd(dt, 'AZS_GRP_BTN9', 1)
	pushSeqCmd(dt, 'AZS_GRP_BTN9', 0)

	# FIRE EXTINGUISHER - ON
	pushSeqCmd(dt, 'DCHARGE_FIRE_DETECT_TEST', 1)

	# FUEL METER - TOTAL
	pushSeqCmd(dt, 'FUEL_METER_SWITCH', 1)

	# LEFT SHUTOFF VALVE - ON
	pushSeqCmd(dt, 'FUEL_LEFT_COVER', 1) # switch cover
	pushSeqCmd(dt, 'FUEL_LEFT_SHUTOFF', 1) # switch
	pushSeqCmd(dt, 'FUEL_LEFT_COVER', 0) # switch cover

	# RIGHT SHUTOFF VALVE - ON
	pushSeqCmd(dt, 'FUEL_RIGHT_COVER', 1) # switch cover
	pushSeqCmd(dt, 'FUEL_RIGTH_SHUTOFF', 1) # switch # NOTE Spelling error in command, "FUEL_RIGTH_SHUTOFF" is the correct spelling for the command.
	pushSeqCmd(dt, 'FUEL_RIGHT_COVER', 0) # switch cover

	# SERVICE TANK PUMP - ON
	pushSeqCmd(dt, 'FUEL_FEED_PUMP', 1)
	# LEFT TANK PUMP - ON
	pushSeqCmd(dt, 'FUEL_LEFT_PUMP', 1)
	# RIGHT TANK PUMP - ON
	pushSeqCmd(dt, 'FUEL_RIGTH_PUMP', 1) # NOTE Spelling error in command, "FUEL_RIGTH_PUMP" is the correct spelling for the command.

	# R-828 radio
	# R-828 RADIO POWER - ON
	pushSeqCmd(dt, 'R828_PWR', 1)

	# APU
	# STARTING APU (28 SEC)
	# APU START MODE - START
	pushSeqCmd(dt, 'APU_START_MODE', 2)
	# APU START BUTTON - HOLD FOR 3 SEC
	pushSeqCmd(dt, 'APU_START', 1) # Press
	pushSeqCmd(3, 'APU_START', 0) # Release after 3 seconds
	pushSeqCmd(20, '', '', 'APU STARTED')

	# Left engine
	# STARTING LEFT ENGINE (61 SEC)
	# ENGINE START MODE - START
	pushSeqCmd(dt, 'ENG_START_MODE', 2)
	# ENGINE SELECTOR SWITCH - LEFT
	pushSeqCmd(dt, 'ENG_SEL', 0)
	# ENGINE START BUTTON - HOLD FOR 3 SEC
	pushSeqCmd(dt, 'ENG_START', 1) # Press
	pushSeqCmd(3, 'ENG_START', 0) # Release after 3 seconds
	# LEFT ENGINE FUEL SHUTOFF LEVER - OPEN
	pushSeqCmd(dt, 'ENG_LEFT_STOP', 1)
	pushSeqCmd(55, '', '', "LEFT ENGINE - STARTED")

	# Right engine
	# STARTING RIGHT ENGINE (61 SEC)
	# ENGINE SELECTOR SWITCH - RIGHT
	pushSeqCmd(dt, 'ENG_SEL', 2)
	# ENGINE START BUTTON - HOLD FOR 3 SEC
	pushSeqCmd(dt, 'ENG_START', 1) # Press
	pushSeqCmd(3, 'ENG_START', 0) # Release after 3 seconds
	# RIGHT ENGINE FUEL SHUTOFF LEVER - OPEN
	pushSeqCmd(dt, 'ENG_RIGHT_STOP', 1)
	pushSeqCmd(55, '', '', "RIGHT ENGINE - STARTED")

	# Engines started, selector to neutral
	# ENGINE SELECTOR SWITCH - CENTER
	pushSeqCmd(dt, 'ENG_SEL', 1)

	# Twist grip to max (INCR)
	# THROTTLE - MAXIMUM (RIGHT)
	pushSeqCmd(dt, 'scriptKeyboard', 'pgup down')
	pushSeqCmd(2, 'scriptKeyboard', 'pgup up') # Hold down for 2 seconds
	# ALLOW RPM TO STABILIZE (10 SEC)
	pushSeqCmd(10, '', '', "RPM STABILIZED")

	# Generators and Rectifiers
	# TURN ON GENERATORS
	# GENERATOR 1 - ON
	pushSeqCmd(dt, 'GEN1_SWITCH', 1)
	# GENERATOR 2 - ON
	pushSeqCmd(dt, 'GEN2_SWITCH', 1)
	# RECTIFIER 1 - ON
	pushSeqCmd(dt, 'RECT1_SWITCH', 1)
	# RECTIFIER 2 - ON
	pushSeqCmd(dt, 'RECT2_SWITCH', 1)
	# RECTIFIER 3 - ON
	pushSeqCmd(dt, 'RECT3_SWITCH', 1)
	# DC VOLTMETER SELECTOR - RECT BUS
	pushSeqCmd(dt, 'DC_VOLT_SEL', 5)
	# AC VOLTMETER SELECTOR - 115V
	pushSeqCmd(dt, 'AC_VOLT_SEL', 10)

	# 36V INVERTER - AUTO (down)
	pushSeqCmd(dt, 'INV_36V_SWITCH', 0)

	# APU STOP
	pushSeqCmd(dt, 'APU_STOP', 1) # Press
	pushSeqCmd(dt, 'APU_STOP', 0) # Release

	# Pilot's triangular panel
	# LEFT ATT IND - ON
	pushSeqCmd(dt, 'ADI_L_ATT_PWR', 1)
	# GYRO CUT OUT - ON
	pushSeqCmd(dt, 'ADI_VK53_PWR', 1)
	# PITCH LIM SYS - ON
	pushSeqCmd(dt, 'SPUU52_PWR', 1)
	# AUDIO WARN - ON
	pushSeqCmd(dt, 'RI65_PWR', 1)

	# Copilot's triangular panel
	# DOPP - ON
	pushSeqCmd(dt, 'DPL_PWR', 1)
	# COMP SYS - ON
	pushSeqCmd(dt, 'GMC_PWR', 1)
	# RIGHT ATT IND - ON
	pushSeqCmd(dt, 'ADI_R_ATT_PWR', 1)
	# COMM RADIO - ON
	pushSeqCmd(dt, 'JAD1A_PWR', 1)

	# Other
	# RADAR ALTIMETER - ON
	pushSeqCmd(dt, 'RADAR_ALT_PWR', 1)
	# FLASHER - ON
	pushSeqCmd(dt, 'SAS_FLASH', 1)
	# AUTOPILOT ROLL/PITCH CHANNEL - ON
	pushSeqCmd(dt, 'AUTOPILOT_PITCH_ROLL_ON', 1) # Press
	pushSeqCmd(dt, 'AUTOPILOT_PITCH_ROLL_ON', 0) # Release

	# UV-26 countermeasures system
	# UV-26 POWER - ON
	pushSeqCmd(dt, 'CMD_PWR', 1)
	# UV-26 DISPENSER - BOTH
	pushSeqCmd(dt, 'CMD_FLARE_SEL', 1)
	# UV-26 RESET TO DEFAULT PROGRAM (110)
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
	# PILOT'S FAN - ON
	pushSeqCmd(dt, 'CPIT_AIR_L_FAN', 1)
	# COPILOT'S FAN - ON
	pushSeqCmd(dt, 'CPIT_AIR_R_FAN', 1)

	# Reset G-meter
	pushSeqCmd(dt, 'ACC_RST', 1) # Press
	pushSeqCmd(dt, 'ACC_RST', 0) # Release

	if vars.get('Weapons') == 'Armed':
		pushSeqCmd(dt, 'scriptSpeech', "Setting up weapon systems.")
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

	pushSeqCmd(dt, 'scriptSpeech', "Manual steps remaining: Set lights.  Tune radios.  Set doppler navigation.  Set altimeter to Q F E or Q N H.")

	return seq


def HotStart(config, vars):
	seq = []
	seqTime = 0
	dt = 0.3

	def pushSeqCmd(dt, cmd, *args, **kwargs):
		nonlocal seq, seqTime

		if len(args):
			seq.append({
				'time': round(dt, 2),
				'cmd': cmd,
				'arg': args[0],
				'msg': args[1] if len(args) > 1 else '',
			})
		else:
			step = {
				'time': round(dt, 2),
				'cmd': cmd,
			}
			for key in kwargs:
				step[key] = kwargs[key]
			seq.append(step)

	pushSeqCmd(0, '', '', "Running Hot Start sequence")

	# RADIO/ICS SWITCH - ICS (allows rearming)
	pushSeqCmd(dt, 'SPU7_L_ICS', 1)

	# Formation lights - Off
	pushSeqCmd(dt, 'LGHT_FRM', 1)

	# Anti-collision/strobe light - Off
	pushSeqCmd(dt, 'LGHT_STROBE', 0)

	# Blade tip lights - Off
	pushSeqCmd(dt, 'LGHT_TIP', 0)

	# Nav (ANO??) lights - Off
	pushSeqCmd(dt, 'LGHT_ANO', 1)

	if vars.get('Time') != 'Day':
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
		# Gunsight brightness
		pushSeqCmd(dt, 'SGT_BRIGHT', int16(0.2))

	# FUEL METER - TOTAL
	pushSeqCmd(dt, 'FUEL_METER_SWITCH', 1)

	# UV-26 countermeasures system
	# UV-26 DISPENSER - BOTH
	pushSeqCmd(dt, 'CMD_FLARE_SEL', 1)
	# UV-26 RESET TO DEFAULT PROGRAM (110)
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
	# PILOT'S FAN - ON
	pushSeqCmd(dt, 'CPIT_AIR_L_FAN', 1)
	# COPILOT'S FAN - ON
	pushSeqCmd(dt, 'CPIT_AIR_R_FAN', 1)

	if vars.get('Weapons') == 'Armed':
		pushSeqCmd(dt, 'scriptSpeech', "Setting up weapon systems.")
		# CB Group 1 - ON
		pushSeqCmd(dt, 'AZS_GRP_BTN1', 1)
		pushSeqCmd(dt, 'AZS_GRP_BTN1', 0)
		# CB Group 2 - ON
		pushSeqCmd(dt, 'AZS_GRP_BTN2', 1)
		pushSeqCmd(dt, 'AZS_GRP_BTN2', 0)
		# CB Group 3 - ON
		pushSeqCmd(dt, 'AZS_GRP_BTN3', 1)
		pushSeqCmd(dt, 'AZS_GRP_BTN3', 0)
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

	pushSeqCmd(dt, 'scriptSpeech', "Manual steps remaining: Set lights.  Tune radios.  Set doppler navigation.  Set altimeter to Q F E or Q N H.")

	return seq


def Shutdown(config, vars):
	seq = []
	seqTime = 0
	dt = 0.3

	def pushSeqCmd(dt, cmd, *args, **kwargs):
		nonlocal seq, seqTime

		if len(args):
			seq.append({
				'time': round(dt, 2),
				'cmd': cmd,
				'arg': args[0],
				'msg': args[1] if len(args) > 1 else '',
			})
		else:
			step = {
				'time': round(dt, 2),
				'cmd': cmd,
			}
			for key in kwargs:
				step[key] = kwargs[key]
			seq.append(step)

	pushSeqCmd(0, '', '', "Running Shutdown sequence")

	# LEFT COCKPIT WINDOW - OPEN
	pushSeqCmd(dt, 'BLST_L_OPEN', 0)

	# Fans
	# PILOT'S FAN - OFF
	pushSeqCmd(dt, 'CPIT_AIR_L_FAN', 0)
	# COPILOT'S FAN - OFF
	pushSeqCmd(dt, 'CPIT_AIR_R_FAN', 0)

	# Main Switch - OFF
	pushSeqCmd(dt, 'WPN_RS_GUV_SEL', 0)
	# Master Arm - OFF
	pushSeqCmd(dt, 'WPN_ARM', 0)

	# Anti-dust system - Off
	pushSeqCmd(dt, 'ENG_L_ENG_DUST', 0)
	pushSeqCmd(dt, 'ENG_R_ENG_DUST', 0)

	# All lights - Off
	# Dome lights.
	pushSeqCmd(dt, 'LGHT_L_CEIL', 1) # 0 = White, 1 = Off, 2 = Red
	pushSeqCmd(dt, 'LGHT_R_CEIL', 1) # 0 = White, 1 = Off, 2 = Red
	# Left red light knobs.
	pushSeqCmd(dt, 'L_RED_LGHT_1', 0)
	pushSeqCmd(dt, 'L_RED_LGHT_2', 0)
	# Right red light knobs.
	pushSeqCmd(dt, 'R_RED_LGHT_1', 0)
	pushSeqCmd(dt, 'R_RED_LGHT_2', 0)
	# Center red light knobs.
	pushSeqCmd(dt, 'C_RED_LGHT_1', 0)
	pushSeqCmd(dt, 'C_RED_LGHT_2', 0)
	# 5.5V lights (radar altimeter and other instruments)
	# Switch
	pushSeqCmd(dt, 'LGHT_5_5V', 0)
	# Brightness
	pushSeqCmd(dt, 'LGHT_55V', 0)
	# ANNUC switch - DAY
	pushSeqCmd(dt, 'SAS_TRANS', 0)

	# Formation lights - Off
	pushSeqCmd(dt, 'LGHT_FRM', 1)
	# Anti-collision/strobe light - Off
	pushSeqCmd(dt, 'LGHT_STROBE', 0)
	# Blade tip lights - Off
	pushSeqCmd(dt, 'LGHT_TIP', 0)
	# Nav (ANO??) lights - Off
	pushSeqCmd(dt, 'LGHT_ANO', 1)

	# Pilot's triangular panel
	# LEFT ATT IND - OFF
	pushSeqCmd(dt, 'ADI_L_ATT_PWR', 0)
	# GYRO CUT OUT - OFF
	pushSeqCmd(dt, 'ADI_VK53_PWR', 0)
	# PITCH LIM SYS - OFF
	pushSeqCmd(dt, 'SPUU52_PWR', 0)
	# AUDIO WARN - OFF
	pushSeqCmd(dt, 'RI65_PWR', 0)

	# Copilot's triangular panel
	# DOPP - OFF
	pushSeqCmd(dt, 'DPL_PWR', 0)
	# COMP SYS - OFF
	pushSeqCmd(dt, 'GMC_PWR', 0)
	# RIGHT ATT IND - OFF
	pushSeqCmd(dt, 'ADI_R_ATT_PWR', 0)
	# COMM RADIO - OFF
	pushSeqCmd(dt, 'JAD1A_PWR', 0)

	# Other
	# RADAR ALTIMETER - OFF
	pushSeqCmd(dt, 'RADAR_ALT_PWR', 0)
	# FLASHER - OFF
	pushSeqCmd(dt, 'SAS_FLASH', 0)

	# Generators and Rectifiers
	# RECTIFIER 1 - OFF
	pushSeqCmd(dt, 'RECT1_SWITCH', 0)
	# RECTIFIER 2 - OFF
	pushSeqCmd(dt, 'RECT2_SWITCH', 0)
	# RECTIFIER 3 - OFF
	pushSeqCmd(dt, 'RECT3_SWITCH', 0)
	# GENERATOR 1 - OFF
	pushSeqCmd(dt, 'GEN1_SWITCH', 0)
	# GENERATOR 2 - OFF
	pushSeqCmd(dt, 'GEN2_SWITCH', 0)

	# Twist grip to min (DECR)
	# THROTTLE - MINIMUM (LEFT)
	pushSeqCmd(dt, 'scriptKeyboard', 'pgdn down')
	pushSeqCmd(2, 'scriptKeyboard', 'pgdn up') # Hold down for 2 seconds

	# Wait 1m10s for rotor to come down to idle RPM (70%)
	pushSeqCmd(dt, 'scriptSpeech', 'Waiting for rotor to reach idle RPM, 70%')
	pushSeqCmd(1 * 60 + 10, '', '', 'Rotor at 70% RPM')

	# LEFT ENGINE FUEL SHUTOFF LEVER - CLOSE
	pushSeqCmd(dt, 'ENG_LEFT_STOP', 0)
	# RIGHT ENGINE FUEL SHUTOFF LEVER - CLOSE
	pushSeqCmd(dt, 'ENG_RIGHT_STOP', 0)

	# Wait 2m40s for rotor to come down to 15% RPM.
	pushSeqCmd(dt, 'scriptSpeech', 'Waiting for rotor to reach 15% RPM')
	pushSeqCmd(1 * 60 + 40, '', '', 'Rotor at 15% RPM')

	# ROTOR BRAKE - ON
	pushSeqCmd(dt, 'ENG_RTR_BRAKE', 1)

	# LEFT SHUTOFF VALVE - OFF
	pushSeqCmd(dt, 'FUEL_LEFT_COVER', 1) # switch cover
	pushSeqCmd(dt, 'FUEL_LEFT_SHUTOFF', 0) # switch
	pushSeqCmd(dt, 'FUEL_LEFT_COVER', 0) # switch cover

	# RIGHT SHUTOFF VALVE - OFF
	pushSeqCmd(dt, 'FUEL_RIGHT_COVER', 1) # switch cover
	pushSeqCmd(dt, 'FUEL_RIGTH_SHUTOFF', 0) # switch # NOTE Spelling error in command, "FUEL_RIGTH_SHUTOFF" is the correct spelling for the command.
	pushSeqCmd(dt, 'FUEL_RIGHT_COVER', 0) # switch cover

	# SERVICE TANK PUMP - OFF
	pushSeqCmd(dt, 'FUEL_FEED_PUMP', 0)
	# LEFT TANK PUMP - OFF
	pushSeqCmd(dt, 'FUEL_LEFT_PUMP', 0)
	# RIGHT TANK PUMP - OFF
	pushSeqCmd(dt, 'FUEL_RIGTH_PUMP', 0) # NOTE Spelling error in command, "FUEL_RIGTH_PUMP" is the correct spelling for the command.

	# FIRE EXTINGUISHER - OFF
	pushSeqCmd(dt, 'DCHARGE_FIRE_DETECT_TEST', 0)

	# R-828 radio
	# R-828 RADIO POWER - OFF
	pushSeqCmd(dt, 'R828_PWR', 0)

	# UV-26 countermeasures system
	# UV-26 POWER - OFF
	pushSeqCmd(dt, 'CMD_PWR', 0)

	# All circuit breakers off
	# Group 1
	pushSeqCmd(dt, 'CB_BW_ESBR', 0)
	pushSeqCmd(dt, 'CB_CTRL', 0)
	pushSeqCmd(dt, 'CB_EQUIP', 0)
	pushSeqCmd(dt, 'CB_ESBR_HEAT', 0)
	pushSeqCmd(dt, 'CB_EXPLODE', 0)
	pushSeqCmd(dt, 'CB_RS_GUV_FIRE', 0)
	pushSeqCmd(dt, 'CB_RS_GUV_WARN', 0)

	# Group 2
	pushSeqCmd(dt, 'CB_311', 0)
	pushSeqCmd(dt, 'CB_GUV_622_LEFT_INNER_LEFT', 0)
	pushSeqCmd(dt, 'CB_GUV_622_LEFT_INNER_RIGHT', 0)
	pushSeqCmd(dt, 'CB_GUV_622_RIGHT_INNER_LEFT', 0)
	pushSeqCmd(dt, 'CB_GUV_622_RIGHT_INNER_RIGHT', 0)
	pushSeqCmd(dt, 'CB_GUV_OUTER_LEFT', 0)
	pushSeqCmd(dt, 'CB_GUV_OUTER_RIGHT', 0)

	# Group 3
	pushSeqCmd(dt, 'CB_ELEC_LAUNCH_LEFT', 0)
	pushSeqCmd(dt, 'CB_ELEC_LAUNCH_RIGHT', 0)
	pushSeqCmd(dt, 'CB_JET_ARM', 0)
	pushSeqCmd(dt, 'CB_JET_BOMB_GUV', 0)
	pushSeqCmd(dt, 'CB_JET_PWR', 0)
	pushSeqCmd(dt, 'CB_PKT', 0)
	pushSeqCmd(dt, 'CB_SIG_FLARE', 0)

	# Group 4
	pushSeqCmd(dt, 'CB_APU_IGN', 0)
	pushSeqCmd(dt, 'CB_APU_START', 0)
	pushSeqCmd(dt, 'CB_CTRL_MAIN', 0)
	pushSeqCmd(dt, 'CB_CTRL_RES', 0)
	pushSeqCmd(dt, 'CB_ENG_IGN', 0)
	pushSeqCmd(dt, 'CB_ENG_START', 0)
	pushSeqCmd(dt, 'CB_NONAME', 0)
	pushSeqCmd(dt, 'CB_RPM', 0)
	pushSeqCmd(dt, 'CB_TURN', 0)

	# Group 5
	pushSeqCmd(dt, 'CB_FUEL_BYPASS', 0)
	pushSeqCmd(dt, 'CB_FUEL_CENTER_PUMP', 0)
	pushSeqCmd(dt, 'CB_FUEL_LEFT_PUMP', 0)
	pushSeqCmd(dt, 'CB_FUEL_LEFT_VALVE', 0)
	pushSeqCmd(dt, 'CB_FUEL_METER', 0)
	pushSeqCmd(dt, 'CB_FUEL_RIGHT_PUMP', 0)
	pushSeqCmd(dt, 'CB_FUEL_RIGHT_VALVE', 0)
	pushSeqCmd(dt, 'CB_SPUU52', 0)
	pushSeqCmd(dt, 'CB_T819', 0)

	# Group 6
	pushSeqCmd(dt, 'CB_ANO', 0)
	pushSeqCmd(dt, 'CB_CHECK_LAMP', 0)
	pushSeqCmd(dt, 'CB_LIGHTS_LEFT_CTRL', 0)
	pushSeqCmd(dt, 'CB_LIGHTS_LEFT_LIGHT', 0)
	pushSeqCmd(dt, 'CB_LIGHTS_RIGHT_CTRL', 0)
	pushSeqCmd(dt, 'CB_LIGHTS_RIGHT_LIGHT', 0)
	pushSeqCmd(dt, 'CB_PRF4_LEFT', 0)
	pushSeqCmd(dt, 'CB_PRF4_RIGHT', 0)
	pushSeqCmd(dt, 'CB_WING_LIGHTS', 0)

	# Group 7
	pushSeqCmd(dt, 'CB_6201', 0)
	pushSeqCmd(dt, 'CB_ALTIMETER', 0)
	pushSeqCmd(dt, 'CB_AUTO_PILOT_CLUTCH', 0)
	pushSeqCmd(dt, 'CB_AUTO_PILOT_FRICTION', 0)
	pushSeqCmd(dt, 'CB_AUTO_PILOT_MAIN', 0)
	pushSeqCmd(dt, 'CB_HYDR_AUX', 0)
	pushSeqCmd(dt, 'CB_HYDR_MAIN', 0)
	pushSeqCmd(dt, 'CB_R863', 0)
	pushSeqCmd(dt, 'CB_SPU', 0)

	# Group 8
	pushSeqCmd(dt, 'CB_ARC9', 0)
	pushSeqCmd(dt, 'CB_ARCUD', 0)
	pushSeqCmd(dt, 'CB_DOPPLER', 0)
	pushSeqCmd(dt, 'CB_FIRE_1_LEFT', 0)
	pushSeqCmd(dt, 'CB_FIRE_1_RIGHT', 0)
	pushSeqCmd(dt, 'CB_FIRE_2_LEFT', 0)
	pushSeqCmd(dt, 'CB_FIRE_2_RIGHT', 0)
	pushSeqCmd(dt, 'CB_FIRE_SIG', 0)
	pushSeqCmd(dt, 'CB_RADIO_METER', 0)

	# Group 9
	pushSeqCmd(dt, 'CB_DFRST_CTRL', 0)
	pushSeqCmd(dt, 'CB_DFRST_GLASS', 0)
	pushSeqCmd(dt, 'CB_DFRST_LEFT', 0)
	pushSeqCmd(dt, 'CB_DFRST_RIGHT', 0)
	pushSeqCmd(dt, 'CB_DFRST_RIO3', 0)
	pushSeqCmd(dt, 'CB_KO50', 0)
	pushSeqCmd(dt, 'CB_RIO3', 0)
	pushSeqCmd(dt, 'CB_WPR_LEFT', 0)
	pushSeqCmd(dt, 'CB_WPR_RIGHT', 0)

	# BATTERY 1 - OFF
	pushSeqCmd(dt, 'BATT1_SWITCH', 0)
	# BATTERY 2 - OFF
	pushSeqCmd(dt, 'BATT2_SWITCH', 0)
	# 115V INVERTER - OFF
	pushSeqCmd(dt, 'INV_115V_SWITCH', 1)
	# 36V INVERTER - OFF
	pushSeqCmd(dt, 'INV_36V_SWITCH', 1)

	# DC VOLTMETER SELECTOR - OFF
	pushSeqCmd(dt, 'DC_VOLT_SEL', 0)
	# AC VOLTMETER SELECTOR - OFF
	pushSeqCmd(dt, 'AC_VOLT_SEL', 0)

	return seq
