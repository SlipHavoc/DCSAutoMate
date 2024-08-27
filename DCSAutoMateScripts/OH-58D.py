# Return a Dictionary of script titles and their corresponding function names.  This is a list of scripts that users will be selecting from.  The module may have other utility functions that will not be run directly by the users.
def getScriptFunctions():
	return {
		'Cold Start (day and night is same)': 'ColdStart',
		'Hot Start (day and night is same)': 'HotStart',
		'Shutdown': 'Shutdown',
		#'Test': 'Test',
	}

def getInfo():
	return """ATTENTION: You must map "Throttle - Closed" to End, "Throttle - Idle" to Home, "Throttle - INCREASE" to Numpad+, and "Throttle - DECREASE" to Numpad-.  Otherwise there is no way for DCS-BIOS to interact with the throttle controls."""

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

	engineStartTime = 50 # Engine takes 50 seconds to start.
	alignmentTime = 2 * 60 + 30 # Alignment time is 2m30s from BATT 1 ON.

	# Start sequence
	pushSeqCmd(0, '', '', "Running Cold Start sequence.")
	pushSeqCmd(dt, 'scriptSpeech', "Warning, uses non standard key bindings.")
	pushSeqCmd(dt, 'scriptSpeech', 'Set collective full down.')

	# Ignition key ... On (rotated, not fore/aft) (center console under collective handle)
	pushSeqCmd(dt, 'IGNITION_KEY', 1)
	
	# BATT 1 switch ... On (forward) (overhead forward panel)
	pushSeqCmd(dt, 'FRONT_OVERHEAD_BATT_1', 2) # 0 = Preheat (momentary), 1 = OFF, 2 = ON
	pushSeqCmd(4, '', '', 'Wait for the power to come on.')
	alignmentTimerStart = getLastSeqTime() # Start a timer for the alignment process at the current seq time.
	
	# IGN and FADEC switches ... On (forward) (overhead forward panel)
	pushSeqCmd(dt, 'FRONT_OVERHEAD_SW_IGN', 1)
	pushSeqCmd(dt, 'FRONT_OVERHEAD_SW_FADEC', 1)

	# Throttle ... Idle position (collective grip) (mapped to Home key)
	pushSeqCmd(dt, 'scriptKeyboard', '{HOME down}{HOME up}') # NOTE Must map Throttle - Idle to Home.

	# Audio warning tone ... cancel with ACK switch (down) (center console top center)
	pushSeqCmd(dt, 'MFK_ACKNOWLEDGE_RECALL', 0) # ACK
	pushSeqCmd(dt, 'MFK_ACKNOWLEDGE_RECALL', 1) # Off (center)
	pushSeqCmd(dt, 'MFK_ACKNOWLEDGE_RECALL', 0) # ACK
	pushSeqCmd(dt, 'MFK_ACKNOWLEDGE_RECALL', 1) # Off (center)
	pushSeqCmd(dt, 'MFK_ACKNOWLEDGE_RECALL', 0) # ACK
	pushSeqCmd(dt, 'MFK_ACKNOWLEDGE_RECALL', 1) # Off (center)
	
	# START switch ... ON and hold for a few seconds until engine begins spooling up (collective head)
	pushSeqCmd(dt, 'PLT_COLLECTIVE_START', 1)
	pushSeqCmd(4, 'PLT_COLLECTIVE_START', 0)

	engineTimerStart = getLastSeqTime() # Start a timer for the engine start process at the current seq time.
	
	# Cancel warning tone.
	pushSeqCmd(7, 'MFK_ACKNOWLEDGE_RECALL', 0) # ACK
	pushSeqCmd(dt, 'MFK_ACKNOWLEDGE_RECALL', 1) # Off (center)
	pushSeqCmd(dt, 'MFK_ACKNOWLEDGE_RECALL', 0) # ACK
	pushSeqCmd(dt, 'MFK_ACKNOWLEDGE_RECALL', 1) # Off (center)

	# Cancel warning tone.
	pushSeqCmd(14, 'MFK_ACKNOWLEDGE_RECALL', 0) # ACK
	pushSeqCmd(dt, 'MFK_ACKNOWLEDGE_RECALL', 1) # Off (center)
	pushSeqCmd(dt, 'MFK_ACKNOWLEDGE_RECALL', 0) # ACK
	pushSeqCmd(dt, 'MFK_ACKNOWLEDGE_RECALL', 1) # Off (center)

	# Wait until the engine is started (total process time minus the difference between now and when the process started).
	engineTimerEnd = engineStartTime - (getLastSeqTime() - engineTimerStart)
	pushSeqCmd(engineTimerEnd, '', '', "Engine started.")

	# DC GEN, AC GEN, and RUN ESNTL BUS switches ... On (forward) (overhead forward panel)
	pushSeqCmd(dt, 'FRONT_OVERHEAD_DC_GEN', 2) # 0 = RESET, 1 = OFF, 2 = ON
	pushSeqCmd(dt, 'FRONT_OVERHEAD_AC_GEN', 1)
	pushSeqCmd(dt, 'FRONT_OVERHEAD_ESSENTIAL_BUS', 1)

	# FUEL BOOST switch ... On (forward) (overhead forward panel)
	pushSeqCmd(dt, 'FRONT_OVERHEAD_FUEL_BOOST', 1)

	# All circuit breakers and switches on rear vertical CB panel On or Pushed In:
	pushSeqCmd(dt, 'POST_CONSOLE_SW_HF', 1)
	pushSeqCmd(dt, 'POST_CONSOLE_SW_IFF', 1)
	pushSeqCmd(dt, 'POST_CONSOLE_SW_RADAR_DETR', 1)
	pushSeqCmd(dt, 'POST_CONSOLE_SW_RADAR_WARN', 1)
	pushSeqCmd(dt, 'POST_CONSOLE_SW_L2MUM', 0) # 0 = ON, 1 = OFF
	pushSeqCmd(dt, 'POST_CONSOLE_CB_PART_SEP', 0) # 0 = IN, 1 = OUT

	# if CMWS is equipped, aircraft will have a CMWS switch over the pilot's head.
	pushSeqCmd(dt, 'PLT_OVERHEAD_SW_CMWS', 1)

	# if IRCM is equipped, aircraft will have a IR JAMMER switch over the pilot's head.
	pushSeqCmd(dt, 'PLT_OVERHEAD_IR_JAMMER_BASE', 1)

	# Throttle ... slowly to Max (throttle increase/decrease mapped to Numpad+/Numpad-)
	# Take about 20 seconds to slowly advance most of the throttle.
	for i in range(60):
		pushSeqCmd(dt, 'scriptKeyboard', '{VK_ADD down}{VK_ADD up}')
	# Then turn it the rest of the way to max.
	pushSeqCmd(dt, 'scriptKeyboard', '{VK_ADD down}')
	pushSeqCmd(1, 'scriptKeyboard', '{VK_ADD up}')
	
	# Clear warnings.
	pushSeqCmd(dt, 'MFK_ACKNOWLEDGE_RECALL', 0) # ACK
	pushSeqCmd(dt, 'MFK_ACKNOWLEDGE_RECALL', 1) # Off (center)
	pushSeqCmd(dt, 'MFK_ACKNOWLEDGE_RECALL', 0) # ACK
	pushSeqCmd(dt, 'MFK_ACKNOWLEDGE_RECALL', 1) # Off (center)

	# MPD (Multiparameter Display) ... Select switch +/- to NR (digital "chicklet" display, instrument panel center bottom, just above center console)
	pushSeqCmd(dt, 'MPD_SELECT', 0) # 0 = down, 1 = center, 2 = up
	pushSeqCmd(dt, 'MPD_SELECT', 1) # 0 = down, 1 = center, 2 = up
	
	# Incr/Decr ("Inker-Dinker") switch ... +/- as needed (right-click 2x) to set NR to 100 (collective head)
	pushSeqCmd(dt, 'PLT_COLLECTIVE_ENGINE_RPM_TRIM', 2) # 0 = down, 1 = center, 2 = up
	pushSeqCmd(dt, 'PLT_COLLECTIVE_ENGINE_RPM_TRIM', 1) # 0 = down, 1 = center, 2 = up
	pushSeqCmd(dt, 'PLT_COLLECTIVE_ENGINE_RPM_TRIM', 2) # 0 = down, 1 = center, 2 = up
	pushSeqCmd(dt, 'PLT_COLLECTIVE_ENGINE_RPM_TRIM', 1) # 0 = down, 1 = center, 2 = up
	# When at 100, NR "chicklet" light should be just one light resting on the 100 line.

	# Bring up NAV ALIGN page on Pilot MFD to monitor alignment.  Shows "GC ALIGN" at bottom of this screen while aligning.
	#pushSeqCmd(dt, 'MFD_PLT_L1', 1) # Press
	#pushSeqCmd(dt, 'MFD_PLT_L1', 1) # Release

	# MMS Mode knob ... PREPT or FWD (instrument panel lower left, above CPG left knee)
	pushSeqCmd(dt, 'MMS_MODE', 1) # 0 = OFF, 1 = STOW, 2 = PREFLT, 3 = PREPT, 4 = FWD, 5 = SRCH
	pushSeqCmd(dt, 'MMS_MODE', 2) # 0 = OFF, 1 = STOW, 2 = PREFLT, 3 = PREPT, 4 = FWD, 5 = SRCH
	pushSeqCmd(dt, 'MMS_MODE', 3) # 0 = OFF, 1 = STOW, 2 = PREFLT, 3 = PREPT, 4 = FWD, 5 = SRCH
	pushSeqCmd(dt, 'MMS_MODE', 4) # 0 = OFF, 1 = STOW, 2 = PREFLT, 3 = PREPT, 4 = FWD, 5 = SRCH

	# SCAS PWR switch, then PITCH/ROLL and YAW switches ... On (center console right)
	pushSeqCmd(dt, 'SCAS_POWER', 1)
	pushSeqCmd(dt, 'SCAS_PITCH_ROLL', 1)
	pushSeqCmd(dt, 'SCAS_YAW', 1)

	# Alignment is shown in INITIAL PAGE > NAV ALIGN on MFD.  Should start aligning automatically when BATT 1 is turned on, takes about 4-4.5 mins.
	# When done, GC ALIGN at bottom of MFD screen goes away and "AUTO" on AUTO/MANUAL OSB gets unboxed.
	# To return to the Pilot INITIAL PAGE, press round INIT button below the MFD frame, not the square INIT button at the bottom center of the frame itself.
	# To return to the Copilot INITIAL PAGE, momentary IDM/INIT switch to INIT (below CPG MFD).
	
	# if CMWS is equipped, aircraft will have a CMWS box in the upper center instrument panel, and a CMWS panel in the center column.
	
	# CMWS PWR knob ... momentarily to TEST, then ON (CMWS control box, instrument panel top center)
	pushSeqCmd(dt, 'CMWS_ON_OFF_TEST', 1) # 0 = OFF, 1 = ON, 2 = TEST
	pushSeqCmd(dt, 'CMWS_ON_OFF_TEST', 2) # 0 = OFF, 1 = ON, 2 = TEST
	pushSeqCmd(dt, 'CMWS_ON_OFF_TEST', 1) # 0 = OFF, 1 = ON, 2 = TEST
		
	# CMWS dispenser AUTO/BYPASS switch ... BYPASS recommended (center console lower panel rear, below collective handle)
	pushSeqCmd(dt, 'CMWS_BYPASS', 0) # 0 = BYPASS, 1 = AUTO
	pushSeqCmd(dt, 'CMWS_ARM', 1) # 0 = SAFE, 1 = ARM

	# Master Arm switch ... ARMED (center console upper panel bottom)
	pushSeqCmd(dt, 'ARMAMENT_MASTER_ARM', 1) # 0 = SAFE, 1 = STBY, 2 = ARM
	pushSeqCmd(dt, 'ARMAMENT_MASTER_ARM', 2) # 0 = SAFE, 1 = STBY, 2 = ARM
	
	# Laser Arm switch ... ARM (instrument panel far left)
	pushSeqCmd(dt, 'MMS_LASER_POWER', 1) # 0 = SAFE, 1 = STBY, 2 = ARM
	pushSeqCmd(dt, 'MMS_LASER_POWER', 2) # 0 = SAFE, 1 = STBY, 2 = ARM

	pushSeqCmd(dt, 'scriptSpeech', 'Waiting for alignment, all other startup items are complete.')

	# Wait until the alignment is complete (total process time minus the difference between now and when the process started).
	alignmentTimerEnd = alignmentTime - (getLastSeqTime() - alignmentTimerStart)
	pushSeqCmd(alignmentTimerEnd, '', '', "Alignment complete.")

	# Bring up INITIAL PAGE on Pilot MFD after alignment complete.
	#pushSeqCmd(dt, 'MFD_PLT_AUX_INIT', 1) # Press
	#pushSeqCmd(dt, 'MFD_PLT_AUX_INIT', 0) # Release

	#pushSeqCmd(dt, 'scriptSpeech', "Manual steps remaining: Set lights.  Tune radios.  Set doppler navigation.  Set altimeter to Q F E or Q N H.")

	return seq


