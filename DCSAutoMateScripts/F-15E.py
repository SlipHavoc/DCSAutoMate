# Return a Dictionary of script titles and their corresponding function names.  This is a list of scripts that users will be selecting from.  The module may have other utility functions that will not be run directly by the users.
def getScriptFunctions():
	return {
		'Cold Start, day, Stored Heading (SH) align': 'ColdStartDaySH',
		#'Cold Start, day, Full Gyrocompass (GC) align': 'ColdStartDayGC',
		'Cold Start, night, Stored Heading (SH) align': 'ColdStartNightSH',
		#'Cold Start, night, Full Gyrocompass (GC) align': 'ColdStartNightGC',
		'Hot Start, day': 'HotStartDay',
		'Hot Start, night': 'HotStartNight',
		'Air Start, day': 'AirStartDay',
		'Air Start, night': 'AirStartNight',
		'Shutdown': 'Shutdown',
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
	
	return seq

def ColdStartDaySH(config):
	return ColdStart(config, dayStart = True, alignSH = True)

def ColdStartDayGC(config):
	return ColdStart(config, dayStart = True, alignSH = False)

def ColdStartNightSH(config):
	return ColdStart(config, dayStart = False, alignSH = True)

def ColdStartNightGC(config):
	return ColdStart(config, dayStart = False, alignSH = False)

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

	insAlignTimeSH = 1 * 60 + 10 # 1m5s, extra 10 seconds as buffer in case of MP lag.
	insAlignTimeGC = 4 * 60 + 10 # 4m5s, extra 10 seconds as buffer in case of MP lag.
	
	pushSeqCmd(0, '', '', "Running Cold Start sequence")
	pushSeqCmd(dt, 'scriptSpeech', "Warning, uses non standard key bindings.")
	pushSeqCmd(dt, 'scriptSpeech', 'Set throttle to minimum.')
	
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

	# L and R GEN switches ... ON
	pushSeqCmd(dt, 'F_GEN_L', 1)
	pushSeqCmd(dt, 'F_GEN_R', 1)
	# L and R ENG CONTR switches ... ON (right console forward middle)
	pushSeqCmd(dt, 'F_ENG_L_CONTL', 1)
	pushSeqCmd(dt, 'F_ENG_R_CONTL', 1)
	#L and R ENG MASTER switches ... ON (right console forward, black guarded switches)
	pushSeqCmd(dt, 'F_ENG_L_MASTER_CVR', 1)
	pushSeqCmd(dt, 'F_ENG_L_MASTER', 1)
	pushSeqCmd(dt, 'F_ENG_L_MASTER_CVR', 0)
	pushSeqCmd(dt, 'F_ENG_R_MASTER_CVR', 1)
	pushSeqCmd(dt, 'F_ENG_R_MASTER', 1)
	pushSeqCmd(dt, 'F_ENG_R_MASTER_CVR', 0)
	# STARTER switch ... ON (right console forward)
	pushSeqCmd(dt, 'F_GEN_JET_START', 1)
	# AIR COND switch ... AUTO (right console forward outboard)
	pushSeqCmd(dt, 'F_AC_AUTO_MAN_OFF', 2)
	# CONF TANK switch ... TRANS (left console forward)
	#pushSeqCmd(dt, 'F_FUEL_CONF_CONTL', 2) # Should be on NORM I think??
	# L and R INLET switches ... AUTO (left console forward outboard)
	pushSeqCmd(dt, 'F_IN_RAMP_L_SW', 0) # 0 = AUTO, 1 = EMERG
	pushSeqCmd(dt, 'F_IN_RAMP_R_SW', 0) # 0 = AUTO, 1 = EMERG
	# JET FUEL STARTER handle ... Pull (left click) (right lower instrument panel)
	pushSeqCmd(dt, 'F_B_JFS_CONT_PULL', 1)
	#pushSeqCmd(1, 'F_B_JFS_CONT_PULL', 0) 
	# Wait for Ready light to turn on.
	pushSeqCmd(5, '', '', 'Starter Ready light is on')
	
	# Start right engine
	# Right fingerlift
	pushSeqCmd(dt, 'F_TQ_R_FINGER', 1)
	pushSeqCmd(dt, 'F_TQ_R_FINGER', 0)
	pushSeqCmd(dt, '', '', 'Wait for 26% RPM')
	pushSeqCmd(23, '', '', 'Right engine at 26% RPM')
	# Right throttle to IDLE
	pushSeqCmd(dt, 'scriptKeyboard', '{VK_RSHIFT down}{VK_HOME}{VK_RSHIFT up}')
	pushSeqCmd(50, '', '', 'Right engine at 72% RPM')

	# Start left engine
	# left fingerlift
	pushSeqCmd(dt, 'F_TQ_L_FINGER', 1)
	pushSeqCmd(dt, 'F_TQ_L_FINGER', 0)
	pushSeqCmd(dt, '', '', 'Wait for 26% RPM')
	pushSeqCmd(23, '', '', 'Left engine at 26% RPM')
	# Left throttle to IDLE
	pushSeqCmd(dt, 'scriptKeyboard', '{VK_LMENU down}{VK_HOME}{VK_LMENU up}', 'ATTENTION: You must remap Throttle (Left) - IDLE to LAlt+Home') # FIXME pyWinAuto doesn't support RAlt or RCtrl.
	pushSeqCmd(50, '', '', 'Left engine at 72% RPM')

	# BRAKEHOLD switch ... ON
	pushSeqCmd(dt, 'F_B_P_BRAKE', 1)

	# MIC switch ... ON
	pushSeqCmd(dt, 'F_MIC_SW', 1)
	
	# Radios
	# Radio 1 ... ON
	pushSeqCmd(dt, 'F_UFC_PRE_CHAN_L_PULL', 1)
	pushSeqCmd(dt, 'F_UFC_PRE_CHAN_L_PULL', 0)
	# Radio 2 ... ON
	pushSeqCmd(dt, 'F_UFC_PRE_CHAN_R_PULL', 1)
	pushSeqCmd(dt, 'F_UFC_PRE_CHAN_R_PULL', 0)
	# Radio volumes
	pushSeqCmd(dt, 'F_UFC_COM1_VOL', int16())
	pushSeqCmd(dt, 'F_UFC_COM2_VOL', int16())
	pushSeqCmd(dt, 'F_UFC_COM3_VOL', int16())
	pushSeqCmd(dt, 'F_UFC_COM4_VOL', int16())

	# OXYGEN supply switch ... ON (right console forward)
	pushSeqCmd(dt, 'F_OXY_MODE', 1)

	# Canopy ... Close and seal (lever on right canopy rail)
	pushSeqCmd(dt, 'CANOPY_F_HND', 2)
	pushSeqCmd(6, 'CANOPY_F_HND', 3)	
	
	# MFDs ... ON (click the rocker switch on each MFD)
	# 0 = ON, 1 = middle, 2 = OFF
	pushSeqCmd(dt, 'F_MPD_L_PW', 0)
	pushSeqCmd(dt, 'F_MPD_L_PW', 1)
	pushSeqCmd(dt, 'F_MPD_R_PW', 0)
	pushSeqCmd(dt, 'F_MPD_R_PW', 1)
	pushSeqCmd(dt, 'F_MPCD_C_PW', 0)
	pushSeqCmd(dt, 'F_MPCD_C_PW', 1)

	# Begin alignment
	pushSeqCmd(dt, 'scriptSpeech', "Beginning INS alignment.  Do not rearm or move controls until alignment is complete.")
	# INS knob ... STORE for stored heading (1 min), or GC ALIGN (gyrocompass) for full alignment (4 mins)
	insAlignTimerStart = getLastSeqTime()
	if alignSH:
		pushSeqCmd(dt, 'F_S_INS', 1) # 0 = OFF, 1 = STORE, 2 = GC, 3 = NAV
	else:
		pushSeqCmd(dt, 'F_S_INS', 2) # 0 = OFF, 1 = STORE, 2 = GC, 3 = NAV

	# IFF mode ... 4A
	pushSeqCmd(dt, 'F_IFF_MODE', 1)

	# IFF reply switch ... LIGHT
	pushSeqCmd(dt, 'F_IFF_REPLY', 2)
	
	# TF RDR switch ... STBY (left console middle, behind throttle)
	pushSeqCmd(dt, 'F_S_RDR_TER_FOL', 1) # 0 = OFF, 1 = STBY, 2 = ON
	
	# RDR ALT switch ... ON (left console middle, behind throttle)
	pushSeqCmd(dt, 'F_S_RDR_ALT', 1) # 0 = OFF, 1 = ON, 2 = OVERIDE

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

	# CAS YAW, ROLL, and PITCH switches ... ON (left console forward inboard)
	pushSeqCmd(dt, 'F_CAS_YAW', 1)
	pushSeqCmd(dt, 'F_CAS_ROLL', 1)
	pushSeqCmd(dt, 'F_CAS_PITCH', 1)
	
	# SAI (Standby Attitude Indicator) ... Uncage and center (left lower instrument panel)
	pushSeqCmd(dt, 'F_FI_BAK_ADI_CAGE_PULL', 1)
	pushSeqCmd(dt, 'F_FI_BAK_ADI_CAGE_KNOB', 0)
	pushSeqCmd(dt, 'F_FI_BAK_ADI_CAGE_PULL', 0)

	# Backup altimeter ... Set to match QNH (current altitude above sea level)
	# TODO

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

	# Ejection seat ... ARM (lever on left forward base of seat)
	pushSeqCmd(dt, 'F_BH_SEAT_ARM', 1)

	# SET UP BACK SEAT
	# All MFDs ... ON
	# 0 = ON, 1 = middle, 2 = OFF
	pushSeqCmd(dt, 'R_MPCD_L_PW', 0)
	pushSeqCmd(dt, 'R_MPCD_L_PW', 1)
	pushSeqCmd(dt, 'R_MPD_L_PW', 0)
	pushSeqCmd(dt, 'R_MPD_L_PW', 1)
	pushSeqCmd(dt, 'R_MPD_R_PW', 0)
	pushSeqCmd(dt, 'R_MPD_R_PW', 1)
	pushSeqCmd(dt, 'R_MPCD_R_PW', 0)
	pushSeqCmd(dt, 'R_MPCD_R_PW', 1)
	# SAI (Standby Attitude Indicator) ... Uncage and center (instrument panel center)
	pushSeqCmd(dt, 'R_FI_BAK_ADI_CAGE_PULL', 1)
	pushSeqCmd(dt, 'R_FI_BAK_ADI_CAGE_KNOB', 0)
	pushSeqCmd(dt, 'R_FI_BAK_ADI_CAGE_PULL', 0)
	# Backup altimeter ... Set to match QNH (current altitude above sea level)
	# TODO

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

	# OXYGEN supply switch ... ON (right console forward, in front of right hand controller)
	pushSeqCmd(dt, 'R_OXY_MODE', 1)
	# ICS power switch ... ON
	pushSeqCmd(dt, 'R_TEWS_ICS_PW', 1)
	# RWR switch ... ON (right console middle, behind right hand controller)
	pushSeqCmd(dt, 'R_TEWS_RWR_PW', 1)
	# EWWS switch ... ON (right console middle, behind right hand controller)
	pushSeqCmd(dt, 'R_TEWS_EWWS_PW', 1)
	# CMD MODE knob ... SEMIAUTO (right console middle)
	pushSeqCmd(dt, 'R_CMD_OP_MODE', 3) # 0 = OFF, 1 = STBY, 2 = MAN ONLY, 3 = SEMIAUTO, 4 = AUTO
	
	# Ejection seat ... ARM (lever on left forward base of seat)
	pushSeqCmd(dt, 'R_TQ_SEAT_ARM', 1)
	# END SET UP BACK SEAT
	
	# Wait for the INS to finish aligning (total process time minus the difference between now and when the process started).
	if alignSH:
		insAlignTimerEnd = insAlignTimeSH - (getLastSeqTime() - insAlignTimerStart)
	else:
		insAlignTimerEnd = insAlignTimeGC - (getLastSeqTime() - insAlignTimerStart)
	pushSeqCmd(insAlignTimerEnd, '', '', "INS Aligned")
	# INS knob ... NAV
	pushSeqCmd(dt, 'F_S_INS', 3) # 0 = OFF, 1 = STORE, 2 = GC, 3 = NAV
	pushSeqCmd(dt, 'scriptSpeech', "INS aiignment is complete, you may rearm and move the controls.")
	
	# NOTE Should be done after INS alignement is complete.
	# BRAKEHOLD switch ... OFF (right lower instrument panel)
	pushSeqCmd(dt, 'F_B_P_BRAKE', 0)

	pushSeqCmd(dt, 'scriptSpeech', "Manual steps remaining: Set up armament page.  Set lights.  Tune radios.")

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
	
	# Canopy ... Open (lever on right canopy rail)
	pushSeqCmd(dt, 'CANOPY_F_HND', 0)
	pushSeqCmd(6, 'CANOPY_F_HND', 1)

	# Set lights
	# Front console lights
	pushSeqCmd(dt, 'F_INTL_CONSOLE', 0)
	# Rear console lights
	pushSeqCmd(dt, 'R_INTL_CONSOLE', 0)
	# Front instrument panel lights
	pushSeqCmd(dt, 'F_INTL_INSTR', 0)
	# Rear instrument panel lights
	pushSeqCmd(dt, 'R_INTL_INSTR', 0)
	# Front day/night mode
	pushSeqCmd(dt, 'F_INTL_DN_MODE', 1) # 0 = NIGHT, 1 = DAY
	# Rear day/night mode
	pushSeqCmd(dt, 'R_INTL_DN_MODE', 1) # 0 = NIGHT, 1 = DAY
	# HUD ... ON and brightness as desired (knob on UFC)
	pushSeqCmd(dt, 'F_HUD_BRIGHT', 0)
	# HUD day/night mode
	pushSeqCmd(dt, 'F_HUD_D_A_N_MODE', 1) # 0 = DAY, 1 = AUTO, 2 = NIGHT??
	# Front UFC brightness ... As desired (knob on UFC)
	pushSeqCmd(dt, 'F_UFC_LCD_BRIGHT', 0)
	# Rear UFC brightness ... As desired (knob on UFC)
	pushSeqCmd(dt, 'R_UFC_LCD_BRIGHT', 0)
	
	# MIC switch ... OFF
	pushSeqCmd(dt, 'F_MIC_SW', 0)
	
	# OXYGEN supply switch ... OFF (right console forward)
	pushSeqCmd(dt, 'F_OXY_MODE', 0)

	# MFDs ... OFF (click the rocker switch on each MFD)
	# 0 = ON, 1 = middle, 2 = OFF
	pushSeqCmd(dt, 'F_MPD_L_PW', 2)
	pushSeqCmd(dt, 'F_MPD_L_PW', 1)
	pushSeqCmd(dt, 'F_MPD_R_PW', 2)
	pushSeqCmd(dt, 'F_MPD_R_PW', 1)
	pushSeqCmd(dt, 'F_MPCD_C_PW', 2)
	pushSeqCmd(dt, 'F_MPCD_C_PW', 1)

	# INS ... OFF
	pushSeqCmd(dt, 'F_S_INS', 0) # 0 = OFF, 1 = STORE, 2 = GC, 3 = NAV
	
	# IFF mode ... OFF
	pushSeqCmd(dt, 'F_IFF_MODE', 0)

	# IFF reply switch ... OFF
	pushSeqCmd(dt, 'F_IFF_REPLY', 0)

	# TF RDR switch ... OFF (left console middle, behind throttle)
	pushSeqCmd(dt, 'F_S_RDR_TER_FOL', 0) # 0 = OFF, 1 = STBY, 2 = ON
	
	# RDR ALT switch ... OFF (left console middle, behind throttle)
	pushSeqCmd(dt, 'F_S_RDR_ALT', 0) # 0 = OFF, 1 = ON, 2 = OVERIDE

	# RADAR switch ... OFF (left console middle, behind throttle)
	pushSeqCmd(dt, 'F_S_RDR_MODE', 0) # 0 = OFF, 1 = STBY, 2 = ON, 3 = EMERG

	# NCTR switch ... OFF
	pushSeqCmd(dt, 'F_BH_NCTR', 0)
	
	# NAV FLIR switch ... OFF (left console middle, behind throttle)
	pushSeqCmd(dt, 'F_S_NAV_FLIR_SW', 0) # 0 = OFF, 1 = STBY, 2 = ON
	# NAV FLIR GAIN/BRIGHTNESS knob ... As desired (left console middle)
	# TODO, not sure if needed

	# JTIDS knob ... OFF (left console middle, behind throttle)
	pushSeqCmd(dt, 'F_S_JTIDS', 0) # 0 = OFF, 1 = POLL, 2 = NORM, 3 = SIL, 4 = HOLD

	# CAS YAW, ROLL, and PITCH switches ... OFF (left console forward inboard)
	pushSeqCmd(dt, 'F_CAS_YAW', 0)
	pushSeqCmd(dt, 'F_CAS_ROLL', 0)
	pushSeqCmd(dt, 'F_CAS_PITCH', 0)
	
	# SAI (Standby Attitude Indicator) ... Uncage and center (left lower instrument panel)
	pushSeqCmd(dt, 'F_FI_BAK_ADI_CAGE_PULL', 1)
	pushSeqCmd(dt, 'F_FI_BAK_ADI_CAGE_KNOB', int16()) # FIXME??
	pushSeqCmd(dt, 'F_FI_BAK_ADI_CAGE_PULL', 0)

	# BINGO fuel ... zero (right lower instrument panel, knob on fuel gauge)
	#for i in range(40):
		#pushSeqCmd(dt, 'F_FUEL_BINGO', '-3200') # FIXME??  negative numbers not turning knob CCW
	
	# Ejection seat ... SAFE (lever on left forward base of seat)
	pushSeqCmd(dt, 'F_BH_SEAT_ARM', 0)

	# SET UP BACK SEAT
	# All MFDs ... OFF
	# 0 = ON, 1 = middle, 2 = OFF
	pushSeqCmd(dt, 'R_MPCD_L_PW', 2)
	pushSeqCmd(dt, 'R_MPCD_L_PW', 1)
	pushSeqCmd(dt, 'R_MPD_L_PW', 2)
	pushSeqCmd(dt, 'R_MPD_L_PW', 1)
	pushSeqCmd(dt, 'R_MPD_R_PW', 2)
	pushSeqCmd(dt, 'R_MPD_R_PW', 1)
	pushSeqCmd(dt, 'R_MPCD_R_PW', 2)
	pushSeqCmd(dt, 'R_MPCD_R_PW', 1)
	# SAI (Standby Attitude Indicator) ... Uncage and center (instrument panel center)
	pushSeqCmd(dt, 'R_FI_BAK_ADI_CAGE_PULL', 1)
	pushSeqCmd(dt, 'R_FI_BAK_ADI_CAGE_KNOB', int16()) #FIXME??
	pushSeqCmd(dt, 'R_FI_BAK_ADI_CAGE_PULL', 0)
	
	# TGT FLIR switch ... OFF (left console middle, behind left hand controller)
	pushSeqCmd(dt, 'R_TGP_PW', 0) # 0 = OFF, 1 = STBY, 2 = ON
	# LASER switch ... SAFE (left console middle, behind left hand controller)
	pushSeqCmd(dt, 'R_TGP_LASER', 0) # 0 = SAFE, 1 = ARM
	# RWR/ICS mode switch ... TRNG
	pushSeqCmd(dt, 'R_EW_RWR_ICS_MODE', 0) # 0 = TRNG, 1 = COMBAT
	# ICS operational mode switch ... STBY
	pushSeqCmd(dt, 'R_EW_ICS_OP_MODE', 0) # 0 = STBY, 1 = AUTO, 2 = MAN
	# MIC switch ... OFF
	pushSeqCmd(dt, 'R_MIC_SW', 0) # FIXME not working??

	# OXYGEN supply switch ... OFF (right console forward, in front of right hand controller)
	pushSeqCmd(dt, 'R_OXY_MODE', 0)
	# ICS power switch ... OFF
	pushSeqCmd(dt, 'R_TEWS_ICS_PW', 0)
	# RWR switch ... OFF (right console middle, behind right hand controller)
	pushSeqCmd(dt, 'R_TEWS_RWR_PW', 0)
	# EWWS switch ... OFF (right console middle, behind right hand controller)
	pushSeqCmd(dt, 'R_TEWS_EWWS_PW', 0)
	# CMD MODE knob ... OFF (right console middle)
	pushSeqCmd(dt, 'R_CMD_OP_MODE', 0) # 0 = OFF, 1 = STBY, 2 = MAN ONLY, 3 = SEMIAUTO, 4 = AUTO
	
	# Ejection seat ... SAFE (lever on left forward base of seat)
	pushSeqCmd(dt, 'R_TQ_SEAT_ARM', 0)
	# END SET UP BACK SEAT

	# Cut right engine
	# Right throttle to OFF
	pushSeqCmd(dt, 'scriptKeyboard', '{VK_RSHIFT down}{VK_END}{VK_RSHIFT up}')
	
	# Cut left engine
	# Left throttle to OFF
	pushSeqCmd(dt, 'scriptKeyboard', '{VK_LMENU down}{VK_END}{VK_LMENU up}', 'ATTENTION: You must remap Throttle (Left) - IDLE to LAlt+Home') # FIXME pyWinAuto doesn't support RAlt or RCtrl.

	# L and R GEN switches ... OFF
	pushSeqCmd(dt, 'F_GEN_L', 0)
	pushSeqCmd(dt, 'F_GEN_R', 0)
	# L and R ENG CONTR switches ... OFF (right console forward middle)
	pushSeqCmd(dt, 'F_ENG_L_CONTL', 0)
	pushSeqCmd(dt, 'F_ENG_R_CONTL', 0)
	#L and R ENG MASTER switches ... OFF (right console forward, black guarded switches)
	pushSeqCmd(dt, 'F_ENG_L_MASTER_CVR', 1)
	pushSeqCmd(dt, 'F_ENG_L_MASTER', 0)
	pushSeqCmd(dt, 'F_ENG_L_MASTER_CVR', 0)
	pushSeqCmd(dt, 'F_ENG_R_MASTER_CVR', 1)
	pushSeqCmd(dt, 'F_ENG_R_MASTER', 0)
	pushSeqCmd(dt, 'F_ENG_R_MASTER_CVR', 0)
	# STARTER switch ... OFF (right console forward)
	pushSeqCmd(dt, 'F_GEN_JET_START', 0)
	# AIR COND switch ... OFF (right console forward outboard)
	pushSeqCmd(dt, 'F_AC_AUTO_MAN_OFF', 0)
	# L and R INLET switches ... EMERG (left console forward outboard)
	pushSeqCmd(dt, 'F_IN_RAMP_L_SW', 1) # 0 = AUTO, 1 = EMERG
	pushSeqCmd(dt, 'F_IN_RAMP_R_SW', 1) # 0 = AUTO, 1 = EMERG
	
	return seq