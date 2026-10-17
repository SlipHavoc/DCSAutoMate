# Return a Dictionary of script data.  The 'scripts' key is a list of scripts that users will be selecting from.  Each script has an associated 'function', which is the name of the function in this file that will be called to generate the command sequence, and a dictionary of 'vars' that the user will be prompted to choose from before running the script, and will be passed into the sequence generating function.
def getScriptData():
	return {
		'moduleName': 'A-10C',
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
				},
			},
			{
				'name': 'Air Start',
				'function': 'AirStart',
				'vars': {
					'time': {
						'label': 'Time',
						'options': {
							'day': 'Day',
							'night': 'Night',
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
	pushSeqCmd(dt, 'scriptSpeech', 'Set throttle to minimum.')

	# BATTERY PWR switch - On (right console forward outboard)
	pushSeqCmd(dt, 'ELEC_INTERFACE.PTR-EPP-BATTERY-PWR', 1)

	# INVERTER switch - STBY (right console forward outboard)
	pushSeqCmd(dt, 'ELEC_INTERFACE.PTR-EPP-INVERTER', 2) # 0 = TEST, 1 = OFF, 2 = STBY

	# APU switch - START (left console inboard next to throttle)
	pushSeqCmd(dt, 'ENGINE_SYSTEM.PTR-APU-START', 1)

	# Canopy - Close
	pushSeqCmd(dt, 'CPT_MECH.PTR-CANOPY-OPEN', 0) # 0 = CLOSE, 1 = HOLD, 2 = OPEN
	pushSeqCmd(7, 'CPT_MECH.PTR-CANOPY-OPEN', 1) # 0 = CLOSE, 1 = HOLD, 2 = OPEN

	# APU started
	pushSeqCmd(dt, 'scriptCockpitState', control='A-10C/arg.APU_RPM', value=0.830, condition='>=', duration=3) # 0.834 is 100%

	# APU GEN switch - PWR (right console forward outboard)
	pushSeqCmd(dt, 'ELEC_INTERFACE.PTR-EPP-APU-GEN-PWR', 1)

	# CDU switch - ON (right console middle inboard)
	pushSeqCmd(dt, 'AAP.PTR-TMB-CDU-SWITCH', 1)

	# EGI switch - ON (right console middle inboard)
	pushSeqCmd(dt, 'AAP.PTR-TMB-EGI-SWITCH', 1)
	# Alignment starts, takes 4m0s

	# Lights
	if vars.get('time') == 'day':
		# Internal lights
		# FLT INST knob
		pushSeqCmd(dt, 'LIGHT_SYSTEM.PTR-LGHTCP-FLIGHT-INST', 1.0)
		# AUX INST knob
		pushSeqCmd(dt, 'LIGHT_SYSTEM.PTR-LGHTCP-AUX-INST', 1.0)
		# ENG INST knob
		pushSeqCmd(dt, 'LIGHT_SYSTEM.PTR-LGHTCP-ENG-INST', 1.0)
		# CONSOLE knob
		pushSeqCmd(dt, 'LIGHT_SYSTEM.PTR-LGHTCP-CONSOLE', 1.0)
		# ACCEL&COMP switch
		pushSeqCmd(dt, 'LIGHT_SYSTEM.PTR-LGHTCP-ACCEL-COMP', 1.0)
		# HUD MODE switch - DAY (instrument panel left lower)
		pushSeqCmd(dt, 'AHCP.PNT-TMB-AHCP-TIME', 1) # 0 = NIGHT, 1 = DAY
		# External lights
		# Anticollision light - OFF
		pushSeqCmd(dt, 'LIGHT_SYSTEM.PTR-LGHTCP-ANTICOLLISION', 0)
		# Position lights - OFF
		pushSeqCmd(dt, 'LIGHT_SYSTEM.PTR-LGHTCP-POSITION', 1) # 0 = STEADY, 1 = OFF, 2 = FLASH
	else:
		# Internal lights
		# FLT INST knob
		pushSeqCmd(dt, 'LIGHT_SYSTEM.PTR-LGHTCP-FLIGHT-INST', 0.5)
		# AUX INST knob
		pushSeqCmd(dt, 'LIGHT_SYSTEM.PTR-LGHTCP-AUX-INST', 0.5)
		# ENG INST knob
		pushSeqCmd(dt, 'LIGHT_SYSTEM.PTR-LGHTCP-ENG-INST', 0.5)
		# CONSOLE knob
		pushSeqCmd(dt, 'LIGHT_SYSTEM.PTR-LGHTCP-CONSOLE', 0.5)
		# ACCEL&COMP switch
		pushSeqCmd(dt, 'LIGHT_SYSTEM.PTR-LGHTCP-ACCEL-COMP', 0.5)
		# HUD MODE switch - NIGHT (instrument panel left lower)
		pushSeqCmd(dt, 'AHCP.PNT-TMB-AHCP-TIME', 0) # 0 = NIGHT, 1 = DAY
		# External lights
		# Anticollision light - OFF
		pushSeqCmd(dt, 'LIGHT_SYSTEM.PTR-LGHTCP-ANTICOLLISION', 0)
		# Position lights - OFF
		pushSeqCmd(dt, 'LIGHT_SYSTEM.PTR-LGHTCP-POSITION', 1) # 0 = STEADY, 1 = OFF, 2 = FLASH

	# Fuel display knob
	pushSeqCmd(dt, 'FUEL_SYSTEM.PTR-FQIS-SELECT', 0) # 0 = INT, 1 = MAIN, 2 = WING, 3 = EXT WING, 4 = EXT CTR

	# ARC-186(V) VHF AM radio (left console inboard, forward radio in stack)
	# Knob - TR
	pushSeqCmd(dt, 'VHF_AM_RADIO.PTR-ANARC186-VHFAM-FREQEMER-CONTROL', 1) # 0 = OFF, 1 = TR, 2 = DF

	# ARC-164 UHF radio (left console inboard, middle radio in stack)
	# Knob - MAIN
	pushSeqCmd(dt, 'UHF_RADIO.PTR-ANARC164-FUNCTION', 1) # 0 = OFF, 1 = MAIN, 2 = BOTH, 3 = ADF

	# ARC-186(V) VHF FM radio (left console inboard, aft radio in stack)
	# Knob - TR
	pushSeqCmd(dt, 'VHF_FM_RADIO.PTR-ANARC186-VHFFM-MODE', 1) # 0 = OFF, 1 = TR, 2 = DF

	if vars.get('time') == 'day':
		# Left/Right MFDs - DAY
		pushSeqCmd(dt, 'MFCD_LEFT.PNT-LVR-MFD-L', 2) # 0 = OFF, 1 = NT, 2 = DAY
		pushSeqCmd(dt, 'MFCD_RIGHT.PNT-LVR-MFD-R', 2) # 0 = OFF, 1 = NT, 2 = DAY
	else:
		# Left/Right MFDs - NIGHT
		pushSeqCmd(dt, 'MFCD_LEFT.PNT-LVR-MFD-L', 1) # 0 = OFF, 1 = NT, 2 = DAY
		pushSeqCmd(dt, 'MFCD_RIGHT.PNT-LVR-MFD-R', 1) # 0 = OFF, 1 = NT, 2 = DAY

	# CICU switch - ON (instrument panel lower left)
	pushSeqCmd(dt, 'AHCP.PNT-TMB-AHCP-CICU', 1)
	# CICU ON starts the MFDs starting up.
	# NOTE MFDs take 45 seconds to start.

	# Left engine - IDLE (RAlt-Home)
	pushSeqCmd(dt, 'scriptSimCommand', 'iCommandLeftEngineStart') # Left throttle IDLE
	# After a few seconds, the ENG START CYCLE light will come on.  When it goes out, the engine is started.
	pushSeqCmd(dt, '', '', 'If ENG START CYCLE light does not go out, advance throttle slightly and wait 10 seconds.') # In cold conditions (below 5 deg C), the ENG START CYCLE light may not go out.  This is a reported bug as of 2025-02-16.
	pushSeqCmd(5, 'scriptCockpitState', control='A-10C/arg.flag_ENG_START_CYCLE', value=0) # ENG START CYCLE light goes out.

	# APU GEN switch - OFF (right console forward outboard)
	pushSeqCmd(dt, 'ELEC_INTERFACE.PTR-EPP-APU-GEN-PWR', 0)

	# Master Caution - Reset
	#pushSeqCmd(dt, 'UFC.PNT-BTN-UFC-MASTER-CAUTION', 1) # Press
	#pushSeqCmd(dt, 'UFC.PNT-BTN-UFC-MASTER-CAUTION', 0) # Release

	# Right engine - IDLE (RCtrl-Home)
	pushSeqCmd(dt, 'scriptSimCommand', 'iCommandRightEngineStart') # Right throttle IDLE
	# After a few seconds, the ENG START CYCLE light will come on.  When it goes out, the engine is started.
	pushSeqCmd(dt, '', '', 'If ENG START CYCLE light does not go out, advance throttle slightly and wait 10 seconds.') # In cold conditions (below 5 deg C), the ENG START CYCLE light may not go out.  This is a reported bug as of 2025-02-16.
	pushSeqCmd(5, 'scriptCockpitState', control='A-10C/arg.flag_ENG_START_CYCLE', value=0) # ENG START CYCLE light goes out.

	# APU switch - OFF (left console inboard next to throttle)
	pushSeqCmd(dt, 'ENGINE_SYSTEM.PTR-APU-START', 0)

	# Go to CDU page on right MFD
	pushSeqCmd(dt, 'MFCD_RIGHT.PNT-BTN-MFD-R-13', 1) # CDU
	pushSeqCmd(dt, 'MFCD_RIGHT.PNT-BTN-MFD-R-13', 0) # Release

	# JTRS switch - ON (instrument panel lower left)
	pushSeqCmd(dt, 'AHCP.PNT-TMB-AHCP-JTRS', 1)

	# IFFCC switch - ON (instrument panel lower left)
	pushSeqCmd(dt, 'AHCP.PNT-TMB-AHCP-IFFCC', 2) # 0 = OFF, 1 = TEST, 2 = ON

	# PITOT HEAT switch - On (right console middle outboard
	pushSeqCmd(dt, 'ENVIRONMENT_SYSTEM.PTR-ENVCP-PITOT-HEAT', 1)

	# Backup ADI - Uncage and center (instrument panel lower left)
	pushSeqCmd(dt, 'SAI.PNT-LVR-SAI-CAGE_arg66', 0.5) # Move the SAI down twice to different values to get it to uncage.
	pushSeqCmd(dt, 'SAI.PNT-LVR-SAI-CAGE_arg66', 0.4) # 0.4 is centered on the horizon line.

	# PITCH and YAW L/R SAS switches - ON (right console forward outboard)
	pushSeqCmd(dt, 'AUTOPILOT.PTR-SASP-PITCH-SASENGAGE-L', 1)
	pushSeqCmd(dt, 'AUTOPILOT.PTR-SASP-PITCH-SASENGAGE-R', 1)
	pushSeqCmd(dt, 'AUTOPILOT.PTR-SASP-YAW-SASENGAGE-L', 1)
	pushSeqCmd(dt, 'AUTOPILOT.PTR-SASP-YAW-SASENGAGE-R', 1)

	# T/O TRIM button - Press for 1-2 seconds
	pushSeqCmd(dt, 'AUTOPILOT.PTR-SASP-TO-TRIM', 1) # Press
	pushSeqCmd(2, 'AUTOPILOT.PTR-SASP-TO-TRIM', 0) # Release after 2 seconds

	# CMS MODE knob - MAN (right console forward inboard)
	pushSeqCmd(dt, 'CMSP.PNT-LEV-CMSP-MODE', 2) # 0 = OFF, 1 = STBY, 2 = MAN, 3 = SEMI, 4 = AUTO

	# MWS, JMR, RWR, DISP switches - ON (middle position) (right console forward inboard)
	pushSeqCmd(dt, 'CMSP.PNT-TMB-CMSP-MWS', 1)
	pushSeqCmd(dt, 'CMSP.PNT-TMB-CMSP-JMR', 1)
	pushSeqCmd(dt, 'CMSP.PNT-TMB-CMSP-RWR', 1)
	pushSeqCmd(dt, 'CMSP.PNT-TMB-CMSP-DISP', 1)

	# ANTI-SKID switch - ON (instrument panel lower left, above gear lever)
	pushSeqCmd(dt, 'AUTOPILOT.PTR-ANTI-SKID', 1)

	# IFF MASTER knob - NORM
	pushSeqCmd(dt, 'IFF.PTR-IFFCP-MASTER', 3) # 0 = OFF, 1 = STBY, 2 = LOW, 3 = NORM, 4 = EMER
	# IFF MODE 4 switch - ON
	pushSeqCmd(dt, 'IFF.PTR-IFFCP-ON-OUT', 1) # 0 = OUT, 1 = ON

	# MASTER ARM switch - ARM
	pushSeqCmd(dt, 'AHCP.PNT-TMB-AHCP-MARM', 2) # 0 = TRAIN, 1 = SAFE, 2 = ARM

	# GUN PAC switch - ARM
	pushSeqCmd(dt, 'AHCP.PNT-TMB-AHCP-GUNPAC', 2) # 0 = GUNARM, 1 = SAFE, 2 = ARM

	# Laser arm switch - ARM
	pushSeqCmd(dt, 'AHCP.PNT-TMB-AHCP-LARM', 2) # 0 = TRAIN, 1 = SAFE, 2 = ARM

	# TGP switch - ON
	pushSeqCmd(dt, 'AHCP.PNT-TMB-AHCP-TGP', 1)

	## DTS LOAD ALL - Left MFD R5 OSB (PB11)
	#pushSeqCmd(dt, 'MFCD_LEFT.PNT-BTN-MFD-L-11', 1) # LOAD ALL
	#pushSeqCmd(dt, 'MFCD_LEFT.PNT-BTN-MFD-L-11', 0) # Release
	#pushSeqCmd(15, '', '', 'DTS loaded')

	## Go to TAD page on left MFD
	#pushSeqCmd(dt, 'MFCD_LEFT.PNT-BTN-MFD-L-15', 1) # LOAD ALL
	#pushSeqCmd(dt, 'MFCD_LEFT.PNT-BTN-MFD-L-15', 0) # Release

	# Wait for INS aligmment to complete.
	pushSeqCmd(dt, 'scriptCockpitState', control='A-10C/ind.3.AlignTime', value='4.0') # CDU Line 7 (0-indexed) or Line 8 (1-indexed) is '   T=   4.0 0.8         '
	pushSeqCmd(dt, 'scriptCockpitState', control='A-10C/ind.3.EstimatedDrift', value='0.8') # CDU Line 7 (0-indexed) or Line 8 (1-indexed) is '   T=   4.0 0.8         '
	pushSeqCmd(dt, 'scriptSpeech', 'I N S alignment complete')

	#######################
	# After INS alignment complete...
	#######################

	# Press NAV on CDU page
	pushSeqCmd(dt, 'CDU.PNT-BTN-CDU-ARW-R3', 1) # Press
	pushSeqCmd(dt, 'CDU.PNT-BTN-CDU-ARW-R3', 0) # Release

	# EGI NAV MODE button - Press (instrument panel bottom center)
	pushSeqCmd(dt, 'NMSP.PTR-NMSP-EGI', 1)
	pushSeqCmd(dt, 'NMSP.PTR-NMSP-EGI', 0)

	# EAC switch - ARM (left console middle inboard, right behind throttle) # NOTE Pitch and Yaw SAS must be ON, and EGI NAV mode button must be enabled, in order to arm EAC.
	pushSeqCmd(dt, 'AUTOPILOT.PTR-LCP-EAC', 1)

	# CDI STEER PT knob - FLIGHT PLAN (right console middle inboard)
	pushSeqCmd(dt, 'AAP.PNT-LVR-STEER-PT-SEL-SWITCH', 0) # 0 = FLT PLAN, 1 = MARK, 2 = MISSION

	# CDI PAGE knob - STEER (right console middle inboard)
	pushSeqCmd(dt, 'AAP.PNT-LEV-PAGE-SEL-SWITCH', 2) # 0 = OTHER, 1 = POSITION, 2 = STEER, 3 = WAYPT

	# Ejection seat - ARM
	pushSeqCmd(dt, 'CPT_MECH.PTR-ARM-SEAT-HANDLE', 0) # 0 = ARM, 1 = SAFE

	pushSeqCmd(dt, 'scriptSpeech', "Manual steps remaining: LOAD page load all.  Set lights.  Tune radios.")

	return seq


def HotStart(config, vars, helper, *args, **kwargs):
	seq = []
	dt = 0.3

	pushSeqCmd = helper.makePushSeqCmd(seq)

	pushSeqCmd(0, '', '', "Running Hot Start sequence")

	# Lights
	if vars.get('time') == 'day':
		# Internal lights
		# FLT INST knob
		pushSeqCmd(dt, 'LIGHT_SYSTEM.PTR-LGHTCP-FLIGHT-INST', 1.0)
		# AUX INST knob
		pushSeqCmd(dt, 'LIGHT_SYSTEM.PTR-LGHTCP-AUX-INST', 1.0)
		# ENG INST knob
		pushSeqCmd(dt, 'LIGHT_SYSTEM.PTR-LGHTCP-ENG-INST', 1.0)
		# CONSOLE knob
		pushSeqCmd(dt, 'LIGHT_SYSTEM.PTR-LGHTCP-CONSOLE', 1.0)
		# ACCEL&COMP switch
		pushSeqCmd(dt, 'LIGHT_SYSTEM.PTR-LGHTCP-ACCEL-COMP', 1.0)
		# HUD MODE switch - DAY (instrument panel left lower)
		pushSeqCmd(dt, 'AHCP.PNT-TMB-AHCP-TIME', 1) # 0 = NIGHT, 1 = DAY
		# External lights
		# Anticollision light - OFF
		pushSeqCmd(dt, 'LIGHT_SYSTEM.PTR-LGHTCP-ANTICOLLISION', 0)
		# Position lights - OFF
		pushSeqCmd(dt, 'LIGHT_SYSTEM.PTR-LGHTCP-POSITION', 1) # 0 = STEADY, 1 = OFF, 2 = FLASH
	else:
		# Internal lights
		# FLT INST knob
		pushSeqCmd(dt, 'LIGHT_SYSTEM.PTR-LGHTCP-FLIGHT-INST', 0.5)
		# AUX INST knob
		pushSeqCmd(dt, 'LIGHT_SYSTEM.PTR-LGHTCP-AUX-INST', 0.5)
		# ENG INST knob
		pushSeqCmd(dt, 'LIGHT_SYSTEM.PTR-LGHTCP-ENG-INST', 0.5)
		# CONSOLE knob
		pushSeqCmd(dt, 'LIGHT_SYSTEM.PTR-LGHTCP-CONSOLE', 0.5)
		# ACCEL&COMP switch
		pushSeqCmd(dt, 'LIGHT_SYSTEM.PTR-LGHTCP-ACCEL-COMP', 0.5)
		# HUD MODE switch - NIGHT (instrument panel left lower)
		pushSeqCmd(dt, 'AHCP.PNT-TMB-AHCP-TIME', 0) # 0 = NIGHT, 1 = DAY
		# External lights
		# Anticollision light - OFF
		pushSeqCmd(dt, 'LIGHT_SYSTEM.PTR-LGHTCP-ANTICOLLISION', 0)
		# Position lights - OFF
		pushSeqCmd(dt, 'LIGHT_SYSTEM.PTR-LGHTCP-POSITION', 1) # 0 = STEADY, 1 = OFF, 2 = FLASH

	# Fuel display knob
	pushSeqCmd(dt, 'FUEL_SYSTEM.PTR-FQIS-SELECT', 0) # 0 = INT, 1 = MAIN, 2 = WING, 3 = EXT WING, 4 = EXT CTR

	# T/O TRIM button - Press for 1-2 seconds
	pushSeqCmd(dt, 'AUTOPILOT.PTR-SASP-TO-TRIM', 1) # Press
	pushSeqCmd(2, 'AUTOPILOT.PTR-SASP-TO-TRIM', 0) # Release after 2 seconds

	# CMS MODE knob - MAN (right console forward inboard)
	pushSeqCmd(dt, 'CMSP.PNT-LEV-CMSP-MODE', 2) # 0 = OFF, 1 = STBY, 2 = MAN, 3 = SEMI, 4 = AUTO

	# IFF MASTER knob - NORM
	pushSeqCmd(dt, 'IFF.PTR-IFFCP-MASTER', 3) # 0 = OFF, 1 = STBY, 2 = LOW, 3 = NORM, 4 = EMER
	# IFF MODE 4 switch - ON
	pushSeqCmd(dt, 'IFF.PTR-IFFCP-ON-OUT', 1) # 0 = OUT, 1 = ON

	# MASTER ARM switch - ARM
	pushSeqCmd(dt, 'AHCP.PNT-TMB-AHCP-MARM', 2) # 0 = TRAIN, 1 = SAFE, 2 = ARM

	# GUN PAC switch - ARM
	pushSeqCmd(dt, 'AHCP.PNT-TMB-AHCP-GUNPAC', 2) # 0 = GUNARM, 1 = SAFE, 2 = ARM

	# Laser arm switch - ARM
	pushSeqCmd(dt, 'AHCP.PNT-TMB-AHCP-LARM', 2) # 0 = TRAIN, 1 = SAFE, 2 = ARM

	# TGP switch - ON
	pushSeqCmd(dt, 'AHCP.PNT-TMB-AHCP-TGP', 1)

	# Press NAV on CDU page
	pushSeqCmd(dt, 'CDU.PNT-BTN-CDU-ARW-R3', 1) # Press
	pushSeqCmd(dt, 'CDU.PNT-BTN-CDU-ARW-R3', 0) # Release

	# CDI STEER PT knob - FLIGHT PLAN (right console middle inboard)
	pushSeqCmd(dt, 'AAP.PNT-LVR-STEER-PT-SEL-SWITCH', 0) # 0 = FLT PLAN, 1 = MARK, 2 = MISSION

	# CDI PAGE knob - STEER (right console middle inboard)
	pushSeqCmd(dt, 'AAP.PNT-LEV-PAGE-SEL-SWITCH', 2) # 0 = OTHER, 1 = POSITION, 2 = STEER, 3 = WAYPT

	pushSeqCmd(dt, 'scriptSpeech', "Manual steps remaining: LOAD page load all.  Set lights.  Tune radios.")

	return seq


def AirStart(config, vars, helper, *args, **kwargs):
	seq = []
	dt = 0.3

	pushSeqCmd = helper.makePushSeqCmd(seq)

	pushSeqCmd(0, '', '', "Running Hot Start sequence")

	# Lights
	if vars.get('time') == 'day':
		# Internal lights
		# FLT INST knob
		pushSeqCmd(dt, 'LIGHT_SYSTEM.PTR-LGHTCP-FLIGHT-INST', 1.0)
		# AUX INST knob
		pushSeqCmd(dt, 'LIGHT_SYSTEM.PTR-LGHTCP-AUX-INST', 1.0)
		# ENG INST knob
		pushSeqCmd(dt, 'LIGHT_SYSTEM.PTR-LGHTCP-ENG-INST', 1.0)
		# CONSOLE knob
		pushSeqCmd(dt, 'LIGHT_SYSTEM.PTR-LGHTCP-CONSOLE', 1.0)
		# ACCEL&COMP switch
		pushSeqCmd(dt, 'LIGHT_SYSTEM.PTR-LGHTCP-ACCEL-COMP', 1.0)
		# HUD MODE switch - DAY (instrument panel left lower)
		pushSeqCmd(dt, 'AHCP.PNT-TMB-AHCP-TIME', 1) # 0 = NIGHT, 1 = DAY
		# External lights
		# Anticollision light - OFF
		pushSeqCmd(dt, 'LIGHT_SYSTEM.PTR-LGHTCP-ANTICOLLISION', 0)
		# Position lights - OFF
		pushSeqCmd(dt, 'LIGHT_SYSTEM.PTR-LGHTCP-POSITION', 1) # 0 = STEADY, 1 = OFF, 2 = FLASH
	else:
		# Internal lights
		# FLT INST knob
		pushSeqCmd(dt, 'LIGHT_SYSTEM.PTR-LGHTCP-FLIGHT-INST', 0.5)
		# AUX INST knob
		pushSeqCmd(dt, 'LIGHT_SYSTEM.PTR-LGHTCP-AUX-INST', 0.5)
		# ENG INST knob
		pushSeqCmd(dt, 'LIGHT_SYSTEM.PTR-LGHTCP-ENG-INST', 0.5)
		# CONSOLE knob
		pushSeqCmd(dt, 'LIGHT_SYSTEM.PTR-LGHTCP-CONSOLE', 0.5)
		# ACCEL&COMP switch
		pushSeqCmd(dt, 'LIGHT_SYSTEM.PTR-LGHTCP-ACCEL-COMP', 0.5)
		# HUD MODE switch - NIGHT (instrument panel left lower)
		pushSeqCmd(dt, 'AHCP.PNT-TMB-AHCP-TIME', 0) # 0 = NIGHT, 1 = DAY
		# External lights
		# Anticollision light - OFF
		pushSeqCmd(dt, 'LIGHT_SYSTEM.PTR-LGHTCP-ANTICOLLISION', 0)
		# Position lights - OFF
		pushSeqCmd(dt, 'LIGHT_SYSTEM.PTR-LGHTCP-POSITION', 1) # 0 = STEADY, 1 = OFF, 2 = FLASH

	# Fuel display knob
	pushSeqCmd(dt, 'FUEL_SYSTEM.PTR-FQIS-SELECT', 0) # 0 = INT, 1 = MAIN, 2 = WING, 3 = EXT WING, 4 = EXT CTR

	# CMS MODE knob - MAN (right console forward inboard)
	pushSeqCmd(dt, 'CMSP.PNT-LEV-CMSP-MODE', 2) # 0 = OFF, 1 = STBY, 2 = MAN, 3 = SEMI, 4 = AUTO

	# IFF MASTER knob - NORM
	pushSeqCmd(dt, 'IFF.PTR-IFFCP-MASTER', 3) # 0 = OFF, 1 = STBY, 2 = LOW, 3 = NORM, 4 = EMER
	# IFF MODE 4 switch - ON
	pushSeqCmd(dt, 'IFF.PTR-IFFCP-ON-OUT', 1) # 0 = OUT, 1 = ON

	# Laser arm switch - ARM
	pushSeqCmd(dt, 'AHCP.PNT-TMB-AHCP-LARM', 2) # 0 = TRAIN, 1 = SAFE, 2 = ARM

	# TGP switch - ON
	pushSeqCmd(dt, 'AHCP.PNT-TMB-AHCP-TGP', 1)

	# CDI STEER PT knob - FLIGHT PLAN (right console middle inboard)
	pushSeqCmd(dt, 'AAP.PNT-LVR-STEER-PT-SEL-SWITCH', 0) # 0 = FLT PLAN, 1 = MARK, 2 = MISSION

	# CDI PAGE knob - STEER (right console middle inboard)
	pushSeqCmd(dt, 'AAP.PNT-LEV-PAGE-SEL-SWITCH', 2) # 0 = OTHER, 1 = POSITION, 2 = STEER, 3 = WAYPT

	pushSeqCmd(dt, 'scriptSpeech', "Manual steps remaining: Set lights.  Tune radios.")

	return seq


def Shutdown(config, vars, helper, *args, **kwargs):
	seq = []
	dt = 0.3

	pushSeqCmd = helper.makePushSeqCmd(seq)

	pushSeqCmd(0, '', '', "Running Shutdown sequence")

	# Ejection seat - SAFE
	pushSeqCmd(dt, 'CPT_MECH.PTR-ARM-SEAT-HANDLE', 1) # 0 = ARM, 1 = SAFE

	# Canopy - Open
	pushSeqCmd(dt, 'CPT_MECH.PTR-CANOPY-OPEN', 2) # 0 = CLOSE, 1 = HOLD, 2 = OPEN
	pushSeqCmd(10, 'CPT_MECH.PTR-CANOPY-OPEN', 1) # NOTE: Takes longer to open than to close. # 0 = CLOSE, 1 = HOLD, 2 = OPEN

	# CDU switch - OFF (right console middle inboard)
	pushSeqCmd(dt, 'AAP.PTR-TMB-CDU-SWITCH', 0)

	# EGI switch - OFF (right console middle inboard)
	pushSeqCmd(dt, 'AAP.PTR-TMB-EGI-SWITCH', 0)

	# Lights
	# FLT INST knob
	pushSeqCmd(dt, 'LIGHT_SYSTEM.PTR-LGHTCP-FLIGHT-INST', 0)
	# AUX INST knob
	pushSeqCmd(dt, 'LIGHT_SYSTEM.PTR-LGHTCP-AUX-INST', 0)
	# ENG INST knob
	pushSeqCmd(dt, 'LIGHT_SYSTEM.PTR-LGHTCP-ENG-INST', 0)
	# CONSOLE knob
	pushSeqCmd(dt, 'LIGHT_SYSTEM.PTR-LGHTCP-CONSOLE', 0)
	# ACCEL&COMP switch
	pushSeqCmd(dt, 'LIGHT_SYSTEM.PTR-LGHTCP-ACCEL-COMP', 0)
	# HUD MODE switch - day/night (instrument panel left lower)
	pushSeqCmd(dt, 'AHCP.PNT-TMB-AHCP-TIME', 1) # 0 = NIGHT, 1 = DAY

	# ARC-186(V) VHF AM radio (left console inboard, forward radio in stack)
	# Knob - OFF
	pushSeqCmd(dt, 'VHF_AM_RADIO.PTR-ANARC186-VHFAM-FREQEMER-CONTROL', 0) # 0 = OFF, 1 = TR, 2 = DF

	# ARC-164 UHF radio (left console inboard, middle radio in stack)
	# Knob - OFF
	pushSeqCmd(dt, 'UHF_RADIO.PTR-ANARC164-FUNCTION', 0) # 0 = OFF, 1 = MAIN, 2 = BOTH, 3 = ADF

	# ARC-186(V) VHF FM radio (left console inboard, aft radio in stack)
	# Knob - OFF
	pushSeqCmd(dt, 'VHF_FM_RADIO.PTR-ANARC186-VHFFM-MODE', 0) # 0 = OFF, 1 = TR, 2 = DF

	# Left/Right MFDs - OFF
	pushSeqCmd(dt, 'MFCD_LEFT.PNT-LVR-MFD-L', 0) # 0 = OFF, 1 = NT, 2 = DAY
	pushSeqCmd(dt, 'MFCD_RIGHT.PNT-LVR-MFD-R', 0) # 0 = OFF, 1 = NT, 2 = DAY

	# CICU switch - OFF (instrument panel lower left)
	pushSeqCmd(dt, 'AHCP.PNT-TMB-AHCP-CICU', 0)

	# Left engine - OFF (RAlt-End)
	pushSeqCmd(dt, 'scriptSimCommand', 'iCommandLeftEngineStop') # Left throttle OFF

	# Right engine - OFF (RCtrl-End)
	pushSeqCmd(dt, 'scriptSimCommand', 'iCommandRightEngineStop') # Right throttle OFF

	# JTRS switch - OFF (instrument panel lower left)
	pushSeqCmd(dt, 'AHCP.PNT-TMB-AHCP-JTRS', 0)

	# IFFCC switch - OFF (instrument panel lower left)
	pushSeqCmd(dt, 'AHCP.PNT-TMB-AHCP-IFFCC', 0) # 0 = OFF, 1 = TEST, 2 = ON

	# PITOT HEAT switch - Off (right console middle outboard
	pushSeqCmd(dt, 'ENVIRONMENT_SYSTEM.PTR-ENVCP-PITOT-HEAT', 0)

	# Backup ADI - Cage (instrument panel lower left)
	pushSeqCmd(dt, 'SAI.PNT-LVR-SAI-CAGE_arg66', 1)
	pushSeqCmd(dt, 'SAI.PNT-LVR-SAI-CAGE_arg66', 0.625) # Set SAI to initial caged position.

	# PITCH and YAW L/R SAS switches - OFF (right console forward outboard)
	pushSeqCmd(dt, 'AUTOPILOT.PTR-SASP-PITCH-SASENGAGE-L', 0)
	pushSeqCmd(dt, 'AUTOPILOT.PTR-SASP-PITCH-SASENGAGE-R', 0)
	pushSeqCmd(dt, 'AUTOPILOT.PTR-SASP-YAW-SASENGAGE-L', 0)
	pushSeqCmd(dt, 'AUTOPILOT.PTR-SASP-YAW-SASENGAGE-R', 0)

	# CMS MODE knob - OFF (right console forward inboard)
	pushSeqCmd(dt, 'CMSP.PNT-LEV-CMSP-MODE', 0) # 0 = OFF, 1 = STBY, 2 = MAN, 3 = SEMI, 4 = AUTO

	# MWS, JMR, RWR, DISP switches - OFF (middle position) (right console forward inboard)
	pushSeqCmd(dt, 'CMSP.PNT-TMB-CMSP-MWS', 0)
	pushSeqCmd(dt, 'CMSP.PNT-TMB-CMSP-JMR', 0)
	pushSeqCmd(dt, 'CMSP.PNT-TMB-CMSP-RWR', 0)
	pushSeqCmd(dt, 'CMSP.PNT-TMB-CMSP-DISP', 0)

	# ANTI-SKID switch - OFF (instrument panel lower left, above gear lever)
	pushSeqCmd(dt, 'AUTOPILOT.PTR-ANTI-SKID', 0)

	# IFF MASTER knob - OFF
	pushSeqCmd(dt, 'IFF.PTR-IFFCP-MASTER', 0) # 0 = OFF, 1 = STBY, 2 = LOW, 3 = NORM, 4 = EMER
	# IFF MODE 4 switch - OUT
	pushSeqCmd(dt, 'IFF.PTR-IFFCP-ON-OUT', 0) # 0 = OUT, 1 = ON

	# MASTER ARM switch - SAFE
	pushSeqCmd(dt, 'AHCP.PNT-TMB-AHCP-MARM', 1) # 0 = TRAIN, 1 = SAFE, 2 = ARM

	# GUN PAC switch - SAFE
	pushSeqCmd(dt, 'AHCP.PNT-TMB-AHCP-GUNPAC', 1) # 0 = GUNARM, 1 = SAFE, 2 = ARM

	# Laser arm switch - SAFE
	pushSeqCmd(dt, 'AHCP.PNT-TMB-AHCP-LARM', 1) # 0 = TRAIN, 1 = SAFE, 2 = ARM

	# TGP switch - OFF
	pushSeqCmd(dt, 'AHCP.PNT-TMB-AHCP-TGP', 0)

	# EAC switch - OFF (left console middle inboard, right behind throttle) # NOTE Pitch and Yaw SAS must be ON, and EGI NAV mode button must be enabled, in order to arm EAC.
	pushSeqCmd(dt, 'AUTOPILOT.PTR-LCP-EAC', 0)

	# CDI STEER PT knob - FLIGHT PLAN (right console middle inboard)
	pushSeqCmd(dt, 'AAP.PNT-LVR-STEER-PT-SEL-SWITCH', 0) # 0 = FLT PLAN, 1 = MARK, 2 = MISSION

	# CDI PAGE knob - OTHER (right console middle inboard)
	pushSeqCmd(dt, 'AAP.PNT-LEV-PAGE-SEL-SWITCH', 0) # 0 = OTHER, 1 = POSITION, 2 = STEER, 3 = WAYPT

	# INVERTER switch - STBY (right console forward outboard)
	pushSeqCmd(dt, 'ELEC_INTERFACE.PTR-EPP-INVERTER', 2) # 0 = TEST, 1 = OFF, 2 = STBY

	# BATTERY PWR switch - OFF (right console forward outboard)
	pushSeqCmd(dt, 'ELEC_INTERFACE.PTR-EPP-BATTERY-PWR', 0)

	return seq
