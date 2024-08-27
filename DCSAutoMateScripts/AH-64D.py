# Return a Dictionary of script titles and their corresponding function names.  This is a list of scripts that users will be selecting from.  The module may have other utility functions that will not be run directly by the users.
def getScriptFunctions():
	return {
		'Cold Start, day': 'ColdStartDay',
		'Cold Start, night': 'ColdStartNight',
		'Hot Start, day': 'HotStartDay',
		'Hot Start, night': 'HotStartNight',
		'Shutdown': 'Shutdown',
		#'Test': 'Test',
	}

def getInfo():
	return """ATTENTION: You must remap "Power Lever (Left) - IDLE" to LAlt+Home, and "Power Lever (Left) - OFF" to LAlt+End.  This is because pyWinAuto doesn't support RAlt or RCtrl."""

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

	# Test code here...
	
	return seq

def ColdStartDay(config):
	return ColdStart(config, dayStart = True)

def ColdStartNight(config):
	return ColdStart(config, dayStart = False)

###############################################################################
###############################################################################
def ColdStart(config, dayStart = True):
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

	alignTime = 4 * 60 # 4m0s
	engine1StartTime = 30
	engine2StartTime = 40
	
	# Function to reset Master Warning and Master Caution for both PLT and CPG.
	def resetMasterCautionWarning():
		# Reset Master Caution and Master Warning
		# PLT - MASTER WARNING - Reset
		pushSeqCmd(dt, 'PLT_INTL_MWARN_BTN', 1) # MSTR WARN
		pushSeqCmd(dt, 'PLT_INTL_MWARN_BTN', 0) # release
		# PLT - MASTER CAUTION - Reset
		pushSeqCmd(dt, 'PLT_INTL_MCAUTION_BTN', 1) # MSTR CAUT
		pushSeqCmd(dt, 'PLT_INTL_MCAUTION_BTN', 0) # release
		# CPG - MASTER WARNING - Reset
		pushSeqCmd(dt, 'CPG_INTL_MWARN_BTN', 1) # MSTR WARN
		pushSeqCmd(dt, 'CPG_INTL_MWARN_BTN', 0) # release
		# CPG - MASTER CAUTION - Reset
		pushSeqCmd(dt, 'CPG_INTL_MCAUTION_BTN', 1) # MSTR CAUT
		pushSeqCmd(dt, 'CPG_INTL_MCAUTION_BTN', 0) # release
	
	# Function to set all the PLT TSD SHOW options.
	def setPltTsdShowOptions():
		# PLT - TSD SHOW options - Set all ON (turn off as needed later)
		# Setting up NAV PHASE
		pushSeqCmd(dt, 'PLT_MPD_R_TSD', 1) # TSD
		pushSeqCmd(dt, 'PLT_MPD_R_TSD', 0) # release
		
		# NAV PHASE
		# SHOW page
		pushSeqCmd(dt, 'PLT_MPD_R_T3', 1) # SHOW
		pushSeqCmd(dt, 'PLT_MPD_R_T3', 0) # release
		pushSeqCmd(dt, 'PLT_MPD_R_L3', 1) # INACTIVE ZONES
		pushSeqCmd(dt, 'PLT_MPD_R_L3', 0) # release
		pushSeqCmd(dt, 'PLT_MPD_R_L5', 1) # CPG CURSOR
		pushSeqCmd(dt, 'PLT_MPD_R_L5', 0) # release
		pushSeqCmd(dt, 'PLT_MPD_R_L6', 1) # CURSOR INFO
		pushSeqCmd(dt, 'PLT_MPD_R_L6', 0) # release
		pushSeqCmd(dt, 'PLT_MPD_R_R4', 1) # HSI
		pushSeqCmd(dt, 'PLT_MPD_R_R4', 0) # release
		# THRT SHOW page
		pushSeqCmd(dt, 'PLT_MPD_R_T5', 1) # THRT SHOW
		pushSeqCmd(dt, 'PLT_MPD_R_T5', 0) # release
		pushSeqCmd(dt, 'PLT_MPD_R_R5', 1) # THREATS
		pushSeqCmd(dt, 'PLT_MPD_R_R5', 0) # release
		pushSeqCmd(dt, 'PLT_MPD_R_R6', 1) # TARGETS
		pushSeqCmd(dt, 'PLT_MPD_R_R6', 0) # release
		# COORD SHOW page
		pushSeqCmd(dt, 'PLT_MPD_R_T6', 1) # COORD SHOW
		pushSeqCmd(dt, 'PLT_MPD_R_T6', 0) # release
		pushSeqCmd(dt, 'PLT_MPD_R_L3', 1) # FRIENDLY UNITS
		pushSeqCmd(dt, 'PLT_MPD_R_L3', 0) # release
		pushSeqCmd(dt, 'PLT_MPD_R_L4', 1) # ENEMY UNITS
		pushSeqCmd(dt, 'PLT_MPD_R_L4', 0) # release
		pushSeqCmd(dt, 'PLT_MPD_R_L5', 1) # PLANNED TGTS/THREATS
		pushSeqCmd(dt, 'PLT_MPD_R_L5', 0) # release
		
		pushSeqCmd(dt, 'PLT_MPD_R_T6', 1) # COORD SHOW
		pushSeqCmd(dt, 'PLT_MPD_R_T6', 0) # release
		# now we're back to the TSD > SHOW page
		
		# ATK PHASE
		pushSeqCmd(dt, 'PLT_MPD_R_B2', 1) # PHASE (to ATK)
		pushSeqCmd(dt, 'PLT_MPD_R_B2', 0) # release
		# SHOW page
		pushSeqCmd(dt, 'PLT_MPD_R_L2', 1) # CURRENT ROUTE
		pushSeqCmd(dt, 'PLT_MPD_R_L2', 0) # release
		pushSeqCmd(dt, 'PLT_MPD_R_L6', 1) # CURSOR INFO
		pushSeqCmd(dt, 'PLT_MPD_R_L6', 0) # release
		pushSeqCmd(dt, 'PLT_MPD_R_R4', 1) # HSI
		pushSeqCmd(dt, 'PLT_MPD_R_R4', 0) # release
		# THRT SHOW (already set from the NAV phase)
		# no action needed
		# COORD SHOW
		pushSeqCmd(dt, 'PLT_MPD_R_T6', 1) # COORD SHOW
		pushSeqCmd(dt, 'PLT_MPD_R_T6', 0) # release
		pushSeqCmd(dt, 'PLT_MPD_R_L4', 1) # ENEMY UNITS
		pushSeqCmd(dt, 'PLT_MPD_R_L4', 0) # release
		
		pushSeqCmd(dt, 'PLT_MPD_R_T3', 1) # SHOW
		pushSeqCmd(dt, 'PLT_MPD_R_T3', 0) # release
		# End TSD SHOW options, should now be back on the main TSD page.


	# Function to set all the CPG TSD SHOW options.
	def setCpgTsdShowOptions():
		# CPG - TSD SHOW options - Set all ON (turn off as needed later)
		# Setting up NAV PHASE
		pushSeqCmd(dt, 'CPG_MPD_R_TSD', 1) # TSD
		pushSeqCmd(dt, 'CPG_MPD_R_TSD', 0) # release
		
		# NAV PHASE
		# SHOW page
		pushSeqCmd(dt, 'CPG_MPD_R_T3', 1) # SHOW
		pushSeqCmd(dt, 'CPG_MPD_R_T3', 0) # release
		pushSeqCmd(dt, 'CPG_MPD_R_L3', 1) # INACTIVE ZONES
		pushSeqCmd(dt, 'CPG_MPD_R_L3', 0) # release
		pushSeqCmd(dt, 'CPG_MPD_R_L5', 1) # CPG CURSOR
		pushSeqCmd(dt, 'CPG_MPD_R_L5', 0) # release
		pushSeqCmd(dt, 'CPG_MPD_R_L6', 1) # CURSOR INFO
		pushSeqCmd(dt, 'CPG_MPD_R_L6', 0) # release
		pushSeqCmd(dt, 'CPG_MPD_R_R4', 1) # HSI
		pushSeqCmd(dt, 'CPG_MPD_R_R4', 0) # release
		# THRT SHOW page
		pushSeqCmd(dt, 'CPG_MPD_R_T5', 1) # THRT SHOW
		pushSeqCmd(dt, 'CPG_MPD_R_T5', 0) # release
		pushSeqCmd(dt, 'CPG_MPD_R_R5', 1) # THREATS
		pushSeqCmd(dt, 'CPG_MPD_R_R5', 0) # release
		pushSeqCmd(dt, 'CPG_MPD_R_R6', 1) # TARGETS
		pushSeqCmd(dt, 'CPG_MPD_R_R6', 0) # release
		# COORD SHOW
		pushSeqCmd(dt, 'CPG_MPD_R_T6', 1) # COORD SHOW
		pushSeqCmd(dt, 'CPG_MPD_R_T6', 0) # release
		pushSeqCmd(dt, 'CPG_MPD_R_L3', 1) # FRIENDLY UNITS
		pushSeqCmd(dt, 'CPG_MPD_R_L3', 0) # release
		pushSeqCmd(dt, 'CPG_MPD_R_L4', 1) # ENEMY UNITS
		pushSeqCmd(dt, 'CPG_MPD_R_L4', 0) # release
		pushSeqCmd(dt, 'CPG_MPD_R_L5', 1) # PLANNED TGTS/THREATS
		pushSeqCmd(dt, 'CPG_MPD_R_L5', 0) # release
		
		pushSeqCmd(dt, 'CPG_MPD_R_T6', 1) # COORD SHOW
		pushSeqCmd(dt, 'CPG_MPD_R_T6', 0) # release
		# now we're back to the TSD > SHOW page
		
		# ATK PHASE
		pushSeqCmd(dt, 'CPG_MPD_R_B2', 1) # PHASE (to ATK)
		pushSeqCmd(dt, 'CPG_MPD_R_B2', 0) # release
		# SHOW page
		pushSeqCmd(dt, 'CPG_MPD_R_L2', 1) # CURRENT ROUTE
		pushSeqCmd(dt, 'CPG_MPD_R_L2', 0) # release
		pushSeqCmd(dt, 'CPG_MPD_R_L6', 1) # CURSOR INFO
		pushSeqCmd(dt, 'CPG_MPD_R_L6', 0) # release
		pushSeqCmd(dt, 'CPG_MPD_R_R4', 1) # HSI
		pushSeqCmd(dt, 'CPG_MPD_R_R4', 0) # release
		# THRT SHOW (already set from the NAV phase)
		# no action needed
		# COORD SHOW
		pushSeqCmd(dt, 'CPG_MPD_R_T6', 1) # COORD SHOW
		pushSeqCmd(dt, 'CPG_MPD_R_T6', 0) # release
		pushSeqCmd(dt, 'CPG_MPD_R_L4', 1) # ENEMY UNITS
		pushSeqCmd(dt, 'CPG_MPD_R_L4', 0) # release
		
		pushSeqCmd(dt, 'CPG_MPD_R_T3', 1) # SHOW
		pushSeqCmd(dt, 'CPG_MPD_R_T3', 0) # release
		# End TSD SHOW options, should now be back on the main TSD page.
	

	# Start sequence
	pushSeqCmd(0, '', '', "Running Cold Start sequence")
	pushSeqCmd(dt, 'scriptSpeech', "Warning, uses non standard key bindings.")
	pushSeqCmd(dt, 'scriptSpeech', 'Set collective full down.')
	
	# Canopy Door - Close
	pushSeqCmd(dt, 'PLT_CANOPY', 0)
	pushSeqCmd(dt, 'CPG_CANOPY', 0)

	# Parking Brake - SET
	pushSeqCmd(dt, 'PLT_PARK_BRAKE', 1)
	# RTR BRK switch - OFF
	pushSeqCmd(dt, 'PLT_ROTOR_BRK', 2)

	# Lights
	if dayStart:
		# PLT Internal Lights
		pushSeqCmd(dt, 'PLT_INTL_SIGNAL_L_KNB', int16())
		pushSeqCmd(dt, 'PLT_INTL_PRIMARY_L_KNB', int16())
		pushSeqCmd(dt, 'PLT_INTL_STBYINST_L_KNB', int16())
		pushSeqCmd(dt, 'PLT_INTL_FLOOD_L_KNB', 0)
		# PLT External lights
		pushSeqCmd(dt, 'PLT_EXTL_NAV_L_SW', 1) # 0 = DIM, 1 = OFF, 2 = BRT
		pushSeqCmd(dt, 'PLT_EXTL_FROMATION_L_KNOB', 0) # NOTE misspelling, 0 = off, int16 = full on
		pushSeqCmd(dt, 'PLT_EXTL_ACOL_L_SW', 1) # 0 = RED, 1 = OFF, 2 = WHT
		# PLT CMWS
		pushSeqCmd(dt, 'PLT_CMWS_LAMP', int16())
		# PLT IHADSS symbology brightness
		pushSeqCmd(dt, 'PLT_VIDEO_SYM_BRT', int16())
		# PLT MPDs
		pushSeqCmd(dt, 'PLT_MPD_R_VIDEO', int16(0.25)) # Makes the TSD page easier to read.

		# CPG Internal Lights
		pushSeqCmd(dt, 'CPG_INTL_SIGNAL_L_KNB', int16())
		pushSeqCmd(dt, 'CPG_INTL_PRIMARY_L_KNB', int16())
		pushSeqCmd(dt, 'CPG_INTL_STBYINST_L_KNB', int16())
		pushSeqCmd(dt, 'CPG_INTL_FLOOD_L_KNB', 0)
		#CPG MPDs
		pushSeqCmd(dt, 'CPG_MPD_R_VIDEO', int16(0.25)) # Makes the TSD page easier to read.
	else:
		# PLT Internal Lights
		pushSeqCmd(dt, 'PLT_INTL_SIGNAL_L_KNB', int16(0.5))
		pushSeqCmd(dt, 'PLT_INTL_PRIMARY_L_KNB', int16(0.5))
		pushSeqCmd(dt, 'PLT_INTL_STBYINST_L_KNB', int16(0.5))
		pushSeqCmd(dt, 'PLT_INTL_FLOOD_L_KNB', 0)
		# PLT External lights
		pushSeqCmd(dt, 'PLT_EXTL_NAV_L_SW', 1) # 0 = DIM, 1 = OFF, 2 = BRT
		pushSeqCmd(dt, 'PLT_EXTL_FROMATION_L_KNOB', 0) # NOTE misspelling, 0 = off, int16 = full on
		pushSeqCmd(dt, 'PLT_EXTL_ACOL_L_SW', 1) # 0 = RED, 1 = OFF, 2 = WHT
		# PLT MPDs
		pushSeqCmd(dt, 'PLT_MPD_L_MODE', 1) # 0 = MONO, 1 = NT, 2 = DAY
		pushSeqCmd(dt, 'PLT_MPD_L_BRT', int16(0.5))
		pushSeqCmd(dt, 'PLT_MPD_L_VIDEO', int16(0.25))
		pushSeqCmd(dt, 'PLT_MPD_R_MODE', 1) # 0 = MONO, 1 = NT, 2 = DAY
		pushSeqCmd(dt, 'PLT_MPD_R_BRT', int16(0.5))
		pushSeqCmd(dt, 'PLT_MPD_R_VIDEO', int16(0.25))
		# PLT UFC
		pushSeqCmd(dt, 'PLT_EUFD_BRT', int16(0.25))
		# PLT KU
		pushSeqCmd(dt, 'PLT_KU_BRT', int16(0.33))
		# PLT CMWS
		pushSeqCmd(dt, 'PLT_CMWS_LAMP', int16(0.25))
		# PLT FLIR Level (IHADSS FLIR brightness)
		pushSeqCmd(dt, 'PLT_VIDEO_FLIR_LVL', int16(0.4))

		# CPG Internal Lights
		pushSeqCmd(dt, 'CPG_INTL_SIGNAL_L_KNB', int16(0.5))
		pushSeqCmd(dt, 'CPG_INTL_PRIMARY_L_KNB', int16(0.5))
		pushSeqCmd(dt, 'CPG_INTL_STBYINST_L_KNB', int16(0.5))
		pushSeqCmd(dt, 'CPG_INTL_FLOOD_L_KNB', 0)
		# CPG MPDs
		pushSeqCmd(dt, 'CPG_MPD_L_MODE', 1) # 0 = MONO, 1 = NT, 2 = DAY
		pushSeqCmd(dt, 'CPG_MPD_L_BRT', int16(0.5))
		pushSeqCmd(dt, 'CPG_MPD_L_VIDEO', int16(0.25))
		pushSeqCmd(dt, 'CPG_MPD_R_MODE', 1) # 0 = MONO, 1 = NT, 2 = DAY
		pushSeqCmd(dt, 'CPG_MPD_R_BRT', int16(0.5))
		pushSeqCmd(dt, 'CPG_MPD_R_VIDEO', int16(0.25))
		# CPG UFC
		pushSeqCmd(dt, 'CPG_EUFD_BRT', int16(0.25))
		# CPG KU
		pushSeqCmd(dt, 'CPG_KU_BRT', int16(0.33))
		# CPG FLIR Level (IHADSS FLIR brightness)
		pushSeqCmd(dt, 'CPG_VIDEO_FLIR_LVL', int16(0.4))
	
	# Starting APU - PILOT
	# MSTR IGN switch - BATT
	pushSeqCmd(dt, 'PLT_MASTER_IGN_SW', 1)

	# Radio volumes and squelch -- Do this immediately after turning on the battery so we don't get blasted by radio static while waiting for the APU.
	# PLT Radio squelch switches - ON (also squelches CPG radios)
	pushSeqCmd(dt, 'PLT_COM_VHF_SQL', 2)
	pushSeqCmd(dt, 'PLT_COM_VHF_SQL', 1)
	pushSeqCmd(dt, 'PLT_COM_UHF_SQL', 2)
	pushSeqCmd(dt, 'PLT_COM_UHF_SQL', 1)
	pushSeqCmd(dt, 'PLT_COM_FM1_SQL', 2)
	pushSeqCmd(dt, 'PLT_COM_FM1_SQL', 1)
	pushSeqCmd(dt, 'PLT_COM_FM2_SQL', 2)
	pushSeqCmd(dt, 'PLT_COM_FM2_SQL', 1)
	pushSeqCmd(dt, 'PLT_COM_HF_SQL', 2)
	pushSeqCmd(dt, 'PLT_COM_HF_SQL', 1)
	# PLT Radio RLWR volume - 75% # Already set by default.
	pushSeqCmd(dt, 'PLT_COM_RLWR_VOL', int16(0.75))
	## CPG
	## CPG Radio squelch switches - ON
	#pushSeqCmd(dt, device = devices.COMM_PANEL_CPG, action = comm_commands.VHF_SQL, 1)
	#pushSeqCmd(dt, device = devices.COMM_PANEL_CPG, action = comm_commands.UHF_SQL, 1)
	#pushSeqCmd(dt, device = devices.COMM_PANEL_CPG, action = comm_commands.FM1_SQL, 1)
	#pushSeqCmd(dt, device = devices.COMM_PANEL_CPG, action = comm_commands.FM2_SQL, 1)
	#pushSeqCmd(dt, device = devices.COMM_PANEL_CPG, action = comm_commands.HF_SQL, 1)
	# CPG Radio RLWR volume - 75%
	pushSeqCmd(dt, 'CPG_COM_RLWR_VOL', int16(0.75))
	
	# Starting APU (30s)
	pushSeqCmd(dt, 'PLT_APU_BTN_CVR', 1) # Cover open
	pushSeqCmd(dt, 'PLT_APU_BTN', 1) # Press
	pushSeqCmd(dt, 'PLT_APU_BTN', 0) # Release
	pushSeqCmd(30, '', '', 'APU started')
	
	# Alignment begins automatically after APU starts.
	# Waiting for EGI alignment, shows TSD chart background when finished (3m55s) ...
	alignTimerStart = getLastSeqTime() # Start a timer for the alignment process at the current seq time.

	# After starting APU
		
	# TEDAC
	if dayStart:
		pushSeqCmd(dt, 'CPG_TEDAC_DISP_MODE', 2) # 0 = OFF, 1 = NT, 2 = DAY
	else:
		pushSeqCmd(dt, 'CPG_TEDAC_DISP_MODE', 1) # 0 = OFF, 1 = NT, 2 = DAY
	
	# Use local time
	pushSeqCmd(dt, 'PLT_MPD_R_TSD', 1) # TSD
	pushSeqCmd(dt, 'PLT_MPD_R_TSD', 0) # release
	pushSeqCmd(dt, 'PLT_MPD_R_T6', 1) # UTIL
	pushSeqCmd(dt, 'PLT_MPD_R_T6', 0) # release
	pushSeqCmd(dt, 'PLT_MPD_R_R2', 1) # TIME
	pushSeqCmd(dt, 'PLT_MPD_R_R2', 0) # release
	pushSeqCmd(dt, 'PLT_MPD_R_T6', 1) # UTIL
	pushSeqCmd(dt, 'PLT_MPD_R_T6', 0) # release

	# TSD SHOW options
	setPltTsdShowOptions()
	setCpgTsdShowOptions()

	# CMWS
	# CMWS PWR knob - ON
	pushSeqCmd(dt, 'PLT_CMWS_PW', 1)
	# CMWS ARM/SAFE switch - ARM
	pushSeqCmd(dt, 'PLT_CMWS_ARM', 1)
	# CMWS CMWS/NAV switch - CMWS
	pushSeqCmd(dt, 'PLT_CMWS_MODE', 1)
	# CMWS BYPASS/AUTO switch - BYPASS
	pushSeqCmd(dt, 'PLT_CMWS_BYPASS', 1)

	# GND ORIDE - ON (needed to arm chaff)
	pushSeqCmd(dt, 'PLT_GROUND_OVERRIDE_BTN', 1) # press
	pushSeqCmd(dt, 'PLT_GROUND_OVERRIDE_BTN', 0) # release

	# MASTER ARM - ON
	pushSeqCmd(dt, 'PLT_MASTER_ARM_BTN', 1) # press
	pushSeqCmd(dt, 'PLT_MASTER_ARM_BTN', 0) # release

	# ASE CHAFF - ARM
	pushSeqCmd(dt, 'PLT_MPD_L_B1', 1) # MENU
	pushSeqCmd(dt, 'PLT_MPD_L_B1', 0) # release
	pushSeqCmd(dt, 'PLT_MPD_L_L3', 1) # ASE
	pushSeqCmd(dt, 'PLT_MPD_L_L3', 0) # release
	pushSeqCmd(dt, 'PLT_MPD_L_T1', 1) # CHAFF (to ARM)
	pushSeqCmd(dt, 'PLT_MPD_L_T1', 0) # release
	# ASE AUTOPAGE - ACQUISITION (only switches to ASE when being acquired/locked up)
	pushSeqCmd(dt, 'PLT_MPD_L_R1', 1) # AUTOPAGE
	pushSeqCmd(dt, 'PLT_MPD_L_R1', 0) # release
	pushSeqCmd(dt, 'PLT_MPD_L_R2', 1) # ACQUISITION
	pushSeqCmd(dt, 'PLT_MPD_L_R1', 0) # release

	# RLWR - ON
	pushSeqCmd(dt, 'PLT_MPD_L_B1', 1) # MENU
	pushSeqCmd(dt, 'PLT_MPD_L_B1', 0) # release
	pushSeqCmd(dt, 'PLT_MPD_L_L3', 1) # ASE
	pushSeqCmd(dt, 'PLT_MPD_L_L3', 0) # release
	pushSeqCmd(dt, 'PLT_MPD_L_T6', 1) # UTIL
	pushSeqCmd(dt, 'PLT_MPD_L_T6', 0) # release
	pushSeqCmd(dt, 'PLT_MPD_L_R4', 1) # RLWR
	pushSeqCmd(dt, 'PLT_MPD_L_R4', 0) # release

	# SAI - FIXME May need changes to DCS BIOS command definitions...
	# Standby Attitude Indicator - Uncage and center
	#pushSeqCmd(dt, device = devices.SAI, action = sai_commands.CageKnobRotate_ITER, value = -1.8) # Turn left to unlock, note "CageKnobRotate" does not seem to work, only "CageKnobRotate_ITER" and "CageKnobRotate_AXIS"
	pushSeqCmd(dt, 'PLT_SAI_CAGE', 0) # fixme Turn left to unlock, note "CageKnobRotate" does not seem to work, only "CageKnobRotate_ITER" and "CageKnobRotate_AXIS"
	#pushSeqCmd(dt, device = devices.SAI, action = sai_commands.CageKnobPull, 0) # Press knob in to uncage
	pushSeqCmd(dt, 'PLT_SAI_PITCH_TRIM', int16(0.6)) # Center SAI

	# Starting engines - PILOT
	# Starting engines (1m25s)
	# POWER levers - OFF
	pushSeqCmd(dt, 'PLT_ENG_L_PW_LVR', 0)
	pushSeqCmd(dt, 'PLT_ENG_R_PW_LVR', 0)
	#FIXME This may not be needed, and takes 14 seconds to do, so commenting out for now.  Just make sure your collective is fully down.
	# Collective - Flat pitch
	#pushSeqCmd(dt, 'scriptKeyboard', '{- down}')
	#pushSeqCmd(14, 'scriptKebyoard','{- up}') # Hold down for 14 seconds to ensure all the way down.

	# Go to ENG page
	pushSeqCmd(dt, 'PLT_MPD_L_AC', 1) # A/C (goes directly to ENG page)
	pushSeqCmd(dt, 'PLT_MPD_L_AC', 0) # release

	# Start first engine (30s)
	pushSeqCmd(dt, 'PLT_ENG1_START', 2)
	pushSeqCmd(dt, 'PLT_ENG1_START', 1)
	pushSeqCmd(2, 'scriptKeyboard', '{VK_LMENU down}{HOME down}{HOME up}{VK_LMENU up}') # NOTE Must remap Power Lever (Left) - IDLE to LAlt-Home.
	pushSeqCmd(engine1StartTime, '','', "Engine 1 started")
	
	# Start second engine (40s)
	pushSeqCmd(dt, 'PLT_ENG2_START', 2)
	pushSeqCmd(dt, 'PLT_ENG2_START', 1)
	pushSeqCmd(2, 'scriptKeyboard', '{VK_RSHIFT down}{HOME down}{HOME up}{VK_RSHIFT up}')
	pushSeqCmd(engine2StartTime, '','', "Engine 2 started")
	
	# POWER levers - Smoothly to FLY
	powerLeverStart = int16(0.25) # Power levers start at 25% - IDLE.
	powerLeverEnd = int16(0.9) # Power levers end at 90% - FLY.
	powerLeverTime = 11 # Number of seconds to advance the power levers.  9 seconds is minimum to avoid "Rotor RPM Low" warning, ISA at sea level.  Default autostart is about 11 seconds.
	powerLeverDt = dt # Time between power lever steps.  If this is too fast, it could possibly lag or something on MP servers.
	powerLeverSteps = int((powerLeverTime / powerLeverDt) / 2) # Divide by 2 here because there are two power levers that need to be advanced.
	powerLeverIncrement = (powerLeverEnd - powerLeverStart) / powerLeverSteps # Increment (step size) is the total amount we need to go divided by the number of steps we're doing to get there.
	powerLeverPosition = powerLeverStart # Power lever starts at start position.
	for i in range(powerLeverSteps):
		powerLeverPosition += int(powerLeverIncrement) # Add the step size to the lever position to make the next lever position.
		pushSeqCmd(powerLeverDt, 'PLT_ENG_L_PW_LVR', powerLeverPosition) # Lever position is absolute.
		pushSeqCmd(powerLeverDt, 'PLT_ENG_R_PW_LVR', powerLeverPosition) # Lever position is absolute.

	pushSeqCmd(7, '', '', "Np and Nr - Verify 101%")
	# APU - OFF
	pushSeqCmd(dt, 'PLT_APU_BTN', 1) # Press
	pushSeqCmd(dt, 'PLT_APU_BTN', 0) # Release
	pushSeqCmd(dt, 'PLT_APU_BTN_CVR', 0) # Cover close
	# Engine start complete

	# After engine start
	# AUX fuel tank - ON (does nothing if AUX tank is not installed)
	pushSeqCmd(dt, 'PLT_MPD_L_AC', 1) # A/C (goes directly to ENG page)
	pushSeqCmd(dt, 'PLT_MPD_L_AC', 0) # release
	pushSeqCmd(dt, 'PLT_MPD_L_T3', 1) # FUEL
	pushSeqCmd(dt, 'PLT_MPD_L_T3', 0) # release
	pushSeqCmd(dt, 'PLT_MPD_L_L2', 1) # C AUX
	pushSeqCmd(dt, 'PLT_MPD_L_L2', 0) # release

	# WCA (Warning/Caution/Advisory) - RESET
	pushSeqCmd(dt, 'PLT_MPD_L_B1', 1) # MENU
	pushSeqCmd(dt, 'PLT_MPD_L_B1', 0) # release
	pushSeqCmd(dt, 'PLT_MPD_L_B1', 1) # DMS
	pushSeqCmd(dt, 'PLT_MPD_L_B1', 0) # release
	pushSeqCmd(dt, 'PLT_MPD_L_B6', 1) # WCA
	pushSeqCmd(dt, 'PLT_MPD_L_B6', 0) # release
	pushSeqCmd(dt, 'PLT_MPD_L_B4', 1) # RESET
	pushSeqCmd(dt, 'PLT_MPD_L_B4', 0) # release

	# PLT ACQ to TADS
	pushSeqCmd(dt, 'PLT_MPD_R_TSD', 1) # TSD
	pushSeqCmd(dt, 'PLT_MPD_R_TSD', 0) # release
	pushSeqCmd(dt, 'PLT_MPD_R_R6', 1) # ACQ
	pushSeqCmd(dt, 'PLT_MPD_R_R6', 0) # release
	pushSeqCmd(dt, 'PLT_MPD_R_B6', 1) # TADS
	pushSeqCmd(dt, 'PLT_MPD_R_B6', 0) # release
	
	# CPG ACQ to TADS
	pushSeqCmd(dt, 'CPG_MPD_R_TSD', 1) # TSD
	pushSeqCmd(dt, 'CPG_MPD_R_TSD', 0) # release
	pushSeqCmd(dt, 'CPG_MPD_R_R6', 1) # ACQ
	pushSeqCmd(dt, 'CPG_MPD_R_R6', 0) # release
	pushSeqCmd(dt, 'CPG_MPD_R_B6', 1) # TADS
	pushSeqCmd(dt, 'CPG_MPD_R_B6', 0) # release
	
	# PLT Weapon MAN RNG to 800 m (a more useful default)
	pushSeqCmd(dt, 'PLT_MPD_R_WPN', 1) # WPN
	pushSeqCmd(dt, 'PLT_MPD_R_WPN', 0) # release
	pushSeqCmd(dt, 'PLT_MPD_R_B6', 1) # MAN RNG>
	pushSeqCmd(dt, 'PLT_MPD_R_B6', 0) # release
	pushSeqCmd(dt, 'PLT_KU_8', 1) # KU key press
	pushSeqCmd(dt, 'PLT_KU_8', 0) # release
	pushSeqCmd(dt, 'PLT_KU_0', 1) # KU key press
	pushSeqCmd(dt, 'PLT_KU_0', 0) # release
	pushSeqCmd(dt, 'PLT_KU_0', 1) # KU key press
	pushSeqCmd(dt, 'PLT_KU_0', 0) # release
	pushSeqCmd(dt, 'PLT_KU_ENT', 1) # KU key press
	pushSeqCmd(dt, 'PLT_KU_ENT', 0) # release
	# Return to TSD.
	pushSeqCmd(dt, 'PLT_MPD_R_TSD', 1) # TSD
	pushSeqCmd(dt, 'PLT_MPD_R_TSD', 0) # release
	
	# CPG Weapon MAN RNG to 800 m (a more useful default)
	pushSeqCmd(dt, 'CPG_MPD_L_WPN', 1) # WPN
	pushSeqCmd(dt, 'CPG_MPD_L_WPN', 0) # release
	pushSeqCmd(dt, 'CPG_MPD_L_B6', 1) # MAN RNG>
	pushSeqCmd(dt, 'CPG_MPD_L_B6', 0) # release
	pushSeqCmd(dt, 'CPG_KU_8', 1) # KU key press
	pushSeqCmd(dt, 'CPG_KU_8', 0) # release
	pushSeqCmd(dt, 'CPG_KU_0', 1) # KU key press
	pushSeqCmd(dt, 'CPG_KU_0', 0) # release
	pushSeqCmd(dt, 'CPG_KU_0', 1) # KU key press
	pushSeqCmd(dt, 'CPG_KU_0', 0) # release
	pushSeqCmd(dt, 'CPG_KU_ENT', 1) # KU key press
	pushSeqCmd(dt, 'CPG_KU_ENT', 0) # release
	# CPG LASER - ON (enable laser) (start from WPN page)
	pushSeqCmd(dt, 'CPG_MPD_L_T6', 1) # UTIL
	pushSeqCmd(dt, 'CPG_MPD_L_T6', 0) # release
	pushSeqCmd(dt, 'CPG_MPD_L_L6', 1) # LASER
	pushSeqCmd(dt, 'CPG_MPD_L_L6', 0) # release
	pushSeqCmd(dt, 'CPG_MPD_L_T6', 1) # UTIL
	pushSeqCmd(dt, 'CPG_MPD_L_T6', 0) # release
	# leaves CPG on WPN page on left MFD
	
	# CPG TADS sensor select - TV for daytime, FLIR for night
	if dayStart:
		pushSeqCmd(dt, 'CPG_LHG_TADS_SEL', 1) # 0 = DVO (not used), 1 = TV, 2 = FLIR (default)
	else:
		pushSeqCmd(dt, 'CPG_LHG_TADS_SEL', 2) # 0 = DVO (not used), 1 = TV, 2 = FLIR (default)

	# PLT Show TADS video on left MFD
	pushSeqCmd(dt, 'PLT_MPD_L_VID', 1) # VID
	pushSeqCmd(dt, 'PLT_MPD_L_VID', 0) # release
	pushSeqCmd(dt, 'PLT_MPD_L_R1', 1) # TADS
	pushSeqCmd(dt, 'PLT_MPD_L_R1', 0) # release
	pushSeqCmd(dt, 'PLT_MPD_L_T6', 1) # TADS
	pushSeqCmd(dt, 'PLT_MPD_L_T6', 0) # release
	pushSeqCmd(dt, 'PLT_MPD_L_L3', 1) # Z (zooms view)
	pushSeqCmd(dt, 'PLT_MPD_L_L3', 0) # release
	
	# PLT IHADSS - Boresight
	pushSeqCmd(dt, 'PLT_MPD_R_WPN', 1) # WPN
	pushSeqCmd(dt, 'PLT_MPD_R_WPN', 0) # release
	pushSeqCmd(dt, 'PLT_MPD_R_L5', 1) # BORESIGHT
	pushSeqCmd(dt, 'PLT_MPD_R_L5', 0) # release
	pushSeqCmd(dt, 'PLT_MPD_R_L4', 1) # IHADSS
	pushSeqCmd(dt, 'PLT_MPD_R_L4', 0) # release
	
	pushSeqCmd(dt, 'scriptSpeech', "Manual steps remaining while waiting for alignment: Bore sight IHADSS. Set Hellfire seeker and laser designator codes.  Tune radios.  Set baro altitude.")
	pushSeqCmd(dt, 'scriptSpeech', "Power on FCR if equipped, FCR page, util, MMA pinned, FCR bit override.")
	
	# Wait until the alignment is complete (total process time minus the difference between now and when the process started).
	alignTimerEnd = alignTime - (getLastSeqTime() - alignTimerStart)
	pushSeqCmd(alignTimerEnd, '', '', "Alignment complete.")
	
	return seq


