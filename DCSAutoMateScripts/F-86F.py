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

	#print(seq)
	return seq


def ColdStart(config, vars):
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

	# Ground electric power ... ON
	pushSeqCmd(dt, 'scriptKeyboard', '\\')
	pushSeqCmd(dt, 'scriptKeyboard', 'F8') # Ground crew
	pushSeqCmd(dt, 'scriptKeyboard', 'F2') # Ground electric power
	pushSeqCmd(dt, 'scriptKeyboard', 'F1') # On
	pushSeqCmd(11, '', '', "Ground electric power is on")

	# Flight control switch ... ALTERNATE ON
	pushSeqCmd(dt, 'FL_CTRL_SWITCH', 2) # 0 = RESET (spring loaded to center), 1 = NORMAL, 2 = ALTERNATE ON

	# Engine Master switch ... ON
	pushSeqCmd(dt, 'ENG_MASTER', 1)

	# Battery switch ... STARTER 2-3 seconds, then BATTERY
	pushSeqCmd(dt, 'BAT_START', 0) # 0 = STARTER, 1 = OFF, 2 = BATTERY
	pushSeqCmd(3, 'BAT_START', 1) # 0 = STARTER, 1 = OFF, 2 = BATTERY
	pushSeqCmd(dt, 'BAT_START', 2) # 0 = STARTER, 1 = OFF, 2 = BATTERY

	# Wait for RPMs to get over 3%.
	pushSeqCmd(dt, 'scriptCockpitState', control='F-86F Sabre/TACHOMETER_VALUE', value=3, condition='>')

	# When RPMs are 3% or more, move throttle to first notch (ignition)
	pushSeqCmd(dt, 'scriptKeyboard', 'home')

	# Wait for RPMs to get over 6%.
	pushSeqCmd(dt, 'scriptCockpitState', control='F-86F Sabre/TACHOMETER_VALUE', value=6, condition='>')

	# When RPMs are 6% or more, move throttle to second notch (idle)
	pushSeqCmd(dt, 'scriptKeyboard', 'home')

	# Wait for RPMs to get over 25%
	pushSeqCmd(dt, 'scriptCockpitState', control='F-86F Sabre/TACHOMETER_VALUE', value=25, condition='>')

	# When RPMs are 25% or more, Flight control switch ... RESET for 2-3 seconds, then NORMAL
	pushSeqCmd(dt, 'FL_CTRL_SWITCH', 0) # 0 = RESET (spring loaded to center), 1 = NORMAL, 2 = ALTERNATE ON
	pushSeqCmd(3, 'FL_CTRL_SWITCH', 1) # 0 = RESET (spring loaded to center), 1 = NORMAL, 2 = ALTERNATE ON

	# Wait for RPMs to get to idle (34%)
	pushSeqCmd(dt, 'scriptCockpitState', control='F-86F Sabre/TACHOMETER_VALUE', value=33, condition='>=')

	# Retract speed brakes
	pushSeqCmd(dt, 'SPD_BRAKE_SW', 2) # 0 = Out, 1 = Hold, 2 = In
	pushSeqCmd(6, 'SPD_BRAKE_SW', 1) # 0 = Out, 1 = Hold, 2 = In

	# Oxygen Regulator Supply lever ... ON full
	pushSeqCmd(dt, 'OXY_REG_SUP', 0) # 0 = ON, int16 = OFF)

	# Ground electric power ... OFF
	pushSeqCmd(dt, 'scriptKeyboard', '\\')
	pushSeqCmd(dt, 'scriptKeyboard', 'F8') # Ground crew
	pushSeqCmd(dt, 'scriptKeyboard', 'F2') # Ground electric power
	pushSeqCmd(dt, 'scriptKeyboard', 'F2') # Off
	pushSeqCmd(11, '', '', "Ground electric power is off")

	# Canopy ... Close
	pushSeqCmd(dt, 'CANOPY', 1) # 0 = OPEN, 1 = OFF, 2 = CLOSE
	pushSeqCmd(dt, 'CANOPY', 2) # 0 = OPEN, 1 = OFF, 2 = CLOSE
	# Wait for canopy to close
	pushSeqCmd(dt, 'scriptCockpitState', control='F-86F Sabre/CANOPY_POS', value=0, condition='=')
	pushSeqCmd(dt, 'CANOPY', 1) # 0 = OPEN, 1 = OFF, 2 = CLOSE

	# Radio ... ON
	pushSeqCmd(dt, 'ARC27_PWR_SEL', 1) # 0 = OFF, 1 = T/R, 2 = T/R + G, 3 = REC/ADF

	# IFF knob ... NORM
	pushSeqCmd(dt, 'APX6_MASTER', 3) # 0 = OFF, 1 = STDBY, 2 = LOW, 3 = NORM, 4 = EMERGENCY

	# IFF MODE 2 switch ... ON
	pushSeqCmd(dt, 'APX6_IFF_2', 2) # 0 = I/P, 1 = OUT, 2 = ON

	# IFF MODE 3 switch ... ON
	pushSeqCmd(dt, 'APX6_IFF_3', 1) # 0 = OUT, 2 = ON

	# PITOT HEAT switch ... ON
	pushSeqCmd(dt, 'PITOT_HEAT', 1) # 0 = OFF, 1 = ON

	# Guns ... ALL GUNS
	pushSeqCmd(dt, 'WPN_GUN_SEL', 4) # 0 = OFF, 1 = UPPER GUNS, 2 = MID GUNS, 3 = LOWER GUNS, 4 = ALL GUNS

	# Gun heater switch ... ON
	pushSeqCmd(dt, 'WPN_GUN_HEAT', 2) # 0 = Reset? (spring loaded to center), 1 = OFF, 2 = ON

	# Gun/Missile selector switch ... GUNS
	pushSeqCmd(dt, 'WPN_GUN_MISS', 1) # 0 = MISSILE, 1 = GUNS, 2 = SIGHT CAMERA & RADAR, 3 = OFF

	# Gun sight wingspan lever ... 30 ft (all the way left)
	pushSeqCmd(dt, 'A4_SGHT_WING_ADJ', 0) # (int values 1-47) 0 = 30 ft, 47 = 120 ft

	pushSeqCmd(dt, 'scriptSpeech', "Manual steps remaining: Set lights, tune radios, If carrying drop tanks, set Fuel Tank Selector Knob.  Set takeoff trim using takeoff trim position indicator light.")

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

	# IFF MODE 2 switch ... ON
	pushSeqCmd(dt, 'APX6_IFF_2', 2) # 0 = I/P, 1 = OUT, 2 = ON

	# IFF MODE 3 switch ... ON
	pushSeqCmd(dt, 'APX6_IFF_3', 1) # 0 = OUT, 2 = ON

	# Guns ... ALL GUNS
	pushSeqCmd(dt, 'WPN_GUN_SEL', 4) # 0 = OFF, 1 = UPPER GUNS, 2 = MID GUNS, 3 = LOWER GUNS, 4 = ALL GUNS

	# Gun heater switch ... ON
	pushSeqCmd(dt, 'WPN_GUN_HEAT', 2) # 0 = Reset? (spring loaded to center), 1 = OFF, 2 = ON

	# Gun sight wingspan lever ... 30 ft (all the way left)
	pushSeqCmd(dt, 'A4_SGHT_WING_ADJ', 0) # (int values 1-47) 0 = 30 ft, 47 = 120 ft

	pushSeqCmd(dt, 'scriptSpeech', "Manual steps remaining: Set lights, tune radios, If carrying drop tanks, set Fuel Tank Selector Knob.  Set takeoff trim using takeoff trim position indicator light.")

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

	# IFF MODE 2 switch ... ON
	pushSeqCmd(dt, 'APX6_IFF_2', 2) # 0 = I/P, 1 = OUT, 2 = ON

	# IFF MODE 3 switch ... ON
	pushSeqCmd(dt, 'APX6_IFF_3', 1) # 0 = OUT, 2 = ON

	# Gun heater switch ... ON
	pushSeqCmd(dt, 'WPN_GUN_HEAT', 2) # 0 = Reset? (spring loaded to center), 1 = OFF, 2 = ON

	# Gun sight wingspan lever ... 30 ft (all the way left)
	pushSeqCmd(dt, 'A4_SGHT_WING_ADJ', 0) # (int values 1-47) 0 = 30 ft, 47 = 120 ft

	pushSeqCmd(dt, 'scriptSpeech', "Manual steps remaining: Set lights, tune radios, If carrying drop tanks, set Fuel Tank Selector Knob.")

	return seq


