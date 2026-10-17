# Return a Dictionary of script data.  The 'scripts' key is a list of scripts that users will be selecting from.  Each script has an associated 'function', which is the name of the function in this file that will be called to generate the command sequence, and a dictionary of 'vars' that the user will be prompted to choose from before running the script, and will be passed into the sequence generating function.
def getScriptData():
	return {
		'moduleName': 'F-4E-45MC',
		'scripts': [
			{
				'name': 'Cold Start With Jester',
				'function': 'ColdStartWithJester',
				'vars': {
					'time': {
						'label': 'Time',
						'options': {
							'day': 'Day',
							'night': 'Night',
						},
					},
					'alignment': {
						'label': 'Alignment',
						'options': {
							'bath': 'BATH',
							'full': 'Full',
						},
					},
					'engineStart': {
						'label': 'Engine Start',
						'options': {
							'external': 'External Air',
							'cartridge': 'Cartridge',
						},
					},
				},
			},
			{
				'name': 'Cold Start No Jester',
				'function': 'ColdStartNoJester',
				'autoSelectHook': 'Cold Start',
				'vars': {
					'time': {
						'label': 'Time',
						'options': {
							'day': 'Day',
							'night': 'Night',
						},
					},
					'alignment': {
						'label': 'Alignment',
						'options': {
							'bath': 'BATH',
							'full': 'Full',
						},
					},
					'engineStart': {
						'label': 'Engine Start',
						'options': {
							'external': 'External Air',
							'cartridge': 'Cartridge',
						},
					},
				},
			},
			{
				'name': 'Auto Start (run after auto start is complete)',
				'function': 'AutoStart',
				'vars': {
					'time': {
						'label': 'Time',
						'options': {
							'day': 'Day',
							'night': 'Night',
						},
					},
				},
			},
			{
				'name': 'Hot Start',
				'function': 'HotStart',
				'vars': {
					'time': {
						'label': 'Time',
						'options': {
							'day': 'Day',
							'night': 'Night',
						},
					},
				},
			},
			{
				'name': 'Air Start',
				'function': 'AirStart',
				'vars': {
					'time': {
						'label': 'Time',
						'options': {
							'day': 'Day',
							'night': 'Night',
						},
					},
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
			#		'time': {
			#			'label': 'Time',
			#			'options': {
			#				'day': 'Day',
			#				'night': 'Night',
			#			},
			#		},
			#		'alignment': {
			#			'label': 'Alignment',
			#			'options': {
			#				'bath': 'BATH',
			#				'full': 'Full',
			#			},
			#		},
			#	},
			#},
			#{
			#	'name': 'Jester Command Test',
			#	'function': 'JesterCommandTest',
			#	'vars': {
			#		'time': {
			#			'label': 'Time',
			#			'options': {
			#				'day': 'Day',
			#				'night': 'Night',
			#			},
			#		},
			#		'alignment': {
			#			'label': 'Alignment',
			#			'options': {
			#				'bath': 'BATH',
			#				'full': 'Full',
			#			},
			#		},
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

def Test(config, vars, helper, *args, **kwargs):
	seq = []
	dt = 0.3

	pushSeqCmd = helper.makePushSeqCmd(seq)

	# Test code here...

	# Put on helmet.
	pushSeqCmd(dt, 'COCKPITMECHANICS.HIDE_HELMET_PILOT', 0) # 0 = Helmet On, 1 = Helmet Off
	pushSeqCmd(14, '', '', 'Wait for boarding ladder to be removed.')

	if vars.get('time') == 'day':
		# Interior lights
		pushSeqCmd(dt, 'INTERIOR_LIGHTS.PILOT_COCKPIT_LIGHTS_CONSOLE_BRIGHTNESS_KNOB', int16(1))
		pushSeqCmd(dt, 'INTERIOR_LIGHTS.PILOT_COCKPIT_LIGHTS_INSTRUMENT_PANEL_BRIGHTNESS_KNOB', int16(1))
		pushSeqCmd(dt, 'INTERIOR_LIGHTS.PILOT_COCKPIT_LIGHTS_CONSOLE_FLOODLIGHT_BRIGHTNESS_SWITCH', 1) # 0 = MED, 1 = DIM, 2 = BRT
		pushSeqCmd(dt, 'INTERIOR_LIGHTS.PILOT_RIGHT_WALL_INSTRUMENT_FLOODLIGHT_BRIGHTNESS_SWITCH', 1) # Also controls WSO panel.  0 = DIM, 1 = OFF, 2 = BRT
		pushSeqCmd(dt, 'INTERIOR_LIGHTS.WSO_COCKPIT_LIGHTS_INSTRUMENT_PANEL_BRIGHTNESS_KNOB', int16(1))
		pushSeqCmd(dt, 'INTERIOR_LIGHTS.WSO_COCKPIT_LIGHTS_CONSOLE_BRIGHTNESS_KNOB', int16(1))
		pushSeqCmd(dt, 'INTERIOR_LIGHTS.WSO_COCKPIT_LIGHTS_CONSOLE_FLOODLIGHT_BRIGHTNESS_SWITCH', 1) # 0 = MED, 1 = DIM, 2 = BRT
		# Radar screen night filter
		pushSeqCmd(dt, 'RADAR.PILOT_DSCG_NIGHT_FILTER', 0) # 0 = Off, 1 = On
		# Exterior lights
		pushSeqCmd(dt, 'EXTERIOR_LIGHTS.PILOT_EXTERIOR_LIGHTS_PANEL_MODE_SWITCH', 1) # 0 = STEADY, 1 = OFF, 2 = FLASH
	else:
		# Interior lights
		pushSeqCmd(dt, 'INTERIOR_LIGHTS.PILOT_COCKPIT_LIGHTS_CONSOLE_BRIGHTNESS_KNOB', int16(0.5))
		pushSeqCmd(dt, 'INTERIOR_LIGHTS.PILOT_COCKPIT_LIGHTS_INSTRUMENT_PANEL_BRIGHTNESS_KNOB', int16(0.5))
		pushSeqCmd(dt, 'INTERIOR_LIGHTS.PILOT_COCKPIT_LIGHTS_CONSOLE_FLOODLIGHT_BRIGHTNESS_SWITCH', 1) # 0 = MED, 1 = DIM, 2 = BRT
		pushSeqCmd(dt, 'INTERIOR_LIGHTS.PILOT_RIGHT_WALL_INSTRUMENT_FLOODLIGHT_BRIGHTNESS_SWITCH', 1) # Also controls WSO panel.  0 = DIM, 1 = OFF, 2 = BRT
		pushSeqCmd(dt, 'INTERIOR_LIGHTS.WSO_COCKPIT_LIGHTS_INSTRUMENT_PANEL_BRIGHTNESS_KNOB', int16(0.5))
		pushSeqCmd(dt, 'INTERIOR_LIGHTS.WSO_COCKPIT_LIGHTS_CONSOLE_BRIGHTNESS_KNOB', int16(0.5))
		pushSeqCmd(dt, 'INTERIOR_LIGHTS.WSO_COCKPIT_LIGHTS_CONSOLE_FLOODLIGHT_BRIGHTNESS_SWITCH', 1) # 0 = MED, 1 = DIM, 2 = BRT
		# Radar screen night filter
		pushSeqCmd(dt, 'RADAR.PILOT_DSCG_NIGHT_FILTER', 1) # 0 = Off, 1 = On
		# Exterior lights
		pushSeqCmd(dt, 'EXTERIOR_LIGHTS.PILOT_EXTERIOR_LIGHTS_PANEL_MODE_SWITCH', 1) # 0 = STEADY, 1 = OFF, 2 = FLASH

	# Radios
	pushSeqCmd(dt, 'ARC164.UHF_Mode_Selector_Knob', 1) # 0 = OFF, 1 = T/R, 2 = T/R+G, 3 = ADF+G, 4 = ADF, 5 = GUARD
	pushSeqCmd(dt, 'ARC164.RIO_UHF_Mode_Selector_Knob', 1) # 0 = OFF, 1 = T/R, 2 = T/R+G, 3 = ADF+G, 4 = ADF, 5 = GUARD

	# Engine Master Switches ... ON
	# Turning on master switches before loading cartridges makes the crew chief respond by voice.  If switches aren't on, cartridges will be installed, but crew chief won't tell you.
	pushSeqCmd(dt, 'ENGINECONTROLS.ENGINES_LeftMasterSwitch', 1)
	pushSeqCmd(dt, 'ENGINECONTROLS.ENGINES_RightMasterSwitch', 1)
	pushSeqCmd(dt, 'scriptSpeech', 'Crew Chief, insert starter cartridges.', asyncFlag=False)
	pushSeqCmd(1, '', '', 'Wait for Jester/Crew Chief to be ready.')

	# Tell Crew Chief to insert starter cartridges.
	pushSeqCmd(dt, 'JESTER_WHEEL.CREW_CHIEF_COMMAND_AIR_SOURCE_LOAD_CARTRIDGES', 1)
	pushSeqCmd(dt, 'JESTER_WHEEL.CREW_CHIEF_COMMAND_AIR_SOURCE_LOAD_CARTRIDGES', 0) # Send 0 to reset the command after triggering it.
	pushSeqCmd(14, '', '', 'Wait for cartridges to be installed.')

	# Start right engine
	pushSeqCmd(dt, 'scriptSpeech', "Starting right engine.")
	pushSeqCmd(dt, 'ENGINECONTROLS.ENGINES_StartSwitch', 2) # 0 = LEFT, 1 = OFF, 2 = RIGHT
	# Release after 1 second.
	pushSeqCmd(1, 'ENGINECONTROLS.ENGINES_StartSwitch', 1) # 0 = LEFT, 1 = OFF, 2 = RIGHT
	# Wait to get past 10% RPM.
	pushSeqCmd(dt, 'scriptCockpitState', control='F-4E-45MC/arg.ENGINES_TACHOMETER_RIGHT_GAUGE', value=0.1, condition='>=', duration=0)
	# At 10% RPM, press and hold ignition button.
	pushSeqCmd(dt, 'ENGINECONTROLS.ENGINES_RightIgnition', 1)
	# Advance throttle to idle detent.
	pushSeqCmd(dt, 'ENGINECONTROLS.ENGINES_IdleStopRight_TOGGLE', 1)
	# Wait for engine to light off.
	pushSeqCmd(dt, 'scriptCockpitState', control='F-4E-45MC/arg.ENGINES_EXHAUST_TEMP_RIGHT_GAUGE', value=0.15, condition='>=', duration=0)
	#pushSeqCmd(5, '', '', 'Wait 5 seconds for engine to light off.')
	# Release ignition.
	pushSeqCmd(dt, 'ENGINECONTROLS.ENGINES_RightIgnition', 0)
	# Wait for RPM to reach idle (65%).
	pushSeqCmd(dt, 'scriptCockpitState', control='F-4E-45MC/arg.ENGINES_TACHOMETER_RIGHT_GAUGE', value=0.64, condition='>=', duration=3)
	# Right generator ... ON
	pushSeqCmd(dt, 'ELECTRICS.PILOT_R_GEN_SWITCH', 2) # 0 = EXTERNAL, 1 = OFF, 2 = GEN

	# Start left engine
	pushSeqCmd(dt, 'scriptSpeech', "Starting left engine.")
	pushSeqCmd(dt, 'ENGINECONTROLS.ENGINES_StartSwitch', 0) # 0 = LEFT, 1 = OFF, 2 = RIGHT
	# Release after 1 second.
	pushSeqCmd(1, 'ENGINECONTROLS.ENGINES_StartSwitch', 1) # 0 = LEFT, 1 = OFF, 2 = RIGHT
	# Wait to get past 10% RPM.
	pushSeqCmd(dt, 'scriptCockpitState', control='F-4E-45MC/arg.ENGINES_TACHOMETER_RIGHT_GAUGE', value=0.1, condition='>=', duration=0)
	# At 10% RPM, press and hold ignition button.
	pushSeqCmd(dt, 'ENGINECONTROLS.ENGINES_LeftIgnition', 1)
	# Advance throttle to idle detent.
	pushSeqCmd(dt, 'ENGINECONTROLS.ENGINES_IdleStopLeft_TOGGLE', 1)
	# Wait for engine to light off.
	pushSeqCmd(dt, 'scriptCockpitState', control='F-4E-45MC/arg.ENGINES_EXHAUST_TEMP_LEFT_GAUGE', value=0.15, condition='>=', duration=0)
	# Release ignition.
	pushSeqCmd(dt, 'ENGINECONTROLS.ENGINES_LeftIgnition', 0)
	# Wait for RPM to reach idle (65%).
	pushSeqCmd(dt, 'scriptCockpitState', control='F-4E-45MC/arg.ENGINES_TACHOMETER_LEFT_GAUGE', value=0.64, condition='>=', duration=3)
	# Right generator ... ON
	pushSeqCmd(dt, 'ELECTRICS.PILOT_L_GEN_SWITCH', 2) # 0 = EXTERNAL, 1 = OFF, 2 = GEN

	pushSeqCmd(dt, 'JESTER_WHEEL.JESTER_COMMAND_CREW_START_ALIGNMENT', 1)
	pushSeqCmd(dt, 'JESTER_WHEEL.JESTER_COMMAND_CREW_START_ALIGNMENT', 0)

	pushSeqCmd(dt, '', '', 'Wait for Jester prompt')
	pushSeqCmd(5, '', '', 'Prompt should be visible')
	pushSeqCmd(dt, 'JESTER_WHEEL.PILOT_JESTER_OPTION_CENTER', 1) # Jester UI Middle/Select (W)
	pushSeqCmd(dt, 'JESTER_WHEEL.PILOT_JESTER_OPTION_CENTER', 0)
	pushSeqCmd(dt, 'JESTER_WHEEL.PILOT_JESTER_OPTION_2', 1)
	pushSeqCmd(dt, 'JESTER_WHEEL.PILOT_JESTER_OPTION_2', 0)

	return seq


def JesterCommandTest(config, vars, helper, *args, **kwargs):
	seq = []
	dt = 0.3

	pushSeqCmd = helper.makePushSeqCmd(seq)

	"""
	The only one of these that seems to work is JESTER_WHEEL.JESTER_COMMAND_CREW_PRESENCE_DISABLED.  None of the others seem to do anything.
	"""
	#pushSeqCmd(dt, 'JESTER_WHEEL.JESTER_COMMAND_CREW_PRESENCE_DISABLED', 1)
	#pushSeqCmd(dt, 'JESTER_WHEEL.JESTER_COMMAND_CREW_PRESENCE_AUTO', 1)
	#pushSeqCmd(dt, 'F-4E/PLT_JESTER_COMMAND_RADAR_OPERATION_STANDBY ', 'TOGGLE')
	#pushSeqCmd(dt, 'F-4E/PLT_JESTER_COMMAND_RADAR_OPERATION_ACTIVE', 'TOGGLE')
	#pushSeqCmd(dt, 'F-4E/PLT_JESTER_COMMAND_RADAR_RANGE_25_NARROW', 'TOGGLE')

	"""
	The Jester wheel interface does work, but it's clunky and not idempotent.  When you open it, it may be in the base menu, a sub-menu, or in a selector.  Press LShift-1 to go up/back one level, but if you press it while at the base menu the wheel will close.  You can put the wheel into a known state by pressing "A, LShift-1, LShift-1, LShift-1", which will always close the wheel and leave it at the base menu, but that's time consuming.

	You can close the wheel by holding down A for 0.5 seconds (other times may work also, but probably can't be much shorter than that).  If the wheel is already closed, long-A will also open it.  To close the wheel idempotically, press LShift-1, which will close the wheel if it's open, but won't open it if it's closed.
	"""

	# This will open the wheel, return to the base menu, and close it.
	pushSeqCmd(dt, 'JESTER_WHEEL.PILOT_JESTER_UI_ACTION', 1) # Jester UI Action, opens the wheel (A)
	pushSeqCmd(dt, 'JESTER_WHEEL.PILOT_JESTER_UI_ACTION', 0)
	pushSeqCmd(1, '', '', 'wait')
	pushSeqCmd(dt, 'JESTER_WHEEL.PILOT_JESTER_OPTION_BACK', 1) # Jester UI Back (LShift+1)
	pushSeqCmd(dt, 'JESTER_WHEEL.PILOT_JESTER_OPTION_BACK', 0)
	pushSeqCmd(1, '', '', 'wait')
	pushSeqCmd(dt, 'JESTER_WHEEL.PILOT_JESTER_OPTION_BACK', 1) # Jester UI Back (LShift+1)
	pushSeqCmd(dt, 'JESTER_WHEEL.PILOT_JESTER_OPTION_BACK', 0)
	pushSeqCmd(1, '', '', 'wait')
	pushSeqCmd(dt, 'JESTER_WHEEL.PILOT_JESTER_OPTION_BACK', 1) # Jester UI Back (LShift+1)
	pushSeqCmd(dt, 'JESTER_WHEEL.PILOT_JESTER_OPTION_BACK', 0)

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
	pushSeqCmd(dt, 'JESTER_WHEEL.PILOT_JESTER_UI_ACTION', 1) # Jester UI Action, opens the wheel (A)
	pushSeqCmd(dt, 'JESTER_WHEEL.PILOT_JESTER_UI_ACTION', 0)
	pushSeqCmd(1, '', '', 'wait')
	# Radar
	pushSeqCmd(dt, 'JESTER_WHEEL.PILOT_JESTER_OPTION_2', 1) # Jester UI Option 2 (LCtrl+2)
	pushSeqCmd(dt, 'JESTER_WHEEL.PILOT_JESTER_OPTION_2', 0)
	pushSeqCmd(1, '', '', 'wait')
	# ScanType
	pushSeqCmd(dt, 'JESTER_WHEEL.PILOT_JESTER_OPTION_5', 1) # Jester UI Option 5 (LCtrl+5)
	pushSeqCmd(dt, 'JESTER_WHEEL.PILOT_JESTER_OPTION_5', 0)
	pushSeqCmd(1, '', '', 'wait')
	# 25 nm narrow
	pushSeqCmd(dt, 'JESTER_WHEEL.PILOT_JESTER_OPTION_RIGHT', 1) # Jester UI Right (E)
	pushSeqCmd(dt, 'JESTER_WHEEL.PILOT_JESTER_OPTION_RIGHT', 0)
	pushSeqCmd(1, '', '', 'wait')
	pushSeqCmd(dt, 'JESTER_WHEEL.PILOT_JESTER_OPTION_CENTER', 1) # Jester UI Middle/Select (W)
	pushSeqCmd(dt, 'JESTER_WHEEL.PILOT_JESTER_OPTION_CENTER', 0)

	return seq


def ColdStartWithJester(config, vars, helper, *args, **kwargs):
	seq = []
	dt = 0.2

	pushSeqCmd = helper.makePushSeqCmd(seq)

	pushSeqCmd(0, '', '', "Running Cold Start sequence")

	# Put on helmet.
	pushSeqCmd(dt, 'COCKPITMECHANICS.HIDE_HELMET_PILOT', 0) # 0 = Helmet On, 1 = Helmet Off
	pushSeqCmd(14, '', '', 'Wait for boarding ladder to be removed.')

	if vars.get('time') == 'day':
		# Interior lights
		pushSeqCmd(dt, 'INTERIOR_LIGHTS.PILOT_COCKPIT_LIGHTS_CONSOLE_BRIGHTNESS_KNOB', int16(1))
		pushSeqCmd(dt, 'INTERIOR_LIGHTS.PILOT_COCKPIT_LIGHTS_INSTRUMENT_PANEL_BRIGHTNESS_KNOB', int16(1))
		pushSeqCmd(dt, 'INTERIOR_LIGHTS.PILOT_COCKPIT_LIGHTS_CONSOLE_FLOODLIGHT_BRIGHTNESS_SWITCH', 1) # 0 = MED, 1 = DIM, 2 = BRT
		pushSeqCmd(dt, 'INTERIOR_LIGHTS.PILOT_RIGHT_WALL_INSTRUMENT_FLOODLIGHT_BRIGHTNESS_SWITCH', 1) # Also controls WSO panel.  0 = DIM, 1 = OFF, 2 = BRT
		pushSeqCmd(dt, 'INTERIOR_LIGHTS.WSO_COCKPIT_LIGHTS_INSTRUMENT_PANEL_BRIGHTNESS_KNOB', int16(1))
		pushSeqCmd(dt, 'INTERIOR_LIGHTS.WSO_COCKPIT_LIGHTS_CONSOLE_BRIGHTNESS_KNOB', int16(1))
		pushSeqCmd(dt, 'INTERIOR_LIGHTS.WSO_COCKPIT_LIGHTS_CONSOLE_FLOODLIGHT_BRIGHTNESS_SWITCH', 1) # 0 = MED, 1 = DIM, 2 = BRT
		# Radar screen night filter
		pushSeqCmd(dt, 'RADAR.PILOT_DSCG_NIGHT_FILTER', 0) # 0 = Off, 1 = On
		# Exterior lights
		pushSeqCmd(dt, 'EXTERIOR_LIGHTS.PILOT_EXTERIOR_LIGHTS_PANEL_MODE_SWITCH', 1) # 0 = STEADY, 1 = OFF, 2 = FLASH
	else:
		# Interior lights
		pushSeqCmd(dt, 'INTERIOR_LIGHTS.PILOT_COCKPIT_LIGHTS_CONSOLE_BRIGHTNESS_KNOB', int16(0.5))
		pushSeqCmd(dt, 'INTERIOR_LIGHTS.PILOT_COCKPIT_LIGHTS_INSTRUMENT_PANEL_BRIGHTNESS_KNOB', int16(0.5))
		pushSeqCmd(dt, 'INTERIOR_LIGHTS.PILOT_COCKPIT_LIGHTS_CONSOLE_FLOODLIGHT_BRIGHTNESS_SWITCH', 1) # 0 = MED, 1 = DIM, 2 = BRT
		pushSeqCmd(dt, 'INTERIOR_LIGHTS.PILOT_RIGHT_WALL_INSTRUMENT_FLOODLIGHT_BRIGHTNESS_SWITCH', 1) # Also controls WSO panel.  0 = DIM, 1 = OFF, 2 = BRT
		pushSeqCmd(dt, 'INTERIOR_LIGHTS.WSO_COCKPIT_LIGHTS_INSTRUMENT_PANEL_BRIGHTNESS_KNOB', int16(0.5))
		pushSeqCmd(dt, 'INTERIOR_LIGHTS.WSO_COCKPIT_LIGHTS_CONSOLE_BRIGHTNESS_KNOB', int16(0.5))
		pushSeqCmd(dt, 'INTERIOR_LIGHTS.WSO_COCKPIT_LIGHTS_CONSOLE_FLOODLIGHT_BRIGHTNESS_SWITCH', 1) # 0 = MED, 1 = DIM, 2 = BRT
		# Radar screen night filter
		pushSeqCmd(dt, 'RADAR.PILOT_DSCG_NIGHT_FILTER', 1) # 0 = Off, 1 = On
		# Exterior lights
		pushSeqCmd(dt, 'EXTERIOR_LIGHTS.PILOT_EXTERIOR_LIGHTS_PANEL_MODE_SWITCH', 1) # 0 = STEADY, 1 = OFF, 2 = FLASH

	# Radios
	pushSeqCmd(dt, 'ARC164.UHF_Mode_Selector_Knob', 1) # 0 = OFF, 1 = T/R, 2 = T/R+G, 3 = ADF+G, 4 = ADF, 5 = GUARD
	pushSeqCmd(dt, 'ARC164.RIO_UHF_Mode_Selector_Knob', 1) # 0 = OFF, 1 = T/R, 2 = T/R+G, 3 = ADF+G, 4 = ADF, 5 = GUARD

	# Engine Master Switches ... ON
	# Turning on master switches before loading cartridges makes the crew chief respond by voice.  If switches aren't on, cartridges will be installed, but crew chief won't tell you.
	pushSeqCmd(dt, 'ENGINECONTROLS.ENGINES_LeftMasterSwitch', 1)
	pushSeqCmd(dt, 'ENGINECONTROLS.ENGINES_RightMasterSwitch', 1)
	pushSeqCmd(dt, 'scriptSpeech', 'Crew Chief, insert starter cartridges.')
	pushSeqCmd(2, '', '', 'Wait for Crew Chief to be ready.')

	# Tell Crew Chief to insert starter cartridges.
	pushSeqCmd(dt, 'JESTER_WHEEL.CREW_CHIEF_COMMAND_AIR_SOURCE_LOAD_CARTRIDGES', 1)
	pushSeqCmd(dt, 'JESTER_WHEEL.CREW_CHIEF_COMMAND_AIR_SOURCE_LOAD_CARTRIDGES', 0) # Send 0 to reset the command after triggering it.
	pushSeqCmd(14, '', '', 'Wait for cartridges to be installed.')

	# Start right engine
	pushSeqCmd(dt, 'scriptSpeech', "Starting right engine.")
	pushSeqCmd(dt, 'ENGINECONTROLS.ENGINES_StartSwitch', 2) # 0 = LEFT, 1 = OFF, 2 = RIGHT
	# Release after 1 second.
	pushSeqCmd(1, 'ENGINECONTROLS.ENGINES_StartSwitch', 1) # 0 = LEFT, 1 = OFF, 2 = RIGHT
	# Wait to get past 10% RPM.
	pushSeqCmd(dt, 'scriptCockpitState', control='F-4E-45MC/arg.ENGINES_TACHOMETER_RIGHT_GAUGE', value=0.1, condition='>=', duration=0)
	# At 10% RPM, press and hold ignition button.
	pushSeqCmd(dt, 'ENGINECONTROLS.ENGINES_RightIgnition', 1)
	# Advance throttle to idle detent.
	pushSeqCmd(dt, 'ENGINECONTROLS.ENGINES_IdleStopRight_TOGGLE', 1)
	# Wait for engine to light off.
	pushSeqCmd(dt, 'scriptCockpitState', control='F-4E-45MC/arg.ENGINES_EXHAUST_TEMP_RIGHT_GAUGE', value=0.15, condition='>=', duration=0)
	#pushSeqCmd(5, '', '', 'Wait 5 seconds for engine to light off.')
	# Release ignition.
	pushSeqCmd(dt, 'ENGINECONTROLS.ENGINES_RightIgnition', 0)
	# Wait for RPM to reach idle (65%).
	pushSeqCmd(dt, 'scriptCockpitState', control='F-4E-45MC/arg.ENGINES_TACHOMETER_RIGHT_GAUGE', value=0.64, condition='>=', duration=3)
	# Right generator ... ON
	pushSeqCmd(dt, 'ELECTRICS.PILOT_R_GEN_SWITCH', 2) # 0 = EXTERNAL, 1 = OFF, 2 = GEN

	# Start left engine
	pushSeqCmd(dt, 'scriptSpeech', "Starting left engine.")
	pushSeqCmd(dt, 'ENGINECONTROLS.ENGINES_StartSwitch', 0) # 0 = LEFT, 1 = OFF, 2 = RIGHT
	# Release after 1 second.
	pushSeqCmd(1, 'ENGINECONTROLS.ENGINES_StartSwitch', 1) # 0 = LEFT, 1 = OFF, 2 = RIGHT
	# Wait to get past 10% RPM.
	pushSeqCmd(dt, 'scriptCockpitState', control='F-4E-45MC/arg.ENGINES_TACHOMETER_RIGHT_GAUGE', value=0.1, condition='>=', duration=0)
	# At 10% RPM, press and hold ignition button.
	pushSeqCmd(dt, 'ENGINECONTROLS.ENGINES_LeftIgnition', 1)
	# Advance throttle to idle detent.
	pushSeqCmd(dt, 'ENGINECONTROLS.ENGINES_IdleStopLeft_TOGGLE', 1)
	# Wait for engine to light off.
	pushSeqCmd(dt, 'scriptCockpitState', control='F-4E-45MC/arg.ENGINES_EXHAUST_TEMP_LEFT_GAUGE', value=0.15, condition='>=', duration=0)
	# Release ignition.
	pushSeqCmd(dt, 'ENGINECONTROLS.ENGINES_LeftIgnition', 0)
	# Wait for RPM to reach idle (65%).
	pushSeqCmd(dt, 'scriptCockpitState', control='F-4E-45MC/arg.ENGINES_TACHOMETER_LEFT_GAUGE', value=0.64, condition='>=', duration=3)
	# Right generator ... ON
	pushSeqCmd(dt, 'ELECTRICS.PILOT_L_GEN_SWITCH', 2) # 0 = EXTERNAL, 1 = OFF, 2 = GEN

	# Prompt Jester to start alignment as soon as the generator is on.
	pushSeqCmd(dt, 'JESTER_WHEEL.JESTER_COMMAND_CREW_START_ALIGNMENT', 1)
	pushSeqCmd(dt, 'JESTER_WHEEL.JESTER_COMMAND_CREW_START_ALIGNMENT', 0)
	pushSeqCmd(dt, '', '', 'Wait for Jester prompt')
	pushSeqCmd(5, '', '', 'Prompt should be visible')
	pushSeqCmd(dt, 'JESTER_WHEEL.PILOT_JESTER_OPTION_CENTER', 1) # Jester UI Middle/Select (W)
	pushSeqCmd(dt, 'JESTER_WHEEL.PILOT_JESTER_OPTION_CENTER', 0)
	# Option 1 for Full alignment.  Option 2 for BATH alignment.
	pushSeqCmd(dt, 'JESTER_WHEEL.PILOT_JESTER_OPTION_2', 1)
	pushSeqCmd(dt, 'JESTER_WHEEL.PILOT_JESTER_OPTION_2', 0)

	pushSeqCmd(dt, 'CANOPYCONTROLS.CANOPYCONTROLS_ActuatePilotCanopy', 0) # 0 = Close, 1 = Open

	# Radar altimeter ... ON, but leave bug at 0 ft
	pushSeqCmd(dt, 'RADARALTIMETER.RADAR_ALTIMETER_LowAltSet', 0.1)

	# DSCG screen mode switch
	pushSeqCmd(dt, 'RADAR.PILOT_DSCG_MODE', 0) # 0 = RADAR, 1 = OFF, 2 = TV

	# IFF
	pushSeqCmd(dt, 'IFF.PILOT_IFF_MASTER_Knob', 3) # 0 = OFF, 1 = STBY, 2 = LOW, 3 = NOR, 4 = EMER

	# Antiskid
	pushSeqCmd(dt, 'GEARANDHOOK.LANDING_GEAR_AntiSkid', 1)

	# Backup ADI
	pushSeqCmd(dt, 'EMERGENCYATTITUDEINDICATOR.EMERG_ADI_Cage', 0)

	# Sight mode
	pushSeqCmd(dt, 'HUD_AN_ASG_26.HUD_SelectHUDMode', 2) # 0 = OFF, 1 = STBY, 2 = CAGE, 3 = A/G, 4 = A/A, 5 = BIT 1, 6 = BIT 2

	# ADI flight director switch
	pushSeqCmd(dt, 'FLIGHTDIRECTORCOMPUTER.NAV_FUNCT_SEL_PANEL_FD_KNOB', 1)

	# Wait for alignment to complete.  With Jester, that's when he moves the INS Power knob to NAV.
	pushSeqCmd(dt, 'scriptCockpitState', control='F-4E-45MC/INS_AN_ASN_63.INS_WSO_POWER_KNOB', value=3, condition='=', duration=0)
	pushSeqCmd(dt, '', '', 'Wait for Jester to finish talking.')
	pushSeqCmd(7, '', '', 'Finished')
	pushSeqCmd(dt, 'scriptSpeech', "Alignment complete.")

	# Reference System switch ... PRIM
	pushSeqCmd(dt, 'ADI_ARU_11_A.MAINADI_reference_absolute', 0) # 0 = PRIM, 1 = STBY
	pushSeqCmd(5, '', '', 'Wait for compass.')

	# Compass Sync knob ... SYNC for a few seconds, then release back to SLAVED
	pushSeqCmd(dt, 'COMPASSSYSTEM.PILOT_COMPASS_PILOT_MODE_SELECTOR_KNOB', 3) # 0 = COMP, 1 = DC, 2 = SLAVED, 3 = SYNC
	pushSeqCmd(4, 'COMPASSSYSTEM.PILOT_COMPASS_PILOT_MODE_SELECTOR_KNOB', 2) # 0 = COMP, 1 = DC, 2 = SLAVED, 3 = SYNC

	# CADC correction
	pushSeqCmd(dt, 'CADC.SPC_switch', 2) # 0 = OFF, 1 = NORM, 2 = RESET
	pushSeqCmd(4, 'CADC.SPC_switch', 1) # 0 = OFF, 1 = NORM, 2 = RESET

	# Altimeter (only do this after CADC correction?)
	pushSeqCmd(dt, 'BAROMETRICALTIMETER.ALTIMETER_Mode', 2)
	# No need to move the lever back after setting it, just wait 3 seconds.
	pushSeqCmd(3, '', '', 'Wait for STBY flag to disappear.')

	# Countermeasures
	pushSeqCmd(dt, 'COUNTERMEASURES.CHAFF_MODE', 1) # 0 = OFF, 1 = SGL, 2 = MULT, 3 = PROG
	pushSeqCmd(dt, 'COUNTERMEASURES.FLARE_MODE', 1) # 0 = OFF, 1 = SGL, 2 = PROG

	# Stab Aug
	pushSeqCmd(dt, 'INPUTCONTROLS.AFCS_ENGAGE_STAB_AUG_PITCH', 1)
	pushSeqCmd(dt, 'INPUTCONTROLS.AFCS_ENGAGE_STAB_AUG_ROLL', 1)
	pushSeqCmd(dt, 'INPUTCONTROLS.AFCS_ENGAGE_STAB_AUG_YAW', 1)

	# Oxygen
	pushSeqCmd(dt, 'OXYGENSYSTEM.OXYGENSYSTEM_Pilot_Set_Ox_Ratio', 0) # 0 = NORMAL OXYGEN, 1 = 100% OXYGEN
	pushSeqCmd(dt, 'OXYGENSYSTEM.OXYGENSYSTEM_Pilot_Set_Ox_Supply', 0) # 0 = ON, 1 = OFF
	pushSeqCmd(dt, 'OXYGENSYSTEM.OXYGENSYSTEM_RIO_Set_Ox_Ratio', 0) # 0 = NORMAL OXYGEN, 1 = 100% OXYGEN
	pushSeqCmd(dt, 'OXYGENSYSTEM.OXYGENSYSTEM_RIO_Set_Ox_Supply', 0) # 0 = ON, 1 = OFF

	# RDR MSL CW switch ... CW ON
	pushSeqCmd(dt, 'WEAPONS.WEAPONS_CW_Switch', 2) # 0 = OFF, 1 = STBY, 2 = CW ON

	# Fuze switch
	pushSeqCmd(dt, 'WEAPONS.WEAPONS_Arm_Switch', 2) # 0 = SAFE, 1 = NOSE, 2 = NOSE & TAIL, 3 = TAIL

	# Bomb quantity
	pushSeqCmd(dt, 'WEAPONS.WEAPONS_SelectBombQty', 11) # 0 = P, 1 = S, 2 = C, 3 = 18, 4 = 12, 5 = 9, 6 = 6, 7 = 5, 8 = 4, 9 = 3, 10 = 2, 11 = 1

	# Arm gun
	pushSeqCmd(dt, 'WEAPONS.WEAPONS_Gun_Arm', 1)

	# Master Arm
	pushSeqCmd(dt, 'WEAPONS.WEAPONS_Master_Arm',  1)

	# Jester, radar to active.
	#pushSeqCmd(dt, 'F-4E/PLT_JESTER_COMMAND_RADAR_OPERATION_ACTIVE', 'TOGGLE') # FIXME This doesn't work.

	# Jester, radar auto-focus on.
	#pushSeqCmd(dt, 'F-4E/PLT_JESTER_COMMAND_RADAR_AUTO_FOCUS_ON', 'TOGGLE') # FIXME This doesn't work.

	pushSeqCmd(dt, 'scriptSpeech', "Manual steps remaining: Lights, Radios.  If carrying drop tanks set External Tanks Feed switch.  Set takeoff trim, 2 units nose down.  Set up Jester as needed.")

	return seq


def ColdStartNoJester(config, vars, helper, *args, **kwargs):
	seq = []
	dt = 0.2

	pushSeqCmd = helper.makePushSeqCmd(seq)

	def pushJesterCmd(dt, command):
		pushSeqCmd(dt, command, 1)
		pushSeqCmd(dt, command, 0)

	pushSeqCmd(0, '', '', "Running Cold Start sequence")

	# Put on helmet.
	pushSeqCmd(dt, 'COCKPITMECHANICS.HIDE_HELMET_PILOT', 0) # 0 = Helmet On, 1 = Helmet Off
	pushSeqCmd(14, '', '', 'Wait for boarding ladder to be removed.')

	# Disable Jester.
	pushSeqCmd(dt, 'scriptSpeech', 'Disabling Jester for the start sequence.')
	pushJesterCmd(dt, 'JESTER_WHEEL.JESTER_COMMAND_CREW_PRESENCE_DISABLED')

	if vars.get('time') == 'day':
		# Interior lights
		pushSeqCmd(dt, 'INTERIOR_LIGHTS.PILOT_COCKPIT_LIGHTS_CONSOLE_BRIGHTNESS_KNOB', int16(1))
		pushSeqCmd(dt, 'INTERIOR_LIGHTS.PILOT_COCKPIT_LIGHTS_INSTRUMENT_PANEL_BRIGHTNESS_KNOB', int16(1))
		pushSeqCmd(dt, 'INTERIOR_LIGHTS.PILOT_COCKPIT_LIGHTS_CONSOLE_FLOODLIGHT_BRIGHTNESS_SWITCH', 1) # 0 = MED, 1 = DIM, 2 = BRT
		pushSeqCmd(dt, 'INTERIOR_LIGHTS.PILOT_RIGHT_WALL_INSTRUMENT_FLOODLIGHT_BRIGHTNESS_SWITCH', 1) # Also controls WSO panel.  0 = DIM, 1 = OFF, 2 = BRT
		pushSeqCmd(dt, 'INTERIOR_LIGHTS.WSO_COCKPIT_LIGHTS_INSTRUMENT_PANEL_BRIGHTNESS_KNOB', int16(1))
		pushSeqCmd(dt, 'INTERIOR_LIGHTS.WSO_COCKPIT_LIGHTS_CONSOLE_BRIGHTNESS_KNOB', int16(1))
		pushSeqCmd(dt, 'INTERIOR_LIGHTS.WSO_COCKPIT_LIGHTS_CONSOLE_FLOODLIGHT_BRIGHTNESS_SWITCH', 1) # 0 = MED, 1 = DIM, 2 = BRT
		# Radar screen night filter
		pushSeqCmd(dt, 'RADAR.PILOT_DSCG_NIGHT_FILTER', 0) # 0 = Off, 1 = On
		# Exterior lights
		pushSeqCmd(dt, 'EXTERIOR_LIGHTS.PILOT_EXTERIOR_LIGHTS_PANEL_MODE_SWITCH', 1) # 0 = STEADY, 1 = OFF, 2 = FLASH
	else:
		# Interior lights
		pushSeqCmd(dt, 'INTERIOR_LIGHTS.PILOT_COCKPIT_LIGHTS_CONSOLE_BRIGHTNESS_KNOB', int16(0.5))
		pushSeqCmd(dt, 'INTERIOR_LIGHTS.PILOT_COCKPIT_LIGHTS_INSTRUMENT_PANEL_BRIGHTNESS_KNOB', int16(0.5))
		pushSeqCmd(dt, 'INTERIOR_LIGHTS.PILOT_COCKPIT_LIGHTS_CONSOLE_FLOODLIGHT_BRIGHTNESS_SWITCH', 1) # 0 = MED, 1 = DIM, 2 = BRT
		pushSeqCmd(dt, 'INTERIOR_LIGHTS.PILOT_RIGHT_WALL_INSTRUMENT_FLOODLIGHT_BRIGHTNESS_SWITCH', 1) # Also controls WSO panel.  0 = DIM, 1 = OFF, 2 = BRT
		pushSeqCmd(dt, 'INTERIOR_LIGHTS.WSO_COCKPIT_LIGHTS_INSTRUMENT_PANEL_BRIGHTNESS_KNOB', int16(0.5))
		pushSeqCmd(dt, 'INTERIOR_LIGHTS.WSO_COCKPIT_LIGHTS_CONSOLE_BRIGHTNESS_KNOB', int16(0.5))
		pushSeqCmd(dt, 'INTERIOR_LIGHTS.WSO_COCKPIT_LIGHTS_CONSOLE_FLOODLIGHT_BRIGHTNESS_SWITCH', 1) # 0 = MED, 1 = DIM, 2 = BRT
		# Radar screen night filter
		pushSeqCmd(dt, 'RADAR.PILOT_DSCG_NIGHT_FILTER', 1) # 0 = Off, 1 = On
		# Exterior lights
		pushSeqCmd(dt, 'EXTERIOR_LIGHTS.PILOT_EXTERIOR_LIGHTS_PANEL_MODE_SWITCH', 1) # 0 = STEADY, 1 = OFF, 2 = FLASH

	# Radios
	pushSeqCmd(dt, 'ARC164.UHF_Mode_Selector_Knob', 1) # 0 = OFF, 1 = T/R, 2 = T/R+G, 3 = ADF+G, 4 = ADF, 5 = GUARD
	pushSeqCmd(dt, 'ARC164.RIO_UHF_Mode_Selector_Knob', 1) # 0 = OFF, 1 = T/R, 2 = T/R+G, 3 = ADF+G, 4 = ADF, 5 = GUARD

	# Engine Master Switches ... ON
	# Turning on master switches before loading cartridges makes the crew chief respond by voice.  If switches aren't on, cartridges will be installed, but crew chief won't tell you.
	pushSeqCmd(dt, 'ENGINECONTROLS.ENGINES_LeftMasterSwitch', 1)
	pushSeqCmd(dt, 'ENGINECONTROLS.ENGINES_RightMasterSwitch', 1)
	pushSeqCmd(2, '', '', 'Wait for Crew Chief to be ready.')

	if vars.get('engineStart') == 'cartridge':
		# Tell Crew Chief to insert starter cartridges.
		pushSeqCmd(dt, 'scriptSpeech', 'Crew Chief, insert starter cartridges.')
		pushJesterCmd(dt, 'JESTER_WHEEL.CREW_CHIEF_COMMAND_AIR_SOURCE_LOAD_CARTRIDGES')
		pushSeqCmd(14, '', '', 'Wait for cartridges to be installed.')

		# Start right engine
		pushSeqCmd(dt, 'scriptSpeech', "Starting right engine.")
		pushSeqCmd(dt, 'ENGINECONTROLS.ENGINES_StartSwitch', 2) # 0 = LEFT, 1 = OFF, 2 = RIGHT
		# Release after 1 second.
		pushSeqCmd(1, 'ENGINECONTROLS.ENGINES_StartSwitch', 1) # 0 = LEFT, 1 = OFF, 2 = RIGHT
		# Wait to get past 10% RPM.
		pushSeqCmd(dt, 'scriptCockpitState', control='F-4E-45MC/arg.ENGINES_TACHOMETER_RIGHT_GAUGE', value=0.1, condition='>=', duration=0)
		# At 10% RPM, press and hold ignition button.
		pushSeqCmd(dt, 'ENGINECONTROLS.ENGINES_RightIgnition', 1)
		# Advance throttle to idle detent.
		pushSeqCmd(dt, 'ENGINECONTROLS.ENGINES_IdleStopRight_TOGGLE', 1)
		# Wait for engine to light off.
		pushSeqCmd(dt, 'scriptCockpitState', control='F-4E-45MC/arg.ENGINES_EXHAUST_TEMP_RIGHT_GAUGE', value=0.15, condition='>=', duration=0)
		#pushSeqCmd(5, '', '', 'Wait 5 seconds for engine to light off.')
		# Release ignition.
		pushSeqCmd(dt, 'ENGINECONTROLS.ENGINES_RightIgnition', 0)
		# Wait for RPM to reach idle (65%).
		pushSeqCmd(dt, 'scriptCockpitState', control='F-4E-45MC/arg.ENGINES_TACHOMETER_RIGHT_GAUGE', value=0.64, condition='>=', duration=3)
		# Right generator ... ON
		pushSeqCmd(dt, 'ELECTRICS.PILOT_R_GEN_SWITCH', 2) # 0 = EXTERNAL, 1 = OFF, 2 = GEN

		# Start left engine
		pushSeqCmd(dt, 'scriptSpeech', "Starting left engine.")
		pushSeqCmd(dt, 'ENGINECONTROLS.ENGINES_StartSwitch', 0) # 0 = LEFT, 1 = OFF, 2 = RIGHT
		# Release after 1 second.
		pushSeqCmd(1, 'ENGINECONTROLS.ENGINES_StartSwitch', 1) # 0 = LEFT, 1 = OFF, 2 = RIGHT
		# Wait to get past 10% RPM.
		pushSeqCmd(dt, 'scriptCockpitState', control='F-4E-45MC/arg.ENGINES_TACHOMETER_RIGHT_GAUGE', value=0.1, condition='>=', duration=0)
		# At 10% RPM, press and hold ignition button.
		pushSeqCmd(dt, 'ENGINECONTROLS.ENGINES_LeftIgnition', 1)
		# Advance throttle to idle detent.
		pushSeqCmd(dt, 'ENGINECONTROLS.ENGINES_IdleStopLeft_TOGGLE', 1)
		# Wait for engine to light off.
		pushSeqCmd(dt, 'scriptCockpitState', control='F-4E-45MC/arg.ENGINES_EXHAUST_TEMP_LEFT_GAUGE', value=0.15, condition='>=', duration=0)
		# Release ignition.
		pushSeqCmd(dt, 'ENGINECONTROLS.ENGINES_LeftIgnition', 0)
		# Wait for RPM to reach idle (65%).
		pushSeqCmd(dt, 'scriptCockpitState', control='F-4E-45MC/arg.ENGINES_TACHOMETER_LEFT_GAUGE', value=0.64, condition='>=', duration=3)
		# Right generator ... ON
		pushSeqCmd(dt, 'ELECTRICS.PILOT_L_GEN_SWITCH', 2) # 0 = EXTERNAL, 1 = OFF, 2 = GEN
	else:
		# Tell Crew Chief to attach external air to right engine.
		pushSeqCmd(dt, 'scriptSpeech', 'Crew Chief, connect ground air supply to right engine.', asyncFlag=False)
		pushJesterCmd(dt, 'JESTER_WHEEL.CREW_CHIEF_COMMAND_AIR_SOURCE_CONNECT_RIGHT')
		pushSeqCmd(14, '', '', 'Wait for external air to be connected.')

		pushSeqCmd(dt, 'scriptSpeech', 'Crew Chief, start ground air supply.', asyncFlag=False)
		pushJesterCmd(dt, 'JESTER_WHEEL.CREW_CHIEF_COMMAND_AIR_SOURCE_START')
		# Start right engine
		pushSeqCmd(dt, 'scriptSpeech', "Starting right engine.")
		# Wait to get past 10% RPM.
		pushSeqCmd(dt, 'scriptCockpitState', control='F-4E-45MC/arg.ENGINES_TACHOMETER_RIGHT_GAUGE', value=0.1, condition='>=', duration=0)
		# At 10% RPM, press and hold ignition button.
		pushSeqCmd(dt, 'ENGINECONTROLS.ENGINES_RightIgnition', 1)
		# Advance throttle to idle detent.
		pushSeqCmd(dt, 'ENGINECONTROLS.ENGINES_IdleStopRight_TOGGLE', 1)
		# Wait for engine to light off.
		pushSeqCmd(dt, 'scriptCockpitState', control='F-4E-45MC/arg.ENGINES_EXHAUST_TEMP_RIGHT_GAUGE', value=0.15, condition='>=', duration=0)
		#pushSeqCmd(5, '', '', 'Wait 5 seconds for engine to light off.')
		# Release ignition.
		pushSeqCmd(dt, 'ENGINECONTROLS.ENGINES_RightIgnition', 0)
		# Wait for RPM to reach 45% and turn off air.
		pushSeqCmd(dt, 'scriptCockpitState', control='F-4E-45MC/arg.ENGINES_TACHOMETER_RIGHT_GAUGE', value=0.45, condition='>=', duration=0)
		pushSeqCmd(dt, 'scriptSpeech', 'Crew Chief, stop ground air supply.', asyncFlag=False)
		pushJesterCmd(dt, 'JESTER_WHEEL.CREW_CHIEF_COMMAND_AIR_SOURCE_STOP')
		pushSeqCmd(5, '', '', 'Wait for external air to stop.')
		# Connect air to left engine.
		pushSeqCmd(dt, 'scriptSpeech', 'Crew Chief, connect ground air supply to left engine.', asyncFlag=False)
		pushJesterCmd(dt, 'JESTER_WHEEL.CREW_CHIEF_COMMAND_AIR_SOURCE_CONNECT_LEFT')
		pushSeqCmd(5, '', '', 'Wait for external air to be connected.')
		# Wait for RPM to reach idle (65%).
		pushSeqCmd(dt, 'scriptCockpitState', control='F-4E-45MC/arg.ENGINES_TACHOMETER_RIGHT_GAUGE', value=0.64, condition='>=', duration=3)
		# Right generator ... ON
		pushSeqCmd(dt, 'ELECTRICS.PILOT_R_GEN_SWITCH', 2) # 0 = EXTERNAL, 1 = OFF, 2 = GEN

		# Start left engine
		pushSeqCmd(dt, 'scriptSpeech', "Crew Chief, start ground air supply.", asyncFlag=False)
		pushJesterCmd(dt, 'JESTER_WHEEL.CREW_CHIEF_COMMAND_AIR_SOURCE_START')
		# Wait to get past 10% RPM.
		pushSeqCmd(dt, 'scriptCockpitState', control='F-4E-45MC/arg.ENGINES_TACHOMETER_LEFT_GAUGE', value=0.1, condition='>=', duration=0)
		# At 10% RPM, press and hold ignition button.
		pushSeqCmd(dt, 'ENGINECONTROLS.ENGINES_LeftIgnition', 1)
		# Advance throttle to idle detent.
		pushSeqCmd(dt, 'ENGINECONTROLS.ENGINES_IdleStopLeft_TOGGLE', 1)
		# Wait for engine to light off.
		pushSeqCmd(dt, 'scriptCockpitState', control='F-4E-45MC/arg.ENGINES_EXHAUST_TEMP_LEFT_GAUGE', value=0.15, condition='>=', duration=0)
		# Release ignition.
		pushSeqCmd(dt, 'ENGINECONTROLS.ENGINES_LeftIgnition', 0)
		# Wait for RPM to reach 45% and turn off air.
		pushSeqCmd(dt, 'scriptCockpitState', control='F-4E-45MC/arg.ENGINES_TACHOMETER_LEFT_GAUGE', value=0.45, condition='>=', duration=0)
		pushSeqCmd(dt, 'scriptSpeech', 'Crew Chief, stop ground air supply.', asyncFlag=False)
		pushJesterCmd(dt, 'JESTER_WHEEL.CREW_CHIEF_COMMAND_AIR_SOURCE_STOP')
		pushSeqCmd(5, '', '', 'Wait for external air to stop.')
		# Disconnect air supply.
		pushSeqCmd(dt, 'scriptSpeech', 'Crew Chief, disconnect ground air supply.', asyncFlag=False)
		pushJesterCmd(dt, 'JESTER_WHEEL.CREW_CHIEF_COMMAND_AIR_SOURCE_DISCONNECT')
		# Wait for RPM to reach idle (65%).
		pushSeqCmd(dt, 'scriptCockpitState', control='F-4E-45MC/arg.ENGINES_TACHOMETER_LEFT_GAUGE', value=0.64, condition='>=', duration=3)
		# Left generator ... ON
		pushSeqCmd(dt, 'ELECTRICS.PILOT_L_GEN_SWITCH', 2) # 0 = EXTERNAL, 1 = OFF, 2 = GEN

	# Navigation Computer Mode knob ... STBY
	pushSeqCmd(dt, 'NavigationComputer_AN_ASN_46A.RIO_NAV_COMP_FUNCTION_SELECTOR_KNOB', 1) # 0 = OFF, 1 = STBY, 2 = TGT1, 3 = TGT2, 4 = RESET

	# Begin alignment.
	if vars.get('alignment') == 'bath':
		# BATH alignment:
		pushSeqCmd(dt, 'scriptSpeech', "Starting BATH alignment.")
		# INS Power knob ... STBY
		pushSeqCmd(dt, 'INS_AN_ASN_63.INS_WSO_POWER_KNOB', 1) # 0 = OFF, 1 = STBY, 2 = ALIGN, 3 = NAV
		# After 1 second, INS Power knob ... ALIGN
		pushSeqCmd(1, 'INS_AN_ASN_63.INS_WSO_POWER_KNOB', 2) # 0 = OFF, 1 = STBY, 2 = ALIGN, 3 = NAV
	else:
		# Full alignment:
		pushSeqCmd(dt, 'scriptSpeech', "Starting full alignment.")
		# INS Power knob ... STBY
		pushSeqCmd(dt, 'INS_AN_ASN_63.INS_WSO_POWER_KNOB', 1) # 0 = OFF, 1 = STBY, 2 = ALIGN, 3 = NAV

	# Close pilot and WSO canopies.
	pushSeqCmd(dt, 'CANOPYCONTROLS.CANOPYCONTROLS_ActuatePilotCanopy', 0) # 0 = Close, 1 = Open
	pushSeqCmd(dt, 'CANOPYCONTROLS.CANOPYCONTROLS_ActuateCopilotCanopy', 0) # 0 = Close, 1 = Open

	# Turn on radar.
	pushSeqCmd(dt, 'RADAR.RADAR_Power_Knob_RIO', 3) # 0 = OFF, 1 = TEST, 2 = STBY, 3 = OPR, 4 = EMER
	# Turn on DSCG screen..
	pushSeqCmd(dt, 'RADAR.RADAR_SCREEN_MODE', 4) # 0 = OFF, 1 = STBY, 2 = DSCG TEST, 3 = RDR BIT, 4 = RDR, 5 = TV

	# Radar altimeter ... ON, but leave bug at 0 ft
	pushSeqCmd(dt, 'RADARALTIMETER.RADAR_ALTIMETER_LowAltSet', 0.1)

	# DSCG screen mode switch
	pushSeqCmd(dt, 'RADAR.PILOT_DSCG_MODE', 0) # 0 = RADAR, 1 = OFF, 2 = TV

	# IFF
	pushSeqCmd(dt, 'IFF.PILOT_IFF_MASTER_Knob', 3) # 0 = OFF, 1 = STBY, 2 = LOW, 3 = NOR, 4 = EMER

	# Antiskid
	pushSeqCmd(dt, 'GEARANDHOOK.LANDING_GEAR_AntiSkid', 1)

	# Backup ADI
	pushSeqCmd(dt, 'EMERGENCYATTITUDEINDICATOR.EMERG_ADI_Cage', 0)

	# Sight mode
	pushSeqCmd(dt, 'HUD_AN_ASG_26.HUD_SelectHUDMode', 2) # 0 = OFF, 1 = STBY, 2 = CAGE, 3 = A/G, 4 = A/A, 5 = BIT 1, 6 = BIT 2

	# ADI flight director switch
	pushSeqCmd(dt, 'FLIGHTDIRECTORCOMPUTER.NAV_FUNCT_SEL_PANEL_FD_KNOB', 1)

	# Wait for alignment to complete.
	if vars.get('alignment') == 'bath':
		# Wait for ALIGN light to be lit for 2 seconds.  This prevents accidentally triggering the codition if you briefly click the light to test it.  However if the light is completely dimmed, it will never be detected.  Takes ~3 mins.
		pushSeqCmd(dt, 'scriptCockpitState', control='F-4E-45MC/arg.INS_WSO_ALIGN_LIGHT', value=0, condition='>', duration=2)
		pushSeqCmd(dt, 'INS_AN_ASN_63.INS_WSO_POWER_KNOB', 3) # 0 = OFF, 1 = STBY, 2 = ALIGN, 3 = NAV
	else:
		# The HEAT light should come on almost immediately.  Wait for HEAT light to go out, ~5-6 mins.
		pushSeqCmd(dt, 'scriptCockpitState', control='F-4E-45MC/arg.INS_WSO_HEAT_LIGHT', value=0, condition='=', duration=2)
		# After the system is warmed up, INS Power knob ... ALIGN
		pushSeqCmd(1, 'INS_AN_ASN_63.INS_WSO_POWER_KNOB', 2) # 0 = OFF, 1 = STBY, 2 = ALIGN, 3 = NAV
		# Wait for ALIGN light to be lit for 2 seconds.  This means the BATH alignment is complete.  Takes ~3 mins.
		pushSeqCmd(dt, 'scriptCockpitState', control='F-4E-45MC/arg.INS_WSO_ALIGN_LIGHT', value=0, condition='>', duration=2)
		# Wait for ALIGN ilght to start flashing.  This means the full alignment is complete.  Takes ~3m45s.
		pushSeqCmd(dt, 'scriptCockpitState', control='F-4E-45MC/arg.INS_WSO_ALIGN_LIGHT', value=0, condition='=', duration=0)
		pushSeqCmd(dt, 'scriptCockpitState', control='F-4E-45MC/arg.INS_WSO_ALIGN_LIGHT', value=0, condition='>', duration=0)
		pushSeqCmd(dt, 'INS_AN_ASN_63.INS_WSO_POWER_KNOB', 3) # 0 = OFF, 1 = STBY, 2 = ALIGN, 3 = NAV
	pushSeqCmd(dt, 'scriptSpeech', "Alignment complete.")

	# Reference System switch ... PRIM
	pushSeqCmd(dt, 'ADI_ARU_11_A.MAINADI_reference_absolute', 0) # 0 = PRIM, 1 = STBY
	pushSeqCmd(5, '', '', 'Wait for compass.')

	# Compass Sync knob ... SYNC for a few seconds, then release back to SLAVED
	pushSeqCmd(dt, 'COMPASSSYSTEM.PILOT_COMPASS_PILOT_MODE_SELECTOR_KNOB', 3) # 0 = COMP, 1 = DC, 2 = SLAVED, 3 = SYNC
	pushSeqCmd(4, 'COMPASSSYSTEM.PILOT_COMPASS_PILOT_MODE_SELECTOR_KNOB', 2) # 0 = COMP, 1 = DC, 2 = SLAVED, 3 = SYNC

	# CADC correction
	pushSeqCmd(dt, 'CADC.SPC_switch', 2) # 0 = OFF, 1 = NORM, 2 = RESET
	pushSeqCmd(4, 'CADC.SPC_switch', 1) # 0 = OFF, 1 = NORM, 2 = RESET

	# Altimeter (only do this after CADC correction?)
	pushSeqCmd(dt, 'BAROMETRICALTIMETER.ALTIMETER_Mode', 2)
	# No need to move the lever back after setting it, just wait 3 seconds.
	pushSeqCmd(3, '', '', 'Wait for STBY flag to disappear.')

	# Countermeasures
	pushSeqCmd(dt, 'COUNTERMEASURES.CHAFF_MODE', 1) # 0 = OFF, 1 = SGL, 2 = MULT, 3 = PROG
	pushSeqCmd(dt, 'COUNTERMEASURES.FLARE_MODE', 1) # 0 = OFF, 1 = SGL, 2 = PROG

	# Stab Aug
	pushSeqCmd(dt, 'INPUTCONTROLS.AFCS_ENGAGE_STAB_AUG_PITCH', 1)
	pushSeqCmd(dt, 'INPUTCONTROLS.AFCS_ENGAGE_STAB_AUG_ROLL', 1)
	pushSeqCmd(dt, 'INPUTCONTROLS.AFCS_ENGAGE_STAB_AUG_YAW', 1)

	# Oxygen
	pushSeqCmd(dt, 'OXYGENSYSTEM.OXYGENSYSTEM_Pilot_Set_Ox_Ratio', 0) # 0 = NORMAL OXYGEN, 1 = 100% OXYGEN
	pushSeqCmd(dt, 'OXYGENSYSTEM.OXYGENSYSTEM_Pilot_Set_Ox_Supply', 0) # 0 = ON, 1 = OFF
	pushSeqCmd(dt, 'OXYGENSYSTEM.OXYGENSYSTEM_RIO_Set_Ox_Ratio', 0) # 0 = NORMAL OXYGEN, 1 = 100% OXYGEN
	pushSeqCmd(dt, 'OXYGENSYSTEM.OXYGENSYSTEM_RIO_Set_Ox_Supply', 0) # 0 = ON, 1 = OFF

	# RDR MSL CW switch ... CW ON
	pushSeqCmd(dt, 'WEAPONS.WEAPONS_CW_Switch', 2) # 0 = OFF, 1 = STBY, 2 = CW ON

	# Fuze switch
	pushSeqCmd(dt, 'WEAPONS.WEAPONS_Arm_Switch', 2) # 0 = SAFE, 1 = NOSE, 2 = NOSE & TAIL, 3 = TAIL

	# Bomb quantity
	pushSeqCmd(dt, 'WEAPONS.WEAPONS_SelectBombQty', 11) # 0 = P, 1 = S, 2 = C, 3 = 18, 4 = 12, 5 = 9, 6 = 6, 7 = 5, 8 = 4, 9 = 3, 10 = 2, 11 = 1

	# Arm gun
	pushSeqCmd(dt, 'WEAPONS.WEAPONS_Gun_Arm', 1)

	# Master Arm
	pushSeqCmd(dt, 'WEAPONS.WEAPONS_Master_Arm',  1)

	# Enable Jester.
	pushSeqCmd(dt, 'JESTER_WHEEL.JESTER_COMMAND_CREW_PRESENCE_AUTO', 1)
	pushSeqCmd(dt, 'JESTER_WHEEL.JESTER_COMMAND_CREW_PRESENCE_AUTO', 0)
	pushSeqCmd(dt, 'scriptSpeech', 'Jester enabled.')
	# Jester, radar to active.
	#pushSeqCmd(dt, 'F-4E/PLT_JESTER_COMMAND_RADAR_OPERATION_ACTIVE', 'TOGGLE')
	# Jester, radar auto-focus on.
	#pushSeqCmd(dt, 'F-4E/PLT_JESTER_COMMAND_RADAR_AUTO_FOCUS_ON', 'TOGGLE')

	pushSeqCmd(dt, 'scriptSpeech', "Manual steps remaining: Lights, Radios.  If carrying drop tanks set External Tanks Feed switch.  Set takeoff trim, 2 units nose down.")

	return seq


def AutoStart(config, vars, helper, *args, **kwargs):
	seq = []
	dt = 0.2

	pushSeqCmd = helper.makePushSeqCmd(seq)

	pushSeqCmd(0, '', '', "Running Auto Start sequence")

	if vars.get('time') == 'day':
		# Interior lights
		pushSeqCmd(dt, 'INTERIOR_LIGHTS.PILOT_COCKPIT_LIGHTS_CONSOLE_BRIGHTNESS_KNOB', int16(1))
		pushSeqCmd(dt, 'INTERIOR_LIGHTS.PILOT_COCKPIT_LIGHTS_INSTRUMENT_PANEL_BRIGHTNESS_KNOB', int16(1))
		pushSeqCmd(dt, 'INTERIOR_LIGHTS.PILOT_COCKPIT_LIGHTS_CONSOLE_FLOODLIGHT_BRIGHTNESS_SWITCH', 1) # 0 = MED, 1 = DIM, 2 = BRT
		pushSeqCmd(dt, 'INTERIOR_LIGHTS.PILOT_RIGHT_WALL_INSTRUMENT_FLOODLIGHT_BRIGHTNESS_SWITCH', 1) # Also controls WSO panel.  0 = DIM, 1 = OFF, 2 = BRT
		pushSeqCmd(dt, 'INTERIOR_LIGHTS.WSO_COCKPIT_LIGHTS_INSTRUMENT_PANEL_BRIGHTNESS_KNOB', int16(1))
		pushSeqCmd(dt, 'INTERIOR_LIGHTS.WSO_COCKPIT_LIGHTS_CONSOLE_BRIGHTNESS_KNOB', int16(1))
		pushSeqCmd(dt, 'INTERIOR_LIGHTS.WSO_COCKPIT_LIGHTS_CONSOLE_FLOODLIGHT_BRIGHTNESS_SWITCH', 1) # 0 = MED, 1 = DIM, 2 = BRT
		# Radar screen night filter
		pushSeqCmd(dt, 'RADAR.PILOT_DSCG_NIGHT_FILTER', 0) # 0 = Off, 1 = On
		# Exterior lights
		pushSeqCmd(dt, 'EXTERIOR_LIGHTS.PILOT_EXTERIOR_LIGHTS_PANEL_MODE_SWITCH', 1) # 0 = STEADY, 1 = OFF, 2 = FLASH
	else:
		# Interior lights
		pushSeqCmd(dt, 'INTERIOR_LIGHTS.PILOT_COCKPIT_LIGHTS_CONSOLE_BRIGHTNESS_KNOB', int16(0.5))
		pushSeqCmd(dt, 'INTERIOR_LIGHTS.PILOT_COCKPIT_LIGHTS_INSTRUMENT_PANEL_BRIGHTNESS_KNOB', int16(0.5))
		pushSeqCmd(dt, 'INTERIOR_LIGHTS.PILOT_COCKPIT_LIGHTS_CONSOLE_FLOODLIGHT_BRIGHTNESS_SWITCH', 1) # 0 = MED, 1 = DIM, 2 = BRT
		pushSeqCmd(dt, 'INTERIOR_LIGHTS.PILOT_RIGHT_WALL_INSTRUMENT_FLOODLIGHT_BRIGHTNESS_SWITCH', 1) # Also controls WSO panel.  0 = DIM, 1 = OFF, 2 = BRT
		pushSeqCmd(dt, 'INTERIOR_LIGHTS.WSO_COCKPIT_LIGHTS_INSTRUMENT_PANEL_BRIGHTNESS_KNOB', int16(0.5))
		pushSeqCmd(dt, 'INTERIOR_LIGHTS.WSO_COCKPIT_LIGHTS_CONSOLE_BRIGHTNESS_KNOB', int16(0.5))
		pushSeqCmd(dt, 'INTERIOR_LIGHTS.WSO_COCKPIT_LIGHTS_CONSOLE_FLOODLIGHT_BRIGHTNESS_SWITCH', 1) # 0 = MED, 1 = DIM, 2 = BRT
		# Radar screen night filter
		pushSeqCmd(dt, 'RADAR.PILOT_DSCG_NIGHT_FILTER', 1) # 0 = Off, 1 = On
		# Exterior lights
		pushSeqCmd(dt, 'EXTERIOR_LIGHTS.PILOT_EXTERIOR_LIGHTS_PANEL_MODE_SWITCH', 1) # 0 = STEADY, 1 = OFF, 2 = FLASH

	pushSeqCmd(dt, 'CANOPYCONTROLS.CANOPYCONTROLS_ActuatePilotCanopy', 0) # 0 = Close, 1 = Open

	# Radar altimeter ... ON, but leave bug at 0 ft
	pushSeqCmd(dt, 'RADARALTIMETER.RADAR_ALTIMETER_LowAltSet', 0.1)

	# DSCG screen mode switch
	pushSeqCmd(dt, 'RADAR.PILOT_DSCG_MODE', 0) # 0 = RADAR, 1 = OFF, 2 = TV

	# IFF
	pushSeqCmd(dt, 'IFF.PILOT_IFF_MASTER_Knob', 3) # 0 = OFF, 1 = STBY, 2 = LOW, 3 = NOR, 4 = EMER

	# Antiskid
	pushSeqCmd(dt, 'GEARANDHOOK.LANDING_GEAR_AntiSkid', 1)

	# Backup ADI
	pushSeqCmd(dt, 'EMERGENCYATTITUDEINDICATOR.EMERG_ADI_Cage', 0)

	# Sight mode
	pushSeqCmd(dt, 'HUD_AN_ASG_26.HUD_SelectHUDMode', 2) # 0 = OFF, 1 = STBY, 2 = CAGE, 3 = A/G, 4 = A/A, 5 = BIT 1, 6 = BIT 2

	# ADI flight director switch
	pushSeqCmd(dt, 'FLIGHTDIRECTORCOMPUTER.NAV_FUNCT_SEL_PANEL_FD_KNOB', 1)

	# Compass Sync knob ... SYNC for a few seconds, then release back to SLAVED
	pushSeqCmd(dt, 'COMPASSSYSTEM.PILOT_COMPASS_PILOT_MODE_SELECTOR_KNOB', 3) # 0 = COMP, 1 = DC, 2 = SLAVED, 3 = SYNC
	pushSeqCmd(4, 'COMPASSSYSTEM.PILOT_COMPASS_PILOT_MODE_SELECTOR_KNOB', 2) # 0 = COMP, 1 = DC, 2 = SLAVED, 3 = SYNC

	# CADC correction
	pushSeqCmd(dt, 'CADC.SPC_switch', 2) # 0 = OFF, 1 = NORM, 2 = RESET
	pushSeqCmd(4, 'CADC.SPC_switch', 1) # 0 = OFF, 1 = NORM, 2 = RESET

	# Stab Aug
	pushSeqCmd(dt, 'INPUTCONTROLS.AFCS_ENGAGE_STAB_AUG_PITCH', 1)
	pushSeqCmd(dt, 'INPUTCONTROLS.AFCS_ENGAGE_STAB_AUG_ROLL', 1)
	pushSeqCmd(dt, 'INPUTCONTROLS.AFCS_ENGAGE_STAB_AUG_YAW', 1)

	# Oxygen
	pushSeqCmd(dt, 'OXYGENSYSTEM.OXYGENSYSTEM_Pilot_Set_Ox_Ratio', 0) # 0 = NORMAL OXYGEN, 1 = 100% OXYGEN

	# RDR MSL CW switch ... CW ON
	pushSeqCmd(dt, 'WEAPONS.WEAPONS_CW_Switch', 2) # 0 = OFF, 1 = STBY, 2 = CW ON

	# Master Arm
	pushSeqCmd(dt, 'WEAPONS.WEAPONS_Master_Arm',  1)

	pushSeqCmd(dt, 'scriptSpeech', "Manual steps remaining: Lights, Radios.  If carrying drop tanks set External Tanks Feed switch.")

	return seq


def HotStart(config, vars, helper, *args, **kwargs):
	seq = []
	dt = 0.2

	pushSeqCmd = helper.makePushSeqCmd(seq)

	pushSeqCmd(0, '', '', "Running Hot Start sequence")

	if vars.get('time') == 'day':
		# Interior lights
		pushSeqCmd(dt, 'INTERIOR_LIGHTS.PILOT_COCKPIT_LIGHTS_CONSOLE_BRIGHTNESS_KNOB', int16(1))
		pushSeqCmd(dt, 'INTERIOR_LIGHTS.PILOT_COCKPIT_LIGHTS_INSTRUMENT_PANEL_BRIGHTNESS_KNOB', int16(1))
		pushSeqCmd(dt, 'INTERIOR_LIGHTS.PILOT_COCKPIT_LIGHTS_CONSOLE_FLOODLIGHT_BRIGHTNESS_SWITCH', 1) # 0 = MED, 1 = DIM, 2 = BRT
		pushSeqCmd(dt, 'INTERIOR_LIGHTS.PILOT_RIGHT_WALL_INSTRUMENT_FLOODLIGHT_BRIGHTNESS_SWITCH', 1) # Also controls WSO panel.  0 = DIM, 1 = OFF, 2 = BRT
		pushSeqCmd(dt, 'INTERIOR_LIGHTS.WSO_COCKPIT_LIGHTS_INSTRUMENT_PANEL_BRIGHTNESS_KNOB', int16(1))
		pushSeqCmd(dt, 'INTERIOR_LIGHTS.WSO_COCKPIT_LIGHTS_CONSOLE_BRIGHTNESS_KNOB', int16(1))
		pushSeqCmd(dt, 'INTERIOR_LIGHTS.WSO_COCKPIT_LIGHTS_CONSOLE_FLOODLIGHT_BRIGHTNESS_SWITCH', 1) # 0 = MED, 1 = DIM, 2 = BRT
		# Radar screen night filter
		pushSeqCmd(dt, 'RADAR.PILOT_DSCG_NIGHT_FILTER', 0) # 0 = Off, 1 = On
		# Exterior lights
		pushSeqCmd(dt, 'EXTERIOR_LIGHTS.PILOT_EXTERIOR_LIGHTS_PANEL_MODE_SWITCH', 1) # 0 = STEADY, 1 = OFF, 2 = FLASH
	else:
		# Interior lights
		pushSeqCmd(dt, 'INTERIOR_LIGHTS.PILOT_COCKPIT_LIGHTS_CONSOLE_BRIGHTNESS_KNOB', int16(0.5))
		pushSeqCmd(dt, 'INTERIOR_LIGHTS.PILOT_COCKPIT_LIGHTS_INSTRUMENT_PANEL_BRIGHTNESS_KNOB', int16(0.5))
		pushSeqCmd(dt, 'INTERIOR_LIGHTS.PILOT_COCKPIT_LIGHTS_CONSOLE_FLOODLIGHT_BRIGHTNESS_SWITCH', 1) # 0 = MED, 1 = DIM, 2 = BRT
		pushSeqCmd(dt, 'INTERIOR_LIGHTS.PILOT_RIGHT_WALL_INSTRUMENT_FLOODLIGHT_BRIGHTNESS_SWITCH', 1) # Also controls WSO panel.  0 = DIM, 1 = OFF, 2 = BRT
		pushSeqCmd(dt, 'INTERIOR_LIGHTS.WSO_COCKPIT_LIGHTS_INSTRUMENT_PANEL_BRIGHTNESS_KNOB', int16(0.5))
		pushSeqCmd(dt, 'INTERIOR_LIGHTS.WSO_COCKPIT_LIGHTS_CONSOLE_BRIGHTNESS_KNOB', int16(0.5))
		pushSeqCmd(dt, 'INTERIOR_LIGHTS.WSO_COCKPIT_LIGHTS_CONSOLE_FLOODLIGHT_BRIGHTNESS_SWITCH', 1) # 0 = MED, 1 = DIM, 2 = BRT
		# Radar screen night filter
		pushSeqCmd(dt, 'RADAR.PILOT_DSCG_NIGHT_FILTER', 1) # 0 = Off, 1 = On
		# Exterior lights
		pushSeqCmd(dt, 'EXTERIOR_LIGHTS.PILOT_EXTERIOR_LIGHTS_PANEL_MODE_SWITCH', 1) # 0 = STEADY, 1 = OFF, 2 = FLASH

	# Sight mode
	pushSeqCmd(dt, 'HUD_AN_ASG_26.HUD_SelectHUDMode', 2) # 0 = OFF, 1 = STBY, 2 = CAGE, 3 = A/G, 4 = A/A, 5 = BIT 1, 6 = BIT 2

	# ADI flight director switch
	pushSeqCmd(dt, 'FLIGHTDIRECTORCOMPUTER.NAV_FUNCT_SEL_PANEL_FD_KNOB', 1)

	# Compass Sync knob ... SYNC for a few seconds, then release back to SLAVED
	pushSeqCmd(dt, 'COMPASSSYSTEM.PILOT_COMPASS_PILOT_MODE_SELECTOR_KNOB', 3) # 0 = COMP, 1 = DC, 2 = SLAVED, 3 = SYNC
	pushSeqCmd(4, 'COMPASSSYSTEM.PILOT_COMPASS_PILOT_MODE_SELECTOR_KNOB', 2) # 0 = COMP, 1 = DC, 2 = SLAVED, 3 = SYNC

	# CADC correction
	pushSeqCmd(dt, 'CADC.SPC_switch', 2) # 0 = OFF, 1 = NORM, 2 = RESET
	pushSeqCmd(4, 'CADC.SPC_switch', 1) # 0 = OFF, 1 = NORM, 2 = RESET

	# Countermeasures
	pushSeqCmd(dt, 'COUNTERMEASURES.CHAFF_MODE', 1) # 0 = OFF, 1 = SGL, 2 = MULT, 3 = PROG
	pushSeqCmd(dt, 'COUNTERMEASURES.FLARE_MODE', 1) # 0 = OFF, 1 = SGL, 2 = PROG

	# RDR MSL CW switch ... CW ON
	pushSeqCmd(dt, 'WEAPONS.WEAPONS_CW_Switch', 2) # 0 = OFF, 1 = STBY, 2 = CW ON

	# Fuze switch
	pushSeqCmd(dt, 'WEAPONS.WEAPONS_Arm_Switch', 2) # 0 = SAFE, 1 = NOSE, 2 = NOSE & TAIL, 3 = TAIL

	# Bomb quantity
	pushSeqCmd(dt, 'WEAPONS.WEAPONS_SelectBombQty', 11) # 0 = P, 1 = S, 2 = C, 3 = 18, 4 = 12, 5 = 9, 6 = 6, 7 = 5, 8 = 4, 9 = 3, 10 = 2, 11 = 1

	# Arm gun
	pushSeqCmd(dt, 'WEAPONS.WEAPONS_Gun_Arm', 1)

	# Master Arm
	pushSeqCmd(dt, 'WEAPONS.WEAPONS_Master_Arm',  1)

	pushSeqCmd(dt, 'scriptSpeech', "Manual steps remaining: Lights, Radios.  If carrying drop tanks set External Tanks Feed switch.")

	return seq


def AirStart(config, vars, helper, *args, **kwargs):
	seq = []
	dt = 0.2

	pushSeqCmd = helper.makePushSeqCmd(seq)

	pushSeqCmd(0, '', '', "Running Air Start sequence")

	if vars.get('time') == 'day':
		# Interior lights
		pushSeqCmd(dt, 'INTERIOR_LIGHTS.PILOT_COCKPIT_LIGHTS_CONSOLE_BRIGHTNESS_KNOB', int16(1))
		pushSeqCmd(dt, 'INTERIOR_LIGHTS.PILOT_COCKPIT_LIGHTS_INSTRUMENT_PANEL_BRIGHTNESS_KNOB', int16(1))
		pushSeqCmd(dt, 'INTERIOR_LIGHTS.PILOT_COCKPIT_LIGHTS_CONSOLE_FLOODLIGHT_BRIGHTNESS_SWITCH', 1) # 0 = MED, 1 = DIM, 2 = BRT
		pushSeqCmd(dt, 'INTERIOR_LIGHTS.PILOT_RIGHT_WALL_INSTRUMENT_FLOODLIGHT_BRIGHTNESS_SWITCH', 1) # Also controls WSO panel.  0 = DIM, 1 = OFF, 2 = BRT
		pushSeqCmd(dt, 'INTERIOR_LIGHTS.WSO_COCKPIT_LIGHTS_INSTRUMENT_PANEL_BRIGHTNESS_KNOB', int16(1))
		pushSeqCmd(dt, 'INTERIOR_LIGHTS.WSO_COCKPIT_LIGHTS_CONSOLE_BRIGHTNESS_KNOB', int16(1))
		pushSeqCmd(dt, 'INTERIOR_LIGHTS.WSO_COCKPIT_LIGHTS_CONSOLE_FLOODLIGHT_BRIGHTNESS_SWITCH', 1) # 0 = MED, 1 = DIM, 2 = BRT
		# Radar screen night filter
		pushSeqCmd(dt, 'RADAR.PILOT_DSCG_NIGHT_FILTER', 0) # 0 = Off, 1 = On
		# Exterior lights
		pushSeqCmd(dt, 'EXTERIOR_LIGHTS.PILOT_EXTERIOR_LIGHTS_PANEL_MODE_SWITCH', 1) # 0 = STEADY, 1 = OFF, 2 = FLASH
	else:
		# Interior lights
		pushSeqCmd(dt, 'INTERIOR_LIGHTS.PILOT_COCKPIT_LIGHTS_CONSOLE_BRIGHTNESS_KNOB', int16(0.5))
		pushSeqCmd(dt, 'INTERIOR_LIGHTS.PILOT_COCKPIT_LIGHTS_INSTRUMENT_PANEL_BRIGHTNESS_KNOB', int16(0.5))
		pushSeqCmd(dt, 'INTERIOR_LIGHTS.PILOT_COCKPIT_LIGHTS_CONSOLE_FLOODLIGHT_BRIGHTNESS_SWITCH', 1) # 0 = MED, 1 = DIM, 2 = BRT
		pushSeqCmd(dt, 'INTERIOR_LIGHTS.PILOT_RIGHT_WALL_INSTRUMENT_FLOODLIGHT_BRIGHTNESS_SWITCH', 1) # Also controls WSO panel.  0 = DIM, 1 = OFF, 2 = BRT
		pushSeqCmd(dt, 'INTERIOR_LIGHTS.WSO_COCKPIT_LIGHTS_INSTRUMENT_PANEL_BRIGHTNESS_KNOB', int16(0.5))
		pushSeqCmd(dt, 'INTERIOR_LIGHTS.WSO_COCKPIT_LIGHTS_CONSOLE_BRIGHTNESS_KNOB', int16(0.5))
		pushSeqCmd(dt, 'INTERIOR_LIGHTS.WSO_COCKPIT_LIGHTS_CONSOLE_FLOODLIGHT_BRIGHTNESS_SWITCH', 1) # 0 = MED, 1 = DIM, 2 = BRT
		# Radar screen night filter
		pushSeqCmd(dt, 'RADAR.PILOT_DSCG_NIGHT_FILTER', 1) # 0 = Off, 1 = On
		# Exterior lights
		pushSeqCmd(dt, 'EXTERIOR_LIGHTS.PILOT_EXTERIOR_LIGHTS_PANEL_MODE_SWITCH', 1) # 0 = STEADY, 1 = OFF, 2 = FLASH

	# Sight mode
	pushSeqCmd(dt, 'HUD_AN_ASG_26.HUD_SelectHUDMode', 2) # 0 = OFF, 1 = STBY, 2 = CAGE, 3 = A/G, 4 = A/A, 5 = BIT 1, 6 = BIT 2

	# ADI flight director switch
	pushSeqCmd(dt, 'FLIGHTDIRECTORCOMPUTER.NAV_FUNCT_SEL_PANEL_FD_KNOB', 1)

	# RDR MSL CW switch ... CW ON
	pushSeqCmd(dt, 'WEAPONS.WEAPONS_CW_Switch', 2) # 0 = OFF, 1 = STBY, 2 = CW ON

	# Fuze switch
	# Air Start defaults to NOSE & TAIL.

	# Bomb quantity
	pushSeqCmd(dt, 'WEAPONS.WEAPONS_SelectBombQty', 11) # 0 = P, 1 = S, 2 = C, 3 = 18, 4 = 12, 5 = 9, 6 = 6, 7 = 5, 8 = 4, 9 = 3, 10 = 2, 11 = 1

	# Arm gun
	pushSeqCmd(dt, 'WEAPONS.WEAPONS_Gun_Arm', 1)

	# Master Arm
	pushSeqCmd(dt, 'WEAPONS.WEAPONS_Master_Arm',  1)

	pushSeqCmd(dt, 'scriptSpeech', "Manual steps remaining: Lights, Radios.  If carrying drop tanks set External Tanks Feed switch.")

	return seq

def Shutdown(self, vars):
	# TODO
	pass
