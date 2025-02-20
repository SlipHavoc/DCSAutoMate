# Return a Dictionary of script data.  The 'scripts' key is a list of scripts that users will be selecting from.  Each script has an associated 'function', which is the name of the function in this file that will be called to generate the command sequence, and a dictionary of 'vars' that the user will be prompted to choose from before running the script, and will be passed into the sequence generating function.
def getScriptData():
	return {
		'scripts': [
			{
				'name': 'Cold Start',
				'function': 'ColdStart',
				'vars': {
					'Time': ['Day', 'Night'],
					'Alignment': ['Stored Heading'] # , 'Full']
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


###############################################################################
###############################################################################
###############################################################################
###############################################################################
###############################################################################
###############################################################################
###############################################################################
###############################################################################
###############################################################################
###############################################################################
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

	insAlignTimeSH = 1 * 60 + 10 # 1m5s, extra 10 seconds as buffer in case of MP lag.
	insAlignTimeGC = 4 * 60 + 10 # 4m5s, extra 10 seconds as buffer in case of MP lag.

	pushSeqCmd(0, '', '', "Running Cold Start sequence")
	pushSeqCmd(dt, 'scriptSpeech', 'Set throttle to minimum.')

	# Set lights
	if vars.get('Time') == 'Day':
		# Internal lights:
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
		# Front Gauges/UFC backlights
		pushSeqCmd(dt, 'F_INTL_BACK', int16())
		# Rear UFC brightness ... As desired (knob on UFC)
		pushSeqCmd(dt, 'R_UFC_LCD_BRIGHT', int16())
		# Rear Gauges/UFC backlights
		pushSeqCmd(dt, 'R_INTL_BACK', int16())

		# External lights:
		# Anti-collision light
		pushSeqCmd(dt, 'F_EXTL_ANTI_COL', 0)
		# Formation lights
		pushSeqCmd(dt, 'F_EXTL_FORMATION', 0)
		# Position lights
		pushSeqCmd(dt, 'F_EXTL_POS', 0)
		# Tail flood lights
		pushSeqCmd(dt, 'F_EXTL_TFLOOD', 0)
	else:
		# Internal lights:
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
		# Front Gauges/UFC backlights
		pushSeqCmd(dt, 'F_INTL_BACK', int16(0.5))
		# Rear UFC brightness ... As desired (knob on UFC)
		pushSeqCmd(dt, 'R_UFC_LCD_BRIGHT', int16(0.5))
		# Rear Gauges/UFC backlights
		pushSeqCmd(dt, 'R_INTL_BACK', int16(0.5))

		# External lights:
		# Anti-collision light
		pushSeqCmd(dt, 'F_EXTL_ANTI_COL', 0)
		# Formation lights
		pushSeqCmd(dt, 'F_EXTL_FORMATION', 0)
		# Position lights
		pushSeqCmd(dt, 'F_EXTL_POS', 0)
		# Tail flood lights
		pushSeqCmd(dt, 'F_EXTL_TFLOOD', 0)

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
	# Air conditioner ... MIN
	pushSeqCmd(dt, 'F_AC_MAX_NORM_MIN', 0) # 0 = MIN, 1 = NORM, 2 = MAX
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
	pushSeqCmd(dt, 'scriptKeyboard', 'RShift down')
	pushSeqCmd(dt, 'scriptKeyboard', 'home')
	pushSeqCmd(dt, 'scriptKeyboard', 'RShift up')
	pushSeqCmd(50, '', '', 'Right engine at 72% RPM')

	# Start left engine
	# left fingerlift
	pushSeqCmd(dt, 'F_TQ_L_FINGER', 1)
	pushSeqCmd(dt, 'F_TQ_L_FINGER', 0)
	pushSeqCmd(dt, '', '', 'Wait for 26% RPM')
	pushSeqCmd(23, '', '', 'Left engine at 26% RPM')
	# Left throttle to IDLE
	pushSeqCmd(dt, 'scriptKeyboard', 'RAlt down')
	pushSeqCmd(dt, 'scriptKeyboard', 'home')
	pushSeqCmd(dt, 'scriptKeyboard', 'RAlt up')
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
	# Radio 1 Manual mode
	pushSeqCmd(dt, 'F_UFC_KEY_L_GUARD', 1) # Press
	pushSeqCmd(dt, 'F_UFC_KEY_L_GUARD', 0) # Release
	# Radio 2 Manual mode
	pushSeqCmd(dt, 'F_UFC_KEY_R_GUARD', 1) # Press
	pushSeqCmd(dt, 'F_UFC_KEY_R_GUARD', 0) # Release
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
	pushSeqCmd(dt, 'scriptSpeech', "Beginning INS alignment.")
	# INS knob ... STORE for stored heading (1 min), or GC ALIGN (gyrocompass) for full alignment (4 mins)
	if vars.get('Alignment') == 'Stored Heading':
		pushSeqCmd(dt, 'scriptTimerStart', name='alignTimer', duration=insAlignTimeSH)
		pushSeqCmd(dt, 'F_S_INS', 1) # 0 = OFF, 1 = STORE, 2 = GC, 3 = NAV
	else:
		pushSeqCmd(dt, 'scriptTimerStart', name='alignTimer', duration=insAlignTimeGC)
		pushSeqCmd(dt, 'F_S_INS', 2) # 0 = OFF, 1 = STORE, 2 = GC, 3 = NAV

	# IFF mode ... 4A
	pushSeqCmd(dt, 'F_IFF_MODE', 1)

	# IFF reply switch ... LIGHT
	pushSeqCmd(dt, 'F_IFF_REPLY', 2)

	# TF RDR switch ... STBY (left console middle, behind throttle)
	pushSeqCmd(dt, 'F_S_RDR_TER_FOL', 1) # 0 = OFF, 1 = STBY, 2 = ON

	# Auto Fly Up switch
	# FIXME DCS-BIOS bug: You need to edit <username>\Saved Games\DCS.openbeta\Scripts\DCS-BIOS\lib\F-15E.lua and change the "F_BH_FLYUP_CVR" and "F_BH_FLYUP" lines to use device 65, instead of device 17 (second function parameter).  This should be fixed in current DCS-BIOS versions.
	pushSeqCmd(dt, 'F_BH_FLYUP_CVR', 1) # Cover open
	pushSeqCmd(dt, 'F_BH_FLYUP', 1) # 0 = ARMED (down), 1 = DISARMED (up)
	pushSeqCmd(dt, 'F_BH_FLYUP_CVR', 0) # Cover close

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
	pushSeqCmd(dt, 'F_UFC_B9', 1) # Radar alt in HUD
	pushSeqCmd(dt, 'F_UFC_B9', 0)
	pushSeqCmd(dt, 'F_UFC_B3', 1) # TAS in HUD
	pushSeqCmd(dt, 'F_UFC_B3', 0)
	# Return to MENU 1.
	pushSeqCmd(dt, 'F_UFC_KEY_MENU', 1)
	pushSeqCmd(dt, 'F_UFC_KEY_MENU', 0)
	# Disable LAW
	pushSeqCmd(dt, 'F_UFC_B1', 1) # LAW
	pushSeqCmd(dt, 'F_UFC_B1', 0)

	# Set Radio 2 MAN-AM mode ON
	pushSeqCmd(dt, 'F_UFC_B6', 1) # Radio 2
	pushSeqCmd(dt, 'F_UFC_B6', 0)
	pushSeqCmd(dt, 'F_UFC_B9', 1) # MAN-AM
	pushSeqCmd(dt, 'F_UFC_B9', 0)
	# Return to MENU 1.
	pushSeqCmd(dt, 'F_UFC_KEY_MENU', 1)
	pushSeqCmd(dt, 'F_UFC_KEY_MENU', 0)

	# Set up IFF
	pushSeqCmd(dt, 'F_UFC_B3', 1) # IFF
	pushSeqCmd(dt, 'F_UFC_B3', 0)
	pushSeqCmd(dt, 'F_UFC_B9', 1) # MC (Mode C/Charlie, adds pressure altitude to your Mode 3 transmissions)
	pushSeqCmd(dt, 'F_UFC_B9', 0)
	pushSeqCmd(dt, 'F_UFC_B7', 1) # AAI SLV
	pushSeqCmd(dt, 'F_UFC_B7', 0)
	# Return to MENU 1.
	pushSeqCmd(dt, 'F_UFC_KEY_MENU', 1)
	pushSeqCmd(dt, 'F_UFC_KEY_MENU', 0)

	# Set up AAI/EID interrogation
	pushSeqCmd(dt, 'F_UFC_B8', 1) # AAI/EID page
	pushSeqCmd(dt, 'F_UFC_B8', 0)
	pushSeqCmd(dt, 'F_UFC_B7', 1) # AUTO ID (first press sets to STT)
	pushSeqCmd(dt, 'F_UFC_B7', 0)
	pushSeqCmd(dt, 'F_UFC_B7', 1) # AUTO ID (second press sets to PDT (which includes STT))
	pushSeqCmd(dt, 'F_UFC_B7', 0)
	# Return to MENU 1.
	pushSeqCmd(dt, 'F_UFC_KEY_MENU', 1)
	pushSeqCmd(dt, 'F_UFC_KEY_MENU', 0)

	# PROGRAM MFDS
	def pressMfdButtons(frontRear, mfd, buttons):
		frontPrefixes = {
			'left': 'F_MPD_L_',
			'right': 'F_MPD_R_',
			'center': 'F_MPCD_C_',
		}
		rearPrefixes = {
			'leftColor': 'R_MPCD_L_',
			'left': 'R_MPD_L_',
			'right': 'R_MPD_R_',
			'rightColor': 'R_MPCD_R_',
		}

		for button in buttons:
			if frontRear == 'front':
				prefix = frontPrefixes[mfd]
			elif frontRear == 'rear':
				prefix = rearPrefixes[mfd]

			# If it's the POWER button, 0 is on and 1 is back to middle position.
			if button == 'PW':
				# 0 = ON, 1 = middle, 2 = OFF
				pushSeqCmd(dt, prefix + button, 0) # ON
				pushSeqCmd(dt, prefix + button, 1) # middle
			# Else it's a regular button where 1 is press and 0 is release.
			else:
				pushSeqCmd(dt, prefix + button, 1) # Press
				pushSeqCmd(dt, prefix + button, 0) # Release

	# Left MFD
	pressMfdButtons('front', 'left', [
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
	pressMfdButtons('front', 'right', [
		# Return to MENU 1 page from anywhere with Power switch ON.
		'PW', # POWER ON
		# Start programming.
		'B6', # PROG
		'B12', # TPOD
		'B3', # HSI
		'B4', # TF
		# End programming.
		'B6', # PROG
	])

	# Center MFD
	pressMfdButtons('front', 'center', [
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

	# Set up TF radar on Right MFD
	pressMfdButtons('front', 'right', [
		# Start programming.
		'B4', # TF
		'B10', # VLC
		'B1', # 100
		'B5', # SOFT toggle to HARD
		'B11', # M, return to menu
	])

	# Set takeoff trim.
	pushSeqCmd(dt, 'F_CAS_TO_TRIM', 1) # Press
	pushSeqCmd(5, 'F_CAS_TO_TRIM', 0) # Release after 5 seconds

	# Ejection seat ... ARM (lever on left forward base of seat)
	pushSeqCmd(dt, 'F_BH_SEAT_ARM', 1)

	# Master Arm ... ON
	pushSeqCmd(dt, 'F_ARM_MASTER_ARM', 1)

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

	# Left MFCD
	pressMfdButtons('rear', 'leftColor', [
		# Return to MENU 1 page from anywhere with Power switch ON.
		'PW', # POWER ON
		'B17', # HUD
		'B16' if vars.get('Time') == 'Day' else 'B20', # CAM else N-F
	])

	# Left MFD
	pressMfdButtons('rear', 'left', [
		# Return to MENU 1 page from anywhere with Power switch ON.
		'PW', # POWER ON
		'B14', # A/G RDR
	])

	# Right MFD
	pressMfdButtons('rear', 'right', [
		# Return to MENU 1 page from anywhere with Power switch ON.
		'PW', # POWER ON
		'B12', # TPOD
	])

	# Right MFCD
	pressMfdButtons('rear', 'rightColor', [
		# Return to MENU 1 page from anywhere with Power switch ON.
		'PW', # POWER ON
		# Start programming.
		'B13', # TEWS
	])

	# Ejection seat ... ARM (lever on left forward base of seat)
	pushSeqCmd(dt, 'R_TQ_SEAT_ARM', 1)
	# END SET UP BACK SEAT

	# Wait for the INS to finish aligning (total process time minus the difference between now and when the process started).
	pushSeqCmd(dt, 'scriptTimerEnd', name='alignTimer')
	pushSeqCmd(dt, '', '', "INS Aligned")
	# INS knob ... NAV
	pushSeqCmd(dt, 'F_S_INS', 3) # 0 = OFF, 1 = STORE, 2 = GC, 3 = NAV
	pushSeqCmd(dt, 'scriptSpeech', "INS aiignment is complete.")

	# NOTE Should be done after INS alignement is complete.
	# BRAKEHOLD switch ... OFF (right lower instrument panel)
	pushSeqCmd(dt, 'F_B_P_BRAKE', 0)

	pushSeqCmd(dt, 'scriptSpeech', "Manual steps remaining: Set up armament page.  Set laser code.  Set lights.  Tune radios.")

	return seq


###############################################################################
###############################################################################
###############################################################################
###############################################################################
###############################################################################
###############################################################################
###############################################################################
###############################################################################
###############################################################################
###############################################################################
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

	# Set lights
	if vars.get('Time') == 'Day':
		# Internal lights:
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
		# Front Gauges/UFC backlights
		pushSeqCmd(dt, 'F_INTL_BACK', int16())
		# Rear UFC brightness ... As desired (knob on UFC)
		pushSeqCmd(dt, 'R_UFC_LCD_BRIGHT', int16())
		# Rear Gauges/UFC backlights
		pushSeqCmd(dt, 'R_INTL_BACK', int16())

		# External lights:
		# Anti-collision light
		pushSeqCmd(dt, 'F_EXTL_ANTI_COL', 0)
		# Formation lights
		pushSeqCmd(dt, 'F_EXTL_FORMATION', 0)
		# Position lights
		pushSeqCmd(dt, 'F_EXTL_POS', 0)
		# Tail flood lights
		pushSeqCmd(dt, 'F_EXTL_TFLOOD', 0)
	else:
		# Internal lights:
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
		# Front Gauges/UFC backlights
		pushSeqCmd(dt, 'F_INTL_BACK', int16(0.5))
		# Rear UFC brightness ... As desired (knob on UFC)
		pushSeqCmd(dt, 'R_UFC_LCD_BRIGHT', int16(0.5))
		# Rear Gauges/UFC backlights
		pushSeqCmd(dt, 'R_INTL_BACK', int16(0.5))

		# External lights:
		# Anti-collision light
		pushSeqCmd(dt, 'F_EXTL_ANTI_COL', 0)
		# Formation lights
		pushSeqCmd(dt, 'F_EXTL_FORMATION', 0)
		# Position lights
		pushSeqCmd(dt, 'F_EXTL_POS', 0)
		# Tail flood lights
		pushSeqCmd(dt, 'F_EXTL_TFLOOD', 0)

	# Air conditioner ... MIN
	pushSeqCmd(dt, 'F_AC_MAX_NORM_MIN', 0) # 0 = MIN, 1 = NORM, 2 = MAX

	# Radio volumes
	pushSeqCmd(dt, 'F_UFC_COM1_VOL', int16())
	pushSeqCmd(dt, 'F_UFC_COM2_VOL', int16())
	pushSeqCmd(dt, 'F_UFC_COM3_VOL', int16())
	pushSeqCmd(dt, 'F_UFC_COM4_VOL', int16())

	# IFF mode ... 4A
	pushSeqCmd(dt, 'F_IFF_MODE', 1)

	# IFF reply switch ... LIGHT
	pushSeqCmd(dt, 'F_IFF_REPLY', 2)

	# Auto Fly Up switch
	# FIXME DCS-BIOS bug: You need to edit <username>\Saved Games\DCS.openbeta\Scripts\DCS-BIOS\lib\F-15E.lua and change the "F_BH_FLYUP_CVR" and "F_BH_FLYUP" lines to use device 65, instead of device 17 (second function parameter).  This should be fixed in current DCS-BIOS versions.
	pushSeqCmd(dt, 'F_BH_FLYUP_CVR', 1) # Cover open
	pushSeqCmd(dt, 'F_BH_FLYUP', 1) # 0 = ARMED (down), 1 = DISARMED (up)
	pushSeqCmd(dt, 'F_BH_FLYUP_CVR', 0) # Cover close

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
	pushSeqCmd(dt, 'F_UFC_B9', 1) # Radar alt in HUD
	pushSeqCmd(dt, 'F_UFC_B9', 0)
	pushSeqCmd(dt, 'F_UFC_B3', 1) # TAS in HUD
	pushSeqCmd(dt, 'F_UFC_B3', 0)
	# Return to MENU 1.
	pushSeqCmd(dt, 'F_UFC_KEY_MENU', 1)
	pushSeqCmd(dt, 'F_UFC_KEY_MENU', 0)
	# Disable LAW
	pushSeqCmd(dt, 'F_UFC_B1', 1) # LAW
	pushSeqCmd(dt, 'F_UFC_B1', 0)

	# Set Radio 2 MAN-AM mode ON
	pushSeqCmd(dt, 'F_UFC_B6', 1) # Radio 2
	pushSeqCmd(dt, 'F_UFC_B6', 0)
	pushSeqCmd(dt, 'F_UFC_B9', 1) # MAN-AM
	pushSeqCmd(dt, 'F_UFC_B9', 0)
	# Return to MENU 1.
	pushSeqCmd(dt, 'F_UFC_KEY_MENU', 1)
	pushSeqCmd(dt, 'F_UFC_KEY_MENU', 0)

	# Set up IFF
	pushSeqCmd(dt, 'F_UFC_B3', 1) # IFF
	pushSeqCmd(dt, 'F_UFC_B3', 0)
	pushSeqCmd(dt, 'F_UFC_B9', 1) # MC (Mode C/Charlie, adds pressure altitude to your Mode 3 transmissions)
	pushSeqCmd(dt, 'F_UFC_B9', 0)
	pushSeqCmd(dt, 'F_UFC_B7', 1) # AAI SLV
	pushSeqCmd(dt, 'F_UFC_B7', 0)
	# Return to MENU 1.
	pushSeqCmd(dt, 'F_UFC_KEY_MENU', 1)
	pushSeqCmd(dt, 'F_UFC_KEY_MENU', 0)

	# Set up AAI/EID interrogation
	pushSeqCmd(dt, 'F_UFC_B8', 1) # AAI/EID page
	pushSeqCmd(dt, 'F_UFC_B8', 0)
	pushSeqCmd(dt, 'F_UFC_B7', 1) # AUTO ID (first press sets to STT)
	pushSeqCmd(dt, 'F_UFC_B7', 0)
	pushSeqCmd(dt, 'F_UFC_B7', 1) # AUTO ID (second press sets to PDT (which includes STT))
	pushSeqCmd(dt, 'F_UFC_B7', 0)
	# Return to MENU 1.
	pushSeqCmd(dt, 'F_UFC_KEY_MENU', 1)
	pushSeqCmd(dt, 'F_UFC_KEY_MENU', 0)

	# PROGRAM MFDS
	def pressMfdButtons(frontRear, mfd, buttons):
		frontPrefixes = {
			'left': 'F_MPD_L_',
			'right': 'F_MPD_R_',
			'center': 'F_MPCD_C_',
		}
		rearPrefixes = {
			'leftColor': 'R_MPCD_L_',
			'left': 'R_MPD_L_',
			'right': 'R_MPD_R_',
			'rightColor': 'R_MPCD_R_',
		}

		for button in buttons:
			if frontRear == 'front':
				prefix = frontPrefixes[mfd]
			elif frontRear == 'rear':
				prefix = rearPrefixes[mfd]

			# If it's the POWER button, 0 is on and 1 is back to middle position.
			if button == 'PW':
				# 0 = ON, 1 = middle, 2 = OFF
				pushSeqCmd(dt, prefix + button, 0) # ON
				pushSeqCmd(dt, prefix + button, 1) # middle
			# Else it's a regular button where 1 is press and 0 is release.
			else:
				pushSeqCmd(dt, prefix + button, 1) # Press
				pushSeqCmd(dt, prefix + button, 0) # Release

	# Left MFD
	pressMfdButtons('front', 'left', [
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
	pressMfdButtons('front', 'right', [
		# Return to MENU 1 page from anywhere with Power switch ON.
		'PW', # POWER ON
		# Start programming.
		'B6', # PROG
		'B12', # TPOD
		'B3', # HSI
		'B4', # TF
		# End programming.
		'B6', # PROG
	])

	# Center MFD
	pressMfdButtons('front', 'center', [
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

	# Set up TF radar on Right MFD
	pressMfdButtons('front', 'right', [
		# Start programming.
		'B4', # TF
		'B10', # VLC
		'B1', # 100
		'B5', # SOFT toggle to HARD
		'B11', # M, return to menu
	])

	# Master Arm ... ON
	pushSeqCmd(dt, 'F_ARM_MASTER_ARM', 1)

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

	# Left MFCD
	pressMfdButtons('rear', 'leftColor', [
		# Return to MENU 1 page from anywhere with Power switch ON.
		'PW', # POWER ON
		'B17', # HUD
		'B16' if vars.get('Time') == 'Day' else 'B20', # CAM else N-F
	])

	# Left MFD
	pressMfdButtons('rear', 'left', [
		# Return to MENU 1 page from anywhere with Power switch ON.
		'PW', # POWER ON
		'B14', # A/G RDR
	])

	# Right MFD
	pressMfdButtons('rear', 'right', [
		# Return to MENU 1 page from anywhere with Power switch ON.
		'PW', # POWER ON
		'B12', # TPOD
	])

	# Right MFCD
	pressMfdButtons('rear', 'rightColor', [
		# Return to MENU 1 page from anywhere with Power switch ON.
		'PW', # POWER ON
		# Start programming.
		'B13', # TEWS
	])
	# END SET UP BACK SEAT

	pushSeqCmd(dt, 'scriptSpeech', "Manual steps remaining: Set up armament page.  Set laser code.  Set lights.  Tune radios.")

	return seq


###############################################################################
###############################################################################
###############################################################################
###############################################################################
###############################################################################
###############################################################################
###############################################################################
###############################################################################
###############################################################################
###############################################################################
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

	pushSeqCmd(0, '', '', "Running Air Start sequence")

	# Set lights
	if vars.get('Time') == 'Day':
		# Internal lights:
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
		# Front Gauges/UFC backlights
		pushSeqCmd(dt, 'F_INTL_BACK', int16())
		# Rear UFC brightness ... As desired (knob on UFC)
		pushSeqCmd(dt, 'R_UFC_LCD_BRIGHT', int16())
		# Rear Gauges/UFC backlights
		pushSeqCmd(dt, 'R_INTL_BACK', int16())

		# External lights:
		# Anti-collision light
		pushSeqCmd(dt, 'F_EXTL_ANTI_COL', 0)
		# Formation lights
		pushSeqCmd(dt, 'F_EXTL_FORMATION', 0)
		# Position lights
		pushSeqCmd(dt, 'F_EXTL_POS', 0)
		# Tail flood lights
		pushSeqCmd(dt, 'F_EXTL_TFLOOD', 0)
	else:
		# Internal lights:
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
		# Front Gauges/UFC backlights
		pushSeqCmd(dt, 'F_INTL_BACK', int16(0.5))
		# Rear UFC brightness ... As desired (knob on UFC)
		pushSeqCmd(dt, 'R_UFC_LCD_BRIGHT', int16(0.5))
		# Rear Gauges/UFC backlights
		pushSeqCmd(dt, 'R_INTL_BACK', int16(0.5))

		# External lights:
		# Anti-collision light
		pushSeqCmd(dt, 'F_EXTL_ANTI_COL', 0)
		# Formation lights
		pushSeqCmd(dt, 'F_EXTL_FORMATION', 0)
		# Position lights
		pushSeqCmd(dt, 'F_EXTL_POS', 0)
		# Tail flood lights
		pushSeqCmd(dt, 'F_EXTL_TFLOOD', 0)

	# Air conditioner ... MIN
	pushSeqCmd(dt, 'F_AC_MAX_NORM_MIN', 0) # 0 = MIN, 1 = NORM, 2 = MAX

	# Radio volumes
	pushSeqCmd(dt, 'F_UFC_COM1_VOL', int16())
	pushSeqCmd(dt, 'F_UFC_COM2_VOL', int16())
	pushSeqCmd(dt, 'F_UFC_COM3_VOL', int16())
	pushSeqCmd(dt, 'F_UFC_COM4_VOL', int16())

	# IFF mode ... 4A
	pushSeqCmd(dt, 'F_IFF_MODE', 1)

	# IFF reply switch ... LIGHT
	pushSeqCmd(dt, 'F_IFF_REPLY', 2)

	# Auto Fly Up switch
	# FIXME DCS-BIOS bug: You need to edit <username>\Saved Games\DCS.openbeta\Scripts\DCS-BIOS\lib\F-15E.lua and change the "F_BH_FLYUP_CVR" and "F_BH_FLYUP" lines to use device 65, instead of device 17 (second function parameter).  This should be fixed in current DCS-BIOS versions.
	pushSeqCmd(dt, 'F_BH_FLYUP_CVR', 1) # Cover open
	pushSeqCmd(dt, 'F_BH_FLYUP', 1) # 0 = ARMED (down), 1 = DISARMED (up)
	pushSeqCmd(dt, 'F_BH_FLYUP_CVR', 0) # Cover close

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
	pushSeqCmd(dt, 'F_UFC_B9', 1) # Radar alt in HUD
	pushSeqCmd(dt, 'F_UFC_B9', 0)
	pushSeqCmd(dt, 'F_UFC_B3', 1) # TAS in HUD
	pushSeqCmd(dt, 'F_UFC_B3', 0)
	# Return to MENU 1.
	pushSeqCmd(dt, 'F_UFC_KEY_MENU', 1)
	pushSeqCmd(dt, 'F_UFC_KEY_MENU', 0)
	# Disable LAW
	pushSeqCmd(dt, 'F_UFC_B1', 1) # LAW
	pushSeqCmd(dt, 'F_UFC_B1', 0)

	# Set Radio 2 MAN-AM mode ON
	pushSeqCmd(dt, 'F_UFC_B6', 1) # Radio 2
	pushSeqCmd(dt, 'F_UFC_B6', 0)
	pushSeqCmd(dt, 'F_UFC_B9', 1) # MAN-AM
	pushSeqCmd(dt, 'F_UFC_B9', 0)
	# Return to MENU 1.
	pushSeqCmd(dt, 'F_UFC_KEY_MENU', 1)
	pushSeqCmd(dt, 'F_UFC_KEY_MENU', 0)

	# Set up IFF
	pushSeqCmd(dt, 'F_UFC_B3', 1) # IFF
	pushSeqCmd(dt, 'F_UFC_B3', 0)
	pushSeqCmd(dt, 'F_UFC_B9', 1) # MC (Mode C/Charlie, adds pressure altitude to your Mode 3 transmissions)
	pushSeqCmd(dt, 'F_UFC_B9', 0)
	pushSeqCmd(dt, 'F_UFC_B7', 1) # AAI SLV
	pushSeqCmd(dt, 'F_UFC_B7', 0)
	# Return to MENU 1.
	pushSeqCmd(dt, 'F_UFC_KEY_MENU', 1)
	pushSeqCmd(dt, 'F_UFC_KEY_MENU', 0)

	# Set up AAI/EID interrogation
	pushSeqCmd(dt, 'F_UFC_B8', 1) # AAI/EID page
	pushSeqCmd(dt, 'F_UFC_B8', 0)
	pushSeqCmd(dt, 'F_UFC_B7', 1) # AUTO ID (first press sets to STT)
	pushSeqCmd(dt, 'F_UFC_B7', 0)
	pushSeqCmd(dt, 'F_UFC_B7', 1) # AUTO ID (second press sets to PDT (which includes STT))
	pushSeqCmd(dt, 'F_UFC_B7', 0)
	# Return to MENU 1.
	pushSeqCmd(dt, 'F_UFC_KEY_MENU', 1)
	pushSeqCmd(dt, 'F_UFC_KEY_MENU', 0)

	# PROGRAM MFDS
	def pressMfdButtons(frontRear, mfd, buttons):
		frontPrefixes = {
			'left': 'F_MPD_L_',
			'right': 'F_MPD_R_',
			'center': 'F_MPCD_C_',
		}
		rearPrefixes = {
			'leftColor': 'R_MPCD_L_',
			'left': 'R_MPD_L_',
			'right': 'R_MPD_R_',
			'rightColor': 'R_MPCD_R_',
		}

		for button in buttons:
			if frontRear == 'front':
				prefix = frontPrefixes[mfd]
			elif frontRear == 'rear':
				prefix = rearPrefixes[mfd]

			# If it's the POWER button, 0 is on and 1 is back to middle position.
			if button == 'PW':
				# 0 = ON, 1 = middle, 2 = OFF
				pushSeqCmd(dt, prefix + button, 0) # ON
				pushSeqCmd(dt, prefix + button, 1) # middle
			# Else it's a regular button where 1 is press and 0 is release.
			else:
				pushSeqCmd(dt, prefix + button, 1) # Press
				pushSeqCmd(dt, prefix + button, 0) # Release

	# Left MFD
	pressMfdButtons('front', 'left', [
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
	pressMfdButtons('front', 'right', [
		# Return to MENU 1 page from anywhere with Power switch ON.
		'PW', # POWER ON
		# Start programming.
		'B6', # PROG
		'B12', # TPOD
		'B3', # HSI
		'B4', # TF
		# End programming.
		'B6', # PROG
	])

	# Center MFD
	pressMfdButtons('front', 'center', [
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

	# Set up TF radar on Right MFD
	pressMfdButtons('front', 'right', [
		# Start programming.
		'B4', # TF
		'B10', # VLC
		'B1', # 100
		'B5', # SOFT toggle to HARD
		'B11', # M, return to menu
	])

	# Master Arm ... ON
	pushSeqCmd(dt, 'F_ARM_MASTER_ARM', 1)

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

	# Left MFCD
	pressMfdButtons('rear', 'leftColor', [
		# Return to MENU 1 page from anywhere with Power switch ON.
		'PW', # POWER ON
		'B17', # HUD
		'B16' if vars.get('Time') == 'Day' else 'B20', # CAM else N-F
	])

	# Left MFD
	pressMfdButtons('rear', 'left', [
		# Return to MENU 1 page from anywhere with Power switch ON.
		'PW', # POWER ON
		'B14', # A/G RDR
	])

	# Right MFD
	pressMfdButtons('rear', 'right', [
		# Return to MENU 1 page from anywhere with Power switch ON.
		'PW', # POWER ON
		'B12', # TPOD
	])

	# Right MFCD
	pressMfdButtons('rear', 'rightColor', [
		# Return to MENU 1 page from anywhere with Power switch ON.
		'PW', # POWER ON
		# Start programming.
		'B13', # TEWS
	])
	# END SET UP BACK SEAT

	return seq


###############################################################################
###############################################################################
###############################################################################
###############################################################################
###############################################################################
###############################################################################
###############################################################################
###############################################################################
###############################################################################
###############################################################################
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
	pushSeqCmd(dt, 'scriptKeyboard', 'RShift down')
	pushSeqCmd(dt, 'scriptKeyboard', 'end')
	pushSeqCmd(dt, 'scriptKeyboard', 'RShift up')

	# Cut left engine
	# Left throttle to OFF
	pushSeqCmd(dt, 'scriptKeyboard', 'LAlt down')
	pushSeqCmd(dt, 'scriptKeyboard', 'end')
	pushSeqCmd(dt, 'scriptKeyboard', 'LAlt up')

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
