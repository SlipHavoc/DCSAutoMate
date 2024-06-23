# Return a Dictionary of script titles and their corresponding function names.  This is a list of scripts that users will be selecting from.  The module may have other utility functions that will not be run directly by the users.
def getScriptFunctions():
	return {
		'Cold Start, day': 'ColdStartDay',
		'Cold Start, night': 'ColdStartNight',
		#'Hot Start, day': 'HotStartDay',
		#'Hot Start, night': 'HotStartNight',
		#'Air Start, day': 'AirStartDay',
		#'Air Start, night': 'AirStartNight',
		'Shutdown': 'Shutdown',
		#'Test': 'Test',
	}

def getInfo():
	return """ATTENTION: You must remap "Engine Start/Stop Left/Right to use LAlt and LCtrl.  This is because pyWinAuto doesn't support RAlt or RCtrl."""

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
	
	return seq

def ColdStartDay(config):
	return ColdStart(config, dayStart = True)

def ColdStartNight(config):
	return ColdStart(config, dayStart = False)

def HotStartDay(config):
	return HotStart(config, dayStart = True)

def HotStartNight(config):
	return HotStart(config, dayStart = False)

def AirStartDay(config):
	return AirStart(config, dayStart = True)

def AirStartNight(config):
	return AirStart(config, dayStart = False)

