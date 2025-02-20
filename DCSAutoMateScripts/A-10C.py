# Return a Dictionary of script data.  The 'scripts' key is a list of scripts that users will be selecting from.  Each script has an associated 'function', which is the name of the function in this file that will be called to generate the command sequence, and a dictionary of 'vars' that the user will be prompted to choose from before running the script, and will be passed into the sequence generating function.
def getScriptData():
	return {
		'scripts': [
			{
				'name': 'Cold Start',
				'function': 'ColdStart',
				'vars': {
					'Time': ['Day', 'Night'],
				},
			},
			{
				'name': 'Hot Start',
				'function': 'HotStart',
				'vars': {
					'Time': ['Day', 'Night'],
				},
			},
			{
				'name': 'Air Start',
				'function': 'AirStart',
				'vars': {
					'Time': ['Day', 'Night'],
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
	pushSeqCmd(dt, 'scriptSpeech', 'Set throttle to minimum.')

	# BATTERY PWR switch - On (right console forward outboard)
	pushSeqCmd(dt, 'EPP_BATTERY_PWR', 1)

	# INVERTER switch - STBY (right console forward outboard)
	pushSeqCmd(dt, 'EPP_INVERTER', 2)

	# APU switch - START (left console inboard next to throttle)
	pushSeqCmd(dt, 'ENGINE_APU_START', 1)

	# Canopy - Close
	pushSeqCmd(dt, 'CANOPY_OPEN', 0) # 0 = CLOSE, 1 = HOLD, 2 = OPEN
	pushSeqCmd(7, 'CANOPY_OPEN', 1) # 0 = CLOSE, 1 = HOLD, 2 = OPEN

	# APU started
	pushSeqCmd(dt, 'scriptCockpitState', control='A-10C/APU_RPM', value=54000, condition='>=', duration=3) # 54650 is 100%

	# APU GEN switch - PWR (right console forward outboard)
	pushSeqCmd(dt, 'EPP_APU_GEN_PWR', 1)

	# CDU switch - ON (right console middle inboard)
	pushSeqCmd(dt, 'AAP_CDUPWR', 1)

	# EGI switch - ON (right console middle inboard)
	pushSeqCmd(dt, 'AAP_EGIPWR', 1)
	# Alignment starts, takes 4m0s

	# Lights
	if vars.get('Time') == 'Day':
		# FLT INST knob
		pushSeqCmd(dt, 'LCP_FLIGHT_INST', int16())
		# AUX INST knob
		pushSeqCmd(dt, 'LCP_AUX_INST', int16())
		# ENG INST knob
		pushSeqCmd(dt, 'LCP_ENG_INST', int16())
		# CONSOLE knob
		pushSeqCmd(dt, 'LCP_CONSOLE', int16())
		# ACCEL&COMP switch
		pushSeqCmd(dt, 'LCP_ACCEL_COMP', int16())
		# HUD MODE switch - DAY (instrument panel left lower)
		pushSeqCmd(dt, 'AHCP_HUD_DAYNIGHT', 1) # 0 = NIGHT, 1 = DAY
	else:
		# FLT INST knob
		pushSeqCmd(dt, 'LCP_FLIGHT_INST', int16(0.5))
		# AUX INST knob
		pushSeqCmd(dt, 'LCP_AUX_INST', int16(0.5))
		# ENG INST knob
		pushSeqCmd(dt, 'LCP_ENG_INST', int16(0.5))
		# CONSOLE knob
		pushSeqCmd(dt, 'LCP_CONSOLE', int16(0.5))
		# ACCEL&COMP switch
		pushSeqCmd(dt, 'LCP_ACCEL_COMP', int16(0.5))
		# HUD MODE switch - NIGHT (instrument panel left lower)
		pushSeqCmd(dt, 'AHCP_HUD_DAYNIGHT', 0) # 0 = NIGHT, 1 = DAY

	# Fuel display knob
	pushSeqCmd(dt, 'FQIS_SELECT', 0) # 0 = INT, 1 = MAIN, 2 = WING, 3 = EXT WING, 4 = EXT CTR

	# ARC-186(V) VHF AM radio (left console inboard, forward radio in stack)
	# Knob - TR
	pushSeqCmd(dt, 'VHFAM_MODE', 1) # 0 = OFF, 1 = TR, 2 = DF

	# ARC-164 UHF radio (left console inboard, middle radio in stack)
	# Knob - MAIN
	pushSeqCmd(dt, 'UHF_FUNCTION', 1) # 0 = OFF, 1 = MAIN, 2 = BOTH, 3 = ADF

	# ARC-186(V) VHF FM radio (left console inboard, aft radio in stack)
	# Knob - TR
	pushSeqCmd(dt, 'VHFFM_MODE', 1) # 0 = OFF, 1 = TR, 2 = DF

	if vars.get('Time') == 'Day':
		# Left/Right MFDs - DAY
		pushSeqCmd(dt, 'LMFD_PWR', 2) # 0 = OFF, 1 = NT, 2 = DAY
		pushSeqCmd(dt, 'RMFD_PWR', 2) # 0 = OFF, 1 = NT, 2 = DAY
	else:
		# Left/Right MFDs - NIGHT
		pushSeqCmd(dt, 'LMFD_PWR', 1) # 0 = OFF, 1 = NT, 2 = DAY
		pushSeqCmd(dt, 'RMFD_PWR', 1) # 0 = OFF, 1 = NT, 2 = DAY

	# CICU switch - ON (instrument panel lower left)
	pushSeqCmd(dt, 'AHCP_CICU', 1)
	# CICU ON starts the MFDs starting up.
	# NOTE MFDs take 45 seconds to start.

	# Left engine - IDLE (RAlt-Home)
	pushSeqCmd(dt, 'scriptKeyboard', 'RAlt down')
	pushSeqCmd(dt, 'scriptKeyboard', 'home')
	pushSeqCmd(dt, 'scriptKeyboard', 'RAlt up')
	# After a few seconds, the ENG START CYCLE light will come on.  When it goes out, the engine is started.
	pushSeqCmd(dt, '', '', 'If ENG START CYCLE light does not go out, advance throttle slightly and wait 10 seconds.') # In cold conditions (below 5 deg C), the ENG START CYCLE light may not go out.  This is a reported bug as of 2025-02-16.
	pushSeqCmd(5, 'scriptCockpitState', control='A-10C/CL_A1', value=0) # ENG START CYCLE light goes out.

	# APU GEN switch - OFF (right console forward outboard)
	pushSeqCmd(dt, 'EPP_APU_GEN_PWR', 0)

	# Master Caution - Reset
	#pushSeqCmd(dt, 'UFC_MASTER_CAUTION', 1) # Press
	#pushSeqCmd(dt, 'UFC_MASTER_CAUTION', 0) # Release

	# Right engine - IDLE (RCtrl-Home)
	pushSeqCmd(dt, 'scriptKeyboard', 'RCtrl down')
	pushSeqCmd(dt, 'scriptKeyboard', 'home')
	pushSeqCmd(dt, 'scriptKeyboard', 'RCtrl up')
	# After a few seconds, the ENG START CYCLE light will come on.  When it goes out, the engine is started.
	pushSeqCmd(dt, '', '', 'If ENG START CYCLE light does not go out, advance throttle slightly and wait 10 seconds.') # In cold conditions (below 5 deg C), the ENG START CYCLE light may not go out.  This is a reported bug as of 2025-02-16.
	pushSeqCmd(5, 'scriptCockpitState', control='A-10C/CL_A1', value=0) # ENG START CYCLE light goes out.

	# APU switch - OFF (left console inboard next to throttle)
	pushSeqCmd(dt, 'ENGINE_APU_START', 0)

	# Go to CDU page on right MFD
	pushSeqCmd(dt, 'RMFD_13', 1) # CDU
	pushSeqCmd(dt, 'RMFD_13', 0) # Release

	# JTRS switch - ON (instrument panel lower left)
	pushSeqCmd(dt, 'AHCP_JTRS', 1)

	# IFFCC switch - ON (instrument panel lower left)
	pushSeqCmd(dt, 'AHCP_IFFCC', 2) # 0 = OFF, 1 = TEST, 2 = ON

	# PITOT HEAT switch - On (right console middle outboard
	pushSeqCmd(dt, 'ENVCP_PITOT_HEAT', 1)

	# Backup ADI - Uncage and center (instrument panel lower left)
	for i in range(4):
		pushSeqCmd(dt, 'SAI_PITCH_TRIM', '-3200')

	# PITCH and YAW L/R SAS switches - ON (right console forward outboard)
	pushSeqCmd(dt, 'SASP_PITCH_SAS_L', 1)
	pushSeqCmd(dt, 'SASP_PITCH_SAS_R', 1)
	pushSeqCmd(dt, 'SASP_YAW_SAS_L', 1)
	pushSeqCmd(dt, 'SASP_YAW_SAS_R', 1)

	# T/O TRIM button - Press for 1-2 seconds
	pushSeqCmd(dt, 'SASP_TO_TRIM', 1) # Press
	pushSeqCmd(2, 'SASP_TO_TRIM', 0) # Release after 2 seconds

	# CMS MODE knob - MAN (right console forward inboard)
	pushSeqCmd(dt, 'CMSP_MODE', 2) # 0 = OFF, 1 = STBY, 2 = MAN, 3 = SEMI, 4 = AUTO

	# MWS, JMR, RWR, DISP switches - ON (middle position) (right console forward inboard)
	pushSeqCmd(dt, 'CMSP_MWS', 1)
	pushSeqCmd(dt, 'CMSP_JMR', 1)
	pushSeqCmd(dt, 'CMSP_RWR', 1)
	pushSeqCmd(dt, 'CMSP_DISP', 1)

	# ANTI-SKID switch - ON (instrument panel lower left, above gear lever)
	pushSeqCmd(dt, 'ANTI_SKID_SWITCH', 1)

	# IFF MASTER knob - NORM
	pushSeqCmd(dt, 'IFF_MASTER', 3) # 0 = OFF, 1 = STBY, 2 = LOW, 3 = NORM, 4 = EMER
	# IFF MODE 4 switch - ON
	pushSeqCmd(dt, 'IFF_ON_OUT', 1) # 0 = OUT, 1 = ON

	# MASTER ARM switch - ARM
	pushSeqCmd(dt, 'AHCP_MASTER_ARM', 2) # 0 = TRAIN, 1 = SAFE, 2 = ARM

	# GUN PAC switch - ARM
	pushSeqCmd(dt, 'AHCP_GUNPAC', 2) # 0 = GUNARM, 1 = SAFE, 2 = ARM

	# Laser arm switch - ARM
	pushSeqCmd(dt, 'AHCP_LASER_ARM', 2) # 0 = TRAIN, 1 = SAFE, 2 = ARM

	# TGP switch - ON
	pushSeqCmd(dt, 'AHCP_TGP', 1)

	## DTS LOAD ALL - Left MFD R5 OSB (PB11)
	#pushSeqCmd(dt, 'LMFD_11', 1) # LOAD ALL
	#pushSeqCmd(dt, 'LMFD_11', 0) # Release
	#pushSeqCmd(15, '', '', 'DTS loaded')

	## Go to TAD page on left MFD
	#pushSeqCmd(dt, 'LMFD_15', 1) # LOAD ALL
	#pushSeqCmd(dt, 'LMFD_15', 0) # Release

	# Wait for INS aligmment to complete.
	pushSeqCmd(dt, 'scriptCockpitState', control='A-10C/CDU_LINE7', value='   T=   4.0 0.8         ') # CDU Line 7 (0-indexed) or Line 8 (1-indexed)
	pushSeqCmd(dt, 'scriptSpeech', 'I N S alignment complete')

	#######################
	# After INS alignment complete...
	#######################

	# Press NAV on CDU page
	pushSeqCmd(dt, 'CDU_LSK_7R', 1) # Press
	pushSeqCmd(dt, 'CDU_LSK_7R', 0) # Release

	# EGI NAV MODE button - Press (instrument panel bottom center)
	pushSeqCmd(dt, 'NMSP_EGI_BTN', 1)
	pushSeqCmd(dt, 'NMSP_EGI_BTN', 0)

	# EAC switch - ARM (left console middle inboard, right behind throttle) # NOTE Pitch and Yaw SAS must be ON, and EGI NAV mode button must be enabled, in order to arm EAC.
	pushSeqCmd(dt, 'LASTE_EAC', 1)

	# CDI STEER PT knob - FLIGHT PLAN (right console middle inboard)
	pushSeqCmd(dt, 'AAP_STEERPT', 0) # 0 = FLT PLAN, 1 = MARK, 2 = MISSION

	# CDI PAGE knob - STEER (right console middle inboard)
	pushSeqCmd(dt, 'AAP_PAGE', 2) # 0 = OTHER, 1 = POSITION, 2 = STEER, 3 = WAYPT

	# Ejection seat - ARM
	pushSeqCmd(dt, 'SEAT_ARM', 0) # 0 = ARM, 1 = SAFE

	pushSeqCmd(dt, 'scriptSpeech', "Manual steps remaining: LOAD page load all.  Set lights.  Tune radios.")

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

	# Lights
	if vars.get('Time') == 'Day':
		# FLT INST knob
		pushSeqCmd(dt, 'LCP_FLIGHT_INST', int16())
		# AUX INST knob
		pushSeqCmd(dt, 'LCP_AUX_INST', int16())
		# ENG INST knob
		pushSeqCmd(dt, 'LCP_ENG_INST', int16())
		# CONSOLE knob
		pushSeqCmd(dt, 'LCP_CONSOLE', int16())
		# ACCEL&COMP switch
		pushSeqCmd(dt, 'LCP_ACCEL_COMP', int16())
		# HUD MODE switch - DAY (instrument panel left lower)
		pushSeqCmd(dt, 'AHCP_HUD_DAYNIGHT', 1) # 0 = NIGHT, 1 = DAY
	else:
		# FLT INST knob
		pushSeqCmd(dt, 'LCP_FLIGHT_INST', int16(0.5))
		# AUX INST knob
		pushSeqCmd(dt, 'LCP_AUX_INST', int16(0.5))
		# ENG INST knob
		pushSeqCmd(dt, 'LCP_ENG_INST', int16(0.5))
		# CONSOLE knob
		pushSeqCmd(dt, 'LCP_CONSOLE', int16(0.5))
		# ACCEL&COMP switch
		pushSeqCmd(dt, 'LCP_ACCEL_COMP', int16(0.5))
		# HUD MODE switch - NIGHT (instrument panel left lower)
		pushSeqCmd(dt, 'AHCP_HUD_DAYNIGHT', 0) # 0 = NIGHT, 1 = DAY

	# Fuel display knob
	pushSeqCmd(dt, 'FQIS_SELECT', 0) # 0 = INT, 1 = MAIN, 2 = WING, 3 = EXT WING, 4 = EXT CTR

	# T/O TRIM button - Press for 1-2 seconds
	pushSeqCmd(dt, 'SASP_TO_TRIM', 1) # Press
	pushSeqCmd(2, 'SASP_TO_TRIM', 0) # Release after 2 seconds

	# CMS MODE knob - MAN (right console forward inboard)
	pushSeqCmd(dt, 'CMSP_MODE', 2) # 0 = OFF, 1 = STBY, 2 = MAN, 3 = SEMI, 4 = AUTO

	# IFF MASTER knob - NORM
	pushSeqCmd(dt, 'IFF_MASTER', 3) # 0 = OFF, 1 = STBY, 2 = LOW, 3 = NORM, 4 = EMER
	# IFF MODE 4 switch - ON
	pushSeqCmd(dt, 'IFF_ON_OUT', 1) # 0 = OUT, 1 = ON

	# MASTER ARM switch - ARM
	pushSeqCmd(dt, 'AHCP_MASTER_ARM', 2) # 0 = TRAIN, 1 = SAFE, 2 = ARM

	# GUN PAC switch - ARM
	pushSeqCmd(dt, 'AHCP_GUNPAC', 2) # 0 = GUNARM, 1 = SAFE, 2 = ARM

	# Laser arm switch - ARM
	pushSeqCmd(dt, 'AHCP_LASER_ARM', 2) # 0 = TRAIN, 1 = SAFE, 2 = ARM

	# TGP switch - ON
	pushSeqCmd(dt, 'AHCP_TGP', 1)

	# Press NAV on CDU page
	pushSeqCmd(dt, 'CDU_LSK_7R', 1) # Press
	pushSeqCmd(dt, 'CDU_LSK_7R', 0) # Release

	# CDI STEER PT knob - FLIGHT PLAN (right console middle inboard)
	pushSeqCmd(dt, 'AAP_STEERPT', 0) # 0 = FLT PLAN, 1 = MARK, 2 = MISSION

	# CDI PAGE knob - STEER (right console middle inboard)
	pushSeqCmd(dt, 'AAP_PAGE', 2) # 0 = OTHER, 1 = POSITION, 2 = STEER, 3 = WAYPT

	pushSeqCmd(dt, 'scriptSpeech', "Manual steps remaining: LOAD page load all.  Set lights.  Tune radios.")

	return seq


def AirStart(config, vars):
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

	# Lights
	if vars.get('Time') == 'Day':
		# FLT INST knob
		pushSeqCmd(dt, 'LCP_FLIGHT_INST', int16())
		# AUX INST knob
		pushSeqCmd(dt, 'LCP_AUX_INST', int16())
		# ENG INST knob
		pushSeqCmd(dt, 'LCP_ENG_INST', int16())
		# CONSOLE knob
		pushSeqCmd(dt, 'LCP_CONSOLE', int16())
		# ACCEL&COMP switch
		pushSeqCmd(dt, 'LCP_ACCEL_COMP', int16())
		# HUD MODE switch - DAY (instrument panel left lower)
		pushSeqCmd(dt, 'AHCP_HUD_DAYNIGHT', 1) # 0 = NIGHT, 1 = DAY
	else:
		# FLT INST knob
		pushSeqCmd(dt, 'LCP_FLIGHT_INST', int16(0.5))
		# AUX INST knob
		pushSeqCmd(dt, 'LCP_AUX_INST', int16(0.5))
		# ENG INST knob
		pushSeqCmd(dt, 'LCP_ENG_INST', int16(0.5))
		# CONSOLE knob
		pushSeqCmd(dt, 'LCP_CONSOLE', int16(0.5))
		# ACCEL&COMP switch
		pushSeqCmd(dt, 'LCP_ACCEL_COMP', int16(0.5))
		# HUD MODE switch - NIGHT (instrument panel left lower)
		pushSeqCmd(dt, 'AHCP_HUD_DAYNIGHT', 0) # 0 = NIGHT, 1 = DAY

	# Fuel display knob
	pushSeqCmd(dt, 'FQIS_SELECT', 0) # 0 = INT, 1 = MAIN, 2 = WING, 3 = EXT WING, 4 = EXT CTR

	# CMS MODE knob - MAN (right console forward inboard)
	pushSeqCmd(dt, 'CMSP_MODE', 2) # 0 = OFF, 1 = STBY, 2 = MAN, 3 = SEMI, 4 = AUTO

	# IFF MASTER knob - NORM
	pushSeqCmd(dt, 'IFF_MASTER', 3) # 0 = OFF, 1 = STBY, 2 = LOW, 3 = NORM, 4 = EMER
	# IFF MODE 4 switch - ON
	pushSeqCmd(dt, 'IFF_ON_OUT', 1) # 0 = OUT, 1 = ON

	# Laser arm switch - ARM
	pushSeqCmd(dt, 'AHCP_LASER_ARM', 2) # 0 = TRAIN, 1 = SAFE, 2 = ARM

	# TGP switch - ON
	pushSeqCmd(dt, 'AHCP_TGP', 1)

	# CDI STEER PT knob - FLIGHT PLAN (right console middle inboard)
	pushSeqCmd(dt, 'AAP_STEERPT', 0) # 0 = FLT PLAN, 1 = MARK, 2 = MISSION

	# CDI PAGE knob - STEER (right console middle inboard)
	pushSeqCmd(dt, 'AAP_PAGE', 2) # 0 = OTHER, 1 = POSITION, 2 = STEER, 3 = WAYPT

	pushSeqCmd(dt, 'scriptSpeech', "Manual steps remaining: Set lights.  Tune radios.")

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

	# Ejection seat - SAFE
	pushSeqCmd(dt, 'SEAT_ARM', 1) # 0 = ARM, 1 = SAFE

	# Canopy - Open
	pushSeqCmd(dt, 'CANOPY_OPEN', 2) # 0 = CLOSE, 1 = HOLD, 2 = OPEN
	pushSeqCmd(10, 'CANOPY_OPEN', 1) # NOTE: Takes longer to open than to close. # 0 = CLOSE, 1 = HOLD, 2 = OPEN

	# CDU switch - OFF (right console middle inboard)
	pushSeqCmd(dt, 'AAP_CDUPWR', 0)

	# EGI switch - OFF (right console middle inboard)
	pushSeqCmd(dt, 'AAP_EGIPWR', 0)

	# Lights
	# FLT INST knob
	pushSeqCmd(dt, 'LCP_FLIGHT_INST', 0)
	# AUX INST knob
	pushSeqCmd(dt, 'LCP_AUX_INST', 0)
	# ENG INST knob
	pushSeqCmd(dt, 'LCP_ENG_INST', 0)
	# CONSOLE knob
	pushSeqCmd(dt, 'LCP_CONSOLE', 0)
	# ACCEL&COMP switch
	pushSeqCmd(dt, 'LCP_ACCEL_COMP', 0)
	# HUD MODE switch - day/night (instrument panel left lower)
	pushSeqCmd(dt, 'AHCP_HUD_DAYNIGHT', 1) # 0 = NIGHT, 1 = DAY

	# ARC-186(V) VHF AM radio (left console inboard, forward radio in stack)
	# Knob - OFF
	pushSeqCmd(dt, 'VHFAM_MODE', 0) # 0 = OFF, 1 = TR, 2 = DF

	# ARC-164 UHF radio (left console inboard, middle radio in stack)
	# Knob - OFF
	pushSeqCmd(dt, 'UHF_FUNCTION', 0) # 0 = OFF, 1 = MAIN, 2 = BOTH, 3 = ADF

	# ARC-186(V) VHF FM radio (left console inboard, aft radio in stack)
	# Knob - OFF
	pushSeqCmd(dt, 'VHFFM_MODE', 0) # 0 = OFF, 1 = TR, 2 = DF

	# Left/Right MFDs - OFF
	pushSeqCmd(dt, 'LMFD_PWR', 0) # 0 = OFF, 1 = NT, 2 = DAY
	pushSeqCmd(dt, 'RMFD_PWR', 0) # 0 = OFF, 1 = NT, 2 = DAY

	# CICU switch - OFF (instrument panel lower left)
	pushSeqCmd(dt, 'AHCP_CICU', 0)

	# Left engine - OFF (RAlt-End)
	pushSeqCmd(dt, 'scriptKeyboard', 'RAlt down')
	pushSeqCmd(dt, 'scriptKeyboard', 'end')
	pushSeqCmd(dt, 'scriptKeyboard', 'RAlt up')

	# Right engine - OFF (RCtrl-End)
	pushSeqCmd(dt, 'scriptKeyboard', 'RCtrl down')
	pushSeqCmd(dt, 'scriptKeyboard', 'end')
	pushSeqCmd(dt, 'scriptKeyboard', 'RCtrl up')

	# JTRS switch - OFF (instrument panel lower left)
	pushSeqCmd(dt, 'AHCP_JTRS', 0)

	# IFFCC switch - OFF (instrument panel lower left)
	pushSeqCmd(dt, 'AHCP_IFFCC', 0) # 0 = OFF, 1 = TEST, 2 = ON

	# PITOT HEAT switch - Off (right console middle outboard
	pushSeqCmd(dt, 'ENVCP_PITOT_HEAT', 0)

	# Backup ADI - Cage (instrument panel lower left)
	pushSeqCmd(dt, 'SAI_CAGE', 1)
	for i in range(4):
		pushSeqCmd(dt, 'SAI_PITCH_TRIM', '+3200')

	# PITCH and YAW L/R SAS switches - OFF (right console forward outboard)
	pushSeqCmd(dt, 'SASP_PITCH_SAS_L', 0)
	pushSeqCmd(dt, 'SASP_PITCH_SAS_R', 0)
	pushSeqCmd(dt, 'SASP_YAW_SAS_L', 0)
	pushSeqCmd(dt, 'SASP_YAW_SAS_R', 0)

	# CMS MODE knob - OFF (right console forward inboard)
	pushSeqCmd(dt, 'CMSP_MODE', 0) # 0 = OFF, 1 = STBY, 2 = MAN, 3 = SEMI, 4 = AUTO

	# MWS, JMR, RWR, DISP switches - OFF (middle position) (right console forward inboard)
	pushSeqCmd(dt, 'CMSP_MWS', 0)
	pushSeqCmd(dt, 'CMSP_JMR', 0)
	pushSeqCmd(dt, 'CMSP_RWR', 0)
	pushSeqCmd(dt, 'CMSP_DISP', 0)

	# ANTI-SKID switch - OFF (instrument panel lower left, above gear lever)
	pushSeqCmd(dt, 'ANTI_SKID_SWITCH', 0)

	# IFF MASTER knob - OFF
	pushSeqCmd(dt, 'IFF_MASTER', 0) # 0 = OFF, 1 = STBY, 2 = LOW, 3 = NORM, 4 = EMER
	# IFF MODE 4 switch - OUT
	pushSeqCmd(dt, 'IFF_ON_OUT', 0) # 0 = OUT, 1 = ON

	# MASTER ARM switch - SAFE
	pushSeqCmd(dt, 'AHCP_MASTER_ARM', 1) # 0 = TRAIN, 1 = SAFE, 2 = ARM

	# GUN PAC switch - SAFE
	pushSeqCmd(dt, 'AHCP_GUNPAC', 1) # 0 = GUNARM, 1 = SAFE, 2 = ARM

	# Laser arm switch - SAFE
	pushSeqCmd(dt, 'AHCP_LASER_ARM', 1) # 0 = TRAIN, 1 = SAFE, 2 = ARM

	# TGP switch - OFF
	pushSeqCmd(dt, 'AHCP_TGP', 0)

	# EAC switch - OFF (left console middle inboard, right behind throttle) # NOTE Pitch and Yaw SAS must be ON, and EGI NAV mode button must be enabled, in order to arm EAC.
	pushSeqCmd(dt, 'LASTE_EAC', 0)

	# CDI STEER PT knob - FLIGHT PLAN (right console middle inboard)
	pushSeqCmd(dt, 'AAP_STEERPT', 0) # 0 = FLT PLAN, 1 = MARK, 2 = MISSION

	# CDI PAGE knob - OTHER (right console middle inboard)
	pushSeqCmd(dt, 'AAP_PAGE', 0) # 0 = OTHER, 1 = POSITION, 2 = STEER, 3 = WAYPT

	# INVERTER switch - STBY (right console forward outboard)
	pushSeqCmd(dt, 'EPP_INVERTER', 2)

	# BATTERY PWR switch - OFF (right console forward outboard)
	pushSeqCmd(dt, 'EPP_BATTERY_PWR', 0)

	return seq
