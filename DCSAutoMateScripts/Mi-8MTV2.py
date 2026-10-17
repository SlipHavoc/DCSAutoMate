# Return a Dictionary of script data.  The 'scripts' key is a list of scripts that users will be selecting from.  Each script has an associated 'function', which is the name of the function in this file that will be called to generate the command sequence, and a dictionary of 'vars' that the user will be prompted to choose from before running the script, and will be passed into the sequence generating function.
def getScriptData():
	return {
		'moduleName': 'Mi-8MT',
		'scripts': [
			{
				'name': 'Cold Start',
				'function': 'ColdStart',
				'vars': {
					'time': {
						'label': 'Time',
						'options': {
							'day': 'Day',
							'night': 'Night',
						},
					},
					'weapons': {
						'label': 'Weapons',
						'options': {
							'armed': 'Armed',
							'unarmed': 'Unarmed',
						},
					},
				},
			},
			{
				'name': 'Hot Start',
				'function': 'HotStart',
				'vars': {
					'time': {
						'label': 'Time',
						'options': {
							'day': 'Day',
							'night': 'Night',
						},
					},
					'weapons': {
						'label': 'Weapons',
						'options': {
							'armed': 'Armed',
							'unarmed': 'Unarmed',
						},
					},
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
			#		'time': {
			#			'label': 'Time',
			#			'options': {
			#				'day': 'Day',
			#				'night': 'Night',
			#			},
			#		},
			#		'weapons': {
			#			'label': 'Weapons',
			#			'options': {
			#				'armed': 'Armed',
			#				'unarmed': 'Unarmed',
			#			},
			#		},
			#	},
			#},
		],
	}

def getInfo():
	return ''

def Test(config, vars, helper, *args, **kwargs):
	seq = []
	dt = 0.3

	pushSeqCmd = helper.makePushSeqCmd(seq)

	# Test code here...

	return seq


def ColdStart(config, vars, helper, *args, **kwargs):
	seq = []
	dt = 0.3

	pushSeqCmd = helper.makePushSeqCmd(seq)

	pushSeqCmd(0, '', '', "Running Cold Start sequence")
	pushSeqCmd(dt, '', '', 'Set collective full down.')
	pushSeqCmd(dt, 'scriptSpeech', 'Set collective full down.')

	# RADIO/ICS SWITCH - ICS (allows rearming)
	pushSeqCmd(dt, 'SPU_7.PTR-LAZS-TMB-RADSPU', 1)

	# LEFT COCKPIT WINDOW - CLOSE
	pushSeqCmd(dt, 'CPT_MECH.PTR-BLISTER-LOCK-L', 1)

	# Power levers and throttle
	# ENGINE POWER LEVERS - AUTO
	# Throttles down twice first to make sure they're at min.
	pushSeqCmd(dt, 'ENGINE_INTERFACE.Button_60', -1) # Throttle down
	pushSeqCmd(dt, 'ENGINE_INTERFACE.Button_60', -1)
	# Then throttles up once to set to auto.
	pushSeqCmd(dt, 'ENGINE_INTERFACE.Button_60', 1) # Throttle up

	# Twist grip to min (DECR)
	# THROTTLE - MINIMUM (LEFT)
	pushSeqCmd(dt, 'scriptSimCommand', 'iCommandThrottleDecrease') # Correction lever decrease (PgDn)
	pushSeqCmd(2, 'scriptSimCommand', 'iCommandThrottleStop') # Hold down for 2 seconds
	# Collective full down.
	# COLLECTIVE - FULL DOWN
	pushSeqCmd(dt, 'scriptSimCommand', 'iCommandPlaneCollectiveDecrease') # Numpad -
	pushSeqCmd(2, 'scriptSimCommand', 'iCommandPlaneCollectiveStop') # Hold down for 2 seconds

	# ROTOR BRAKE - OFF
	pushSeqCmd(dt, 'ENGINE_INTERFACE.PTR-VINTBRAKE-ARM', 0)

	# BATTERY 1 - ON
	pushSeqCmd(dt, 'ELEC_INTERFACE.PTR-RSPE-TMB-AKK1', 1)
	# BATTERY 2 - ON
	pushSeqCmd(dt, 'ELEC_INTERFACE.PTR-RSPE-TMB-AKK2', 1)
	# 115V INVERTER - AUTO (down) # 0 = AUTO, 1 = OFF, 2 = MAN
	pushSeqCmd(dt, 'ELEC_INTERFACE.PTR-EEP-TMB-PO', 0)

	if vars.get('time') != 'day':
		# Dome lights.
		pushSeqCmd(dt, 'LIGHT_SYSTEM.PTR-LES-TMB-PLF', 2) # 0 = WHITE, 1 = OFF, 2 = RED
		pushSeqCmd(dt, 'LIGHT_SYSTEM.PTR-RES-TMB-PLF', 2) # 0 = WHITE, 1 = OFF, 2 = RED
		# Left red light knobs.
		pushSeqCmd(dt, 'LIGHT_SYSTEM.PTR-LSPE-LVR-REDGRP1', 1.0)
		pushSeqCmd(dt, 'LIGHT_SYSTEM.PTR-LSPE-LVR-REDGRP2', 1.0)
		# Right red light knobs.
		pushSeqCmd(dt, 'LIGHT_SYSTEM.PTR-RSPE-LVR-REDGRP1', 1.0)
		pushSeqCmd(dt, 'LIGHT_SYSTEM.PTR-RSPE-LVR-REDGRP2', 1.0)
		# Center red light knobs.
		pushSeqCmd(dt, 'LIGHT_SYSTEM.PTR-RSPE-LVR-REDGRP003', 1.0)
		pushSeqCmd(dt, 'LIGHT_SYSTEM.PTR-RSPE-LVR-REDGRP004', 1.0)
		# 5.5V lights (radar altimeter and other instruments)
		# Switch
		pushSeqCmd(dt, 'LIGHT_SYSTEM.PTR-RES-TMB-LGT', 1)
		# Brightness
		pushSeqCmd(dt, 'LIGHT_SYSTEM.PTR-RSPE-LVR-REDGRP005', 1.0)
		# ANNUC switch - NIGHT
		pushSeqCmd(dt, 'SYS_CONTROLLER.PTR-RSPE-TMB-TAB', 1)
		# Gunsight brightness
		pushSeqCmd(dt, 'PKV.PTR-LAZS-LVR-AIMLGT', 0.2)

	# DC VOLTMETER SELECTOR - BATT BUS
	pushSeqCmd(dt, 'ELEC_INTERFACE.PTR-RSPE-LVR-FEEDMODE', 4)

	# CIRCUIT BREAKER GROUP 4 - ON
	pushSeqCmd(dt, 'ELEC_INTERFACE.PTR-GRAZS-2', 1)
	pushSeqCmd(dt, 'ELEC_INTERFACE.PTR-GRAZS-2', 0)

	# CIRCUIT BREAKER GROUP 5 - ON
	pushSeqCmd(dt, 'ELEC_INTERFACE.PTR-GRAZS-5', 1)
	pushSeqCmd(dt, 'ELEC_INTERFACE.PTR-GRAZS-5', 0)

	# CIRCUIT BREAKER GROUP 6 - ON
	pushSeqCmd(dt, 'ELEC_INTERFACE.PTR-GRAZS-8', 1)
	pushSeqCmd(dt, 'ELEC_INTERFACE.PTR-GRAZS-8', 0)

	# CIRCUIT BREAKER GROUP 7 - ON
	pushSeqCmd(dt, 'ELEC_INTERFACE.PTR-GRAZS-3', 1)
	pushSeqCmd(dt, 'ELEC_INTERFACE.PTR-GRAZS-3', 0)

	# CIRCUIT BREAKER GROUP 8 - ON
	pushSeqCmd(dt, 'ELEC_INTERFACE.PTR-GRAZS-6', 1)
	pushSeqCmd(dt, 'ELEC_INTERFACE.PTR-GRAZS-6', 0)

	# CIRCUIT BREAKER GROUP 9 - ON
	pushSeqCmd(dt, 'ELEC_INTERFACE.PTR-GRAZS-9', 1)
	pushSeqCmd(dt, 'ELEC_INTERFACE.PTR-GRAZS-9', 0)

	# FIRE EXTINGUISHER - ON
	pushSeqCmd(dt, 'FIRE_EXTING_INTERFACE.PTR-CPE-TMB-CONTR-FIRE', 1)

	# FUEL METER - TOTAL
	pushSeqCmd(dt, 'FUELSYS_INTERFACE.PTR-FUEL-LVR-MODE', 1) # 0 = OFF, 1 = TOTAL, 2 = LEFT, 3 = RIGHT, 4 = SERV, 5 = AUX

	# LEFT SHUTOFF VALVE - ON
	pushSeqCmd(dt, 'FUELSYS_INTERFACE.PTR-CPE-CVR-PUMP-L', 1) # switch cover
	pushSeqCmd(dt, 'FUELSYS_INTERFACE.PTR-CPE-TMB-PUMP-L', 1) # switch
	pushSeqCmd(dt, 'FUELSYS_INTERFACE.PTR-CPE-CVR-PUMP-L', 0) # switch cover

	# RIGHT SHUTOFF VALVE - ON
	pushSeqCmd(dt, 'FUELSYS_INTERFACE.PTR-CPE-CVR-PUMP-R', 1) # switch cover
	pushSeqCmd(dt, 'FUELSYS_INTERFACE.PTR-CPE-TMB-PUMP-R', 1) # switch # NOTE Spelling error in command, "FUELSYS_INTERFACE.PTR-CPE-TMB-PUMP-R" is the correct spelling for the command.
	pushSeqCmd(dt, 'FUELSYS_INTERFACE.PTR-CPE-CVR-PUMP-R', 0) # switch cover

	# SERVICE TANK PUMP - ON
	pushSeqCmd(dt, 'FUELSYS_INTERFACE.PTR-CPE-TMB-PUMP-RATE', 1)
	# LEFT TANK PUMP - ON
	pushSeqCmd(dt, 'FUELSYS_INTERFACE.PTR-CPE-TMB-PUMPTNK-L', 1)
	# RIGHT TANK PUMP - ON
	pushSeqCmd(dt, 'FUELSYS_INTERFACE.PTR-CPE-TMB-PUMPTNK-R', 1) # NOTE Spelling error in command, "FUELSYS_INTERFACE.PTR-CPE-TMB-PUMPTNK-R" is the correct spelling for the command.

	# R-828 radio
	# R-828 RADIO POWER - ON
	pushSeqCmd(dt, 'R_828.PTR-ADDSECPLT-TMB-P828', 1)

	# APU
	# STARTING APU (28 SEC)
	# APU START MODE - START
	pushSeqCmd(dt, 'ENGINE_INTERFACE.PTR-CPE-TMB-TURBOSTART-ST', 2) # 0 = FALSE START, 1 = CRANK, 2 = START
	# APU START BUTTON - HOLD FOR 3 SEC
	pushSeqCmd(dt, 'ENGINE_INTERFACE.PTR-CPE-BTN-TURBOSTART-ON', 1) # Press
	pushSeqCmd(3, 'ENGINE_INTERFACE.PTR-CPE-BTN-TURBOSTART-ON', 0) # Release after 3 seconds
	pushSeqCmd(20, '', '', 'APU STARTED')

	# Left engine
	# STARTING LEFT ENGINE (61 SEC)
	# ENGINE START MODE - START
	pushSeqCmd(dt, 'ENGINE_INTERFACE.PTR-CPE-TMB-ENGSTART-ROLL', 2) # 0 = CRANK, 1 = OFF, 2 = START
	# ENGINE SELECTOR SWITCH - LEFT
	pushSeqCmd(dt, 'ENGINE_INTERFACE.PTR-CPE-TMB-ENGSTART-LFTRGT', 0) # 0 = LEFT, 1 = OFF, 2 = RIGHT
	# ENGINE START BUTTON - HOLD FOR 3 SEC
	pushSeqCmd(dt, 'ENGINE_INTERFACE.PTR-CPE-BTN-ENGSTART-ON', 1) # Press
	pushSeqCmd(3, 'ENGINE_INTERFACE.PTR-CPE-BTN-ENGSTART-ON', 0) # Release after 3 seconds
	# LEFT ENGINE FUEL SHUTOFF LEVER - OPEN
	pushSeqCmd(dt, 'ENGINE_INTERFACE.PTR-ENGSTOP-ARM-L', 1)
	pushSeqCmd(55, '', '', "LEFT ENGINE - STARTED")

	# Right engine
	# STARTING RIGHT ENGINE (61 SEC)
	# ENGINE SELECTOR SWITCH - RIGHT
	pushSeqCmd(dt, 'ENGINE_INTERFACE.PTR-CPE-TMB-ENGSTART-LFTRGT', 2) # 0 = LEFT, 1 = OFF, 2 = RIGHT
	# ENGINE START BUTTON - HOLD FOR 3 SEC
	pushSeqCmd(dt, 'ENGINE_INTERFACE.PTR-CPE-BTN-ENGSTART-ON', 1) # Press
	pushSeqCmd(3, 'ENGINE_INTERFACE.PTR-CPE-BTN-ENGSTART-ON', 0) # Release after 3 seconds
	# RIGHT ENGINE FUEL SHUTOFF LEVER - OPEN
	pushSeqCmd(dt, 'ENGINE_INTERFACE.PTR-ENGSTOP-ARM-R', 1)
	pushSeqCmd(55, '', '', "RIGHT ENGINE - STARTED")

	# Engines started, selector to neutral
	# ENGINE SELECTOR SWITCH - CENTER
	pushSeqCmd(dt, 'ENGINE_INTERFACE.PTR-CPE-TMB-ENGSTART-LFTRGT', 1) # 0 = LEFT, 1 = OFF, 2 = RIGHT

	# Twist grip to max (INCR)
	# THROTTLE - MAXIMUM (RIGHT)
	pushSeqCmd(dt, 'scriptSimCommand', 'iCommandThrottleIncrease') # Correction lever increase (PgUp)
	pushSeqCmd(2, 'scriptSimCommand', 'iCommandThrottleStop') # Hold down for 2 seconds
	# ALLOW RPM TO STABILIZE (10 SEC)
	pushSeqCmd(10, '', '', "RPM STABILIZED")

	# Generators and Rectifiers
	# TURN ON GENERATORS
	# GENERATOR 1 - ON
	pushSeqCmd(dt, 'ELEC_INTERFACE.PTR-EEP-TMB-GEN1', 1)
	# GENERATOR 2 - ON
	pushSeqCmd(dt, 'ELEC_INTERFACE.PTR-EEP-TMB-GEN2', 1)
	# RECTIFIER 1 - ON
	pushSeqCmd(dt, 'ELEC_INTERFACE.PTR-RSPE-TMB-RECT1', 1)
	# RECTIFIER 2 - ON
	pushSeqCmd(dt, 'ELEC_INTERFACE.PTR-RSPE-TMB-RECT2', 1)
	# RECTIFIER 3 - ON
	pushSeqCmd(dt, 'ELEC_INTERFACE.PTR-RSPE-TMB-RECT3', 1)
	# DC VOLTMETER SELECTOR - RECT BUS
	pushSeqCmd(dt, 'ELEC_INTERFACE.PTR-RSPE-LVR-FEEDMODE', 5)
	# AC VOLTMETER SELECTOR - 115V
	pushSeqCmd(dt, 'ELEC_INTERFACE.PTR-EEP-LVR-MODE', 10)

	# 36V INVERTER - AUTO (down)
	pushSeqCmd(dt, 'ELEC_INTERFACE.PTR-EEP-TMB-PT', 0) # 0 = AUTO, 1 = OFF, 2 = MAN

	# APU STOP
	pushSeqCmd(dt, 'ENGINE_INTERFACE.PTR-CPE-BTN-TURBOSTART-OFF', 1) # Press
	pushSeqCmd(dt, 'ENGINE_INTERFACE.PTR-CPE-BTN-TURBOSTART-OFF', 0) # Release

	# Pilot's triangular panel
	# LEFT ATT IND - ON
	pushSeqCmd(dt, 'AGB_3K_LEFT.PTR-LES-TMB-AG', 1)
	# GYRO CUT OUT - ON
	pushSeqCmd(dt, 'CORRECTION_INTERRUPT.PTR-LES-TMB-VK53', 1)
	# PITCH LIM SYS - ON
	pushSeqCmd(dt, 'SPUU_52.PTR-LES-TMB-SPPU52', 1)
	# AUDIO WARN - ON
	pushSeqCmd(dt, 'VMS.PTR-LES-TMB-RK85', 1)

	# Copilot's triangular panel
	# DOPP - ON
	pushSeqCmd(dt, 'DISS_15.PTR-RES-TMB-DISS', 1)
	# COMP SYS - ON
	pushSeqCmd(dt, 'GMK1A.PTR-RES-TMB-GMK', 1)
	# RIGHT ATT IND - ON
	pushSeqCmd(dt, 'AGB_3K_RIGHT.PTR-RES-TMB-AG', 1)
	# COMM RADIO - ON
	pushSeqCmd(dt, 'JADRO_1A.PTR-RES-TMB-RS', 1)

	# Other
	# RADAR ALTIMETER - ON
	pushSeqCmd(dt, 'RADAR_ALTIMETER.PTR-ALTR-TMB-ONOFF', 1)
	# FLASHER - ON
	pushSeqCmd(dt, 'SYS_CONTROLLER.PTR-RSPE-TMB-WINK', 1)
	# AUTOPILOT ROLL/PITCH CHANNEL - ON
	pushSeqCmd(dt, 'AUTOPILOT.PTR-APP-BTN-KTON_arg138', 1) # Press
	pushSeqCmd(dt, 'AUTOPILOT.PTR-APP-BTN-KTON_arg138', 0) # Release

	# UV-26 countermeasures system
	# UV-26 POWER - ON
	pushSeqCmd(dt, 'UV_26.PTR-UV26-ONOFF', 1)
	# UV-26 DISPENSER - BOTH
	pushSeqCmd(dt, 'UV_26.PTR-UV26-BOARD', 1) # 0 = LEFT, 1 = BOTH, 2 = RIGHT
	# UV-26 RESET TO DEFAULT PROGRAM (110)
	pushSeqCmd(dt, 'UV_26.PTR-RESET-PROG-BTN', 1) # Press
	pushSeqCmd(dt, 'UV_26.PTR-RESET-PROG-BTN', 0) # Release
	# Set "411" (4 flares, 1 second apart)...
	# Press "Num Of Sequences" button 3x.
	for i in range(3): # Press and release 3 times
		pushSeqCmd(dt, 'UV_26.PTR-L45-BTN', 1) # Press
		pushSeqCmd(dt, 'UV_26.PTR-L45-BTN', 0) # Release
	# "Num In Sequence" is already set to 1.
	#pushSeqCmd(dt, 'UV_26.PTR-L8-BTN', 1) # Press
	#pushSeqCmd(dt, 'UV_26.PTR-L8-BTN', 0) # Release
	# Press "Dispense Interval" button 1x.
	pushSeqCmd(dt, 'UV_26.PTR-L68-BTN', 1) # Press
	pushSeqCmd(dt, 'UV_26.PTR-L68-BTN', 0) # Release

	# Fans
	# PILOT'S FAN - ON
	pushSeqCmd(dt, 'CPT_MECH.PTR-LES-TMB-VENT', 1)
	# COPILOT'S FAN - ON
	pushSeqCmd(dt, 'CPT_MECH.PTR-RES-TMB-VENT', 1)

	# Reset G-meter
	pushSeqCmd(dt, 'CPT_MECH.PTR-RSPE-TMB-WINK002', 1) # Press
	pushSeqCmd(dt, 'CPT_MECH.PTR-RSPE-TMB-WINK002', 0) # Release

	if vars.get('weapons') == 'armed':
		pushSeqCmd(dt, 'scriptSpeech', "Setting up weapon systems.")
		# CB Group 1 - ON
		pushSeqCmd(dt, 'ELEC_INTERFACE.PTR-GRAZS-1', 1)
		pushSeqCmd(dt, 'ELEC_INTERFACE.PTR-GRAZS-1', 0)
		# CB Group 2 - ON
		pushSeqCmd(dt, 'ELEC_INTERFACE.PTR-GRAZS-4', 1)
		pushSeqCmd(dt, 'ELEC_INTERFACE.PTR-GRAZS-4', 0)
		# CB Group 3 - ON
		pushSeqCmd(dt, 'ELEC_INTERFACE.PTR-GRAZS-7', 1)
		pushSeqCmd(dt, 'ELEC_INTERFACE.PTR-GRAZS-7', 0)
		# Main Switch - ON
		pushSeqCmd(dt, 'WEAPON_SYS.PTR-LAZS-TMB-RSGUV', 1)
		# Master Arm - ON
		pushSeqCmd(dt, 'WEAPON_SYS.PTR-SAFE-WEAPON', 1)

		# Arm rocket systems...
		# UPK/PKT/RS switch - RS
		pushSeqCmd(dt, 'WEAPON_SYS.PTR-LPE-TMB-RS', 0)
		# Push and hold FIRE TEST UNIT ARM button for 4 seconds.
		pushSeqCmd(dt, 'WEAPON_SYS.PTR-LAZS-BTN-ENTER', 1)
		pushSeqCmd(4, 'WEAPON_SYS.PTR-LAZS-BTN-ENTER', 0) # Release after 4 seconds.
		# UPK/PKT/RS switch - PKT (default)
		pushSeqCmd(dt, 'WEAPON_SYS.PTR-LPE-TMB-RS', 1)

		# Set sight depression to red index marker.
		pushSeqCmd(dt, 'PKV.PTR-PKV-ROTARY', 0.2659)  # was 17427 (raw int16, 17427/65535)

	pushSeqCmd(dt, 'scriptSpeech', "Manual steps remaining: Set lights.  Tune radios.  Set doppler navigation.  Set altimeter to Q F E or Q N H.")

	return seq


def HotStart(config, vars, helper, *args, **kwargs):
	seq = []
	dt = 0.3

	pushSeqCmd = helper.makePushSeqCmd(seq)

	pushSeqCmd(0, '', '', "Running Hot Start sequence")

	# RADIO/ICS SWITCH - ICS (allows rearming)
	pushSeqCmd(dt, 'SPU_7.PTR-LAZS-TMB-RADSPU', 1)

	# Formation lights - Off
	pushSeqCmd(dt, 'NAVLIGHT_SYSTEM.PTR-RSPE-TMB-LGTWING', 1) # 0 = DIM, 1 = OFF, 2 = BRIGHT

	# Anti-collision/strobe light - Off
	pushSeqCmd(dt, 'NAVLIGHT_SYSTEM.PTR-RSPE-TMB-BEAC', 0)

	# Blade tip lights - Off
	pushSeqCmd(dt, 'NAVLIGHT_SYSTEM.PTR-RSPE-TMB-LGTCONT', 0)

	# Nav (ANO??) lights - Off
	pushSeqCmd(dt, 'NAVLIGHT_SYSTEM.PTR-RSPE-TMB-ANO', 1) # 0 = DIM, 1 = OFF, 2 = BRIGHT

	if vars.get('time') != 'day':
		# Dome lights.
		pushSeqCmd(dt, 'LIGHT_SYSTEM.PTR-LES-TMB-PLF', 2) # 0 = WHITE, 1 = OFF, 2 = RED
		pushSeqCmd(dt, 'LIGHT_SYSTEM.PTR-RES-TMB-PLF', 2) # 0 = WHITE, 1 = OFF, 2 = RED
		# Left red light knobs.
		pushSeqCmd(dt, 'LIGHT_SYSTEM.PTR-LSPE-LVR-REDGRP1', 1.0)
		pushSeqCmd(dt, 'LIGHT_SYSTEM.PTR-LSPE-LVR-REDGRP2', 1.0)
		# Right red light knobs.
		pushSeqCmd(dt, 'LIGHT_SYSTEM.PTR-RSPE-LVR-REDGRP1', 1.0)
		pushSeqCmd(dt, 'LIGHT_SYSTEM.PTR-RSPE-LVR-REDGRP2', 1.0)
		# Center red light knobs.
		pushSeqCmd(dt, 'LIGHT_SYSTEM.PTR-RSPE-LVR-REDGRP003', 1.0)
		pushSeqCmd(dt, 'LIGHT_SYSTEM.PTR-RSPE-LVR-REDGRP004', 1.0)
		# 5.5V lights (radar altimeter and other instruments)
		# Switch
		pushSeqCmd(dt, 'LIGHT_SYSTEM.PTR-RES-TMB-LGT', 1)
		# Brightness
		pushSeqCmd(dt, 'LIGHT_SYSTEM.PTR-RSPE-LVR-REDGRP005', 1.0)
		# ANNUC switch - NIGHT
		pushSeqCmd(dt, 'SYS_CONTROLLER.PTR-RSPE-TMB-TAB', 1)
		# Gunsight brightness
		pushSeqCmd(dt, 'PKV.PTR-LAZS-LVR-AIMLGT', 0.2)

	# FUEL METER - TOTAL
	pushSeqCmd(dt, 'FUELSYS_INTERFACE.PTR-FUEL-LVR-MODE', 1) # 0 = OFF, 1 = TOTAL, 2 = LEFT, 3 = RIGHT, 4 = SERV, 5 = AUX

	# UV-26 countermeasures system
	# UV-26 DISPENSER - BOTH
	pushSeqCmd(dt, 'UV_26.PTR-UV26-BOARD', 1) # 0 = LEFT, 1 = BOTH, 2 = RIGHT
	# UV-26 RESET TO DEFAULT PROGRAM (110)
	pushSeqCmd(dt, 'UV_26.PTR-RESET-PROG-BTN', 1) # Press
	pushSeqCmd(dt, 'UV_26.PTR-RESET-PROG-BTN', 0) # Release
	# Set "411" (4 flares, 1 second apart)...
	# Press "Num Of Sequences" button 3x.
	for i in range(3): # Press and release 3 times
		pushSeqCmd(dt, 'UV_26.PTR-L45-BTN', 1) # Press
		pushSeqCmd(dt, 'UV_26.PTR-L45-BTN', 0) # Release
	# "Num In Sequence" is already set to 1.
	#pushSeqCmd(dt, 'UV_26.PTR-L8-BTN', 1) # Press
	#pushSeqCmd(dt, 'UV_26.PTR-L8-BTN', 0) # Release
	# Press "Dispense Interval" button 1x.
	pushSeqCmd(dt, 'UV_26.PTR-L68-BTN', 1) # Press
	pushSeqCmd(dt, 'UV_26.PTR-L68-BTN', 0) # Release

	# Fans
	# PILOT'S FAN - ON
	pushSeqCmd(dt, 'CPT_MECH.PTR-LES-TMB-VENT', 1)
	# COPILOT'S FAN - ON
	pushSeqCmd(dt, 'CPT_MECH.PTR-RES-TMB-VENT', 1)

	if vars.get('weapons') == 'armed':
		pushSeqCmd(dt, 'scriptSpeech', "Setting up weapon systems.")
		# CB Group 1 - ON
		pushSeqCmd(dt, 'ELEC_INTERFACE.PTR-GRAZS-1', 1)
		pushSeqCmd(dt, 'ELEC_INTERFACE.PTR-GRAZS-1', 0)
		# CB Group 2 - ON
		pushSeqCmd(dt, 'ELEC_INTERFACE.PTR-GRAZS-4', 1)
		pushSeqCmd(dt, 'ELEC_INTERFACE.PTR-GRAZS-4', 0)
		# CB Group 3 - ON
		pushSeqCmd(dt, 'ELEC_INTERFACE.PTR-GRAZS-7', 1)
		pushSeqCmd(dt, 'ELEC_INTERFACE.PTR-GRAZS-7', 0)
		# Master Arm - ON
		pushSeqCmd(dt, 'WEAPON_SYS.PTR-SAFE-WEAPON', 1)

		# Arm rocket systems...
		# UPK/PKT/RS switch - RS
		pushSeqCmd(dt, 'WEAPON_SYS.PTR-LPE-TMB-RS', 0)
		# Push and hold FIRE TEST UNIT ARM button for 4 seconds.
		pushSeqCmd(dt, 'WEAPON_SYS.PTR-LAZS-BTN-ENTER', 1)
		pushSeqCmd(4, 'WEAPON_SYS.PTR-LAZS-BTN-ENTER', 0) # Release after 4 seconds.
		# UPK/PKT/RS switch - PKT (default)
		pushSeqCmd(dt, 'WEAPON_SYS.PTR-LPE-TMB-RS', 1)

		# Set sight depression to red index marker.
		pushSeqCmd(dt, 'PKV.PTR-PKV-ROTARY', 0.2659)  # was 17427 (raw int16, 17427/65535)

	pushSeqCmd(dt, 'scriptSpeech', "Manual steps remaining: Set lights.  Tune radios.  Set doppler navigation.  Set altimeter to Q F E or Q N H.")

	return seq


def Shutdown(config, vars, helper, *args, **kwargs):
	seq = []
	dt = 0.3

	pushSeqCmd = helper.makePushSeqCmd(seq)

	pushSeqCmd(0, '', '', "Running Shutdown sequence")

	# LEFT COCKPIT WINDOW - OPEN
	pushSeqCmd(dt, 'CPT_MECH.PTR-BLISTER-LOCK-L', 0)

	# Fans
	# PILOT'S FAN - OFF
	pushSeqCmd(dt, 'CPT_MECH.PTR-LES-TMB-VENT', 0)
	# COPILOT'S FAN - OFF
	pushSeqCmd(dt, 'CPT_MECH.PTR-RES-TMB-VENT', 0)

	# Main Switch - OFF
	pushSeqCmd(dt, 'WEAPON_SYS.PTR-LAZS-TMB-RSGUV', 0)
	# Master Arm - OFF
	pushSeqCmd(dt, 'WEAPON_SYS.PTR-SAFE-WEAPON', 0)

	# Anti-dust system - Off
	pushSeqCmd(dt, 'ENGINE_INTERFACE.PTR-RSPE-TMB-PZUENG-L', 0)
	pushSeqCmd(dt, 'ENGINE_INTERFACE.PTR-RSPE-TMB-PZUENG-R', 0)

	# All lights - Off
	# Dome lights.
	pushSeqCmd(dt, 'LIGHT_SYSTEM.PTR-LES-TMB-PLF', 1) # 0 = WHITE, 1 = OFF, 2 = RED
	pushSeqCmd(dt, 'LIGHT_SYSTEM.PTR-RES-TMB-PLF', 1) # 0 = WHITE, 1 = OFF, 2 = RED
	# Left red light knobs.
	pushSeqCmd(dt, 'LIGHT_SYSTEM.PTR-LSPE-LVR-REDGRP1', 0)
	pushSeqCmd(dt, 'LIGHT_SYSTEM.PTR-LSPE-LVR-REDGRP2', 0)
	# Right red light knobs.
	pushSeqCmd(dt, 'LIGHT_SYSTEM.PTR-RSPE-LVR-REDGRP1', 0)
	pushSeqCmd(dt, 'LIGHT_SYSTEM.PTR-RSPE-LVR-REDGRP2', 0)
	# Center red light knobs.
	pushSeqCmd(dt, 'LIGHT_SYSTEM.PTR-RSPE-LVR-REDGRP003', 0)
	pushSeqCmd(dt, 'LIGHT_SYSTEM.PTR-RSPE-LVR-REDGRP004', 0)
	# 5.5V lights (radar altimeter and other instruments)
	# Switch
	pushSeqCmd(dt, 'LIGHT_SYSTEM.PTR-RES-TMB-LGT', 0)
	# Brightness
	pushSeqCmd(dt, 'LIGHT_SYSTEM.PTR-RSPE-LVR-REDGRP005', 0)
	# ANNUC switch - DAY
	pushSeqCmd(dt, 'SYS_CONTROLLER.PTR-RSPE-TMB-TAB', 0)

	# Formation lights - Off
	pushSeqCmd(dt, 'NAVLIGHT_SYSTEM.PTR-RSPE-TMB-LGTWING', 1) # 0 = DIM, 1 = OFF, 2 = BRIGHT
	# Anti-collision/strobe light - Off
	pushSeqCmd(dt, 'NAVLIGHT_SYSTEM.PTR-RSPE-TMB-BEAC', 0)
	# Blade tip lights - Off
	pushSeqCmd(dt, 'NAVLIGHT_SYSTEM.PTR-RSPE-TMB-LGTCONT', 0)
	# Nav (ANO??) lights - Off
	pushSeqCmd(dt, 'NAVLIGHT_SYSTEM.PTR-RSPE-TMB-ANO', 1) # 0 = DIM, 1 = OFF, 2 = BRIGHT

	# Pilot's triangular panel
	# LEFT ATT IND - OFF
	pushSeqCmd(dt, 'AGB_3K_LEFT.PTR-LES-TMB-AG', 0)
	# GYRO CUT OUT - OFF
	pushSeqCmd(dt, 'CORRECTION_INTERRUPT.PTR-LES-TMB-VK53', 0)
	# PITCH LIM SYS - OFF
	pushSeqCmd(dt, 'SPUU_52.PTR-LES-TMB-SPPU52', 0)
	# AUDIO WARN - OFF
	pushSeqCmd(dt, 'VMS.PTR-LES-TMB-RK85', 0)

	# Copilot's triangular panel
	# DOPP - OFF
	pushSeqCmd(dt, 'DISS_15.PTR-RES-TMB-DISS', 0)
	# COMP SYS - OFF
	pushSeqCmd(dt, 'GMK1A.PTR-RES-TMB-GMK', 0)
	# RIGHT ATT IND - OFF
	pushSeqCmd(dt, 'AGB_3K_RIGHT.PTR-RES-TMB-AG', 0)
	# COMM RADIO - OFF
	pushSeqCmd(dt, 'JADRO_1A.PTR-RES-TMB-RS', 0)

	# Other
	# RADAR ALTIMETER - OFF
	pushSeqCmd(dt, 'RADAR_ALTIMETER.PTR-ALTR-TMB-ONOFF', 0)
	# FLASHER - OFF
	pushSeqCmd(dt, 'SYS_CONTROLLER.PTR-RSPE-TMB-WINK', 0)

	# Generators and Rectifiers
	# RECTIFIER 1 - OFF
	pushSeqCmd(dt, 'ELEC_INTERFACE.PTR-RSPE-TMB-RECT1', 0)
	# RECTIFIER 2 - OFF
	pushSeqCmd(dt, 'ELEC_INTERFACE.PTR-RSPE-TMB-RECT2', 0)
	# RECTIFIER 3 - OFF
	pushSeqCmd(dt, 'ELEC_INTERFACE.PTR-RSPE-TMB-RECT3', 0)
	# GENERATOR 1 - OFF
	pushSeqCmd(dt, 'ELEC_INTERFACE.PTR-EEP-TMB-GEN1', 0)
	# GENERATOR 2 - OFF
	pushSeqCmd(dt, 'ELEC_INTERFACE.PTR-EEP-TMB-GEN2', 0)

	# Twist grip to min (DECR)
	# THROTTLE - MINIMUM (LEFT)
	pushSeqCmd(dt, 'scriptSimCommand', 'iCommandThrottleDecrease') # Correction lever decrease (PgDn)
	pushSeqCmd(2, 'scriptSimCommand', 'iCommandThrottleStop') # Hold down for 2 seconds

	# Wait 1m10s for rotor to come down to idle RPM (70%)
	# FIXME Monitor arg.RotorRPM, 0.645 = 75% rpm, 0.130 = 15% rpm
	pushSeqCmd(dt, 'scriptSpeech', 'Waiting for rotor to reach idle RPM, 70%')
	pushSeqCmd(1 * 60 + 10, '', '', 'Rotor at 70% RPM')

	# LEFT ENGINE FUEL SHUTOFF LEVER - CLOSE
	pushSeqCmd(dt, 'ENGINE_INTERFACE.PTR-ENGSTOP-ARM-L', 0)
	# RIGHT ENGINE FUEL SHUTOFF LEVER - CLOSE
	pushSeqCmd(dt, 'ENGINE_INTERFACE.PTR-ENGSTOP-ARM-R', 0)

	# Wait 2m40s for rotor to come down to 15% RPM.
	pushSeqCmd(dt, 'scriptSpeech', 'Waiting for rotor to reach 15% RPM')
	pushSeqCmd(1 * 60 + 40, '', '', 'Rotor at 15% RPM')

	# ROTOR BRAKE - ON
	pushSeqCmd(dt, 'ENGINE_INTERFACE.PTR-VINTBRAKE-ARM', 1)

	# LEFT SHUTOFF VALVE - OFF
	pushSeqCmd(dt, 'FUELSYS_INTERFACE.PTR-CPE-CVR-PUMP-L', 1) # switch cover
	pushSeqCmd(dt, 'FUELSYS_INTERFACE.PTR-CPE-TMB-PUMP-L', 0) # switch
	pushSeqCmd(dt, 'FUELSYS_INTERFACE.PTR-CPE-CVR-PUMP-L', 0) # switch cover

	# RIGHT SHUTOFF VALVE - OFF
	pushSeqCmd(dt, 'FUELSYS_INTERFACE.PTR-CPE-CVR-PUMP-R', 1) # switch cover
	pushSeqCmd(dt, 'FUELSYS_INTERFACE.PTR-CPE-TMB-PUMP-R', 0) # switch # NOTE Spelling error in command, "FUELSYS_INTERFACE.PTR-CPE-TMB-PUMP-R" is the correct spelling for the command.
	pushSeqCmd(dt, 'FUELSYS_INTERFACE.PTR-CPE-CVR-PUMP-R', 0) # switch cover

	# SERVICE TANK PUMP - OFF
	pushSeqCmd(dt, 'FUELSYS_INTERFACE.PTR-CPE-TMB-PUMP-RATE', 0)
	# LEFT TANK PUMP - OFF
	pushSeqCmd(dt, 'FUELSYS_INTERFACE.PTR-CPE-TMB-PUMPTNK-L', 0)
	# RIGHT TANK PUMP - OFF
	pushSeqCmd(dt, 'FUELSYS_INTERFACE.PTR-CPE-TMB-PUMPTNK-R', 0) # NOTE Spelling error in command, "FUELSYS_INTERFACE.PTR-CPE-TMB-PUMPTNK-R" is the correct spelling for the command.

	# FIRE EXTINGUISHER - OFF
	pushSeqCmd(dt, 'FIRE_EXTING_INTERFACE.PTR-CPE-TMB-CONTR-FIRE', 0)

	# R-828 radio
	# R-828 RADIO POWER - OFF
	pushSeqCmd(dt, 'R_828.PTR-ADDSECPLT-TMB-P828', 0)

	# UV-26 countermeasures system
	# UV-26 POWER - OFF
	pushSeqCmd(dt, 'UV_26.PTR-UV26-ONOFF', 0)

	# All circuit breakers off
	# Group 1
	pushSeqCmd(dt, 'ELEC_INTERFACE.PTR-LAZS-TMB-BV-ZSBR', 0)
	pushSeqCmd(dt, 'ELEC_INTERFACE.PTR-LAZS-TMB-BV-DIR', 0)
	pushSeqCmd(dt, 'ELEC_INTERFACE.PTR-LAZS-TMB-BV-EQU', 0)
	pushSeqCmd(dt, 'ELEC_INTERFACE.PTR-LAZS-TMB-RSGUV-WARM', 0)
	pushSeqCmd(dt, 'ELEC_INTERFACE.PTR-LAZS-TMB-BV-EXP', 0)
	pushSeqCmd(dt, 'ELEC_INTERFACE.PTR-LAZS-TMB-RSGUV-FIRE', 0)
	pushSeqCmd(dt, 'ELEC_INTERFACE.PTR-LAZS-TMB-RSGUV-SIGN', 0)

	# Group 2
	pushSeqCmd(dt, 'ELEC_INTERFACE.PTR-LAZS-TMB-311', 0)
	pushSeqCmd(dt, 'ELEC_INTERFACE.PTR-LAZS-TMB-GUOUTL-622L', 0)
	pushSeqCmd(dt, 'ELEC_INTERFACE.PTR-LAZS-TMB-GUOUTL-622R', 0)
	pushSeqCmd(dt, 'ELEC_INTERFACE.PTR-LAZS-TMB-GUOUTR-622L', 0)
	pushSeqCmd(dt, 'ELEC_INTERFACE.PTR-LAZS-TMB-GUOUTR-622R', 0)
	pushSeqCmd(dt, 'ELEC_INTERFACE.PTR-LAZS-TMB-GUOUT-800L', 0)
	pushSeqCmd(dt, 'ELEC_INTERFACE.PTR-LAZS-TMB-GUOUT-800R', 0)

	# Group 3
	pushSeqCmd(dt, 'ELEC_INTERFACE.PTR-LAZS-TMB-ES-800L', 0)
	pushSeqCmd(dt, 'ELEC_INTERFACE.PTR-LAZS-TMB-ES-622R', 0)
	pushSeqCmd(dt, 'ELEC_INTERFACE.PTR-LAZS-TMB-JETEXPL', 0)
	pushSeqCmd(dt, 'ELEC_INTERFACE.PTR-LAZS-TMB-JETBOMB', 0)
	pushSeqCmd(dt, 'ELEC_INTERFACE.PTR-LAZS-TMB-JETPWR', 0)
	pushSeqCmd(dt, 'ELEC_INTERFACE.PTR-LAZS-TMB-PKT', 0)
	pushSeqCmd(dt, 'ELEC_INTERFACE.PTR-LAZS-TMB-JETRCKT', 0)

	# Group 4
	pushSeqCmd(dt, 'ELEC_INTERFACE.PTR-RAZS-TMB-START-TRBIGN', 0)
	pushSeqCmd(dt, 'ELEC_INTERFACE.PTR-RAZS-TMB-START-TRBON', 0)
	pushSeqCmd(dt, 'ELEC_INTERFACE.PTR-SW-LOCKER-BASE', 0)
	pushSeqCmd(dt, 'ELEC_INTERFACE.PTR-SW-LOCKER-RES', 0)
	pushSeqCmd(dt, 'ELEC_INTERFACE.PTR-RAZS-TMB-START-ENGIGN', 0)
	pushSeqCmd(dt, 'ELEC_INTERFACE.PTR-RAZS-TMB-START-ENGON', 0)
	pushSeqCmd(dt, 'ELEC_INTERFACE.PTR-NONAME', 0)
	pushSeqCmd(dt, 'ELEC_INTERFACE.PTR-RAZS-TMB-RPM', 0)
	pushSeqCmd(dt, 'ELEC_INTERFACE.PTR-RAZS-TMB-TURN', 0)

	# Group 5
	pushSeqCmd(dt, 'ELEC_INTERFACE.PTR-RAZS-TMB-TSCOCK-ON', 0)
	pushSeqCmd(dt, 'ELEC_INTERFACE.PTR-RAZS-TMB-TSPMP-C', 0)
	pushSeqCmd(dt, 'ELEC_INTERFACE.PTR-RAZS-TMB-TSPMP-L', 0)
	pushSeqCmd(dt, 'ELEC_INTERFACE.PTR-RAZS-TMB-TSCOCK-L', 0)
	pushSeqCmd(dt, 'ELEC_INTERFACE.PTR-RAZS-TMB-TSCOUNT', 0)
	pushSeqCmd(dt, 'ELEC_INTERFACE.PTR-RAZS-TMB-TSPMP-R', 0)
	pushSeqCmd(dt, 'ELEC_INTERFACE.PTR-RAZS-TMB-TSCOCK-R', 0)
	pushSeqCmd(dt, 'ELEC_INTERFACE.PTR-RAZS-TMB-SPPU52', 0)
	pushSeqCmd(dt, 'ELEC_INTERFACE.PTR-RAZS-TMB-T819', 0)

	# Group 6
	pushSeqCmd(dt, 'ELEC_INTERFACE.PTR-RAZS-TMB-ANO', 0)
	pushSeqCmd(dt, 'ELEC_INTERFACE.PTR-RAZS-TMB-LAMPTEST', 0)
	pushSeqCmd(dt, 'ELEC_INTERFACE.PTR-RAZS-TMB-HLGT-DIR-L', 0)
	pushSeqCmd(dt, 'ELEC_INTERFACE.PTR-RAZS-TMB-HLGT-ON-L', 0)
	pushSeqCmd(dt, 'ELEC_INTERFACE.PTR-RAZS-TMB-HLGT-DIR-R', 0)
	pushSeqCmd(dt, 'ELEC_INTERFACE.PTR-RAZS-TMB-HLGT-ON-R', 0)
	pushSeqCmd(dt, 'ELEC_INTERFACE.PTR-SW-LIGHT-PRF4-LEFT', 0)
	pushSeqCmd(dt, 'ELEC_INTERFACE.PTR-SW-LIGHT-PRF4-RIGHT', 0)
	pushSeqCmd(dt, 'ELEC_INTERFACE.PTR-RAZS-TMB-WNGLGT', 0)

	# Group 7
	pushSeqCmd(dt, 'ELEC_INTERFACE.PTR-RAZS-TMB-RADRS', 0)
	pushSeqCmd(dt, 'ELEC_INTERFACE.PTR-RAZS-TMB-RADALT', 0)
	pushSeqCmd(dt, 'ELEC_INTERFACE.PTR-RAZS-TMB-APELCT', 0)
	pushSeqCmd(dt, 'ELEC_INTERFACE.PTR-RAZS-TMB-APFRICT', 0)
	pushSeqCmd(dt, 'ELEC_INTERFACE.PTR-RAZS-TMB-APMAIN', 0)
	pushSeqCmd(dt, 'ELEC_INTERFACE.PTR-RAZS-TMB-GSDBL', 0)
	pushSeqCmd(dt, 'ELEC_INTERFACE.PTR-RAZS-TMB-GSMAIN', 0)
	pushSeqCmd(dt, 'ELEC_INTERFACE.PTR-RAZS-TMB-RADCOMM', 0)
	pushSeqCmd(dt, 'ELEC_INTERFACE.PTR-RAZS-TMB-RADSPU', 0)

	# Group 8
	pushSeqCmd(dt, 'ELEC_INTERFACE.PTR-RAZS-TMB-RADCMP-SV', 0)
	pushSeqCmd(dt, 'ELEC_INTERFACE.PTR-RAZS-TMB-RADCMP-UKV', 0)
	pushSeqCmd(dt, 'ELEC_INTERFACE.PTR-RAZS-TMB-RADDISS', 0)
	pushSeqCmd(dt, 'ELEC_INTERFACE.PTR-RAZS-TMB-PPSQUE1-L', 0)
	pushSeqCmd(dt, 'ELEC_INTERFACE.PTR-RAZS-TMB-PPSQUE1-R', 0)
	pushSeqCmd(dt, 'ELEC_INTERFACE.PTR-RAZS-TMB-PPSQUE2-L', 0)
	pushSeqCmd(dt, 'ELEC_INTERFACE.PTR-RAZS-TMB-PPSQUE2-R', 0)
	pushSeqCmd(dt, 'ELEC_INTERFACE.PTR-RAZS-TMB-PPSSIGN', 0)
	pushSeqCmd(dt, 'ELEC_INTERFACE.PTR-RAZS-TMB-RADRNTG', 0)

	# Group 9
	pushSeqCmd(dt, 'ELEC_INTERFACE.PTR-RAZS-TMB-POSDIR', 0)
	pushSeqCmd(dt, 'ELEC_INTERFACE.PTR-RAZS-TMB-POSGLS', 0)
	pushSeqCmd(dt, 'ELEC_INTERFACE.PTR-RAZS-TMB-POSPZUENG-L', 0)
	pushSeqCmd(dt, 'ELEC_INTERFACE.PTR-RAZS-TMB-POSPZUENG-R', 0)
	pushSeqCmd(dt, 'ELEC_INTERFACE.PTR-RAZS-TMB-POSRIO3', 0)
	pushSeqCmd(dt, 'ELEC_INTERFACE.PTR-RAZS-TMB-KO50', 0)
	pushSeqCmd(dt, 'ELEC_INTERFACE.PTR-RAZS-TMB-L1800', 0)
	pushSeqCmd(dt, 'ELEC_INTERFACE.PTR-RAZS-TMB-WIPER-L', 0)
	pushSeqCmd(dt, 'ELEC_INTERFACE.PTR-RAZS-TMB-WIPER-R', 0)

	# BATTERY 1 - OFF
	pushSeqCmd(dt, 'ELEC_INTERFACE.PTR-RSPE-TMB-AKK1', 0)
	# BATTERY 2 - OFF
	pushSeqCmd(dt, 'ELEC_INTERFACE.PTR-RSPE-TMB-AKK2', 0)
	# 115V INVERTER - OFF
	pushSeqCmd(dt, 'ELEC_INTERFACE.PTR-EEP-TMB-PO', 1) # 0 = AUTO, 1 = OFF, 2 = MAN
	# 36V INVERTER - OFF
	pushSeqCmd(dt, 'ELEC_INTERFACE.PTR-EEP-TMB-PT', 1) # 0 = AUTO, 1 = OFF, 2 = MAN

	# DC VOLTMETER SELECTOR - OFF
	pushSeqCmd(dt, 'ELEC_INTERFACE.PTR-RSPE-LVR-FEEDMODE', 0)
	# AC VOLTMETER SELECTOR - OFF
	pushSeqCmd(dt, 'ELEC_INTERFACE.PTR-EEP-LVR-MODE', 0)

	return seq