def Shutdown(config, vars):
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


	pushSeqCmd(0, '', '', "Running Shutdown sequence")

	# Gun/Missile selector switch ... OFF
	pushSeqCmd(dt, 'WPN_GUN_MISS', 3) # 0 = MISSILE, 1 = GUNS, 2 = SIGHT CAMERA & RADAR, 3 = OFF

	# Gun heater switch ... OFF
	pushSeqCmd(dt, 'WPN_GUN_HEAT', 1) # 0 = Reset? (spring loaded to center), 1 = OFF, 2 = ON

	# Guns ... OFF
	pushSeqCmd(dt, 'WPN_GUN_SEL', 0) # 0 = OFF, 1 = UPPER GUNS, 2 = MID GUNS, 3 = LOWER GUNS, 4 = ALL GUNS

	# PITOT HEAT switch ... OFF
	pushSeqCmd(dt, 'PITOT_HEAT', 0) # 0 = OFF, 1 = ON

	# IFF knob ... OFF
	pushSeqCmd(dt, 'APX6_MASTER', 0) # 0 = OFF, 1 = STDBY, 2 = LOW, 3 = NORM, 4 = EMERGENCY

	# IFF MODE 2 switch ... OFF
	pushSeqCmd(dt, 'APX6_IFF_2', 1) # 0 = I/P, 1 = OUT, 2 = ON

	# IFF MODE 3 switch ... OFF
	pushSeqCmd(dt, 'APX6_IFF_3', 0) # 0 = OUT, 2 = ON

	# Radio ... OFF
	pushSeqCmd(dt, 'ARC27_PWR_SEL', 0) # 0 = OFF, 1 = T/R, 2 = T/R + G, 3 = REC/ADF

	# Canopy ... Open
	pushSeqCmd(dt, 'CANOPY', 0) # 0 = OPEN, 1 = OFF, 2 = CLOSE
	# Wait for canopy to close
	pushSeqCmd(dt, 'scriptCockpitState', control='F-86F Sabre/CANOPY_POS', value=58981, condition='=')
	pushSeqCmd(dt, 'CANOPY', 1) # 0 = OPEN, 1 = OFF, 2 = CLOSE

	# Oxygen Regulator Supply lever ... OFF
	pushSeqCmd(dt, 'OXY_REG_SUP', int16()) # 0 = ON, int16 = OFF)

	# Throttle ... OFF
	pushSeqCmd(dt, 'scriptKeyboard', 'end')

	# Engine Master switch ... OFF
	pushSeqCmd(dt, 'ENG_MASTER', 0)

	# Battery switch ... OFF
	pushSeqCmd(dt, 'BAT_START', 1) # 0 = STARTER, 1 = OFF, 2 = BATTERY

	return seq
