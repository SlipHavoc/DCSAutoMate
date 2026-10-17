# Return a Dictionary of script data.  The 'scripts' key is a list of scripts that users will be selecting from.  Each script has an associated 'function', which is the name of the function in this file that will be called to generate the command sequence, and a dictionary of 'vars' that the user will be prompted to choose from before running the script, and will be passed into the sequence generating function.
import math


def getScriptData():
	return {
		'moduleName': 'F-15ESE',
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
					'alignment': {
						'label': 'Alignment',
						'options': {
							'storedHeading': 'Stored Heading',
							'full': 'Full',
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
			{
				'name': 'Load Route',
				'function': 'LoadRoute',
				'vars': {
					'routeFile': {
						'label': 'Route File',
						'type': 'dropdown',
						'function': 'getRouteFiles',
					},
					'routeName': {
						'label': 'Route Name',
						'type': 'dropdown',
						'function': 'getRouteNames',
						'params': ['routeFile'],
					},
					'altitude': {
						'label': 'Altitude',
						'options': {
							'forceGround': 'Force Ground',
							'useWaypointAltitudes': 'Use Waypoint Altitudes',
						},
					},
					'startingWaypoint': {
						'label': 'Starting Waypoint',
						'type': 'text',
						'default': '1',
					},
					'setAsTargetPoints': {
						'label': 'Set As Target Points',
						'options': {
							'yes': 'Yes',
							'no': 'No',
						},
					},
				},
			},
			{
				'name': 'Load Scratchpad',
				'function': 'LoadScratchpad',
				'vars': {
					'scratchpadFile': {
						'label': 'Scratchpad File',
						'type': 'dropdown',
						'function': 'getScratchpadFiles',
					},
					'startingWaypoint': {
						'label': 'Starting Waypoint',
						'type': 'text',
						'default': '1',
					},
					'setAsTargetPoints': {
						'label': 'Set As Target Points',
						'options': {
							'yes': 'Yes',
							'no': 'No',
						},
					},
				},
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
			#		'startingWaypoint': {
			#			'label': 'Starting Waypoint',
			#			'type': 'text',
			#			'default': '1',
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
def ColdStart(config, vars, helper, *args, **kwargs):
	seq = []
	dt = 0.3

	pushSeqCmd = helper.makePushSeqCmd(seq)

	insAlignTimeSH = 1 * 60 + 10 # 1m5s, extra 10 seconds as buffer in case of MP lag.
	insAlignTimeGC = 4 * 60 + 10 # 4m5s, extra 10 seconds as buffer in case of MP lag.

	pushSeqCmd(0, '', '', "Running Cold Start sequence")
	pushSeqCmd(dt, 'scriptSpeech', 'Set throttle to minimum.')

	# Set lights
	if vars.get('time') == 'day':
		# Internal lights:
		# Front console lights
		pushSeqCmd(dt, 'INTLT.console_lt_knob', 1.0)
		# Rear console lights
		pushSeqCmd(dt, 'INTLT.rc_console_lt_knob', 1.0)
		# Front instrument panel lights
		pushSeqCmd(dt, 'INTLT.inst_pnl_lt_knob', 1.0)
		# Rear instrument panel lights
		pushSeqCmd(dt, 'INTLT.rc_inst_pnl_lt_knob', 1.0)
		# Front day/night mode
		pushSeqCmd(dt, 'INTLT.daynite_mode_sw', 1) # 0 = NIGHT, 1 = DAY
		# Rear day/night mode
		pushSeqCmd(dt, 'INTLT.rc_daynite_mode_sw', 1) # 0 = NIGHT, 1 = DAY
		# HUD ... ON and brightness as desired (knob on UFC)
		pushSeqCmd(dt, 'HUDCTRL.HUD_BRT_Knob', 1.0)
		# HUD day/night mode
		pushSeqCmd(dt, 'HUDCTRL.HUD_MODE_Switch', 0) # 0 = DAY, 1 = AUTO, 2 = NIGHT??
		# Front UFC brightness ... As desired (knob on UFC)
		pushSeqCmd(dt, 'UFCCTRL_FRONT.UFC_BRT_CTRL', 1.0)
		# Front Gauges/UFC backlights
		pushSeqCmd(dt, 'INTLT.ufc_bcklt_br_knob', 1.0)
		# Rear UFC brightness ... As desired (knob on UFC)
		pushSeqCmd(dt, 'UFCCTRL_REAR.UFC_BRT_CTRL', 1.0)
		# Rear Gauges/UFC backlights
		pushSeqCmd(dt, 'INTLT.rc_ufc_bcklt_br_knob', 1.0)

		# External lights:
		# Anti-collision light
		pushSeqCmd(dt, 'EXTLT.anticoll_lt_sw', 0)
		# Formation lights
		pushSeqCmd(dt, 'EXTLT.formation_lt_knob', 0)
		# Position lights
		pushSeqCmd(dt, 'EXTLT.pos_lt_knob', 0)
		# Tail flood lights
		pushSeqCmd(dt, 'EXTLT.vert_tail_lt_sw', 0)
	else:
		# Internal lights:
		# Front console lights
		pushSeqCmd(dt, 'INTLT.console_lt_knob', 0.5)
		# Rear console lights
		pushSeqCmd(dt, 'INTLT.rc_console_lt_knob', 0.5)
		# Front instrument panel lights
		pushSeqCmd(dt, 'INTLT.inst_pnl_lt_knob', 0.5)
		# Rear instrument panel lights
		pushSeqCmd(dt, 'INTLT.rc_inst_pnl_lt_knob', 0.5)
		# Front day/night mode
		pushSeqCmd(dt, 'INTLT.daynite_mode_sw', 0) # 0 = NIGHT, 1 = DAY
		# Rear day/night mode
		pushSeqCmd(dt, 'INTLT.rc_daynite_mode_sw', 0) # 0 = NIGHT, 1 = DAY
		# HUD ... ON and brightness as desired (knob on UFC)
		pushSeqCmd(dt, 'HUDCTRL.HUD_BRT_Knob', 0.5)
		# HUD day/night mode
		pushSeqCmd(dt, 'HUDCTRL.HUD_MODE_Switch', 2) # 0 = DAY, 1 = AUTO, 2 = NIGHT??
		# Front UFC brightness ... As desired (knob on UFC)
		pushSeqCmd(dt, 'UFCCTRL_FRONT.UFC_BRT_CTRL', 0.5)
		# Front Gauges/UFC backlights
		pushSeqCmd(dt, 'INTLT.ufc_bcklt_br_knob', 0.5)
		# Rear UFC brightness ... As desired (knob on UFC)
		pushSeqCmd(dt, 'UFCCTRL_REAR.UFC_BRT_CTRL', 0.5)
		# Rear Gauges/UFC backlights
		pushSeqCmd(dt, 'INTLT.rc_ufc_bcklt_br_knob', 0.5)

		# External lights:
		# Anti-collision light
		pushSeqCmd(dt, 'EXTLT.anticoll_lt_sw', 0)
		# Formation lights
		pushSeqCmd(dt, 'EXTLT.formation_lt_knob', 0)
		# Position lights
		pushSeqCmd(dt, 'EXTLT.pos_lt_knob', 0)
		# Tail flood lights
		pushSeqCmd(dt, 'EXTLT.vert_tail_lt_sw', 0)

	# L and R GEN switches ... ON
	pushSeqCmd(dt, 'EPSS.generator_left_sw', 1)
	pushSeqCmd(dt, 'EPSS.generator_right_sw', 1)
	# L and R ENG CONTR switches ... ON (right console forward middle)
	pushSeqCmd(dt, 'DEEC.left_eng_ctrl_sw', 1)
	pushSeqCmd(dt, 'DEEC.right_eng_ctrl_sw', 1)
	#L and R ENG MASTER switches ... ON (right console forward, black guarded switches)
	pushSeqCmd(dt, 'DEEC.left_eng_master_cover', 1)
	pushSeqCmd(dt, 'DEEC.left_eng_master_sw', 1)
	pushSeqCmd(dt, 'DEEC.left_eng_master_cover', 0)
	pushSeqCmd(dt, 'DEEC.right_eng_master_cover', 1)
	pushSeqCmd(dt, 'DEEC.right_eng_master_sw', 1)
	pushSeqCmd(dt, 'DEEC.right_eng_master_cover', 0)
	# STARTER switch ... ON (right console forward)
	pushSeqCmd(dt, 'EPSS.starter_gen_sw', 1)
	# AIR COND switch ... AUTO (right console forward outboard)
	pushSeqCmd(dt, 'ECS.airco_auto_man_off_sw', 2)
	# Air conditioner ... MIN
	pushSeqCmd(dt, 'ECS.airco_max_norm_min_sw', 0) # 0 = MIN, 1 = NORM, 2 = MAX
	# CONF TANK switch ... TRANS (left console forward)
	#pushSeqCmd(dt, 'AFSS.fueltrnfr_cft_sw', 2) # Should be on NORM I think??
	# L and R INLET switches ... AUTO (left console forward outboard)
	pushSeqCmd(dt, 'DEEC.left_inlet_sw', 0) # 0 = AUTO, 1 = EMERG
	pushSeqCmd(dt, 'DEEC.right_inlet_sw', 0) # 0 = AUTO, 1 = EMERG
	# JET FUEL STARTER handle ... Pull (left click) (right lower instrument panel)
	pushSeqCmd(dt, 'EPSS.cmd_3386', 1)
	#pushSeqCmd(1, 'EPSS.cmd_3386', 0)
	# Wait for Ready light to turn on.
	pushSeqCmd(5, '', '', 'Starter Ready light is on')

	# Start right engine
	# Right fingerlift
	pushSeqCmd(dt, 'DEEC.right_eng_finger_lift', 1)
	pushSeqCmd(dt, 'DEEC.right_eng_finger_lift', 0)
	pushSeqCmd(dt, '', '', 'Wait for 26% RPM')
	pushSeqCmd(23, '', '', 'Right engine at 26% RPM')
	# Right throttle to IDLE
	pushSeqCmd(dt, 'scriptSimCommand', 'iCommandRightEngineStart') # Right throttle IDLE
	pushSeqCmd(50, '', '', 'Right engine at 72% RPM')

	# Start left engine
	# left fingerlift
	pushSeqCmd(dt, 'DEEC.left_eng_finger_lift', 1)
	pushSeqCmd(dt, 'DEEC.left_eng_finger_lift', 0)
	pushSeqCmd(dt, '', '', 'Wait for 26% RPM')
	pushSeqCmd(23, '', '', 'Left engine at 26% RPM')
	# Left throttle to IDLE
	pushSeqCmd(dt, 'scriptSimCommand', 'iCommandLeftEngineStart') # Left throttle IDLE
	pushSeqCmd(50, '', '', 'Left engine at 72% RPM')

	# BRAKEHOLD switch ... ON
	pushSeqCmd(dt, 'LGS.park_brake_sw', 1)

	# MIC switch ... ON
	pushSeqCmd(dt, 'ICS.cmd_3509', 1)

	# Radios
	# Radio 1 ... ON
	pushSeqCmd(dt, 'UFCCTRL_FRONT.UFC_PRESET_SW_LEFT', 1)
	pushSeqCmd(dt, 'UFCCTRL_FRONT.UFC_PRESET_SW_LEFT', 0)
	# Radio 2 ... ON
	pushSeqCmd(dt, 'UFCCTRL_FRONT.UFC_PRESET_SW_RIGHT', 1)
	pushSeqCmd(dt, 'UFCCTRL_FRONT.UFC_PRESET_SW_RIGHT', 0)
	# Radio 1 Manual mode
	pushSeqCmd(dt, 'UFCCTRL_FRONT.UFC_GREC_CM_LEFT', 1) # Press
	pushSeqCmd(dt, 'UFCCTRL_FRONT.UFC_GREC_CM_LEFT', 0) # Release
	# Radio 2 Manual mode
	pushSeqCmd(dt, 'UFCCTRL_FRONT.UFC_GREC_CM_RIGHT', 1) # Press
	pushSeqCmd(dt, 'UFCCTRL_FRONT.UFC_GREC_CM_RIGHT', 0) # Release
	# Radio volumes
	pushSeqCmd(dt, 'UFCCTRL_FRONT.UFC_VOL_R1', 1.0)
	pushSeqCmd(dt, 'UFCCTRL_FRONT.UFC_VOL_R2', 1.0)
	pushSeqCmd(dt, 'UFCCTRL_FRONT.UFC_VOL_R3', 1.0)
	pushSeqCmd(dt, 'UFCCTRL_FRONT.UFC_VOL_R4', 1.0)

	# OXYGEN supply switch ... ON (right console forward)
	pushSeqCmd(dt, 'ECS.oxy_pbg_on_off_sw', 1)

	# Canopy ... Close and seal (lever on right canopy rail)
	pushSeqCmd(dt, 'CNPYSYST.cnpy_lever', 2)
	pushSeqCmd(6, 'CNPYSYST.cnpy_lever', 3)

	# MFDs ... ON (click the rocker switch on each MFD)
	# 0 = ON, 1 = middle, 2 = OFF
	pushSeqCmd(dt, 'MPD_FLEFT.Switch_Power', 0)
	pushSeqCmd(dt, 'MPD_FLEFT.Switch_Power', 1)
	pushSeqCmd(dt, 'MPD_FRIGHT.Switch_Power', 0)
	pushSeqCmd(dt, 'MPD_FRIGHT.Switch_Power', 1)
	pushSeqCmd(dt, 'MPCD_FCENTER.Switch_Power', 0)
	pushSeqCmd(dt, 'MPCD_FCENTER.Switch_Power', 1)

	# Begin alignment
	pushSeqCmd(dt, 'scriptSpeech', "Beginning INS alignment.")
	# INS knob ... STORE for stored heading (1 min), or GC ALIGN (gyrocompass) for full alignment (4 mins)
	if vars.get('alignment') == 'storedHeading':
		pushSeqCmd(dt, 'scriptTimerStart', name='alignTimer', duration=insAlignTimeSH)
		pushSeqCmd(dt, 'INS.ins_knob', 1) # 0 = OFF, 1 = STORE, 2 = GC, 3 = NAV
	else:
		pushSeqCmd(dt, 'scriptTimerStart', name='alignTimer', duration=insAlignTimeGC)
		pushSeqCmd(dt, 'INS.ins_knob', 2) # 0 = OFF, 1 = STORE, 2 = GC, 3 = NAV

	# IFF mode ... 4A
	pushSeqCmd(dt, 'IFF_TRN.mode_sw', 1)

	# IFF reply switch ... LIGHT
	pushSeqCmd(dt, 'IFF_TRN.rec_sw', 2)

	# TF RDR switch ... STBY (left console middle, behind throttle)
	pushSeqCmd(dt, 'TFR.tf_rdr_sw', 1) # 0 = OFF, 1 = STBY, 2 = ON

	# Auto Fly Up switch
	pushSeqCmd(dt, 'TFR.flyup_cover', 1) # Cover open
	pushSeqCmd(dt, 'TFR.flyup_sw', 1) # 0 = ARMED (down), 1 = DISARMED (up)
	pushSeqCmd(dt, 'TFR.flyup_cover', 0) # Cover close

	# RDR ALT switch ... ON (left console middle, behind throttle)
	pushSeqCmd(dt, 'CARA.rdr_alt_sw', 1) # 0 = OFF, 1 = ON, 2 = OVERIDE

	# RADAR switch ... ON (radar will stay off while weight-on-wheels) (left console middle, behind throttle)
	pushSeqCmd(dt, 'AN_APG70.rdr_power_sw', 2) # 0 = OFF, 1 = STBY, 2 = ON, 3 = EMERG

	# NCTR switch ... ON
	pushSeqCmd(dt, 'AN_APG70.nctr_sw', 1)

	# NAV FLIR switch ... ON (turns on NAV FLIR for use in both MFD and HUD) (left console middle, behind throttle)
	pushSeqCmd(dt, 'NAVPOD.nav_flir_sw', 2) # 0 = OFF, 1 = STBY, 2 = ON
	# NAV FLIR GAIN/BRIGHTNESS knob ... As desired (left console middle)
	# TODO, not sure if needed

	# JTIDS knob ... NORM (left console middle, behind throttle)
	pushSeqCmd(dt, 'RDRCTRL_AA.jtids_knob', 2) # 0 = OFF, 1 = POLL, 2 = NORM, 3 = SIL, 4 = HOLD

	# CAS YAW, ROLL, and PITCH switches ... ON (left console forward inboard)
	pushSeqCmd(dt, 'FLCTRL.cmd_3452', 1)
	pushSeqCmd(dt, 'FLCTRL.cmd_3453', 1)
	pushSeqCmd(dt, 'FLCTRL.pitch_sw', 1)

	# SAI (Standby Attitude Indicator) ... Uncage and center (left lower instrument panel)
	pushSeqCmd(dt, 'FLINST.art_hor_uncage', 1)
	pushSeqCmd(dt, 'FLINST.art_hor_adj', 0.5)
	pushSeqCmd(dt, 'FLINST.art_hor_uncage', 0)

	# Backup altimeter ... Set to match QNH (current altitude above sea level)
	# TODO

	# Fuel totalizer ... EXT WNG
	pushSeqCmd(dt, 'FLINST.fuelqty_totalizer', 3) # 0 = FEED, 1 = INTL WNG, 2 = TANK 1, 3 = EXT WNG, 4 = EXT CTR, 5 = CONF TANK, not sure if BIT is selectable??

	# BINGO fuel ... As desired (4000 lbs is a good default??) (right lower instrument panel, knob on fuel gauge)
	for i in range(40):
		pushSeqCmd(dt, 'FLINST.cmd_3385', 0.1)

	# Add UFC DATA to HUD
	# Return to MENU 1 screen from anywhere with DATA, MENU.  Go to DATA 1 screen from anywhere with MENU, DATA.
	pushSeqCmd(dt, 'UFCCTRL_FRONT.UFC_MENU', 1)
	pushSeqCmd(dt, 'UFCCTRL_FRONT.UFC_MENU', 0)
	pushSeqCmd(dt, 'UFCCTRL_FRONT.UFC_DATA', 1)
	pushSeqCmd(dt, 'UFCCTRL_FRONT.UFC_DATA', 0)
	pushSeqCmd(dt, 'UFCCTRL_FRONT.UFC_PB_9', 1) # Radar alt in HUD
	pushSeqCmd(dt, 'UFCCTRL_FRONT.UFC_PB_9', 0)
	pushSeqCmd(dt, 'UFCCTRL_FRONT.UFC_PB_3', 1) # TAS in HUD
	pushSeqCmd(dt, 'UFCCTRL_FRONT.UFC_PB_3', 0)
	# Return to MENU 1.
	pushSeqCmd(dt, 'UFCCTRL_FRONT.UFC_MENU', 1)
	pushSeqCmd(dt, 'UFCCTRL_FRONT.UFC_MENU', 0)
	# Disable LAW
	pushSeqCmd(dt, 'UFCCTRL_FRONT.UFC_PB_1', 1) # LAW
	pushSeqCmd(dt, 'UFCCTRL_FRONT.UFC_PB_1', 0)

	# Set Radio 2 MAN-AM mode ON
	pushSeqCmd(dt, 'UFCCTRL_FRONT.UFC_PB_6', 1) # Radio 2
	pushSeqCmd(dt, 'UFCCTRL_FRONT.UFC_PB_6', 0)
	pushSeqCmd(dt, 'UFCCTRL_FRONT.UFC_PB_9', 1) # MAN-AM
	pushSeqCmd(dt, 'UFCCTRL_FRONT.UFC_PB_9', 0)
	# Return to MENU 1.
	pushSeqCmd(dt, 'UFCCTRL_FRONT.UFC_MENU', 1)
	pushSeqCmd(dt, 'UFCCTRL_FRONT.UFC_MENU', 0)

	# Set up IFF
	pushSeqCmd(dt, 'UFCCTRL_FRONT.UFC_PB_3', 1) # IFF
	pushSeqCmd(dt, 'UFCCTRL_FRONT.UFC_PB_3', 0)
	pushSeqCmd(dt, 'UFCCTRL_FRONT.UFC_PB_9', 1) # MC (Mode C/Charlie, adds pressure altitude to your Mode 3 transmissions)
	pushSeqCmd(dt, 'UFCCTRL_FRONT.UFC_PB_9', 0)
	pushSeqCmd(dt, 'UFCCTRL_FRONT.UFC_PB_7', 1) # AAI SLV
	pushSeqCmd(dt, 'UFCCTRL_FRONT.UFC_PB_7', 0)
	# Return to MENU 1.
	pushSeqCmd(dt, 'UFCCTRL_FRONT.UFC_MENU', 1)
	pushSeqCmd(dt, 'UFCCTRL_FRONT.UFC_MENU', 0)

	# Set up AAI/EID interrogation
	pushSeqCmd(dt, 'UFCCTRL_FRONT.UFC_PB_8', 1) # AAI/EID page
	pushSeqCmd(dt, 'UFCCTRL_FRONT.UFC_PB_8', 0)
	pushSeqCmd(dt, 'UFCCTRL_FRONT.UFC_PB_7', 1) # AUTO ID (first press sets to STT)
	pushSeqCmd(dt, 'UFCCTRL_FRONT.UFC_PB_7', 0)
	pushSeqCmd(dt, 'UFCCTRL_FRONT.UFC_PB_7', 1) # AUTO ID (second press sets to PDT (which includes STT))
	pushSeqCmd(dt, 'UFCCTRL_FRONT.UFC_PB_7', 0)
	# Return to MENU 1.
	pushSeqCmd(dt, 'UFCCTRL_FRONT.UFC_MENU', 1)
	pushSeqCmd(dt, 'UFCCTRL_FRONT.UFC_MENU', 0)

	# PROGRAM MFDS
	def pressMfdButtons(frontRear, mfd, buttons):
		frontPrefixes = {
			'left': 'MPD_FLEFT',
			'right': 'MPD_FRIGHT',
			'center': 'MPCD_FCENTER',
		}
		rearPrefixes = {
			'leftColor': 'MPCD_RLEFT',
			'left': 'MPD_RLEFT',
			'right': 'MPD_RRIGHT',
			'rightColor': 'MPCD_RRIGHT',
		}

		for button in buttons:
			if frontRear == 'front':
				device = frontPrefixes[mfd]
			elif frontRear == 'rear':
				device = rearPrefixes[mfd]

			# If it's the POWER button, 0 is on and 1 is back to middle position.
			if button == 'PW':
				# 0 = ON, 1 = middle, 2 = OFF
				pushSeqCmd(dt, device + '.Switch_Power', 0) # ON
				pushSeqCmd(dt, device + '.Switch_Power', 1) # middle
			# Else it's a regular button where 1 is press and 0 is release.
			else:
				btnNum = int(button[1:])
				btnName = device + f'.Button_{btnNum:02d}'
				pushSeqCmd(dt, btnName, 1) # Press
				pushSeqCmd(dt, btnName, 0) # Release

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
	pushSeqCmd(dt, 'FLCTRL.cmd_3457', 1) # Press
	pushSeqCmd(5, 'FLCTRL.cmd_3457', 0) # Release after 5 seconds

	# Ejection seat ... ARM (lever on left forward base of seat)
	pushSeqCmd(dt, 'CNPYSYST.seat_arm_handle', 1)

	# Master Arm ... ON
	pushSeqCmd(dt, 'PACS.Master_Arm_SW', 1)

	# SET UP BACK SEAT
	# All MFDs ... ON
	# 0 = ON, 1 = middle, 2 = OFF
	pushSeqCmd(dt, 'MPCD_RLEFT.Switch_Power', 0)
	pushSeqCmd(dt, 'MPCD_RLEFT.Switch_Power', 1)
	pushSeqCmd(dt, 'MPD_RLEFT.Switch_Power', 0)
	pushSeqCmd(dt, 'MPD_RLEFT.Switch_Power', 1)
	pushSeqCmd(dt, 'MPD_RRIGHT.Switch_Power', 0)
	pushSeqCmd(dt, 'MPD_RRIGHT.Switch_Power', 1)
	pushSeqCmd(dt, 'MPCD_RRIGHT.Switch_Power', 0)
	pushSeqCmd(dt, 'MPCD_RRIGHT.Switch_Power', 1)
	# SAI (Standby Attitude Indicator) ... Uncage and center (instrument panel center)
	pushSeqCmd(dt, 'FLINST.cmd_3401', 1)
	pushSeqCmd(dt, 'FLINST.rc_art_hor_adj', 0.5)
	pushSeqCmd(dt, 'FLINST.cmd_3401', 0)
	# Backup altimeter ... Set to match QNH (current altitude above sea level)
	# TODO

	# Radio volumes
	pushSeqCmd(dt, 'UFCCTRL_REAR.UFC_VOL_R1', 1.0)
	pushSeqCmd(dt, 'UFCCTRL_REAR.UFC_VOL_R2', 1.0)
	pushSeqCmd(dt, 'UFCCTRL_REAR.UFC_VOL_R3', 1.0)
	pushSeqCmd(dt, 'UFCCTRL_REAR.UFC_VOL_R4', 1.0)

	# TGT FLIR switch ... ON (left console middle, behind left hand controller)
	pushSeqCmd(dt, 'TGPCTRL.tpod_pwr_sw', 2) # 0 = OFF, 1 = STBY, 2 = ON
	# LASER switch ... ARM (left console middle, behind left hand controller)
	pushSeqCmd(dt, 'TGPCTRL.tpod_laser_sw', 1) # 0 = SAFE, 1 = ARM
	# RWR/ICS mode switch ... COMBAT
	pushSeqCmd(dt, 'TEWS.rwr_ics_mode_sw', 1) # 0 = TRNG, 1 = COMBAT
	# ICS operational mode switch ... AUTO
	pushSeqCmd(dt, 'EWS_JMR.ics_mode_sw', 1) # 0 = STBY, 1 = AUTO, 2 = MAN
	# MIC switch ... ON
	pushSeqCmd(dt, 'ICS.cmd_3427', 1)

	# OXYGEN supply switch ... ON (right console forward, in front of right hand controller)
	pushSeqCmd(dt, 'ECS.cmd_3573', 1)
	# ICS power switch ... ON
	pushSeqCmd(dt, 'EWS_JMR.ics_power_sw', 1)
	# RWR switch ... ON (right console middle, behind right hand controller)
	pushSeqCmd(dt, 'TEWS.rwr_power_sw', 1)
	# EWWS switch ... ON (right console middle, behind right hand controller)
	pushSeqCmd(dt, 'TEWS.ewss_power_sw', 1)
	# CMD MODE knob ... SEMIAUTO (right console middle)
	pushSeqCmd(dt, 'EWS_CMD.cmd_mode_knob', 3) # 0 = OFF, 1 = STBY, 2 = MAN ONLY, 3 = SEMIAUTO, 4 = AUTO

	# Left MFCD
	pressMfdButtons('rear', 'leftColor', [
		# Return to MENU 1 page from anywhere with Power switch ON.
		'PW', # POWER ON
		'B17', # HUD
		'B16' if vars.get('time') == 'day' else 'B20', # CAM else N-F
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
	pushSeqCmd(dt, 'CNPYSYST.seat_arm_handle_rc', 1)
	# END SET UP BACK SEAT

	# Wait for the INS to finish aligning (total process time minus the difference between now and when the process started).
	pushSeqCmd(dt, 'scriptTimerEnd', name='alignTimer')
	pushSeqCmd(dt, '', '', "INS Aligned")
	# INS knob ... NAV
	pushSeqCmd(dt, 'INS.ins_knob', 3) # 0 = OFF, 1 = STORE, 2 = GC, 3 = NAV
	pushSeqCmd(dt, 'scriptSpeech', "INS aiignment is complete.")

	# NOTE Should be done after INS alignement is complete.
	# BRAKEHOLD switch ... OFF (right lower instrument panel)
	pushSeqCmd(dt, 'LGS.park_brake_sw', 0)

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
def HotStart(config, vars, helper, *args, **kwargs):
	seq = []
	dt = 0.3

	pushSeqCmd = helper.makePushSeqCmd(seq)

	pushSeqCmd(0, '', '', "Running Hot Start sequence")

	# Set lights
	if vars.get('time') == 'day':
		# Internal lights:
		# Front console lights
		pushSeqCmd(dt, 'INTLT.console_lt_knob', 1.0)
		# Rear console lights
		pushSeqCmd(dt, 'INTLT.rc_console_lt_knob', 1.0)
		# Front instrument panel lights
		pushSeqCmd(dt, 'INTLT.inst_pnl_lt_knob', 1.0)
		# Rear instrument panel lights
		pushSeqCmd(dt, 'INTLT.rc_inst_pnl_lt_knob', 1.0)
		# Front day/night mode
		pushSeqCmd(dt, 'INTLT.daynite_mode_sw', 1) # 0 = NIGHT, 1 = DAY
		# Rear day/night mode
		pushSeqCmd(dt, 'INTLT.rc_daynite_mode_sw', 1) # 0 = NIGHT, 1 = DAY
		# HUD ... ON and brightness as desired (knob on UFC)
		pushSeqCmd(dt, 'HUDCTRL.HUD_BRT_Knob', 1.0)
		# HUD day/night mode
		pushSeqCmd(dt, 'HUDCTRL.HUD_MODE_Switch', 0) # 0 = DAY, 1 = AUTO, 2 = NIGHT??
		# Front UFC brightness ... As desired (knob on UFC)
		pushSeqCmd(dt, 'UFCCTRL_FRONT.UFC_BRT_CTRL', 1.0)
		# Front Gauges/UFC backlights
		pushSeqCmd(dt, 'INTLT.ufc_bcklt_br_knob', 1.0)
		# Rear UFC brightness ... As desired (knob on UFC)
		pushSeqCmd(dt, 'UFCCTRL_REAR.UFC_BRT_CTRL', 1.0)
		# Rear Gauges/UFC backlights
		pushSeqCmd(dt, 'INTLT.rc_ufc_bcklt_br_knob', 1.0)

		# External lights:
		# Anti-collision light
		pushSeqCmd(dt, 'EXTLT.anticoll_lt_sw', 0)
		# Formation lights
		pushSeqCmd(dt, 'EXTLT.formation_lt_knob', 0)
		# Position lights
		pushSeqCmd(dt, 'EXTLT.pos_lt_knob', 0)
		# Tail flood lights
		pushSeqCmd(dt, 'EXTLT.vert_tail_lt_sw', 0)
	else:
		# Internal lights:
		# Front console lights
		pushSeqCmd(dt, 'INTLT.console_lt_knob', 0.5)
		# Rear console lights
		pushSeqCmd(dt, 'INTLT.rc_console_lt_knob', 0.5)
		# Front instrument panel lights
		pushSeqCmd(dt, 'INTLT.inst_pnl_lt_knob', 0.5)
		# Rear instrument panel lights
		pushSeqCmd(dt, 'INTLT.rc_inst_pnl_lt_knob', 0.5)
		# Front day/night mode
		pushSeqCmd(dt, 'INTLT.daynite_mode_sw', 0) # 0 = NIGHT, 1 = DAY
		# Rear day/night mode
		pushSeqCmd(dt, 'INTLT.rc_daynite_mode_sw', 0) # 0 = NIGHT, 1 = DAY
		# HUD ... ON and brightness as desired (knob on UFC)
		pushSeqCmd(dt, 'HUDCTRL.HUD_BRT_Knob', 0.5)
		# HUD day/night mode
		pushSeqCmd(dt, 'HUDCTRL.HUD_MODE_Switch', 2) # 0 = DAY, 1 = AUTO, 2 = NIGHT??
		# Front UFC brightness ... As desired (knob on UFC)
		pushSeqCmd(dt, 'UFCCTRL_FRONT.UFC_BRT_CTRL', 0.5)
		# Front Gauges/UFC backlights
		pushSeqCmd(dt, 'INTLT.ufc_bcklt_br_knob', 0.5)
		# Rear UFC brightness ... As desired (knob on UFC)
		pushSeqCmd(dt, 'UFCCTRL_REAR.UFC_BRT_CTRL', 0.5)
		# Rear Gauges/UFC backlights
		pushSeqCmd(dt, 'INTLT.rc_ufc_bcklt_br_knob', 0.5)

		# External lights:
		# Anti-collision light
		pushSeqCmd(dt, 'EXTLT.anticoll_lt_sw', 0)
		# Formation lights
		pushSeqCmd(dt, 'EXTLT.formation_lt_knob', 0)
		# Position lights
		pushSeqCmd(dt, 'EXTLT.pos_lt_knob', 0)
		# Tail flood lights
		pushSeqCmd(dt, 'EXTLT.vert_tail_lt_sw', 0)

	# Air conditioner ... MIN
	pushSeqCmd(dt, 'ECS.airco_max_norm_min_sw', 0) # 0 = MIN, 1 = NORM, 2 = MAX

	# Radio volumes
	pushSeqCmd(dt, 'UFCCTRL_FRONT.UFC_VOL_R1', 1.0)
	pushSeqCmd(dt, 'UFCCTRL_FRONT.UFC_VOL_R2', 1.0)
	pushSeqCmd(dt, 'UFCCTRL_FRONT.UFC_VOL_R3', 1.0)
	pushSeqCmd(dt, 'UFCCTRL_FRONT.UFC_VOL_R4', 1.0)

	# IFF mode ... 4A
	pushSeqCmd(dt, 'IFF_TRN.mode_sw', 1)

	# IFF reply switch ... LIGHT
	pushSeqCmd(dt, 'IFF_TRN.rec_sw', 2)

	# Auto Fly Up switch
	pushSeqCmd(dt, 'TFR.flyup_cover', 1) # Cover open
	pushSeqCmd(dt, 'TFR.flyup_sw', 1) # 0 = ARMED (down), 1 = DISARMED (up)
	pushSeqCmd(dt, 'TFR.flyup_cover', 0) # Cover close

	# RADAR switch ... ON (radar will stay off while weight-on-wheels) (left console middle, behind throttle)
	pushSeqCmd(dt, 'AN_APG70.rdr_power_sw', 2) # 0 = OFF, 1 = STBY, 2 = ON, 3 = EMERG

	# NCTR switch ... ON
	pushSeqCmd(dt, 'AN_APG70.nctr_sw', 1)

	# NAV FLIR switch ... ON (turns on NAV FLIR for use in both MFD and HUD) (left console middle, behind throttle)
	pushSeqCmd(dt, 'NAVPOD.nav_flir_sw', 2) # 0 = OFF, 1 = STBY, 2 = ON
	# NAV FLIR GAIN/BRIGHTNESS knob ... As desired (left console middle)
	# TODO, not sure if needed

	# JTIDS knob ... NORM (left console middle, behind throttle)
	pushSeqCmd(dt, 'RDRCTRL_AA.jtids_knob', 2) # 0 = OFF, 1 = POLL, 2 = NORM, 3 = SIL, 4 = HOLD

	# Fuel totalizer ... EXT WNG
	pushSeqCmd(dt, 'FLINST.fuelqty_totalizer', 3) # 0 = FEED, 1 = INTL WNG, 2 = TANK 1, 3 = EXT WNG, 4 = EXT CTR, 5 = CONF TANK??

	# BINGO fuel ... As desired (4000 lbs is a good default??) (right lower instrument panel, knob on fuel gauge)
	for i in range(40):
		pushSeqCmd(dt, 'FLINST.cmd_3385', 0.04884)

	# Add UFC DATA to HUD
	# Return to MENU 1 screen from anywhere with DATA, MENU.  Go to DATA 1 screen from anywhere with MENU, DATA.
	pushSeqCmd(dt, 'UFCCTRL_FRONT.UFC_MENU', 1)
	pushSeqCmd(dt, 'UFCCTRL_FRONT.UFC_MENU', 0)
	pushSeqCmd(dt, 'UFCCTRL_FRONT.UFC_DATA', 1)
	pushSeqCmd(dt, 'UFCCTRL_FRONT.UFC_DATA', 0)
	pushSeqCmd(dt, 'UFCCTRL_FRONT.UFC_PB_9', 1) # Radar alt in HUD
	pushSeqCmd(dt, 'UFCCTRL_FRONT.UFC_PB_9', 0)
	pushSeqCmd(dt, 'UFCCTRL_FRONT.UFC_PB_3', 1) # TAS in HUD
	pushSeqCmd(dt, 'UFCCTRL_FRONT.UFC_PB_3', 0)
	# Return to MENU 1.
	pushSeqCmd(dt, 'UFCCTRL_FRONT.UFC_MENU', 1)
	pushSeqCmd(dt, 'UFCCTRL_FRONT.UFC_MENU', 0)
	# Disable LAW
	pushSeqCmd(dt, 'UFCCTRL_FRONT.UFC_PB_1', 1) # LAW
	pushSeqCmd(dt, 'UFCCTRL_FRONT.UFC_PB_1', 0)

	# Set Radio 2 MAN-AM mode ON
	pushSeqCmd(dt, 'UFCCTRL_FRONT.UFC_PB_6', 1) # Radio 2
	pushSeqCmd(dt, 'UFCCTRL_FRONT.UFC_PB_6', 0)
	pushSeqCmd(dt, 'UFCCTRL_FRONT.UFC_PB_9', 1) # MAN-AM
	pushSeqCmd(dt, 'UFCCTRL_FRONT.UFC_PB_9', 0)
	# Return to MENU 1.
	pushSeqCmd(dt, 'UFCCTRL_FRONT.UFC_MENU', 1)
	pushSeqCmd(dt, 'UFCCTRL_FRONT.UFC_MENU', 0)

	# Set up IFF
	pushSeqCmd(dt, 'UFCCTRL_FRONT.UFC_PB_3', 1) # IFF
	pushSeqCmd(dt, 'UFCCTRL_FRONT.UFC_PB_3', 0)
	pushSeqCmd(dt, 'UFCCTRL_FRONT.UFC_PB_9', 1) # MC (Mode C/Charlie, adds pressure altitude to your Mode 3 transmissions)
	pushSeqCmd(dt, 'UFCCTRL_FRONT.UFC_PB_9', 0)
	pushSeqCmd(dt, 'UFCCTRL_FRONT.UFC_PB_7', 1) # AAI SLV
	pushSeqCmd(dt, 'UFCCTRL_FRONT.UFC_PB_7', 0)
	# Return to MENU 1.
	pushSeqCmd(dt, 'UFCCTRL_FRONT.UFC_MENU', 1)
	pushSeqCmd(dt, 'UFCCTRL_FRONT.UFC_MENU', 0)

	# Set up AAI/EID interrogation
	pushSeqCmd(dt, 'UFCCTRL_FRONT.UFC_PB_8', 1) # AAI/EID page
	pushSeqCmd(dt, 'UFCCTRL_FRONT.UFC_PB_8', 0)
	pushSeqCmd(dt, 'UFCCTRL_FRONT.UFC_PB_7', 1) # AUTO ID (first press sets to STT)
	pushSeqCmd(dt, 'UFCCTRL_FRONT.UFC_PB_7', 0)
	pushSeqCmd(dt, 'UFCCTRL_FRONT.UFC_PB_7', 1) # AUTO ID (second press sets to PDT (which includes STT))
	pushSeqCmd(dt, 'UFCCTRL_FRONT.UFC_PB_7', 0)
	# Return to MENU 1.
	pushSeqCmd(dt, 'UFCCTRL_FRONT.UFC_MENU', 1)
	pushSeqCmd(dt, 'UFCCTRL_FRONT.UFC_MENU', 0)

	# PROGRAM MFDS
	def pressMfdButtons(frontRear, mfd, buttons):
		frontPrefixes = {
			'left': 'MPD_FLEFT',
			'right': 'MPD_FRIGHT',
			'center': 'MPCD_FCENTER',
		}
		rearPrefixes = {
			'leftColor': 'MPCD_RLEFT',
			'left': 'MPD_RLEFT',
			'right': 'MPD_RRIGHT',
			'rightColor': 'MPCD_RRIGHT',
		}

		for button in buttons:
			if frontRear == 'front':
				device = frontPrefixes[mfd]
			elif frontRear == 'rear':
				device = rearPrefixes[mfd]

			# If it's the POWER button, 0 is on and 1 is back to middle position.
			if button == 'PW':
				# 0 = ON, 1 = middle, 2 = OFF
				pushSeqCmd(dt, device + '.Switch_Power', 0) # ON
				pushSeqCmd(dt, device + '.Switch_Power', 1) # middle
			# Else it's a regular button where 1 is press and 0 is release.
			else:
				btnNum = int(button[1:])
				btnName = device + f'.Button_{btnNum:02d}'
				pushSeqCmd(dt, btnName, 1) # Press
				pushSeqCmd(dt, btnName, 0) # Release

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
	pushSeqCmd(dt, 'PACS.Master_Arm_SW', 1)

	# SET UP BACK SEAT
	# Radio volumes
	pushSeqCmd(dt, 'UFCCTRL_REAR.UFC_VOL_R1', 1.0)
	pushSeqCmd(dt, 'UFCCTRL_REAR.UFC_VOL_R2', 1.0)
	pushSeqCmd(dt, 'UFCCTRL_REAR.UFC_VOL_R3', 1.0)
	pushSeqCmd(dt, 'UFCCTRL_REAR.UFC_VOL_R4', 1.0)
	# TGT FLIR switch ... ON (left console middle, behind left hand controller)
	pushSeqCmd(dt, 'TGPCTRL.tpod_pwr_sw', 2) # 0 = OFF, 1 = STBY, 2 = ON
	# LASER switch ... ARM (left console middle, behind left hand controller)
	pushSeqCmd(dt, 'TGPCTRL.tpod_laser_sw', 1) # 0 = SAFE, 1 = ARM
	# RWR/ICS mode switch ... COMBAT
	pushSeqCmd(dt, 'TEWS.rwr_ics_mode_sw', 1) # 0 = TRNG, 1 = COMBAT
	# ICS operational mode switch ... AUTO
	pushSeqCmd(dt, 'EWS_JMR.ics_mode_sw', 1) # 0 = STBY, 1 = AUTO, 2 = MAN
	# MIC switch ... ON
	pushSeqCmd(dt, 'ICS.cmd_3427', 1)

	# ICS power switch ... ON
	pushSeqCmd(dt, 'EWS_JMR.ics_power_sw', 1)

	# Left MFCD
	pressMfdButtons('rear', 'leftColor', [
		# Return to MENU 1 page from anywhere with Power switch ON.
		'PW', # POWER ON
		'B17', # HUD
		'B16' if vars.get('time') == 'day' else 'B20', # CAM else N-F
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
def AirStart(config, vars, helper, *args, **kwargs):
	seq = []
	dt = 0.3

	pushSeqCmd = helper.makePushSeqCmd(seq)

	pushSeqCmd(0, '', '', "Running Air Start sequence")

	# Set lights
	if vars.get('time') == 'day':
		# Internal lights:
		# Front console lights
		pushSeqCmd(dt, 'INTLT.console_lt_knob', 1.0)
		# Rear console lights
		pushSeqCmd(dt, 'INTLT.rc_console_lt_knob', 1.0)
		# Front instrument panel lights
		pushSeqCmd(dt, 'INTLT.inst_pnl_lt_knob', 1.0)
		# Rear instrument panel lights
		pushSeqCmd(dt, 'INTLT.rc_inst_pnl_lt_knob', 1.0)
		# Front day/night mode
		pushSeqCmd(dt, 'INTLT.daynite_mode_sw', 1) # 0 = NIGHT, 1 = DAY
		# Rear day/night mode
		pushSeqCmd(dt, 'INTLT.rc_daynite_mode_sw', 1) # 0 = NIGHT, 1 = DAY
		# HUD ... ON and brightness as desired (knob on UFC)
		pushSeqCmd(dt, 'HUDCTRL.HUD_BRT_Knob', 1.0)
		# HUD day/night mode
		pushSeqCmd(dt, 'HUDCTRL.HUD_MODE_Switch', 0) # 0 = DAY, 1 = AUTO, 2 = NIGHT??
		# Front UFC brightness ... As desired (knob on UFC)
		pushSeqCmd(dt, 'UFCCTRL_FRONT.UFC_BRT_CTRL', 1.0)
		# Front Gauges/UFC backlights
		pushSeqCmd(dt, 'INTLT.ufc_bcklt_br_knob', 1.0)
		# Rear UFC brightness ... As desired (knob on UFC)
		pushSeqCmd(dt, 'UFCCTRL_REAR.UFC_BRT_CTRL', 1.0)
		# Rear Gauges/UFC backlights
		pushSeqCmd(dt, 'INTLT.rc_ufc_bcklt_br_knob', 1.0)

		# External lights:
		# Anti-collision light
		pushSeqCmd(dt, 'EXTLT.anticoll_lt_sw', 0)
		# Formation lights
		pushSeqCmd(dt, 'EXTLT.formation_lt_knob', 0)
		# Position lights
		pushSeqCmd(dt, 'EXTLT.pos_lt_knob', 0)
		# Tail flood lights
		pushSeqCmd(dt, 'EXTLT.vert_tail_lt_sw', 0)
	else:
		# Internal lights:
		# Front console lights
		pushSeqCmd(dt, 'INTLT.console_lt_knob', 0.5)
		# Rear console lights
		pushSeqCmd(dt, 'INTLT.rc_console_lt_knob', 0.5)
		# Front instrument panel lights
		pushSeqCmd(dt, 'INTLT.inst_pnl_lt_knob', 0.5)
		# Rear instrument panel lights
		pushSeqCmd(dt, 'INTLT.rc_inst_pnl_lt_knob', 0.5)
		# Front day/night mode
		pushSeqCmd(dt, 'INTLT.daynite_mode_sw', 0) # 0 = NIGHT, 1 = DAY
		# Rear day/night mode
		pushSeqCmd(dt, 'INTLT.rc_daynite_mode_sw', 0) # 0 = NIGHT, 1 = DAY
		# HUD ... ON and brightness as desired (knob on UFC)
		pushSeqCmd(dt, 'HUDCTRL.HUD_BRT_Knob', 0.5)
		# HUD day/night mode
		pushSeqCmd(dt, 'HUDCTRL.HUD_MODE_Switch', 2) # 0 = DAY, 1 = AUTO, 2 = NIGHT??
		# Front UFC brightness ... As desired (knob on UFC)
		pushSeqCmd(dt, 'UFCCTRL_FRONT.UFC_BRT_CTRL', 0.5)
		# Front Gauges/UFC backlights
		pushSeqCmd(dt, 'INTLT.ufc_bcklt_br_knob', 0.5)
		# Rear UFC brightness ... As desired (knob on UFC)
		pushSeqCmd(dt, 'UFCCTRL_REAR.UFC_BRT_CTRL', 0.5)
		# Rear Gauges/UFC backlights
		pushSeqCmd(dt, 'INTLT.rc_ufc_bcklt_br_knob', 0.5)

		# External lights:
		# Anti-collision light
		pushSeqCmd(dt, 'EXTLT.anticoll_lt_sw', 0)
		# Formation lights
		pushSeqCmd(dt, 'EXTLT.formation_lt_knob', 0)
		# Position lights
		pushSeqCmd(dt, 'EXTLT.pos_lt_knob', 0)
		# Tail flood lights
		pushSeqCmd(dt, 'EXTLT.vert_tail_lt_sw', 0)

	# Air conditioner ... MIN
	pushSeqCmd(dt, 'ECS.airco_max_norm_min_sw', 0) # 0 = MIN, 1 = NORM, 2 = MAX

	# Radio volumes
	pushSeqCmd(dt, 'UFCCTRL_FRONT.UFC_VOL_R1', 1.0)
	pushSeqCmd(dt, 'UFCCTRL_FRONT.UFC_VOL_R2', 1.0)
	pushSeqCmd(dt, 'UFCCTRL_FRONT.UFC_VOL_R3', 1.0)
	pushSeqCmd(dt, 'UFCCTRL_FRONT.UFC_VOL_R4', 1.0)

	# IFF mode ... 4A
	pushSeqCmd(dt, 'IFF_TRN.mode_sw', 1)

	# IFF reply switch ... LIGHT
	pushSeqCmd(dt, 'IFF_TRN.rec_sw', 2)

	# Auto Fly Up switch
	pushSeqCmd(dt, 'TFR.flyup_cover', 1) # Cover open
	pushSeqCmd(dt, 'TFR.flyup_sw', 1) # 0 = ARMED (down), 1 = DISARMED (up)
	pushSeqCmd(dt, 'TFR.flyup_cover', 0) # Cover close

	# NCTR switch ... ON
	pushSeqCmd(dt, 'AN_APG70.nctr_sw', 1)

	# JTIDS knob ... NORM (left console middle, behind throttle)
	pushSeqCmd(dt, 'RDRCTRL_AA.jtids_knob', 2) # 0 = OFF, 1 = POLL, 2 = NORM, 3 = SIL, 4 = HOLD

	# Fuel totalizer ... EXT WNG
	pushSeqCmd(dt, 'FLINST.fuelqty_totalizer', 3) # 0 = FEED, 1 = INTL WNG, 2 = TANK 1, 3 = EXT WNG, 4 = EXT CTR, 5 = CONF TANK, not sure if BIT is selectable??

	# BINGO fuel ... As desired (4000 lbs is a good default??) (right lower instrument panel, knob on fuel gauge)
	for i in range(40):
		pushSeqCmd(dt, 'FLINST.cmd_3385', 0.04884)

	# Add UFC DATA to HUD
	# Return to MENU 1 screen from anywhere with DATA, MENU.  Go to DATA 1 screen from anywhere with MENU, DATA.
	pushSeqCmd(dt, 'UFCCTRL_FRONT.UFC_MENU', 1)
	pushSeqCmd(dt, 'UFCCTRL_FRONT.UFC_MENU', 0)
	pushSeqCmd(dt, 'UFCCTRL_FRONT.UFC_DATA', 1)
	pushSeqCmd(dt, 'UFCCTRL_FRONT.UFC_DATA', 0)
	pushSeqCmd(dt, 'UFCCTRL_FRONT.UFC_PB_9', 1) # Radar alt in HUD
	pushSeqCmd(dt, 'UFCCTRL_FRONT.UFC_PB_9', 0)
	pushSeqCmd(dt, 'UFCCTRL_FRONT.UFC_PB_3', 1) # TAS in HUD
	pushSeqCmd(dt, 'UFCCTRL_FRONT.UFC_PB_3', 0)
	# Return to MENU 1.
	pushSeqCmd(dt, 'UFCCTRL_FRONT.UFC_MENU', 1)
	pushSeqCmd(dt, 'UFCCTRL_FRONT.UFC_MENU', 0)
	# Disable LAW
	pushSeqCmd(dt, 'UFCCTRL_FRONT.UFC_PB_1', 1) # LAW
	pushSeqCmd(dt, 'UFCCTRL_FRONT.UFC_PB_1', 0)

	# Set Radio 2 MAN-AM mode ON
	pushSeqCmd(dt, 'UFCCTRL_FRONT.UFC_PB_6', 1) # Radio 2
	pushSeqCmd(dt, 'UFCCTRL_FRONT.UFC_PB_6', 0)
	pushSeqCmd(dt, 'UFCCTRL_FRONT.UFC_PB_9', 1) # MAN-AM
	pushSeqCmd(dt, 'UFCCTRL_FRONT.UFC_PB_9', 0)
	# Return to MENU 1.
	pushSeqCmd(dt, 'UFCCTRL_FRONT.UFC_MENU', 1)
	pushSeqCmd(dt, 'UFCCTRL_FRONT.UFC_MENU', 0)

	# Set up IFF
	pushSeqCmd(dt, 'UFCCTRL_FRONT.UFC_PB_3', 1) # IFF
	pushSeqCmd(dt, 'UFCCTRL_FRONT.UFC_PB_3', 0)
	pushSeqCmd(dt, 'UFCCTRL_FRONT.UFC_PB_9', 1) # MC (Mode C/Charlie, adds pressure altitude to your Mode 3 transmissions)
	pushSeqCmd(dt, 'UFCCTRL_FRONT.UFC_PB_9', 0)
	pushSeqCmd(dt, 'UFCCTRL_FRONT.UFC_PB_7', 1) # AAI SLV
	pushSeqCmd(dt, 'UFCCTRL_FRONT.UFC_PB_7', 0)
	# Return to MENU 1.
	pushSeqCmd(dt, 'UFCCTRL_FRONT.UFC_MENU', 1)
	pushSeqCmd(dt, 'UFCCTRL_FRONT.UFC_MENU', 0)

	# Set up AAI/EID interrogation
	pushSeqCmd(dt, 'UFCCTRL_FRONT.UFC_PB_8', 1) # AAI/EID page
	pushSeqCmd(dt, 'UFCCTRL_FRONT.UFC_PB_8', 0)
	pushSeqCmd(dt, 'UFCCTRL_FRONT.UFC_PB_7', 1) # AUTO ID (first press sets to STT)
	pushSeqCmd(dt, 'UFCCTRL_FRONT.UFC_PB_7', 0)
	pushSeqCmd(dt, 'UFCCTRL_FRONT.UFC_PB_7', 1) # AUTO ID (second press sets to PDT (which includes STT))
	pushSeqCmd(dt, 'UFCCTRL_FRONT.UFC_PB_7', 0)
	# Return to MENU 1.
	pushSeqCmd(dt, 'UFCCTRL_FRONT.UFC_MENU', 1)
	pushSeqCmd(dt, 'UFCCTRL_FRONT.UFC_MENU', 0)

	# PROGRAM MFDS
	def pressMfdButtons(frontRear, mfd, buttons):
		frontPrefixes = {
			'left': 'MPD_FLEFT',
			'right': 'MPD_FRIGHT',
			'center': 'MPCD_FCENTER',
		}
		rearPrefixes = {
			'leftColor': 'MPCD_RLEFT',
			'left': 'MPD_RLEFT',
			'right': 'MPD_RRIGHT',
			'rightColor': 'MPCD_RRIGHT',
		}

		for button in buttons:
			if frontRear == 'front':
				device = frontPrefixes[mfd]
			elif frontRear == 'rear':
				device = rearPrefixes[mfd]

			# If it's the POWER button, 0 is on and 1 is back to middle position.
			if button == 'PW':
				# 0 = ON, 1 = middle, 2 = OFF
				pushSeqCmd(dt, device + '.Switch_Power', 0) # ON
				pushSeqCmd(dt, device + '.Switch_Power', 1) # middle
			# Else it's a regular button where 1 is press and 0 is release.
			else:
				btnNum = int(button[1:])
				btnName = device + f'.Button_{btnNum:02d}'
				pushSeqCmd(dt, btnName, 1) # Press
				pushSeqCmd(dt, btnName, 0) # Release

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
	pushSeqCmd(dt, 'PACS.Master_Arm_SW', 1)

	# SET UP BACK SEAT
	# Radio volumes
	pushSeqCmd(dt, 'UFCCTRL_REAR.UFC_VOL_R1', 1.0)
	pushSeqCmd(dt, 'UFCCTRL_REAR.UFC_VOL_R2', 1.0)
	pushSeqCmd(dt, 'UFCCTRL_REAR.UFC_VOL_R3', 1.0)
	pushSeqCmd(dt, 'UFCCTRL_REAR.UFC_VOL_R4', 1.0)

	# RWR/ICS mode switch ... COMBAT
	pushSeqCmd(dt, 'TEWS.rwr_ics_mode_sw', 1) # 0 = TRNG, 1 = COMBAT
	# ICS operational mode switch ... AUTO
	pushSeqCmd(dt, 'EWS_JMR.ics_mode_sw', 1) # 0 = STBY, 1 = AUTO, 2 = MAN
	# MIC switch ... ON
	pushSeqCmd(dt, 'ICS.cmd_3427', 1)

	# Left MFCD
	pressMfdButtons('rear', 'leftColor', [
		# Return to MENU 1 page from anywhere with Power switch ON.
		'PW', # POWER ON
		'B17', # HUD
		'B16' if vars.get('time') == 'day' else 'B20', # CAM else N-F
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
def Shutdown(config, vars, helper, *args, **kwargs):
	seq = []
	dt = 0.3

	pushSeqCmd = helper.makePushSeqCmd(seq)

	pushSeqCmd(0, '', '', "Running Shutdown sequence")

	# Canopy ... Open (lever on right canopy rail)
	pushSeqCmd(dt, 'CNPYSYST.cnpy_lever', 0)
	pushSeqCmd(6, 'CNPYSYST.cnpy_lever', 1)

	# Set lights
	# Front console lights
	pushSeqCmd(dt, 'INTLT.console_lt_knob', 0)
	# Rear console lights
	pushSeqCmd(dt, 'INTLT.rc_console_lt_knob', 0)
	# Front instrument panel lights
	pushSeqCmd(dt, 'INTLT.inst_pnl_lt_knob', 0)
	# Rear instrument panel lights
	pushSeqCmd(dt, 'INTLT.rc_inst_pnl_lt_knob', 0)
	# Front day/night mode
	pushSeqCmd(dt, 'INTLT.daynite_mode_sw', 1) # 0 = NIGHT, 1 = DAY
	# Rear day/night mode
	pushSeqCmd(dt, 'INTLT.rc_daynite_mode_sw', 1) # 0 = NIGHT, 1 = DAY
	# HUD ... ON and brightness as desired (knob on UFC)
	pushSeqCmd(dt, 'HUDCTRL.HUD_BRT_Knob', 0)
	# HUD day/night mode
	pushSeqCmd(dt, 'HUDCTRL.HUD_MODE_Switch', 1) # 0 = DAY, 1 = AUTO, 2 = NIGHT??
	# Front UFC brightness ... As desired (knob on UFC)
	pushSeqCmd(dt, 'UFCCTRL_FRONT.UFC_BRT_CTRL', 0)
	# Rear UFC brightness ... As desired (knob on UFC)
	pushSeqCmd(dt, 'UFCCTRL_REAR.UFC_BRT_CTRL', 0)

	# MIC switch ... OFF
	pushSeqCmd(dt, 'ICS.cmd_3509', 0)

	# OXYGEN supply switch ... OFF (right console forward)
	pushSeqCmd(dt, 'ECS.oxy_pbg_on_off_sw', 0)

	# MFDs ... OFF (click the rocker switch on each MFD)
	# 0 = ON, 1 = middle, 2 = OFF
	pushSeqCmd(dt, 'MPD_FLEFT.Switch_Power', 2)
	pushSeqCmd(dt, 'MPD_FLEFT.Switch_Power', 1)
	pushSeqCmd(dt, 'MPD_FRIGHT.Switch_Power', 2)
	pushSeqCmd(dt, 'MPD_FRIGHT.Switch_Power', 1)
	pushSeqCmd(dt, 'MPCD_FCENTER.Switch_Power', 2)
	pushSeqCmd(dt, 'MPCD_FCENTER.Switch_Power', 1)

	# INS ... OFF
	pushSeqCmd(dt, 'INS.ins_knob', 0) # 0 = OFF, 1 = STORE, 2 = GC, 3 = NAV

	# IFF mode ... OFF
	pushSeqCmd(dt, 'IFF_TRN.mode_sw', 0)

	# IFF reply switch ... OFF
	pushSeqCmd(dt, 'IFF_TRN.rec_sw', 0)

	# TF RDR switch ... OFF (left console middle, behind throttle)
	pushSeqCmd(dt, 'TFR.tf_rdr_sw', 0) # 0 = OFF, 1 = STBY, 2 = ON

	# RDR ALT switch ... OFF (left console middle, behind throttle)
	pushSeqCmd(dt, 'CARA.rdr_alt_sw', 0) # 0 = OFF, 1 = ON, 2 = OVERIDE

	# RADAR switch ... OFF (left console middle, behind throttle)
	pushSeqCmd(dt, 'AN_APG70.rdr_power_sw', 0) # 0 = OFF, 1 = STBY, 2 = ON, 3 = EMERG

	# NCTR switch ... OFF
	pushSeqCmd(dt, 'AN_APG70.nctr_sw', 0)

	# NAV FLIR switch ... OFF (left console middle, behind throttle)
	pushSeqCmd(dt, 'NAVPOD.nav_flir_sw', 0) # 0 = OFF, 1 = STBY, 2 = ON
	# NAV FLIR GAIN/BRIGHTNESS knob ... As desired (left console middle)
	# TODO, not sure if needed

	# JTIDS knob ... OFF (left console middle, behind throttle)
	pushSeqCmd(dt, 'RDRCTRL_AA.jtids_knob', 0) # 0 = OFF, 1 = POLL, 2 = NORM, 3 = SIL, 4 = HOLD

	# CAS YAW, ROLL, and PITCH switches ... OFF (left console forward inboard)
	pushSeqCmd(dt, 'FLCTRL.cmd_3452', 0)
	pushSeqCmd(dt, 'FLCTRL.cmd_3453', 0)
	pushSeqCmd(dt, 'FLCTRL.pitch_sw', 0)

	# SAI (Standby Attitude Indicator) ... Cage (left lower instrument panel)
	pushSeqCmd(dt, 'FLINST.art_hor_uncage', 1)
	pushSeqCmd(dt, 'FLINST.art_hor_adj', 1.0)
	pushSeqCmd(dt, 'FLINST.art_hor_uncage', 0)

	# BINGO fuel ... zero (right lower instrument panel, knob on fuel gauge)
	for i in range(40):
		pushSeqCmd(dt, 'FLINST.cmd_3385', -0.1)

	# Ejection seat ... SAFE (lever on left forward base of seat)
	pushSeqCmd(dt, 'CNPYSYST.seat_arm_handle', 0)

	# SET UP BACK SEAT
	# All MFDs ... OFF
	# 0 = ON, 1 = middle, 2 = OFF
	pushSeqCmd(dt, 'MPCD_RLEFT.Switch_Power', 2)
	pushSeqCmd(dt, 'MPCD_RLEFT.Switch_Power', 1)
	pushSeqCmd(dt, 'MPD_RLEFT.Switch_Power', 2)
	pushSeqCmd(dt, 'MPD_RLEFT.Switch_Power', 1)
	pushSeqCmd(dt, 'MPD_RRIGHT.Switch_Power', 2)
	pushSeqCmd(dt, 'MPD_RRIGHT.Switch_Power', 1)
	pushSeqCmd(dt, 'MPCD_RRIGHT.Switch_Power', 2)
	pushSeqCmd(dt, 'MPCD_RRIGHT.Switch_Power', 1)
	# SAI (Standby Attitude Indicator) ... Cage (instrument panel center)
	pushSeqCmd(dt, 'FLINST.cmd_3401', 1)
	pushSeqCmd(dt, 'FLINST.rc_art_hor_adj', 1.0)
	pushSeqCmd(dt, 'FLINST.cmd_3401', 0)

	# TGT FLIR switch ... OFF (left console middle, behind left hand controller)
	pushSeqCmd(dt, 'TGPCTRL.tpod_pwr_sw', 0) # 0 = OFF, 1 = STBY, 2 = ON
	# LASER switch ... SAFE (left console middle, behind left hand controller)
	pushSeqCmd(dt, 'TGPCTRL.tpod_laser_sw', 0) # 0 = SAFE, 1 = ARM
	# RWR/ICS mode switch ... TRNG
	pushSeqCmd(dt, 'TEWS.rwr_ics_mode_sw', 0) # 0 = TRNG, 1 = COMBAT
	# ICS operational mode switch ... STBY
	pushSeqCmd(dt, 'EWS_JMR.ics_mode_sw', 0) # 0 = STBY, 1 = AUTO, 2 = MAN
	# MIC switch ... OFF
	pushSeqCmd(dt, 'ICS.cmd_3427', 0)

	# OXYGEN supply switch ... OFF (right console forward, in front of right hand controller)
	pushSeqCmd(dt, 'ECS.cmd_3573', 0)
	# ICS power switch ... OFF
	pushSeqCmd(dt, 'EWS_JMR.ics_power_sw', 0)
	# RWR switch ... OFF (right console middle, behind right hand controller)
	pushSeqCmd(dt, 'TEWS.rwr_power_sw', 0)
	# EWWS switch ... OFF (right console middle, behind right hand controller)
	pushSeqCmd(dt, 'TEWS.ewss_power_sw', 0)
	# CMD MODE knob ... OFF (right console middle)
	pushSeqCmd(dt, 'EWS_CMD.cmd_mode_knob', 0) # 0 = OFF, 1 = STBY, 2 = MAN ONLY, 3 = SEMIAUTO, 4 = AUTO

	# Ejection seat ... SAFE (lever on left forward base of seat)
	pushSeqCmd(dt, 'CNPYSYST.seat_arm_handle_rc', 0)
	# END SET UP BACK SEAT

	# Cut right engine
	# Right throttle to OFF
	pushSeqCmd(dt, 'scriptSimCommand', 'iCommandRightEngineStop') # Right throttle OFF

	# Cut left engine
	# Left throttle to OFF
	pushSeqCmd(dt, 'scriptSimCommand', 'iCommandLeftEngineStop') # Left throttle OFF

	# L and R GEN switches ... OFF
	pushSeqCmd(dt, 'EPSS.generator_left_sw', 0)
	pushSeqCmd(dt, 'EPSS.generator_right_sw', 0)
	# L and R ENG CONTR switches ... OFF (right console forward middle)
	pushSeqCmd(dt, 'DEEC.left_eng_ctrl_sw', 0)
	pushSeqCmd(dt, 'DEEC.right_eng_ctrl_sw', 0)
	#L and R ENG MASTER switches ... OFF (right console forward, black guarded switches)
	pushSeqCmd(dt, 'DEEC.left_eng_master_cover', 1)
	pushSeqCmd(dt, 'DEEC.left_eng_master_sw', 0)
	pushSeqCmd(dt, 'DEEC.left_eng_master_cover', 0)
	pushSeqCmd(dt, 'DEEC.right_eng_master_cover', 1)
	pushSeqCmd(dt, 'DEEC.right_eng_master_sw', 0)
	pushSeqCmd(dt, 'DEEC.right_eng_master_cover', 0)
	# STARTER switch ... OFF (right console forward)
	pushSeqCmd(dt, 'EPSS.starter_gen_sw', 0)
	# AIR COND switch ... OFF (right console forward outboard)
	pushSeqCmd(dt, 'ECS.airco_auto_man_off_sw', 0)
	# L and R INLET switches ... EMERG (left console forward outboard)
	pushSeqCmd(dt, 'DEEC.left_inlet_sw', 1) # 0 = AUTO, 1 = EMERG
	pushSeqCmd(dt, 'DEEC.right_inlet_sw', 1) # 0 = AUTO, 1 = EMERG

	return seq


###############################################################################
###############################################################################
def LoadRoute(config, vars, helper, *args, **kwargs):
	seq = []
	dt = 0.3

	pushSeqCmd = helper.makePushSeqCmd(seq)

	def pressUfcButton(btn):
		btn = str(btn).upper()
		aliases = {
			'1': 'KEY_A1',
			'2': 'KEY_N2',
			'3': 'KEY_B3',
			'4': 'KEY_W4',
			'5': 'KEY_M5',
			'6': 'KEY_E6',
			'7': 'KEY_7',
			'8': 'KEY_S8',
			'9': 'KEY_C9',
			'0': 'KEY_0',
			'.': 'KEY_DOT',

			# Shifted keypad buttons
			'A': 'KEY_A1',
			'N': 'KEY_N2',
			'B': 'KEY_B3',
			'W': 'KEY_W4',
			'M': 'KEY_M5',
			'E': 'KEY_E6',
			':': 'KEY_7',
			'S': 'KEY_S8',
			'C': 'KEY_C9',
			'-': 'KEY_0',

			# Other buttons
			'DATA' : 'KEY_DATA',
			'MENU' : 'KEY_MENU',
			'SHF' : 'KEY_SHF',
			'CLR' : 'KEY_CLR',

			# OSBs
			'L1': 'B1',
			'L2': 'B2',
			'L3': 'B3',
			'L4': 'B4',
			'L5': 'B5',
			'R1': 'B10',
			'R2': 'B9',
			'R3': 'B8',
			'R4': 'B7',
			'R5': 'B6',
		}

		ufcKeyMap = {
			'KEY_A1': 'UFCCTRL_FRONT.UFC_KEY_A1',
			'KEY_N2': 'UFCCTRL_FRONT.UFC_KEY_N2',
			'KEY_B3': 'UFCCTRL_FRONT.UFC_KEY_B3',
			'KEY_W4': 'UFCCTRL_FRONT.UFC_KEY_W4',
			'KEY_M5': 'UFCCTRL_FRONT.UFC_KEY_M5',
			'KEY_E6': 'UFCCTRL_FRONT.UFC_KEY_E6',
			'KEY_7': 'UFCCTRL_FRONT.UFC_KEY__7',
			'KEY_S8': 'UFCCTRL_FRONT.UFC_KEY_S8',
			'KEY_C9': 'UFCCTRL_FRONT.UFC_KEY_C9',
			'KEY_0': 'UFCCTRL_FRONT.UFC_KEY__0',
			'KEY_DOT': 'UFCCTRL_FRONT.UFC_DOT',
			'KEY_DATA': 'UFCCTRL_FRONT.UFC_DATA',
			'KEY_MENU': 'UFCCTRL_FRONT.UFC_MENU',
			'KEY_SHF': 'UFCCTRL_FRONT.UFC_SHF',
			'KEY_CLR': 'UFCCTRL_FRONT.UFC_CLEAR',
			'KEY_AP': 'UFCCTRL_FRONT.UFC_A_P',
			'KEY_MARK': 'UFCCTRL_FRONT.UFC_MARK',
			'KEY_IP': 'UFCCTRL_FRONT.UFC_I_P',
			'B1': 'UFCCTRL_FRONT.UFC_PB_1',
			'B2': 'UFCCTRL_FRONT.UFC_PB_2',
			'B3': 'UFCCTRL_FRONT.UFC_PB_3',
			'B4': 'UFCCTRL_FRONT.UFC_PB_4',
			'B5': 'UFCCTRL_FRONT.UFC_PB_5',
			'B6': 'UFCCTRL_FRONT.UFC_PB_6',
			'B7': 'UFCCTRL_FRONT.UFC_PB_7',
			'B8': 'UFCCTRL_FRONT.UFC_PB_8',
			'B9': 'UFCCTRL_FRONT.UFC_PB_9',
			'B10': 'UFCCTRL_FRONT.UFC_PB_0',
		}

		if btn in aliases:
			cmd = aliases[btn]
		else:
			cmd = btn

		canonicalName = ufcKeyMap.get(cmd, 'UFCCTRL_FRONT.' + cmd)
		pushSeqCmd(dt, canonicalName, 1) # Press
		pushSeqCmd(dt, canonicalName, 0) # Release

	def enterUfcSequence(input):
		input = str(input).upper()
		for char in input:
			pressUfcButton(char)

	# Start sequence
	pushSeqCmd(0, '', '', 'Loading waypoints from file')
	routeData = helper.getRouteData(vars.get('routeFile'), vars.get('routeName'))
	if not routeData:
		pushSeqCmd(dt, '', '', 'Route selection cancelled.')
		return seq

	waypoints = routeData['waypoints']
	if not waypoints:
		pushSeqCmd(dt, '', '', 'No waypoints in route.')
		return seq

	# Get the starting waypoint number from the user.
	startingWaypointNumber = vars.get('startingWaypoint')
	if startingWaypointNumber is None or int(startingWaypointNumber) < 1:
		pushSeqCmd(dt, '', '', 'Waypoint entry cancelled.')
		return seq

	pushSeqCmd(dt, 'scriptSpeech', 'Do not use any functions on UFC until waypoint entry is complete.')

	# Start entering waypoints.

	# Clear the scratchpad.
	pressUfcButton('CLR')
	pressUfcButton('CLR')
	# Idempotent path to UFC MENU 1 screen.
	pressUfcButton('DATA')
	pressUfcButton('MENU')
	# Set current waypoint to B to ensure we can enter waypoints starting from any number.
	pressUfcButton('SHF')
	pressUfcButton('B')
	pressUfcButton('R1')
	# Go to waypoint entry screen.
	pressUfcButton('R1')

	currentWaypointNumber = int(startingWaypointNumber)
	waypointCount = len(waypoints)
	for waypointIndex, waypoint in enumerate(waypoints):
		pushSeqCmd(dt, '', '', f'Entering waypoint {waypointIndex + 1}/{waypointCount} as waypoint {currentWaypointNumber}A.')
		# Set waypoint number to currentWaypointNumber.
		enterUfcSequence(currentWaypointNumber)
		pressUfcButton('SHF')
		pressUfcButton('A') # Only using the 'A' route here.
		pressUfcButton('L1')
		# If waypoints should be set as targets, set it as target.
		if vars.get('setAsTargetPoints') == 'yes':
			enterUfcSequence(currentWaypointNumber)
			pressUfcButton('.')
			pressUfcButton('SHF')
			pressUfcButton('A')
			pressUfcButton('L1') # Rename with '.' at the end to set as target.

		latLonDDM = waypoint['latLonDDM']

		# Enter latitude in DDM format.
		# If lat is positive, N; if negative, S.
		if latLonDDM['lat']['deg'] >= 0:
			pressUfcButton('SHF')
			pressUfcButton('N')
		else:
			pressUfcButton('SHF')
			pressUfcButton('S')
		deg = latLonDDM['lat']['deg']
		min = latLonDDM['lat']['min']
		wholeMin, fracMin = str(min).split('.')
		enterUfcSequence(str(deg).zfill(2)) # Pad the degrees with leading zeros to 2 digits.
		enterUfcSequence(wholeMin.zfill(2) + fracMin[0:3].zfill(3)) # Whole mins padded to 2 digits + first 3 decimal places padded to 3 digits, no decimal point.
		pressUfcButton('L2')

		# Enter longitude in DDM format.
		# If lon is positive, E; if negative, W.
		if latLonDDM['lon']['deg'] >= 0:
			pressUfcButton('SHF')
			pressUfcButton('E')
		else:
			pressUfcButton('SHF')
			pressUfcButton('W')
		deg = latLonDDM['lon']['deg']
		min = latLonDDM['lon']['min']
		wholeMin, fracMin = str(min).split('.')
		enterUfcSequence(str(deg).zfill(3)) # Pad the degrees with leading zeros to 3 digits.
		enterUfcSequence(wholeMin.zfill(2) + fracMin[0:3].zfill(3)) # Whole mins padded to 2 digits + first 3 decimal places padded to 3 digits, no decimal point.
		pressUfcButton('L3')

		# Enter altitude in feet.
		if vars.get('altitude') == 'forceGround':
			altFeet = round(waypoint['groundAltFeet'])
		else:
			altFeet = round(waypoint.get('altFeet'))
		enterUfcSequence(altFeet)
		pressUfcButton('R4')

		# If we're not on the last waypoint, increment to the next waypoint.
		if waypointIndex != waypointCount - 1:
			currentWaypointNumber += 1

	# After entry is complete, return to MENU 1.
	pressUfcButton('MENU')

	return seq


###############################################################################
###############################################################################
def LoadScratchpad(config, vars, helper, *args, **kwargs):
	seq = []
	dt = 0.3

	pushSeqCmd = helper.makePushSeqCmd(seq)

	def pressUfcButton(btn):
		btn = str(btn).upper()
		aliases = {
			'1': 'KEY_A1',
			'2': 'KEY_N2',
			'3': 'KEY_B3',
			'4': 'KEY_W4',
			'5': 'KEY_M5',
			'6': 'KEY_E6',
			'7': 'KEY_7',
			'8': 'KEY_S8',
			'9': 'KEY_C9',
			'0': 'KEY_0',
			'.': 'KEY_DOT',

			# Shifted keypad buttons
			'A': 'KEY_A1',
			'N': 'KEY_N2',
			'B': 'KEY_B3',
			'W': 'KEY_W4',
			'M': 'KEY_M5',
			'E': 'KEY_E6',
			':': 'KEY_7',
			'S': 'KEY_S8',
			'C': 'KEY_C9',
			'-': 'KEY_0',

			# Other buttons
			'DATA' : 'KEY_DATA',
			'MENU' : 'KEY_MENU',
			'SHF' : 'KEY_SHF',
			'CLR' : 'KEY_CLR',

			# OSBs
			'L1': 'B1',
			'L2': 'B2',
			'L3': 'B3',
			'L4': 'B4',
			'L5': 'B5',
			'R1': 'B10',
			'R2': 'B9',
			'R3': 'B8',
			'R4': 'B7',
			'R5': 'B6',
		}

		ufcKeyMap = {
			'KEY_A1': 'UFCCTRL_FRONT.UFC_KEY_A1',
			'KEY_N2': 'UFCCTRL_FRONT.UFC_KEY_N2',
			'KEY_B3': 'UFCCTRL_FRONT.UFC_KEY_B3',
			'KEY_W4': 'UFCCTRL_FRONT.UFC_KEY_W4',
			'KEY_M5': 'UFCCTRL_FRONT.UFC_KEY_M5',
			'KEY_E6': 'UFCCTRL_FRONT.UFC_KEY_E6',
			'KEY_7': 'UFCCTRL_FRONT.UFC_KEY__7',
			'KEY_S8': 'UFCCTRL_FRONT.UFC_KEY_S8',
			'KEY_C9': 'UFCCTRL_FRONT.UFC_KEY_C9',
			'KEY_0': 'UFCCTRL_FRONT.UFC_KEY__0',
			'KEY_DOT': 'UFCCTRL_FRONT.UFC_DOT',
			'KEY_DATA': 'UFCCTRL_FRONT.UFC_DATA',
			'KEY_MENU': 'UFCCTRL_FRONT.UFC_MENU',
			'KEY_SHF': 'UFCCTRL_FRONT.UFC_SHF',
			'KEY_CLR': 'UFCCTRL_FRONT.UFC_CLEAR',
			'KEY_AP': 'UFCCTRL_FRONT.UFC_A_P',
			'KEY_MARK': 'UFCCTRL_FRONT.UFC_MARK',
			'KEY_IP': 'UFCCTRL_FRONT.UFC_I_P',
			'B1': 'UFCCTRL_FRONT.UFC_PB_1',
			'B2': 'UFCCTRL_FRONT.UFC_PB_2',
			'B3': 'UFCCTRL_FRONT.UFC_PB_3',
			'B4': 'UFCCTRL_FRONT.UFC_PB_4',
			'B5': 'UFCCTRL_FRONT.UFC_PB_5',
			'B6': 'UFCCTRL_FRONT.UFC_PB_6',
			'B7': 'UFCCTRL_FRONT.UFC_PB_7',
			'B8': 'UFCCTRL_FRONT.UFC_PB_8',
			'B9': 'UFCCTRL_FRONT.UFC_PB_9',
			'B10': 'UFCCTRL_FRONT.UFC_PB_0',
		}

		if btn in aliases:
			cmd = aliases[btn]
		else:
			cmd = btn

		canonicalName = ufcKeyMap.get(cmd, 'UFCCTRL_FRONT.' + cmd)
		pushSeqCmd(dt, canonicalName, 1) # Press
		pushSeqCmd(dt, canonicalName, 0) # Release

	def enterUfcSequence(input):
		input = str(input).upper()
		for char in input:
			pressUfcButton(char)

	# Start sequence
	pushSeqCmd(0, '', '', 'Loading waypoints from file')
	waypoints = helper.getScratchpadData(vars.get('scratchpadFile'))
	if not waypoints:
		pushSeqCmd(dt, 'scriptText', 'No waypoints found.')
		return seq

	# Get the starting waypoint number from the user.
	startingWaypointNumber = vars.get('startingWaypoint')
	if startingWaypointNumber is None or int(startingWaypointNumber) < 1:
		pushSeqCmd(dt, '', '', 'Waypoint entry cancelled.')
		return seq

	pushSeqCmd(dt, 'scriptSpeech', 'Do not use any functions on UFC until waypoint entry is complete.')

	# Start entering waypoints.

	# Clear the scratchpad.
	pressUfcButton('CLR')
	pressUfcButton('CLR')
	# Idempotent path to UFC MENU 1 screen.
	pressUfcButton('DATA')
	pressUfcButton('MENU')
	# Set current waypoint to B to ensure we can enter waypoints starting from any number.
	pressUfcButton('SHF')
	pressUfcButton('B')
	pressUfcButton('R1')
	# Go to waypoint entry screen.
	pressUfcButton('R1')

	currentWaypointNumber = int(startingWaypointNumber)
	waypointCount = len(waypoints)
	for waypointIndex, waypoint in enumerate(waypoints):
		pushSeqCmd(dt, '', '', f'Entering waypoint {waypointIndex + 1}/{waypointCount} as waypoint {currentWaypointNumber}A.')
		# Set waypoint number to currentWaypointNumber.
		enterUfcSequence(currentWaypointNumber)
		pressUfcButton('SHF')
		pressUfcButton('A') # Only using the 'A' route here.
		pressUfcButton('L1')
		# If waypoints should be set as targets, set it as target.
		if vars.get('setAsTargetPoints') == 'yes':
			enterUfcSequence(currentWaypointNumber)
			pressUfcButton('.')
			pressUfcButton('SHF')
			pressUfcButton('A')
			pressUfcButton('L1') # Rename with '.' at the end to set as target.

		latLonDDM = waypoint['latLonDDM']

		# Enter latitude in DDM format.
		# If lat is positive, N; if negative, S.
		if latLonDDM['lat']['deg'] >= 0:
			pressUfcButton('SHF')
			pressUfcButton('N')
		else:
			pressUfcButton('SHF')
			pressUfcButton('S')
		deg = latLonDDM['lat']['deg']
		min = latLonDDM['lat']['min']
		wholeMin, fracMin = str(min).split('.')
		enterUfcSequence(str(deg).zfill(2)) # Pad the degrees with leading zeros to 2 digits.
		enterUfcSequence(wholeMin.zfill(2) + fracMin[0:3].zfill(3)) # Whole mins padded to 2 digits + first 3 decimal places padded to 3 digits, no decimal point.
		pressUfcButton('L2')

		# Enter longitude in DDM format.
		# If lon is positive, E; if negative, W.
		if latLonDDM['lon']['deg'] >= 0:
			pressUfcButton('SHF')
			pressUfcButton('E')
		else:
			pressUfcButton('SHF')
			pressUfcButton('W')
		deg = latLonDDM['lon']['deg']
		min = latLonDDM['lon']['min']
		wholeMin, fracMin = str(min).split('.')
		enterUfcSequence(str(deg).zfill(3)) # Pad the degrees with leading zeros to 3 digits.
		enterUfcSequence(wholeMin.zfill(2) + fracMin[0:3].zfill(3)) # Whole mins padded to 2 digits + first 3 decimal places padded to 3 digits, no decimal point.
		pressUfcButton('L3')

		# Enter altitude in feet.
		if vars.get('altitude') == 'forceGround':
			altFeet = round(waypoint['groundAltFeet'])
		else:
			altFeet = round(waypoint.get('altFeet'))
		enterUfcSequence(altFeet)
		pressUfcButton('R4')

		# If we're not on the last waypoint, increment to the next waypoint.
		if waypointIndex != waypointCount - 1:
			currentWaypointNumber += 1

	# After entry is complete, return to MENU 1.
	pressUfcButton('MENU')

	return seq