def HotStartDay(config):
	return HotStart(config, dayStart = True)

def HotStartNight(config):
	return HotStart(config, dayStart = False)

###############################################################################
###############################################################################
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

	# Function to set all the PLT TSD SHOW options.
	def setPltTsdShowOptions():
		# PLT - TSD SHOW options - Set all ON (turn off as needed later)
		# Setting up NAV PHASE
		pushSeqCmd(dt, 'PLT_MPD_R_TSD', 1) # TSD
		pushSeqCmd(dt, 'PLT_MPD_R_TSD', 0) # release
		
		# NAV PHASE
		# SHOW page
		pushSeqCmd(dt, 'PLT_MPD_R_T3', 1) # SHOW
		pushSeqCmd(dt, 'PLT_MPD_R_T3', 0) # release
		pushSeqCmd(dt, 'PLT_MPD_R_L3', 1) # INACTIVE ZONES
		pushSeqCmd(dt, 'PLT_MPD_R_L3', 0) # release
		pushSeqCmd(dt, 'PLT_MPD_R_L5', 1) # CPG CURSOR
		pushSeqCmd(dt, 'PLT_MPD_R_L5', 0) # release
		pushSeqCmd(dt, 'PLT_MPD_R_L6', 1) # CURSOR INFO
		pushSeqCmd(dt, 'PLT_MPD_R_L6', 0) # release
		pushSeqCmd(dt, 'PLT_MPD_R_R4', 1) # HSI
		pushSeqCmd(dt, 'PLT_MPD_R_R4', 0) # release
		# THRT SHOW page
		pushSeqCmd(dt, 'PLT_MPD_R_T5', 1) # THRT SHOW
		pushSeqCmd(dt, 'PLT_MPD_R_T5', 0) # release
		pushSeqCmd(dt, 'PLT_MPD_R_R5', 1) # THREATS
		pushSeqCmd(dt, 'PLT_MPD_R_R5', 0) # release
		pushSeqCmd(dt, 'PLT_MPD_R_R6', 1) # TARGETS
		pushSeqCmd(dt, 'PLT_MPD_R_R6', 0) # release
		# COORD SHOW page
		pushSeqCmd(dt, 'PLT_MPD_R_T6', 1) # COORD SHOW
		pushSeqCmd(dt, 'PLT_MPD_R_T6', 0) # release
		pushSeqCmd(dt, 'PLT_MPD_R_L3', 1) # FRIENDLY UNITS
		pushSeqCmd(dt, 'PLT_MPD_R_L3', 0) # release
		pushSeqCmd(dt, 'PLT_MPD_R_L4', 1) # ENEMY UNITS
		pushSeqCmd(dt, 'PLT_MPD_R_L4', 0) # release
		pushSeqCmd(dt, 'PLT_MPD_R_L5', 1) # PLANNED TGTS/THREATS
		pushSeqCmd(dt, 'PLT_MPD_R_L5', 0) # release
		
		pushSeqCmd(dt, 'PLT_MPD_R_T6', 1) # COORD SHOW
		pushSeqCmd(dt, 'PLT_MPD_R_T6', 0) # release
		# now we're back to the TSD > SHOW page
		
		# ATK PHASE
		pushSeqCmd(dt, 'PLT_MPD_R_B2', 1) # PHASE (to ATK)
		pushSeqCmd(dt, 'PLT_MPD_R_B2', 0) # release
		# SHOW page
		pushSeqCmd(dt, 'PLT_MPD_R_L2', 1) # CURRENT ROUTE
		pushSeqCmd(dt, 'PLT_MPD_R_L2', 0) # release
		pushSeqCmd(dt, 'PLT_MPD_R_L6', 1) # CURSOR INFO
		pushSeqCmd(dt, 'PLT_MPD_R_L6', 0) # release
		pushSeqCmd(dt, 'PLT_MPD_R_R4', 1) # HSI
		pushSeqCmd(dt, 'PLT_MPD_R_R4', 0) # release
		# THRT SHOW (already set from the NAV phase)
		# no action needed
		# COORD SHOW
		pushSeqCmd(dt, 'PLT_MPD_R_T6', 1) # COORD SHOW
		pushSeqCmd(dt, 'PLT_MPD_R_T6', 0) # release
		pushSeqCmd(dt, 'PLT_MPD_R_L4', 1) # ENEMY UNITS
		pushSeqCmd(dt, 'PLT_MPD_R_L4', 0) # release
		
		pushSeqCmd(dt, 'PLT_MPD_R_T3', 1) # SHOW
		pushSeqCmd(dt, 'PLT_MPD_R_T3', 0) # release
		# End TSD SHOW options, should now be back on the main TSD page.


	# Function to set all the CPG TSD SHOW options.
	def setCpgTsdShowOptions():
		# CPG - TSD SHOW options - Set all ON (turn off as needed later)
		# Setting up NAV PHASE
		pushSeqCmd(dt, 'CPG_MPD_R_TSD', 1) # TSD
		pushSeqCmd(dt, 'CPG_MPD_R_TSD', 0) # release
		
		# NAV PHASE
		# SHOW page
		pushSeqCmd(dt, 'CPG_MPD_R_T3', 1) # SHOW
		pushSeqCmd(dt, 'CPG_MPD_R_T3', 0) # release
		pushSeqCmd(dt, 'CPG_MPD_R_L3', 1) # INACTIVE ZONES
		pushSeqCmd(dt, 'CPG_MPD_R_L3', 0) # release
		pushSeqCmd(dt, 'CPG_MPD_R_L5', 1) # CPG CURSOR
		pushSeqCmd(dt, 'CPG_MPD_R_L5', 0) # release
		pushSeqCmd(dt, 'CPG_MPD_R_L6', 1) # CURSOR INFO
		pushSeqCmd(dt, 'CPG_MPD_R_L6', 0) # release
		pushSeqCmd(dt, 'CPG_MPD_R_R4', 1) # HSI
		pushSeqCmd(dt, 'CPG_MPD_R_R4', 0) # release
		# THRT SHOW page
		pushSeqCmd(dt, 'CPG_MPD_R_T5', 1) # THRT SHOW
		pushSeqCmd(dt, 'CPG_MPD_R_T5', 0) # release
		pushSeqCmd(dt, 'CPG_MPD_R_R5', 1) # THREATS
		pushSeqCmd(dt, 'CPG_MPD_R_R5', 0) # release
		pushSeqCmd(dt, 'CPG_MPD_R_R6', 1) # TARGETS
		pushSeqCmd(dt, 'CPG_MPD_R_R6', 0) # release
		# COORD SHOW
		pushSeqCmd(dt, 'CPG_MPD_R_T6', 1) # COORD SHOW
		pushSeqCmd(dt, 'CPG_MPD_R_T6', 0) # release
		pushSeqCmd(dt, 'CPG_MPD_R_L3', 1) # FRIENDLY UNITS
		pushSeqCmd(dt, 'CPG_MPD_R_L3', 0) # release
		pushSeqCmd(dt, 'CPG_MPD_R_L4', 1) # ENEMY UNITS
		pushSeqCmd(dt, 'CPG_MPD_R_L4', 0) # release
		pushSeqCmd(dt, 'CPG_MPD_R_L5', 1) # PLANNED TGTS/THREATS
		pushSeqCmd(dt, 'CPG_MPD_R_L5', 0) # release
		
		pushSeqCmd(dt, 'CPG_MPD_R_T6', 1) # COORD SHOW
		pushSeqCmd(dt, 'CPG_MPD_R_T6', 0) # release
		# now we're back to the TSD > SHOW page
		
		# ATK PHASE
		pushSeqCmd(dt, 'CPG_MPD_R_B2', 1) # PHASE (to ATK)
		pushSeqCmd(dt, 'CPG_MPD_R_B2', 0) # release
		# SHOW page
		pushSeqCmd(dt, 'CPG_MPD_R_L2', 1) # CURRENT ROUTE
		pushSeqCmd(dt, 'CPG_MPD_R_L2', 0) # release
		pushSeqCmd(dt, 'CPG_MPD_R_L6', 1) # CURSOR INFO
		pushSeqCmd(dt, 'CPG_MPD_R_L6', 0) # release
		pushSeqCmd(dt, 'CPG_MPD_R_R4', 1) # HSI
		pushSeqCmd(dt, 'CPG_MPD_R_R4', 0) # release
		# THRT SHOW (already set from the NAV phase)
		# no action needed
		# COORD SHOW
		pushSeqCmd(dt, 'CPG_MPD_R_T6', 1) # COORD SHOW
		pushSeqCmd(dt, 'CPG_MPD_R_T6', 0) # release
		pushSeqCmd(dt, 'CPG_MPD_R_L4', 1) # ENEMY UNITS
		pushSeqCmd(dt, 'CPG_MPD_R_L4', 0) # release
		
		pushSeqCmd(dt, 'CPG_MPD_R_T3', 1) # SHOW
		pushSeqCmd(dt, 'CPG_MPD_R_T3', 0) # release
		# End TSD SHOW options, should now be back on the main TSD page.

	# Start sequence
	pushSeqCmd(0, '', '', "Running Hot Start sequence")
	
	# POWER levers - Smoothly to FLY
	powerLeverStart = int16(0.25) # Power levers start at 25% - IDLE.
	powerLeverEnd = int16(0.9) # Power levers end at 90% - FLY.
	powerLeverTime = 11 # Number of seconds to advance the power levers.  9 seconds is minimum to avoid "Rotor RPM Low" warning, ISA at sea level.  Default autostart is about 11 seconds.
	powerLeverDt = dt # Time between power lever steps.  If this is too fast, it could possibly lag or something on MP servers.
	powerLeverSteps = int((powerLeverTime / powerLeverDt) / 2) # Divide by 2 here because there are two power levers that need to be advanced.
	powerLeverIncrement = (powerLeverEnd - powerLeverStart) / powerLeverSteps # Increment (step size) is the total amount we need to go divided by the number of steps we're doing to get there.
	powerLeverPosition = powerLeverStart # Power lever starts at start position.
	for i in range(powerLeverSteps):
		powerLeverPosition += int(powerLeverIncrement) # Add the step size to the lever position to make the next lever position.
		pushSeqCmd(powerLeverDt, 'PLT_ENG_L_PW_LVR', powerLeverPosition) # Lever position is absolute.
		pushSeqCmd(powerLeverDt, 'PLT_ENG_R_PW_LVR', powerLeverPosition) # Lever position is absolute.

	# Lights
	if dayStart:
		# PLT Internal Lights
		pushSeqCmd(dt, 'PLT_INTL_SIGNAL_L_KNB', int16())
		pushSeqCmd(dt, 'PLT_INTL_PRIMARY_L_KNB', int16())
		pushSeqCmd(dt, 'PLT_INTL_STBYINST_L_KNB', int16())
		pushSeqCmd(dt, 'PLT_INTL_FLOOD_L_KNB', 0)
		# PLT External lights
		pushSeqCmd(dt, 'PLT_EXTL_NAV_L_SW', 1) # 0 = DIM, 1 = OFF, 2 = BRT
		pushSeqCmd(dt, 'PLT_EXTL_FROMATION_L_KNOB', 0) # NOTE misspelling, 0 = off, int16 = full on
		pushSeqCmd(dt, 'PLT_EXTL_ACOL_L_SW', 1) # 0 = RED, 1 = OFF, 2 = WHT
		# PLT CMWS
		pushSeqCmd(dt, 'PLT_CMWS_LAMP', int16())
		# PLT IHADSS symbology brightness
		pushSeqCmd(dt, 'PLT_VIDEO_SYM_BRT', int16())
		# PLT MPDs
		pushSeqCmd(dt, 'PLT_MPD_R_VIDEO', int16(0.25)) # Makes the TSD page easier to read.

		# CPG Internal Lights
		pushSeqCmd(dt, 'CPG_INTL_SIGNAL_L_KNB', int16())
		pushSeqCmd(dt, 'CPG_INTL_PRIMARY_L_KNB', int16())
		pushSeqCmd(dt, 'CPG_INTL_STBYINST_L_KNB', int16())
		pushSeqCmd(dt, 'CPG_INTL_FLOOD_L_KNB', 0)
		# CPG MPDs
		pushSeqCmd(dt, 'CPG_MPD_R_VIDEO', int16(0.25)) # Makes the TSD page easier to read.

	else:
		# PLT Internal Lights
		pushSeqCmd(dt, 'PLT_INTL_SIGNAL_L_KNB', int16(0.5))
		pushSeqCmd(dt, 'PLT_INTL_PRIMARY_L_KNB', int16(0.5))
		pushSeqCmd(dt, 'PLT_INTL_STBYINST_L_KNB', int16(0.5))
		pushSeqCmd(dt, 'PLT_INTL_FLOOD_L_KNB', 0)
		# PLT External lights
		pushSeqCmd(dt, 'PLT_EXTL_NAV_L_SW', 1) # 0 = DIM, 1 = OFF, 2 = BRT
		pushSeqCmd(dt, 'PLT_EXTL_FROMATION_L_KNOB', 0) # NOTE misspelling, 0 = off, int16 = full on
		pushSeqCmd(dt, 'PLT_EXTL_ACOL_L_SW', 1) # 0 = RED, 1 = OFF, 2 = WHT
		# PLT MPDs
		pushSeqCmd(dt, 'PLT_MPD_L_MODE', 1) # 0 = MONO, 1 = NT, 2 = DAY
		pushSeqCmd(dt, 'PLT_MPD_L_BRT', int16(0.5))
		pushSeqCmd(dt, 'PLT_MPD_L_VIDEO', int16(0.25))
		pushSeqCmd(dt, 'PLT_MPD_R_MODE', 1) # 0 = MONO, 1 = NT, 2 = DAY
		pushSeqCmd(dt, 'PLT_MPD_R_BRT', int16(0.5))
		pushSeqCmd(dt, 'PLT_MPD_R_VIDEO', int16(0.25))
		# PLT UFC
		pushSeqCmd(dt, 'PLT_EUFD_BRT', int16(0.25))
		# PLT KU
		pushSeqCmd(dt, 'PLT_KU_BRT', int16(0.33))
		# PLT CMWS
		pushSeqCmd(dt, 'PLT_CMWS_LAMP', int16(0.25))
		# PLT FLIR Level (IHADSS FLIR brightness)
		pushSeqCmd(dt, 'PLT_VIDEO_FLIR_LVL', int16(0.4))

		# CPG Internal Lights
		pushSeqCmd(dt, 'CPG_INTL_SIGNAL_L_KNB', int16(0.5))
		pushSeqCmd(dt, 'CPG_INTL_PRIMARY_L_KNB', int16(0.5))
		pushSeqCmd(dt, 'CPG_INTL_STBYINST_L_KNB', int16(0.5))
		pushSeqCmd(dt, 'CPG_INTL_FLOOD_L_KNB', 0)
		# CPG MPDs
		pushSeqCmd(dt, 'CPG_MPD_L_MODE', 1) # 0 = MONO, 1 = NT, 2 = DAY
		pushSeqCmd(dt, 'CPG_MPD_L_BRT', int16(0.5))
		pushSeqCmd(dt, 'CPG_MPD_L_VIDEO', int16(0.25))
		pushSeqCmd(dt, 'CPG_MPD_R_MODE', 1) # 0 = MONO, 1 = NT, 2 = DAY
		pushSeqCmd(dt, 'CPG_MPD_R_BRT', int16(0.5))
		pushSeqCmd(dt, 'CPG_MPD_R_VIDEO', int16(0.25))
		# CPG UFC
		pushSeqCmd(dt, 'CPG_EUFD_BRT', int16(0.25))
		# CPG KU
		pushSeqCmd(dt, 'CPG_KU_BRT', int16(0.33))
		# CPG FLIR Level (IHADSS FLIR brightness)
		pushSeqCmd(dt, 'CPG_VIDEO_FLIR_LVL', int16(0.4))

	# Radio volumes and squelch
	# PLT Radio RLWR volume - 75%
	pushSeqCmd(dt, 'PLT_COM_RLWR_VOL', int16(0.75))
	# CPG Radio RLWR volume - 75%
	pushSeqCmd(dt, 'CPG_COM_RLWR_VOL', int16(0.75))
	
	# TEDAC
	if dayStart:
		pushSeqCmd(dt, 'CPG_TEDAC_DISP_MODE', 2) # 0 = OFF, 1 = NT, 2 = DAY
	else:
		pushSeqCmd(dt, 'CPG_TEDAC_DISP_MODE', 1) # 0 = OFF, 1 = NT, 2 = DAY
	
	# Use local time
	pushSeqCmd(dt, 'PLT_MPD_R_TSD', 1) # TSD
	pushSeqCmd(dt, 'PLT_MPD_R_TSD', 0) # release
	pushSeqCmd(dt, 'PLT_MPD_R_T6', 1) # UTIL
	pushSeqCmd(dt, 'PLT_MPD_R_T6', 0) # release
	pushSeqCmd(dt, 'PLT_MPD_R_R2', 1) # TIME
	pushSeqCmd(dt, 'PLT_MPD_R_R2', 0) # release
	pushSeqCmd(dt, 'PLT_MPD_R_T6', 1) # UTIL
	pushSeqCmd(dt, 'PLT_MPD_R_T6', 0) # release

	# TSD SHOW options
	setPltTsdShowOptions()
	setCpgTsdShowOptions()

	# CMWS
	# CMWS PWR knob - ON
	pushSeqCmd(dt, 'PLT_CMWS_PW', 1)
	# CMWS ARM/SAFE switch - ARM
	pushSeqCmd(dt, 'PLT_CMWS_ARM', 1)
	# CMWS CMWS/NAV switch - CMWS
	pushSeqCmd(dt, 'PLT_CMWS_MODE', 1)
	# CMWS BYPASS/AUTO switch - BYPASS
	pushSeqCmd(dt, 'PLT_CMWS_BYPASS', 1)

	# GND ORIDE - ON (needed to arm chaff)
	pushSeqCmd(dt, 'PLT_GROUND_OVERRIDE_BTN', 1) # Press
	pushSeqCmd(dt, 'PLT_GROUND_OVERRIDE_BTN', 0) # Release

	# MASTER ARM - ON
	pushSeqCmd(dt, 'PLT_MASTER_ARM_BTN', 1) # press
	pushSeqCmd(dt, 'PLT_MASTER_ARM_BTN', 0) # release

	# ASE CHAFF - ARM
	pushSeqCmd(dt, 'PLT_MPD_L_B1', 1) # MENU
	pushSeqCmd(dt, 'PLT_MPD_L_B1', 0) # release
	pushSeqCmd(dt, 'PLT_MPD_L_L3', 1) # ASE
	pushSeqCmd(dt, 'PLT_MPD_L_L3', 0) # release
	pushSeqCmd(dt, 'PLT_MPD_L_T1', 1) # CHAFF (to ARM)
	pushSeqCmd(dt, 'PLT_MPD_L_T1', 0) # release
	# ASE AUTOPAGE - ACQUISITION
	pushSeqCmd(dt, 'PLT_MPD_L_R1', 1) # AUTOPAGE
	pushSeqCmd(dt, 'PLT_MPD_L_R1', 0) # release
	pushSeqCmd(dt, 'PLT_MPD_L_R2', 1) # ACQUISITION
	pushSeqCmd(dt, 'PLT_MPD_L_R1', 0) # release
	
	# AUX fuel tank - ON (does nothing if AUX tank is not installed)
	pushSeqCmd(dt, 'PLT_MPD_L_AC', 1) # A/C (goes directly to ENG page)
	pushSeqCmd(dt, 'PLT_MPD_L_AC', 0) # release
	pushSeqCmd(dt, 'PLT_MPD_L_T3', 1) # FUEL
	pushSeqCmd(dt, 'PLT_MPD_L_T3', 0) # release
	pushSeqCmd(dt, 'PLT_MPD_L_L2', 1) # C AUX
	pushSeqCmd(dt, 'PLT_MPD_L_L2', 0) # release

	# CPG ACQ to TADS
	pushSeqCmd(dt, 'CPG_MPD_R_TSD', 1) # TSD
	pushSeqCmd(dt, 'CPG_MPD_R_TSD', 0) # release
	pushSeqCmd(dt, 'CPG_MPD_R_R6', 1) # ACQ
	pushSeqCmd(dt, 'CPG_MPD_R_R6', 0) # release
	pushSeqCmd(dt, 'CPG_MPD_R_B6', 1) # TADS
	pushSeqCmd(dt, 'CPG_MPD_R_B6', 0) # release
	
	# PLT Weapon MAN RNG to 800 m (a more useful default)
	pushSeqCmd(dt, 'PLT_MPD_R_WPN', 1) # WPN
	pushSeqCmd(dt, 'PLT_MPD_R_WPN', 0) # release
	pushSeqCmd(dt, 'PLT_MPD_R_B6', 1) # MAN RNG>
	pushSeqCmd(dt, 'PLT_MPD_R_B6', 0) # release
	pushSeqCmd(dt, 'PLT_KU_8', 1) # KU key press
	pushSeqCmd(dt, 'PLT_KU_8', 0) # release
	pushSeqCmd(dt, 'PLT_KU_0', 1) # KU key press
	pushSeqCmd(dt, 'PLT_KU_0', 0) # release
	pushSeqCmd(dt, 'PLT_KU_0', 1) # KU key press
	pushSeqCmd(dt, 'PLT_KU_0', 0) # release
	pushSeqCmd(dt, 'PLT_KU_ENT', 1) # KU key press
	pushSeqCmd(dt, 'PLT_KU_ENT', 0) # release
	# Return to TSD.
	pushSeqCmd(dt, 'PLT_MPD_R_TSD', 1) # TSD
	pushSeqCmd(dt, 'PLT_MPD_R_TSD', 0) # release
	
	# CPG Weapon MAN RNG to 800 m (a more useful default)
	pushSeqCmd(dt, 'CPG_MPD_L_WPN', 1) # WPN
	pushSeqCmd(dt, 'CPG_MPD_L_WPN', 0) # release
	pushSeqCmd(dt, 'CPG_MPD_L_B6', 1) # MAN RNG>
	pushSeqCmd(dt, 'CPG_MPD_L_B6', 0) # release
	pushSeqCmd(dt, 'CPG_KU_8', 1) # KU key press
	pushSeqCmd(dt, 'CPG_KU_8', 0) # release
	pushSeqCmd(dt, 'CPG_KU_0', 1) # KU key press
	pushSeqCmd(dt, 'CPG_KU_0', 0) # release
	pushSeqCmd(dt, 'CPG_KU_0', 1) # KU key press
	pushSeqCmd(dt, 'CPG_KU_0', 0) # release
	pushSeqCmd(dt, 'CPG_KU_ENT', 1) # KU key press
	pushSeqCmd(dt, 'CPG_KU_ENT', 0) # release

	# CPG Laser Tracker - OFF # FIXME This is a bug, it should start off, but currently starts on.  Should be fixed in DCS soon, at which point this command can be removed.
	pushSeqCmd(dt, 'CPG_RHG_LASER_TRACK', 1) # 0 = M (manual), 1 = O (off), 2 = A (automatic)

	# CPG TADS sensor select - TV for daytime, FLIR for night
	if dayStart:
		pushSeqCmd(dt, 'CPG_LHG_TADS_SEL', 1) # 0 = DVO (not used), 1 = TV, 2 = FLIR (default)
	else:
		pushSeqCmd(dt, 'CPG_LHG_TADS_SEL', 2) # 0 = DVO (not used), 1 = TV, 2 = FLIR (default)

	# PLT Show TADS video on left MFD
	pushSeqCmd(dt, 'PLT_MPD_L_VID', 1) # VID
	pushSeqCmd(dt, 'PLT_MPD_L_VID', 0) # release
	pushSeqCmd(dt, 'PLT_MPD_L_R1', 1) # TADS
	pushSeqCmd(dt, 'PLT_MPD_L_R1', 0) # release
	pushSeqCmd(dt, 'PLT_MPD_L_T6', 1) # TADS
	pushSeqCmd(dt, 'PLT_MPD_L_T6', 0) # release
	pushSeqCmd(dt, 'PLT_MPD_L_L3', 1) # Z (zooms view)
	pushSeqCmd(dt, 'PLT_MPD_L_L3', 0) # release
	
	pushSeqCmd(dt, 'scriptSpeech', "Manual steps remaining: Set Hellfire seeker and laser designator codes.  Tune radios.")
	pushSeqCmd(dt, 'scriptSpeech', "Power on FCR if equipped, FCR page, util, MMA pinned, FCR bit override.")
	
	return seq


