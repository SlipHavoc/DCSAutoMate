# Return a Dictionary of script titles and their corresponding function names.  This is a list of scripts that users will be selecting from.  The module may have other utility functions that will not be run directly by the users.
def getScriptFunctions():
	return {
		'Cold Start C-101CC': 'ColdStartCC',
		'Cold Start C-101EB': 'ColdStartEB',
		'Hot Start C-101CC': 'HotStartCC',
		'Hot Start C-101EB': 'HotStartEB',
	}

def ColdStartCC(config):
	return ColdStart(config, 'C-101CC')

def ColdStartEB(config):
	return ColdStart(config, 'C-101EB')

def HotStartCC(config):
	return HotStart(config, 'C-101CC')

def HotStartEB(config):
	return HotStart(config, 'C-101EB')

def ColdStart(config, airplaneName = 'C-101CC'):
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
		# MASTER WARNING - Reset
		pushSeqCmd(dt, 'FRONT_CAWS_FAULT_RESET', 1)
		pushSeqCmd(dt, 'FRONT_CAWS_FAULT_RESET', 0)
		# MASTER CAUTION - Reset
		pushSeqCmd(dt, 'FRONT_CAWS_CAUTION_RESET', 1)
		pushSeqCmd(dt, 'FRONT_CAWS_CAUTION_RESET', 0)

	"""
	def turnOffRadios():
		if airplaneName == 'C-101CC':
			# V/TVU-740 radio, front instrument panel
			# V/TVU-740 V/UHF radio - Off
			pushSeqCmd(dt, 'CC_FRONT_UHF_FUNCT', 0) # 0 = OFF, 1 = A3 (on), 2 = A3+G (on+guard), 3 = DF (not implemented)
			
			#  VHF-20B radio, right console
			# VHF-20B VHF radio - Off
			pushSeqCmd(dt, 'CC_FRONT_VHF_COMM_PW', 0) # 0 = OFF, 1 = PWR, 2 = TEST
		elif airplaneName == 'C-101EB':
			# ARC-164(V) radio, front instrument panel
			# ARC-164(V) UHF radio - Off
			pushSeqCmd(dt, 'EB_FRONT_UHF_FUNCT', 0) # 0 = OFF, 1 = MAIN, 2 = BOTH, 3 = ADF
			
			# ARC-134 radio, right console
			# ARC-134 VHF radio - Off
			pushSeqCmd(dt, 'EB_FRONT_VHF_COMM_PW', 0)
	
	def turnOffGunsight():
		if airplaneName == 'C-101CC':
			# Gunsight
			# Gunsight - Off, Auto")
			#pushSeqCmd(dt, {device = devices.SYSTEMS, action = device_commands.Button_318, 0) # 0.0 = OFF, 1.0 = ON
			#pushSeqCmd(dt, {device = devices.SYSTEMS, action = device_commands.Button_317, 1) # 1.0 = AUTO, 0.5 = MAN, 0.0 = TEST (momentary, so set back to 0.5 afterwards if used)
	"""

	##################################################
	##################################################
	# Start sequence
	pushSeqCmd(0, '', '', "Running Cold Start sequence")
	pushSeqCmd(dt, 'scriptSpeech', 'Set throttle to minimum.')

	# Ignition - Off
	pushSeqCmd(dt, 'FRONT_CONT_ING_START', 1) # 0 = CONT (back), 1 = OFF (middle), 2 = START (forward)

	# Parking brake - Set
	pushSeqCmd(dt, 'FRONT_PARK_BRAKE_LVR', 1)
	
	# Ground power supply - On (waiting 13s)
	pushSeqCmd(dt, 'scriptKeyboard', '{\ down}{\ up}') # Must have separate down and up to register key press.
	pushSeqCmd(dt, 'scriptKeyboard', '{F8}')
	pushSeqCmd(dt, 'scriptKeyboard', '{F2}')
	pushSeqCmd(dt, 'scriptKeyboard', '{F1}')
	pushSeqCmd(13, '', '', "Ground power is on")
	
	# Accelerometer - Reset
	pushSeqCmd(dt, 'FRONT_GMETER_RESET', 1)
	pushSeqCmd(dt, 'FRONT_GMETER_RESET', 0)

	# Oxygen valve lever (Front seat) - Open
	pushSeqCmd(dt, 'FRONT_OXY_SUPPLY', 1)
	# Oxygen valve lever (Rear seat) - Open
	pushSeqCmd(dt, 'BACK_OXY_SUPPLY', 1)

	###- START UP
	# Battery switch - On
	pushSeqCmd(dt, 'FRONT_BATT_MASTER_SW', 1)
	
	# Reset MASTER WARNING and MASTER CAUTION
	resetMasterCaution()
	
	# Radios
	if airplaneName == 'C-101CC':
		# V/TVU-740 radio, front instrument panel
		# V/TVU-740 V/UHF radio - On
		pushSeqCmd(dt, 'CC_FRONT_UHF_FUNCT', 1) # 0 = OFF, 1 = A3 (on), 2 = A3+G (on+guard), 3 = DF (not implemented)
		
		#  VHF-20B radio, right console
		# VHF-20B VHF radio - On
		pushSeqCmd(dt, 'CC_FRONT_VHF_COMM_PW', 1) # 0 = OFF, 1 = PWR, 2 = TEST
	elif airplaneName == 'C-101EB':
		# ARC-164(V) radio, front instrument panel
		# ARC-164(V) UHF radio - On
		pushSeqCmd(dt, 'EB_FRONT_UHF_FUNCT', 1) # 0 = OFF, 1 = MAIN, 2 = BOTH, 3 = ADF
		
		# ARC-134 radio, right console
		# ARC-134 VHF radio - On
		pushSeqCmd(dt, 'EB_FRONT_VHF_COMM_PW', 1)
	
	# Ground power on
	# GPU - On (3s)
	pushSeqCmd(dt, 'FRONT_GPU', 1)
	pushSeqCmd(dt, 'FRONT_GPU', 0)
	pushSeqCmd(3, '', '', "Ground power supply is revved up")

	# Bus tie switch - On
	pushSeqCmd(dt, 'FRONT_DC_BUS_TIE', 1)
	
	# Reset MASTER WARNING and MASTER CAUTION
	resetMasterCaution()
	
	# Inverter switch - Normal
	pushSeqCmd(dt, 'FRONT_AC_INVERTER', 1)
	# Waiting for TARSYN syncronization (2m5s)
	tarsynSyncTimerStart = getLastSeqTime() # Start a timer for the TARSYN sync at the current sequence time value.

	# Transfer pump switches - Auto
	pushSeqCmd(dt, 'FRONT_FUEL_TRANS_C1', 1)
	pushSeqCmd(dt, 'FRONT_FUEL_TRANS_C2', 1)
	pushSeqCmd(dt, 'FRONT_FUEL_TRANS_L', 1)
	pushSeqCmd(dt, 'FRONT_FUEL_TRANS_R', 1)
	
	# Fuselage tank pump button - On
	pushSeqCmd(dt, 'FRONT_FUSE_TANK_PUMP_COVER', 1) # Cover open
	pushSeqCmd(dt, 'FRONT_FUSE_TANK_PUMP', 1)
	pushSeqCmd(dt, 'FRONT_FUSE_TANK_PUMP', 0)
	pushSeqCmd(dt, 'FRONT_FUSE_TANK_PUMP_COVER', 0) # Cover close

	# Fuel shutoff valve button - On (fuel flow enabled)
	pushSeqCmd(dt, 'FRONT_ENG_FUEL_VALVE_PUMP_COVER', 1) # Cover open
	pushSeqCmd(dt, 'FRONT_ENG_FUEL_VALVE_PUMP', 1)
	pushSeqCmd(dt, 'FRONT_ENG_FUEL_VALVE_PUMP', 0)
	pushSeqCmd(dt, 'FRONT_ENG_FUEL_VALVE_PUMP_COVER', 0) # Cover close

	# STARTING ENGINE (37s)

	# Ignition switch - Start (2s)
	pushSeqCmd(dt, 'FRONT_CONT_ING_START', 2)
	pushSeqCmd(2, 'FRONT_CONT_ING_START', 1)
	
	# At 10% N2: power lever - Idle
	pushSeqCmd(5, 'scriptKeyboard', '{VK_RSHIFT down}{HOME down}{HOME up}{VK_RSHIFT up}')
	
	# Wait for engine instruments to stabilize (30s)
	pushSeqCmd(30, '', '', "Engine instruments - Stabilized")
	
	# Ground power off
	# GPU - Off
	pushSeqCmd(dt, 'FRONT_GPU', 1)
	pushSeqCmd(dt, 'FRONT_GPU', 0)
	# Ground power supply is off

	# Ground power supply - Off
	pushSeqCmd(dt, 'scriptKeyboard', '{\ down}{\ up}') # Must have separate down and up to register key press.
	pushSeqCmd(dt, 'scriptKeyboard', '{F8}')
	pushSeqCmd(dt, 'scriptKeyboard', '{F2}')
	pushSeqCmd(dt, 'scriptKeyboard', '{F2}')
	pushSeqCmd(13, '', '', "Ground power is off")

	# Generator - Reset, then On
	pushSeqCmd(dt, 'FRONT_GEN_SW', 0)
	pushSeqCmd(dt, 'FRONT_GEN_SW', 2)
	
	# IFF
	# IFF Master switch - NORM
	pushSeqCmd(dt, 'FRONT_IFF_MASTER_SW', 1) # 0 = EMER, 1 = NORM, 2 = LOW, 3 = STBY, 4 = OFF
	# IFF Mode 4 switch - ON
	pushSeqCmd(dt, 'FRONT_IFF_MODE4', 1)

	# Standby artificial horizon - Uncage
	pushSeqCmd(dt, 'FRONT_BAK_ADI_CAGE_BNT', 0) # Misspelling, "BNT" is correct.
	pushSeqCmd(dt, 'FRONT_BAK_ADI_CAGE_KNOB', int(int16 * 0.5))
	
	# Gunsight (C-101CC only)
	if airplaneName == 'C-101CC':
		# Gunsight
		# Gunsight - On, Man
		pushSeqCmd(dt, 'CC_FRONT_HUD_SIGHT', 1) # On
		pushSeqCmd(dt, 'CC_FRONT_HUD_DEPRESS_MODE', 1) # Man
		# NOTE The gunsight starts at 030 mils, and should be set to 010 mils initially for a waterline reference, but we can't guarantee the value on a cold restart after a shutdown, so leaving this to be set manually.
		## Gunsight depression - 010 mils (waterline)
		#pushSeqCmd(dt, 'CC_FRONT_HUD_DEPRESS_XX0', 'DEC')
		#pushSeqCmd(dt, 'CC_FRONT_HUD_DEPRESS_XX0', 'DEC')

	# Flaps - Takeoff
	pushSeqCmd(dt, 'FRONT_FLAP_SEL', 1)

	# Canopy - Close and lock
	pushSeqCmd(dt, 'FRONT_CANOPY_SAFE', 1) # Canopy safety latch
	pushSeqCmd(3.2, 'FRONT_CANOPY_LOCK', 1)
	
	# Air conditioning - Reset and On
	pushSeqCmd(dt, 'FRONT_AIR_COND_MASTER', 0)
	pushSeqCmd(dt, 'FRONT_AIR_COND_MASTER', 1)
	pushSeqCmd(dt, 'FRONT_AIR_COND_MASTER', 2)
	
	# Ejection seat safety pin (Front seat) - Remove
	pushSeqCmd(dt, 'FRONT_EJECT_HANDLE_COVER', 1)
	# Ejection seat safety pin (Rear seat) - Remove
	pushSeqCmd(dt, 'BACK_EJECT_HANDLE_COVER', 1)
	
	# Canopy Fracture Safety Pin (C-101CC only) (right console)
	if airplaneName == 'C-101CC':
		# Canopy fracture safety pin (Front seat) - Remove
		pushSeqCmd(dt, 'CC_FRONT_CANOPY_EMERG_FRAC_PIN', 1)
		# Canopy fracture safety pin (Rear seat) - Remove
		pushSeqCmd(dt, 'CC_BACK_CANOPY_EMERG_FRAC_PIN', 1)

	# Wait until the TARSYN sync is complete (total process time minus the difference between now and when the process started).
	tarsynSyncTimerEnd = tarsynSyncTime - (getLastSeqTime() - tarsynSyncTimerStart)
	pushSeqCmd(tarsynSyncTimerEnd, '', '', "TARSYN alignment complete")

	manualSteps = "Manual steps remaining: Set lights.  Tune radios.  Set navigation system.  Set altimeter to Q F E or Q N H."
	if airplaneName == 'C-101CC':
		manualSteps += "  Set gunsight to 0 1 0 mils for aircraft centerline."
	pushSeqCmd(dt, 'scriptSpeech', manualSteps)
	
	return seq


