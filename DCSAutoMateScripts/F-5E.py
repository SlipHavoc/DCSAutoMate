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
				'name': 'Test',
				'function': 'Test',
				'vars': {},
			},
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

	pushSeqCmd(dt, 'CANOPY_LEVER', 1)

	# Oxygen
	pushSeqCmd(dt, 'O2_LEVER', 1)
	pushSeqCmd(dt, 'DILUTER_LEVER', 0) # 0 = NORMAL, 1 = 100% OXYGEN

	pushSeqCmd(dt, 'SW_BATTERY', 1)

	pushSeqCmd(dt, 'FLIGHT_LIGHTS', int16())
	pushSeqCmd(dt, 'ENGINE_LIGHTS', int16())
	pushSeqCmd(dt, 'CONSOLE_LIGHTS', int16())
	pushSeqCmd(dt, 'ARM_LIGHTS', int16())

	pushSeqCmd(dt, 'UHF_FUNC', 1) # 0 = OFF, 1 = MAIN, 2 = BOTH, 3 = ADF

	pushSeqCmd(dt, 'L_GENERATOR', 1)
	pushSeqCmd(dt, 'R_GENERATOR', 1)

	pushSeqCmd(dt, 'L_BOOSTPUMP', 1)
	pushSeqCmd(dt, 'R_BOOSTPUMP', 1)

	# Start engines

	# Ground air supply on
	pushSeqCmd(dt, 'scriptKeyboard', '\\')
	pushSeqCmd(dt, 'scriptKeyboard', 'F8') # Ground crew
	pushSeqCmd(dt, 'scriptKeyboard', 'F5') # Ground air supply
	pushSeqCmd(dt, 'scriptKeyboard', 'F1') # Connect
	pushSeqCmd(8, '', '', "Ground air supply is on")

	# Left engine
	# Apply ground air supply
	pushSeqCmd(dt, 'scriptKeyboard', '\\')
	pushSeqCmd(dt, 'scriptKeyboard', 'F8') # Ground crew
	pushSeqCmd(dt, 'scriptKeyboard', 'F5') # Ground air supply
	pushSeqCmd(dt, 'scriptKeyboard', 'F3') # Apply
	pushSeqCmd(8, '', '', 'Left engine at 10% RPM')
	pushSeqCmd(dt, 'L_START', 1) # Press
	pushSeqCmd(dt, 'L_START', 0) # Release
	pushSeqCmd(dt, 'scriptKeyboard', 'RAlt down')
	pushSeqCmd(dt, 'scriptKeyboard', 'home')
	pushSeqCmd(dt, 'scriptKeyboard', 'RAlt up')
	pushSeqCmd(15, '', '', 'Left engine at 50% (idle)')

	# Right engine
	# Ground air supply on
	pushSeqCmd(dt, 'scriptKeyboard', '\\')
	pushSeqCmd(dt, 'scriptKeyboard', 'F8') # Ground crew
	pushSeqCmd(dt, 'scriptKeyboard', 'F5') # Ground air supply
	pushSeqCmd(dt, 'scriptKeyboard', 'F3') # Apply
	pushSeqCmd(8, '', '', 'Right engine at 10% RPM')
	pushSeqCmd(dt, 'R_START', 1) # Press
	pushSeqCmd(dt, 'R_START', 0) # Release
	pushSeqCmd(dt, 'scriptKeyboard', 'RShift down')
	pushSeqCmd(dt, 'scriptKeyboard', 'home')
	pushSeqCmd(dt, 'scriptKeyboard', 'RShift up')
	pushSeqCmd(15, '', '', 'Right engine at 50% (idle)')

	# Ground air supply off
	pushSeqCmd(dt, 'scriptKeyboard', '\\') # Must have separate down and up to register key press.
	pushSeqCmd(dt, 'scriptKeyboard', 'F8') # Ground crew
	pushSeqCmd(dt, 'scriptKeyboard', 'F5') # Ground air supply
	pushSeqCmd(dt, 'scriptKeyboard', 'F2') # Disconnect
	pushSeqCmd(8, '', '', 'Ground air supply is off')

	pushSeqCmd(dt, 'AUTOBAL', 0) # = 0 LEFT LOW, 1 = NEUTRAL, 2 = RIGHT LOW

	pushSeqCmd(dt, 'SIGHT_MODE', 1) # 0 = OFF, 1 = MSL, 2 = A/A1 GUNS, 3 = A/A2 GUNS, 4 = MAN

	pushSeqCmd(dt, 'RADAR_MODE', 1) # 0 = OFF, 1 = STBY, 2 = OPER, 3 = TEST

	pushSeqCmd(dt, 'RWR_PWR', 1)

	# Retract speed brake
	pushSeqCmd(dt, 'SPEED', 2) # 0 = Out, 1 = Stop, 2 = In
	pushSeqCmd(2, 'SPEED', 1) # 0 = Out, 1 = Stop, 2 = In

	pushSeqCmd(dt, 'A_FLAPS', 0) # 0 = AUTO, 2 = FIXED, 3 = UP
	pushSeqCmd(dt, 'PITCH_DAMPER', 1)
	pushSeqCmd(dt, 'YAW_DAMPER', 1)

	# BACKUP ATTITUDE INDICATOR - UNCAGE
	inc = 1000
	val = 5000
	for i in range(30):
		pushSeqCmd(dt, 'SAI_PITCH_TRIM', val)
		val += inc

	# SPEED INDEX - 325KTS (CORNER SPEED
	# Set index to 0 first (29 iterations of value=1.0 resets it to 0 from max).
	for i in range(29):
		pushSeqCmd(dt, 'IAS_SET', int16(-1))
	# Then set to desired speed (16.6 units)
	for i in range(16):
		pushSeqCmd(dt, 'IAS_SET', int16())
	pushSeqCmd(dt, 'IAS_SET', int16(0.6)) # Turn the remaining fraction of units.

	pushSeqCmd(dt, 'CANOPY_LEVER', 0)

	pushSeqCmd(dt, 'MC_RESET_BTN', 1) # Press
	pushSeqCmd(dt, 'MC_RESET_BTN', 0) # Release

	pushSeqCmd(dt, 'CHAFF_MODE', 1) # 0 = OFF, 1 = SINGLE, 2 = PRGM, 3 = MULT
	# NOTE Inconsistent command name between CHAFF_MODE and FLARE_MODE_SEL.
	pushSeqCmd(dt, 'FLARE_MODE_SEL', 1) # 0 = OFF, 1 = SINGLE, 2 = PRGM, 3 = MULT

	# FIXME IFF controls not working in DCS BIOS, and some may be wired to the wrong things.  IFF4_MASTER should control the mode knob, but instead turns one of the code number wheels.
	#pushSeqCmd(dt, 'IFF4_CONTROL', 1)

	pushSeqCmd(dt, 'PITOT_HEATER', 1)

	pushSeqCmd(dt, 'EMER_JETT_COVER', 1)

	pushSeqCmd(dt, 'scriptSpeech', "Manual steps remaining: I F F, Lights, Radios, If carrying drop tanks set Fuel EXTERNAL PYLON switches, Set pitch trim for takeoff, see kneeboard.")

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

	pushSeqCmd(dt, 'FLIGHT_LIGHTS', int16())
	pushSeqCmd(dt, 'ENGINE_LIGHTS', int16())
	pushSeqCmd(dt, 'CONSOLE_LIGHTS', int16())
	pushSeqCmd(dt, 'ARM_LIGHTS', int16())

	pushSeqCmd(dt, 'AUTOBAL', 0) # = 0 LEFT LOW, 1 = NEUTRAL, 2 = RIGHT LOW

	pushSeqCmd(dt, 'RWR_PWR', 1)

	# SPEED INDEX - 325KTS (CORNER SPEED)
	# Set index to 0 first (29 iterations of value=1.0 resets it to 0 from max).
	for i in range(29):
		pushSeqCmd(dt, 'IAS_SET', int16(-1))
	# Then set to desired speed (16.6 units)
	for i in range(16):
		pushSeqCmd(dt, 'IAS_SET', int16())
	pushSeqCmd(dt, 'IAS_SET', int16(0.6)) # Turn the remaining fraction of units.

	pushSeqCmd(dt, 'CHAFF_MODE', 1) # 0 = OFF, 1 = SINGLE, 2 = PRGM, 3 = MULT
	# NOTE Inconsistent command name between CHAFF_MODE and FLARE_MODE_SEL.
	pushSeqCmd(dt, 'FLARE_MODE_SEL', 1) # 0 = OFF, 1 = SINGLE, 2 = PRGM, 3 = MULT

	# FIXME IFF controls not working in DCS BIOS, and some may be wired to the wrong things.  IFF4_MASTER should control the mode knob, but instead turns one of the code number wheels.
	#pushSeqCmd(dt, 'IFF4_CONTROL', 1)

	pushSeqCmd(dt, 'EMER_JETT_COVER', 1)

	pushSeqCmd(dt, 'scriptSpeech', "Manual steps remaining: I F F, Lights, Radios, If carrying drop tanks set Fuel EXTERNAL PYLON switches, Set pitch trim for takeoff, see kneeboard.")

	return seq