def ColdStart(config, dayStart = True, alignSH = True):
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

	apuStartTime = 20
	insAlignTime = 30 + 4 * 60 + 3 # 30s for CDU BIT test, then 4m0s for alignment, plus 3 seconds extra buffer
	mfdBootTime = 30

	pushSeqCmd(0, '', '', "Running Cold Start sequence")
	pushSeqCmd(dt, 'scriptSpeech', "Warning, uses non standard key bindings.")
	pushSeqCmd(dt, 'scriptSpeech', 'Set throttle to minimum.')
	
	# BATTERY PWR switch - On (right console forward outboard)
	pushSeqCmd(dt, 'EPP_BATTERY_PWR', 1)

	# INVERTER switch - STBY (right console forward outboard)
	pushSeqCmd(dt, 'EPP_INVERTER', 2)


	# APU switch - START (left console inboard next to throttle)
	pushSeqCmd(dt, 'ENGINE_APU_START', 1)
	apuTimerStart = getLastSeqTime()

	# Canopy - Close
	pushSeqCmd(dt, 'CANOPY_OPEN', 0) # 0 = CLOSE, 1 = HOLD, 2 = OPEN
	pushSeqCmd(7, 'CANOPY_OPEN', 1) # 0 = CLOSE, 1 = HOLD, 2 = OPEN

	# APU started
	apuTimerEnd = apuStartTime - (getLastSeqTime() - apuTimerStart)
	pushSeqCmd(apuTimerEnd, '', '', "APU started")
	

	# APU GEN switch - PWR (right console forward outboard)
	pushSeqCmd(dt, 'EPP_APU_GEN_PWR', 1)

	# CDU switch - ON (right console middle inboard)
	pushSeqCmd(dt, 'AAP_CDUPWR', 1)

	# EGI switch - ON (right console middle inboard)
	pushSeqCmd(dt, 'AAP_EGIPWR', 1)
	# Alignment starts, takes 4m0s
	insAlignTimerStart = getLastSeqTime()

	# Lights
	if dayStart:
		# FLT INST knob
		pushSeqCmd(dt, 'LCP_FLT_INST', int16())
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
		pushSeqCmd(dt, 'LCP_FLT_INST', int16(0.5))
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
	
	# ARC-210 radio (left console inboard, forward radio in stack)
	# Knob - TR
	pushSeqCmd(dt, 'ARC210_MASTER', 2) # 0 = OFF, 1 = TR G, 2 = TR, 3 = ADF, 4 = CHG PRST, 5 = TEST, 6 = ZERO (PULL)

	# ARC-164 radio (left console inboard, middle radio in stack)
	# NOTE DCS-BIOS calls this the "UHF Radio"
	# Knob - MAIN
	pushSeqCmd(dt, 'UHF_FUNCTION', 1) # 0 = OFF, 1 = MAIN, 2 = BOTH, 3 = ADF

	# ARC-186(V) radio (left console inboard, aft radio in stack)
	# NOTE FIXME DCS-BIOS calls this either "VHF FM Radio" or "VHF AM Radio"??
	# Knob - TR
	pushSeqCmd(dt, 'VHFFM_MODE', 1) # 0 = OFF, 1 = TR, 2 = DF

	if dayStart:
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
	
	# Left engine - IDLE (LAlt-Home)
	pushSeqCmd(dt, 'scriptKeyboard', '{VK_LMENU down}{VK_HOME}{VK_LMENU up}') # FIXME pyWinAuto doesn't support RAlt or RCtrl.
	pushSeqCmd(50, '', '', 'Left engine started')
	# Idle at 60%, ENGINE START CYCLE light on light panel goes out.

	# APU GEN switch - OFF (right console forward outboard)
	pushSeqCmd(dt, 'EPP_APU_GEN_PWR', 0)

	# Master Caution - Reset
	#pushSeqCmd(dt, 'UFC_MASTER_CAUTION', 1) # Press
	#pushSeqCmd(dt, 'UFC_MASTER_CAUTION', 0) # Release

	# Right engine - IDLE (LCtrl-Home)
	pushSeqCmd(dt, 'scriptKeyboard', '{VK_LCONTROL down}{VK_HOME}{VK_LCONTROL up}') # FIXME pyWinAuto doesn't support RAlt or RCtrl.
	pushSeqCmd(50, '', '', 'Right engine started')
	# Idle at 60%, ENGINE START CYCLE light on light panel goes out.

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

	# HMCS power - ON (right console rear inboard)
	pushSeqCmd(dt, 'A102_HMCS_PW', 2) # 0 = BAT, 1 = OFF, 2 = ON

	# GUN PAC switch - ARM
	pushSeqCmd(dt, 'AHCP_GUNPAC', 2) # 0 = GUNARM, 1 = SAFE, 2 = ARM
	
	# Laser arm switch - ARM
	#pushSeqCmd(dt, 'AHCP_LASER_ARM', 2) # 0 = TRAIN, 1 = SAFE, 2 = ARM

	# TGP switch - ON
	#pushSeqCmd(dt, 'AHCP_TGP', 1)

	## DTS LOAD ALL - Left MFD R5 OSB (PB11)
	#pushSeqCmd(dt, 'LMFD_11', 1) # LOAD ALL
	#pushSeqCmd(dt, 'LMFD_11', 0) # Release
	#pushSeqCmd(15, '', '', 'DTS loaded')

	## Go to TAD page on left MFD
	#pushSeqCmd(dt, 'LMFD_15', 1) # LOAD ALL
	#pushSeqCmd(dt, 'LMFD_15', 0) # Release


	# Trigger the INS alignment check after the correct time (total process time minus the difference between now and when the process started).
	insAlignTimerEnd = insAlignTime - (getLastSeqTime() - insAlignTimerStart)
	pushSeqCmd(insAlignTimerEnd, '', '', "INS aligned")

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
	
	pushSeqCmd(dt, 'scriptSpeech', "Manual steps remaining: D S M S page load all.  Set lights.  Tune radios.")

	return seq


