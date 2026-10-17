# Return a Dictionary of script data.  The 'scripts' key is a list of scripts that users will be selecting from.  Each script has an associated 'function', which is the name of the function in this file that will be called to generate the command sequence, and a dictionary of 'vars' that the user will be prompted to choose from before running the script, and will be passed into the sequence generating function.
def getScriptData():
	return {
		'moduleName': 'Mi-24P',
		'scripts': [
			{
				'name': 'Cold Start',
				'function': 'ColdStart',
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
			{
				'name': 'Shutdown',
				'function': 'Shutdown',
				'vars': {},
			},
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
			#	},
			#},
		],
	}

def Test(config, vars, helper, *args, **kwargs):
	seq = []
	dt = 0.3

	pushSeqCmd = helper.makePushSeqCmd(seq)

	# Test code here...
	pushSeqCmd(0, '', '', "Running Test sequence")


	#print(seq)
	return seq


def ColdStart(config, vars, helper, *args, **kwargs):
	seq = []
	dt = 0.3

	pushSeqCmd = helper.makePushSeqCmd(seq)

	apuStartTime = 25 # APU takes 25 seconds to start.
	engineStartTime = 55 # Engines each take 55 seconds to start.
	engineSpoolTime = 10 # Engines take 10 seconds to spool up from idle to flight-ready (collective twist grip max).

	# Start sequence
	pushSeqCmd(0, '', '', "Running Cold Start sequence.")
	pushSeqCmd(dt, '', '', 'Set collective full down.')
	pushSeqCmd(dt, 'scriptSpeech', 'Set collective full down.')

	# Radio/ICS switch (Pilot) - ICS (allows rearming)
	pushSeqCmd(dt, 'SPU_8.CMD_SPU8_P_ICS_RADIO', 1)

	# Cockpit Doors - Close
	pushSeqCmd(dt, 'CPT_MECH.Command_CPT_MECH_Door_EXT', 1) # Open/close cockpit door (LCtrl+C)

	# Left Engine Stop lever - OFF
	pushSeqCmd(dt, 'ENGINE_INTERFACE.LEVER_Left_Engine_Lock', 0)
	# Right Engine Stop lever - OFF
	pushSeqCmd(dt, 'ENGINE_INTERFACE.LEVER_Right_Engine_Lock', 0)
	# Rotor Brake - OFF
	pushSeqCmd(dt, 'ENGINE_INTERFACE.LEVER_Rotor_Lock', 0)

	# Left and Right throttles to min, then auto
	pushSeqCmd(dt, 'ENGINE_INTERFACE.CONTROL_LEFT_THROTTLE_CLICK', -1.0)
	pushSeqCmd(0, 'ENGINE_INTERFACE.CONTROL_RIGHT_THROTTLE_CLICK', -1.0)
	for i in range(8): # 8x +3000 works, though trial and error.
		pushSeqCmd(dt, 'ENGINE_INTERFACE.CONTROL_LEFT_THROTTLE_CLICK', 0.0458)
		pushSeqCmd(dt, 'ENGINE_INTERFACE.CONTROL_RIGHT_THROTTLE_CLICK', 0.0458)
	# Twist grip to min (DECR)
	pushSeqCmd(dt, 'scriptSimCommand', 'iCommandThrottleDecrease') # Correction lever decrease (PgDn)
	pushSeqCmd(2, 'scriptSimCommand', 'iCommandThrottleStop') # Hold down for 2 seconds
	# Collective full down
	pushSeqCmd(dt, 'scriptSimCommand', 'iCommandPlaneCollectiveDecrease') # Numpad -
	pushSeqCmd(2, 'scriptSimCommand', 'iCommandPlaneCollectiveStop') # Hold down for 2 seconds

	# Electric Power
	# Right Battery - ON
	pushSeqCmd(dt, 'ELEC_INTERFACE.BatteryRight', 1)
	# Left Battery - ON
	pushSeqCmd(dt, 'ELEC_INTERFACE.BatteryLeft', 1)
	# DC Voltmeter knob - BATT
	pushSeqCmd(dt, 'ELEC_INTERFACE.DCGangSwitcher', 2)
	# Inverter PO-750A - ON
	pushSeqCmd(dt, 'ELEC_INTERFACE.Rotary115vConverterCover', 1) # Cover open
	pushSeqCmd(dt, 'ELEC_INTERFACE.Rotary115vConverter', 1) # Switch
	# Left CBs - ON (gang bar)
	pushSeqCmd(dt, 'ELEC_INTERFACE.CB_FRAME_LEFT', 1)
	pushSeqCmd(dt, 'ELEC_INTERFACE.CB_FRAME_LEFT', 0)
	# Right CBs - ON (gang bar)
	pushSeqCmd(dt, 'ELEC_INTERFACE.CB_FRAME_RIGHT', 1)
	pushSeqCmd(dt, 'ELEC_INTERFACE.CB_FRAME_RIGHT', 0)

	# POWER FROM BATT (Network To Batteries) - Powers onboard systems from batteries?
	# Power From Batt (Network To Batteries) switch - ON
	pushSeqCmd(dt, 'ELEC_INTERFACE.NetworkToBatteriesCover', 1) # Cover open
	pushSeqCmd(dt, 'ELEC_INTERFACE.NetworkToBatteries', 1) # Switch

	# Lights
	if vars['time'] == 'day':
		# Interior Lights - Pilot
		# Cargo lighting switch - OFF (left wall rear top)
		pushSeqCmd(dt, 'INT_LIGHTS_SYSTEM.CargoLightingWhiteBlue', 1) # 0 = BLUE, 1 = OFF, 2 = WHITE
		# Pilot Cabin Light - OFF (left wall rear top)
		pushSeqCmd(dt, 'INT_LIGHTS_SYSTEM.PilotCabinLightingWhiteRed', 1) # 0 = RED, 1 = OFF, 2 = WHITE
		# Day-Night switch - DAY (left wall rear top)
		pushSeqCmd(dt, 'INT_LIGHTS_SYSTEM.DayNight', 1) # 0 = NIGHT, 1 = DAY
		# AFCS buttons lighting - BRIGHT (not sure if this does anything) (left angled panel middle)
		pushSeqCmd(dt, 'AUTOPILOT.Lighting', 1) # 0 = DIM, 1 = BRIGHT
		# Map lighting - OFF (right angled panel top)
		pushSeqCmd(dt, 'MAP_DISPLAY.Lights', 1) # 0 = DIM, 1 = OFF, 2 = BRIGHT
		# RED LIGHTING INSTR PANEL AND RH PANELS knobs (right console rear inboard)
		# Builtin Red Lights Transformer - OFF
		pushSeqCmd(dt, 'INT_LIGHTS_SYSTEM.RedLightsPilotBuiltInRedLights', 0) # 0 = OFF, 10 = Full On (discrete steps)
		# Transformer 1 Group Of Red Lights Right And Pilot Panel - OFF
		pushSeqCmd(dt, 'INT_LIGHTS_SYSTEM.RedLightsPilotInstrumentPanelRightPanel_1', 0) # 0 = OFF, 10 = Full On (discrete steps)
		# Transformer 2 Group Of Red Lights Right And Pilot Panel - OFF
		pushSeqCmd(dt, 'INT_LIGHTS_SYSTEM.RedLightsPilotInstrumentPanelRightPanel_2', 0) # 0 = OFF, 10 = Full On (discrete steps)
		# LEFT PANELS RED LIGHTNG knobs (right angled panel bottom)
		# Transformer 1 Group Of Red Lights Right And Pilot Panel - OFF
		pushSeqCmd(dt, 'INT_LIGHTS_SYSTEM.RedLightsPilotLeftPanel_1', 0) # 0 = OFF, 10 = Full On (discrete steps)
		# Transformer 2 Group Of Red Lights Right And Pilot Panel - OFF
		pushSeqCmd(dt, 'INT_LIGHTS_SYSTEM.RedLightsPilotLeftPanel_2', 0) # 0 = OFF, 10 = Full On (discrete steps)
		# AUX STORES LIGHTS switch (right angled panel bottom)
		# Armament Panel Red Lights Switch - OFF (these are very bright and not really necessary)
		pushSeqCmd(dt, 'INT_LIGHTS_SYSTEM.SpecialEquipmentPanelRedLights', 0) # 0 = OFF, 1 = ON

		# Interior Lights - Operator
		# Operator Cabin Light - OFF (Operator, left wall middle)
		pushSeqCmd(dt, 'INT_LIGHTS_SYSTEM.OperatorCabinLightingWhiteRed', 1) # 0 = RED, 1 = OFF, 2 = WHITE
		# Transformer 1 Group Of Red Lights Left And Operator Panel - OFF (Operator, left wall forward bottom)
		pushSeqCmd(dt, 'INT_LIGHTS_SYSTEM.RedLightsOperatorPanel_1', 0) # 0 = OFF, 10 = Full On (discrete steps)
		# Transformer 2 Group Of Red Lights Left And Operator Panel - OFF (Operator, left wall forward bottom)
		pushSeqCmd(dt, 'INT_LIGHTS_SYSTEM.RedLightsOperatorPanel_2', 0) # 0 = OFF, 10 = Full On (discrete steps)

		# Exterior Lights
		# Strobe lights - OFF (left wall forward top)
		pushSeqCmd(dt, 'EXT_LIGHTS_SYSTEM.StrobeLight', 0)
		# Blade Tip lights - OFF (left wall forward top)
		pushSeqCmd(dt, 'EXT_LIGHTS_SYSTEM.TipLights', 0)
		# Formation lights - OFF (left wall forward top)
		pushSeqCmd(dt, 'EXT_LIGHTS_SYSTEM.FormationLights', 1) # 0 = DIM, 1 = OFF, 2 = BRIGHT
		# Nav lights - OFF (left angled panel top)
		pushSeqCmd(dt, 'EXT_LIGHTS_SYSTEM.NavLtSwitch', 1) # 0 = DIM, 1 = OFF, 2 = BRIGHT

	else: # Night
		# Interior Lights - Pilot
		# Cargo lighting switch - OFF (left wall rear top)
		pushSeqCmd(dt, 'INT_LIGHTS_SYSTEM.CargoLightingWhiteBlue', 1) # 0 = BLUE, 1 = OFF, 2 = WHITE
		# Pilot Cabin Light - OFF (left wall rear top)
		pushSeqCmd(dt, 'INT_LIGHTS_SYSTEM.PilotCabinLightingWhiteRed', 1) # 0 = RED, 1 = OFF, 2 = WHITE
		# Day-Night switch - NIGHT (left wall rear top)
		pushSeqCmd(dt, 'INT_LIGHTS_SYSTEM.DayNight', 0) # 0 = NIGHT, 1 = DAY
		# AFCS buttons lighting - DIM (not sure if this does anything) (left angled panel middle)
		pushSeqCmd(dt, 'AUTOPILOT.Lighting', 0) # 0 = DIM, 1 = BRIGHT
		# Map lighting - DIM (right angled panel top)
		pushSeqCmd(dt, 'MAP_DISPLAY.Lights', 0) # 0 = DIM, 1 = OFF, 2 = BRIGHT
		# RED LIGHTING INSTR PANEL AND RH PANELS knobs (right console rear inboard)
		# Builtin Red Lights Transformer - Half
		pushSeqCmd(dt, 'INT_LIGHTS_SYSTEM.RedLightsPilotBuiltInRedLights', 5) # 0 = OFF, 10 = Full On (discrete steps)
		# Transformer 1 Group Of Red Lights Right And Pilot Panel - Half
		pushSeqCmd(dt, 'INT_LIGHTS_SYSTEM.RedLightsPilotInstrumentPanelRightPanel_1', 5) # 0 = OFF, 10 = Full On (discrete steps)
		# Transformer 2 Group Of Red Lights Right And Pilot Panel - Half
		pushSeqCmd(dt, 'INT_LIGHTS_SYSTEM.RedLightsPilotInstrumentPanelRightPanel_2', 5) # 0 = OFF, 10 = Full On (discrete steps)
		# LEFT PANELS RED LIGHTNG knobs (right angled panel bottom)
		# Transformer 1 Group Of Red Lights Right And Pilot Panel - Half
		pushSeqCmd(dt, 'INT_LIGHTS_SYSTEM.RedLightsPilotLeftPanel_1', 5) # 0 = OFF, 10 = Full On (discrete steps)
		# Transformer 2 Group Of Red Lights Right And Pilot Panel - Half
		pushSeqCmd(dt, 'INT_LIGHTS_SYSTEM.RedLightsPilotLeftPanel_2', 5) # 0 = OFF, 10 = Full On (discrete steps)
		# AUX STORES LIGHTS switch (right angled panel bottom)
		# Armament Panel Red Lights Switch - OFF (these are very bright and not really necessary)
		pushSeqCmd(dt, 'INT_LIGHTS_SYSTEM.SpecialEquipmentPanelRedLights', 0) # 0 = OFF, 1 = ON

		# Interior Lights - Operator
		# Operator Cabin Light - OFF (Operator, left wall middle)
		pushSeqCmd(dt, 'INT_LIGHTS_SYSTEM.OperatorCabinLightingWhiteRed', 1) # 0 = RED, 1 = OFF, 2 = WHITE
		# Transformer 1 Group Of Red Lights Left And Operator Panel - Half (Operator, left wall forward bottom)
		pushSeqCmd(dt, 'INT_LIGHTS_SYSTEM.RedLightsOperatorPanel_1', 5) # 0 = OFF, 10 = Full On (discrete steps)
		# Transformer 2 Group Of Red Lights Left And Operator Panel - Half (Operator, left wall forward bottom)
		pushSeqCmd(dt, 'INT_LIGHTS_SYSTEM.RedLightsOperatorPanel_2', 5) # 0 = OFF, 10 = Full On (discrete steps)

		# Exterior Lights
		# Strobe lights - OFF (left wall forward top)
		pushSeqCmd(dt, 'EXT_LIGHTS_SYSTEM.StrobeLight', 0)
		# Blade Tip lights - OFF (left wall forward top)
		pushSeqCmd(dt, 'EXT_LIGHTS_SYSTEM.TipLights', 0)
		# Formation lights - OFF (left wall forward top)
		pushSeqCmd(dt, 'EXT_LIGHTS_SYSTEM.FormationLights', 1) # 0 = DIM, 1 = OFF, 2 = BRIGHT
		# Nav lights - OFF (left angled panel top)
		pushSeqCmd(dt, 'EXT_LIGHTS_SYSTEM.NavLtSwitch', 1) # 0 = DIM, 1 = OFF, 2 = BRIGHT

	# Hydraulic system (starts on MAIN)
	## Main/Auxiliary Hydraulic Switch - MAIN
	#pushSeqCmd(dt, device = devices.HYDRO_SYS_INTERFACE, action = hydraulic_commands.MainHydroCover, value = 1)
	#pushSeqCmd(dt, device = devices.HYDRO_SYS_INTERFACE, action = hydraulic_commands.MainHydro, value = 1)
	#pushSeqCmd(dt, device = devices.HYDRO_SYS_INTERFACE, action = hydraulic_commands.MainHydroCover, value = 0)

	# Seal and pressurize cabin
	# Cabin Press valve - OPEN (CCW)
	pushSeqCmd(dt, 'ECS_INTERFACE.Sealing_valve', 0)
	# Cabin Depress switch - ON
	pushSeqCmd(dt, 'ECS_INTERFACE.CabinUnseal', 1)
	# Blowdown Conditioning switch - CONDITION
	pushSeqCmd(dt, 'ECS_INTERFACE.BlowdownConditioning', 2)

	# Fuel System
	# Service (Feed) Tanks 1 switch - ON
	pushSeqCmd(dt, 'FUELSYS_INTERFACE.ValveTank1', 1)
	# Service (Feed) Tanks 2 switch - ON
	pushSeqCmd(dt, 'FUELSYS_INTERFACE.ValveTank2', 1)
	# Fuel Shutoff Left switch - ON
	pushSeqCmd(dt, 'FUELSYS_INTERFACE.ValveLeftEngineCover', 1) # Cover open
	pushSeqCmd(dt, 'FUELSYS_INTERFACE.ValveLeftEngine', 1) # Switch
	pushSeqCmd(dt, 'FUELSYS_INTERFACE.ValveLeftEngineCover', 0) # Cover close
	# Fuel Shutoff Right switch - ON
	pushSeqCmd(dt, 'FUELSYS_INTERFACE.ValveRightEngineCover', 1) # Cover open
	pushSeqCmd(dt, 'FUELSYS_INTERFACE.ValveRightEngine', 1) # Switch
	pushSeqCmd(dt, 'FUELSYS_INTERFACE.ValveRightEngineCover', 0) # Cover close
	# Fuel Crossfeed (Delimiter) switch - ON # "Fuel Delimiter Valve"
	pushSeqCmd(dt, 'FUELSYS_INTERFACE.ValveDelimiter', 1)
	# Service Tank Pumps 1, 2, 4, and 5 switches - ON
	pushSeqCmd(dt, 'FUELSYS_INTERFACE.Tank1Pump', 1)
	pushSeqCmd(dt, 'FUELSYS_INTERFACE.Tank2Pump', 1)
	pushSeqCmd(dt, 'FUELSYS_INTERFACE.Tank4Pump', 1)
	pushSeqCmd(dt, 'FUELSYS_INTERFACE.Tank5Pump', 1)

	# Fire Extinguisher
	# Fire Extinguisher Power switch - ON
	pushSeqCmd(dt, 'FIRE_EXTING_INTERFACE.Power', 1)
	# Fire Extinguisher Control switch - ON
	pushSeqCmd(dt, 'FIRE_EXTING_INTERFACE.SensorControl', 1)

	# Start APU
	# Starting APU (25s)
	pushSeqCmd(dt, 'ENGINE_INTERFACE.STARTUP_APU_Launch_Method', 0) # 0 = START, 1 = CRANK, 2 = FALSE START
	pushSeqCmd(dt, 'ENGINE_INTERFACE.STARTUP_APU_StartUp', 1) # Press
	pushSeqCmd(dt, 'ENGINE_INTERFACE.STARTUP_APU_StartUp', 0) # Release
	pushSeqCmd(apuStartTime, '', '', 'APU started')

	# Prepare for engine start
	pushSeqCmd(dt, 'ENGINE_INTERFACE.STARTUP_Engine_Launch_Method', 0) # 0 = START, 1 = CRANK

	# Starting Left Engine (55s)
	# Engine Start switch - LEFT
	pushSeqCmd(dt, 'ENGINE_INTERFACE.STARTUP_Engine_Select', 1) # 0 = RIGHT, 1 = LEFT
	# Engine Start button - Press
	pushSeqCmd(dt, 'ENGINE_INTERFACE.STARTUP_Engine_StartUp', 1) # Press
	pushSeqCmd(dt, 'ENGINE_INTERFACE.STARTUP_Engine_StartUp', 0) # Release
	pushSeqCmd(engineStartTime, '', '', 'Left engine started')

	# Starting Right Engine (55s)
	# Engine Start switch - RIGHT
	pushSeqCmd(dt, 'ENGINE_INTERFACE.STARTUP_Engine_Select', 0) # 0 = RIGHT, 1 = LEFT
	# Engine Start button - Press
	pushSeqCmd(dt, 'ENGINE_INTERFACE.STARTUP_Engine_StartUp', 1) # Press
	pushSeqCmd(dt, 'ENGINE_INTERFACE.STARTUP_Engine_StartUp', 0) # Release
	pushSeqCmd(engineStartTime, '', '', 'Right engine started')

	# Spool Up
	# Collective Throttle - Set to max (INCR, right)
	# Twist grip to max (INCR)
	pushSeqCmd(dt, 'scriptSimCommand', 'iCommandThrottleIncrease') # Correction lever increase (PgUp)
	pushSeqCmd(2, 'scriptSimCommand', 'iCommandThrottleStop') # Hold down for 2 seconds
	pushSeqCmd(engineSpoolTime, '', '', "Engines Spooled Up")

	# Generators and other electrics
	# Left Generator switch - ON
	pushSeqCmd(dt, 'ELEC_INTERFACE.ACGeneratorLeft', 1)
	# Right Generator switch - ON
	pushSeqCmd(dt, 'ELEC_INTERFACE.ACGeneratorRight', 1)
	# 115V Transformer switch - MAIN
	pushSeqCmd(dt, 'ELEC_INTERFACE.Transformer115vMainBackup', 2)
	# 36V Transformer switch - MAIN
	pushSeqCmd(dt, 'ELEC_INTERFACE.Transformer36vMainBackup', 2)
	# Left Rectifier switch - ON
	pushSeqCmd(dt, 'ELEC_INTERFACE.RectifierLeft', 1)
	# Right Rectifier switch - ON
	pushSeqCmd(dt, 'ELEC_INTERFACE.RectifierRight', 1)
	# AC Voltmeter knob - LEFT GENERATORS C-A
	pushSeqCmd(dt, 'ELEC_INTERFACE.ACGangSwitcher', 5)
	# Inverter PO-750A - OFF
	pushSeqCmd(dt, 'ELEC_INTERFACE.Rotary115vConverter', 0) # Switch
	pushSeqCmd(dt, 'ELEC_INTERFACE.Rotary115vConverterCover', 0) # Cover close

	# APU Stop button - Press
	pushSeqCmd(dt, 'ENGINE_INTERFACE.STARTUP_APU_Stop', 1)
	pushSeqCmd(dt, 'ENGINE_INTERFACE.STARTUP_APU_Stop', 0)

	# Power From Batt (Network To Batteries) switch - OFF
	pushSeqCmd(dt, 'ELEC_INTERFACE.NetworkToBatteries', 0) # Switch
	pushSeqCmd(dt, 'ELEC_INTERFACE.NetworkToBatteriesCover', 0) # Cover close

	# Left Panel switches
	# SPUU (Tail Roter Pitch Limiter) Power switch - ON
	pushSeqCmd(dt, 'SPUU_52.On_Off', 1)
	# Radar Altimeter (RV-5) Power switch - ON
	pushSeqCmd(dt, 'RADAR_ALTIMETER.POWER', 1)
	# Doppler (DISS-15) switch - ON
	pushSeqCmd(dt, 'DISS_15.POWER', 1)
	# Vert Gyro 1 switch - ON
	pushSeqCmd(dt, 'MGV1SU_1.POWER', 1)
	# Vert Gyro 2 switch - ON
	pushSeqCmd(dt, 'MGV1SU_2.POWER', 1)
	# Vert Gyro 1 Cage button - Press for 2 seconds
	pushSeqCmd(dt, 'MGV1SU_1.CAGE', 1) # Press
	pushSeqCmd(2, 'MGV1SU_1.CAGE', 0) # Release after 2 seconds
	# Vert Gyro 2 Cage button - Press for 2 seconds
	pushSeqCmd(dt, 'MGV1SU_2.CAGE', 1) # Press
	pushSeqCmd(2, 'MGV1SU_2.CAGE', 0) # Release after 2 seconds
	# Comp. System (GREBEN) switch - ON
	pushSeqCmd(dt, 'GREBEN.POWER', 1)
	#pushSeqCmd(1,{device = devices.KM_2, action =  avKM_2_commands.calc_magn_var, value = 1, message = _("set magnetic declination on KM-2, message_timeout = std_message_timeout) # This is done automatically by Petrovich??
	# Intercom (SPU-8) Network 1 switch - ON
	pushSeqCmd(dt, 'SPU_8.CMD_SPU8_NETWORK_1', 1)
	# Intercom (SPU-8) Network 2 switch - ON
	pushSeqCmd(dt, 'SPU_8.CMD_SPU8_NETWORK_2', 1)
	# HF Radio (JADRO-1A) switch - ON
	pushSeqCmd(dt, 'JADRO_1I.POWER', 1)
	# R-828 Radio switch - ON
	pushSeqCmd(dt, 'EUCALYPT_M24.POWER_ON_OFF2', 1)
	# R-863 Radio switch - ON
	pushSeqCmd(dt, 'R_863.POWER', 1)
	# Blink (Flasher) switch - ON
	pushSeqCmd(dt, 'INT_LIGHTS_SYSTEM.BlinkerSystem', 1)

	# IFF switch - ON
	pushSeqCmd(dt, 'IFF.CMD_IFF_Power_Sw', 1)

	# JADRO-1A Radio Mode knob - AM
	pushSeqCmd(dt, 'JADRO_1I.MODE', 2) # 0 = OFF, 1 = STB (SSB), 2 = AM

	# RWR switch - ON
	pushSeqCmd(dt, 'SPO_10.Command_SPO_POWER', 1)

	# RADAR ALTIMETER - Alert height to 0 m so it doesn't beep.
	pushSeqCmd(dt, 'RADAR_ALTIMETER.ROTARY', -3.125) # All the way down from any starting position.

	# PU-38 GREBEN compass system
	# GREBEN Tune/Oper switch - OPER
	pushSeqCmd(dt, 'GREBEN.SETUP_OPER', 1)
	# GREBEN Match (Sync) button - Press for 3 seconds
	pushSeqCmd(dt, 'GREBEN.MATCH', 1)
	pushSeqCmd(3, 'GREBEN.MATCH', 0)
	# GREBEN Mode switch - GYRO
	pushSeqCmd(dt, 'GREBEN.MODE', 1)

	# Autopilot
	# Pedals microswitch - ON (feet on pedals)
	# NOTE In game options, Special settings for Mi-24, set the following: Pedals Auto Move - unchecked, Pedals Microswitch Logic - Automatic Microswitch Off,
	pushSeqCmd(dt, 'scriptSpeech', 'Setting pedals microswitch on (feet on pedals).')
	pushSeqCmd(dt, 'AUTOPILOT.RudderSignal', 1) # Sending 1 turns microswitch on (feet on pedals).  Sending 0 turns microswitch off (feet off pedals).
	# Autopilot Yaw Channel button - ON
	pushSeqCmd(dt, 'AUTOPILOT.ButtonHon', 1) # Press
	pushSeqCmd(dt, 'AUTOPILOT.ButtonHon', 0) # Release
	# Autopilot Roll Channel button - ON
	pushSeqCmd(dt, 'AUTOPILOT.ButtonKon', 1) # Press
	pushSeqCmd(dt, 'AUTOPILOT.ButtonKon', 0) # Release
	# Autopilot Pitch Channel button - ON
	pushSeqCmd(dt, 'AUTOPILOT.ButtonTon', 1) # Press
	pushSeqCmd(dt, 'AUTOPILOT.ButtonTon', 0) # Release

	# Gunsight and Weapons Panel
	# Sight Power switch - ON # Weapons panel.
	pushSeqCmd(dt, 'ASP_17V.Power', 1)
	# Range Insert switch - AUTO # Weapons panel.
	pushSeqCmd(dt, 'ASP_17V.Range_Auto_Manual', 1)
	# Sight (Ranging) Mode switch - AUTO # Sight base.
	pushSeqCmd(dt, 'ASP_17V.Manual_Auto', 1)
	# Sync/Async switch - ASYNC # Sight base.
	pushSeqCmd(dt, 'ASP_17V.Sync_Async', 0)
	# Fire Ctrl (Master Arm) switch - ON # Weapons panel.
	pushSeqCmd(dt, 'WEAP_SYS.Pilot_SWITCHER_FIRE_CONTROL', 1)
	# MG Rate (Cannon ROF) switch - INCR # Weapons panel
	pushSeqCmd(dt, 'WEAP_SYS.Pilot_TEMP_NPU30', 1)
	# Fixed Crosshair Brightness - 60% # Sight base.
	pushSeqCmd(dt, 'ASP_17V.Brightness_NS', 0.6)
	# Aux Stores Lights switch - ON # Right angled panel bottom.
	pushSeqCmd(dt, 'INT_LIGHTS_SYSTEM.SpecialEquipmentPanelRedLights', 1)

	# Pilot-Operator (front) seat
	# Setting up Pilot-Operator switches...
	# Intercom (SPU-8) Power switch - ON
	pushSeqCmd(dt, 'SPU_8.CMD_SPU8_O_ICS', 1)
	# Safety Switches (Master Arm) gang bar - ON
	pushSeqCmd(dt, 'WEAP_SYS.Operator_SWITCHER_SAFE_WEAP', 1)
	# Missile Power switch - ON
	pushSeqCmd(dt, 'WEAP_SYS.Operator_URS_POWER', 1)
	# FDI (ADI) switch - ON
	pushSeqCmd(dt, 'PKP72M_INTERFACE.PKP72MoperatorSwitch', 1)
	# Cplr/Distr switch - ON # turns on gunsight?
	pushSeqCmd(dt, 'ASP_17V.USR', 1)
	# Missile Station Selector (SCHO) power switch - ON
	pushSeqCmd(dt, 'WEAP_SYS.Operator_POWER_SHO_SWITCHER', 1)
	# Guid. Unit Power switch - ON
	pushSeqCmd(dt, 'I9K113.Command_POWER_PN', 1)
	# Burst Length - SHORT
	pushSeqCmd(dt, 'WEAP_SYS.Operator_CHAIN_LENGTH_SHORT_MED_LONG', 2)
	# Fxd MG-30 Rate (Cannon ROF) switch - INCR # Weapons panel
	pushSeqCmd(dt, 'WEAP_SYS.Operator_OPERATOR_RATE_MORE', 1)
	#pushSeqCmd(dt, device = devices.I9K113, action = i9K113_commands.Command_NABL, value = 1) # OBSERVE
	#pushSeqCmd(dt, device = devices.I9K113, action = i9K113_commands.Command_STVORKI, value = 1) # Sight Doors
	# Done with Pilot-Operator switches

	# RWR test beep
	pushSeqCmd(dt, 'SPO_10.Command_SPO_SIGNAL', 1) # Turn on RWR audio
	pushSeqCmd(dt, 'SPO_10.Command_SPO_CHECK', 1) # Press (makes a beep)
	pushSeqCmd(dt, 'SPO_10.Command_SPO_CHECK', 0) # Release
	pushSeqCmd(dt, 'SPO_10.Command_SPO_SIGNAL', 0) # Turn off RWR audio

	# Pilot and Operator Fans - ON
	pushSeqCmd(dt, 'CPT_MECH.Command_CPT_MECH_FAN_PILOT', 1)
	pushSeqCmd(dt, 'CPT_MECH.Command_CPT_MECH_FAN_OPERATOR', 1)

	pushSeqCmd(dt, 'scriptSpeech', "Manual steps remaining: Set lights.  Tune radios.  Set doppler navigation.  Set altimeter to Q F E or Q N H.")

	return seq


def HotStart(config, vars, helper, *args, **kwargs):
	seq = []
	dt = 0.3

	pushSeqCmd = helper.makePushSeqCmd(seq)

	engineSpoolTime = 10 # Engines take 10 seconds to spool up from idle to flight-ready (collective twist grip max).

	# Start sequence
	pushSeqCmd(0, '', '', "Running Hot Start sequence.")

	# Twist grip to max (INCR)
	pushSeqCmd(dt, 'scriptSimCommand', 'iCommandThrottleIncrease') # Correction lever increase (PgUp)
	pushSeqCmd(2, 'scriptSimCommand', 'iCommandThrottleStop') # Hold down for 2 seconds
	pushSeqCmd(engineSpoolTime, '', '', "Engines Spooled Up")

	# Radio/ICS switch (Pilot) - ICS (allows rearming)
	pushSeqCmd(dt, 'SPU_8.CMD_SPU8_P_ICS_RADIO', 1)

	# Lights
	if vars['time'] == 'day':
		# Interior Lights - Pilot
		# Cargo lighting switch - OFF (left wall rear top)
		pushSeqCmd(dt, 'INT_LIGHTS_SYSTEM.CargoLightingWhiteBlue', 1) # 0 = BLUE, 1 = OFF, 2 = WHITE
		# Pilot Cabin Light - OFF (left wall rear top)
		pushSeqCmd(dt, 'INT_LIGHTS_SYSTEM.PilotCabinLightingWhiteRed', 1) # 0 = RED, 1 = OFF, 2 = WHITE
		# Day-Night switch - DAY (left wall rear top)
		pushSeqCmd(dt, 'INT_LIGHTS_SYSTEM.DayNight', 1) # 0 = NIGHT, 1 = DAY
		# AFCS buttons lighting - BRIGHT (not sure if this does anything) (left angled panel middle)
		pushSeqCmd(dt, 'AUTOPILOT.Lighting', 1) # 0 = DIM, 1 = BRIGHT
		# Map lighting - OFF (right angled panel top)
		pushSeqCmd(dt, 'MAP_DISPLAY.Lights', 1) # 0 = DIM, 1 = OFF, 2 = BRIGHT
		# RED LIGHTING INSTR PANEL AND RH PANELS knobs (right console rear inboard)
		# Builtin Red Lights Transformer - OFF
		pushSeqCmd(dt, 'INT_LIGHTS_SYSTEM.RedLightsPilotBuiltInRedLights', 0) # 0 = OFF, 10 = Full On (discrete steps)
		# Transformer 1 Group Of Red Lights Right And Pilot Panel - OFF
		pushSeqCmd(dt, 'INT_LIGHTS_SYSTEM.RedLightsPilotInstrumentPanelRightPanel_1', 0) # 0 = OFF, 10 = Full On (discrete steps)
		# Transformer 2 Group Of Red Lights Right And Pilot Panel - OFF
		pushSeqCmd(dt, 'INT_LIGHTS_SYSTEM.RedLightsPilotInstrumentPanelRightPanel_2', 0) # 0 = OFF, 10 = Full On (discrete steps)
		# LEFT PANELS RED LIGHTNG knobs (right angled panel bottom)
		# Transformer 1 Group Of Red Lights Right And Pilot Panel - OFF
		pushSeqCmd(dt, 'INT_LIGHTS_SYSTEM.RedLightsPilotLeftPanel_1', 0) # 0 = OFF, 10 = Full On (discrete steps)
		# Transformer 2 Group Of Red Lights Right And Pilot Panel - OFF
		pushSeqCmd(dt, 'INT_LIGHTS_SYSTEM.RedLightsPilotLeftPanel_2', 0) # 0 = OFF, 10 = Full On (discrete steps)
		# AUX STORES LIGHTS switch (right angled panel bottom)
		# Armament Panel Red Lights Switch - OFF (these are very bright and not really necessary)
		pushSeqCmd(dt, 'INT_LIGHTS_SYSTEM.SpecialEquipmentPanelRedLights', 0) # 0 = OFF, 1 = ON

		# Interior Lights - Operator
		# Operator Cabin Light - OFF (Operator, left wall middle)
		pushSeqCmd(dt, 'INT_LIGHTS_SYSTEM.OperatorCabinLightingWhiteRed', 1) # 0 = RED, 1 = OFF, 2 = WHITE
		# Transformer 1 Group Of Red Lights Left And Operator Panel - OFF (Operator, left wall forward bottom)
		pushSeqCmd(dt, 'INT_LIGHTS_SYSTEM.RedLightsOperatorPanel_1', 0) # 0 = OFF, 10 = Full On (discrete steps)
		# Transformer 2 Group Of Red Lights Left And Operator Panel - OFF (Operator, left wall forward bottom)
		pushSeqCmd(dt, 'INT_LIGHTS_SYSTEM.RedLightsOperatorPanel_2', 0) # 0 = OFF, 10 = Full On (discrete steps)

		# Exterior Lights
		# Strobe lights - OFF (left wall forward top)
		pushSeqCmd(dt, 'EXT_LIGHTS_SYSTEM.StrobeLight', 0)
		# Blade Tip lights - OFF (left wall forward top)
		pushSeqCmd(dt, 'EXT_LIGHTS_SYSTEM.TipLights', 0)
		# Formation lights - OFF (left wall forward top)
		pushSeqCmd(dt, 'EXT_LIGHTS_SYSTEM.FormationLights', 1) # 0 = DIM, 1 = OFF, 2 = BRIGHT
		# Nav lights - OFF (left angled panel top)
		pushSeqCmd(dt, 'EXT_LIGHTS_SYSTEM.NavLtSwitch', 1) # 0 = DIM, 1 = OFF, 2 = BRIGHT

	else: # Night
		# Interior Lights - Pilot
		# Cargo lighting switch - OFF (left wall rear top)
		pushSeqCmd(dt, 'INT_LIGHTS_SYSTEM.CargoLightingWhiteBlue', 1) # 0 = BLUE, 1 = OFF, 2 = WHITE
		# Pilot Cabin Light - OFF (left wall rear top)
		pushSeqCmd(dt, 'INT_LIGHTS_SYSTEM.PilotCabinLightingWhiteRed', 1) # 0 = RED, 1 = OFF, 2 = WHITE
		# Day-Night switch - NIGHT (left wall rear top)
		pushSeqCmd(dt, 'INT_LIGHTS_SYSTEM.DayNight', 0) # 0 = NIGHT, 1 = DAY
		# AFCS buttons lighting - DIM (not sure if this does anything) (left angled panel middle)
		pushSeqCmd(dt, 'AUTOPILOT.Lighting', 0) # 0 = DIM, 1 = BRIGHT
		# Map lighting - DIM (right angled panel top)
		pushSeqCmd(dt, 'MAP_DISPLAY.Lights', 0) # 0 = DIM, 1 = OFF, 2 = BRIGHT
		# RED LIGHTING INSTR PANEL AND RH PANELS knobs (right console rear inboard)
		# Builtin Red Lights Transformer - Half
		pushSeqCmd(dt, 'INT_LIGHTS_SYSTEM.RedLightsPilotBuiltInRedLights', 5) # 0 = OFF, 10 = Full On (discrete steps)
		# Transformer 1 Group Of Red Lights Right And Pilot Panel - Half
		pushSeqCmd(dt, 'INT_LIGHTS_SYSTEM.RedLightsPilotInstrumentPanelRightPanel_1', 5) # 0 = OFF, 10 = Full On (discrete steps)
		# Transformer 2 Group Of Red Lights Right And Pilot Panel - Half
		pushSeqCmd(dt, 'INT_LIGHTS_SYSTEM.RedLightsPilotInstrumentPanelRightPanel_2', 5) # 0 = OFF, 10 = Full On (discrete steps)
		# LEFT PANELS RED LIGHTNG knobs (right angled panel bottom)
		# Transformer 1 Group Of Red Lights Right And Pilot Panel - Half
		pushSeqCmd(dt, 'INT_LIGHTS_SYSTEM.RedLightsPilotLeftPanel_1', 5) # 0 = OFF, 10 = Full On (discrete steps)
		# Transformer 2 Group Of Red Lights Right And Pilot Panel - Half
		pushSeqCmd(dt, 'INT_LIGHTS_SYSTEM.RedLightsPilotLeftPanel_2', 5) # 0 = OFF, 10 = Full On (discrete steps)
		# AUX STORES LIGHTS switch (right angled panel bottom)
		# Armament Panel Red Lights Switch - OFF (these are very bright and not really necessary)
		pushSeqCmd(dt, 'INT_LIGHTS_SYSTEM.SpecialEquipmentPanelRedLights', 0) # 0 = OFF, 1 = ON

		# Interior Lights - Operator
		# Operator Cabin Light - OFF (Operator, left wall middle)
		pushSeqCmd(dt, 'INT_LIGHTS_SYSTEM.OperatorCabinLightingWhiteRed', 1) # 0 = RED, 1 = OFF, 2 = WHITE
		# Transformer 1 Group Of Red Lights Left And Operator Panel - Half (Operator, left wall forward bottom)
		pushSeqCmd(dt, 'INT_LIGHTS_SYSTEM.RedLightsOperatorPanel_1', 5) # 0 = OFF, 10 = Full On (discrete steps)
		# Transformer 2 Group Of Red Lights Left And Operator Panel - Half (Operator, left wall forward bottom)
		pushSeqCmd(dt, 'INT_LIGHTS_SYSTEM.RedLightsOperatorPanel_2', 5) # 0 = OFF, 10 = Full On (discrete steps)

		# Exterior Lights
		# Strobe lights - OFF (left wall forward top)
		pushSeqCmd(dt, 'EXT_LIGHTS_SYSTEM.StrobeLight', 0)
		# Blade Tip lights - OFF (left wall forward top)
		pushSeqCmd(dt, 'EXT_LIGHTS_SYSTEM.TipLights', 0)
		# Formation lights - OFF (left wall forward top)
		pushSeqCmd(dt, 'EXT_LIGHTS_SYSTEM.FormationLights', 1) # 0 = DIM, 1 = OFF, 2 = BRIGHT
		# Nav lights - OFF (left angled panel top)
		pushSeqCmd(dt, 'EXT_LIGHTS_SYSTEM.NavLtSwitch', 1) # 0 = DIM, 1 = OFF, 2 = BRIGHT

	# Electric Power
	# DC Voltmeter knob - BATT
	pushSeqCmd(dt, 'ELEC_INTERFACE.DCGangSwitcher', 2)

	# Generators and other electrics
	# AC Voltmeter knob - LEFT GENERATORS C-A
	pushSeqCmd(dt, 'ELEC_INTERFACE.ACGangSwitcher', 5)

	# IFF switch - ON
	pushSeqCmd(dt, 'IFF.CMD_IFF_Power_Sw', 1)

	# RWR switch - ON
	pushSeqCmd(dt, 'SPO_10.Command_SPO_POWER', 1)

	# RADAR ALTIMETER - Alert height to 0 m so it doesn't beep.
	pushSeqCmd(dt, 'RADAR_ALTIMETER.ROTARY', -3.125) # All the way down from any starting position.

	# PU-38 GREBEN compass system
	# GREBEN Match (Sync) button - Press for 3 seconds
	pushSeqCmd(dt, 'GREBEN.MATCH', 1)
	pushSeqCmd(3, 'GREBEN.MATCH', 0)

	# Autopilot
	# Pedals microswitch - ON (feet on pedals)
	# NOTE In game options, Special settings for Mi-24, set the following: Pedals Auto Move - unchecked, Pedals Microswitch Logic - Automatic Microswitch Off,
	pushSeqCmd(dt, 'scriptSpeech', 'Setting pedals microswitch on (feet on pedals).')
	pushSeqCmd(dt, 'AUTOPILOT.RudderSignal', 1) # Sending 1 turns microswitch on (feet on pedals).  Sending 0 turns microswitch off (feet off pedals).

	# Gunsight and Weapons Panel
	# Sight Power switch - ON # Weapons panel.
	pushSeqCmd(dt, 'ASP_17V.Power', 1)
	# Range Insert switch - AUTO # Weapons panel.
	pushSeqCmd(dt, 'ASP_17V.Range_Auto_Manual', 1)
	# Sight (Ranging) Mode switch - AUTO # Sight base.
	pushSeqCmd(dt, 'ASP_17V.Manual_Auto', 1)
	# Sync/Async switch - ASYNC # Sight base.
	pushSeqCmd(dt, 'ASP_17V.Sync_Async', 0)
	# Fire Ctrl (Master Arm) switch - ON # Weapons panel.
	pushSeqCmd(dt, 'WEAP_SYS.Pilot_SWITCHER_FIRE_CONTROL', 1)
	# MG Rate (Cannon ROF) switch - INCR # Weapons panel
	pushSeqCmd(dt, 'WEAP_SYS.Pilot_TEMP_NPU30', 1)
	# Fixed Crosshair Brightness - 60% # Sight base.
	pushSeqCmd(dt, 'ASP_17V.Brightness_NS', 0.6)

	# Pilot-Operator (front) seat
	# Setting up Pilot-Operator switches...
	# Intercom (SPU-8) Power switch - ON
	pushSeqCmd(dt, 'SPU_8.CMD_SPU8_O_ICS', 1)
	# Safety Switches (Master Arm) gang bar - ON
	pushSeqCmd(dt, 'WEAP_SYS.Operator_SWITCHER_SAFE_WEAP', 1)
	# Missile Power switch - ON
	pushSeqCmd(dt, 'WEAP_SYS.Operator_URS_POWER', 1)
	# Cplr/Distr switch - ON # turns on gunsight?
	pushSeqCmd(dt, 'ASP_17V.USR', 1)
	# Missile Station Selector (SCHO) power switch - ON
	pushSeqCmd(dt, 'WEAP_SYS.Operator_POWER_SHO_SWITCHER', 1)
	# Guid. Unit Power switch - ON
	pushSeqCmd(dt, 'I9K113.Command_POWER_PN', 1)
	# Burst Length - SHORT
	pushSeqCmd(dt, 'WEAP_SYS.Operator_CHAIN_LENGTH_SHORT_MED_LONG', 2)
	# Fxd MG-30 Rate (Cannon ROF) switch - INCR # Weapons panel
	pushSeqCmd(dt, 'WEAP_SYS.Operator_OPERATOR_RATE_MORE', 1)
	#pushSeqCmd(dt, device = devices.I9K113, action = i9K113_commands.Command_NABL, value = 1) # OBSERVE
	#pushSeqCmd(dt, device = devices.I9K113, action = i9K113_commands.Command_STVORKI, value = 1) # Sight Doors
	# Done with Pilot-Operator switches

	# RWR test beep
	pushSeqCmd(dt, 'SPO_10.Command_SPO_SIGNAL', 1) # Turn on RWR audio
	pushSeqCmd(dt, 'SPO_10.Command_SPO_CHECK', 1) # Press (makes a beep)
	pushSeqCmd(dt, 'SPO_10.Command_SPO_CHECK', 0) # Release
	pushSeqCmd(dt, 'SPO_10.Command_SPO_SIGNAL', 0) # Turn off RWR audio

	# Pilot and Operator Fans - ON
	pushSeqCmd(dt, 'CPT_MECH.Command_CPT_MECH_FAN_PILOT', 1)
	pushSeqCmd(dt, 'CPT_MECH.Command_CPT_MECH_FAN_OPERATOR', 1)

	pushSeqCmd(dt, 'scriptSpeech', "Manual steps remaining: Set lights.  Tune radios.  Set doppler navigation.  Set altimeter to Q F E or Q N H.")

	return seq


def AirStart(config, vars, helper, *args, **kwargs):
	seq = []
	dt = 0.3

	pushSeqCmd = helper.makePushSeqCmd(seq)

	# Start sequence
	pushSeqCmd(0, '', '', "Running Air Start sequence.")

	# Radio/ICS switch (Pilot) - ICS (allows rearming)
	pushSeqCmd(dt, 'SPU_8.CMD_SPU8_P_ICS_RADIO', 1)

	# Lights
	if vars['time'] == 'day':
		# Interior Lights - Pilot
		# Cargo lighting switch - OFF (left wall rear top)
		pushSeqCmd(dt, 'INT_LIGHTS_SYSTEM.CargoLightingWhiteBlue', 1) # 0 = BLUE, 1 = OFF, 2 = WHITE
		# Pilot Cabin Light - OFF (left wall rear top)
		pushSeqCmd(dt, 'INT_LIGHTS_SYSTEM.PilotCabinLightingWhiteRed', 1) # 0 = RED, 1 = OFF, 2 = WHITE
		# Day-Night switch - DAY (left wall rear top)
		pushSeqCmd(dt, 'INT_LIGHTS_SYSTEM.DayNight', 1) # 0 = NIGHT, 1 = DAY
		# AFCS buttons lighting - BRIGHT (not sure if this does anything) (left angled panel middle)
		pushSeqCmd(dt, 'AUTOPILOT.Lighting', 1) # 0 = DIM, 1 = BRIGHT
		# Map lighting - OFF (right angled panel top)
		pushSeqCmd(dt, 'MAP_DISPLAY.Lights', 1) # 0 = DIM, 1 = OFF, 2 = BRIGHT
		# RED LIGHTING INSTR PANEL AND RH PANELS knobs (right console rear inboard)
		# Builtin Red Lights Transformer - OFF
		pushSeqCmd(dt, 'INT_LIGHTS_SYSTEM.RedLightsPilotBuiltInRedLights', 0) # 0 = OFF, 10 = Full On (discrete steps)
		# Transformer 1 Group Of Red Lights Right And Pilot Panel - OFF
		pushSeqCmd(dt, 'INT_LIGHTS_SYSTEM.RedLightsPilotInstrumentPanelRightPanel_1', 0) # 0 = OFF, 10 = Full On (discrete steps)
		# Transformer 2 Group Of Red Lights Right And Pilot Panel - OFF
		pushSeqCmd(dt, 'INT_LIGHTS_SYSTEM.RedLightsPilotInstrumentPanelRightPanel_2', 0) # 0 = OFF, 10 = Full On (discrete steps)
		# LEFT PANELS RED LIGHTNG knobs (right angled panel bottom)
		# Transformer 1 Group Of Red Lights Right And Pilot Panel - OFF
		pushSeqCmd(dt, 'INT_LIGHTS_SYSTEM.RedLightsPilotLeftPanel_1', 0) # 0 = OFF, 10 = Full On (discrete steps)
		# Transformer 2 Group Of Red Lights Right And Pilot Panel - OFF
		pushSeqCmd(dt, 'INT_LIGHTS_SYSTEM.RedLightsPilotLeftPanel_2', 0) # 0 = OFF, 10 = Full On (discrete steps)
		# AUX STORES LIGHTS switch (right angled panel bottom)
		# Armament Panel Red Lights Switch - OFF (these are very bright and not really necessary)
		pushSeqCmd(dt, 'INT_LIGHTS_SYSTEM.SpecialEquipmentPanelRedLights', 0) # 0 = OFF, 1 = ON

		# Interior Lights - Operator
		# Operator Cabin Light - OFF (Operator, left wall middle)
		pushSeqCmd(dt, 'INT_LIGHTS_SYSTEM.OperatorCabinLightingWhiteRed', 1) # 0 = RED, 1 = OFF, 2 = WHITE
		# Transformer 1 Group Of Red Lights Left And Operator Panel - OFF (Operator, left wall forward bottom)
		pushSeqCmd(dt, 'INT_LIGHTS_SYSTEM.RedLightsOperatorPanel_1', 0) # 0 = OFF, 10 = Full On (discrete steps)
		# Transformer 2 Group Of Red Lights Left And Operator Panel - OFF (Operator, left wall forward bottom)
		pushSeqCmd(dt, 'INT_LIGHTS_SYSTEM.RedLightsOperatorPanel_2', 0) # 0 = OFF, 10 = Full On (discrete steps)

		# Exterior Lights
		# Strobe lights - OFF (left wall forward top)
		pushSeqCmd(dt, 'EXT_LIGHTS_SYSTEM.StrobeLight', 0)
		# Blade Tip lights - OFF (left wall forward top)
		pushSeqCmd(dt, 'EXT_LIGHTS_SYSTEM.TipLights', 0)
		# Formation lights - OFF (left wall forward top)
		pushSeqCmd(dt, 'EXT_LIGHTS_SYSTEM.FormationLights', 1) # 0 = DIM, 1 = OFF, 2 = BRIGHT
		# Nav lights - OFF (left angled panel top)
		pushSeqCmd(dt, 'EXT_LIGHTS_SYSTEM.NavLtSwitch', 1) # 0 = DIM, 1 = OFF, 2 = BRIGHT

	else: # Night
		# Interior Lights - Pilot
		# Cargo lighting switch - OFF (left wall rear top)
		pushSeqCmd(dt, 'INT_LIGHTS_SYSTEM.CargoLightingWhiteBlue', 1) # 0 = BLUE, 1 = OFF, 2 = WHITE
		# Pilot Cabin Light - OFF (left wall rear top)
		pushSeqCmd(dt, 'INT_LIGHTS_SYSTEM.PilotCabinLightingWhiteRed', 1) # 0 = RED, 1 = OFF, 2 = WHITE
		# Day-Night switch - NIGHT (left wall rear top)
		pushSeqCmd(dt, 'INT_LIGHTS_SYSTEM.DayNight', 0) # 0 = NIGHT, 1 = DAY
		# AFCS buttons lighting - DIM (not sure if this does anything) (left angled panel middle)
		pushSeqCmd(dt, 'AUTOPILOT.Lighting', 0) # 0 = DIM, 1 = BRIGHT
		# Map lighting - DIM (right angled panel top)
		pushSeqCmd(dt, 'MAP_DISPLAY.Lights', 0) # 0 = DIM, 1 = OFF, 2 = BRIGHT
		# RED LIGHTING INSTR PANEL AND RH PANELS knobs (right console rear inboard)
		# Builtin Red Lights Transformer - Half
		pushSeqCmd(dt, 'INT_LIGHTS_SYSTEM.RedLightsPilotBuiltInRedLights', 5) # 0 = OFF, 10 = Full On (discrete steps)
		# Transformer 1 Group Of Red Lights Right And Pilot Panel - Half
		pushSeqCmd(dt, 'INT_LIGHTS_SYSTEM.RedLightsPilotInstrumentPanelRightPanel_1', 5) # 0 = OFF, 10 = Full On (discrete steps)
		# Transformer 2 Group Of Red Lights Right And Pilot Panel - Half
		pushSeqCmd(dt, 'INT_LIGHTS_SYSTEM.RedLightsPilotInstrumentPanelRightPanel_2', 5) # 0 = OFF, 10 = Full On (discrete steps)
		# LEFT PANELS RED LIGHTNG knobs (right angled panel bottom)
		# Transformer 1 Group Of Red Lights Right And Pilot Panel - Half
		pushSeqCmd(dt, 'INT_LIGHTS_SYSTEM.RedLightsPilotLeftPanel_1', 5) # 0 = OFF, 10 = Full On (discrete steps)
		# Transformer 2 Group Of Red Lights Right And Pilot Panel - Half
		pushSeqCmd(dt, 'INT_LIGHTS_SYSTEM.RedLightsPilotLeftPanel_2', 5) # 0 = OFF, 10 = Full On (discrete steps)
		# AUX STORES LIGHTS switch (right angled panel bottom)
		# Armament Panel Red Lights Switch - OFF (these are very bright and not really necessary)
		pushSeqCmd(dt, 'INT_LIGHTS_SYSTEM.SpecialEquipmentPanelRedLights', 0) # 0 = OFF, 1 = ON

		# Interior Lights - Operator
		# Operator Cabin Light - OFF (Operator, left wall middle)
		pushSeqCmd(dt, 'INT_LIGHTS_SYSTEM.OperatorCabinLightingWhiteRed', 1) # 0 = RED, 1 = OFF, 2 = WHITE
		# Transformer 1 Group Of Red Lights Left And Operator Panel - Half (Operator, left wall forward bottom)
		pushSeqCmd(dt, 'INT_LIGHTS_SYSTEM.RedLightsOperatorPanel_1', 5) # 0 = OFF, 10 = Full On (discrete steps)
		# Transformer 2 Group Of Red Lights Left And Operator Panel - Half (Operator, left wall forward bottom)
		pushSeqCmd(dt, 'INT_LIGHTS_SYSTEM.RedLightsOperatorPanel_2', 5) # 0 = OFF, 10 = Full On (discrete steps)

		# Exterior Lights
		# Strobe lights - OFF (left wall forward top)
		pushSeqCmd(dt, 'EXT_LIGHTS_SYSTEM.StrobeLight', 0)
		# Blade Tip lights - OFF (left wall forward top)
		pushSeqCmd(dt, 'EXT_LIGHTS_SYSTEM.TipLights', 0)
		# Formation lights - OFF (left wall forward top)
		pushSeqCmd(dt, 'EXT_LIGHTS_SYSTEM.FormationLights', 1) # 0 = DIM, 1 = OFF, 2 = BRIGHT
		# Nav lights - OFF (left angled panel top)
		pushSeqCmd(dt, 'EXT_LIGHTS_SYSTEM.NavLtSwitch', 1) # 0 = DIM, 1 = OFF, 2 = BRIGHT

	# Electric Power
	# DC Voltmeter knob - BATT
	pushSeqCmd(dt, 'ELEC_INTERFACE.DCGangSwitcher', 2)

	# Generators and other electrics
	# AC Voltmeter knob - LEFT GENERATORS C-A
	pushSeqCmd(dt, 'ELEC_INTERFACE.ACGangSwitcher', 5)

	# IFF switch - ON
	pushSeqCmd(dt, 'IFF.CMD_IFF_Power_Sw', 1)

	# RADAR ALTIMETER - Alert height to 0 m so it doesn't beep.
	pushSeqCmd(dt, 'RADAR_ALTIMETER.ROTARY', -3.125) # All the way down from any starting position.

	# Autopilot
	# Pedals microswitch - ON (feet on pedals)
	# NOTE In game options, Special settings for Mi-24, set the following: Pedals Auto Move - unchecked, Pedals Microswitch Logic - Automatic Microswitch Off,
	pushSeqCmd(dt, 'scriptSpeech', 'Setting pedals microswitch on (feet on pedals).')
	pushSeqCmd(dt, 'AUTOPILOT.RudderSignal', 1) # Sending 1 turns microswitch on (feet on pedals).  Sending 0 turns microswitch off (feet off pedals).

	# Gunsight and Weapons Panel
	# MG Rate (Cannon ROF) switch - INCR # Weapons panel
	pushSeqCmd(dt, 'WEAP_SYS.Pilot_TEMP_NPU30', 1)
	# Fixed Crosshair Brightness - 60% # Sight base.
	pushSeqCmd(dt, 'ASP_17V.Brightness_NS', 0.6)

	# Pilot-Operator (front) seat
	# Setting up Pilot-Operator switches...
	# Intercom (SPU-8) Power switch - ON
	pushSeqCmd(dt, 'SPU_8.CMD_SPU8_O_ICS', 1)
	# Burst Length - SHORT
	pushSeqCmd(dt, 'WEAP_SYS.Operator_CHAIN_LENGTH_SHORT_MED_LONG', 2)
	# Fxd MG-30 Rate (Cannon ROF) switch - INCR # Weapons panel
	pushSeqCmd(dt, 'WEAP_SYS.Operator_OPERATOR_RATE_MORE', 1)
	#pushSeqCmd(dt, device = devices.I9K113, action = i9K113_commands.Command_NABL, value = 1) # OBSERVE
	#pushSeqCmd(dt, device = devices.I9K113, action = i9K113_commands.Command_STVORKI, value = 1) # Sight Doors
	# Done with Pilot-Operator switches

	# RWR test beep
	pushSeqCmd(dt, 'SPO_10.Command_SPO_SIGNAL', 1) # Turn on RWR audio
	pushSeqCmd(dt, 'SPO_10.Command_SPO_CHECK', 1) # Press (makes a beep)
	pushSeqCmd(dt, 'SPO_10.Command_SPO_CHECK', 0) # Release
	pushSeqCmd(dt, 'SPO_10.Command_SPO_SIGNAL', 0) # Turn off RWR audio

	# Pilot and Operator Fans - ON
	pushSeqCmd(dt, 'CPT_MECH.Command_CPT_MECH_FAN_PILOT', 1)
	pushSeqCmd(dt, 'CPT_MECH.Command_CPT_MECH_FAN_OPERATOR', 1)

	pushSeqCmd(dt, 'scriptSpeech', "Manual steps remaining: Set lights.  Tune radios.  Set doppler navigation.  Set altimeter to Q F E or Q N H.")

	return seq


def Shutdown(config, vars, helper, *args, **kwargs):
	seq = []
	dt = 0.3

	pushSeqCmd = helper.makePushSeqCmd(seq)

	# Start sequence
	pushSeqCmd(0, '', '', "Running Shutdown sequence.")

	# Lights
	# Strobe lights - OFF
	pushSeqCmd(dt, 'EXT_LIGHTS_SYSTEM.StrobeLight', 0)
	# Blade Tip lights - OFF
	pushSeqCmd(dt, 'EXT_LIGHTS_SYSTEM.TipLights', 0)
	# Formation lights - OFF
	pushSeqCmd(dt, 'EXT_LIGHTS_SYSTEM.FormationLights', 1) # 0 = DIM, 1 = OFF, 2 = BRIGHT
	# Nav lights - OFF
	pushSeqCmd(dt, 'EXT_LIGHTS_SYSTEM.NavLtSwitch', 1) # 0 = DIM, 1 = OFF, 2 = BRIGHT

	# Left Panel switches
	# SPUU (Tail Roter Pitch Limiter) Power switch - OFF
	pushSeqCmd(dt, 'SPUU_52.On_Off', 0)
	# Radar Altimeter (RV-5) Power switch - OFF
	pushSeqCmd(dt, 'RADAR_ALTIMETER.POWER', 0)
	# Doppler (DISS-15) switch - OFF
	pushSeqCmd(dt, 'DISS_15.POWER', 0)
	# Vert Gyro 1 switch - OFF
	pushSeqCmd(dt, 'MGV1SU_1.POWER', 0)
	# Vert Gyro 2 switch - OFF
	pushSeqCmd(dt, 'MGV1SU_2.POWER', 0)
	# Comp. System (GREBEN) switch - OFF
	pushSeqCmd(dt, 'GREBEN.POWER', 0)
	# Intercom (SPU-8) Network 1 switch - OFF
	pushSeqCmd(dt, 'SPU_8.CMD_SPU8_NETWORK_1', 0)
	# Intercom (SPU-8) Network 2 switch - OFF
	pushSeqCmd(dt, 'SPU_8.CMD_SPU8_NETWORK_2', 0)
	# HF Radio (JADRO-1A) switch - OFF
	pushSeqCmd(dt, 'JADRO_1I.POWER', 0)
	# R-828 Radio switch - OFF
	pushSeqCmd(dt, 'EUCALYPT_M24.POWER_ON_OFF2', 0)
	# R-863 Radio switch - OFF
	pushSeqCmd(dt, 'R_863.POWER', 0)
	# Blink (Flasher) switch - OFF
	pushSeqCmd(dt, 'INT_LIGHTS_SYSTEM.BlinkerSystem', 0)

	# IFF switch - OFF
	pushSeqCmd(dt, 'IFF.CMD_IFF_Power_Sw', 0)

	# RWR switch - OFF
	pushSeqCmd(dt, 'SPO_10.Command_SPO_POWER', 0)

	# Pilot-Operator (front) seat
	# Setting up Pilot-Operator switches...
	# Intercom (SPU-8) Power switch - OFF
	pushSeqCmd(dt, 'SPU_8.CMD_SPU8_O_ICS', 0)
	# Safety Switches (Master Arm) gang bar - OFF
	pushSeqCmd(dt, 'WEAP_SYS.Operator_SWITCHER_SAFE_WEAP', 0)
	# Missile Power switch - OFF
	pushSeqCmd(dt, 'WEAP_SYS.Operator_URS_POWER', 0)
	# FDI (ADI) switch - OFF
	pushSeqCmd(dt, 'PKP72M_INTERFACE.PKP72MoperatorSwitch', 0)
	# Cplr/Distr switch - OFF # turns on gunsight?
	pushSeqCmd(dt, 'ASP_17V.USR', 0)
	# Missile Station Selector (SCHO) power switch - OFF
	pushSeqCmd(dt, 'WEAP_SYS.Operator_POWER_SHO_SWITCHER', 0)
	# Guid. Unit Power switch - OFF
	pushSeqCmd(dt, 'I9K113.Command_POWER_PN', 0)
	# Done with Pilot-Operator switches

	# Pilot and Operator Fans - OFF
	pushSeqCmd(dt, 'CPT_MECH.Command_CPT_MECH_FAN_PILOT', 0)
	pushSeqCmd(dt, 'CPT_MECH.Command_CPT_MECH_FAN_OPERATOR', 0)

	# JADRO-1A Radio Mode knob - OFF
	pushSeqCmd(dt, 'JADRO_1I.MODE', 0) # 0 = OFF, 1 = STB (SSB), 2 = AM

	# Gunsight and Weapons Panel
	# Sight Power switch - OFF # Weapons panel.
	pushSeqCmd(dt, 'ASP_17V.Power', 0)
	# Range Insert switch - AUTO # Weapons panel.
	pushSeqCmd(dt, 'ASP_17V.Range_Auto_Manual', 0)
	# Sight (Ranging) Mode switch - AUTO # Sight base.
	pushSeqCmd(dt, 'ASP_17V.Manual_Auto', 0)
	# Sync/Async switch - ASYNC # Sight base.
	pushSeqCmd(dt, 'ASP_17V.Sync_Async', 0)
	# Fire Ctrl (Master Arm) switch - OFF # Weapons panel.
	pushSeqCmd(dt, 'WEAP_SYS.Pilot_SWITCHER_FIRE_CONTROL', 0)
	# Fixed Crosshair Brightness - 100% # Sight base.
	pushSeqCmd(dt, 'ASP_17V.Brightness_NS', 1.0)
	# Aux Stores Lights switch - OFF # Right angled panel bottom.
	pushSeqCmd(dt, 'INT_LIGHTS_SYSTEM.SpecialEquipmentPanelRedLights', 0)

	# Unseal and depressurize cabin
	# Cabin Press valve - Close (CCW)
	pushSeqCmd(dt, 'ECS_INTERFACE.Sealing_valve', 1)
	# Cabin Depress switch - OFF
	pushSeqCmd(dt, 'ECS_INTERFACE.CabinUnseal', 0)
	# Blowdown Conditioning switch - OFF
	pushSeqCmd(dt, 'ECS_INTERFACE.BlowdownConditioning', 1)

	# Cockpit Doors - Open
	pushSeqCmd(dt, 'CPT_MECH.Command_CPT_MECH_Door_EXT', 1) # Open/close cockpit door (LCtrl+C)

	# Twist grip to min (DECR)
	pushSeqCmd(dt, 'scriptSimCommand', 'iCommandThrottleDecrease') # Correction lever decrease (PgDn)
	pushSeqCmd(2, 'scriptSimCommand', 'iCommandThrottleStop') # Hold down for 2 seconds

	# Wait for rotor to spool down to 80%.
	pushSeqCmd(dt, 'scriptSpeech', 'Waiting for rotor to spool down to 80%')
	pushSeqCmd(dt, 'scriptCockpitState', control='Mi-24P/arg.RotorRPM_Pilot', condition='<=', value=0.71) # Wait for rotor RPM to be <= 80%

	# Left Engine Stop lever - ON
	pushSeqCmd(dt, 'ENGINE_INTERFACE.LEVER_Left_Engine_Lock', 1)
	# Right Engine Stop lever - ON
	pushSeqCmd(dt, 'ENGINE_INTERFACE.LEVER_Right_Engine_Lock', 1)

	# Wait for rotor to get to 15%.
	pushSeqCmd(dt, 'scriptSpeech', 'Waiting for rotor to spool down to 15%')
	pushSeqCmd(dt, 'scriptCockpitState', control='Mi-24P/arg.RotorRPM_Pilot', condition='<=', value=0.13) # Wait for rotor RPM to be <= 15%

	# Rotor Brake - ON
	pushSeqCmd(dt, 'ENGINE_INTERFACE.LEVER_Rotor_Lock', 1)

	# Fuel System
	# Service (Feed) Tanks 1 switch - OFF
	pushSeqCmd(dt, 'FUELSYS_INTERFACE.ValveTank1', 0)
	# Service (Feed) Tanks 2 switch - OFF
	pushSeqCmd(dt, 'FUELSYS_INTERFACE.ValveTank2', 0)
	# Fuel Shutoff Left switch - OFF
	pushSeqCmd(dt, 'FUELSYS_INTERFACE.ValveLeftEngineCover', 1) # Cover open
	pushSeqCmd(dt, 'FUELSYS_INTERFACE.ValveLeftEngine', 0) # Switch
	pushSeqCmd(dt, 'FUELSYS_INTERFACE.ValveLeftEngineCover', 0) # Cover close
	# Fuel Shutoff Right switch - OFF
	pushSeqCmd(dt, 'FUELSYS_INTERFACE.ValveRightEngineCover', 1) # Cover open
	pushSeqCmd(dt, 'FUELSYS_INTERFACE.ValveRightEngine', 0) # Switch
	pushSeqCmd(dt, 'FUELSYS_INTERFACE.ValveRightEngineCover', 0) # Cover close
	# Fuel Crossfeed (Delimiter) switch - OFF # "Fuel Delimiter Valve"
	pushSeqCmd(dt, 'FUELSYS_INTERFACE.ValveDelimiter', 0)
	# Service Tank Pumps 1, 2, 4, and 5 switches - OFF
	pushSeqCmd(dt, 'FUELSYS_INTERFACE.Tank1Pump', 0)
	pushSeqCmd(dt, 'FUELSYS_INTERFACE.Tank2Pump', 0)
	pushSeqCmd(dt, 'FUELSYS_INTERFACE.Tank4Pump', 0)
	pushSeqCmd(dt, 'FUELSYS_INTERFACE.Tank5Pump', 0)

	# Fire Extinguisher
	# Fire Extinguisher Power switch - OFF
	pushSeqCmd(dt, 'FIRE_EXTING_INTERFACE.Power', 0)
	# Fire Extinguisher Control switch - OFF
	pushSeqCmd(dt, 'FIRE_EXTING_INTERFACE.SensorControl', 0)

	# Left CBs - OFF
	pushSeqCmd(dt, 'ELEC_INTERFACE.CB_LEFT_RADIOCOMPASS_HF', 0)
	pushSeqCmd(dt, 'ELEC_INTERFACE.CB_LEFT_AUTOPILOT_ALARM', 0)
	pushSeqCmd(dt, 'ELEC_INTERFACE.CB_LEFT_AIRSPEED_SENSOR', 0)
	pushSeqCmd(dt, 'ELEC_INTERFACE.CB_FRAME_LEFT', 0)
	pushSeqCmd(dt, 'ELEC_INTERFACE.CB_LEFT_STARTUP_BLOCK', 0)
	pushSeqCmd(dt, 'ELEC_INTERFACE.CB_LEFT_BEACON', 0)
	pushSeqCmd(dt, 'ELEC_INTERFACE.CB_LEFT_BOMB_EXPLOSION', 0)
	pushSeqCmd(dt, 'ELEC_INTERFACE.CB_LEFT_EXT_CARGO_EMERGENCY_DROP', 0)
	pushSeqCmd(dt, 'ELEC_INTERFACE.CB_LEFT_PUMP_TANK_5', 0)
	pushSeqCmd(dt, 'ELEC_INTERFACE.CB_LEFT_BOMB_EMERGENCY_DETACH', 0)
	pushSeqCmd(dt, 'ELEC_INTERFACE.CB_LEFT_FIRE_1_AUTO', 0)
	pushSeqCmd(dt, 'ELEC_INTERFACE.CB_LEFT_FIRE_1_MANUAL', 0)
	pushSeqCmd(dt, 'ELEC_INTERFACE.CB_LEFT_FIRE_ALARM', 0)
	pushSeqCmd(dt, 'ELEC_INTERFACE.CB_LEFT_RECORDER_PARAMS', 0)
	pushSeqCmd(dt, 'ELEC_INTERFACE.CB_LEFT_PUMP_TANK_1', 0)
	pushSeqCmd(dt, 'ELEC_INTERFACE.CB_LEFT_GEAR_EXTENT_HANDLE', 0)
	pushSeqCmd(dt, 'ELEC_INTERFACE.CB_LEFT_GEAR_ALARM', 0)
	pushSeqCmd(dt, 'ELEC_INTERFACE.CB_LEFT_STARTUP_IGNITION', 0)
	pushSeqCmd(dt, 'ELEC_INTERFACE.CB_LEFT_PT125Ts', 0)
	pushSeqCmd(dt, 'ELEC_INTERFACE.CB_LEFT_HEADLIGHT_CONTROL', 0)
	pushSeqCmd(dt, 'ELEC_INTERFACE.CB_LEFT_PILOTING_DEVICE', 0)
	pushSeqCmd(dt, 'ELEC_INTERFACE.CB_LEFT_HOMING_MISSILE_POWER', 0)
	pushSeqCmd(dt, 'ELEC_INTERFACE.CB_LEFT_UNGUIDED_ROCKETS', 0)
	pushSeqCmd(dt, 'ELEC_INTERFACE.CB_LEFT_VALVE_TANK_1', 0)
	pushSeqCmd(dt, 'ELEC_INTERFACE.CB_LEFT_VALVE_FIRE_LEFT', 0)
	pushSeqCmd(dt, 'ELEC_INTERFACE.CB_LEFT_VALVE_SEPARATION', 0)
	pushSeqCmd(dt, 'ELEC_INTERFACE.CB_LEFT_SPEECH_INFORMER', 0)
	pushSeqCmd(dt, 'ELEC_INTERFACE.CB_LEFT_GLASS_SPRINKLER', 0)
	pushSeqCmd(dt, 'ELEC_INTERFACE.CB_LEFT_GLASS_WIPER_OP', 0)
	pushSeqCmd(dt, 'ELEC_INTERFACE.CB_LEFT_GLASS_WIPER_PILOT', 0)

	# Right CBs - OFF
	pushSeqCmd(dt, 'ELEC_INTERFACE.CB_RIGHT_ANTIICE_CONTROL', 0)
	pushSeqCmd(dt, 'ELEC_INTERFACE.CB_RIGHT_ANTIICE_ALARM', 0)
	pushSeqCmd(dt, 'ELEC_INTERFACE.CB_RIGHT_CONDITIONER_CONTROL', 0)
	pushSeqCmd(dt, 'ELEC_INTERFACE.CB_FRAME_RIGHT', 0)
	pushSeqCmd(dt, 'ELEC_INTERFACE.CB_RIGHT_ARMAMENT_CONTROL', 0)
	pushSeqCmd(dt, 'ELEC_INTERFACE.CB_RIGHT_BOMB_COMBAT_DROP', 0)
	pushSeqCmd(dt, 'ELEC_INTERFACE.CB_RIGHT_ARMAMENT_CAMERA_SHUTTER', 0)
	pushSeqCmd(dt, 'ELEC_INTERFACE.CB_RIGHT_ARMAMENT_CANNON', 0)
	pushSeqCmd(dt, 'ELEC_INTERFACE.CB_RIGHT_CONNECTION_DISTRIBUTION_DEVICE', 0)
	pushSeqCmd(dt, 'ELEC_INTERFACE.CB_RIGHT_CONTROL_CLUTCH', 0)
	pushSeqCmd(dt, 'ELEC_INTERFACE.CB_RIGHT_CONTROL_FORCE_MECHANISM', 0)
	pushSeqCmd(dt, 'ELEC_INTERFACE.CB_RIGHT_LAUNCHER_DETACH', 0)
	pushSeqCmd(dt, 'ELEC_INTERFACE.CB_RIGHT_DUAS_V_HEATING', 0)
	pushSeqCmd(dt, 'ELEC_INTERFACE.CB_RIGHT_FIRE_2_AUTO', 0)
	pushSeqCmd(dt, 'ELEC_INTERFACE.CB_RIGHT_FIRE_2_MANUAL', 0)
	pushSeqCmd(dt, 'ELEC_INTERFACE.CB_RIGHT_FUEL_METER', 0)
	pushSeqCmd(dt, 'ELEC_INTERFACE.CB_RIGHT_PUMP_TANK_2', 0)
	pushSeqCmd(dt, 'ELEC_INTERFACE.CB_RIGHT_PUMP_TANK_4', 0)
	pushSeqCmd(dt, 'ELEC_INTERFACE.CB_RIGHT_VALVE_FIRE_RIGHT', 0)
	pushSeqCmd(dt, 'ELEC_INTERFACE.CB_RIGHT_VALVE_TANK_2', 0)
	pushSeqCmd(dt, 'ELEC_INTERFACE.CB_RIGHT_GEAR_EXTENT_HANDLE_BACKUP', 0)
	pushSeqCmd(dt, 'ELEC_INTERFACE.CB_RIGHT_EMERGENCY_DOOR_DETACH_OP', 0)
	pushSeqCmd(dt, 'ELEC_INTERFACE.CB_RIGHT_EMERGENCY_DOOR_DETACH_PILOT', 0)
	pushSeqCmd(dt, 'ELEC_INTERFACE.CB_RIGHT_PILOT_SEAT_MECHANISM', 0)
	pushSeqCmd(dt, 'ELEC_INTERFACE.CB_RIGHT_PILOT_AIM', 0)
	pushSeqCmd(dt, 'ELEC_INTERFACE.CB_RIGHT_ROTOR_RPM_ADJUST', 0)
	pushSeqCmd(dt, 'ELEC_INTERFACE.CB_RIGHT_ARMAMENT_SIGNAL', 0)
	pushSeqCmd(dt, 'ELEC_INTERFACE.CB_RIGHT_EXT_STORES_LOCK_RELEASE', 0)
	pushSeqCmd(dt, 'ELEC_INTERFACE.CB_RIGHT_EXT_STORES_TACTICAL_DROP', 0)
	pushSeqCmd(dt, 'ELEC_INTERFACE.CB_RIGHT_ENGINE_TEMP_ADJUST_LEFT', 0)
	pushSeqCmd(dt, 'ELEC_INTERFACE.CB_RIGHT_ENGINE_TEMP_ADJUST_RIGHT', 0)

	# Generators and other electrics
	# Left Generator switch - OFF
	pushSeqCmd(dt, 'ELEC_INTERFACE.ACGeneratorLeft', 0)
	# Right Generator switch - OFF
	pushSeqCmd(dt, 'ELEC_INTERFACE.ACGeneratorRight', 0)
	# 115V Transformer switch - AUTO
	pushSeqCmd(dt, 'ELEC_INTERFACE.Transformer115vMainBackup', 1)
	# 36V Transformer switch - AUTO
	pushSeqCmd(dt, 'ELEC_INTERFACE.Transformer36vMainBackup', 1)
	# Left Rectifier switch - OFF
	pushSeqCmd(dt, 'ELEC_INTERFACE.RectifierLeft', 0)
	# Right Rectifier switch - OFF
	pushSeqCmd(dt, 'ELEC_INTERFACE.RectifierRight', 0)
	# AC Voltmeter knob - OFF
	pushSeqCmd(dt, 'ELEC_INTERFACE.ACGangSwitcher', 0)

	# Electric Power
	# Right Battery - OFF
	pushSeqCmd(dt, 'ELEC_INTERFACE.BatteryRight', 0)
	# Left Battery - OFF
	pushSeqCmd(dt, 'ELEC_INTERFACE.BatteryLeft', 0)
	# DC Voltmeter knob - OFF
	pushSeqCmd(dt, 'ELEC_INTERFACE.DCGangSwitcher', 0)

	return seq
