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
		],
	}

def getInfo():
	return """"""

# Returns 0-65535 scaled by multiple (0-1), eg for 50% call int16(0.5)
def int16(mult = 1):
	int16 = 65535
	return int(mult * int16)


# Starting state should be NAV Master Mode, not in the menu screen for the left MFD's B3 OSB.
def setupMFDs(dt, seq, pushSeqCmd):
	# Set up MFDs in all modes (NAV, A-A, A-G, DGFT, MSL).  Left MFD: FCR, HAD, WPN.  Right MFD: SMS, HSD, TGP
	# NAV mode (default)
	# Left MFD
	pushSeqCmd(dt, 'MFD_L_13', 1) # B3 OSB
	pushSeqCmd(dt, 'MFD_L_13', 0) # release
	pushSeqCmd(dt, 'MFD_L_13', 1) # B3 OSB
	pushSeqCmd(dt, 'MFD_L_13', 0) # release
	pushSeqCmd(dt, 'MFD_L_2', 1) # HAD
	pushSeqCmd(dt, 'MFD_L_2', 0) # release
	pushSeqCmd(dt, 'MFD_L_12', 1) # B4 OSB
	pushSeqCmd(dt, 'MFD_L_12', 0) # release
	pushSeqCmd(dt, 'MFD_L_12', 1) # B4 OSB
	pushSeqCmd(dt, 'MFD_L_12', 0) # release
	pushSeqCmd(dt, 'MFD_L_18', 1) # WPN
	pushSeqCmd(dt, 'MFD_L_18', 0) # release
	# Right MFD
	pushSeqCmd(dt, 'MFD_R_12', 1) # B4 OSB
	pushSeqCmd(dt, 'MFD_R_12', 0) # release
	pushSeqCmd(dt, 'MFD_R_12', 1) # B4 OSB
	pushSeqCmd(dt, 'MFD_R_12', 0) # release
	pushSeqCmd(dt, 'MFD_R_19', 1) # TGP
	pushSeqCmd(dt, 'MFD_R_19', 0) # release
	# Select FCR/HSD
	pushSeqCmd(dt, 'MFD_L_14', 1) # B3 OSB
	pushSeqCmd(dt, 'MFD_L_14', 0) # release
	pushSeqCmd(dt, 'MFD_R_13', 1) # B3 OSB
	pushSeqCmd(dt, 'MFD_R_13', 0) # release

	# A-A mode
	pushSeqCmd(dt, 'ICP_AA_MODE_BTN', 1) # Switch to A-A Master Mode
	pushSeqCmd(dt, 'ICP_AA_MODE_BTN', 0)
	pushSeqCmd(dt, 'MFD_L_13', 1) # B3 OSB
	pushSeqCmd(dt, 'MFD_L_13', 0) # release
	pushSeqCmd(dt, 'MFD_L_13', 1) # B3 OSB
	pushSeqCmd(dt, 'MFD_L_13', 0) # release
	pushSeqCmd(dt, 'MFD_L_2', 1) # HAD
	pushSeqCmd(dt, 'MFD_L_2', 0) # release
	pushSeqCmd(dt, 'MFD_L_12', 1) # B4 OSB
	pushSeqCmd(dt, 'MFD_L_12', 0) # release
	pushSeqCmd(dt, 'MFD_L_12', 1) # B4 OSB
	pushSeqCmd(dt, 'MFD_L_12', 0) # release
	pushSeqCmd(dt, 'MFD_L_18', 1) # WPN
	pushSeqCmd(dt, 'MFD_L_18', 0) # release
	# Right MFD
	pushSeqCmd(dt, 'MFD_R_12', 1) # B4 OSB
	pushSeqCmd(dt, 'MFD_R_12', 0) # release
	pushSeqCmd(dt, 'MFD_R_12', 1) # B4 OSB
	pushSeqCmd(dt, 'MFD_R_12', 0) # release
	pushSeqCmd(dt, 'MFD_R_19', 1) # TGP
	pushSeqCmd(dt, 'MFD_R_19', 0) # release
	# Select FCR/HSD
	pushSeqCmd(dt, 'MFD_L_14', 1) # B3 OSB
	pushSeqCmd(dt, 'MFD_L_14', 0) # release
	pushSeqCmd(dt, 'MFD_R_13', 1) # B3 OSB
	pushSeqCmd(dt, 'MFD_R_13', 0) # release

	# A-G mode
	pushSeqCmd(dt, 'ICP_AG_MODE_BTN', 1) # Switch to A-G Master Mode
	pushSeqCmd(dt, 'ICP_AG_MODE_BTN', 0)
	pushSeqCmd(dt, 'MFD_L_13', 1) # B3 OSB
	pushSeqCmd(dt, 'MFD_L_13', 0) # release
	pushSeqCmd(dt, 'MFD_L_13', 1) # B3 OSB
	pushSeqCmd(dt, 'MFD_L_13', 0) # release
	pushSeqCmd(dt, 'MFD_L_2', 1) # HAD
	pushSeqCmd(dt, 'MFD_L_2', 0) # release
	pushSeqCmd(dt, 'MFD_L_12', 1) # B4 OSB
	pushSeqCmd(dt, 'MFD_L_12', 0) # release
	pushSeqCmd(dt, 'MFD_L_12', 1) # B4 OSB
	pushSeqCmd(dt, 'MFD_L_12', 0) # release
	pushSeqCmd(dt, 'MFD_L_18', 1) # WPN
	pushSeqCmd(dt, 'MFD_L_18', 0) # release
	# Right MFD
	pushSeqCmd(dt, 'MFD_R_12', 1) # B4 OSB
	pushSeqCmd(dt, 'MFD_R_12', 0) # release
	pushSeqCmd(dt, 'MFD_R_12', 1) # B4 OSB
	pushSeqCmd(dt, 'MFD_R_12', 0) # release
	pushSeqCmd(dt, 'MFD_R_19', 1) # TGP
	pushSeqCmd(dt, 'MFD_R_19', 0) # release
	# Select FCR/HSD
	pushSeqCmd(dt, 'MFD_L_14', 1) # B3 OSB
	pushSeqCmd(dt, 'MFD_L_14', 0) # release
	pushSeqCmd(dt, 'MFD_R_13', 1) # B3 OSB
	pushSeqCmd(dt, 'MFD_R_13', 0) # release

	# Return to NAV mode
	pushSeqCmd(dt, 'ICP_AG_MODE_BTN', 1) # Switch back to NAV Master Mode (we were in A-G mode)
	pushSeqCmd(dt, 'ICP_AG_MODE_BTN', 0)

	# DGFT OVRD mode
	pushSeqCmd(dt, 'scriptKeyboard', '3') # Note: No DCS BIOS command to switch to the override modes.  3 and 4 are the default keys for DGFT and MSL respectively.
	pushSeqCmd(dt, 'MFD_L_13', 1) # B3 OSB
	pushSeqCmd(dt, 'MFD_L_13', 0) # release
	pushSeqCmd(dt, 'MFD_L_13', 1) # B3 OSB
	pushSeqCmd(dt, 'MFD_L_13', 0) # release
	pushSeqCmd(dt, 'MFD_L_2', 1) # HAD
	pushSeqCmd(dt, 'MFD_L_2', 0) # release
	pushSeqCmd(dt, 'MFD_L_12', 1) # B4 OSB
	pushSeqCmd(dt, 'MFD_L_12', 0) # release
	pushSeqCmd(dt, 'MFD_L_12', 1) # B4 OSB
	pushSeqCmd(dt, 'MFD_L_12', 0) # release
	pushSeqCmd(dt, 'MFD_L_18', 1) # WPN
	pushSeqCmd(dt, 'MFD_L_18', 0) # release
	# Select FCR/SMS
	pushSeqCmd(dt, 'MFD_R_13', 1) # B3 OSB
	pushSeqCmd(dt, 'MFD_R_13', 0) # release
	pushSeqCmd(dt, 'MFD_R_13', 1) # B3 OSB
	pushSeqCmd(dt, 'MFD_R_13', 0) # release
	pushSeqCmd(dt, 'MFD_R_7', 1) # HSD
	pushSeqCmd(dt, 'MFD_R_7', 0) # release
	pushSeqCmd(dt, 'MFD_R_12', 1) # B4 OSB
	pushSeqCmd(dt, 'MFD_R_12', 0) # release
	pushSeqCmd(dt, 'MFD_R_12', 1) # B4 OSB
	pushSeqCmd(dt, 'MFD_R_12', 0) # release
	pushSeqCmd(dt, 'MFD_R_19', 1) # TGP
	pushSeqCmd(dt, 'MFD_R_19', 0) # release
	# Select FCR/HSD
	pushSeqCmd(dt, 'MFD_L_14', 1) # B3 OSB
	pushSeqCmd(dt, 'MFD_L_14', 0) # release
	pushSeqCmd(dt, 'MFD_R_13', 1) # B3 OSB
	pushSeqCmd(dt, 'MFD_R_13', 0) # release
	# Return to NAV mode
	pushSeqCmd(dt, 'scriptKeyboard', '3')

	# MSL OVRD mode
	pushSeqCmd(dt, 'scriptKeyboard', '4') # Note: No DCS BIOS command to switch to the override modes.  3 and 4 are the default keys for DGFT and MSL respectively.
	pushSeqCmd(dt, 'MFD_L_13', 1) # B3 OSB
	pushSeqCmd(dt, 'MFD_L_13', 0) # release
	pushSeqCmd(dt, 'MFD_L_13', 1) # B3 OSB
	pushSeqCmd(dt, 'MFD_L_13', 0) # release
	pushSeqCmd(dt, 'MFD_L_2', 1) # HAD
	pushSeqCmd(dt, 'MFD_L_2', 0) # release
	pushSeqCmd(dt, 'MFD_L_12', 1) # B4 OSB
	pushSeqCmd(dt, 'MFD_L_12', 0) # release
	pushSeqCmd(dt, 'MFD_L_12', 1) # B4 OSB
	pushSeqCmd(dt, 'MFD_L_12', 0) # release
	pushSeqCmd(dt, 'MFD_L_18', 1) # WPN
	pushSeqCmd(dt, 'MFD_L_18', 0) # release
	# Right MFD
	pushSeqCmd(dt, 'MFD_R_13', 1) # B3 OSB
	pushSeqCmd(dt, 'MFD_R_13', 0) # release
	pushSeqCmd(dt, 'MFD_R_13', 1) # B3 OSB
	pushSeqCmd(dt, 'MFD_R_13', 0) # release
	pushSeqCmd(dt, 'MFD_R_7', 1) # HSD
	pushSeqCmd(dt, 'MFD_R_7', 0) # release
	pushSeqCmd(dt, 'MFD_R_12', 1) # B4 OSB
	pushSeqCmd(dt, 'MFD_R_12', 0) # release
	pushSeqCmd(dt, 'MFD_R_12', 1) # B4 OSB
	pushSeqCmd(dt, 'MFD_R_12', 0) # release
	pushSeqCmd(dt, 'MFD_R_19', 1) # TGP
	pushSeqCmd(dt, 'MFD_R_19', 0) # release
	# Select FCR/HSD
	pushSeqCmd(dt, 'MFD_L_14', 1) # B3 OSB
	pushSeqCmd(dt, 'MFD_L_14', 0) # release
	pushSeqCmd(dt, 'MFD_R_13', 1) # B3 OSB
	pushSeqCmd(dt, 'MFD_R_13', 0) # release
	# Return to NAV mode
	pushSeqCmd(dt, 'scriptKeyboard', '4')
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

	insAlignTime = 95 # 1m30s
	engineSpoolTime = 25

	pushSeqCmd(0, '', '', "Running Cold Start sequence")
	pushSeqCmd(dt, 'scriptSpeech', 'Do not rearm until alignment complete.')

	pushSeqCmd(dt, 'MAIN_PWR_SW', 2, "MAIN PWR SWITCH - ON") # 0 = OFF, 1 = BATT, 2 = MAIN PWR
	pushSeqCmd(dt, 'ANTI_SKID_SW', 2, "PARKING BRAKE/ANTI-SKID SWITCH - PARKING BRAKE") # 0 = OFF, 1 = ANTI-SKID, 2 = PARKING BRAKE

	# Starting Engine (60s)
	# SPOOL UP (25s) - 20% RPM MINIMUM
	pushSeqCmd(dt, 'scriptTimerStart', name='engineTimer', duration=engineSpoolTime)
	pushSeqCmd(dt, 'JFS_SW', 0, "JFS SWITCH - START 2") # 0 = START 2, 1 = OFF, 2 = START 1
	pushSeqCmd(dt, 'JFS_SW', 1, "JFS SWITCH - OFF") # 0 = START 2, 1 = OFF, 2 = START 1

	# Close canopy while we wait
	#pushSeqCmd(dt, '', '', "CANOPY - CLOSE AND LOCK
	pushSeqCmd(dt, 'CANOPY_HANDLE', 0) # Unlock, up
	pushSeqCmd(dt, 'CANOPY_SW', 0)
	pushSeqCmd(7, 'CANOPY_SW', 1)
	pushSeqCmd(dt, 'CANOPY_HANDLE', 1) # Lock, down

	pushSeqCmd(dt, 'scriptTimerEnd', name='engineTimer')
	pushSeqCmd(dt, '', '', 'Engine at 25%')

	# ENGINE START (35s)
	# THROTTLE - IDLE
	pushSeqCmd(dt, 'scriptKeyboard', 'RShift down')
	pushSeqCmd(dt, 'scriptKeyboard', 'home')
	pushSeqCmd(dt, 'scriptKeyboard', 'RShift up')
	pushSeqCmd(25, '', '', 'Engine started')

	# Interior lights
	if vars.get('Time') == 'Day':
		pushSeqCmd(dt, 'PRI_CONSOLES_BRT_KNB', int16())
		pushSeqCmd(dt, 'PRI_INST_PNL_BRT_KNB', int16())
		pushSeqCmd(dt, 'AOA_INDEX_BRT_KNB', int16())
		pushSeqCmd(dt, 'AR_STATUS_BRT_KNB', int16())
	else:
		pushSeqCmd(dt, 'PRI_CONSOLES_BRT_KNB', int16(0.5))
		pushSeqCmd(dt, 'PRI_INST_PNL_BRT_KNB', int16(0.5))
		pushSeqCmd(dt, 'AOA_INDEX_BRT_KNB', int16(0.5))
		pushSeqCmd(dt, 'AR_STATUS_BRT_KNB', int16(0.5))
		# Cockpit flood lights start on at night, so turn them off.
		pushSeqCmd(dt, 'FLOOD_CONSOLES_BRT_KNB', 0)
		pushSeqCmd(dt, 'FLOOD_INST_PNL_BRT_KNB', 0)

	# AVIONICS POWER panel
	pushSeqCmd(dt, 'MMC_PWR_SW', 1, "MMC SWITCH - ON")
	pushSeqCmd(dt, 'ST_STA_SW', 1, "ST STA SWITCH - ON")
	pushSeqCmd(dt, 'MFD_SW', 1, "MFD SWITCH - ON")
	pushSeqCmd(dt, 'UFC_SW', 1, "UFC SWITCH - ON")
	#pushSeqCmd(dt, 'MAP_SW', 1, "MAP SWITCH - ON") # Not used.
	pushSeqCmd(dt, 'GPS_SW', 1, "GPS SWITCH - ON")
	#pushSeqCmd(dt, 'DL_SW', 1, "DL SWITCH - ON") # Not used, see MDS LVT knob for datalink.
	# v.2.9.3.51704: MIDS switch should be left OFF until 60 seconds after GPS switch is set to ON.

	# Begin alignment, takes 90 seconds for STOR HDG.
	pushSeqCmd(dt, 'INS_KNB', 1, "INS KNOB - STOR HDG") # 0 = OFF, 1 = STOR HDG, 2 = NORM, 3 = NAV, 4 = CAL, 5 = IN FLT ALIGN, 6 = ATT
	pushSeqCmd(dt, 'scriptTimerStart', name='alignTimer', duration=insAlignTime)
	# Shouldn't have to verify starting coordinates when using STOR HDG, but might not hurt to do it anyway...
	pushSeqCmd(3, '', '', "VERIFYING INITIAL COORDINATES ON DED")
	pushSeqCmd(dt, 'ICP_ENTR_BTN', 1)
	pushSeqCmd(dt, 'ICP_ENTR_BTN', 0)
	pushSeqCmd(dt, 'ICP_DATA_UP_DN_SW', 0) # 0 = Down, 1 = center, 2 = Up
	pushSeqCmd(0.5, 'ICP_DATA_UP_DN_SW', 1) # 0 = Down, 1 = center, 2 = Up
	pushSeqCmd(dt, 'ICP_ENTR_BTN', 1)
	pushSeqCmd(dt, 'ICP_ENTR_BTN', 0)

	# SNSR PWR panel
	pushSeqCmd(dt, 'FCR_PWR_SW', 1, "FCR SWITCH - ON")
	pushSeqCmd(dt, 'RDR_ALT_PWR_SW', 1, "RDR ALT SWITCH - ON")

	if vars.get('Time') == 'Day':
		pushSeqCmd(dt, 'HMCS_INT_KNB', int16(), "HMCS BRIGHTNESS - MAX")
		pushSeqCmd(dt, 'ICP_HUD_BRT_KNB', int16(), "HUD BRIGHTNESS - MAX")
	else:
		pushSeqCmd(dt, 'HMCS_INT_KNB', int16(0.5), "HMCS BRIGHTNESS - 50%")
		pushSeqCmd(dt, 'ICP_HUD_BRT_KNB', int16(0.5), "HUD BRIGHTNESS - 50%")

	pushSeqCmd(dt, 'SAI_PITCH_TRIM', int16(0.5), "STANDBY ATTITUDE INDICATOR - UNCAGE AND CENTER")

	# UHF Radio
	pushSeqCmd(dt, 'UHF_FUNC_KNB', 1, "UHF FUNCTION KNOB - MAIN") # 0 = OFF, 1 = MAIN, 2 = BOTH, 3 = ADF

	# IFF
	pushSeqCmd(dt, 'IFF_MASTER_KNB', 3, "IFF MASTER KNOB - NORM") # 0 = OFF, 1 = STBY, 2 = LOW, 3 = NORM, 4 = EMER

	# CMDS panel
	pushSeqCmd(dt, 'CMDS_PWR_SOURCHE_SW', 1, "CMDS RWR SWITCH - ON")
	pushSeqCmd(dt, 'CMDS_JMR_SOURCHE_SW', 1, "CMDS JMR SWITCH - ON")
	pushSeqCmd(dt, 'CMDS_CH_EXP_CAT_SW', 1, "CMDS CH SWITCH - ON")
	pushSeqCmd(dt, 'CMDS_FL_EXP_CAT_SW', 1, "CMDS FL SWITCH - ON")
	pushSeqCmd(dt, 'CMDS_MODE_KNB', 2, "CMDS MODE KNOB - MAN (MANUAL CHAFF/FLARES)") # 0 = OFF, 1 = STBY, 2 = MAN, 3 = SEMI, 4 = AUTO, 5 = BYP

	# Left and right hardpoints on
	pushSeqCmd(dt, 'HDPT_SW_L', 1)
	pushSeqCmd(dt, 'HDPT_SW_R', 1)

	# RWR
	pushSeqCmd(dt, 'RWR_PWR_BTN', 1, "RWR INDICATOR CONTROL POWER - ON") # Press only
	pushSeqCmd(dt, 'RWR_SEARCH_BTN', 1, "RWR INDICATOR SEARCH BUTTON - ON") # Press only

	# DATALINK XMT - L16 (RMFD OSB 6/R1)
	pushSeqCmd(dt, 'MFD_R_6', 1) # Press
	pushSeqCmd(dt, 'MFD_R_6', 0) # Release

	# Set up the MFDs while we wait for alignment to complete.
	setupMFDs(dt, seq, pushSeqCmd)

	pushSeqCmd(dt, 'scriptSpeech', 'Don\'t rearm until alignment complete.') # Reminder not to rearm until alignment is complete.

	pushSeqCmd(dt, 'scriptTimerEnd', name='alignTimer')
	pushSeqCmd(dt, '', '', 'INS alignment complete')

	# INS Knob - NAV after aligning
	pushSeqCmd(dt, 'INS_KNB', 3, "INS KNOB - NAV") # 0 = OFF, 1 = STOR HDG, 2 = NORM, 3 = NAV, 4 = CAL, 5 = IN FLT ALIGN, 6 = ATT
	pushSeqCmd(dt, 'scriptSpeech', 'Alignment complete, you may now rearm.')

	# MIDS switch - ON
	pushSeqCmd(dt, 'MIDS_LVT_KNB', 2, "MDS LVT KNOB - ON") # Required for Link16 to work. 0 = ZERO, 1 = OFF, 2 = ON

	# RETURN TO MAIN DED PAGE
	pushSeqCmd(dt, 'ICP_DATA_RTN_SEQ_SW', 0) # 0 = RTN, 1 = center, 2 = SEQ
	pushSeqCmd(0.5, 'ICP_DATA_RTN_SEQ_SW', 1) # 0 = RTN, 1 = center, 2 = SEQ

	# ECM
	# ECM POWER SWITCH - ON
	pushSeqCmd(dt, 'ECM_PW_SW', 1) # Must go through center position first.  0 = OFF, 1 = STBY, 2 = OPR
	pushSeqCmd(dt, 'ECM_PW_SW', 2)
	# ECM modules ON
	pushSeqCmd(dt, 'ECM_1_BTN', 1, "ECM 1 MODULE - ON")
	pushSeqCmd(dt, 'ECM_2_BTN', 1, "ECM 2 MODULE - ON")
	pushSeqCmd(dt, 'ECM_3_BTN', 1, "ECM 3 MODULE - ON")
	pushSeqCmd(dt, 'ECM_4_BTN', 1, "ECM 4 MODULE - ON")
	pushSeqCmd(dt, 'ECM_5_BTN', 1, "ECM 5 MODULE - ON")
	pushSeqCmd(dt, 'ECM_6_BTN', 1, "ECM 6 MODULE - ON")

	# Prepare HMCS for alignment
	pushSeqCmd(dt, 'ICP_LIST_BTN', 1)
	pushSeqCmd(dt, 'ICP_LIST_BTN', 0)
	pushSeqCmd(dt, 'ICP_BTN_0', 1) # MISC in DED
	pushSeqCmd(dt, 'ICP_BTN_0', 0)
	pushSeqCmd(dt, 'ICP_RCL_BTN', 1) # HMCS in DED
	pushSeqCmd(dt, 'ICP_RCL_BTN', 0)
	pushSeqCmd(dt, 'ICP_DATA_RTN_SEQ_SW', 2) # HMCS ALIGN; 0 = RTN, 1 = center, 2 = SEQ
	pushSeqCmd(0.5, 'ICP_DATA_RTN_SEQ_SW', 1) # 0 = RTN, 1 = center, 2 = SEQ
	pushSeqCmd(dt, 'ICP_BTN_0', 1) # COARSE in DED
	pushSeqCmd(dt, 'ICP_BTN_0', 0)
	pushSeqCmd(dt, 'scriptSpeech', 'Press shift T D C press to align.  Press M SELL (zero) twice to go to next mode, use T D C to align, then go to next mode and align.  When all modes are aligned press Return on Dobber to exit align.')

	# Laser arm switch - ARM
	pushSeqCmd(dt, 'LASER_ARM_SW', 1)

	# Master arm switch - ARM
	pushSeqCmd(dt, 'MASTER_ARM_SW', 2)

	pushSeqCmd(dt, 'SEAT_EJECT_SAFE', 1, "EJECTION SAFETY LEVER - ARM (DOWN)")
	pushSeqCmd(dt, 'ANTI_SKID_SW', 1, "PARKING BRAKE/ANTI-SKID SWITCH - ANTI-SKID") # 0 = OFF, 1 = ANTI-SKID, 2 = PARKING BRAKE

	# Probe Heat (only when icing conditions on the ground, must take off within 5 minutes to prevent overheat)
	#FIXME: pushSeqCmd(dt, ELEC_INTERFACE, action = elec_commands.ProbeHeatSw, 1)
	pushSeqCmd(dt, 'scriptSpeech', 'Manual steps remaining: Set cat 1 or cat 3.')

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

	# Interior lights
	if vars.get('Time') == 'Day':
		pushSeqCmd(dt, 'PRI_CONSOLES_BRT_KNB', int16())
		pushSeqCmd(dt, 'PRI_INST_PNL_BRT_KNB', int16())
		pushSeqCmd(dt, 'AOA_INDEX_BRT_KNB', int16())
		pushSeqCmd(dt, 'AR_STATUS_BRT_KNB', int16())
	else:
		pushSeqCmd(dt, 'PRI_CONSOLES_BRT_KNB', int16(0.5))
		pushSeqCmd(dt, 'PRI_INST_PNL_BRT_KNB', int16(0.5))
		pushSeqCmd(dt, 'AOA_INDEX_BRT_KNB', int16(0.5))
		pushSeqCmd(dt, 'AR_STATUS_BRT_KNB', int16(0.5))
		# Cockpit flood lights start on at night, so turn them off.
		pushSeqCmd(dt, 'FLOOD_CONSOLES_BRT_KNB', 0)
		pushSeqCmd(dt, 'FLOOD_INST_PNL_BRT_KNB', 0)

	if vars.get('Time') == 'Day':
		pushSeqCmd(dt, 'HMCS_INT_KNB', int16(), "HMCS BRIGHTNESS - MAX")
		pushSeqCmd(dt, 'ICP_HUD_BRT_KNB', int16(), "HUD BRIGHTNESS - MAX")
	else:
		pushSeqCmd(dt, 'HMCS_INT_KNB', int16(0.5), "HMCS BRIGHTNESS - 50%")
		pushSeqCmd(dt, 'ICP_HUD_BRT_KNB', int16(0.5), "HUD BRIGHTNESS - 50%")

	# UHF Radio
	pushSeqCmd(dt, 'UHF_FUNC_KNB', 1, "UHF FUNCTION KNOB - MAIN") # 0 = OFF, 1 = MAIN, 2 = BOTH, 3 = ADF

	# CMDS panel
	pushSeqCmd(dt, 'CMDS_MODE_KNB', 2, "CMDS MODE KNOB - MAN (MANUAL CHAFF/FLARES)") # 0 = OFF, 1 = STBY, 2 = MAN, 3 = SEMI, 4 = AUTO, 5 = BYP

	# Left and right hardpoints on
	pushSeqCmd(dt, 'HDPT_SW_L', 1)
	pushSeqCmd(dt, 'HDPT_SW_R', 1)

	# RWR
	pushSeqCmd(dt, 'RWR_PWR_BTN', 1, "RWR INDICATOR CONTROL POWER - ON") # Press only
	pushSeqCmd(dt, 'RWR_SEARCH_BTN', 1, "RWR INDICATOR SEARCH BUTTON - ON") # Press only

	# DATALINK XMT - L16 (RMFD OSB 6/R1)
	pushSeqCmd(dt, 'MFD_R_6', 1) # Press
	pushSeqCmd(dt, 'MFD_R_6', 0) # Release

	# ECM
	# ECM POWER SWITCH - ON
	pushSeqCmd(dt, 'ECM_PW_SW', 1) # Must go through center position first.  0 = OFF, 1 = STBY, 2 = OPR
	pushSeqCmd(dt, 'ECM_PW_SW', 2)
	# ECM XMIT SWITCH - 3 (BARRAGE JAMMING)
	#pushSeqCmd(dt, 'ECM_XMIT_SW', 1) # Must go through center position first.  0 = 3, 1 = 2, 2 = 1
	#pushSeqCmd(dt, 'ECM_XMIT_SW', 2)
	pushSeqCmd(dt, 'ECM_1_BTN', 1, "ECM 1 MODULE - ON")
	pushSeqCmd(dt, 'ECM_2_BTN', 1, "ECM 2 MODULE - ON")
	pushSeqCmd(dt, 'ECM_3_BTN', 1, "ECM 3 MODULE - ON")
	pushSeqCmd(dt, 'ECM_4_BTN', 1, "ECM 4 MODULE - ON")
	pushSeqCmd(dt, 'ECM_5_BTN', 1, "ECM 5 MODULE - ON")
	pushSeqCmd(dt, 'ECM_6_BTN', 1, "ECM 6 MODULE - ON")

	setupMFDs(dt, seq, pushSeqCmd)

	# Laser arm switch - ARM
	pushSeqCmd(dt, 'LASER_ARM_SW', 1)

	# Master arm switch - ARM
	pushSeqCmd(dt, 'MASTER_ARM_SW', 2)

	pushSeqCmd(dt, 'scriptSpeech', 'Manual steps remaining: Set cat 1 or cat 3.')

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

	pushSeqCmd(0, '', '', "Running Air Start sequence")

	# Interior lights
	if vars.get('Time') == 'Day':
		pushSeqCmd(dt, 'PRI_CONSOLES_BRT_KNB', int16())
		pushSeqCmd(dt, 'PRI_INST_PNL_BRT_KNB', int16())
		pushSeqCmd(dt, 'AOA_INDEX_BRT_KNB', int16())
		pushSeqCmd(dt, 'AR_STATUS_BRT_KNB', int16())
	else:
		pushSeqCmd(dt, 'PRI_CONSOLES_BRT_KNB', int16(0.5))
		pushSeqCmd(dt, 'PRI_INST_PNL_BRT_KNB', int16(0.5))
		pushSeqCmd(dt, 'AOA_INDEX_BRT_KNB', int16(0.5))
		pushSeqCmd(dt, 'AR_STATUS_BRT_KNB', int16(0.5))
		# Cockpit flood lights start on at night, so turn them off.
		pushSeqCmd(dt, 'FLOOD_CONSOLES_BRT_KNB', 0)
		pushSeqCmd(dt, 'FLOOD_INST_PNL_BRT_KNB', 0)

	if vars.get('Time') == 'Day':
		pushSeqCmd(dt, 'HMCS_INT_KNB', int16(), "HMCS BRIGHTNESS - MAX")
		pushSeqCmd(dt, 'ICP_HUD_BRT_KNB', int16(), "HUD BRIGHTNESS - MAX")
	else:
		pushSeqCmd(dt, 'HMCS_INT_KNB', int16(0.5), "HMCS BRIGHTNESS - 50%")
		pushSeqCmd(dt, 'ICP_HUD_BRT_KNB', int16(0.5), "HUD BRIGHTNESS - 50%")

	# UHF Radio
	pushSeqCmd(dt, 'UHF_FUNC_KNB', 1, "UHF FUNCTION KNOB - MAIN") # 0 = OFF, 1 = MAIN, 2 = BOTH, 3 = ADF

	# Left and right hardpoints on
	pushSeqCmd(dt, 'HDPT_SW_L', 1)
	pushSeqCmd(dt, 'HDPT_SW_R', 1)

	# RWR
	pushSeqCmd(dt, 'RWR_SEARCH_BTN', 1, "RWR INDICATOR SEARCH BUTTON - ON") # Press only

	# DATALINK XMT - L16 (RMFD OSB 6/R1)
	pushSeqCmd(dt, 'MFD_R_6', 1) # Press
	pushSeqCmd(dt, 'MFD_R_6', 0) # Release

	# ECM
	pushSeqCmd(dt, 'ECM_1_BTN', 1, "ECM 1 MODULE - ON")
	pushSeqCmd(dt, 'ECM_2_BTN', 1, "ECM 2 MODULE - ON")
	pushSeqCmd(dt, 'ECM_3_BTN', 1, "ECM 3 MODULE - ON")
	pushSeqCmd(dt, 'ECM_4_BTN', 1, "ECM 4 MODULE - ON")
	pushSeqCmd(dt, 'ECM_5_BTN', 1, "ECM 5 MODULE - ON")
	pushSeqCmd(dt, 'ECM_6_BTN', 1, "ECM 6 MODULE - ON")

	setupMFDs(dt, seq, pushSeqCmd)

	# Laser arm switch - ARM
	pushSeqCmd(dt, 'LASER_ARM_SW', 1)

	# Master arm switch - ARM
	pushSeqCmd(dt, 'MASTER_ARM_SW', 2)

	pushSeqCmd(dt, 'scriptSpeech', 'Manual steps remaining: Set cat 1 or cat 3.')

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

	# AVIONICS POWER panel
	pushSeqCmd(dt, 'MMC_PWR_SW', 0) # MMC SWITCH - OFF
	pushSeqCmd(dt, 'ST_STA_SW', 0) # ST STA SWITCH - OFF
	pushSeqCmd(dt, 'MFD_SW', 0) # MFD SWITCH - OFF
	pushSeqCmd(dt, 'UFC_SW', 0) #, "UFC SWITCH - OFF
	#pushSeqCmd(dt, 'MAP_SW', 0) # MAP SWITCH - OFF (not used)
	pushSeqCmd(dt, 'GPS_SW', 0) # GPS SWITCH - OFF
	#pushSeqCmd(dt, 'DL_SW', 0) # DL SWITCH - OFF (not used)
	pushSeqCmd(dt, 'MIDS_LVT_KNB', 0) # MDS LVT KNOB - OFF

	# INS off
	pushSeqCmd(dt, 'INS_KNB', 0) # INS KNOB - OFF # 0 = OFF, 1 = STOR HDG, 2 = NORM, 3 = NAV, 4 = CAL, 5 = IN FLT ALIGN, 6 = ATT

	# SNSR PWR panel
	pushSeqCmd(dt, 'FCR_PWR_SW', 0) # FCR SWITCH - OFF
	pushSeqCmd(dt, 'RDR_ALT_PWR_SW', 0) # RDR ALT SWITCH - OFF

	pushSeqCmd(dt, 'HMCS_INT_KNB', 0)
	pushSeqCmd(dt, 'ICP_HUD_BRT_KNB', 0)

	#pushSeqCmd(dt, 'SAI_PITCH_TRIM', int16(0.5), "STANDBY ATTITUDE INDICATOR - UNCAGE AND CENTER")

	# UHF Radio
	pushSeqCmd(dt, 'UHF_FUNC_KNB', 0) # 0 = OFF, 1 = MAIN, 2 = BOTH, 3 = ADF

	# IFF
	pushSeqCmd(dt, 'IFF_MASTER_KNB', 0) # 0 = OFF, 1 = STBY, 2 = LOW, 3 = NORM, 4 = EMER

	# CMDS panel
	pushSeqCmd(dt, 'CMDS_PWR_SOURCHE_SW', 0, "CMDS RWR SWITCH - OFF")
	pushSeqCmd(dt, 'CMDS_JMR_SOURCHE_SW', 0, "CMDS JMR SWITCH - OFF")
	pushSeqCmd(dt, 'CMDS_CH_EXP_CAT_SW', 0, "CMDS CH SWITCH - OFF")
	pushSeqCmd(dt, 'CMDS_FL_EXP_CAT_SW', 0, "CMDS FL SWITCH - OFF")
	pushSeqCmd(dt, 'CMDS_MODE_KNB', 0, "CMDS MODE KNOB - MAN (MANUAL CHAFF/FLARES)") # 0 = OFF, 1 = STBY, 2 = MAN, 3 = SEMI, 4 = AUTO, 5 = BYP

	# Left and right hardpoints off
	pushSeqCmd(dt, 'HDPT_SW_L', 0)
	pushSeqCmd(dt, 'HDPT_SW_R', 0)

	# RWR
	pushSeqCmd(dt, 'RWR_PWR_BTN', 1, "RWR INDICATOR CONTROL POWER - OFF") # Press only
	pushSeqCmd(dt, 'RWR_SEARCH_BTN', 1, "RWR INDICATOR SEARCH BUTTON - OFF") # Press only

	# ECM
	# ECM POWER SWITCH - OFF
	pushSeqCmd(dt, 'ECM_PW_SW', 1) # Must go through center position first.  0 = OFF, 1 = STBY, 2 = OPR
	pushSeqCmd(dt, 'ECM_PW_SW', 0)
	# ECM modules OFF
	pushSeqCmd(dt, 'ECM_1_BTN', 0, "ECM 1 MODULE - OFF")
	pushSeqCmd(dt, 'ECM_2_BTN', 0, "ECM 2 MODULE - OFF")
	pushSeqCmd(dt, 'ECM_3_BTN', 0, "ECM 3 MODULE - OFF")
	pushSeqCmd(dt, 'ECM_4_BTN', 0, "ECM 4 MODULE - OFF")
	pushSeqCmd(dt, 'ECM_5_BTN', 0, "ECM 5 MODULE - OFF")
	pushSeqCmd(dt, 'ECM_6_BTN', 0, "ECM 6 MODULE - OFF")

	pushSeqCmd(dt, 'SEAT_EJECT_SAFE', 0, "EJECTION SAFETY LEVER - SAFE (UP)")
	pushSeqCmd(dt, 'ANTI_SKID_SW', 2, "PARKING BRAKE/ANTI-SKID SWITCH - PARKING BRAKE") # 0 = OFF, 1 = ANTI-SKID, 2 = PARKING BRAKE

	# Probe Heat (only when icing conditions on the ground, must take off within 5 minutes to prevent overheat)
	#FIXME: pushSeqCmd(dt, ELEC_INTERFACE, action = elec_commands.ProbeHeatSw, 0)

	# Interior lights
	pushSeqCmd(dt, 'PRI_CONSOLES_BRT_KNB', 0)
	pushSeqCmd(dt, 'PRI_INST_PNL_BRT_KNB', 0)
	pushSeqCmd(dt, 'AOA_INDEX_BRT_KNB', 0)
	pushSeqCmd(dt, 'AR_STATUS_BRT_KNB', 0)
	pushSeqCmd(dt, 'FLOOD_CONSOLES_BRT_KNB', 0)
	pushSeqCmd(dt, 'FLOOD_INST_PNL_BRT_KNB', 0)

	# Open canopy
	pushSeqCmd(dt, 'CANOPY_HANDLE', 0) # Unlock, up
	pushSeqCmd(dt, 'CANOPY_SW', 2)
	pushSeqCmd(11, 'CANOPY_SW', 1)

	# THROTTLE - OFF
	pushSeqCmd(dt, 'scriptKeyboard', 'RShift down')
	pushSeqCmd(dt, 'scriptKeyboard', 'end')
	pushSeqCmd(dt, 'scriptKeyboard', 'RShift up')

	pushSeqCmd(dt, 'MAIN_PWR_SW', 0, "MAIN PWR SWITCH - ON") # 0 = OFF, 1 = BATT, 2 = MAIN PWR

	return seq