###############################################################################
###############################################################################
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

	# Start sequence
	pushSeqCmd(0, '', '', "Running Shutdown sequence")
	#pushSeqCmd(dt, 'scriptSpeech', "Warning, uses non standard key bindings.")
	#pushSeqCmd(dt, 'scriptSpeech', 'Set collective full down.')
	
	# Parking Brake - SET
	pushSeqCmd(dt, 'PLT_PARK_BRAKE', 1)
	
	# Start APU to provide power during shutdown sequence.
	# Starting APU - PILOT
	# Starting APU (20s)
	pushSeqCmd(dt, 'PLT_APU_BTN_CVR', 1) # Cover open
	pushSeqCmd(dt, 'PLT_APU_BTN', 1) # Press
	pushSeqCmd(dt, 'PLT_APU_BTN', 0) # Release
	pushSeqCmd(20, '', '', 'APU started')
	
	# POWER levers - IDLE
	pushSeqCmd(dt, 'PLT_ENG_L_PW_LVR', 0.25)
	pushSeqCmd(dt, 'PLT_ENG_R_PW_LVR', 0.25)
	pushSeqCmd(15, '', '', 'Wait 15 seconds for engines to spool down.')

	# Left engine OFF
	pushSeqCmd(dt, 'scriptKeyboard', '{VK_LMENU down}{END down}{END up}{VK_LMENU up}') # NOTE Must remap Power Lever (Left) - OFF to LAlt-End.
	
	# Right engine OFF
	pushSeqCmd(dt, 'scriptKeyboard', '{VK_RSHIFT down}{END down}{END up}{VK_RSHIFT up}')
	
	# Lights
	# PLT Internal Lights
	pushSeqCmd(dt, 'PLT_INTL_SIGNAL_L_KNB', 0)
	pushSeqCmd(dt, 'PLT_INTL_PRIMARY_L_KNB', 0)
	pushSeqCmd(dt, 'PLT_INTL_STBYINST_L_KNB', 0)
	pushSeqCmd(dt, 'PLT_INTL_FLOOD_L_KNB', 0)
	# PLT External lights
	pushSeqCmd(dt, 'PLT_EXTL_NAV_L_SW', 1) # 0 = DIM, 1 = OFF, 2 = BRT
	pushSeqCmd(dt, 'PLT_EXTL_FROMATION_L_KNOB', 0) # NOTE misspelling, 0 = off, int16 = full on
	pushSeqCmd(dt, 'PLT_EXTL_ACOL_L_SW', 1) # 0 = RED, 1 = OFF, 2 = WHT
	# PLT MPDs
	pushSeqCmd(dt, 'PLT_MPD_L_MODE', 2) # 0 = MONO, 1 = NT, 2 = DAY
	pushSeqCmd(dt, 'PLT_MPD_L_BRT', int16())
	pushSeqCmd(dt, 'PLT_MPD_L_VIDEO', int16(0.5))
	pushSeqCmd(dt, 'PLT_MPD_R_MODE', 2) # 0 = MONO, 1 = NT, 2 = DAY
	pushSeqCmd(dt, 'PLT_MPD_R_BRT', int16())
	pushSeqCmd(dt, 'PLT_MPD_R_VIDEO', int16(0.5))
	# PLT UFC
	pushSeqCmd(dt, 'PLT_EUFD_BRT', int16())
	# PLT KU
	pushSeqCmd(dt, 'PLT_KU_BRT', int16())
	# PLT CMWS
	pushSeqCmd(dt, 'PLT_CMWS_LAMP', int16(1))
	# PLT FLIR Level (IHADSS FLIR brightness)
	pushSeqCmd(dt, 'PLT_VIDEO_FLIR_LVL', int16(0.75))

	# CPG Internal Lights
	pushSeqCmd(dt, 'CPG_INTL_SIGNAL_L_KNB', int16(0))
	pushSeqCmd(dt, 'CPG_INTL_PRIMARY_L_KNB', int16(0))
	pushSeqCmd(dt, 'CPG_INTL_STBYINST_L_KNB', int16(0))
	pushSeqCmd(dt, 'CPG_INTL_FLOOD_L_KNB', 0)
	# CPG MPDs
	pushSeqCmd(dt, 'CPG_MPD_L_MODE', 2) # 0 = MONO, 1 = NT, 2 = DAY
	pushSeqCmd(dt, 'CPG_MPD_L_BRT', int16())
	pushSeqCmd(dt, 'CPG_MPD_L_VIDEO', int16(0.5))
	pushSeqCmd(dt, 'CPG_MPD_R_MODE', 2) # 0 = MONO, 1 = NT, 2 = DAY
	pushSeqCmd(dt, 'CPG_MPD_R_BRT', int16())
	pushSeqCmd(dt, 'CPG_MPD_R_VIDEO', int16(0.5))
	# CPG UFC
	pushSeqCmd(dt, 'CPG_EUFD_BRT', int16())
	# CPG KU
	pushSeqCmd(dt, 'CPG_KU_BRT', int16())
	# CPG FLIR Level (IHADSS FLIR brightness)
	pushSeqCmd(dt, 'CPG_VIDEO_FLIR_LVL', int16(0.75))
		
	# TEDAC
	pushSeqCmd(dt, 'CPG_TEDAC_DISP_MODE', 0) # 0 = OFF, 1 = NT, 2 = DAY
	
	# CMWS
	# CMWS PWR knob - OFF
	pushSeqCmd(dt, 'PLT_CMWS_PW', 0)
	# CMWS ARM/SAFE switch - SAFE
	pushSeqCmd(dt, 'PLT_CMWS_ARM', 0)
	# CMWS CMWS/NAV switch - NAV
	pushSeqCmd(dt, 'PLT_CMWS_MODE', 0)
	# CMWS BYPASS/AUTO switch - AUTO
	pushSeqCmd(dt, 'PLT_CMWS_BYPASS', 0)

	# APU - OFF
	pushSeqCmd(dt, 'PLT_APU_BTN', 1) # Press
	pushSeqCmd(dt, 'PLT_APU_BTN', 0) # Release
	pushSeqCmd(dt, 'PLT_APU_BTN_CVR', 0) # Cover close

	# MSTR IGN switch - OFF
	pushSeqCmd(dt, 'PLT_MASTER_IGN_SW', 0)

	# RTR BRK switch - ON
	pushSeqCmd(dt, 'PLT_ROTOR_BRK', 1)

	# Canopy Door - Open
	pushSeqCmd(dt, 'CPG_CANOPY', 1)
	pushSeqCmd(dt, 'PLT_CANOPY', 1)

	return seq
