# Return a Dictionary of script data.  The 'scripts' key is a list of scripts that users will be selecting from.  Each script has an associated 'function', which is the name of the function in this file that will be called to generate the command sequence, and a dictionary of 'vars' that the user will be prompted to choose from before running the script, and will be passed into the sequence generating function.
def getScriptData():
	return {
		'moduleName': 'F-86F Sabre',
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
				'name': 'Air Start',
				'function': 'AirStart',
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
	return ''


def Test(config, vars, helper, *args, **kwargs):
	seq = []
	dt = 0.3

	pushSeqCmd = helper.makePushSeqCmd(seq)

	# Test code here...
	pushSeqCmd(0, '', '', "Running Test sequence")

	pushSeqCmd(dt, 'scriptSimCommand', 'ICommandMenuItem12') # Reset comms menu to top level
	pushSeqCmd(dt, 'scriptSimCommand', 'ICommandMenuItem8') # F8 Ground crew
	pushSeqCmd(dt, 'scriptSimCommand', 'ICommandMenuItem2') # F2 Ground electric power
	pushSeqCmd(dt, 'scriptSimCommand', 'ICommandMenuItem1') # F1 On

	#pushSeqCmd(dt, 'scriptSpeech', 'Stay in cockpit until told it\'s OK to leave.')
	#pushSeqCmd(dt, 'scriptSpeech', 'OK to leave cockpit.')
	#pushSeqCmd(dt, 'scriptSpeech', 'Don\'t use comms menu until told it\'s OK.')
	#pushSeqCmd(dt, 'scriptSpeech', 'OK to use comms menu.')

	#print(seq)
	return seq


def ColdStart(config, vars, helper, *args, **kwargs):
	seq = []
	dt = 0.2

	pushSeqCmd = helper.makePushSeqCmd(seq)


	pushSeqCmd(0, '', '', "Running Cold Start sequence")

	# Ground electric power ... ON
	pushSeqCmd(dt, 'scriptSimCommand', 'ICommandMenuItem12') # Reset comms menu to top level
	pushSeqCmd(dt, 'scriptSimCommand', 'ICommandMenuItem8') # F8 Ground crew
	pushSeqCmd(dt, 'scriptSimCommand', 'ICommandMenuItem2') # F2 Ground electric power
	pushSeqCmd(dt, 'scriptSimCommand', 'ICommandMenuItem1') # F1 On
	pushSeqCmd(11, '', '', "Ground electric power is on")

	# Flight control switch ... ALTERNATE ON
	pushSeqCmd(dt, 'HYDRO_INTERFACE.F86_CockpitDeviceCommand_FlightControl', 2) # 0 = RESET (spring loaded to center), 1 = NORMAL, 2 = ALTERNATE ON

	# Engine Master switch ... ON
	pushSeqCmd(dt, 'ELEC_INTERFACE.F86_CockpitDeviceCommand_EngineMasterSw', 1)

	# Battery switch ... STARTER 2-3 seconds, then BATTERY
	pushSeqCmd(dt, 'ELEC_INTERFACE.F86_CockpitDeviceCommand_BatteryStarterSw', 0) # 0 = STARTER, 1 = OFF, 2 = BATTERY
	pushSeqCmd(3, 'ELEC_INTERFACE.F86_CockpitDeviceCommand_BatteryStarterSw', 1) # 0 = STARTER, 1 = OFF, 2 = BATTERY
	pushSeqCmd(dt, 'ELEC_INTERFACE.F86_CockpitDeviceCommand_BatteryStarterSw', 2) # 0 = STARTER, 1 = OFF, 2 = BATTERY

	# Wait for RPMs to get over 3%.
	pushSeqCmd(dt, 'scriptCockpitState', control='F-86F Sabre/arg.Tachometer', value=0.03, condition='>', duration=3) # Safer to wait 3 seconds after reaching 3%, the value seems to be a bit greater than the number shown by the needle.

	# When RPMs are 3% or more, move throttle to first notch (ignition)
	pushSeqCmd(dt, 'CONTROL_INTERFACE.F86_CockpitDeviceCommand_EngineStart', 1) # Throttle forward one notch

	# Wait for RPMs to get over 6%.
	pushSeqCmd(dt, 'scriptCockpitState', control='F-86F Sabre/arg.Tachometer', value=0.06, condition='>', duration=3) # Safer to wait 3 seconds after reaching 6%, the value seems to be a bit greater than the number shown by the needle.

	# When RPMs are 6% or more, move throttle to second notch (idle)
	pushSeqCmd(dt, 'CONTROL_INTERFACE.F86_CockpitDeviceCommand_EngineStart', 1) # Throttle forward one notch

	# Wait for RPMs to get over 25%
	pushSeqCmd(dt, 'scriptCockpitState', control='F-86F Sabre/arg.Tachometer', value=0.25, condition='>', duration=3) # Safer to wait 3 seconds after reaching 25%.

	# When RPMs are 25% or more, Flight control switch ... RESET for 2-3 seconds, then NORMAL
	pushSeqCmd(dt, 'HYDRO_INTERFACE.F86_CockpitDeviceCommand_FlightControl', 0) # 0 = RESET (spring loaded to center), 1 = NORMAL, 2 = ALTERNATE ON
	pushSeqCmd(3, 'HYDRO_INTERFACE.F86_CockpitDeviceCommand_FlightControl', 1) # 0 = RESET (spring loaded to center), 1 = NORMAL, 2 = ALTERNATE ON

	# Wait for RPMs to get to idle (34%)
	pushSeqCmd(dt, 'scriptCockpitState', control='F-86F Sabre/arg.Tachometer', value=0.30, condition='>=', duration=3) # Safer to wait 3 seconds after reaching 30%.

	# Retract speed brakes
	pushSeqCmd(dt, 'HYDRO_INTERFACE.F86_CockpitDeviceCommand_AirBrakesHandle', 2) # 0 = Out, 1 = Hold, 2 = In
	pushSeqCmd(6, 'HYDRO_INTERFACE.F86_CockpitDeviceCommand_AirBrakesHandle', 1) # 0 = Out, 1 = Hold, 2 = In

	# Oxygen Regulator Supply lever ... ON full
	pushSeqCmd(dt, 'OXYGEN_INTERFACE.F86_CockpitDeviceCommand_OxygenSupplyLever', 0) # 0 = ON, int16 = OFF)

	# Ground electric power ... OFF
	pushSeqCmd(dt, 'scriptSimCommand', 'ICommandMenuItem12') # Reset comms menu to top level
	pushSeqCmd(dt, 'scriptSimCommand', 'ICommandMenuItem8') # F8 Ground crew
	pushSeqCmd(dt, 'scriptSimCommand', 'ICommandMenuItem2') # F2 Ground electric power
	pushSeqCmd(dt, 'scriptSimCommand', 'ICommandMenuItem2') # F2 Off
	pushSeqCmd(11, '', '', "Ground electric power is off")

	# Canopy ... Close
	pushSeqCmd(dt, 'COCKPIT_MECHANICS.F86_CockpitDeviceCommand_CockpitCanopyControlSw', 1) # 0 = OPEN, 1 = OFF, 2 = CLOSE
	pushSeqCmd(dt, 'COCKPIT_MECHANICS.F86_CockpitDeviceCommand_CockpitCanopyControlSw', 2) # 0 = OPEN, 1 = OFF, 2 = CLOSE
	# Wait for canopy to close
	pushSeqCmd(dt, 'scriptCockpitState', control='F-86F Sabre/arg.CockpitCanopy', value=0, condition='=')
	pushSeqCmd(dt, 'COCKPIT_MECHANICS.F86_CockpitDeviceCommand_CockpitCanopyControlSw', 1) # 0 = OPEN, 1 = OFF, 2 = CLOSE

	# Radio ... ON
	pushSeqCmd(dt, 'AN_ARC_27_COMMAND_SET.F86_CockpitDeviceCommand_ARC27_Mode', 1) # 0 = OFF, 1 = T/R, 2 = T/R + G, 3 = REC/ADF

	# IFF knob ... NORM
	pushSeqCmd(dt, 'AN_APX6_IFF.F86_CockpitDeviceCommand_APX6_Mode', 3) # 0 = OFF, 1 = STDBY, 2 = LOW, 3 = NORM, 4 = EMERGENCY

	# IFF MODE 2 switch ... ON
	pushSeqCmd(dt, 'AN_APX6_IFF.F86_CockpitDeviceCommand_APX6_Mode2Sw', 2) # 0 = I/P, 1 = OUT, 2 = ON

	# IFF MODE 3 switch ... ON
	pushSeqCmd(dt, 'AN_APX6_IFF.F86_CockpitDeviceCommand_APX6_Mode3Sw', 1) # 0 = OUT, 1 = ON

	# PITOT HEAT switch ... ON
	pushSeqCmd(dt, 'AIR_INTERFACE.F86_CockpitDeviceCommand_PitotHeater_Sw', 1) # 0 = OFF, 1 = ON

	# Guns ... ALL GUNS
	pushSeqCmd(dt, 'WEAPON_SYSTEM.Guns_Selector', 4) # 0 = OFF, 1 = UPPER GUNS, 2 = MID GUNS, 3 = LOWER GUNS, 4 = ALL GUNS

	# Gun heater switch ... ON
	pushSeqCmd(dt, 'WEAPON_SYSTEM.Gun_Heater_Switch', 2) # 0 = Reset? (spring loaded to center), 1 = OFF, 2 = ON

	# Gun/Missile selector switch ... GUNS
	pushSeqCmd(dt, 'WEAPON_SYSTEM.MISSILE_GUNS_RADAR-Selector', 1) # 0 = MISSILE, 1 = GUNS, 2 = SIGHT CAMERA & RADAR, 3 = OFF

	# Gun sight wingspan lever ... 30 ft (all the way left)
	pushSeqCmd(dt, 'A4_GUNSIGHT.Wing_span_adjustment_knob', 0) # (int values 1-47) 0 = 30 ft, 47 = 120 ft

	pushSeqCmd(dt, 'scriptSpeech', "Manual steps remaining: Set lights, tune radios, If carrying drop tanks, set Fuel Tank Selector Knob.  Set takeoff trim using takeoff trim position indicator light.")

	return seq


def HotStart(config, vars, helper, *args, **kwargs):
	seq = []
	dt = 0.2

	pushSeqCmd = helper.makePushSeqCmd(seq)


	pushSeqCmd(0, '', '', "Running Hot Start sequence")

	# IFF MODE 2 switch ... ON
	pushSeqCmd(dt, 'AN_APX6_IFF.F86_CockpitDeviceCommand_APX6_Mode2Sw', 2) # 0 = I/P, 1 = OUT, 2 = ON

	# IFF MODE 3 switch ... ON
	pushSeqCmd(dt, 'AN_APX6_IFF.F86_CockpitDeviceCommand_APX6_Mode3Sw', 1) # 0 = OUT, 1 = ON

	# Guns ... ALL GUNS
	pushSeqCmd(dt, 'WEAPON_SYSTEM.Guns_Selector', 4) # 0 = OFF, 1 = UPPER GUNS, 2 = MID GUNS, 3 = LOWER GUNS, 4 = ALL GUNS

	# Gun heater switch ... ON
	pushSeqCmd(dt, 'WEAPON_SYSTEM.Gun_Heater_Switch', 2) # 0 = Reset? (spring loaded to center), 1 = OFF, 2 = ON

	# Gun sight wingspan lever ... 30 ft (all the way left)
	pushSeqCmd(dt, 'A4_GUNSIGHT.Wing_span_adjustment_knob', 0) # (int values 1-47) 0 = 30 ft, 47 = 120 ft

	pushSeqCmd(dt, 'scriptSpeech', "Manual steps remaining: Set lights, tune radios, If carrying drop tanks, set Fuel Tank Selector Knob.  Set takeoff trim using takeoff trim position indicator light.")

	return seq


def AirStart(config, vars, helper, *args, **kwargs):
	seq = []
	dt = 0.2

	pushSeqCmd = helper.makePushSeqCmd(seq)


	pushSeqCmd(0, '', '', "Running Air Start sequence")

	# IFF MODE 2 switch ... ON
	pushSeqCmd(dt, 'AN_APX6_IFF.F86_CockpitDeviceCommand_APX6_Mode2Sw', 2) # 0 = I/P, 1 = OUT, 2 = ON

	# IFF MODE 3 switch ... ON
	pushSeqCmd(dt, 'AN_APX6_IFF.F86_CockpitDeviceCommand_APX6_Mode3Sw', 1) # 0 = OUT, 1 = ON

	# Gun heater switch ... ON
	pushSeqCmd(dt, 'WEAPON_SYSTEM.Gun_Heater_Switch', 2) # 0 = Reset? (spring loaded to center), 1 = OFF, 2 = ON

	# Gun sight wingspan lever ... 30 ft (all the way left)
	pushSeqCmd(dt, 'A4_GUNSIGHT.Wing_span_adjustment_knob', 0) # (int values 1-47) 0 = 30 ft, 47 = 120 ft

	pushSeqCmd(dt, 'scriptSpeech', "Manual steps remaining: Set lights, tune radios, If carrying drop tanks, set Fuel Tank Selector Knob.")

	return seq


def Shutdown(config, vars, helper, *args, **kwargs):
	seq = []
	dt = 0.2

	pushSeqCmd = helper.makePushSeqCmd(seq)


	pushSeqCmd(0, '', '', "Running Shutdown sequence")

	# Gun/Missile selector switch ... OFF
	pushSeqCmd(dt, 'WEAPON_SYSTEM.MISSILE_GUNS_RADAR-Selector', 3) # 0 = MISSILE, 1 = GUNS, 2 = SIGHT CAMERA & RADAR, 3 = OFF

	# Gun heater switch ... OFF
	pushSeqCmd(dt, 'WEAPON_SYSTEM.Gun_Heater_Switch', 1) # 0 = Reset? (spring loaded to center), 1 = OFF, 2 = ON

	# Guns ... OFF
	pushSeqCmd(dt, 'WEAPON_SYSTEM.Guns_Selector', 0) # 0 = OFF, 1 = UPPER GUNS, 2 = MID GUNS, 3 = LOWER GUNS, 4 = ALL GUNS

	# PITOT HEAT switch ... OFF
	pushSeqCmd(dt, 'AIR_INTERFACE.F86_CockpitDeviceCommand_PitotHeater_Sw', 0) # 0 = OFF, 1 = ON

	# IFF knob ... OFF
	pushSeqCmd(dt, 'AN_APX6_IFF.F86_CockpitDeviceCommand_APX6_Mode', 0) # 0 = OFF, 1 = STDBY, 2 = LOW, 3 = NORM, 4 = EMERGENCY
	# 0 = OFF, 1 = STDBY, 2 = LOW, 3 = NORM, 4 = EMERGENCY

	# IFF MODE 2 switch ... OFF
	pushSeqCmd(dt, 'AN_APX6_IFF.F86_CockpitDeviceCommand_APX6_Mode2Sw', 1) # 0 = I/P, 1 = OUT, 2 = ON

	# IFF MODE 3 switch ... OFF
	pushSeqCmd(dt, 'AN_APX6_IFF.F86_CockpitDeviceCommand_APX6_Mode3Sw', 0) # 0 = OUT, 1 = ON

	# Radio ... OFF
	pushSeqCmd(dt, 'AN_ARC_27_COMMAND_SET.F86_CockpitDeviceCommand_ARC27_Mode', 0) # 0 = OFF, 1 = T/R, 2 = T/R + G, 3 = REC/ADF

	# Canopy ... Open
	pushSeqCmd(dt, 'COCKPIT_MECHANICS.F86_CockpitDeviceCommand_CockpitCanopyControlSw', 0) # 0 = OPEN, 1 = OFF, 2 = CLOSE
	# Wait for canopy to open.
	pushSeqCmd(dt, 'scriptCockpitState', control='F-86F Sabre/arg.CockpitCanopy', value=0.9, condition='>=')
	pushSeqCmd(dt, 'COCKPIT_MECHANICS.F86_CockpitDeviceCommand_CockpitCanopyControlSw', 1) # 0 = OPEN, 1 = OFF, 2 = CLOSE

	# Oxygen Regulator Supply lever ... OFF
	pushSeqCmd(dt, 'OXYGEN_INTERFACE.F86_CockpitDeviceCommand_OxygenSupplyLever', 1.0) # 0 = ON, int16 = OFF)

	# Throttle ... OFF
	pushSeqCmd(dt, 'CONTROL_INTERFACE.F86_CockpitDeviceCommand_EngineStop', 1)

	# Engine Master switch ... OFF
	pushSeqCmd(dt, 'ELEC_INTERFACE.F86_CockpitDeviceCommand_EngineMasterSw', 0)

	# Battery switch ... OFF
	pushSeqCmd(dt, 'ELEC_INTERFACE.F86_CockpitDeviceCommand_BatteryStarterSw', 1) # 0 = STARTER, 1 = OFF, 2 = BATTERY

	return seq
