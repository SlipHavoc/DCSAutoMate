# Return a Dictionary of script data.  The 'scripts' key is a list of scripts that users will be selecting from.  Each script has an associated 'function', which is the name of the function in this file that will be called to generate the command sequence, and a dictionary of 'vars' that the user will be prompted to choose from before running the script, and will be passed into the sequence generating function.
def getScriptData():
	return {
		'moduleName': 'OH58D',
		'scripts': [
			{
				'name': 'Cold Start',
				'function': 'ColdStart',
				'vars': {},
			},
			{
				'name': 'Hot Start',
				'function': 'HotStart',
				'vars': {},
			},
			{
				'name': 'Shutdown',
				'function': 'Shutdown',
				'vars': {},
			},
			#{
			#	'name': 'Test',
			#	'function': 'Test',
			#	'vars': {},
			#},
		],
	}

def getInfo():
	return """ATTENTION: You must map "Throttle - Closed" to End, "Throttle - Idle" to Home, "Throttle - INCREASE" to Numpad+, and "Throttle - DECREASE" to Numpad-.  Otherwise there is no way for DCS-BIOS to interact with the throttle controls."""

def Test(config, vars, helper, *args, **kwargs):
	seq = []
	dt = 0.3

	pushSeqCmd = helper.makePushSeqCmd(seq)

	pushSeqCmd(0, '', '', "Running Test sequence")
	# Test code here...



	return seq