def HotStart(config, dayStart = True):
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
	
	# Set lights
	if dayStart:
		# Front console lights
		pushSeqCmd(dt, 'F_INTL_CONSOLE', int16())
		# Rear console lights
		pushSeqCmd(dt, 'R_INTL_CONSOLE', int16())
		# Front instrument panel lights
		pushSeqCmd(dt, 'F_INTL_INSTR', int16())
		# Rear instrument panel lights
		pushSeqCmd(dt, 'R_INTL_INSTR', int16())
		# Front day/night mode
		pushSeqCmd(dt, 'F_INTL_DN_MODE', 1) # 0 = NIGHT, 1 = DAY
		# Rear day/night mode
		pushSeqCmd(dt, 'R_INTL_DN_MODE', 1) # 0 = NIGHT, 1 = DAY
		# HUD ... ON and brightness as desired (knob on UFC)
		pushSeqCmd(dt, 'F_HUD_BRIGHT', int16())
		# HUD day/night mode
		pushSeqCmd(dt, 'F_HUD_D_A_N_MODE', 0) # 0 = DAY, 1 = AUTO, 2 = NIGHT??
		# Front UFC brightness ... As desired (knob on UFC)
		pushSeqCmd(dt, 'F_UFC_LCD_BRIGHT', int16())
		# Rear UFC brightness ... As desired (knob on UFC)
		pushSeqCmd(dt, 'R_UFC_LCD_BRIGHT', int16())
	else:
		# Front console lights
		pushSeqCmd(dt, 'F_INTL_CONSOLE', int16(0.5))
		# Rear console lights
		pushSeqCmd(dt, 'R_INTL_CONSOLE', int16(0.5))
		# Front instrument panel lights
		pushSeqCmd(dt, 'F_INTL_INSTR', int16(0.5))
		# Rear instrument panel lights
		pushSeqCmd(dt, 'R_INTL_INSTR', int16(0.5))
		# Front day/night mode
		pushSeqCmd(dt, 'F_INTL_DN_MODE', 0) # 0 = NIGHT, 1 = DAY
		# Rear day/night mode
		pushSeqCmd(dt, 'R_INTL_DN_MODE', 0) # 0 = NIGHT, 1 = DAY
		# HUD ... ON and brightness as desired (knob on UFC)
		pushSeqCmd(dt, 'F_HUD_BRIGHT', int16(0.5))
		# HUD day/night mode
		pushSeqCmd(dt, 'F_HUD_D_A_N_MODE', 2) # 0 = DAY, 1 = AUTO, 2 = NIGHT??
		# Front UFC brightness ... As desired (knob on UFC)
		pushSeqCmd(dt, 'F_UFC_LCD_BRIGHT', int16(0.5))
		# Rear UFC brightness ... As desired (knob on UFC)
		pushSeqCmd(dt, 'R_UFC_LCD_BRIGHT', int16(0.5))

	# Radio volumes
	pushSeqCmd(dt, 'F_UFC_COM1_VOL', int16())
	pushSeqCmd(dt, 'F_UFC_COM2_VOL', int16())
	pushSeqCmd(dt, 'F_UFC_COM3_VOL', int16())
	pushSeqCmd(dt, 'F_UFC_COM4_VOL', int16())

	# IFF mode ... 4A
	pushSeqCmd(dt, 'F_IFF_MODE', 1)

	# IFF reply switch ... LIGHT
	pushSeqCmd(dt, 'F_IFF_REPLY', 2)

	# RADAR switch ... ON (radar will stay off while weight-on-wheels) (left console middle, behind throttle)
	pushSeqCmd(dt, 'F_S_RDR_MODE', 2) # 0 = OFF, 1 = STBY, 2 = ON, 3 = EMERG

	# NCTR switch ... ON
	pushSeqCmd(dt, 'F_BH_NCTR', 1)
	
	# NAV FLIR switch ... ON (turns on NAV FLIR for use in both MFD and HUD) (left console middle, behind throttle)
	pushSeqCmd(dt, 'F_S_NAV_FLIR_SW', 2) # 0 = OFF, 1 = STBY, 2 = ON
	# NAV FLIR GAIN/BRIGHTNESS knob ... As desired (left console middle)
	# TODO, not sure if needed

	# JTIDS knob ... NORM (left console middle, behind throttle)
	pushSeqCmd(dt, 'F_S_JTIDS', 2) # 0 = OFF, 1 = POLL, 2 = NORM, 3 = SIL, 4 = HOLD

	# Fuel totalizer ... EXT WNG
	pushSeqCmd(dt, 'F_FUEL_TOTAL', 3) # 0 = FEED, 1 = INTL WNG, 2 = TANK 1, 3 = EXT WNG, 4 = EXT CTR, 5 = CONF TANK??

	# BINGO fuel ... As desired (4000 lbs is a good default??) (right lower instrument panel, knob on fuel gauge)
	for i in range(40):
		pushSeqCmd(dt, 'F_FUEL_BINGO', 3200)
	
	# Add UFC DATA to HUD
	# Return to MENU 1 screen from anywhere with DATA, MENU.  Go to DATA 1 screen from anywhere with MENU, DATA.
	pushSeqCmd(dt, 'F_UFC_KEY_MENU', 1)
	pushSeqCmd(dt, 'F_UFC_KEY_MENU', 0)
	pushSeqCmd(dt, 'F_UFC_KEY_DATA', 1)
	pushSeqCmd(dt, 'F_UFC_KEY_DATA', 0)
	pushSeqCmd(dt, 'F_UFC_B7', 1) # Radar alt in HUD # FIXME This is actually B9, but Front UFC B7 and B9 are swapped.
	pushSeqCmd(dt, 'F_UFC_B7', 0)
	pushSeqCmd(dt, 'F_UFC_B3', 1) # TAS in HUD
	pushSeqCmd(dt, 'F_UFC_B3', 0)
	# Return to MENU 1.
	pushSeqCmd(dt, 'F_UFC_KEY_MENU', 1)
	pushSeqCmd(dt, 'F_UFC_KEY_MENU', 0)

	# PROGRAM MFDS
	def pressMfdButtons(mfd, buttons):
		prefixes = {
			'left': 'F_MPD_L_',
			'right': 'F_MPD_R_',
			'center': 'F_MPCD_C_',
		}
		prefix = prefixes[mfd]
		for button in buttons:
			if button == 'PW':
				# 0 = ON, 1 = middle, 2 = OFF
				pushSeqCmd(dt, prefix + button, 0) # ON
				pushSeqCmd(dt, prefix + button, 1) # middle
			else:
				pushSeqCmd(dt, prefix + button, 1) # Press
				pushSeqCmd(dt, prefix + button, 0) # Release

	# Left MFD
	pressMfdButtons('left', [
		# Return to MENU 1 page from anywhere with Power switch ON.
		'PW', # POWER ON
		# Start programming.
		'B6', # PROG
		'B15', # A/A RDR
		'B14', # A/G RDR
		'B12', # TPOD
		# End programming.
		'B6', #PROG
	])
	
	# Right MFD
	pressMfdButtons('right', [
		# Return to MENU 1 page from anywhere with Power switch ON.
		'PW', # POWER ON
		# Start programming.
		'B6', # PROG
		'B12', # TPOD
		'B3', # HSI
		'B2', # ARMT
		# End programming.
		'B6', # PROG
	])

	# Center MFD
	pressMfdButtons('center', [
		# Return to MENU 1 page from anywhere with Power switch ON.
		'PW', # POWER ON
		# Start programming.
		'B6', # PROG
		'B5', # TSD
		'B3', # HSI
		'B2', # ARMT
		# End programming.
		'B6', # PROG
		# END PROGRAM MFDS
	])

	# SET UP BACK SEAT
	# Radio volumes
	pushSeqCmd(dt, 'R_UFC_COM1_VOL', int16())
	pushSeqCmd(dt, 'R_UFC_COM2_VOL', int16())
	pushSeqCmd(dt, 'R_UFC_COM3_VOL', int16())
	pushSeqCmd(dt, 'R_UFC_COM4_VOL', int16())
	# TGT FLIR switch ... ON (left console middle, behind left hand controller)
	pushSeqCmd(dt, 'R_TGP_PW', 2) # 0 = OFF, 1 = STBY, 2 = ON
	# LASER switch ... ARM (left console middle, behind left hand controller)
	pushSeqCmd(dt, 'R_TGP_LASER', 1) # 0 = SAFE, 1 = ARM
	# RWR/ICS mode switch ... COMBAT
	pushSeqCmd(dt, 'R_EW_RWR_ICS_MODE', 1) # 0 = TRNG, 1 = COMBAT
	# ICS operational mode switch ... AUTO
	pushSeqCmd(dt, 'R_EW_ICS_OP_MODE', 1) # 0 = STBY, 1 = AUTO, 2 = MAN
	# MIC switch ... ON
	pushSeqCmd(dt, 'R_MIC_SW', 1) # FIXME not working??

	# ICS power switch ... ON
	pushSeqCmd(dt, 'R_TEWS_ICS_PW', 1)
	# END SET UP BACK SEAT
	
	pushSeqCmd(dt, 'scriptSpeech', "Manual steps remaining: Set up armament page.  Set lights.  Tune radios.")

	return seq


