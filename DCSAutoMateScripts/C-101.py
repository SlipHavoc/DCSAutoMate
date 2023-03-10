# Return a Dictionary of script titles and their corresponding function names.  This is a list of scripts that users will be selecting from.  The module may have other utility functions that will not be run directly by the users.
def getScriptFunctions():
	return {
		'Cold Start C-101CC': 'ColdStartCC',
		'Cold Start C-101EB': 'ColdStartEB',
	}

def ScriptColdStartCC(config):
	return ColdStart('C-101CC')

def ScriptColdStartEB(config):
	return ColdStart('C-101EB')

def ColdStart(airplaneName = 'C-101CC'):
	seq = []
	seqTime = 0
	dt = 0.2

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
	
	tarsynSyncTime = 2 * 60 + 5 # TARSYN sync time, 2m5s, starts when Inverter switch is set to NORM.
		
	int16 = 65535

	def resetMasterCaution():
		# Reset MASTER WARNING and MASTER CAUTION
		#pushSeqCmd(dt, '', '', "MASTER WARNING - Reset")
		pushSeqCmd(dt, 'FRONT_CAWS_FAULT_RESET', 1)
		pushSeqCmd(dt, 'FRONT_CAWS_FAULT_RESET', 0)
		#pushSeqCmd(dt, '', '', "MASTER CAUTION - Reset")
		pushSeqCmd(dt, 'FRONT_CAWS_CAUTION_RESET', 1)
		pushSeqCmd(dt, 'FRONT_CAWS_CAUTION_RESET', 0)

	"""
	def turnOffRadios():
		if airplaneName == 'C-101CC':
			# V/TVU-740 radio, front instrument panel
			#pushSeqCmd(dt, '', '', "V/TVU-740 V/UHF radio - Off")
			pushSeqCmd(dt, 'CC_FRONT_UHF_FUNCT', 0) # 0 = OFF, 1 = A3 (on), 2 = A3+G (on+guard), 3 = DF (not implemented)
			
			#  VHF-20B radio, right console
			#pushSeqCmd(dt, '', '', "VHF-20B VHF radio - Off")
			pushSeqCmd(dt, 'CC_FRONT_VHF_COMM_PW', 0) # 0 = OFF, 1 = PWR, 2 = TEST
		elif airplaneName == 'C-101EB':
			# ARC-164(V) radio, front instrument panel
			#pushSeqCmd(dt, '', '', "ARC-164(V) UHF radio - Off")
			pushSeqCmd(dt, 'EB_FRONT_UHF_FUNCT', 0) # 0 = OFF, 1 = MAIN, 2 = BOTH, 3 = ADF
			
			# ARC-134 radio, right console
			#pushSeqCmd(dt, '', '', "ARC-134 VHF radio - Off")
			pushSeqCmd(dt, 'EB_FRONT_VHF_COMM_PW', 0)
	
	def turnOffGunsight():
		if airplaneName == 'C-101CC':
			# Gunsight
			#pushSeqCmd(dt, '', '', "Gunsight - Off, Auto")
			#pushSeqCmd(dt, {device = devices.SYSTEMS, action = device_commands.Button_318, 0) # 0.0 = OFF, 1.0 = ON
			#pushSeqCmd(dt, {device = devices.SYSTEMS, action = device_commands.Button_317, 1) # 1.0 = AUTO, 0.5 = MAN, 0.0 = TEST (momentary, so set back to 0.5 afterwards if used)
	"""

	##################################################
	##################################################
	# Start sequence
	pushSeqCmd(0, '', '', "Running Cold Start sequence")

	#pushSeqCmd(dt, '', '', "Ignition - Off")
	pushSeqCmd(dt, 'FRONT_CONT_ING_START', 1) # 0 = CONT (back), 1 = OFF (middle), 2 = START (forward)

	#pushSeqCmd(dt, '', '', "Parking brake - Set")
	pushSeqCmd(dt, 'FRONT_PARK_BRAKE_LVR', 1)
	
	#pushSeqCmd(dt, '', '', "Ground power supply - On (waiting 12s)")
	pushSeqCmd(dt, 'scriptKeyboard', '{\ down}{\ up}') # Must have separate down and up to register key press.
	pushSeqCmd(dt, 'scriptKeyboard', '{F8}')
	pushSeqCmd(dt, 'scriptKeyboard', '{F2}')
	pushSeqCmd(dt, 'scriptKeyboard', '{F1}')
	pushSeqCmd(12.0, '', '', "Ground power is on")
	
	#pushSeqCmd(dt, '', '', "Accelerometer - Reset")
	pushSeqCmd(dt, 'FRONT_GMETER_RESET', 1)
	pushSeqCmd(dt, 'FRONT_GMETER_RESET', 0)

	#pushSeqCmd(dt, '', '', "Oxygen valve lever (Front seat) - Open")
	pushSeqCmd(dt, 'FRONT_OXY_SUPPLY', 1)
	#pushSeqCmd(dt, '', '', "Oxygen valve lever (Rear seat) - Open")
	pushSeqCmd(dt, 'BACK_OXY_SUPPLY', 1)

	###- START UP
	#pushSeqCmd(dt, '', '', "Battery switch - On")
	pushSeqCmd(dt, 'FRONT_BATT_MASTER_SW', 1)
	
	# Reset MASTER WARNING and MASTER CAUTION
	resetMasterCaution()
	
	# Radios
	if airplaneName == 'C-101CC':
		# V/TVU-740 radio, front instrument panel
		#pushSeqCmd(dt, '', '', "V/TVU-740 V/UHF radio - On")
		pushSeqCmd(dt, 'CC_FRONT_UHF_FUNCT', 1) # 0 = OFF, 1 = A3 (on), 2 = A3+G (on+guard), 3 = DF (not implemented)
		
		#  VHF-20B radio, right console
		#pushSeqCmd(dt, '', '', "VHF-20B VHF radio - On")
		pushSeqCmd(dt, 'CC_FRONT_VHF_COMM_PW', 1) # 0 = OFF, 1 = PWR, 2 = TEST
	elif airplaneName == 'C-101EB':
		# ARC-164(V) radio, front instrument panel
		#pushSeqCmd(dt, '', '', "ARC-164(V) UHF radio - On")
		pushSeqCmd(dt, 'EB_FRONT_UHF_FUNCT', 1) # 0 = OFF, 1 = MAIN, 2 = BOTH, 3 = ADF
		
		# ARC-134 radio, right console
		#pushSeqCmd(dt, '', '', "ARC-134 VHF radio - On")
		pushSeqCmd(dt, 'EB_FRONT_VHF_COMM_PW', 1)
	
	# Ground power on
	#pushSeqCmd(dt, '', '', "GPU - On (3s)")
	pushSeqCmd(dt, 'FRONT_GPU', 1)
	pushSeqCmd(dt, 'FRONT_GPU', 0)
	pushSeqCmd(3, '', '', "Ground power supply is revved up")

	#pushSeqCmd(dt, '', '', "Bus tie switch - On")
	pushSeqCmd(dt, 'FRONT_DC_BUS_TIE', 1)
	
	# Reset MASTER WARNING and MASTER CAUTION
	resetMasterCaution()
	
	#pushSeqCmd(dt, '', '', "Inverter switch - Normal")
	pushSeqCmd(dt, 'FRONT_AC_INVERTER', 1)
	#pushSeqCmd(dt, '', '', "Waiting for TARSYN syncronization (2m5s)")
	tarsynSyncTimerStart = getLastSeqTime() # Start a timer for the TARSYN sync at the current sequence time value.

	#pushSeqCmd(dt, '', '', "Transfer pump switches - Auto")
	pushSeqCmd(dt, 'FRONT_FUEL_TRANS_C1', 1)
	pushSeqCmd(dt, 'FRONT_FUEL_TRANS_C2', 1)
	pushSeqCmd(dt, 'FRONT_FUEL_TRANS_L', 1)
	pushSeqCmd(dt, 'FRONT_FUEL_TRANS_R', 1)
	
	#pushSeqCmd(dt, '', '', "Fuselage tank pump button - On")
	pushSeqCmd(dt, 'FRONT_FUSE_TANK_PUMP_COVER', 1) # Cover open
	pushSeqCmd(dt, 'FRONT_FUSE_TANK_PUMP', 1)
	pushSeqCmd(dt, 'FRONT_FUSE_TANK_PUMP', 0)
	pushSeqCmd(dt, 'FRONT_FUSE_TANK_PUMP_COVER', 0) # Cover close

	#pushSeqCmd(dt, '', '', "Fuel shutoff valve button - On (fuel flow enabled)")
	pushSeqCmd(dt, 'FRONT_ENG_FUEL_VALVE_PUMP_COVER', 1) # Cover open
	pushSeqCmd(dt, 'FRONT_ENG_FUEL_VALVE_PUMP', 1)
	pushSeqCmd(dt, 'FRONT_ENG_FUEL_VALVE_PUMP', 0)
	pushSeqCmd(dt, 'FRONT_ENG_FUEL_VALVE_PUMP_COVER', 0) # Cover close

	#pushSeqCmd(dt, '', '', "STARTING ENGINE (37s)")

	#pushSeqCmd(dt, '', '', "Ignition switch - Start (2s)")
	pushSeqCmd(dt, 'FRONT_CONT_ING_START', 2)
	pushSeqCmd(2, 'FRONT_CONT_ING_START', 1)
	
	#pushSeqCmd(dt, '', '', "At 10% N2: power lever - Idle")
	pushSeqCmd(5.0, 'scriptKeyboard', '{VK_RSHIFT down}{HOME down}{HOME up}{VK_RSHIFT up}')
	
	#pushSeqCmd(dt, '', '', "Wait for engine instruments to stabilize (30s)")
	pushSeqCmd(30, '', '', "Engine instruments - Stabilized")
	
	# Ground power off
	#pushSeqCmd(dt, '', '', "GPU - Off")
	pushSeqCmd(dt, 'FRONT_GPU', 1)
	pushSeqCmd(dt, 'FRONT_GPU', 0)
	#pushSeqCmd(dt, '', '', "Ground power supply is off")

	#pushSeqCmd(dt, '', '', "Generator - Reset, then On")
	pushSeqCmd(dt, 'FRONT_GEN_SW', 0)
	pushSeqCmd(dt, 'FRONT_GEN_SW', 2)
	
	# IFF
	#pushSeqCmd(dt, '', '', "IFF Master switch - NORM")
	pushSeqCmd(dt, 'FRONT_IFF_MASTER_SW', 1) # 0 = EMER, 1 = NORM, 2 = LOW, 3 = STBY, 4 = OFF
	#pushSeqCmd(dt, '', '', "IFF Mode 4 switch - ON")
	pushSeqCmd(dt, 'FRONT_IFF_MODE4', 1)

	#pushSeqCmd(dt, '', '', "Standby artificial horizon - Uncage")
	pushSeqCmd(dt, 'FRONT_BAK_ADI_CAGE_BNT', 0) # Misspelling, "BNT" is correct.
	pushSeqCmd(dt, 'FRONT_BAK_ADI_CAGE_KNOB', int(int16 * 0.5))
	
	# Gunsight (C-101CC only)
	if airplaneName == 'C-101CC':
		# Gunsight
		#pushSeqCmd(dt, '', '', "Gunsight - On, Man")
		pushSeqCmd(dt, 'CC_FRONT_HUD_SIGHT', 1) # On
		pushSeqCmd(dt, 'CC_FRONT_HUD_DEPRESS_MODE', 1) # Man
		# NOTE The gunsight starts at 030 mils, and should be set to 010 mils initially for a waterline reference, but we can't guarantee the value on a cold restart after a shutdown, so leaving this to be set manually.
		##pushSeqCmd(dt, '', '', "Gunsight depression - 010 mils (waterline)")
		#pushSeqCmd(dt, 'CC_FRONT_HUD_DEPRESS_XX0', 'DEC')
		#pushSeqCmd(dt, 'CC_FRONT_HUD_DEPRESS_XX0', 'DEC')

	#pushSeqCmd(dt, '', '', "Flaps - Takeoff")
	pushSeqCmd(dt, 'FRONT_FLAP_SEL', 1)

	#pushSeqCmd(dt, '', '', "Canopy - Close and lock")
	pushSeqCmd(dt, 'FRONT_CANOPY_SAFE', 1) # Canopy safety latch
	pushSeqCmd(3.2, 'FRONT_CANOPY_LOCK', 1)
	
	#pushSeqCmd(dt, '', '', "Air conditioning - Reset and On")
	pushSeqCmd(dt, 'FRONT_AIR_COND_MASTER', 0)
	pushSeqCmd(dt, 'FRONT_AIR_COND_MASTER', 1)
	pushSeqCmd(dt, 'FRONT_AIR_COND_MASTER', 2)
	
	#pushSeqCmd(dt, '', '', "Ejection seat safety pin (Front seat) - Remove")
	pushSeqCmd(dt, 'FRONT_EJECT_HANDLE_COVER', 1)
	#pushSeqCmd(dt, '', '', "Ejection seat safety pin (Rear seat) - Remove")
	pushSeqCmd(dt, 'BACK_EJECT_HANDLE_COVER', 1)
	
	# Canopy Fracture Safety Pin (C-101CC only) (right console)
	if airplaneName == 'C-101CC':
		#pushSeqCmd(dt, '', '', "Canopy fracture satefy pin (Front seat) - Remove")
		pushSeqCmd(dt, 'CC_FRONT_CANOPY_EMERG_FRAC_PIN', 1)
		#pushSeqCmd(dt, '', '', "Canopy fracture satefy pin (Rear seat) - Remove")
		pushSeqCmd(dt, 'CC_BACK_CANOPY_EMERG_FRAC_PIN', 1)

	# Wait until the TARSYN sync is complete (total process time minus the difference between now and when the process started).
	tarsynSyncTimerEnd = tarsynSyncTime - (getLastSeqTime() - tarsynSyncTimerStart)
	pushSeqCmd(tarsynSyncTimerEnd, '', '', "TARSYN alignment complete")

	#pushSeqCmd(dt, '', '', "Manual steps remaining:")
	#pushSeqCmd(dt, '', '', "Lights ... As needed")
	#pushSeqCmd(dt, '', '', "Radios ... As needed")
	#pushSeqCmd(dt, '', '', "Navigation ... As needed")
	#pushSeqCmd(dt, '', '', "Set altimeter to match QFE (airfield elevation) or QNH (sea level altitude) as desired")
	#pushSeqCmd(dt, '', '', "Set gunsight to 010 mils for aircraft centerline")
	manualSteps = "Manual steps remaining: Set lights.  Tune radios.  Set navigation system.  Set altimeter to Q F E or Q N H."
	if airplaneName == 'C-101CC':
		manualSteps += "  Set gunsight to 0 1 0 mils for aircraft centerline."
	pushSeqCmd(dt, 'scriptSpeech', manualSteps)
	
	return seq