def ColdStart(config, vars, helper, *args, **kwargs):
	seq = []
	dt = 0.3

	pushSeqCmd = helper.makePushSeqCmd(seq)

	engineStartTime = 50 # Engine takes 50 seconds to start.
	alignmentTime = 2 * 60 + 30 # Alignment time is 2m30s from BATT 1 ON.

	# Start sequence
	pushSeqCmd(0, '', '', "Running Cold Start sequence.")
	pushSeqCmd(dt, 'scriptSpeech', "Warning, uses non standard key bindings.")
	pushSeqCmd(dt, 'scriptSpeech', 'Set collective full down.')

	# Ignition key ... On (rotated, not fore/aft) (center console under collective handle)
	pushSeqCmd(dt, 'ELECTRIC.HLP_MAIN_KEY', 1)

	# BATT 1 switch ... On (forward) (overhead forward panel)
	pushSeqCmd(dt, 'ELECTRIC.HLP_BATT1', 2) # 0 = Preheat (momentary), 1 = OFF, 2 = ON
	pushSeqCmd(4, '', '', 'Wait for the power to come on.')
	pushSeqCmd(dt, 'scriptTimerStart', name='alignTimer', duration=alignmentTime)

	# IGN and FADEC switches ... On (forward) (overhead forward panel)
	pushSeqCmd(dt, 'ELECTRIC.HLP_IGN', 1)
	pushSeqCmd(dt, 'ELECTRIC.HLP_FADEC', 1)

	# Throttle ... Idle position (collective grip) (mapped to Home key)
	pushSeqCmd(dt, 'FUEL.Button_5', 1) # Throttle - Idle
	pushSeqCmd(dt, 'FUEL.Button_5', 0)

	# Audio warning tone ... cancel with ACK switch (down) (center console top center)
	pushSeqCmd(dt, 'MFK.HLP_MFK_REC_ACK', 0) # ACK
	pushSeqCmd(dt, 'MFK.HLP_MFK_REC_ACK', 1) # Off (center)
	pushSeqCmd(dt, 'MFK.HLP_MFK_REC_ACK', 0) # ACK
	pushSeqCmd(dt, 'MFK.HLP_MFK_REC_ACK', 1) # Off (center)
	pushSeqCmd(dt, 'MFK.HLP_MFK_REC_ACK', 0) # ACK
	pushSeqCmd(dt, 'MFK.HLP_MFK_REC_ACK', 1) # Off (center)

	# START switch ... ON and hold for a few seconds until engine begins spooling up (collective head)
	pushSeqCmd(dt, 'ELECTRIC.HLP_START_SWITCH', 1)
	pushSeqCmd(4, 'ELECTRIC.HLP_START_SWITCH', 0)

	pushSeqCmd(dt, 'scriptTimerStart', name='engineTimer', duration=engineStartTime)

	# Cancel warning tone.
	pushSeqCmd(7, 'MFK.HLP_MFK_REC_ACK', 0) # ACK
	pushSeqCmd(dt, 'MFK.HLP_MFK_REC_ACK', 1) # Off (center)
	pushSeqCmd(dt, 'MFK.HLP_MFK_REC_ACK', 0) # ACK
	pushSeqCmd(dt, 'MFK.HLP_MFK_REC_ACK', 1) # Off (center)

	# Cancel warning tone.
	pushSeqCmd(14, 'MFK.HLP_MFK_REC_ACK', 0) # ACK
	pushSeqCmd(dt, 'MFK.HLP_MFK_REC_ACK', 1) # Off (center)
	pushSeqCmd(dt, 'MFK.HLP_MFK_REC_ACK', 0) # ACK
	pushSeqCmd(dt, 'MFK.HLP_MFK_REC_ACK', 1) # Off (center)

	# Wait until the engine is started (total process time minus the difference between now and when the process started).
	pushSeqCmd(dt, 'scriptTimerEnd', name='engineTimer')
	pushSeqCmd(dt, '', '', "Engine started.")

	# DC GEN, AC GEN, and RUN ESNTL BUS switches ... On (forward) (overhead forward panel)
	pushSeqCmd(dt, 'ELECTRIC.HLP_DC_GEN', 2) # 0 = RESET, 1 = OFF, 2 = ON
	pushSeqCmd(dt, 'ELECTRIC.HLP_AC_GEN', 1)
	pushSeqCmd(dt, 'ELECTRIC.HLP_ESSENTIAL_BUS', 1)

	# FUEL BOOST switch ... On (forward) (overhead forward panel)
	pushSeqCmd(dt, 'ELECTRIC.HLP_FUELBOOST', 1)

	# All circuit breakers and switches on rear vertical CB panel On or Pushed In:
	pushSeqCmd(dt, 'ELECTRIC.HLP_BFT', 1)
	pushSeqCmd(dt, 'ELECTRIC.HLP_IFF', 1)
	pushSeqCmd(dt, 'ELECTRIC.HLP_RADAR_DETR', 1)
	pushSeqCmd(dt, 'ELECTRIC.HLP_RADAR_WARN', 1)
	pushSeqCmd(dt, 'ELECTRIC.HLP_L2MUM', 0) # 0 = ON, 1 = OFF
	pushSeqCmd(dt, 'ELECTRIC.HLP_PART_SEP', 0) # 0 = IN, 1 = OUT

	# if CMWS is equipped, aircraft will have a CMWS switch over the pilot's head.
	pushSeqCmd(dt, 'ELECTRIC.HLP_CMWS_SWITCH', 1)

	# if IRCM is equipped, aircraft will have a IR JAMMER switch over the pilot's head.
	pushSeqCmd(dt, 'ELECTRIC.HLP_ALQ144_SWITCH01', 1)

	# Throttle ... set to Max
	pushSeqCmd(dt, 'FUEL.Button_6', 1) # Throttle - Full Open
	pushSeqCmd(dt, 'FUEL.Button_6', 0)

	# Clear warnings.
	pushSeqCmd(dt, 'MFK.HLP_MFK_REC_ACK', 0) # ACK
	pushSeqCmd(dt, 'MFK.HLP_MFK_REC_ACK', 1) # Off (center)
	pushSeqCmd(dt, 'MFK.HLP_MFK_REC_ACK', 0) # ACK
	pushSeqCmd(dt, 'MFK.HLP_MFK_REC_ACK', 1) # Off (center)

	# MPD (Multiparameter Display) ... Select switch +/- to NR (digital "chicklet" display, instrument panel center bottom, just above center console)
	pushSeqCmd(dt, 'MPD.HLP_MPD_SEL', 0) # 0 = down, 1 = center, 2 = up
	pushSeqCmd(dt, 'MPD.HLP_MPD_SEL', 1) # 0 = down, 1 = center, 2 = up

	# Incr/Decr ("Inker-Dinker") switch ... +/- as needed (right-click 2x) to set NR to 100 (collective head)
	pushSeqCmd(dt, 'ENGINE.HLP_PILOT_ENG_RPM_TRIM', 2) # 0 = down, 1 = center, 2 = up
	pushSeqCmd(dt, 'ENGINE.HLP_PILOT_ENG_RPM_TRIM', 1) # 0 = down, 1 = center, 2 = up
	pushSeqCmd(dt, 'ENGINE.HLP_PILOT_ENG_RPM_TRIM', 2) # 0 = down, 1 = center, 2 = up
	pushSeqCmd(dt, 'ENGINE.HLP_PILOT_ENG_RPM_TRIM', 1) # 0 = down, 1 = center, 2 = up
	# When at 100, NR "chicklet" light should be just one light resting on the 100 line.

	# Bring up NAV ALIGN page on Pilot MFD to monitor alignment.  Shows "GC ALIGN" at bottom of this screen while aligning.
	#pushSeqCmd(dt, 'RMFD.HLP_RMFD_L1', 1) # Press
	#pushSeqCmd(dt, 'RMFD.HLP_RMFD_L1', 1) # Release

	# MMS Mode knob ... PREPT or FWD (instrument panel lower left, above CPG left knee)
	pushSeqCmd(dt, 'MMS.HLP_MMS_MODE_ROTATOR', 1) # 0 = OFF, 1 = STOW, 2 = PREFLT, 3 = PREPT, 4 = FWD, 5 = SRCH
	pushSeqCmd(dt, 'MMS.HLP_MMS_MODE_ROTATOR', 2) # 0 = OFF, 1 = STOW, 2 = PREFLT, 3 = PREPT, 4 = FWD, 5 = SRCH
	pushSeqCmd(dt, 'MMS.HLP_MMS_MODE_ROTATOR', 3) # 0 = OFF, 1 = STOW, 2 = PREFLT, 3 = PREPT, 4 = FWD, 5 = SRCH
	pushSeqCmd(dt, 'MMS.HLP_MMS_MODE_ROTATOR', 4) # 0 = OFF, 1 = STOW, 2 = PREFLT, 3 = PREPT, 4 = FWD, 5 = SRCH

	# SCAS PWR switch, then PITCH/ROLL and YAW switches ... On (center console right)
	pushSeqCmd(dt, 'SCAS.HLP_SCAS_POWER_SWITCH', 1)
	pushSeqCmd(dt, 'SCAS.HLP_SCAS_PITCHROLL_SWITCH', 1)
	pushSeqCmd(dt, 'SCAS.HLP_SCAS_YAW_SWITCH', 1)

	# Alignment is shown in INITIAL PAGE > NAV ALIGN on MFD.  Should start aligning automatically when BATT 1 is turned on, takes about 4-4.5 mins.
	# When done, GC ALIGN at bottom of MFD screen goes away and "AUTO" on AUTO/MANUAL OSB gets unboxed.
	# To return to the Pilot INITIAL PAGE, press round INIT button below the MFD frame, not the square INIT button at the bottom center of the frame itself.
	# To return to the Copilot INITIAL PAGE, momentary IDM/INIT switch to INIT (below CPG MFD).

	# if CMWS is equipped, aircraft will have a CMWS box in the upper center instrument panel, and a CMWS panel in the center column.

	# CMWS PWR knob ... momentarily to TEST, then ON (CMWS control box, instrument panel top center)
	pushSeqCmd(dt, 'CI.HLP_CI_PWR_KNOB', 1) # 0 = OFF, 1 = ON, 2 = TEST
	pushSeqCmd(dt, 'CI.HLP_CI_PWR_KNOB', 2) # 0 = OFF, 1 = ON, 2 = TEST
	pushSeqCmd(dt, 'CI.HLP_CI_PWR_KNOB', 1) # 0 = OFF, 1 = ON, 2 = TEST

	# CMWS dispenser AUTO/BYPASS switch ... BYPASS recommended (center console lower panel rear, below collective handle)
	pushSeqCmd(dt, 'CI.HLP_CMWS_AUTO_BYPASS', 0) # 0 = BYPASS, 1 = AUTO
	pushSeqCmd(dt, 'CI.HLP_CMWS_ARM_SAFE', 1) # 0 = SAFE, 1 = ARM

	# Master Arm switch ... ARMED (center console upper panel bottom)
	pushSeqCmd(dt, 'WEAPONS.HLP_ACP_MASTER_SWITCH', 1) # 0 = SAFE, 1 = STBY, 2 = ARM
	pushSeqCmd(dt, 'WEAPONS.HLP_ACP_MASTER_SWITCH', 2) # 0 = SAFE, 1 = STBY, 2 = ARM

	# Laser Arm switch ... ARM (instrument panel far left)
	pushSeqCmd(dt, 'SYNC_CONTROLS.HLP_MMS_POWER_SWITCH', 1) # 0 = SAFE, 1 = STBY, 2 = ARM
	pushSeqCmd(dt, 'SYNC_CONTROLS.HLP_MMS_POWER_SWITCH', 2) # 0 = SAFE, 1 = STBY, 2 = ARM

	pushSeqCmd(dt, 'scriptSpeech', 'Waiting for alignment, all other startup items are complete.')

	# Wait until the alignment is complete (total process time minus the difference between now and when the process started).
	pushSeqCmd(dt, 'scriptTimerEnd', name='alignTimer')
	pushSeqCmd(dt, '', '', "Alignment complete.")

	# Bring up INITIAL PAGE on Pilot MFD after alignment complete.
	#pushSeqCmd(dt, 'RMFD.HLP_RMFD_AUX_INIT', 1) # Press
	#pushSeqCmd(dt, 'RMFD.HLP_RMFD_AUX_INIT', 0) # Release

	#pushSeqCmd(dt, 'scriptSpeech', "Manual steps remaining: Set lights.  Tune radios.  Set doppler navigation.  Set altimeter to Q F E or Q N H.")

	return seq