def HotStart(config):
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
	pushSeqCmd(0, '', '', "Running Hot Start sequence.")

	# CMWS dispenser AUTO/BYPASS switch ... BYPASS recommended (center console lower panel rear, below collective handle)
	pushSeqCmd(dt, 'CMWS_BYPASS', 0) # 0 = BYPASS, 1 = AUTO
	
	# Master Arm switch ... ARMED (center console upper panel bottom)
	pushSeqCmd(dt, 'ARMAMENT_MASTER_ARM', 1) # 0 = SAFE, 1 = STBY, 2 = ARM
	pushSeqCmd(dt, 'ARMAMENT_MASTER_ARM', 2) # 0 = SAFE, 1 = STBY, 2 = ARM
	
	# Laser Arm switch ... ARM (instrument panel far left)
	pushSeqCmd(dt, 'MMS_LASER_POWER', 1) # 0 = SAFE, 1 = STBY, 2 = ARM
	pushSeqCmd(dt, 'MMS_LASER_POWER', 2) # 0 = SAFE, 1 = STBY, 2 = ARM

	#pushSeqCmd(dt, 'scriptSpeech', "Manual steps remaining: Set lights.  Tune radios.  Set doppler navigation.  Set altimeter to Q F E or Q N H.")

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

	
	# Start sequence
	pushSeqCmd(0, '', '', "Running Shutdown sequence.")
	pushSeqCmd(dt, 'scriptSpeech', "Warning, uses non standard key bindings.")
	pushSeqCmd(dt, 'scriptSpeech', 'Set collective full down.')
	
	# Laser Arm switch ... SAFE (instrument panel far left)
	pushSeqCmd(dt, 'MMS_LASER_POWER', 1) # 0 = SAFE, 1 = STBY, 2 = ARM
	pushSeqCmd(dt, 'MMS_LASER_POWER', 0) # 0 = SAFE, 1 = STBY, 2 = ARM

	# Master Arm switch ... SAFE (center console upper panel bottom)
	pushSeqCmd(dt, 'ARMAMENT_MASTER_ARM', 1) # 0 = SAFE, 1 = STBY, 2 = ARM
	pushSeqCmd(dt, 'ARMAMENT_MASTER_ARM', 0) # 0 = SAFE, 1 = STBY, 2 = ARM

	# CMWS dispenser ARM/SAFE switch ... SAFE (center console lower panel rear, below collective handle)
	pushSeqCmd(dt, 'CMWS_ARM', 0) # 0 = SAFE, 1 = ARM

	# CMWS PWR knob ... OFF (CMWS control box, instrument panel top center)
	pushSeqCmd(dt, 'CMWS_ON_OFF_TEST', 0) # 0 = OFF, 1 = ON, 2 = TEST
	
	# SCAS PWR switch, then PITCH/ROLL and YAW switches ... On (center console right)
	pushSeqCmd(dt, 'SCAS_YAW', 0)
	pushSeqCmd(dt, 'SCAS_PITCH_ROLL', 0)
	pushSeqCmd(dt, 'SCAS_POWER', 0)

	# Cancel warning tone.
	pushSeqCmd(dt, 'MFK_ACKNOWLEDGE_RECALL', 0) # ACK
	pushSeqCmd(dt, 'MFK_ACKNOWLEDGE_RECALL', 1) # Off (center)

	# MMS Mode knob ... STOW then OFF (instrument panel lower left, above CPG left knee)
	pushSeqCmd(dt, 'MMS_MODE', 1) # 0 = OFF, 1 = STOW, 2 = PREFLT, 3 = PREPT, 4 = FWD, 5 = SRCH
	# NOTE Worse case stow time is 20 seconds, if MMS is rotated all the way to the right.
	pushSeqCmd(20, 'MMS_MODE', 0) # 0 = OFF, 1 = STOW, 2 = PREFLT, 3 = PREPT, 4 = FWD, 5 = SRCH

	# Incr/Decr ("Inker-Dinker") switch ... Decr 2x to return engine trim to cold start condition (collective head)
	pushSeqCmd(dt, 'PLT_COLLECTIVE_ENGINE_RPM_TRIM', 0) # 0 = down, 1 = center, 2 = up
	pushSeqCmd(dt, 'PLT_COLLECTIVE_ENGINE_RPM_TRIM', 1) # 0 = down, 1 = center, 2 = up
	pushSeqCmd(dt, 'PLT_COLLECTIVE_ENGINE_RPM_TRIM', 0) # 0 = down, 1 = center, 2 = up
	pushSeqCmd(dt, 'PLT_COLLECTIVE_ENGINE_RPM_TRIM', 1) # 0 = down, 1 = center, 2 = up

	# Throttle ... Idle (throttle increase/decrease mapped to Numpad+/Numpad-)
	pushSeqCmd(dt, 'scriptKeyboard', '{VK_SUBTRACT down}')
	pushSeqCmd(4, 'scriptKeyboard', '{VK_SUBTRACT up}')
	# Throttle ... Closed
	pushSeqCmd(3, 'scriptKeyboard', '{END down}{END up}')
	
	## if IRCM is equipped, aircraft will have a IR JAMMER switch over the pilot's head.
	#pushSeqCmd(dt, 'PLT_OVERHEAD_IR_JAMMER_BASE', 0)

	## if CMWS is equipped, aircraft will have a CMWS switch over the pilot's head.
	#pushSeqCmd(dt, 'PLT_OVERHEAD_SW_CMWS', 0)

	## All circuit breakers and switches on rear vertical CB panel On or Pushed In:
	#pushSeqCmd(dt, 'POST_CONSOLE_SW_HF', 0)
	#pushSeqCmd(dt, 'POST_CONSOLE_SW_IFF', 0)
	#pushSeqCmd(dt, 'POST_CONSOLE_SW_RADAR_DETR', 0)
	#pushSeqCmd(dt, 'POST_CONSOLE_SW_RADAR_WARN', 0)
	#pushSeqCmd(dt, 'POST_CONSOLE_SW_L2MUM', 1) # 0 = ON, 1 = OFF
	#pushSeqCmd(dt, 'POST_CONSOLE_CB_PART_SEP', 1) # 0 = IN, 1 = OUT

	# FUEL BOOST switch ... OFF (forward) (overhead forward panel)
	pushSeqCmd(dt, 'FRONT_OVERHEAD_FUEL_BOOST', 0)

	# DC GEN, AC GEN, and RUN ESNTL BUS switches ... On (forward) (overhead forward panel)
	pushSeqCmd(dt, 'FRONT_OVERHEAD_ESSENTIAL_BUS', 0)
	pushSeqCmd(dt, 'FRONT_OVERHEAD_AC_GEN', 0)
	pushSeqCmd(dt, 'FRONT_OVERHEAD_DC_GEN', 1) # 0 = RESET, 1 = OFF, 2 = ON
	
	# IGN and FADEC switches ... OFF (forward) (overhead forward panel)
	pushSeqCmd(dt, 'FRONT_OVERHEAD_SW_FADEC', 0)
	pushSeqCmd(dt, 'FRONT_OVERHEAD_SW_IGN', 0)
	
	# BATT 1 switch ... OFF (forward) (overhead forward panel)
	pushSeqCmd(dt, 'FRONT_OVERHEAD_BATT_1', 1) # 0 = Preheat (momentary), 1 = OFF, 2 = ON
	
	# Ignition key ... OFF (fore/aft, not rotated) (center console under collective handle)
	pushSeqCmd(dt, 'IGNITION_KEY', 0)

	return seq
