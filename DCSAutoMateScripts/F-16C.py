# Return a Dictionary of script titles and their corresponding function names.  This is a list of scripts that users will be selecting from.  The module may have other utility functions that will not be run directly by the users.
def getScriptFunctions():
	return {
		'Cold Start': 'ColdStart',
	}

def getInfo():
	return """"""

# Returns 0-65535 scaled by multiple (0-1), eg for 50% call int16(0.5)
def int16(mult = 1):
	int16 = 65535
	return int(mult * int16)

def ColdStart(config):
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
	
	insAlignTime = 95 # 1m30s
	engineSpoolTime = 25
	
	pushSeqCmd(0, '', '', "Running Cold Start sequence")
	pushSeqCmd(dt, 'scriptSpeech', 'Do not rearm until alignment complete.')

	pushSeqCmd(dt, 'MAIN_PWR_SW', 2, "MAIN PWR SWITCH - ON") # 0 = OFF, 1 = BATT, 2 = MAIN PWR
	pushSeqCmd(dt, 'ANTI_SKID_SW', 2, "PARKING BRAKE/ANTI-SKID SWITCH - PARKING BRAKE") # 0 = OFF, 1 = ANTI-SKID, 2 = PARKING BRAKE

	# Starting Engine
	#pushSeqCmd(dt, '', '', "STARTING UP (60s)"), message_timeout = 60.0)
	#pushSeqCmd(dt, '', '', "SPOOL UP (25s) - 20% RPM MINIMUM"), message_timeout = 25.0)
	engineSpoolTimerStart = getLastSeqTime()
	pushSeqCmd(dt, 'JFS_SW', 0, "JFS SWITCH - START 2") # 0 = START 2, 1 = OFF, 2 = START 1
	pushSeqCmd(dt, 'JFS_SW', 1, "JFS SWITCH - OFF") # 0 = START 2, 1 = OFF, 2 = START 1

	# Close canopy while we wait
	#pushSeqCmd(dt, '', '', "CANOPY - CLOSE AND LOCK"), message_timeout = 8.0)
	pushSeqCmd(dt, 'CANOPY_HANDLE', 0) # Unlock, up
	pushSeqCmd(dt, 'CANOPY_SW', 0)
	pushSeqCmd(7, 'CANOPY_SW', 1)
	pushSeqCmd(dt, 'CANOPY_HANDLE', 1) # Lock, down

	engineSpoolTimerEnd = engineSpoolTime - (getLastSeqTime() - engineSpoolTimerStart)
	pushSeqCmd(engineSpoolTimerEnd, '', '', 'Engine at 25%')


	#pushSeqCmd(dt, '', '', "ENGINE START (35s)"), message_timeout = 35.0)
	#pushSeqCmd(dt, '', '', "THROTTLE - IDLE")
	pushSeqCmd(dt, 'scriptKeyboard', '{VK_RSHIFT down}{VK_HOME}{VK_RSHIFT up}')
	pushSeqCmd(20, '', '', 'Engine started')

	pushSeqCmd(dt, 'PRI_CONSOLES_BRT_KNB', int16())
	pushSeqCmd(dt, 'PRI_INST_PNL_BRT_KNB', int16())
	
	# AVIONICS POWER panel
	#pushSeqCmd(dt, '', '', "AVIONICS POWER PANEL...")
	pushSeqCmd(dt, 'MMC_PWR_SW', 1, "MMC SWITCH - ON")
	pushSeqCmd(dt, 'ST_STA_SW', 1, "ST STA SWITCH - ON")
	pushSeqCmd(dt, 'MFD_SW', 1, "MFD SWITCH - ON")
	pushSeqCmd(dt, 'UFC_SW', 1, "UFC SWITCH - ON")
	#pushSeqCmd(dt, 'MAP_SW', 1, "MAP SWITCH - ON") # Not used.
	pushSeqCmd(dt, 'GPS_SW', 1, "GPS SWITCH - ON")
	#pushSeqCmd(dt, 'DL_SW', 1, "DL SWITCH - ON") # Not used, see MDS LVT knob for datalink.
	pushSeqCmd(dt, 'MIDS_LVT_KNB', 2, "MDS LVT KNOB - ON") # Required for Link16 to work. 0 = ZERO, 1 = OFF, 2 = ON

	# Begin alignment, takes 90 seconds for STOR HDG.
	#pushSeqCmd(dt, '', '', "INS ALIGNMENT (90s)..."), message_timeout = ins_align_time)
	pushSeqCmd(dt, 'INS_KNB', 1, "INS KNOB - STOR HDG") # 0 = OFF, 1 = STOR HDG, 2 = NORM, 3 = NAV, 4 = CAL, 5 = IN FLT ALIGN, 6 = ATT
	insAlignTimerStart = getLastSeqTime()
	# Shouldn't have to verify starting coordinates when using STOR HDG, but might not hurt to do it anyway...
	pushSeqCmd(3, '', '', "VERIFYING INITIAL COORDINATES ON DED")
	pushSeqCmd(dt, 'ICP_ENTR_BTN', 1)
	pushSeqCmd(dt, 'ICP_ENTR_BTN', 0)
	pushSeqCmd(dt, 'ICP_DATA_UP_DN_SW', 0) # 0 = Down, 1 = center, 2 = Up
	pushSeqCmd(0.5, 'ICP_DATA_UP_DN_SW', 1) # 0 = Down, 1 = center, 2 = Up
	pushSeqCmd(dt, 'ICP_ENTR_BTN', 1)
	pushSeqCmd(dt, 'ICP_ENTR_BTN', 0)
	
	# SNSR PWR panel
	#pushSeqCmd(dt, '', '', "SNSR PWR PANEL...")
	pushSeqCmd(dt, 'scriptSpeech', 'Turn on left or right hardpoints as needed.')
	pushSeqCmd(dt, 'FCR_PWR_SW', 1, "FCR SWITCH - ON")
	pushSeqCmd(dt, 'RDR_ALT_PWR_SW', 1, "RDR ALT SWITCH - ON")
	
	pushSeqCmd(dt, 'HMCS_INT_KNB', int16(), "HMCS BRIGHTNESS - MAX")
	pushSeqCmd(dt, 'ICP_HUD_BRT_KNB', int16(), "HUD BRIGHTNESS - MAX")
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

	# RWR
	pushSeqCmd(dt, 'RWR_PWR_BTN', 1, "RWR INDICATOR CONTROL POWER - ON") # Press only
	pushSeqCmd(dt, 'RWR_SEARCH_BTN', 1, "RWR INDICATOR SEARCH BUTTON - ON") # Press only

	# Datalink
	#pushSeqCmd(dt, '', '', "DATALINK XMT - L16 (RMFD OSB 6/R1)")
	pushSeqCmd(dt, 'MFD_R_6', 1) # Press
	pushSeqCmd(dt, 'MFD_R_6', 0) # Release

	insAlignTimerEnd = insAlignTime - (getLastSeqTime() - insAlignTimerStart)
	pushSeqCmd(insAlignTimerEnd, '', '', 'INS alignment complete')

	# INS Knob - NAV after aligning
	pushSeqCmd(dt, 'INS_KNB', 3, "INS KNOB - NAV") # 0 = OFF, 1 = STOR HDG, 2 = NORM, 3 = NAV, 4 = CAL, 5 = IN FLT ALIGN, 6 = ATT
	pushSeqCmd(dt, 'scriptSpeech', 'Alignment complete, you may now rearm.')

	#pushSeqCmd(dt, '', '', "RETURN TO MAIN DED PAGE")
	pushSeqCmd(dt, 'ICP_DATA_RTN_SEQ_SW', 0) # 0 = RTN, 1 = center, 2 = SEQ
	pushSeqCmd(0.5, 'ICP_DATA_RTN_SEQ_SW', 1) # 0 = RTN, 1 = center, 2 = SEQ

	# ECM
	#pushSeqCmd(dt, '', '', "ECM POWER SWITCH - ON")
	pushSeqCmd(dt, 'ECM_PW_SW', 1) # Must go through center position first.  0 = OFF, 1 = STBY, 2 = OPR
	pushSeqCmd(dt, 'ECM_PW_SW', 2)
	#pushSeqCmd(dt, '', '', "ECM XMIT SWITCH - 3 (BARRAGE JAMMING)")
	pushSeqCmd(dt, 'ECM_XMIT_SW', 1) # Must go through center position first.  0 = 3, 1 = 2, 2 = 1
	pushSeqCmd(dt, 'ECM_XMIT_SW', 2)
	pushSeqCmd(dt, 'ECM_1_BTN', 1, "ECM 1 MODULE - ON")
	pushSeqCmd(dt, 'ECM_2_BTN', 1, "ECM 2 MODULE - ON")
	pushSeqCmd(dt, 'ECM_3_BTN', 1, "ECM 3 MODULE - ON")
	pushSeqCmd(dt, 'ECM_4_BTN', 1, "ECM 4 MODULE - ON")
	pushSeqCmd(dt, 'ECM_5_BTN', 1, "ECM 5 MODULE - ON")
	pushSeqCmd(dt, 'ECM_6_BTN', 1, "ECM 6 MODULE - ON")
	
	pushSeqCmd(dt, 'SEAT_EJECT_SAFE', 1, "EJECTION SAFETY LEVER - ARM (DOWN)")
	pushSeqCmd(dt, 'ANTI_SKID_SW', 1, "PARKING BRAKE/ANTI-SKID SWITCH - ANTI-SKID") # 0 = OFF, 1 = ANTI-SKID, 2 = PARKING BRAKE

	# Probe Heat (only when icing conditions on the ground, must take off within 5 minutes to prevent overheat)
	##pushSeqCmd(dt, '', '', "PROBE HEAT - HEAT")
	#pushSeqCmd(dt, ELEC_INTERFACE, action = elec_commands.ProbeHeatSw, 1)

	#pushSeqCmd(dt, '', '', "HAVOC'S QUICK AUTOSTART IS COMPLETE"), message_timeout = 60.0)
	
	return seq
