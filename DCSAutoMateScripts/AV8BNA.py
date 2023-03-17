# Return a Dictionary of script titles and their corresponding function names.  This is a list of scripts that users will be selecting from.  The module may have other utility functions that will not be run directly by the users.
def getScriptFunctions():
	return {
		'Cold Start': 'ColdStart',
		'Hot Start': 'HotStart',
	}

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
	
	int16 = 65535
	
	pushSeqCmd(0, '', '', "Running Cold Start sequence")
	pushSeqCmd(dt, 'CANOPY_HAND_L', 1)
	pushSeqCmd(dt, 'DECS_SW', 1)
	pushSeqCmd(dt, 'FUEL_SHUTOFF', 1)
	pushSeqCmd(dt, 'O2_SW', 1)
	#pushSeqCmd(dt, 'FUEL_PUMP_L', 2)
	#pushSeqCmd(dt, 'FUEL_PUMP_R', 2)
	#pushSeqCmd(dt, 'YAW_TRIM_SW', 1)
	#pushSeqCmd(dt, 'ANTI_SKID', 1)
	pushSeqCmd(dt, 'FLAP_POWER', 1)
	
	pushSeqCmd(dt, 'BATT_SW', 2)
	# Internal lights
	pushSeqCmd(dt, 'INST_LIGHTS', int16)
	pushSeqCmd(dt, 'CONSOLE_LIGHTS', int16)
	
	pushSeqCmd(dt, 'MPCD_L_BRIGHT', int16)
	pushSeqCmd(dt, 'MPCD_R_BRIGHT', int16)
	pushSeqCmd(dt, 'HUD_BRIGHT', int(int16 * 0.5))
	pushSeqCmd(dt, 'UFC_BRIGHT', int16)
	pushSeqCmd(dt, 'EDP_BRIGHT', int16)
	pushSeqCmd(dt, 'UFC_COM1_VOL', int(int16 * 0.5))
	pushSeqCmd(dt, 'UFC_COM2_VOL', int(int16 * 0.5))
	
	# Volume 68% is about lined up with the little mark.
	pushSeqCmd(dt, 'ICS_GND_VOL', int(int16 * 0.68))
	pushSeqCmd(dt, 'ICS_AUX_VOL', int(int16 * 0.68))
	
	# Starting engine
	pushSeqCmd(dt, 'ENG_START_SW', 1)
	pushSeqCmd(dt, 'M_Caution', 1) # NOTE Case sensitive
	pushSeqCmd(dt, 'M_Caution', 0)
	
	#pushSeqCmd(dt, '', '', 'Wait for 20 seconds for engine starter to spool up...')
	pushSeqCmd(20, '', '', 'Engine starter spooled up.')
	
	# Bump throttle forward past detent.  Note, must hold key down for a bit.
	pushSeqCmd(dt, 'scriptKeyboard', '{VK_ADD down}')
	pushSeqCmd(1, 'scriptKeyboard', '{VK_ADD up}') # Release after 1 second.
	
	# Then wait for engine to spool up.
	#pushSeqCmd(dt, '', '', 'Wait for 25 seconds for engine to spool up...')
	pushSeqCmd(25, '', '', 'Engine started.')
	
	# Go to EHSD screen.
	pushSeqCmd(dt, 'MPCD_L_2', 1) # EHSD OSB
	pushSeqCmd(dt, 'MPCD_L_2', 0) # release

	# Set INS to IFA, going through all the other positions on the way.
	for i in range(5):
		pushSeqCmd(dt, 'INS_MODE', i)
	# Reset Master Caution
	pushSeqCmd(dt, 'M_Caution', 1) # NOTE Case sensitive
	pushSeqCmd(dt, 'M_Caution', 0)

	# Set EHSD color to be readable in VR.
	pushSeqCmd(dt, 'MPCD_L_3', 1) # MAPM OSB
	pushSeqCmd(dt, 'MPCD_L_3', 0) # release
	pushSeqCmd(dt, 'MPCD_L_17', 1) # COLOR OSB
	pushSeqCmd(dt, 'MPCD_L_17', 0) # release
	pushSeqCmd(dt, 'MPCD_L_17', 1) # COLOR OSB
	pushSeqCmd(dt, 'MPCD_L_17', 0) # release
	pushSeqCmd(dt, 'MPCD_L_17', 1) # COLOR OSB
	pushSeqCmd(dt, 'MPCD_L_17', 0) # release
	pushSeqCmd(dt, 'MPCD_L_17', 1) # COLOR OSB
	pushSeqCmd(dt, 'MPCD_L_17', 0) # release
	pushSeqCmd(dt, 'MPCD_L_3', 1) # MAPM OSB
	pushSeqCmd(dt, 'MPCD_L_3', 0) # release
	
	# Turn on FLIR, DMT, and chaff/flare dispenser.
	pushSeqCmd(dt, 'FLIR', 1)
	pushSeqCmd(dt, 'DMT', 1)
	pushSeqCmd(dt, 'DECOY_CONTROL', 1) # 0 = OFF, 1 = AUT, 2 = UP, 3 = DWN, 4 = RWR
	# Volume 11141 is equivalent to one mousewheel-up on the knob (powered on, minimum volume)
	pushSeqCmd(dt, 'RWR_VOL', 11141)

	# Program chaff and flare dispensers to 10x, 1 second intervals
	# Defaults to Menu page when first starting up.
	pushSeqCmd(dt, 'MPCD_R_15', 1) # EW OSB
	pushSeqCmd(dt, 'MPCD_R_15', 0) # release
	pushSeqCmd(dt, 'MPCD_R_5', 1) # CHF OSB, changes mode from S (single) to P (program)
	pushSeqCmd(dt, 'MPCD_R_5', 0) # release
	pushSeqCmd(dt, 'MPCD_R_4', 1) # FLR OSB, changes mode from S (single) to P (program), other modes are M, G, R, unknown function
	pushSeqCmd(dt, 'MPCD_R_4', 0) # release
	pushSeqCmd(dt, 'MPCD_R_2', 1) # PROG OSB
	pushSeqCmd(dt, 'MPCD_R_2', 0) # release
	# PROG page starts with CHF selected.  Set salvo quantity to 10.
	pushSeqCmd(dt, 'ODU_OPT5', 1) # SQTY ODU OSB
	pushSeqCmd(dt, 'ODU_OPT5', 0) # release
	pushSeqCmd(dt, 'UFC_B1', 1) # UFC button 1
	pushSeqCmd(dt, 'UFC_B1', 0) # release
	pushSeqCmd(dt, 'UFC_B0', 1) # UFC button 0
	pushSeqCmd(dt, 'UFC_B0', 0) # release
	pushSeqCmd(dt, 'UFC_ENTER', 1) # UFC button 0
	pushSeqCmd(dt, 'UFC_ENTER', 0) # release
	# Then change to FLR and set quantity to 10.
	pushSeqCmd(dt, 'MPCD_R_8', 1) # FLR OSB
	pushSeqCmd(dt, 'MPCD_R_8', 0) # release
	pushSeqCmd(dt, 'ODU_OPT4', 1) # QTY ODU OSB
	pushSeqCmd(dt, 'ODU_OPT4', 0) # release
	pushSeqCmd(dt, 'UFC_B1', 1) # UFC button 1
	pushSeqCmd(dt, 'UFC_B1', 0) # release
	pushSeqCmd(dt, 'UFC_B0', 1) # UFC button 0
	pushSeqCmd(dt, 'UFC_B0', 0) # release
	pushSeqCmd(dt, 'UFC_ENTER', 1) # UFC button 0
	pushSeqCmd(dt, 'UFC_ENTER', 0) # release
	# Return to menu page.
	pushSeqCmd(dt, 'MPCD_R_18', 1) # Menu OSB
	pushSeqCmd(dt, 'MPCD_R_18', 0) # release
	
	# Set Low Altitude Warning to 50 ft.
	pushSeqCmd(dt, 'UFC_ALT', 1) # UFC ALT button
	pushSeqCmd(dt, 'UFC_ALT', 0) # release
	pushSeqCmd(dt, 'UFC_B5', 1) # UFC button 5
	pushSeqCmd(dt, 'UFC_B5', 0) # release
	pushSeqCmd(dt, 'UFC_B0', 1) # UFC button 0
	pushSeqCmd(dt, 'UFC_B0', 0) # release
	pushSeqCmd(dt, 'UFC_ENTER', 1) # UFC button 0
	pushSeqCmd(dt, 'UFC_ENTER', 0) # release

	# Fuel totalizer to TOT
	pushSeqCmd(dt, 'FUEL_SEL', 1) # Actual values: 0 = INT, 1 = TOT, 2 = FEED, 3 = BIT.  Should be: 0 = OUTBD, 1 = INBD, 2 = WING, 3 = INT, 4 = TOT, 5 = FEED, 6 = BIT

	# Increment 25 times to set bingo to 2500 lbs
	for i in range(25):
		pushSeqCmd(dt, 'BINGO_SET', 'INC')
	
	# External lights
	pushSeqCmd(dt, 'EXT_LIGHTS', 2) # 0 = OFF, 1 = NVG, 2 = NORM
	
	pushSeqCmd(dt, 'SEAT_SAFE_LEVER', 1)
	
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
	
	int16 = 65535
	
	pushSeqCmd(0, '', '', "Running Hot Start sequence")
	# Internal lights
	pushSeqCmd(dt, 'INST_LIGHTS', int16)
	pushSeqCmd(dt, 'CONSOLE_LIGHTS', int16)
	
	pushSeqCmd(dt, 'EDP_BRIGHT', int16)
	
	# Volume 68% is about lined up with the little mark.
	pushSeqCmd(dt, 'ICS_GND_VOL', int(int16 * 0.68))
	pushSeqCmd(dt, 'ICS_AUX_VOL', int(int16 * 0.68))
	
	# Turn on FLIR, DMT, and chaff/flare dispenser.
	pushSeqCmd(dt, 'DECOY_CONTROL', 1) # 0 = OFF, 1 = AUT, 2 = UP, 3 = DWN, 4 = RWR
	# Volume 11141 is equivalent to one mousewheel-up on the knob (powered on, minimum volume)
	pushSeqCmd(dt, 'RWR_VOL', 11141)
	
	# Increment 25 times to set bingo to 2500 lbs
	for i in range(25):
		pushSeqCmd(dt, 'BINGO_SET', 'INC')
	
	# External lights
	pushSeqCmd(dt, 'EXT_LIGHTS', 2) # 0 = OFF, 1 = NVG, 2 = NORM
	
	return seq
	