def HotStart(config, vars, helper, *args, **kwargs):
	seq = []
	dt = 0.3

	pushSeqCmd = helper.makePushSeqCmd(seq)

	# Start sequence
	pushSeqCmd(0, '', '', "Running Hot Start sequence.")

	# CMWS dispenser AUTO/BYPASS switch ... BYPASS recommended (center console lower panel rear, below collective handle)
	pushSeqCmd(dt, 'CI.HLP_CMWS_AUTO_BYPASS', 0) # 0 = BYPASS, 1 = AUTO

	# Master Arm switch ... ARMED (center console upper panel bottom)
	pushSeqCmd(dt, 'WEAPONS.HLP_ACP_MASTER_SWITCH', 1) # 0 = SAFE, 1 = STBY, 2 = ARM
	pushSeqCmd(dt, 'WEAPONS.HLP_ACP_MASTER_SWITCH', 2) # 0 = SAFE, 1 = STBY, 2 = ARM

	# Laser Arm switch ... ARM (instrument panel far left)
	pushSeqCmd(dt, 'SYNC_CONTROLS.HLP_MMS_POWER_SWITCH', 1) # 0 = SAFE, 1 = STBY, 2 = ARM
	pushSeqCmd(dt, 'SYNC_CONTROLS.HLP_MMS_POWER_SWITCH', 2) # 0 = SAFE, 1 = STBY, 2 = ARM

	#pushSeqCmd(dt, 'scriptSpeech', "Manual steps remaining: Set lights.  Tune radios.  Set doppler navigation.  Set altimeter to Q F E or Q N H.")

	return seq


