# Return a Dictionary of script data.  The 'scripts' key is a list of scripts that users will be selecting from.  Each script has an associated 'function', which is the name of the function in this file that will be called to generate the command sequence, and a dictionary of 'vars' that the user will be prompted to choose from before running the script, and will be passed into the sequence generating function.
def getScriptData():
	return {
		'moduleName': 'F-5E-3',
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

	#print(seq)
	return seq


def ColdStart(config, vars, helper, *args, **kwargs):
	seq = []
	dt = 0.2

	pushSeqCmd = helper.makePushSeqCmd(seq)


	pushSeqCmd(0, '', '', "Running Cold Start sequence")

	pushSeqCmd(dt, 'CPT_MECH.CanopyLever', 1)

	# Oxygen
	pushSeqCmd(dt, 'OXYGEN_INTERFACE.SupplyLever', 1)
	pushSeqCmd(dt, 'OXYGEN_INTERFACE.DiluterLever', 0) # 0 = NORMAL, 1 = 100% OXYGEN

	pushSeqCmd(dt, 'ELEC_INTERFACE.BatterySw', 1)

	pushSeqCmd(dt, 'INTLIGHTS_SYSTEM.FltInstr_knob', 1.0)
	pushSeqCmd(dt, 'INTLIGHTS_SYSTEM.EngInstr_knob', 1.0)
	pushSeqCmd(dt, 'INTLIGHTS_SYSTEM.Console_knob', 1.0)
	pushSeqCmd(dt, 'INTLIGHTS_SYSTEM.ArmtPanel_knob', 1.0)

	pushSeqCmd(dt, 'UHF_RADIO.PTR-ANARC164-FUNCTION-311', 1) # 0 = OFF, 1 = MAIN, 2 = BOTH, 3 = ADF

	pushSeqCmd(dt, 'ELEC_INTERFACE.LeftGenResetSw', 2)
	pushSeqCmd(dt, 'ELEC_INTERFACE.RightGenResetSw', 2)

	pushSeqCmd(dt, 'FUEL_INTERFACE.FuelBoostPump_Left', 1)
	pushSeqCmd(dt, 'FUEL_INTERFACE.FuelBoostPump_Right', 1)

	# Start engines

	# Ground air supply on
	pushSeqCmd(dt, 'scriptSimCommand', 'ICommandMenuItem12') # Reset comms menu to top level
	pushSeqCmd(dt, 'scriptSimCommand', 'ICommandMenuItem8') # F8 Ground crew
	pushSeqCmd(dt, 'scriptSimCommand', 'ICommandMenuItem5') # F5 Ground air supply
	pushSeqCmd(dt, 'scriptSimCommand', 'ICommandMenuItem1') # F1 Connect
	pushSeqCmd(8, '', '', "Ground air supply is on")

	# Left engine
	# Apply ground air supply
	pushSeqCmd(dt, 'scriptSimCommand', 'ICommandMenuItem12') # Reset comms menu to top level
	pushSeqCmd(dt, 'scriptSimCommand', 'ICommandMenuItem8') # F8 Ground crew
	pushSeqCmd(dt, 'scriptSimCommand', 'ICommandMenuItem5') # F5 Ground air supply
	pushSeqCmd(dt, 'scriptSimCommand', 'ICommandMenuItem3') # F3 Apply
	pushSeqCmd(8, '', '', 'Left engine at 10% RPM')
	pushSeqCmd(dt, 'ENGINE_INTERFACE.EngineStartLeft', 1) # Press
	pushSeqCmd(dt, 'ENGINE_INTERFACE.EngineStartLeft', 0) # Release
	pushSeqCmd(dt, 'scriptSimCommand', 'iCommandLeftEngineStart') # Left throttle IDLE
	pushSeqCmd(15, '', '', 'Left engine at 50% (idle)')

	# Right engine
	# Ground air supply on
	pushSeqCmd(dt, 'scriptSimCommand', 'ICommandMenuItem12') # Reset comms menu to top level
	pushSeqCmd(dt, 'scriptSimCommand', 'ICommandMenuItem8') # F8 Ground crew
	pushSeqCmd(dt, 'scriptSimCommand', 'ICommandMenuItem5') # F5 Ground air supply
	pushSeqCmd(dt, 'scriptSimCommand', 'ICommandMenuItem3') # F3 Apply
	pushSeqCmd(8, '', '', 'Right engine at 10% RPM')
	pushSeqCmd(dt, 'ENGINE_INTERFACE.EngineStartRight', 1) # Press
	pushSeqCmd(dt, 'ENGINE_INTERFACE.EngineStartRight', 0) # Release
	pushSeqCmd(dt, 'scriptSimCommand', 'iCommandRightEngineStart') # Right throttle IDLE
	pushSeqCmd(15, '', '', 'Right engine at 50% (idle)')

	# Ground air supply off
	pushSeqCmd(dt, 'scriptSimCommand', 'ICommandMenuItem12') # Reset comms menu to top level
	pushSeqCmd(dt, 'scriptSimCommand', 'ICommandMenuItem8') # F8 Ground crew
	pushSeqCmd(dt, 'scriptSimCommand', 'ICommandMenuItem5') # F5 Ground air supply
	pushSeqCmd(dt, 'scriptSimCommand', 'ICommandMenuItem2') # F2 Disconnect
	pushSeqCmd(8, '', '', 'Ground air supply is off')

	pushSeqCmd(dt, 'FUEL_INTERFACE.FuelAutoLeft', 0) # = 0 LEFT LOW, 1 = NEUTRAL, 2 = RIGHT LOW

	pushSeqCmd(dt, 'AN_ASG31.ModeSelector', 1) # 0 = OFF, 1 = MSL, 2 = A/A1 GUNS, 3 = A/A2 GUNS, 4 = MAN

	pushSeqCmd(dt, 'AN_APQ159.ModeSelector', 1) # 0 = OFF, 1 = STBY, 2 = OPER, 3 = TEST

	pushSeqCmd(dt, 'RWR_IC.Power', 1)

	# Retract speed brake
	pushSeqCmd(dt, 'CONTROL_INTERFACE.SpdBrk', 2) # 0 = Out, 1 = Stop, 2 = In
	pushSeqCmd(2, 'CONTROL_INTERFACE.SpdBrk', 1) # 0 = Out, 1 = Stop, 2 = In

	pushSeqCmd(dt, 'CONTROL_INTERFACE.FlapSwitch', 0) # 0 = AUTO, 2 = FIXED, 3 = UP
	pushSeqCmd(dt, 'CONTROL_INTERFACE.PitchDamper', 1)
	pushSeqCmd(dt, 'CONTROL_INTERFACE.YawDamper', 1)

	# BACKUP ATTITUDE INDICATOR - UNCAGE
	pushSeqCmd(dt, 'SAI.CMD_SAI_PITCH_ZERO_SHIFT', -0.125) # Decrement one step to the zero position.
	pushSeqCmd(dt, 'SAI.CMD_SAI_CAGE', 0) # Push in the cage knob.

	# SPEED INDEX - 325KTS (CORNER SPEED
	# Set index to 0 first (-29.0 resets it to 0 from max).
	pushSeqCmd(dt, 'IAS_MACH_INDICATOR.PTR-LVR-AIRSPD-SET-180', -29.0)
	# Then set to desired speed (16.6 units)
	pushSeqCmd(dt, 'IAS_MACH_INDICATOR.PTR-LVR-AIRSPD-SET-180', 16.6)

	pushSeqCmd(dt, 'CPT_MECH.CanopyLever', 0)

	pushSeqCmd(dt, 'INTLIGHTS_SYSTEM.MasterReset', 1) # Press
	pushSeqCmd(dt, 'INTLIGHTS_SYSTEM.MasterReset', 0) # Release

	pushSeqCmd(dt, 'CMDS.ChaffMode', 1) # 0 = OFF, 1 = SINGLE, 2 = PRGM, 3 = MULT
	pushSeqCmd(dt, 'CMDS.FlareMode', 1) # 0 = OFF, 1 = SINGLE, 2 = PRGM, 3 = MULT

	# IFF ... ON
	pushSeqCmd(dt, 'IFF.PTR-IFFCP-ON-OUT-208', 1) # 0 = OUT, 1 = ON

	pushSeqCmd(dt, 'ELEC_INTERFACE.PitotHeater', 1)

	pushSeqCmd(dt, 'JETTISON_SYSTEM.EmerAllJettCap', 1)

	pushSeqCmd(dt, 'scriptSpeech', "Manual steps remaining: Lights, Radios, If carrying drop tanks set Fuel EXTERNAL PYLON switches, Set pitch trim for takeoff, see kneeboard.")

	return seq


def HotStart(config, vars, helper, *args, **kwargs):
	seq = []
	dt = 0.2

	pushSeqCmd = helper.makePushSeqCmd(seq)


	pushSeqCmd(0, '', '', "Running Hot Start sequence")

	pushSeqCmd(dt, 'INTLIGHTS_SYSTEM.FltInstr_knob', 1.0)
	pushSeqCmd(dt, 'INTLIGHTS_SYSTEM.EngInstr_knob', 1.0)
	pushSeqCmd(dt, 'INTLIGHTS_SYSTEM.Console_knob', 1.0)
	pushSeqCmd(dt, 'INTLIGHTS_SYSTEM.ArmtPanel_knob', 1.0)

	pushSeqCmd(dt, 'FUEL_INTERFACE.FuelAutoLeft', 0) # = 0 LEFT LOW, 1 = NEUTRAL, 2 = RIGHT LOW

	pushSeqCmd(dt, 'RWR_IC.Power', 1)

	# SPEED INDEX - 325KTS (CORNER SPEED
	# Set index to 0 first (-29.0 resets it to 0 from max).
	pushSeqCmd(dt, 'IAS_MACH_INDICATOR.PTR-LVR-AIRSPD-SET-180', -29.0)
	# Then set to desired speed (16.6 units)
	pushSeqCmd(dt, 'IAS_MACH_INDICATOR.PTR-LVR-AIRSPD-SET-180', 16.6)

	pushSeqCmd(dt, 'CMDS.ChaffMode', 1) # 0 = OFF, 1 = SINGLE, 2 = PRGM, 3 = MULT
	pushSeqCmd(dt, 'CMDS.FlareMode', 1) # 0 = OFF, 1 = SINGLE, 2 = PRGM, 3 = MULT

	# IFF ... ON
	pushSeqCmd(dt, 'IFF.PTR-IFFCP-ON-OUT-208', 1) # 0 = OUT, 1 = ON

	pushSeqCmd(dt, 'JETTISON_SYSTEM.EmerAllJettCap', 1)

	pushSeqCmd(dt, 'scriptSpeech', "Manual steps remaining: Lights, Radios, If carrying drop tanks set Fuel EXTERNAL PYLON switches, Set pitch trim for takeoff, see kneeboard.")

	return seq