def HotStart(config, airplaneName = 'C-101CC'):
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
	
	int16 = 65535

	pushSeqCmd(0, '', '', "Running Hot Start sequence")

	# Accelerometer - Reset
	pushSeqCmd(dt, 'FRONT_GMETER_RESET', 1)
	pushSeqCmd(dt, 'FRONT_GMETER_RESET', 0)

	# Radios
	if airplaneName == 'C-101CC':
		# V/TVU-740 radio, front instrument panel
		# V/TVU-740 V/UHF radio - On
		pushSeqCmd(dt, 'CC_FRONT_UHF_FUNCT', 1) # 0 = OFF, 1 = A3 (on), 2 = A3+G (on+guard), 3 = DF (not implemented)
		
		#  VHF-20B radio, right console
		# VHF-20B VHF radio - On
		pushSeqCmd(dt, 'CC_FRONT_VHF_COMM_PW', 1) # 0 = OFF, 1 = PWR, 2 = TEST
	elif airplaneName == 'C-101EB':
		# ARC-164(V) radio, front instrument panel
		# ARC-164(V) UHF radio - On
		pushSeqCmd(dt, 'EB_FRONT_UHF_FUNCT', 1) # 0 = OFF, 1 = MAIN, 2 = BOTH, 3 = ADF
		
		# ARC-134 radio, right console
		# ARC-134 VHF radio - On
		pushSeqCmd(dt, 'EB_FRONT_VHF_COMM_PW', 1)
	
	# Gunsight (C-101CC only)
	if airplaneName == 'C-101CC':
		# Gunsight
		# Gunsight - On, Man
		pushSeqCmd(dt, 'CC_FRONT_HUD_SIGHT', 1) # On
		pushSeqCmd(dt, 'CC_FRONT_HUD_DEPRESS_MODE', 1) # Man
		# NOTE The gunsight starts at 030 mils, and should be set to 010 mils initially for a waterline reference, but we can't guarantee the value on a cold restart after a shutdown, so leaving this to be set manually.
		## Gunsight depression - 010 mils (waterline)
		#pushSeqCmd(dt, 'CC_FRONT_HUD_DEPRESS_XX0', 'DEC')
		#pushSeqCmd(dt, 'CC_FRONT_HUD_DEPRESS_XX0', 'DEC')

	# Flaps - Takeoff
	pushSeqCmd(dt, 'FRONT_FLAP_SEL', 1)

	manualSteps = "Manual steps remaining: Set lights.  Tune radios.  Set navigation system.  Set altimeter to Q F E or Q N H."
	if airplaneName == 'C-101CC':
		manualSteps += "  Set gunsight to 0 1 0 mils for aircraft centerline."
	pushSeqCmd(dt, 'scriptSpeech', manualSteps)
	
	return seq
