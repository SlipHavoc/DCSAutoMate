# Return a Dictionary of script data.  The 'scripts' key is a list of scripts that users will be selecting from.  Each script has an associated 'function', which is the name of the function in this file that will be called to generate the command sequence, and a dictionary of 'vars' that the user will be prompted to choose from before running the script, and will be passed into the sequence generating function.
def getScriptData():
	return {
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
		],
	}

# Returns 0-65535 scaled by multiple (0-1), eg for 50% call int16(0.5)
def int16(mult = 1):
	int16 = 65535
	return int(mult * int16)

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

	apuStartTime = 25 # APU takes 25 seconds to start.
	engineStartTime = 55 # Engines each take 55 seconds to start.
	engineSpoolTime = 10 # Engines take 10 seconds to spool up from idle to flight-ready (collective twist grip max).

	# Start sequence
	pushSeqCmd(0, '', '', "Running Cold Start sequence.")
	pushSeqCmd(dt, '', '', 'Set collective full down.')
	pushSeqCmd(dt, 'scriptSpeech', 'Set collective full down.')

	# Radio/ICS switch (Pilot) - ICS (allows rearming)
	pushSeqCmd(dt, 'PLT_SPU8_ICS', 1)

	# Cockpit Doors - Close
	pushSeqCmd(dt, 'scriptKeyboard', 'LCtrl down')
	pushSeqCmd(dt, 'scriptKeyboard', 'c')
	pushSeqCmd(dt, 'scriptKeyboard', 'LCtrl up')

	# Left Engine Stop lever - OFF
	pushSeqCmd(dt, 'PLT_ENG_STOP_L', 0)
	# Right Engine Stop lever - OFF
	pushSeqCmd(dt, 'PLT_ENG_STOP_R', 0)
	# Rotor Brake - OFF
	pushSeqCmd(dt, 'PLT_ROTOR_BRAKE', 0)

	# Left and Right throttles to min, then auto
	pushSeqCmd(dt, 'PLT_ENG_THROTTLE_L', '-'+str(int16()))
	pushSeqCmd(0, 'PLT_ENG_THROTTLE_R', '-'+str(int16()))
	for i in range(8): # 8x +3000 works, though trial and error.
		pushSeqCmd(dt, 'PLT_ENG_THROTTLE_L', '+3000')
		pushSeqCmd(dt, 'PLT_ENG_THROTTLE_R', '+3000')
	# Twist grip to min (DECR)
	pushSeqCmd(dt, 'scriptKeyboard', 'pgdn down')
	pushSeqCmd(2, 'scriptKeyboard', 'pgdn up') # Hold down for 2 seconds
	# Collective full down
	pushSeqCmd(dt, 'scriptKeyboard', 'subtract down') # Numpad -
	pushSeqCmd(2, 'scriptKeyboard', 'subtract up') # Hold down for 2 seconds

	# Electric Power
	# Right Battery - ON
	pushSeqCmd(dt, 'PLT_D_BATT_R', 1)
	# Left Battery - ON
	pushSeqCmd(dt, 'PLT_D_BATT_L', 1)
	# DC Voltmeter knob - BATT
	pushSeqCmd(dt, 'PLT_D_VOLT_KNB', 2)
	# Inverter PO-750A - ON
	pushSeqCmd(dt, 'PLT_A_INVERT_115_CV', 1) # Cover open
	pushSeqCmd(dt, 'PLT_A_INVERT_115', 1) # Switch
	# Left CBs - ON (gang bar)
	pushSeqCmd(dt, 'PLT_CB_L_ALL', 1)
	pushSeqCmd(dt, 'PLT_CB_L_ALL', 0)
	# Right CBs - ON (gang bar)
	pushSeqCmd(dt, 'PLT_CB_R_ALL', 1)
	pushSeqCmd(dt, 'PLT_CB_R_ALL', 0)

	# POWER FROM BATT (Network To Batteries) - Powers onboard systems from batteries?
	# Power From Batt (Network To Batteries) switch - ON
	pushSeqCmd(dt, 'PLT_D_NET_BATT_CV', 1) # Cover open
	pushSeqCmd(dt, 'PLT_D_NET_BATT', 1) # Switch

	# Hydraulic system (starts on MAIN)
	## Main/Auxiliary Hydraulic Switch - MAIN
	#pushSeqCmd(dt, device = devices.HYDRO_SYS_INTERFACE, action = hydraulic_commands.MainHydroCover, value = 1)
	#pushSeqCmd(dt, device = devices.HYDRO_SYS_INTERFACE, action = hydraulic_commands.MainHydro, value = 1)
	#pushSeqCmd(dt, device = devices.HYDRO_SYS_INTERFACE, action = hydraulic_commands.MainHydroCover, value = 0)

	# Seal and pressurize cabin
	# Cabin Press valve - OPEN (CCW)
	pushSeqCmd(dt, 'PLT_CABIN_PRESS', 0)
	# Cabin Depress switch - ON
	pushSeqCmd(dt, 'PLT_CABIN_UNSEAL', 1)
	# Blowdown Conditioning switch - CONDITION
	pushSeqCmd(dt, 'PLT_AC_MODE', 2)

	# Fuel System
	# Service (Feed) Tanks 1 switch - ON
	pushSeqCmd(dt, 'PLT_FEED_TANK1', 1)
	# Service (Feed) Tanks 2 switch - ON
	pushSeqCmd(dt, 'PLT_FEED_TANK2', 1)
	# Fuel Shutoff Left switch - ON
	pushSeqCmd(dt, 'PLT_FIRE_VALVE_L_CV', 1) # Cover open
	pushSeqCmd(dt, 'PLT_FIRE_VALVE_L', 1) # Switch
	pushSeqCmd(dt, 'PLT_FIRE_VALVE_L_CV', 0) # Cover close
	# Fuel Shutoff Right switch - ON
	pushSeqCmd(dt, 'PLT_FIRE_VALVE_R_CV', 1) # Cover open
	pushSeqCmd(dt, 'PLT_FIRE_VALVE_R', 1) # Switch
	pushSeqCmd(dt, 'PLT_FIRE_VALVE_R_CV', 0) # Cover close
	# Fuel Crossfeed (Delimiter) switch - ON # "Fuel Delimiter Valve"
	pushSeqCmd(dt, 'PLT_FUEL_DELIM', 1)
	# Service Tank Pumps 1, 2, 4, and 5 switches - ON
	pushSeqCmd(dt, 'PLT_PUMP_TANK1', 1)
	pushSeqCmd(dt, 'PLT_PUMP_TANK2', 1)
	pushSeqCmd(dt, 'PLT_PUMP_TANK4', 1)
	pushSeqCmd(dt, 'PLT_PUMP_TANK5', 1)

	# Fire Extinguisher
	# Fire Extinguisher Power switch - ON
	pushSeqCmd(dt, 'PLT_FIRE_EX_PW', 1)
	# Fire Extinguisher Control switch - ON
	pushSeqCmd(dt, 'PLT_FIRE_EX_CONTROL', 1)

	# Start APU
	# Starting APU (25s)
	pushSeqCmd(dt, 'PLT_APU_CRANK', 0) # 0 = START, 1 = CRANK, 2 = FALSE START
	pushSeqCmd(dt, 'PLT_APU_START', 1) # Press
	pushSeqCmd(dt, 'PLT_APU_START', 0) # Release
	pushSeqCmd(apuStartTime, '', '', 'APU started')

	# Prepare for engine start
	pushSeqCmd(dt, 'PLT_ENG_SEL_LAUNCH', 0) # 0 = START, 1 = CRANK

	# Starting Left Engine (55s)
	# Engine Start switch - LEFT
	pushSeqCmd(dt, 'PLT_ENG_SEL_LR', 1) # 0 = RIGHT, 1 = LEFT
	# Engine Start button - Press
	pushSeqCmd(dt, 'PLT_ENG_START', 1) # Press
	pushSeqCmd(dt, 'PLT_ENG_START', 0) # Release
	pushSeqCmd(engineStartTime, '', '', 'Left engine started')

	# Starting Right Engine (55s)
	# Engine Start switch - RIGHT
	pushSeqCmd(dt, 'PLT_ENG_SEL_LR', 0) # 0 = RIGHT, 1 = LEFT
	# Engine Start button - Press
	pushSeqCmd(dt, 'PLT_ENG_START', 1) # Press
	pushSeqCmd(dt, 'PLT_ENG_START', 0) # Release
	pushSeqCmd(engineStartTime, '', '', 'Right engine started')

	# Spool Up
	# Collective Throttle - Set to max (INCR, right)
	# Twist grip to max (INCR)
	pushSeqCmd(dt, 'scriptKeyboard', 'pgup down')
	pushSeqCmd(2, 'scriptKeyboard', 'pgup up') # Hold down for 2 seconds
	pushSeqCmd(engineSpoolTime, '', '', "Engines Spooled Up")

	# Generators and other electrics
	# Left Generator switch - ON
	pushSeqCmd(dt, 'PLT_A_GEN_L', 1)
	# Right Generator switch - ON
	pushSeqCmd(dt, 'PLT_A_GEN_R', 1)
	# 115V Transformer switch - MAIN
	pushSeqCmd(dt, 'PLT_A_TRANS_115', 2)
	# 36V Transformer switch - MAIN
	pushSeqCmd(dt, 'PLT_A_TRANS_36', 2)
	# Left Rectifier switch - ON
	pushSeqCmd(dt, 'PLT_D_RECT_L', 1)
	# Right Rectifier switch - ON
	pushSeqCmd(dt, 'PLT_D_RECT_R', 1)
	# AC Voltmeter knob - LEFT GENERATORS C-A
	pushSeqCmd(dt, 'PLT_A_VOLT_KNB', 5)
	# Inverter PO-750A - OFF
	pushSeqCmd(dt, 'PLT_A_INVERT_115', 0) # Switch
	pushSeqCmd(dt, 'PLT_A_INVERT_115_CV', 0) # Cover close

	# APU Stop button - Press
	pushSeqCmd(dt, 'PLT_APU_STOP', 1)
	pushSeqCmd(dt, 'PLT_APU_STOP', 0)

	# Power From Batt (Network To Batteries) switch - OFF
	pushSeqCmd(dt, 'PLT_D_NET_BATT', 0) # Switch
	pushSeqCmd(dt, 'PLT_D_NET_BATT_CV', 0) # Cover close

	# Left Panel switches
	# SPUU (Tail Roter Pitch Limiter) Power switch - ON
	pushSeqCmd(dt, 'PLT_SPUU_POWER', 1)
	# Radar Altimeter (RV-5) Power switch - ON
	pushSeqCmd(dt, 'PLT_RV5_PW', 1)
	# Doppler (DISS-15) switch - ON
	pushSeqCmd(dt, 'PLT_DISS_PW', 1)
	# Vert Gyro 1 switch - ON
	pushSeqCmd(dt, 'PLT_GYRO_1_PWR', 1)
	# Vert Gyro 2 switch - ON
	pushSeqCmd(dt, 'PLT_GYRO_2_PWR', 1)
	# Vert Gyro 1 Cage button - Press for 2 seconds
	pushSeqCmd(dt, 'PLT_GYRO_1_CAGE', 1) # Press
	pushSeqCmd(2, 'PLT_GYRO_1_CAGE', 0) # Release after 2 seconds
	# Vert Gyro 2 Cage button - Press for 2 seconds
	pushSeqCmd(dt, 'PLT_GYRO_2_CAGE', 1) # Press
	pushSeqCmd(2, 'PLT_GYRO_2_CAGE', 0) # Release after 2 seconds
	# Comp. System (GREBEN) switch - ON
	pushSeqCmd(dt, 'PLT_GREB_PW', 1)
	#pushSeqCmd(1,{device = devices.KM_2, action =  avKM_2_commands.calc_magn_var, value = 1, message = _("set magnetic declination on KM-2, message_timeout = std_message_timeout) # This is done automatically by Petrovich??
	# Intercom (SPU-8) Network 1 switch - ON
	pushSeqCmd(dt, 'PLT_SPU8_1_PW', 1)
	# Intercom (SPU-8) Network 2 switch - ON
	pushSeqCmd(dt, 'PLT_SPU8_2_PW', 1)
	# HF Radio (JADRO-1A) switch - ON
	pushSeqCmd(dt, 'PLT_JADRO_PW', 1)
	# R-828 Radio switch - ON
	pushSeqCmd(dt, 'PLT_R828_PW', 1)
	# R-863 Radio switch - ON
	pushSeqCmd(dt, 'PLT_R863_PW', 1)
	# Blink (Flasher) switch - ON
	pushSeqCmd(dt, 'PLT_BLINK_SW', 1)

	# IFF switch - ON
	pushSeqCmd(dt, 'PLT_IFF_PW', 1)

	# JADRO-1A Radio Mode knob - AM
	pushSeqCmd(dt, 'PLT_JADRO_MODUL', 2) # 0 = OFF, 1 = STB (SSB), 2 = AM

	# RWR switch - ON
	pushSeqCmd(dt, 'PLT_RWR_PW', 1)

	# PU-38 GREBEN compass system
	# GREBEN Tune/Oper switch - OPER
	pushSeqCmd(dt, 'PLT_GREB_SETUP', 1)
	# GREBEN Match (Sync) button - Press for 3 seconds
	pushSeqCmd(dt, 'PLT_GREB_MATCH', 1)
	pushSeqCmd(3, 'PLT_GREB_MATCH', 0)
	# GREBEN Mode switch - GYRO
	pushSeqCmd(dt, 'PLT_GREB_MODE', 1)

	# Autopilot
	# Autopilot Roll Channel button - ON
	pushSeqCmd(dt, 'PLT_SAU_K_ON', 1) # Press
	pushSeqCmd(dt, 'PLT_SAU_K_ON', 0) # Release
	# Autopilot Pitch Channel button - ON
	pushSeqCmd(dt, 'PLT_SAU_T_ON', 1) # Press
	pushSeqCmd(dt, 'PLT_SAU_T_ON', 0) # Release

	# Gunsight and Weapons Panel
	# Sight Power switch - ON # Weapons panel.
	pushSeqCmd(dt, 'PLT_PUVL_WPN_SIGHT', 1)
	# Range Insert switch - AUTO # Weapons panel.
	pushSeqCmd(dt, 'PLT_PUVL_SIGHT_DIST', 1)
	# Sight (Ranging) Mode switch - AUTO # Sight base.
	pushSeqCmd(dt, 'PLT_ASP17_MODE_MAN_AUTO', 1)
	# Sync/Async switch - ASYNC # Sight base.
	pushSeqCmd(dt, 'PLT_ASP17_MODE_SYNC_ASYNC', 0)
	# Fire Ctrl (Master Arm) switch - ON # Weapons panel.
	pushSeqCmd(dt, 'PLT_PUVL_FIRE_CONTROL', 1)
	# MG Rate (Cannon ROF) switch - INCR # Weapons panel
	pushSeqCmd(dt, 'PLT_PUVL_CANNON_FIRE_RATE', 1)
	# Fixed Crosshair Brightness - 60% # Sight base.
	pushSeqCmd(dt, 'PLT_ASP17_GRID_BRIGHT_ADJ', int16(0.6))
	# Aux Stores Lights switch - ON # Right angled panel bottom.
	pushSeqCmd(dt, 'PLT_ARM_RED_L_SW', 1)

	# Pilot-Operator (front) seat
	# Setting up Pilot-Operator switches...
	# Intercom (SPU-8) Power switch - ON
	pushSeqCmd(dt, 'OP_SPU8_SPUU_PW', 1)
	# Safety Switches (Master Arm) gang bar - ON
	pushSeqCmd(dt, 'OP_MAIN_WPN_SAVE', 1)
	# Missile Power switch - ON
	pushSeqCmd(dt, 'OP_MISSL_PW', 1)
	# FDI (ADI) switch - ON
	pushSeqCmd(dt, 'OP_ADI_SW', 1)
	# Cplr/Distr switch - ON # turns on gunsight?
	pushSeqCmd(dt, 'OP_USR_PW', 1)
	# Missile Station Selector (SCHO) power switch - ON
	pushSeqCmd(dt, 'OP_SCHO_PW', 1)
	# Guid. Unit Power switch - ON
	pushSeqCmd(dt, 'OP_SIGHT_PW', 1)
	# Burst Length - SHORT
	pushSeqCmd(dt, 'OP_BURST_LENGTH', 2)
	# Fxd MG-30 Rate (Cannon ROF) switch - INCR # Weapons panel
	pushSeqCmd(dt, 'OP_CAN_RATE', 1)
	#pushSeqCmd(dt, device = devices.I9K113, action = i9K113_commands.Command_NABL, value = 1) # OBSERVE
	#pushSeqCmd(dt, device = devices.I9K113, action = i9K113_commands.Command_STVORKI, value = 1) # Sight Doors
	# Done with Pilot-Operator switches

	# RWR test beep
	pushSeqCmd(dt, 'PLT_RWR_SIGNAL', 1) # Turn on RWR audio
	pushSeqCmd(dt, 'PLT_RWR_CHECK', 1) # Press (makes a beep)
	pushSeqCmd(dt, 'PLT_RWR_CHECK', 0) # Release
	pushSeqCmd(dt, 'PLT_RWR_SIGNAL', 0) # Turn off RWR audio

	# Pilot and Operator Fans - ON
	pushSeqCmd(dt, 'PLT_FAN', 1)
	pushSeqCmd(dt, 'OP_FAN', 1)

	pushSeqCmd(dt, 'scriptSpeech', "Manual steps remaining: Set lights.  Tune radios.  Set doppler navigation.  Set altimeter to Q F E or Q N H.")

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

	# Start sequence
	pushSeqCmd(0, '', '', "Running Hot Start sequence.")

	# Radio/ICS switch (Pilot) - ICS (allows rearming)
	pushSeqCmd(dt, 'PLT_SPU8_ICS', 1)

	# Lights
	# Strobe lights - OFF
	pushSeqCmd(dt, 'PLT_STROBE_L_SW', 0)
	# Blade Tip lights - OFF
	pushSeqCmd(dt, 'PLT_TIP_L_SW', 0)
	# Formation lights - OFF
	pushSeqCmd(dt, 'PLT_FORMATION_L_SW', 1) # 0 = DIM, 1 = OFF, 2 = BRIGHT
	# Nav lights - OFF
	pushSeqCmd(dt, 'PLT_NAV_L_SW', 1) # 0 = DIM, 1 = OFF, 2 = BRIGHT

	# Electric Power
	# DC Voltmeter knob - BATT
	pushSeqCmd(dt, 'PLT_D_VOLT_KNB', 2)

	# Generators and other electrics
	# AC Voltmeter knob - LEFT GENERATORS C-A
	pushSeqCmd(dt, 'PLT_A_VOLT_KNB', 5)

	# IFF switch - ON
	pushSeqCmd(dt, 'PLT_IFF_PW', 1)

	# RWR switch - ON
	pushSeqCmd(dt, 'PLT_RWR_PW', 1)

	# PU-38 GREBEN compass system
	# GREBEN Match (Sync) button - Press for 3 seconds
	pushSeqCmd(dt, 'PLT_GREB_MATCH', 1)
	pushSeqCmd(3, 'PLT_GREB_MATCH', 0)

	# Autopilot
	# Autopilot Yaw Channel button - OFF
	pushSeqCmd(dt, 'PLT_SAU_H_OFF', 1) # Press
	pushSeqCmd(dt, 'PLT_SAU_H_OFF', 0) # Release

	# Gunsight and Weapons Panel
	# Sight Power switch - ON # Weapons panel.
	pushSeqCmd(dt, 'PLT_PUVL_WPN_SIGHT', 1)
	# Range Insert switch - AUTO # Weapons panel.
	pushSeqCmd(dt, 'PLT_PUVL_SIGHT_DIST', 1)
	# Sight (Ranging) Mode switch - AUTO # Sight base.
	pushSeqCmd(dt, 'PLT_ASP17_MODE_MAN_AUTO', 1)
	# Sync/Async switch - ASYNC # Sight base.
	pushSeqCmd(dt, 'PLT_ASP17_MODE_SYNC_ASYNC', 0)
	# Fire Ctrl (Master Arm) switch - ON # Weapons panel.
	pushSeqCmd(dt, 'PLT_PUVL_FIRE_CONTROL', 1)
	# MG Rate (Cannon ROF) switch - INCR # Weapons panel
	pushSeqCmd(dt, 'PLT_PUVL_CANNON_FIRE_RATE', 1)
	# Fixed Crosshair Brightness - 60% # Sight base.
	pushSeqCmd(dt, 'PLT_ASP17_GRID_BRIGHT_ADJ', int16(0.6))

	# Pilot-Operator (front) seat
	# Setting up Pilot-Operator switches...
	# Intercom (SPU-8) Power switch - ON
	pushSeqCmd(dt, 'OP_SPU8_SPUU_PW', 1)
	# Safety Switches (Master Arm) gang bar - ON
	pushSeqCmd(dt, 'OP_MAIN_WPN_SAVE', 1)
	# Missile Power switch - ON
	pushSeqCmd(dt, 'OP_MISSL_PW', 1)
	# Cplr/Distr switch - ON # turns on gunsight?
	pushSeqCmd(dt, 'OP_USR_PW', 1)
	# Missile Station Selector (SCHO) power switch - ON
	pushSeqCmd(dt, 'OP_SCHO_PW', 1)
	# Guid. Unit Power switch - ON
	pushSeqCmd(dt, 'OP_SIGHT_PW', 1)
	# Burst Length - SHORT
	pushSeqCmd(dt, 'OP_BURST_LENGTH', 2)
	# Fxd MG-30 Rate (Cannon ROF) switch - INCR # Weapons panel
	pushSeqCmd(dt, 'OP_CAN_RATE', 1)
	#pushSeqCmd(dt, device = devices.I9K113, action = i9K113_commands.Command_NABL, value = 1) # OBSERVE
	#pushSeqCmd(dt, device = devices.I9K113, action = i9K113_commands.Command_STVORKI, value = 1) # Sight Doors
	# Done with Pilot-Operator switches

	# RWR test beep
	pushSeqCmd(dt, 'PLT_RWR_SIGNAL', 1) # Turn on RWR audio
	pushSeqCmd(dt, 'PLT_RWR_CHECK', 1) # Press (makes a beep)
	pushSeqCmd(dt, 'PLT_RWR_CHECK', 0) # Release
	pushSeqCmd(dt, 'PLT_RWR_SIGNAL', 0) # Turn off RWR audio

	# Pilot and Operator Fans - ON
	pushSeqCmd(dt, 'PLT_FAN', 1)
	pushSeqCmd(dt, 'OP_FAN', 1)

	pushSeqCmd(dt, 'scriptSpeech', "Manual steps remaining: Set lights.  Tune radios.  Set doppler navigation.  Set altimeter to Q F E or Q N H.")

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

	# Start sequence
	pushSeqCmd(0, '', '', "Running Shutdown sequence.")

	# Lights
	# Strobe lights - OFF
	pushSeqCmd(dt, 'PLT_STROBE_L_SW', 0)
	# Blade Tip lights - OFF
	pushSeqCmd(dt, 'PLT_TIP_L_SW', 0)
	# Formation lights - OFF
	pushSeqCmd(dt, 'PLT_FORMATION_L_SW', 1) # 0 = DIM, 1 = OFF, 2 = BRIGHT
	# Nav lights - OFF
	pushSeqCmd(dt, 'PLT_NAV_L_SW', 1) # 0 = DIM, 1 = OFF, 2 = BRIGHT

	# Left Panel switches
	# SPUU (Tail Roter Pitch Limiter) Power switch - OFF
	pushSeqCmd(dt, 'PLT_SPUU_POWER', 0)
	# Radar Altimeter (RV-5) Power switch - OFF
	pushSeqCmd(dt, 'PLT_RV5_PW', 0)
	# Doppler (DISS-15) switch - OFF
	pushSeqCmd(dt, 'PLT_DISS_PW', 0)
	# Vert Gyro 1 switch - OFF
	pushSeqCmd(dt, 'PLT_GYRO_1_PWR', 0)
	# Vert Gyro 2 switch - OFF
	pushSeqCmd(dt, 'PLT_GYRO_2_PWR', 0)
	# Comp. System (GREBEN) switch - OFF
	pushSeqCmd(dt, 'PLT_GREB_PW', 0)
	# Intercom (SPU-8) Network 1 switch - OFF
	pushSeqCmd(dt, 'PLT_SPU8_1_PW', 0)
	# Intercom (SPU-8) Network 2 switch - OFF
	pushSeqCmd(dt, 'PLT_SPU8_2_PW', 0)
	# HF Radio (JADRO-1A) switch - OFF
	pushSeqCmd(dt, 'PLT_JADRO_PW', 0)
	# R-828 Radio switch - OFF
	pushSeqCmd(dt, 'PLT_R828_PW', 0)
	# R-863 Radio switch - OFF
	pushSeqCmd(dt, 'PLT_R863_PW', 0)
	# Blink (Flasher) switch - OFF
	pushSeqCmd(dt, 'PLT_BLINK_SW', 0)

	# IFF switch - OFF
	pushSeqCmd(dt, 'PLT_IFF_PW', 0)

	# RWR switch - OFF
	pushSeqCmd(dt, 'PLT_RWR_PW', 0)

	# Pilot-Operator (front) seat
	# Setting up Pilot-Operator switches...
	# Intercom (SPU-8) Power switch - OFF
	pushSeqCmd(dt, 'OP_SPU8_SPUU_PW', 0)
	# Safety Switches (Master Arm) gang bar - OFF
	pushSeqCmd(dt, 'OP_MAIN_WPN_SAVE', 0)
	# Missile Power switch - OFF
	pushSeqCmd(dt, 'OP_MISSL_PW', 0)
	# FDI (ADI) switch - OFF
	pushSeqCmd(dt, 'OP_ADI_SW', 0)
	# Cplr/Distr switch - OFF # turns on gunsight?
	pushSeqCmd(dt, 'OP_USR_PW', 0)
	# Missile Station Selector (SCHO) power switch - OFF
	pushSeqCmd(dt, 'OP_SCHO_PW', 0)
	# Guid. Unit Power switch - OFF
	pushSeqCmd(dt, 'OP_SIGHT_PW', 0)
	# Done with Pilot-Operator switches

	# Pilot and Operator Fans - OFF
	pushSeqCmd(dt, 'PLT_FAN', 0)
	pushSeqCmd(dt, 'OP_FAN', 0)

	# JADRO-1A Radio Mode knob - OFF
	pushSeqCmd(dt, 'PLT_JADRO_MODUL', 0) # 0 = OFF, 1 = STB (SSB), 2 = AM

	# Gunsight and Weapons Panel
	# Sight Power switch - OFF # Weapons panel.
	pushSeqCmd(dt, 'PLT_PUVL_WPN_SIGHT', 0)
	# Range Insert switch - AUTO # Weapons panel.
	pushSeqCmd(dt, 'PLT_PUVL_SIGHT_DIST', 0)
	# Sight (Ranging) Mode switch - AUTO # Sight base.
	pushSeqCmd(dt, 'PLT_ASP17_MODE_MAN_AUTO', 0)
	# Sync/Async switch - ASYNC # Sight base.
	pushSeqCmd(dt, 'PLT_ASP17_MODE_SYNC_ASYNC', 0)
	# Fire Ctrl (Master Arm) switch - OFF # Weapons panel.
	pushSeqCmd(dt, 'PLT_PUVL_FIRE_CONTROL', 0)
	# Fixed Crosshair Brightness - 100% # Sight base.
	pushSeqCmd(dt, 'PLT_ASP17_GRID_BRIGHT_ADJ', int16())
	# Aux Stores Lights switch - OFF # Right angled panel bottom.
	pushSeqCmd(dt, 'PLT_ARM_RED_L_SW', 0)

	# Unseal and depressurize cabin
	# Cabin Press valve - Close (CCW)
	pushSeqCmd(dt, 'PLT_CABIN_PRESS', 1)
	# Cabin Depress switch - OFF
	pushSeqCmd(dt, 'PLT_CABIN_UNSEAL', 0)
	# Blowdown Conditioning switch - OFF
	pushSeqCmd(dt, 'PLT_AC_MODE', 1)

	# Cockpit Doors - Open
	pushSeqCmd(dt, 'scriptKeyboard', 'LCtrl down')
	pushSeqCmd(dt, 'scriptKeyboard', 'c')
	pushSeqCmd(dt, 'scriptKeyboard', 'LCtrl up')

	# Twist grip to min (DECR)
	pushSeqCmd(dt, 'scriptKeyboard', 'pgdn down')
	pushSeqCmd(2, 'scriptKeyboard', 'pgdn up') # Hold down for 2 seconds

	# Wait 40 seconds for rotor to spool down.
	pushSeqCmd(dt, 'scriptSpeech', 'Waiting for rotor to spool down to 80%, 40 seconds')
	pushSeqCmd(40, '', '', 'Rotor spooled down')

	# Left Engine Stop lever - ON
	pushSeqCmd(dt, 'PLT_ENG_STOP_L', 1)
	# Right Engine Stop lever - ON
	pushSeqCmd(dt, 'PLT_ENG_STOP_R', 1)

	# Wait for rotor to get to 15%.
	pushSeqCmd(dt, 'scriptSpeech', 'Waiting for rotor to spool down to 15%, 1 minute 10 seconds')
	pushSeqCmd(1* 60 + 10, '', '', 'Rotor at 15%')

	# Rotor Brake - ON
	pushSeqCmd(dt, 'PLT_ROTOR_BRAKE', 1)

	# Fuel System
	# Service (Feed) Tanks 1 switch - OFF
	pushSeqCmd(dt, 'PLT_FEED_TANK1', 0)
	# Service (Feed) Tanks 2 switch - OFF
	pushSeqCmd(dt, 'PLT_FEED_TANK2', 0)
	# Fuel Shutoff Left switch - OFF
	pushSeqCmd(dt, 'PLT_FIRE_VALVE_L_CV', 1) # Cover open
	pushSeqCmd(dt, 'PLT_FIRE_VALVE_L', 0) # Switch
	pushSeqCmd(dt, 'PLT_FIRE_VALVE_L_CV', 0) # Cover close
	# Fuel Shutoff Right switch - OFF
	pushSeqCmd(dt, 'PLT_FIRE_VALVE_R_CV', 1) # Cover open
	pushSeqCmd(dt, 'PLT_FIRE_VALVE_R', 0) # Switch
	pushSeqCmd(dt, 'PLT_FIRE_VALVE_R_CV', 0) # Cover close
	# Fuel Crossfeed (Delimiter) switch - OFF # "Fuel Delimiter Valve"
	pushSeqCmd(dt, 'PLT_FUEL_DELIM', 0)
	# Service Tank Pumps 1, 2, 4, and 5 switches - OFF
	pushSeqCmd(dt, 'PLT_PUMP_TANK1', 0)
	pushSeqCmd(dt, 'PLT_PUMP_TANK2', 0)
	pushSeqCmd(dt, 'PLT_PUMP_TANK4', 0)
	pushSeqCmd(dt, 'PLT_PUMP_TANK5', 0)

	# Fire Extinguisher
	# Fire Extinguisher Power switch - OFF
	pushSeqCmd(dt, 'PLT_FIRE_EX_PW', 0)
	# Fire Extinguisher Control switch - OFF
	pushSeqCmd(dt, 'PLT_FIRE_EX_CONTROL', 0)

	# Left CBs - OFF
	pushSeqCmd(dt, 'PLT_CB_L_ADF', 0)
	pushSeqCmd(dt, 'PLT_CB_L_AFCS_WARN', 0)
	pushSeqCmd(dt, 'PLT_CB_L_AIR_SPEED', 0)
	pushSeqCmd(dt, 'PLT_CB_L_ALL', 0)
	pushSeqCmd(dt, 'PLT_CB_L_AUTO_START', 0)
	pushSeqCmd(dt, 'PLT_CB_L_BEACON_L', 0)
	pushSeqCmd(dt, 'PLT_CB_L_BOMBS', 0)
	pushSeqCmd(dt, 'PLT_CB_L_CARGO_EXT_JETT', 0)
	pushSeqCmd(dt, 'PLT_CB_L_CROSS_FEED', 0)
	pushSeqCmd(dt, 'PLT_CB_L_EMERG_JETT', 0)
	pushSeqCmd(dt, 'PLT_CB_L_FIRE_SYS_AUTO', 0)
	pushSeqCmd(dt, 'PLT_CB_L_FIRE_SYS_MAN', 0)
	pushSeqCmd(dt, 'PLT_CB_L_FIRE_SYS_WARN', 0)
	pushSeqCmd(dt, 'PLT_CB_L_FLIGHT_REC', 0)
	pushSeqCmd(dt, 'PLT_CB_L_FUEL_OFF', 0)
	pushSeqCmd(dt, 'PLT_CB_L_GEAR', 0)
	pushSeqCmd(dt, 'PLT_CB_L_GEAR_WARN', 0)
	pushSeqCmd(dt, 'PLT_CB_L_IGNITION', 0)
	pushSeqCmd(dt, 'PLT_CB_L_INVERTER', 0)
	pushSeqCmd(dt, 'PLT_CB_L_LAND_L', 0)
	pushSeqCmd(dt, 'PLT_CB_L_MAIN_ATT', 0)
	pushSeqCmd(dt, 'PLT_CB_L_MISSLE_PWR', 0)
	pushSeqCmd(dt, 'PLT_CB_L_ROCKETS', 0)
	pushSeqCmd(dt, 'PLT_CB_L_TANK1', 0)
	pushSeqCmd(dt, 'PLT_CB_L_TANK_FIRE', 0)
	pushSeqCmd(dt, 'PLT_CB_L_VALVE_SEP', 0)
	pushSeqCmd(dt, 'PLT_CB_L_WARN_SYS', 0)
	pushSeqCmd(dt, 'PLT_CB_L_WS_SPRAY', 0)
	pushSeqCmd(dt, 'PLT_CB_L_WS_WIPER_OP', 0)
	pushSeqCmd(dt, 'PLT_CB_L_WS_WIPER_PLT', 0)

	# Right CBs - OFF
	pushSeqCmd(dt, 'PLT_CB_R_AICE_CONTR', 0)
	pushSeqCmd(dt, 'PLT_CB_R_AICE_WARN', 0)
	pushSeqCmd(dt, 'PLT_CB_R_AIR_CONT', 0)
	pushSeqCmd(dt, 'PLT_CB_R_ALL', 0)
	pushSeqCmd(dt, 'PLT_CB_R_ARM_CONTROL', 0)
	pushSeqCmd(dt, 'PLT_CB_R_BOMB_REL', 0)
	pushSeqCmd(dt, 'PLT_CB_R_CAMERA', 0)
	pushSeqCmd(dt, 'PLT_CB_R_CANNON', 0)
	pushSeqCmd(dt, 'PLT_CB_R_CONNECT_DISTR', 0)
	pushSeqCmd(dt, 'PLT_CB_R_CONTR_CLUTCH', 0)
	pushSeqCmd(dt, 'PLT_CB_R_CONTR_FORCE', 0)
	pushSeqCmd(dt, 'PLT_CB_R_DETACH_RAILS', 0)
	pushSeqCmd(dt, 'PLT_CB_R_DUASV_HEAT', 0)
	pushSeqCmd(dt, 'PLT_CB_R_FIRE_AUTO', 0)
	pushSeqCmd(dt, 'PLT_CB_R_FIRE_MAN', 0)
	pushSeqCmd(dt, 'PLT_CB_R_FUEL_IND', 0)
	pushSeqCmd(dt, 'PLT_CB_R_FUEL_PUMP2', 0)
	pushSeqCmd(dt, 'PLT_CB_R_FUEL_PUMP4', 0)
	pushSeqCmd(dt, 'PLT_CB_R_FUEL_T2_OFF', 0)
	pushSeqCmd(dt, 'PLT_CB_R_FUEL_T2_VALVE', 0)
	pushSeqCmd(dt, 'PLT_CB_R_GEAR_VALVE', 0)
	pushSeqCmd(dt, 'PLT_CB_R_JETT_DOOR_OP', 0)
	pushSeqCmd(dt, 'PLT_CB_R_JETT_DOOR_PLT', 0)
	pushSeqCmd(dt, 'PLT_CB_R_PILOT_SEAT', 0)
	pushSeqCmd(dt, 'PLT_CB_R_PILOT_SIGHT', 0)
	pushSeqCmd(dt, 'PLT_CB_R_ROTOR_RPM', 0)
	pushSeqCmd(dt, 'PLT_CB_R_SIGNAL', 0)
	pushSeqCmd(dt, 'PLT_CB_R_STORE_LOCK', 0)
	pushSeqCmd(dt, 'PLT_CB_R_STORE_TAC', 0)
	pushSeqCmd(dt, 'PLT_CB_R_TEMP_L', 0)
	pushSeqCmd(dt, 'PLT_CB_R_TEMP_R', 0)

	# Generators and other electrics
	# Left Generator switch - OFF
	pushSeqCmd(dt, 'PLT_A_GEN_L', 0)
	# Right Generator switch - OFF
	pushSeqCmd(dt, 'PLT_A_GEN_R', 0)
	# 115V Transformer switch - AUTO
	pushSeqCmd(dt, 'PLT_A_TRANS_115', 1)
	# 36V Transformer switch - AUTO
	pushSeqCmd(dt, 'PLT_A_TRANS_36', 1)
	# Left Rectifier switch - OFF
	pushSeqCmd(dt, 'PLT_D_RECT_L', 0)
	# Right Rectifier switch - OFF
	pushSeqCmd(dt, 'PLT_D_RECT_R', 0)
	# AC Voltmeter knob - OFF
	pushSeqCmd(dt, 'PLT_A_VOLT_KNB', 0)

	# Electric Power
	# Right Battery - OFF
	pushSeqCmd(dt, 'PLT_D_BATT_R', 0)
	# Left Battery - OFF
	pushSeqCmd(dt, 'PLT_D_BATT_L', 0)
	# DC Voltmeter knob - OFF
	pushSeqCmd(dt, 'PLT_D_VOLT_KNB', 0)

	return seq
