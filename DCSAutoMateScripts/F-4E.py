# Return a Dictionary of script data.  The 'scripts' key is a list of scripts that users will be selecting from.  Each script has an associated 'function', which is the name of the function in this file that will be called to generate the command sequence, and a dictionary of 'vars' that the user will be prompted to choose from before running the script, and will be passed into the sequence generating function.
def getScriptData():
	return {
		'scripts': [
			{
				'name': 'Cold Start With Jester',
				'function': 'ColdStartWithJester',
				'vars': {
					'Time': ['Day', 'Night'],
					'Alignment': ['BATH', 'Full'],
				},
			},
			#{
			#	'name': 'Cold Start No Jester',
			#	'function': 'ColdStartNoJester',
			#	'vars': {
			#		'Time': ['Day', 'Night'],
			#		'Alignment': ['BATH', 'Full'],
			#	},
			#},
			{
				'name': 'Auto Start (run after auto start is complete)',
				'function': 'HotStart',
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
			#{
			#	'name': 'Shutdown TODO',
			#	'function': 'Shutdown',
			#	'vars': {},
			#},
			#{
			#	'name': 'Test',
			#	'function': 'Test',
			#	'vars': {
			#		'Time': ['Day', 'Night'],
			#		'Alignment': ['BATH', 'Full'],
			#	},
			#},
			#{
			#	'name': 'Jester Command Test',
			#	'function': 'JesterCommandTest',
			#	'vars': {
			#		'Time': ['Day', 'Night'],
			#		'Alignment': ['BATH', 'Full'],
			#	},
			#},
		],
	}

def getInfo():
	return """"""

# Returns 0-65535 scaled by multiple (0-1), eg for 50% call int16(0.5)
def int16(mult = 1):
	int16 = 65535
	return int(mult * int16)

def Test(config, vars):
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

	# Test code here...


	return seq


def JesterCommandTest(config, vars):
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

	"""
	The only one of these that seems to work is F-4E/PLT_JESTER_COMMAND_CREW_PRESENCE_DISABLED.  None of the others seem do to anything.
	"""
	#pushSeqCmd(dt, 'F-4E/PLT_JESTER_COMMAND_CREW_PRESENCE_DISABLED', 'TOGGLE')
	#pushSeqCmd(dt, 'F-4E/PLT_JESTER_COMMAND_CREW_PRESENCE_AUTO', 'TOGGLE')
	#pushSeqCmd(dt, 'F-4E/PLT_JESTER_COMMAND_RADAR_OPERATION_STANDBY ', 'TOGGLE')
	#pushSeqCmd(dt, 'F-4E/PLT_JESTER_COMMAND_RADAR_OPERATION_ACTIVE', 'TOGGLE')
	#pushSeqCmd(dt, 'F-4E/PLT_JESTER_COMMAND_RADAR_RANGE_25_NARROW', 'TOGGLE')

	"""
	The Jester wheel interface does work, but it's clunky and not idempotent.  When you open it, it may be in the base menu, a sub-menu, or in a selector.  Press LShift-1 to go up/back one level, but if you press it while at the base menu the wheel will close.  You can put the wheel into a known state by pressing "A, LShift-1, LShift-1, LShift-1", which will always close the wheel and leave it at the base menu, but that's time consuming.

	You can close the wheel by holding down A for 0.5 seconds (other times may work also, but probably can't be much shorter than that).  If the wheel is already closed, long-A will also open it.  To close the wheel idempotically, press LShift-1, which will close the wheel if it's open, but won't open it if it's closed.
	"""

	# This will open the wheel, return to the base menu, and close it.
	pushSeqCmd(dt, 'scriptKeyboard', 'a')
	pushSeqCmd(1, '', '', 'wait')
	pushSeqCmd(dt, 'scriptKeyboard', 'LShift down')
	pushSeqCmd(dt, 'scriptKeyboard', '1')
	pushSeqCmd(dt, 'scriptKeyboard', 'LShift up')
	pushSeqCmd(1, '', '', 'wait')
	pushSeqCmd(dt, 'scriptKeyboard', 'LShift down')
	pushSeqCmd(dt, 'scriptKeyboard', '1')
	pushSeqCmd(dt, 'scriptKeyboard', 'LShift up')
	pushSeqCmd(1, '', '', 'wait')
	pushSeqCmd(dt, 'scriptKeyboard', 'LShift down')
	pushSeqCmd(dt, 'scriptKeyboard', '1')
	pushSeqCmd(dt, 'scriptKeyboard', 'LShift up')

	## Enable Jester using the wheel interface.
	#pushSeqCmd(dt, 'scriptKeyboard', 'a')
	#pushSeqCmd(1, '', '', 'wait')
	## Jester
	#pushSeqCmd(dt, 'scriptKeyboard', 'LCtrl down')
	#pushSeqCmd(dt, 'scriptKeyboard', '6')
	#pushSeqCmd(dt, 'scriptKeyboard', 'LCtrl up')
	#pushSeqCmd(1, '', '', 'wait')
	## Presense
	#pushSeqCmd(dt, 'scriptKeyboard', 'LCtrl down')
	#pushSeqCmd(dt, 'scriptKeyboard', '1')
	#pushSeqCmd(dt, 'scriptKeyboard', 'LCtrl up')
	#pushSeqCmd(1, '', '', 'wait')
	## Auto
	#pushSeqCmd(dt, 'scriptKeyboard', 'w')

	## Jester radar active.
	#pushSeqCmd(dt, 'scriptKeyboard', 'a')
	#pushSeqCmd(1, '', '', 'wait')
	## Radar
	#pushSeqCmd(dt, 'scriptKeyboard', 'LCtrl down')
	#pushSeqCmd(dt, 'scriptKeyboard', '2')
	#pushSeqCmd(dt, 'scriptKeyboard', 'LCtrl up')
	#pushSeqCmd(1, '', '', 'wait')
	## Operation
	#pushSeqCmd(dt, 'scriptKeyboard', 'LCtrl down')
	#pushSeqCmd(dt, 'scriptKeyboard', '1')
	#pushSeqCmd(dt, 'scriptKeyboard', 'LCtrl up')
	#pushSeqCmd(1, '', '', 'wait')
	## Active
	#pushSeqCmd(dt, 'scriptKeyboard', 'w')

	# Jester radar 25nm narrow.
	pushSeqCmd(dt, 'scriptKeyboard', 'a')
	pushSeqCmd(1, '', '', 'wait')
	# Radar
	pushSeqCmd(dt, 'scriptKeyboard', 'LCtrl down')
	pushSeqCmd(dt, 'scriptKeyboard', '2')
	pushSeqCmd(dt, 'scriptKeyboard', 'LCtrl up')
	pushSeqCmd(1, '', '', 'wait')
	# ScanType
	pushSeqCmd(dt, 'scriptKeyboard', 'LCtrl down')
	pushSeqCmd(dt, 'scriptKeyboard', '5')
	pushSeqCmd(dt, 'scriptKeyboard', 'LCtrl up')
	pushSeqCmd(1, '', '', 'wait')
	# 25 nm narrow
	pushSeqCmd(dt, 'scriptKeyboard', 'e')
	pushSeqCmd(1, '', '', 'wait')
	pushSeqCmd(dt, 'scriptKeyboard', 'w')

	return seq


def ColdStartWithJester(config, vars):
	seq = []
	seqTime = 0
	dt = 0.2

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

	alignTime = 3 * 60 + 10 # 3m10s max for BATH align?  Seems to be randomized.  Can take as little as 2m30s in testing.

	pushSeqCmd(0, '', '', "Running Cold Start sequence")

	# Put on helmet.
	pushSeqCmd(dt, 'PLT_COCKPIT_HELMET', 0) # 0 = Helmet On, 1 = Helmet Off
	pushSeqCmd(14, '', '', 'Wait for boarding ladder to be removed.')

	if vars.get('Time') == 'Day':
		# Interior lights
		pushSeqCmd(dt, 'PLT_INT_LIGHT_CONSOLE_BRIGHTNESS', int16(1))
		pushSeqCmd(dt, 'PLT_INT_LIGHT_INSTRUMENT_PANEL_BRIGHTNESS', int16(1))
		pushSeqCmd(dt, 'PLT_INT_LIGHT_FLOOD_RED_BRIGHTNESS', 1) # 0 = MED, 1 = DIM, 2 = BRT
		pushSeqCmd(dt, 'PLT_INT_LIGHT_FLOOD_INST_BRIGHTNESS', 1) # Also controls WSO panel.  0 = DIM, 1 = OFF, 2 = BRT
		pushSeqCmd(dt, 'WSO_INT_LIGHT_INSTRUMENT_PANEL_BRIGHTNESS', int16(1))
		pushSeqCmd(dt, 'WSO_INT_LIGHT_CONSOLE_BRIGHTNESS', int16(1))
		pushSeqCmd(dt, 'WSO_INT_LIGHT_FLOOD_RED_BRIGHTNESS', 1) # 0 = MED, 1 = DIM, 2 = BRT
		# Radar screen night filter
		pushSeqCmd(dt, 'PLT_RADAR_NIGHT_FILTER', 0) # 0 = Off, 1 = On
		# Exterior lights
		pushSeqCmd(dt, 'PLT_EXT_LIGHT_FLASH_MODE', 1) # 0 = STEADY, 1 = OFF, 2 = FLASH
	else:
		# Interior lights
		pushSeqCmd(dt, 'PLT_INT_LIGHT_CONSOLE_BRIGHTNESS', int16(0.5))
		pushSeqCmd(dt, 'PLT_INT_LIGHT_INSTRUMENT_PANEL_BRIGHTNESS', int16(0.5))
		pushSeqCmd(dt, 'PLT_INT_LIGHT_FLOOD_RED_BRIGHTNESS', 1) # 0 = MED, 1 = DIM, 2 = BRT
		pushSeqCmd(dt, 'PLT_INT_LIGHT_FLOOD_INST_BRIGHTNESS', 1) # Also controls WSO panel.  0 = DIM, 1 = OFF, 2 = BRT
		pushSeqCmd(dt, 'WSO_INT_LIGHT_INSTRUMENT_PANEL_BRIGHTNESS', int16(0.5))
		pushSeqCmd(dt, 'WSO_INT_LIGHT_CONSOLE_BRIGHTNESS', int16(0.5))
		pushSeqCmd(dt, 'WSO_INT_LIGHT_FLOOD_RED_BRIGHTNESS', 1) # 0 = MED, 1 = DIM, 2 = BRT
		# Radar screen night filter
		pushSeqCmd(dt, 'PLT_RADAR_NIGHT_FILTER', 1) # 0 = Off, 1 = On
		# Exterior lights
		pushSeqCmd(dt, 'PLT_EXT_LIGHT_FLASH_MODE', 1) # 0 = STEADY, 1 = OFF, 2 = FLASH

	# Radios
	pushSeqCmd(dt, 'PLT_ARC_164_MODE', 1) # 0 = OFF, 1 = T/R, 2 = T/R+G, 3 = ADF+G, 4 = ADF, 5 = GUARD
	pushSeqCmd(dt, 'WSO_ARC_164_MODE', 1) # 0 = OFF, 1 = T/R, 2 = T/R+G, 3 = ADF+G, 4 = ADF, 5 = GUARD

	# Engine Master Switches ... ON
	# Turning on master switches before loading cartridges makes the crew chief respond by voice.  If switches aren't on, cartridges will be installed, but crew chief won't tell you.
	pushSeqCmd(dt, 'PLT_ENGINE_MASTER_L', 1)
	pushSeqCmd(dt, 'PLT_ENGINE_MASTER_R', 1)
	pushSeqCmd(dt, 'scriptSpeech', 'Crew Chief, insert starter cartridges.')
	pushSeqCmd(1, '', '', 'Wait for Jester/Crew Chief to be ready.')

	# Tell Crew Chief to insert starter cartridges.
	pushSeqCmd(dt, 'PLT_CREW_CHIEF_COMMAND_AIR_SOURCE_LOAD_CARTRIDGES', 'TOGGLE') # Pass 'TOGGLE' to trigger command.
	pushSeqCmd(14, '', '', 'Wait for cartridges to be installed.')

	# Start right engine
	pushSeqCmd(dt, 'scriptSpeech', "Starting right engine.")
	pushSeqCmd(dt, 'PLT_ENGINE_START', 2) # 0 = LEFT, 1 = OFF, 2 = RIGHT
	# Release after 1 second.
	pushSeqCmd(1, 'PLT_ENGINE_START', 1) # 0 = LEFT, 1 = OFF, 2 = RIGHT
	# Wait to get past 10% RPM.
	pushSeqCmd(dt, 'scriptCockpitState', control='F-4E/PLT_ENGINE_TACH_R_LARGE', value=int16(0.1), condition='>=', duration=0)
	# At 10% RPM, press and hold ignition button.
	pushSeqCmd(dt, 'PLT_THROTTLE_IGNITION_R', 1)
	# Advance throttle to idle detent.
	pushSeqCmd(dt, 'PLT_THROTTLE_DETENT_R', 1)
	# Wait for engine to light off.
	pushSeqCmd(dt, 'scriptCockpitState', control='F-4E/PLT_ENGINE_EXHAUST_R_LARGE', value=int16(0.15), condition='>=', duration=0)
	#pushSeqCmd(5, '', '', 'Wait 5 seconds for engine to light off.')
	# Release ignition.
	pushSeqCmd(dt, 'PLT_THROTTLE_IGNITION_R', 0)
	# Wait for RPM to reach idle (65%).
	pushSeqCmd(dt, 'scriptCockpitState', control='F-4E/PLT_ENGINE_TACH_R_LARGE', value=int16(0.64), condition='>=', duration=3)
	# Right generator ... ON
	pushSeqCmd(dt, 'PLT_ELECTRICS_GENERATOR_R', 2) # 0 = EXTERNAL, 1 = OFF, 2 = GEN

	# Start left engine
	pushSeqCmd(dt, 'scriptSpeech', "Starting left engine.")
	pushSeqCmd(dt, 'PLT_ENGINE_START', 0) # 0 = LEFT, 1 = OFF, 2 = RIGHT
	# Release after 1 second.
	pushSeqCmd(1, 'PLT_ENGINE_START', 1) # 0 = LEFT, 1 = OFF, 2 = RIGHT
	# Wait to get past 10% RPM.
	pushSeqCmd(dt, 'scriptCockpitState', control='F-4E/PLT_ENGINE_TACH_R_LARGE', value=int16(0.1), condition='>=', duration=0)
	# At 10% RPM, press and hold ignition button.
	pushSeqCmd(dt, 'PLT_THROTTLE_IGNITION_L', 1)
	# Advance throttle to idle detent.
	pushSeqCmd(dt, 'PLT_THROTTLE_DETENT_L', 1)
	# Wait for engine to light off.
	pushSeqCmd(dt, 'scriptCockpitState', control='F-4E/PLT_ENGINE_EXHAUST_L_LARGE', value=int16(0.15), condition='>=', duration=0)
	# Release ignition.
	pushSeqCmd(dt, 'PLT_THROTTLE_IGNITION_L', 0)
	# Wait for RPM to reach idle (65%).
	pushSeqCmd(dt, 'scriptCockpitState', control='F-4E/PLT_ENGINE_TACH_L_LARGE', value=int16(0.64), condition='>=', duration=3)
	# Right generator ... ON
	pushSeqCmd(dt, 'PLT_ELECTRICS_GENERATOR_L', 2) # 0 = EXTERNAL, 1 = OFF, 2 = GEN

	pushSeqCmd(4, '', '', 'Wait for Jester prompt.')
	#pushSeqCmd(dt, 'PLT_JESTER_COMMAND_CREW_START_ALIGNMENT', 'TOGGLE') # Pass 'TOGGLE' to trigger command.
	pushSeqCmd(dt, 'scriptKeyboard', 'w')
	pushSeqCmd(2, '', '', 'Wait for Jester prompt.')
	#pushSeqCmd(dt, 'PILOT_JESTER_OPTION_2 ', 'TOGGLE') # Pass 'TOGGLE' to trigger command.
	# Select "BATH alignment".
	pushSeqCmd(dt, 'scriptKeyboard', 'LCtrl down')
	pushSeqCmd(dt, 'scriptKeyboard', '2')
	pushSeqCmd(dt, 'scriptKeyboard', 'LCtrl up')

	pushSeqCmd(5, '', '', 'Wait for Jester prompt.')
	pushSeqCmd(dt, 'scriptKeyboard', 'w')
	pushSeqCmd(2, '', '', 'Wait for Jester prompt.')
	# Select "Yep".
	pushSeqCmd(dt, 'scriptKeyboard', 'LCtrl down')
	pushSeqCmd(dt, 'scriptKeyboard', '1')
	pushSeqCmd(dt, 'scriptKeyboard', 'LCtrl up')

	pushSeqCmd(dt, 'PLT_CANOPY_CONTROL', 0) # 0 = Close, 1 = Open

	# Radar altimeter ... ON, but leave bug at 0 ft
	pushSeqCmd(dt, 'PLT_RADAR_ALT_MOVE_BUG', "+3200")

	# DSCG screen mode switch
	pushSeqCmd(dt, 'PLT_RADAR_SCREEN_MODE', 0) # 0 = RADAR, 1 = OFF, 2 = TV

	# IFF
	pushSeqCmd(dt, 'PLT_IFF_MASTER', 3) # 0 = OFF, 1 = STBY, 2 = LOW, 3 = NOR, 4 = EMER

	# Antiskid
	pushSeqCmd(dt, 'PLT_GEAR_ANTI_SKID', 1)

	# Backup ADI
	pushSeqCmd(dt, 'PLT_SAI_CAGE', 0)

	# Sight mode
	pushSeqCmd(dt, 'PLT_HUD_MODE', 2) # 0 = OFF, 1 = STBY, 2 = CAGE, 3 = A/G, 4 = A/A, 5 = BIT 1, 6 = BIT 2

	# ADI flight director switch
	pushSeqCmd(dt, 'PLT_FDC_FLIGHT_DIRECTOR', 1)

	# Wait for alignment to complete.  With Jester, that's when he moves the INS Power knob to NAV.
	pushSeqCmd(dt, 'scriptCockpitState', control='F-4E/WSO_INS_POWER', value=3, condition='=', duration=0)
	pushSeqCmd(7, '', '', 'Wait for Jester to finish talking.')
	pushSeqCmd(dt, 'scriptSpeech', "Alignment complete.")

	# Reference System switch ... PRIM
	pushSeqCmd(dt, 'PLT_ADI_REFERENCE_SYSTEM  ', 0) # 0 = PRIM, 1 = STBY
	pushSeqCmd(5, '', '', 'Wait for compass.')

	# Compass Sync knob ... SYNC for a few seconds, then release back to SLAVED
	pushSeqCmd(dt, 'PLT_COMPASS_MODE_SYNC', 3) # 0 = COMP, 1 = DC, 2 = SLAVED, 3 = SYNC
	pushSeqCmd(4, 'PLT_COMPASS_MODE_SYNC', 2) # 0 = COMP, 1 = DC, 2 = SLAVED, 3 = SYNC

	# CADC correction
	pushSeqCmd(dt, 'PLT_CADC_CORRECTION', 2) # 0 = OFF, 1 = NORM, 2 = RESET
	pushSeqCmd(4, 'PLT_CADC_CORRECTION', 1) # 0 = OFF, 1 = NORM, 2 = RESET

	# Altimeter (only do this after CADC correction?)
	pushSeqCmd(dt, 'PLT_BARO_MODE', 2)
	# No need to move the lever back after setting it, just wait 3 seconds.
	pushSeqCmd(3, '', '', 'Wait for STBY flag to disappear.')

	# Countermeasures
	pushSeqCmd(dt, 'WSO_CM_CHAFF_MODE', 1) # 0 = OFF, 1 = SGL, 2 = MULT, 3 = PROG
	pushSeqCmd(dt, 'WSO_CM_FLARE_MODE', 1) # 0 = OFF, 1 = SGL, 2 = PROG

	# Stab Aug
	pushSeqCmd(dt, 'PLT_AFCS_STAB_AUG_PITCH', 1)
	pushSeqCmd(dt, 'PLT_AFCS_STAB_AUG_ROLL', 1)
	pushSeqCmd(dt, 'PLT_AFCS_STAB_AUG_YAW', 1)

	# Oxygen
	pushSeqCmd(dt, 'PLT_O2_MIXTURE', 0) # 0 = NORMAL OXYGEN, 1 = 100% OXYGEN
	pushSeqCmd(dt, 'PLT_O2_SUPPLY', 0) # 0 = ON, 1 = OFF
	pushSeqCmd(dt, 'WSO_O2_MIXTURE', 0) # 0 = NORMAL OXYGEN, 1 = 100% OXYGEN
	pushSeqCmd(dt, 'WSO_O2_SUPPLY', 0) # 0 = ON, 1 = OFF

	# RDR MSL CW switch ... CW ON
	pushSeqCmd(dt, 'PLT_WPN_RADAR_MISSILE_CW', 2) # 0 = OFF, 1 = STBY, 2 = CW ON

	# Fuze switch
	pushSeqCmd(dt, 'PLT_WPN_FUZE_ARM', 2) # 0 = SAFE, 1 = NOSE, 2 = NOSE & TAIL, 3 = TAIL

	# Bomb quantity
	pushSeqCmd(dt, 'PLT_WPN_BOMB_QUANTITY', 11) # 0 = P, 1 = S, 2 = C, 3 = 18, 4 = 12, 5 = 9, 6 = 6, 7 = 5, 8 = 4, 9 = 3, 10 = 2, 11 = 1

	# Arm gun
	pushSeqCmd(dt, 'PLT_WPN_GUN_ARM', 1)

	# Master Arm
	pushSeqCmd(dt, 'PLT_WPN_MASTER_ARM',  1)

	# Jester, radar to active.
	#pushSeqCmd(dt, 'F-4E/PLT_JESTER_COMMAND_RADAR_OPERATION_ACTIVE', 'TOGGLE') # FIXME This doesn't work.

	# Jester, radar auto-focus on.
	#pushSeqCmd(dt, 'F-4E/PLT_JESTER_COMMAND_RADAR_AUTO_FOCUS_ON', 'TOGGLE') # FIXME This doesn't work.

	pushSeqCmd(dt, 'scriptSpeech', "Manual steps remaining: Lights, Radios.  If carrying drop tanks set External Tanks Feed switch.  Set takeoff trim, 2 units nose down.  Set up Jester as needed.")

	return seq


def ColdStartNoJester(config, vars):
	seq = []
	seqTime = 0
	dt = 0.2

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

	pushSeqCmd(0, '', '', "Running Cold Start sequence")

	# Put on helmet.
	pushSeqCmd(dt, 'PLT_COCKPIT_HELMET', 0) # 0 = Helmet On, 1 = Helmet Off
	pushSeqCmd(14, '', '', 'Wait for boarding ladder to be removed.')

	# Disable Jester.
	pushSeqCmd(dt, 'PLT_JESTER_COMMAND_CREW_PRESENCE_DISABLED', 'TOGGLE')

	if vars.get('Time') == 'Day':
		# Interior lights
		pushSeqCmd(dt, 'PLT_INT_LIGHT_CONSOLE_BRIGHTNESS', int16(1))
		pushSeqCmd(dt, 'PLT_INT_LIGHT_INSTRUMENT_PANEL_BRIGHTNESS', int16(1))
		pushSeqCmd(dt, 'PLT_INT_LIGHT_FLOOD_RED_BRIGHTNESS', 1) # 0 = MED, 1 = DIM, 2 = BRT
		pushSeqCmd(dt, 'PLT_INT_LIGHT_FLOOD_INST_BRIGHTNESS', 1) # Also controls WSO panel.  0 = DIM, 1 = OFF, 2 = BRT
		pushSeqCmd(dt, 'WSO_INT_LIGHT_INSTRUMENT_PANEL_BRIGHTNESS', int16(1))
		pushSeqCmd(dt, 'WSO_INT_LIGHT_CONSOLE_BRIGHTNESS', int16(1))
		pushSeqCmd(dt, 'WSO_INT_LIGHT_FLOOD_RED_BRIGHTNESS', 1) # 0 = MED, 1 = DIM, 2 = BRT
		# Radar screen night filter
		pushSeqCmd(dt, 'PLT_RADAR_NIGHT_FILTER', 0) # 0 = Off, 1 = On
		# Exterior lights
		pushSeqCmd(dt, 'PLT_EXT_LIGHT_FLASH_MODE', 1) # 0 = STEADY, 1 = OFF, 2 = FLASH
	else:
		# Interior lights
		pushSeqCmd(dt, 'PLT_INT_LIGHT_CONSOLE_BRIGHTNESS', int16(0.5))
		pushSeqCmd(dt, 'PLT_INT_LIGHT_INSTRUMENT_PANEL_BRIGHTNESS', int16(0.5))
		pushSeqCmd(dt, 'PLT_INT_LIGHT_FLOOD_RED_BRIGHTNESS', 1) # 0 = MED, 1 = DIM, 2 = BRT
		pushSeqCmd(dt, 'PLT_INT_LIGHT_FLOOD_INST_BRIGHTNESS', 1) # Also controls WSO panel.  0 = DIM, 1 = OFF, 2 = BRT
		pushSeqCmd(dt, 'WSO_INT_LIGHT_INSTRUMENT_PANEL_BRIGHTNESS', int16(0.5))
		pushSeqCmd(dt, 'WSO_INT_LIGHT_CONSOLE_BRIGHTNESS', int16(0.5))
		pushSeqCmd(dt, 'WSO_INT_LIGHT_FLOOD_RED_BRIGHTNESS', 1) # 0 = MED, 1 = DIM, 2 = BRT
		# Radar screen night filter
		pushSeqCmd(dt, 'PLT_RADAR_NIGHT_FILTER', 1) # 0 = Off, 1 = On
		# Exterior lights
		pushSeqCmd(dt, 'PLT_EXT_LIGHT_FLASH_MODE', 1) # 0 = STEADY, 1 = OFF, 2 = FLASH

	# Radios
	pushSeqCmd(dt, 'PLT_ARC_164_MODE', 1) # 0 = OFF, 1 = T/R, 2 = T/R+G, 3 = ADF+G, 4 = ADF, 5 = GUARD
	pushSeqCmd(dt, 'WSO_ARC_164_MODE', 1) # 0 = OFF, 1 = T/R, 2 = T/R+G, 3 = ADF+G, 4 = ADF, 5 = GUARD

	# Engine Master Switches ... ON
	# Turning on master switches before loading cartridges makes the crew chief respond by voice.  If switches aren't on, cartridges will be installed, but crew chief won't tell you.
	pushSeqCmd(dt, 'PLT_ENGINE_MASTER_L', 1)
	pushSeqCmd(dt, 'PLT_ENGINE_MASTER_R', 1)
	pushSeqCmd(dt, 'scriptSpeech', 'Crew Chief, insert starter cartridges.')
	pushSeqCmd(2, '', '', 'Wait for Jester/Crew Chief to be ready.')

	# Tell Crew Chief to insert starter cartridges.
	pushSeqCmd(dt, 'PLT_CREW_CHIEF_COMMAND_AIR_SOURCE_LOAD_CARTRIDGES', 'TOGGLE') # Pass 'TOGGLE' to trigger command.
	pushSeqCmd(14, '', '', 'Wait for cartridges to be installed.')

	# Start right engine
	pushSeqCmd(dt, 'scriptSpeech', "Starting right engine.")
	pushSeqCmd(dt, 'PLT_ENGINE_START', 2) # 0 = LEFT, 1 = OFF, 2 = RIGHT
	# Release after 1 second.
	pushSeqCmd(1, 'PLT_ENGINE_START', 1) # 0 = LEFT, 1 = OFF, 2 = RIGHT
	# Wait to get past 10% RPM.
	pushSeqCmd(dt, 'scriptCockpitState', control='F-4E/PLT_ENGINE_TACH_R_LARGE', value=int16(0.1), condition='>=', duration=0)
	# At 10% RPM, press and hold ignition button.
	pushSeqCmd(dt, 'PLT_THROTTLE_IGNITION_R', 1)
	# Advance throttle to idle detent.
	pushSeqCmd(dt, 'PLT_THROTTLE_DETENT_R', 1)
	# Wait for engine to light off.
	pushSeqCmd(dt, 'scriptCockpitState', control='F-4E/PLT_ENGINE_EXHAUST_R_LARGE', value=int16(0.15), condition='>=', duration=0)
	#pushSeqCmd(5, '', '', 'Wait 5 seconds for engine to light off.')
	# Release ignition.
	pushSeqCmd(dt, 'PLT_THROTTLE_IGNITION_R', 0)
	# Wait for RPM to reach idle (65%).
	pushSeqCmd(dt, 'scriptCockpitState', control='F-4E/PLT_ENGINE_TACH_R_LARGE', value=int16(0.64), condition='>=', duration=3)
	# Right generator ... ON
	pushSeqCmd(dt, 'PLT_ELECTRICS_GENERATOR_R', 2) # 0 = EXTERNAL, 1 = OFF, 2 = GEN

	# Start left engine
	pushSeqCmd(dt, 'scriptSpeech', "Starting left engine.")
	pushSeqCmd(dt, 'PLT_ENGINE_START', 0) # 0 = LEFT, 1 = OFF, 2 = RIGHT
	# Release after 1 second.
	pushSeqCmd(1, 'PLT_ENGINE_START', 1) # 0 = LEFT, 1 = OFF, 2 = RIGHT
	# Wait to get past 10% RPM.
	pushSeqCmd(dt, 'scriptCockpitState', control='F-4E/PLT_ENGINE_TACH_R_LARGE', value=int16(0.1), condition='>=', duration=0)
	# At 10% RPM, press and hold ignition button.
	pushSeqCmd(dt, 'PLT_THROTTLE_IGNITION_L', 1)
	# Advance throttle to idle detent.
	pushSeqCmd(dt, 'PLT_THROTTLE_DETENT_L', 1)
	# Wait for engine to light off.
	pushSeqCmd(dt, 'scriptCockpitState', control='F-4E/PLT_ENGINE_EXHAUST_L_LARGE', value=int16(0.15), condition='>=', duration=0)
	# Release ignition.
	pushSeqCmd(dt, 'PLT_THROTTLE_IGNITION_L', 0)
	# Wait for RPM to reach idle (65%).
	pushSeqCmd(dt, 'scriptCockpitState', control='F-4E/PLT_ENGINE_TACH_L_LARGE', value=int16(0.64), condition='>=', duration=3)
	# Right generator ... ON
	pushSeqCmd(dt, 'PLT_ELECTRICS_GENERATOR_L', 2) # 0 = EXTERNAL, 1 = OFF, 2 = GEN

	# Navigation Computer Mode knob ... STBY
	pushSeqCmd(dt, 'WSO_NAV_MODE', 1) # 0 = OFF, 1 = STBY, 2 = TGT1, 3 = TGT2, 4 = RESET

	# Begin alignment.
	if vars.get('Alignment') == 'BATH':
		# BATH alignment:
		pushSeqCmd(dt, 'scriptSpeech', "Starting BATH alignment.")
		# INS Power knob ... STBY
		pushSeqCmd(dt, 'WSO_INS_POWER', 1) # 0 = OFF, 1 = STBY, 2 = ALIGN, 3 = NAV
		# After 1 second, INS Power knob ... ALIGN
		pushSeqCmd(1, 'WSO_INS_POWER', 2) # 0 = OFF, 1 = STBY, 2 = ALIGN, 3 = NAV
	else:
		# Full alignment:
		pushSeqCmd(dt, 'scriptSpeech', "Starting full alignment.")
		# INS Power knob ... STBY
		pushSeqCmd(dt, 'WSO_INS_POWER', 1) # 0 = OFF, 1 = STBY, 2 = ALIGN, 3 = NAV

	pushSeqCmd(dt, 'PLT_CANOPY_CONTROL', 0) # 0 = Close, 1 = Open
	pushSeqCmd(dt, 'WSO_CANOPY_CONTROL', 0) # 0 = Close, 1 = Open

	# Turn on radar.
	pushSeqCmd(dt, 'WSO_RADAR_POWER', 3) # 0 = OFF, 1 = TEST, 2 = STBY, 3 = OPR, 4 = EMER
	# Turn on DSCG screen..
	pushSeqCmd(dt, 'WSO_RADAR_SCREEN', 4) # 0 = OFF, 1 = STBY, 2 = DSCG TEST, 3 = RDR BIT, 4 = RDR, 5 = TV

	# Radar altimeter ... ON, but leave bug at 0 ft
	pushSeqCmd(dt, 'PLT_RADAR_ALT_MOVE_BUG', "+3200")

	# DSCG screen mode switch
	pushSeqCmd(dt, 'PLT_RADAR_SCREEN_MODE', 0) # 0 = RADAR, 1 = OFF, 2 = TV

	# IFF
	pushSeqCmd(dt, 'PLT_IFF_MASTER', 3) # 0 = OFF, 1 = STBY, 2 = LOW, 3 = NOR, 4 = EMER

	# Antiskid
	pushSeqCmd(dt, 'PLT_GEAR_ANTI_SKID', 1)

	# Backup ADI
	pushSeqCmd(dt, 'PLT_SAI_CAGE', 0)

	# Sight mode
	pushSeqCmd(dt, 'PLT_HUD_MODE', 2) # 0 = OFF, 1 = STBY, 2 = CAGE, 3 = A/G, 4 = A/A, 5 = BIT 1, 6 = BIT 2

	# ADI flight director switch
	pushSeqCmd(dt, 'PLT_FDC_FLIGHT_DIRECTOR', 1)

	# Wait for alignment to complete.
	if vars.get('Alignment') == 'BATH':
		# Wait for ALIGN light to be lit for 2 seconds.  This prevents accidentally triggering the codition if you briefly click the light to test it.  However if the light is completely dimmed, it will never be detected.  Takes ~3 mins.
		pushSeqCmd(dt, 'scriptCockpitState', control='F-4E/WSO_INS_ALIGN', value=0, condition='>', duration=2)
		pushSeqCmd(dt, 'WSO_INS_POWER', 3) # 0 = OFF, 1 = STBY, 2 = ALIGN, 3 = NAV
	else:
		# The HEAT light should come on almost immediately.  Wait for HEAT light to go out, ~5-6 mins.
		pushSeqCmd(dt, 'scriptCockpitState', control='F-4E/WSO_INS_HEAT', value=0, condition='=', duration=2)
		# After the system is warmed up, INS Power knob ... ALIGN
		pushSeqCmd(1, 'WSO_INS_POWER', 2) # 0 = OFF, 1 = STBY, 2 = ALIGN, 3 = NAV
		# Wait for ALIGN light to be lit for 2 seconds.  This means the BATH alignment is complete.  Takes ~3 mins.
		pushSeqCmd(dt, 'scriptCockpitState', control='F-4E/WSO_INS_ALIGN', value=0, condition='>', duration=2)
		# Wait for ALIGN ilght to start flashing.  This means the full alignment is complete.  Takes ~3m45s.
		pushSeqCmd(dt, 'scriptCockpitState', control='F-4E/WSO_INS_ALIGN', value=0, condition='=', duration=0)
		pushSeqCmd(dt, 'scriptCockpitState', control='F-4E/WSO_INS_ALIGN', value=0, condition='>', duration=0)
		pushSeqCmd(dt, 'WSO_INS_POWER', 3) # 0 = OFF, 1 = STBY, 2 = ALIGN, 3 = NAV
	pushSeqCmd(dt, 'scriptSpeech', "Alignment complete.")

	# Reference System switch ... PRIM
	pushSeqCmd(dt, 'PLT_ADI_REFERENCE_SYSTEM  ', 0) # 0 = PRIM, 1 = STBY
	pushSeqCmd(5, '', '', 'Wait for compass.')

	# Compass Sync knob ... SYNC for a few seconds, then release back to SLAVED
	pushSeqCmd(dt, 'PLT_COMPASS_MODE_SYNC', 3) # 0 = COMP, 1 = DC, 2 = SLAVED, 3 = SYNC
	pushSeqCmd(4, 'PLT_COMPASS_MODE_SYNC', 2) # 0 = COMP, 1 = DC, 2 = SLAVED, 3 = SYNC

	# CADC correction
	pushSeqCmd(dt, 'PLT_CADC_CORRECTION', 2) # 0 = OFF, 1 = NORM, 2 = RESET
	pushSeqCmd(4, 'PLT_CADC_CORRECTION', 1) # 0 = OFF, 1 = NORM, 2 = RESET

	# Altimeter (only do this after CADC correction?)
	pushSeqCmd(dt, 'PLT_BARO_MODE', 2)
	# No need to move the lever back after setting it, just wait 3 seconds.
	pushSeqCmd(3, '', '', 'Wait for STBY flag to disappear.')

	# Countermeasures
	pushSeqCmd(dt, 'WSO_CM_CHAFF_MODE', 1) # 0 = OFF, 1 = SGL, 2 = MULT, 3 = PROG
	pushSeqCmd(dt, 'WSO_CM_FLARE_MODE', 1) # 0 = OFF, 1 = SGL, 2 = PROG

	# Stab Aug
	pushSeqCmd(dt, 'PLT_AFCS_STAB_AUG_PITCH', 1)
	pushSeqCmd(dt, 'PLT_AFCS_STAB_AUG_ROLL', 1)
	pushSeqCmd(dt, 'PLT_AFCS_STAB_AUG_YAW', 1)

	# Oxygen
	pushSeqCmd(dt, 'PLT_O2_MIXTURE', 0) # 0 = NORMAL OXYGEN, 1 = 100% OXYGEN
	pushSeqCmd(dt, 'PLT_O2_SUPPLY', 0) # 0 = ON, 1 = OFF
	pushSeqCmd(dt, 'WSO_O2_MIXTURE', 0) # 0 = NORMAL OXYGEN, 1 = 100% OXYGEN
	pushSeqCmd(dt, 'WSO_O2_SUPPLY', 0) # 0 = ON, 1 = OFF

	# RDR MSL CW switch ... CW ON
	pushSeqCmd(dt, 'PLT_WPN_RADAR_MISSILE_CW', 2) # 0 = OFF, 1 = STBY, 2 = CW ON

	# Fuze switch
	pushSeqCmd(dt, 'PLT_WPN_FUZE_ARM', 2) # 0 = SAFE, 1 = NOSE, 2 = NOSE & TAIL, 3 = TAIL

	# Bomb quantity
	pushSeqCmd(dt, 'PLT_WPN_BOMB_QUANTITY', 11) # 0 = P, 1 = S, 2 = C, 3 = 18, 4 = 12, 5 = 9, 6 = 6, 7 = 5, 8 = 4, 9 = 3, 10 = 2, 11 = 1

	# Arm gun
	pushSeqCmd(dt, 'PLT_WPN_GUN_ARM', 1)

	# Master Arm
	pushSeqCmd(dt, 'PLT_WPN_MASTER_ARM',  1)

	# Enable Jester.
	pushSeqCmd(dt, 'F-4E/PLT_JESTER_COMMAND_CREW_PRESENCE_AUTO', 'TOGGLE')
	# Jester, radar to active.
	#pushSeqCmd(dt, 'F-4E/PLT_JESTER_COMMAND_RADAR_OPERATION_ACTIVE', 'TOGGLE')
	# Jester, radar auto-focus on.
	#pushSeqCmd(dt, 'F-4E/PLT_JESTER_COMMAND_RADAR_AUTO_FOCUS_ON', 'TOGGLE')

	pushSeqCmd(dt, 'scriptSpeech', "Manual steps remaining: Lights, Radios.  If carrying drop tanks set External Tanks Feed switch.  Set takeoff trim, 2 units nose down.")

	return seq


def AutoStart(config, vars):
	seq = []
	seqTime = 0
	dt = 0.2

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

	pushSeqCmd(0, '', '', "Running Auto Start sequence")

	if vars.get('Time') == 'Day':
		# Interior lights
		pushSeqCmd(dt, 'PLT_INT_LIGHT_CONSOLE_BRIGHTNESS', int16(1))
		pushSeqCmd(dt, 'PLT_INT_LIGHT_INSTRUMENT_PANEL_BRIGHTNESS', int16(1))
		pushSeqCmd(dt, 'PLT_INT_LIGHT_FLOOD_RED_BRIGHTNESS', 1) # 0 = MED, 1 = DIM, 2 = BRT
		pushSeqCmd(dt, 'PLT_INT_LIGHT_FLOOD_INST_BRIGHTNESS', 1) # Also controls WSO panel.  0 = DIM, 1 = OFF, 2 = BRT
		pushSeqCmd(dt, 'WSO_INT_LIGHT_INSTRUMENT_PANEL_BRIGHTNESS', int16(1))
		pushSeqCmd(dt, 'WSO_INT_LIGHT_CONSOLE_BRIGHTNESS', int16(1))
		pushSeqCmd(dt, 'WSO_INT_LIGHT_FLOOD_RED_BRIGHTNESS', 1) # 0 = MED, 1 = DIM, 2 = BRT
		# Radar screen night filter
		pushSeqCmd(dt, 'PLT_RADAR_NIGHT_FILTER', 0) # 0 = Off, 1 = On
		# Exterior lights
		pushSeqCmd(dt, 'PLT_EXT_LIGHT_FLASH_MODE', 1) # 0 = STEADY, 1 = OFF, 2 = FLASH
	else:
		# Interior lights
		pushSeqCmd(dt, 'PLT_INT_LIGHT_CONSOLE_BRIGHTNESS', int16(0.5))
		pushSeqCmd(dt, 'PLT_INT_LIGHT_INSTRUMENT_PANEL_BRIGHTNESS', int16(0.5))
		pushSeqCmd(dt, 'PLT_INT_LIGHT_FLOOD_RED_BRIGHTNESS', 1) # 0 = MED, 1 = DIM, 2 = BRT
		pushSeqCmd(dt, 'PLT_INT_LIGHT_FLOOD_INST_BRIGHTNESS', 1) # Also controls WSO panel.  0 = DIM, 1 = OFF, 2 = BRT
		pushSeqCmd(dt, 'WSO_INT_LIGHT_INSTRUMENT_PANEL_BRIGHTNESS', int16(0.5))
		pushSeqCmd(dt, 'WSO_INT_LIGHT_CONSOLE_BRIGHTNESS', int16(0.5))
		pushSeqCmd(dt, 'WSO_INT_LIGHT_FLOOD_RED_BRIGHTNESS', 1) # 0 = MED, 1 = DIM, 2 = BRT
		# Radar screen night filter
		pushSeqCmd(dt, 'PLT_RADAR_NIGHT_FILTER', 1) # 0 = Off, 1 = On
		# Exterior lights
		pushSeqCmd(dt, 'PLT_EXT_LIGHT_FLASH_MODE', 1) # 0 = STEADY, 1 = OFF, 2 = FLASH

	pushSeqCmd(dt, 'PLT_CANOPY_CONTROL', 0) # 0 = Close, 1 = Open

	# Radar altimeter ... ON, but leave bug at 0 ft
	pushSeqCmd(dt, 'PLT_RADAR_ALT_MOVE_BUG', "+3200")

	# DSCG screen mode switch
	pushSeqCmd(dt, 'PLT_RADAR_SCREEN_MODE', 0) # 0 = RADAR, 1 = OFF, 2 = TV

	# IFF
	pushSeqCmd(dt, 'PLT_IFF_MASTER', 3) # 0 = OFF, 1 = STBY, 2 = LOW, 3 = NOR, 4 = EMER

	# Antiskid
	pushSeqCmd(dt, 'PLT_GEAR_ANTI_SKID', 1)

	# Backup ADI
	pushSeqCmd(dt, 'PLT_SAI_CAGE', 0)

	# Sight mode
	pushSeqCmd(dt, 'PLT_HUD_MODE', 2) # 0 = OFF, 1 = STBY, 2 = CAGE, 3 = A/G, 4 = A/A, 5 = BIT 1, 6 = BIT 2

	# ADI flight director switch
	pushSeqCmd(dt, 'PLT_FDC_FLIGHT_DIRECTOR', 1)

	# Compass Sync knob ... SYNC for a few seconds, then release back to SLAVED
	pushSeqCmd(dt, 'PLT_COMPASS_MODE_SYNC', 3) # 0 = COMP, 1 = DC, 2 = SLAVED, 3 = SYNC
	pushSeqCmd(4, 'PLT_COMPASS_MODE_SYNC', 2) # 0 = COMP, 1 = DC, 2 = SLAVED, 3 = SYNC

	# CADC correction
	pushSeqCmd(dt, 'PLT_CADC_CORRECTION', 2) # 0 = OFF, 1 = NORM, 2 = RESET
	pushSeqCmd(4, 'PLT_CADC_CORRECTION', 1) # 0 = OFF, 1 = NORM, 2 = RESET

	# Stab Aug
	pushSeqCmd(dt, 'PLT_AFCS_STAB_AUG_PITCH', 1)
	pushSeqCmd(dt, 'PLT_AFCS_STAB_AUG_ROLL', 1)
	pushSeqCmd(dt, 'PLT_AFCS_STAB_AUG_YAW', 1)

	# Oxygen
	pushSeqCmd(dt, 'PLT_O2_MIXTURE', 0) # 0 = NORMAL OXYGEN, 1 = 100% OXYGEN

	# RDR MSL CW switch ... CW ON
	pushSeqCmd(dt, 'PLT_WPN_RADAR_MISSILE_CW', 2) # 0 = OFF, 1 = STBY, 2 = CW ON

	# Master Arm
	pushSeqCmd(dt, 'PLT_WPN_MASTER_ARM',  1)

	pushSeqCmd(dt, 'scriptSpeech', "Manual steps remaining: Lights, Radios.  If carrying drop tanks set External Tanks Feed switch.")

	return seq


def HotStart(config, vars):
	seq = []
	seqTime = 0
	dt = 0.2

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

	if vars.get('Time') == 'Day':
		# Interior lights
		pushSeqCmd(dt, 'PLT_INT_LIGHT_CONSOLE_BRIGHTNESS', int16(1))
		pushSeqCmd(dt, 'PLT_INT_LIGHT_INSTRUMENT_PANEL_BRIGHTNESS', int16(1))
		pushSeqCmd(dt, 'PLT_INT_LIGHT_FLOOD_RED_BRIGHTNESS', 1) # 0 = MED, 1 = DIM, 2 = BRT
		pushSeqCmd(dt, 'PLT_INT_LIGHT_FLOOD_INST_BRIGHTNESS', 1) # Also controls WSO panel.  0 = DIM, 1 = OFF, 2 = BRT
		pushSeqCmd(dt, 'WSO_INT_LIGHT_INSTRUMENT_PANEL_BRIGHTNESS', int16(1))
		pushSeqCmd(dt, 'WSO_INT_LIGHT_CONSOLE_BRIGHTNESS', int16(1))
		pushSeqCmd(dt, 'WSO_INT_LIGHT_FLOOD_RED_BRIGHTNESS', 1) # 0 = MED, 1 = DIM, 2 = BRT
		# Radar screen night filter
		pushSeqCmd(dt, 'PLT_RADAR_NIGHT_FILTER', 0) # 0 = Off, 1 = On
		# Exterior lights
		pushSeqCmd(dt, 'PLT_EXT_LIGHT_FLASH_MODE', 1) # 0 = STEADY, 1 = OFF, 2 = FLASH
	else:
		# Interior lights
		pushSeqCmd(dt, 'PLT_INT_LIGHT_CONSOLE_BRIGHTNESS', int16(0.5))
		pushSeqCmd(dt, 'PLT_INT_LIGHT_INSTRUMENT_PANEL_BRIGHTNESS', int16(0.5))
		pushSeqCmd(dt, 'PLT_INT_LIGHT_FLOOD_RED_BRIGHTNESS', 1) # 0 = MED, 1 = DIM, 2 = BRT
		pushSeqCmd(dt, 'PLT_INT_LIGHT_FLOOD_INST_BRIGHTNESS', 1) # Also controls WSO panel.  0 = DIM, 1 = OFF, 2 = BRT
		pushSeqCmd(dt, 'WSO_INT_LIGHT_INSTRUMENT_PANEL_BRIGHTNESS', int16(0.5))
		pushSeqCmd(dt, 'WSO_INT_LIGHT_CONSOLE_BRIGHTNESS', int16(0.5))
		pushSeqCmd(dt, 'WSO_INT_LIGHT_FLOOD_RED_BRIGHTNESS', 1) # 0 = MED, 1 = DIM, 2 = BRT
		# Radar screen night filter
		pushSeqCmd(dt, 'PLT_RADAR_NIGHT_FILTER', 1) # 0 = Off, 1 = On
		# Exterior lights
		pushSeqCmd(dt, 'PLT_EXT_LIGHT_FLASH_MODE', 1) # 0 = STEADY, 1 = OFF, 2 = FLASH

	# Sight mode
	pushSeqCmd(dt, 'PLT_HUD_MODE', 2) # 0 = OFF, 1 = STBY, 2 = CAGE, 3 = A/G, 4 = A/A, 5 = BIT 1, 6 = BIT 2

	# ADI flight director switch
	pushSeqCmd(dt, 'PLT_FDC_FLIGHT_DIRECTOR', 1)

	# Compass Sync knob ... SYNC for a few seconds, then release back to SLAVED
	pushSeqCmd(dt, 'PLT_COMPASS_MODE_SYNC', 3) # 0 = COMP, 1 = DC, 2 = SLAVED, 3 = SYNC
	pushSeqCmd(4, 'PLT_COMPASS_MODE_SYNC', 2) # 0 = COMP, 1 = DC, 2 = SLAVED, 3 = SYNC

	# CADC correction
	pushSeqCmd(dt, 'PLT_CADC_CORRECTION', 2) # 0 = OFF, 1 = NORM, 2 = RESET
	pushSeqCmd(4, 'PLT_CADC_CORRECTION', 1) # 0 = OFF, 1 = NORM, 2 = RESET

	# Countermeasures
	pushSeqCmd(dt, 'WSO_CM_CHAFF_MODE', 1) # 0 = OFF, 1 = SGL, 2 = MULT, 3 = PROG
	pushSeqCmd(dt, 'WSO_CM_FLARE_MODE', 1) # 0 = OFF, 1 = SGL, 2 = PROG

	# RDR MSL CW switch ... CW ON
	pushSeqCmd(dt, 'PLT_WPN_RADAR_MISSILE_CW', 2) # 0 = OFF, 1 = STBY, 2 = CW ON

	# Fuze switch
	pushSeqCmd(dt, 'PLT_WPN_FUZE_ARM', 2) # 0 = SAFE, 1 = NOSE, 2 = NOSE & TAIL, 3 = TAIL

	# Bomb quantity
	pushSeqCmd(dt, 'PLT_WPN_BOMB_QUANTITY', 11) # 0 = P, 1 = S, 2 = C, 3 = 18, 4 = 12, 5 = 9, 6 = 6, 7 = 5, 8 = 4, 9 = 3, 10 = 2, 11 = 1

	# Arm gun
	pushSeqCmd(dt, 'PLT_WPN_GUN_ARM', 1)

	# Master Arm
	pushSeqCmd(dt, 'PLT_WPN_MASTER_ARM',  1)

	pushSeqCmd(dt, 'scriptSpeech', "Manual steps remaining: Lights, Radios.  If carrying drop tanks set External Tanks Feed switch.")

	return seq


def AirStart(config, vars):
	seq = []
	seqTime = 0
	dt = 0.2

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

	if vars.get('Time') == 'Day':
		# Interior lights
		pushSeqCmd(dt, 'PLT_INT_LIGHT_CONSOLE_BRIGHTNESS', int16(1))
		pushSeqCmd(dt, 'PLT_INT_LIGHT_INSTRUMENT_PANEL_BRIGHTNESS', int16(1))
		pushSeqCmd(dt, 'PLT_INT_LIGHT_FLOOD_RED_BRIGHTNESS', 1) # 0 = MED, 1 = DIM, 2 = BRT
		pushSeqCmd(dt, 'PLT_INT_LIGHT_FLOOD_INST_BRIGHTNESS', 1) # Also controls WSO panel.  0 = DIM, 1 = OFF, 2 = BRT
		pushSeqCmd(dt, 'WSO_INT_LIGHT_INSTRUMENT_PANEL_BRIGHTNESS', int16(1))
		pushSeqCmd(dt, 'WSO_INT_LIGHT_CONSOLE_BRIGHTNESS', int16(1))
		pushSeqCmd(dt, 'WSO_INT_LIGHT_FLOOD_RED_BRIGHTNESS', 1) # 0 = MED, 1 = DIM, 2 = BRT
		# Radar screen night filter
		pushSeqCmd(dt, 'PLT_RADAR_NIGHT_FILTER', 0) # 0 = Off, 1 = On
		# Exterior lights
		pushSeqCmd(dt, 'PLT_EXT_LIGHT_FLASH_MODE', 1) # 0 = STEADY, 1 = OFF, 2 = FLASH
	else:
		# Interior lights
		pushSeqCmd(dt, 'PLT_INT_LIGHT_CONSOLE_BRIGHTNESS', int16(0.5))
		pushSeqCmd(dt, 'PLT_INT_LIGHT_INSTRUMENT_PANEL_BRIGHTNESS', int16(0.5))
		pushSeqCmd(dt, 'PLT_INT_LIGHT_FLOOD_RED_BRIGHTNESS', 1) # 0 = MED, 1 = DIM, 2 = BRT
		pushSeqCmd(dt, 'PLT_INT_LIGHT_FLOOD_INST_BRIGHTNESS', 1) # Also controls WSO panel.  0 = DIM, 1 = OFF, 2 = BRT
		pushSeqCmd(dt, 'WSO_INT_LIGHT_INSTRUMENT_PANEL_BRIGHTNESS', int16(0.5))
		pushSeqCmd(dt, 'WSO_INT_LIGHT_CONSOLE_BRIGHTNESS', int16(0.5))
		pushSeqCmd(dt, 'WSO_INT_LIGHT_FLOOD_RED_BRIGHTNESS', 1) # 0 = MED, 1 = DIM, 2 = BRT
		# Radar screen night filter
		pushSeqCmd(dt, 'PLT_RADAR_NIGHT_FILTER', 1) # 0 = Off, 1 = On
		# Exterior lights
		pushSeqCmd(dt, 'PLT_EXT_LIGHT_FLASH_MODE', 1) # 0 = STEADY, 1 = OFF, 2 = FLASH

	# Sight mode
	pushSeqCmd(dt, 'PLT_HUD_MODE', 2) # 0 = OFF, 1 = STBY, 2 = CAGE, 3 = A/G, 4 = A/A, 5 = BIT 1, 6 = BIT 2

	# ADI flight director switch
	pushSeqCmd(dt, 'PLT_FDC_FLIGHT_DIRECTOR', 1)

	# RDR MSL CW switch ... CW ON
	pushSeqCmd(dt, 'PLT_WPN_RADAR_MISSILE_CW', 2) # 0 = OFF, 1 = STBY, 2 = CW ON

	# Fuze switch
	# Air Start defaults to NOSE & TAIL.

	# Bomb quantity
	pushSeqCmd(dt, 'PLT_WPN_BOMB_QUANTITY', 11) # 0 = P, 1 = S, 2 = C, 3 = 18, 4 = 12, 5 = 9, 6 = 6, 7 = 5, 8 = 4, 9 = 3, 10 = 2, 11 = 1

	# Arm gun
	pushSeqCmd(dt, 'PLT_WPN_GUN_ARM', 1)

	# Master Arm
	pushSeqCmd(dt, 'PLT_WPN_MASTER_ARM',  1)

	pushSeqCmd(dt, 'scriptSpeech', "Manual steps remaining: Lights, Radios.  If carrying drop tanks set External Tanks Feed switch.")

	return seq

def Shutdown(self, vars):
	# TODO
	pass