def Shutdown(config, vars, helper, *args, **kwargs):
	seq = []
	dt = 0.3

	pushSeqCmd = helper.makePushSeqCmd(seq)


	# Start sequence
	pushSeqCmd(0, '', '', "Running Shutdown sequence.")
	pushSeqCmd(dt, 'scriptSpeech', "Warning, uses non standard key bindings.")
	pushSeqCmd(dt, 'scriptSpeech', 'Set collective full down.')

	# Laser Arm switch ... SAFE (instrument panel far left)
	pushSeqCmd(dt, 'SYNC_CONTROLS.HLP_MMS_POWER_SWITCH', 1) # 0 = SAFE, 1 = STBY, 2 = ARM
	pushSeqCmd(dt, 'SYNC_CONTROLS.HLP_MMS_POWER_SWITCH', 0) # 0 = SAFE, 1 = STBY, 2 = ARM

	# Master Arm switch ... SAFE (center console upper panel bottom)
	pushSeqCmd(dt, 'WEAPONS.HLP_ACP_MASTER_SWITCH', 1) # 0 = SAFE, 1 = STBY, 2 = ARM
	pushSeqCmd(dt, 'WEAPONS.HLP_ACP_MASTER_SWITCH', 0) # 0 = SAFE, 1 = STBY, 2 = ARM

	# CMWS dispenser ARM/SAFE switch ... SAFE (center console lower panel rear, below collective handle)
	pushSeqCmd(dt, 'CI.HLP_CMWS_ARM_SAFE', 0) # 0 = SAFE, 1 = ARM

	# CMWS PWR knob ... OFF (CMWS control box, instrument panel top center)
	pushSeqCmd(dt, 'CI.HLP_CI_PWR_KNOB', 0) # 0 = OFF, 1 = ON, 2 = TEST

	# SCAS PWR switch, then PITCH/ROLL and YAW switches ... On (center console right)
	pushSeqCmd(dt, 'SCAS.HLP_SCAS_YAW_SWITCH', 0)
	pushSeqCmd(dt, 'SCAS.HLP_SCAS_PITCHROLL_SWITCH', 0)
	pushSeqCmd(dt, 'SCAS.HLP_SCAS_POWER_SWITCH', 0)

	# Cancel warning tone.
	pushSeqCmd(dt, 'MFK.HLP_MFK_REC_ACK', 0) # ACK
	pushSeqCmd(dt, 'MFK.HLP_MFK_REC_ACK', 1) # Off (center)

	# MMS Mode knob ... STOW then OFF (instrument panel lower left, above CPG left knee)
	pushSeqCmd(dt, 'MMS.HLP_MMS_MODE_ROTATOR', 1) # 0 = OFF, 1 = STOW, 2 = PREFLT, 3 = PREPT, 4 = FWD, 5 = SRCH
	# NOTE Worse case stow time is 20 seconds, if MMS is rotated all the way to the right.
	pushSeqCmd(20, 'MMS.HLP_MMS_MODE_ROTATOR', 0) # 0 = OFF, 1 = STOW, 2 = PREFLT, 3 = PREPT, 4 = FWD, 5 = SRCH

	# Incr/Decr ("Inker-Dinker") switch ... Decr 2x to return engine trim to cold start condition (collective head)
	pushSeqCmd(dt, 'ENGINE.HLP_PILOT_ENG_RPM_TRIM', 0) # 0 = down, 1 = center, 2 = up
	pushSeqCmd(dt, 'ENGINE.HLP_PILOT_ENG_RPM_TRIM', 1) # 0 = down, 1 = center, 2 = up
	pushSeqCmd(dt, 'ENGINE.HLP_PILOT_ENG_RPM_TRIM', 0) # 0 = down, 1 = center, 2 = up
	pushSeqCmd(dt, 'ENGINE.HLP_PILOT_ENG_RPM_TRIM', 1) # 0 = down, 1 = center, 2 = up

	# Throttle ... Idle (throttle increase/decrease mapped to Numpad+/Numpad-)
	pushSeqCmd(dt, 'FUEL.Button_5', 1) # Throttle - Idle
	pushSeqCmd(dt, 'FUEL.Button_5', 0)
	# Throttle ... Closed
	pushSeqCmd(3, 'FUEL.Button_4', 1) # Throttle - Closed
	pushSeqCmd(dt, 'FUEL.Button_4', 0)

	## if IRCM is equipped, aircraft will have a IR JAMMER switch over the pilot's head.
	#pushSeqCmd(dt, 'ELECTRIC.HLP_ALQ144_SWITCH01', 0)

	## if CMWS is equipped, aircraft will have a CMWS switch over the pilot's head.
	#pushSeqCmd(dt, 'ELECTRIC.HLP_CMWS_SWITCH', 0)

	## All circuit breakers and switches on rear vertical CB panel On or Pushed In:
	#pushSeqCmd(dt, 'ELECTRIC.HLP_BFT', 0)
	#pushSeqCmd(dt, 'ELECTRIC.HLP_IFF', 0)
	#pushSeqCmd(dt, 'ELECTRIC.HLP_RADAR_DETR', 0)
	#pushSeqCmd(dt, 'ELECTRIC.HLP_RADAR_WARN', 0)
	#pushSeqCmd(dt, 'ELECTRIC.HLP_L2MUM', 1) # 0 = ON, 1 = OFF
	#pushSeqCmd(dt, 'ELECTRIC.HLP_PART_SEP', 1) # 0 = IN, 1 = OUT

	# FUEL BOOST switch ... OFF (forward) (overhead forward panel)
	pushSeqCmd(dt, 'ELECTRIC.HLP_FUELBOOST', 0)

	# DC GEN, AC GEN, and RUN ESNTL BUS switches ... On (forward) (overhead forward panel)
	pushSeqCmd(dt, 'ELECTRIC.HLP_ESSENTIAL_BUS', 0)
	pushSeqCmd(dt, 'ELECTRIC.HLP_AC_GEN', 0)
	pushSeqCmd(dt, 'ELECTRIC.HLP_DC_GEN', 1) # 0 = RESET, 1 = OFF, 2 = ON

	# IGN and FADEC switches ... OFF (forward) (overhead forward panel)
	pushSeqCmd(dt, 'ELECTRIC.HLP_FADEC', 0)
	pushSeqCmd(dt, 'ELECTRIC.HLP_IGN', 0)

	# BATT 1 switch ... OFF (forward) (overhead forward panel)
	pushSeqCmd(dt, 'ELECTRIC.HLP_BATT1', 1) # 0 = Preheat (momentary), 1 = OFF, 2 = ON

	# Ignition key ... OFF (fore/aft, not rotated) (center console under collective handle)
	pushSeqCmd(dt, 'ELECTRIC.HLP_MAIN_KEY', 0)

	return seq
