# Return a Dictionary of script titles and their corresponding function names.  This is a list of scripts that users will be selecting from.  The module may have other utility functions that will not be run directly by the users.
def getScriptFunctions():
	return {
		'Cold Start': 'ColdStart',
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
		
	def getLastSeqTime():
		nonlocal seq
		return float(seq[len(seq) - 1]['time'])

	int16 = 65535
	apuStartTime = 25 # APU takes 25 seconds to start.
	engineStartTime = 55 # Engines each take 55 seconds to start.
	engineSpoolTime = 10 # Engines take 10 seconds to spool up from idle to flight-ready (collective twist grip max).
	
	# Start sequence
	pushSeqCmd(0, '', '', "Running Cold Start sequence.")
	pushSeqCmd(dt, '', '', 'Set collective full down.')
	pushSeqCmd(dt, 'scriptSpeech', 'Set collective full down.')

	#pushSeqCmd(dt, '', '', "Radio/ICS switch (Pilot) - ICS (allows rearming)")
	pushSeqCmd(dt, 'PLT_SPU8_ICS', 1)

	#pushSeqCmd(dt, '', '', "Cockpit Doors - Close")
	pushSeqCmd(dt, 'scriptKeyboard', '{VK_LCONTROL down}')
	if config['dvorak']:
		pushSeqCmd(dt, 'scriptKeyboard', '{j down}{j up}') # QWERTY 'c', Dvorak 'j'.
	else:
		pushSeqCmd(dt, 'scriptKeyboard', '{c down}{c up}') # QWERTY 'c', Dvorak 'j'.
	pushSeqCmd(dt, 'scriptKeyboard', '{VK_LCONTROL up}')

	#pushSeqCmd(dt, '', '', "Left Engine Stop lever - OFF")
	pushSeqCmd(dt, 'PLT_ENG_STOP_L', 0)
	#pushSeqCmd(dt, '', '', "Right Engine Stop lever - OFF")
	pushSeqCmd(dt, 'PLT_ENG_STOP_R', 0)
	#pushSeqCmd(dt, '', '', "Rotor Brake - OFF")
	pushSeqCmd(dt, 'PLT_ROTOR_BRAKE', 0)
	
	# Left and Right throttles to min, then auto
	pushSeqCmd(dt, 'PLT_ENG_THROTTLE_L', '-'+str(int16))
	pushSeqCmd(0, 'PLT_ENG_THROTTLE_R', '-'+str(int16))
	for i in range(8): # 8x +3000 works, though trial and error.
		pushSeqCmd(dt, 'PLT_ENG_THROTTLE_L', '+3000')
		pushSeqCmd(dt, 'PLT_ENG_THROTTLE_R', '+3000')
	# Twist grip to min (DECR)
	pushSeqCmd(dt, 'scriptKeyboard', '{PGDN down}')
	pushSeqCmd(2, 'scriptKeyboard', '{PGDN up}') # Hold down for 2 seconds
	# Collective full down
	pushSeqCmd(dt, 'scriptKeyboard', '{VK_SUBTRACT down}')
	pushSeqCmd(2, 'scriptKeyboard', '{VK_SUBTRACT up}') # Hold down for 2 seconds
	
	# Electric Power
	#pushSeqCmd(dt, '', '', "Right Battery - ON")
	pushSeqCmd(dt, 'PLT_D_BATT_R', 1)
	#pushSeqCmd(dt, '', '', "Left Battery - ON")
	pushSeqCmd(dt, 'PLT_D_BATT_L', 1)
	#pushSeqCmd(dt, '', '', "DC Voltmeter knob - BATT")
	pushSeqCmd(dt, 'PLT_D_VOLT_KNB', 2)
	#pushSeqCmd(dt, '', '', "Inverter PO-750A - ON")
	pushSeqCmd(dt, 'PLT_A_INVERT_115_CV', 1) # Cover open
	pushSeqCmd(dt, 'PLT_A_INVERT_115', 1) # Switch
	#pushSeqCmd(dt, '', '', "Left CBs - ON (gang bar)")
	pushSeqCmd(dt, 'PLT_CB_L_ALL', 1)
	pushSeqCmd(dt, 'PLT_CB_L_ALL', 0)
	#pushSeqCmd(dt, '', '', "Right CBs - ON (gang bar)")
	pushSeqCmd(dt, 'PLT_CB_R_ALL', 1)
	pushSeqCmd(dt, 'PLT_CB_R_ALL', 0)

	# POWER FROM BATT (Network To Batteries) - Powers onboard systems from batteries?
	#pushSeqCmd(dt, '', '', "Power From Batt (Network To Batteries) switch - ON")
	pushSeqCmd(dt, 'PLT_D_NET_BATT_CV', 1) # Cover open
	pushSeqCmd(dt, 'PLT_D_NET_BATT', 1) # Switch

	# Hydraulic system (starts on MAIN)
	##pushSeqCmd(dt, '', '', "Main/Auxiliary Hydraulic Switch - MAIN")
	#pushSeqCmd(dt, device = devices.HYDRO_SYS_INTERFACE, action = hydraulic_commands.MainHydroCover, value = 1)
	#pushSeqCmd(dt, device = devices.HYDRO_SYS_INTERFACE, action = hydraulic_commands.MainHydro, value = 1)
	#pushSeqCmd(dt, device = devices.HYDRO_SYS_INTERFACE, action = hydraulic_commands.MainHydroCover, value = 0)

	# Seal and pressurize cabin
	#pushSeqCmd(dt, '', '', "Cabin Press valve - OPEN (CCW)")
	pushSeqCmd(dt, 'PLT_CABIN_PRESS', 0)
	#pushSeqCmd(dt, '', '', "Cabin Depress switch - ON")
	pushSeqCmd(dt, 'PLT_CABIN_UNSEAL', 1)
	#pushSeqCmd(dt, '', '', "Blowdown Conditioning switch - CONDITION")
	pushSeqCmd(dt, 'PLT_AC_MODE', 2)

	# Fuel System
	#pushSeqCmd(dt, '', '', "Service (Feed) Tanks 1 switch - ON")
	pushSeqCmd(dt, 'PLT_FEED_TANK1', 1)
	#pushSeqCmd(dt, '', '', "Service (Feed) Tanks 2 switch - ON")
	pushSeqCmd(dt, 'PLT_FEED_TANK2', 1)
	#pushSeqCmd(dt, '', '', "Fuel Shutoff Left switch - ON")
	pushSeqCmd(dt, 'PLT_FIRE_VALVE_L_CV', 1) # Cover open
	pushSeqCmd(dt, 'PLT_FIRE_VALVE_L', 1) # Switch
	pushSeqCmd(dt, 'PLT_FIRE_VALVE_L_CV', 0) # Cover close
	#pushSeqCmd(dt, '', '', "Fuel Shutoff Right switch - ON")
	pushSeqCmd(dt, 'PLT_FIRE_VALVE_R_CV', 1) # Cover open
	pushSeqCmd(dt, 'PLT_FIRE_VALVE_R', 1) # Switch
	pushSeqCmd(dt, 'PLT_FIRE_VALVE_R_CV', 0) # Cover close
	#pushSeqCmd(dt, '', '', "Fuel Crossfeed (Delimiter) switch - ON") # "Fuel Delimiter Valve"
	pushSeqCmd(dt, 'PLT_FUEL_DELIM', 1)
	#pushSeqCmd(dt, '', '', "Service Tank Pumps 1, 2, 4, and 5 switches - ON")
	pushSeqCmd(dt, 'PLT_PUMP_TANK1', 1)
	pushSeqCmd(dt, 'PLT_PUMP_TANK2', 1)
	pushSeqCmd(dt, 'PLT_PUMP_TANK4', 1)
	pushSeqCmd(dt, 'PLT_PUMP_TANK5', 1)
	
	# Fire Extinguisher
	#pushSeqCmd(dt, '', '', "Fire Extinguisher Power switch - ON")
	pushSeqCmd(dt, 'PLT_FIRE_EX_PW', 1)
	#pushSeqCmd(dt, '', '', "Fire Extinguisher Control switch - ON")
	pushSeqCmd(dt, 'PLT_FIRE_EX_CONTROL', 1)
	
	# Start APU
	#pushSeqCmd(dt, '', '', "Starting APU (25s)")
	pushSeqCmd(dt, 'PLT_APU_CRANK', 0) # 0 = START, 1 = CRANK, 2 = FALSE START
	pushSeqCmd(dt, 'PLT_APU_START', 1) # Press
	pushSeqCmd(dt, 'PLT_APU_START', 0) # Release
	pushSeqCmd(apuStartTime, '', '', 'APU started')
	
	# Prepare for engine start
	pushSeqCmd(dt, 'PLT_ENG_SEL_LAUNCH', 0) # 0 = START, 1 = CRANK
	
	# Start Left Engine
	#pushSeqCmd(dt, '', '', "Starting Left Engine (55s)")
	#pushSeqCmd(dt, '', '', "Engine Start switch # LEFT")
	pushSeqCmd(dt, 'PLT_ENG_SEL_LR', 1) # 0 = RIGHT, 1 = LEFT
	#pushSeqCmd(dt, '', '', "Engine Start button # Press")
	pushSeqCmd(dt, 'PLT_ENG_START', 1) # Press
	pushSeqCmd(dt, 'PLT_ENG_START', 0) # Release
	pushSeqCmd(engineStartTime, '', '', 'Left engine started')

	# Start Right Engine
	#pushSeqCmd(dt, '', '', "Starting Right Engine (55s)")
	#pushSeqCmd(dt, '', '', "Engine Start switch # RIGHT")
	pushSeqCmd(dt, 'PLT_ENG_SEL_LR', 0) # 0 = RIGHT, 1 = LEFT
	#pushSeqCmd(dt, '', '', "Engine Start button # Press")
	pushSeqCmd(dt, 'PLT_ENG_START', 1) # Press
	pushSeqCmd(dt, 'PLT_ENG_START', 0) # Release
	pushSeqCmd(engineStartTime, '', '', 'Right engine started')

	# Spool Up
	#pushSeqCmd(dt, '', '', "Collective Throttle - Set to max (INCR, right)")
	# Twist grip to min (DECR)
	pushSeqCmd(dt, 'scriptKeyboard', '{PGUP down}')
	pushSeqCmd(2, 'scriptKeyboard', '{PGUP up}') # Hold down for 2 seconds
	pushSeqCmd(engineSpoolTime, '', '', "Engines Spooled Up")

	# Generators and other electrics
	#pushSeqCmd(dt, '', '', "Left Generator switch - ON")
	pushSeqCmd(dt, 'PLT_A_GEN_L', 1)
	#pushSeqCmd(dt, '', '', "Right Generator switch - ON")
	pushSeqCmd(dt, 'PLT_A_GEN_R', 1)
	#pushSeqCmd(dt, '', '', "115V Transformer switch - MAIN")
	pushSeqCmd(dt, 'PLT_A_TRANS_115', 2)
	#pushSeqCmd(dt, '', '', "36V Transformer switch - MAIN")
	pushSeqCmd(dt, 'PLT_A_TRANS_36', 2)
	#pushSeqCmd(dt, '', '', "Left Rectifier switch - ON")
	pushSeqCmd(dt, 'PLT_D_RECT_L', 1)
	#pushSeqCmd(dt, '', '', "Right Rectifier switch - ON")
	pushSeqCmd(dt, 'PLT_D_RECT_R', 1)
	#pushSeqCmd(dt, '', '', "AC Voltmeter knob - LEFT GENERATORS C-A")
	pushSeqCmd(dt, 'PLT_A_VOLT_KNB', 5)
	#pushSeqCmd(dt, '', '', "Inverter PO-750A - OFF")
	pushSeqCmd(dt, 'PLT_A_INVERT_115', 0) # Switch
	pushSeqCmd(dt, 'PLT_A_INVERT_115_CV', 0) # Cover close

	#pushSeqCmd(dt, '', '', "APU Stop button - Press")
	pushSeqCmd(dt, 'PLT_APU_STOP', 1)
	pushSeqCmd(dt, 'PLT_APU_STOP', 0)

	#pushSeqCmd(dt, '', '', "Power From Batt (Network To Batteries) switch - OFF")
	pushSeqCmd(dt, 'PLT_D_NET_BATT', 0) # Switch
	pushSeqCmd(dt, 'PLT_D_NET_BATT_CV', 0) # Cover close

	# Left Panel switches
	#pushSeqCmd(dt, '', '', "SPUU (Tail Roter Pitch Limiter) Power switch - ON")
	pushSeqCmd(dt, 'PLT_SPUU_POWER', 1)
	#pushSeqCmd(dt, '', '', "Radar Altimeter (RV-5) Power switch - ON")
	pushSeqCmd(dt, 'PLT_RV5_PW', 1)
	#pushSeqCmd(dt, '', '', "Doppler (DISS-15) switch - ON")
	pushSeqCmd(dt, 'PLT_DISS_PW', 1)
	#pushSeqCmd(dt, '', '', "Vert Gyro 1 switch - ON")
	pushSeqCmd(dt, 'PLT_GYRO_1_PWR', 1)
	#pushSeqCmd(dt, '', '', "Vert Gyro 2 switch - ON")
	pushSeqCmd(dt, 'PLT_GYRO_2_PWR', 1)
	#pushSeqCmd(dt, '', '', "Vert Gyro 1 Cage button - Press for 2 seconds")
	pushSeqCmd(dt, 'PLT_GYRO_1_CAGE', 1) # Press
	pushSeqCmd(2, 'PLT_GYRO_1_CAGE', 0) # Release after 2 seconds
	#pushSeqCmd(dt, '', '', "Vert Gyro 2 Cage button - Press for 2 seconds")
	pushSeqCmd(dt, 'PLT_GYRO_2_CAGE', 1) # Press
	pushSeqCmd(2, 'PLT_GYRO_2_CAGE', 0) # Release after 2 seconds
	#pushSeqCmd(dt, '', '', "Comp. System (GREBEN) switch - ON")
	pushSeqCmd(dt, 'PLT_GREB_PW', 1)
	#pushSeqCmd(1,{device = devices.KM_2, action =  avKM_2_commands.calc_magn_var, value = 1, message = _("set magnetic declination on KM-2"), message_timeout = std_message_timeout) # This is done automatically by Petrovich??
	#pushSeqCmd(dt, '', '', "Intercom (SPU-8) Network 1 switch - ON")
	pushSeqCmd(dt, 'PLT_SPU8_1_PW', 1)
	#pushSeqCmd(dt, '', '', "Intercom (SPU-8) Network 2 switch - ON")
	pushSeqCmd(dt, 'PLT_SPU8_2_PW', 1)
	#pushSeqCmd(dt, '', '', "HF Radio (JADRO-1A) switch - ON")
	pushSeqCmd(dt, 'PLT_JADRO_PW', 1)
	#pushSeqCmd(dt, '', '', "R-828 Radio switch - ON")
	pushSeqCmd(dt, 'PLT_R828_PW', 1)
	#pushSeqCmd(dt, '', '', "R-863 Radio switch - ON")
	pushSeqCmd(dt, 'PLT_R863_PW', 1)
	#pushSeqCmd(dt, '', '', "Blink (Flasher) switch - ON")
	pushSeqCmd(dt, 'PLT_BLINK_SW', 1)
	
	# IFF
	#pushSeqCmd(dt, '', '', "IFF switch - ON")
	pushSeqCmd(dt, 'PLT_IFF_PW', 1)
	
	# JADRO-1A Radio
	#pushSeqCmd(dt, '', '', "JADRO-1A Radio Mode knob - AM")
	pushSeqCmd(dt, 'PLT_JADRO_MODUL', 2) # 0 = OFF, 1 = STB (SSB), 2 = AM
	
	# RWR
	#pushSeqCmd(dt, '', '', "RWR switch - ON")
	pushSeqCmd(dt, 'PLT_RWR_PW', 1)
	
	# PU-38 GREBEN compass system
	#pushSeqCmd(dt, '', '', "GREBEN Tune/Oper switch - OPER")
	pushSeqCmd(dt, 'PLT_GREB_SETUP', 1)
	#pushSeqCmd(dt, '', '', "GREBEN Match (Sync) button - Press for 3 seconds")
	pushSeqCmd(dt, 'PLT_GREB_MATCH', 1)
	pushSeqCmd(3, 'PLT_GREB_MATCH', 0)
	#pushSeqCmd(dt, '', '', "GREBEN Mode switch - GYRO")
	pushSeqCmd(dt, 'PLT_GREB_MODE', 1)
	
	# Autopilot
	#pushSeqCmd(dt, '', '', "Autopilot Roll Channel button - ON")
	pushSeqCmd(dt, 'PLT_SAU_K_ON', 1) # Press
	pushSeqCmd(dt, 'PLT_SAU_K_ON', 0) # Release
	#pushSeqCmd(dt, '', '', "Autopilot Pitch Channel button - ON")
	pushSeqCmd(dt, 'PLT_SAU_T_ON', 1) # Press
	pushSeqCmd(dt, 'PLT_SAU_T_ON', 0) # Release

	# Gunsight and Weapons Panel
	#pushSeqCmd(dt, '', '', "Sight Power switch - ON") # Weapons panel.
	pushSeqCmd(dt, 'PLT_PUVL_WPN_SIGHT', 1)
	#pushSeqCmd(dt, '', '', "Range Insert switch - AUTO") # Weapons panel.
	pushSeqCmd(dt, 'PLT_PUVL_SIGHT_DIST', 1)
	#pushSeqCmd(dt, '', '', "Sight (Ranging) Mode switch - AUTO") # Sight base.
	pushSeqCmd(dt, 'PLT_ASP17_MODE_MAN_AUTO', 1)
	#pushSeqCmd(dt, '', '', "Sync/Async switch - ASYNC") # Sight base.
	pushSeqCmd(dt, 'PLT_ASP17_MODE_SYNC_ASYNC', 0)
	#pushSeqCmd(dt, '', '', "Fire Ctrl (Master Arm) switch - ON") # Weapons panel.
	pushSeqCmd(dt, 'PLT_PUVL_FIRE_CONTROL', 1)
	#pushSeqCmd(dt, '', '', "MG Rate (Cannon ROF) switch - INCR") # Weapons panel
	pushSeqCmd(dt, 'PLT_PUVL_CANNON_FIRE_RATE', 1)
	#pushSeqCmd(dt, '', '', "Fixed Crosshair Brightness - 20%") # Sight base.
	pushSeqCmd(dt, 'PLT_ASP17_GRID_BRIGHT_ADJ', int(int16 * 0.2))
	#pushSeqCmd(dt, '', '', "Aux Stores Lights switch - ON") # Right angled panel bottom.
	pushSeqCmd(dt, 'PLT_ARM_RED_L_SW', 1)

	# Pilot-Operator (front) seat
	#pushSeqCmd(dt, '', '', "Setting up Pilot-Operator switches...")
	#pushSeqCmd(dt, '', '', "Intercom (SPU-8) Power switch - ON") # Popup switch label says "SPUU Power ON/OFF" but I think that's wrong...
	pushSeqCmd(dt, 'OP_SPU8_SPUU_PW', 1)
	#pushSeqCmd(dt, '', '', "Safety Switches (Master Arm) gang bar - ON")
	pushSeqCmd(dt, 'OP_MAIN_WPN_SAVE', 1)
	#pushSeqCmd(dt, '', '', "Missile Power switch - ON")
	pushSeqCmd(dt, 'OP_MISSL_PW', 1)
	#pushSeqCmd(dt, '', '', "FDI (ADI) switch - ON")
	pushSeqCmd(dt, 'OP_ADI_SW', 1)
	#pushSeqCmd(dt, '', '', "Cplr/Distr switch - ON") # turns on gunsight?
	pushSeqCmd(dt, 'OP_USR_PW', 1)
	#pushSeqCmd(dt, '', '', "Missile Station Selector (SCHO) power switch - ON")
	pushSeqCmd(dt, 'OP_SCHO_PW', 1)
	#pushSeqCmd(dt, '', '', "Guid. Unit Power switch - ON")
	pushSeqCmd(dt, 'OP_SIGHT_PW', 1)
	#pushSeqCmd(dt, '', '', "Burst Length - SHORT")
	pushSeqCmd(dt, 'OP_BURST_LENGTH', 2)
	#pushSeqCmd(dt, '', '', "Fxd MG-30 Rate (Cannon ROF) switch - INCR") # Weapons panel
	pushSeqCmd(dt, 'OP_CAN_RATE', 1)
	#pushSeqCmd(dt, device = devices.I9K113, action = i9K113_commands.Command_NABL, value = 1) # OBSERVE
	#pushSeqCmd(dt, device = devices.I9K113, action = i9K113_commands.Command_STVORKI, value = 1) # Sight Doors
	#pushSeqCmd(dt, '', '', "Done with Pilot-Operator switches")

	# RWR test beep
	#pushSeqCmd(dt, '', '', "RWR test beep")
	pushSeqCmd(dt, 'PLT_RWR_SIGNAL', 1) # Turn on RWR audio
	pushSeqCmd(dt, 'PLT_RWR_CHECK', 1) # Press (makes a beep)
	pushSeqCmd(dt, 'PLT_RWR_CHECK', 0) # Release
	pushSeqCmd(dt, 'PLT_RWR_SIGNAL', 0) # Turn off RWR audio

	# Fans
	#pushSeqCmd(dt, '', '', "Pilot and Operator Fans - ON")
	pushSeqCmd(dt, 'PLT_FAN', 1)
	pushSeqCmd(dt, 'OP_FAN', 1)

	#pushSeqCmd(dt, '', '', "HAVOC'S QUICK AUTOSTART IS COMPLETE")
	#pushSeqCmd(dt, '', '', "Manual steps remaining:")
	#pushSeqCmd(dt, '', '', "Lights ... As needed")
	#pushSeqCmd(dt, '', '', "Radios ... As needed")
	#pushSeqCmd(dt, '', '', "Navigation ... As needed")
	#pushSeqCmd(dt, '', '', "Altimeter ... Set to match QFE (airfield elevation) or QNH (sea level altitude) as desired")
	pushSeqCmd(dt, 'scriptSpeech', "Manual steps remaining: Set lights.  Tune radios.  Set doppler navigation.  Set altimeter to Q F E or Q N H.")
	
	return seq