def AirStart(config, dayStart = True):
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
	
	# Set lights
	if dayStart:
		# Front console lights
		pushSeqCmd(dt, 'F_INTL_CONSOLE', int16())
		# Rear console lights
		pushSeqCmd(dt, 'R_INTL_CONSOLE', int16())
		# Front instrument panel lights
		pushSeqCmd(dt, 'F_INTL_INSTR', int16())
		# Rear instrument panel lights
		pushSeqCmd(dt, 'R_INTL_INSTR', int16())
		# Front day/night mode
		pushSeqCmd(dt, 'F_INTL_DN_MODE', 1) # 0 = NIGHT, 1 = DAY
		# Rear day/night mode
		pushSeqCmd(dt, 'R_INTL_DN_MODE', 1) # 0 = NIGHT, 1 = DAY
		# HUD ... ON and brightness as desired (knob on UFC)
		pushSeqCmd(dt, 'F_HUD_BRIGHT', int16())
		# HUD day/night mode
		pushSeqCmd(dt, 'F_HUD_D_A_N_MODE', 0) # 0 = DAY, 1 = AUTO, 2 = NIGHT??
		# Front UFC brightness ... As desired (knob on UFC)
		pushSeqCmd(dt, 'F_UFC_LCD_BRIGHT', int16())
		# Rear UFC brightness ... As desired (knob on UFC)
		pushSeqCmd(dt, 'R_UFC_LCD_BRIGHT', int16())
	else:
		# Front console lights
		pushSeqCmd(dt, 'F_INTL_CONSOLE', int16(0.5))
		# Rear console lights
		pushSeqCmd(dt, 'R_INTL_CONSOLE', int16(0.5))
		# Front instrument panel lights
		pushSeqCmd(dt, 'F_INTL_INSTR', int16(0.5))
		# Rear instrument panel lights
		pushSeqCmd(dt, 'R_INTL_INSTR', int16(0.5))
		# Front day/night mode
		pushSeqCmd(dt, 'F_INTL_DN_MODE', 0) # 0 = NIGHT, 1 = DAY
		# Rear day/night mode
		pushSeqCmd(dt, 'R_INTL_DN_MODE', 0) # 0 = NIGHT, 1 = DAY
		# HUD ... ON and brightness as desired (knob on UFC)
		pushSeqCmd(dt, 'F_HUD_BRIGHT', int16(0.5))
		# HUD day/night mode
		pushSeqCmd(dt, 'F_HUD_D_A_N_MODE', 2) # 0 = DAY, 1 = AUTO, 2 = NIGHT??
		# Front UFC brightness ... As desired (knob on UFC)
		pushSeqCmd(dt, 'F_UFC_LCD_BRIGHT', int16(0.5))
		# Rear UFC brightness ... As desired (knob on UFC)
		pushSeqCmd(dt, 'R_UFC_LCD_BRIGHT', int16(0.5))

	# Radio volumes
	pushSeqCmd(dt, 'F_UFC_COM1_VOL', int16())
	pushSeqCmd(dt, 'F_UFC_COM2_VOL', int16())
	pushSeqCmd(dt, 'F_UFC_COM3_VOL', int16())
	pushSeqCmd(dt, 'F_UFC_COM4_VOL', int16())

	# IFF mode ... 4A
	pushSeqCmd(dt, 'F_IFF_MODE', 1)

	# IFF reply switch ... LIGHT
	pushSeqCmd(dt, 'F_IFF_REPLY', 2)
	
	# NCTR switch ... ON
	pushSeqCmd(dt, 'F_BH_NCTR', 1)
	
	# JTIDS knob ... NORM (left console middle, behind throttle)
	pushSeqCmd(dt, 'F_S_JTIDS', 2) # 0 = OFF, 1 = POLL, 2 = NORM, 3 = SIL, 4 = HOLD

	# Fuel totalizer ... EXT WNG
	pushSeqCmd(dt, 'F_FUEL_TOTAL', 3) # 0 = FEED, 1 = INTL WNG, 2 = TANK 1, 3 = EXT WNG, 4 = EXT CTR, 5 = CONF TANK, not sure if BIT is selectable??

	# BINGO fuel ... As desired (4000 lbs is a good default??) (right lower instrument panel, knob on fuel gauge)
	for i in range(40):
		pushSeqCmd(dt, 'F_FUEL_BINGO', 3200)
	
	# Add UFC DATA to HUD
	# Return to MENU 1 screen from anywhere with DATA, MENU.  Go to DATA 1 screen from anywhere with MENU, DATA.
	pushSeqCmd(dt, 'F_UFC_KEY_MENU', 1)
	pushSeqCmd(dt, 'F_UFC_KEY_MENU', 0)
	pushSeqCmd(dt, 'F_UFC_KEY_DATA', 1)
	pushSeqCmd(dt, 'F_UFC_KEY_DATA', 0)
	pushSeqCmd(dt, 'F_UFC_B7', 1) # Radar alt in HUD # FIXME This is actually B9, but Front UFC B7 and B9 are swapped.
	pushSeqCmd(dt, 'F_UFC_B7', 0)
	pushSeqCmd(dt, 'F_UFC_B3', 1) # TAS in HUD
	pushSeqCmd(dt, 'F_UFC_B3', 0)
	# Return to MENU 1.
	pushSeqCmd(dt, 'F_UFC_KEY_MENU', 1)
	pushSeqCmd(dt, 'F_UFC_KEY_MENU', 0)

	# PROGRAM MFDS
	def pressMfdButtons(mfd, buttons):
		prefixes = {
			'left': 'F_MPD_L_',
			'right': 'F_MPD_R_',
			'center': 'F_MPCD_C_',
		}
		prefix = prefixes[mfd]
		for button in buttons:
			if button == 'PW':
				# 0 = ON, 1 = middle, 2 = OFF
				pushSeqCmd(dt, prefix + button, 0) # ON
				pushSeqCmd(dt, prefix + button, 1) # middle
			else:
				pushSeqCmd(dt, prefix + button, 1) # Press
				pushSeqCmd(dt, prefix + button, 0) # Release

	# Left MFD
	pressMfdButtons('left', [
		# Return to MENU 1 page from anywhere with Power switch ON.
		'PW', # POWER ON
		# Start programming.
		'B6', # PROG
		'B15', # A/A RDR
		'B14', # A/G RDR
		'B12', # TPOD
		# End programming.
		'B6', #PROG
	])
	
	# Right MFD
	pressMfdButtons('right', [
		# Return to MENU 1 page from anywhere with Power switch ON.
		'PW', # POWER ON
		# Start programming.
		'B6', # PROG
		'B12', # TPOD
		'B3', # HSI
		'B2', # ARMT
		# End programming.
		'B6', # PROG
	])

	# Center MFD
	pressMfdButtons('center', [
		# Return to MENU 1 page from anywhere with Power switch ON.
		'PW', # POWER ON
		# Start programming.
		'B6', # PROG
		'B5', # TSD
		'B3', # HSI
		'B2', # ARMT
		# End programming.
		'B6', # PROG
		# END PROGRAM MFDS
	])

	# SET UP BACK SEAT
	# Radio volumes
	pushSeqCmd(dt, 'R_UFC_COM1_VOL', int16())
	pushSeqCmd(dt, 'R_UFC_COM2_VOL', int16())
	pushSeqCmd(dt, 'R_UFC_COM3_VOL', int16())
	pushSeqCmd(dt, 'R_UFC_COM4_VOL', int16())

	# RWR/ICS mode switch ... COMBAT
	pushSeqCmd(dt, 'R_EW_RWR_ICS_MODE', 1) # 0 = TRNG, 1 = COMBAT
	# ICS operational mode switch ... AUTO
	pushSeqCmd(dt, 'R_EW_ICS_OP_MODE', 1) # 0 = STBY, 1 = AUTO, 2 = MAN
	# MIC switch ... ON
	pushSeqCmd(dt, 'R_MIC_SW', 1) # FIXME not working??
	# END SET UP BACK SEAT
	
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

	pushSeqCmd(0, '', '', "Running Shutdown sequence")
	pushSeqCmd(dt, 'scriptSpeech', "Warning, uses non standard key bindings.")
	
	# Ejection seat - SAFE
	pushSeqCmd(dt, 'SEAT_ARM', 1) # 0 = ARM, 1 = SAFE
	
	# Canopy - Open
	pushSeqCmd(dt, 'CANOPY_OPEN', 2) # 0 = CLOSE, 1 = HOLD, 2 = OPEN
	pushSeqCmd(7, 'CANOPY_OPEN', 1) # 0 = CLOSE, 1 = HOLD, 2 = OPEN

	# CDU switch - OFF (right console middle inboard)
	pushSeqCmd(dt, 'AAP_CDUPWR', 0)

	# EGI switch - OFF (right console middle inboard)
	pushSeqCmd(dt, 'AAP_EGIPWR', 0)
	
	# Lights
	# FLT INST knob
	pushSeqCmd(dt, 'LCP_FLT_INST', 0)
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
	
	# ARC-210 radio (left console inboard, forward radio in stack)
	# Knob - OFF
	pushSeqCmd(dt, 'ARC210_MASTER', 0) # 0 = OFF, 1 = TR G, 2 = TR, 3 = ADF, 4 = CHG PRST, 5 = TEST, 6 = ZERO (PULL)

	# ARC-164 radio (left console inboard, middle radio in stack)
	# NOTE DCS-BIOS calls this the "UHF Radio"
	# Knob - OFF
	pushSeqCmd(dt, 'UHF_FUNCTION', 0) # 0 = OFF, 1 = MAIN, 2 = BOTH, 3 = ADF

	# ARC-186(V) radio (left console inboard, aft radio in stack)
	# NOTE FIXME DCS-BIOS calls this either "VHF FM Radio" or "VHF AM Radio"??
	# Knob - OFF
	pushSeqCmd(dt, 'VHFFM_MODE', 0) # 0 = OFF, 1 = TR, 2 = DF

	# Left/Right MFDs - OFF
	pushSeqCmd(dt, 'LMFD_PWR', 0) # 0 = OFF, 1 = NT, 2 = DAY
	pushSeqCmd(dt, 'RMFD_PWR', 0) # 0 = OFF, 1 = NT, 2 = DAY
	
	# CICU switch - OFF (instrument panel lower left)
	pushSeqCmd(dt, 'AHCP_CICU', 0)
	
	# Left engine - OFF (LAlt-End)
	pushSeqCmd(dt, 'scriptKeyboard', '{VK_LMENU down}{VK_END}{VK_LMENU up}') # FIXME pyWinAuto doesn't support RAlt or RCtrl.

	# Right engine - IDLE (LCtrl-End)
	pushSeqCmd(dt, 'scriptKeyboard', '{VK_LCONTROL down}{VK_END}{VK_LCONTROL up}') # FIXME pyWinAuto doesn't support RAlt or RCtrl.

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

	# HMCS power - OFF (right console rear inboard)
	pushSeqCmd(dt, 'A102_HMCS_PW', 1) # 0 = BAT, 1 = OFF, 2 = ON

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
