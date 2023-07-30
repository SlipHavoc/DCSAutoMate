# Return a Dictionary of script titles and their corresponding function names.  This is a list of scripts that users will be selecting from.  The module may have other utility functions that will not be run directly by the users.
def getScriptFunctions():
	return {
		'Cold Start': 'ColdStart',
		'Hot Start': 'HotStart',
	}

def getInfo():
	return """ATTENTION: You must remap "Throttle (Left) - IDLE" to LAlt+Home, and "Throttle (Left) - OFF" to LAlt+End.  This is because pyWinAuto doesn't support RAlt or RCtrl."""

# Returns 0-65535 scaled by multiple (0-1), eg for 50% call int16(0.5)
def int16(mult = 1):
	int16 = 65535
	return int(mult * int16)


def ColdStart(config):
	seq = []
	seqTime = 0
	dt = 0.2

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
	
	
	pushSeqCmd(0, '', '', "Running Cold Start sequence")
	pushSeqCmd(dt, 'scriptSpeech', "Warning, uses non standard key bindings.")

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
	pushSeqCmd(dt, 'scriptKeyboard', '{\ down}{\ up}') # Must have separate down and up to register key press.
	pushSeqCmd(dt, 'scriptKeyboard', '{F8}') # Ground crew
	pushSeqCmd(dt, 'scriptKeyboard', '{F5}') # Ground air supply
	pushSeqCmd(dt, 'scriptKeyboard', '{F1}') # Connect
	pushSeqCmd(8, '', '', "Ground air supply is on")

	# Left engine
	# Apply ground air supply
	pushSeqCmd(dt, 'scriptKeyboard', '{\ down}{\ up}') # Must have separate down and up to register key press.
	pushSeqCmd(dt, 'scriptKeyboard', '{F8}') # Ground crew
	pushSeqCmd(dt, 'scriptKeyboard', '{F5}') # Ground air supply
	pushSeqCmd(dt, 'scriptKeyboard', '{F3}') # Apply
	pushSeqCmd(8, '', '', 'Left engine at 10% RPM')
	pushSeqCmd(dt, 'L_START', 1) # Press
	pushSeqCmd(dt, 'L_START', 0) # Release
	pushSeqCmd(dt, 'scriptKeyboard', '{VK_LMENU down}{VK_HOME}{VK_LMENU up}', 'ATTENTION: You must remap Throttle (Left) - IDLE to LAlt+Home') # FIXME pyWinAuto doesn't support RAlt or RCtrl.
	pushSeqCmd(15, '', '', 'Left engine at 50% (idle)')
	
	# Right engine
	# Ground air supply on
	pushSeqCmd(dt, 'scriptKeyboard', '{\ down}{\ up}') # Must have separate down and up to register key press.
	pushSeqCmd(dt, 'scriptKeyboard', '{F8}') # Ground crew
	pushSeqCmd(dt, 'scriptKeyboard', '{F5}') # Ground air supply
	pushSeqCmd(dt, 'scriptKeyboard', '{F3}') # Apply
	pushSeqCmd(8, '', '', 'Right engine at 10% RPM')
	pushSeqCmd(dt, 'R_START', 1) # Press
	pushSeqCmd(dt, 'R_START', 0) # Release
	pushSeqCmd(dt, 'scriptKeyboard', '{VK_RSHIFT down}{VK_HOME}{VK_RSHIFT up}')
	pushSeqCmd(15, '', '', 'Right engine at 50% (idle)')

	# Ground air supply off
	pushSeqCmd(dt, 'scriptKeyboard', '{\ down}{\ up}') # Must have separate down and up to register key press.
	pushSeqCmd(dt, 'scriptKeyboard', '{F8}') # Ground crew
	pushSeqCmd(dt, 'scriptKeyboard', '{F5}') # Ground air supply
	pushSeqCmd(dt, 'scriptKeyboard', '{F2}') # Disconnect
	pushSeqCmd(8, '', '', 'Ground air supply is off')
	
	pushSeqCmd(dt, 'AUTOBAL', 0) # = 0 LEFT LOW, 1 = NEUTRAL, 2 = RIGHT LOW
	
	pushSeqCmd(dt, 'SIGHT_MODE', 1) # 0 = OFF, 1 = MSL, 2 = A/A1 GUNS, 3 = A/A2 GUNS, 4 = MAN

	pushSeqCmd(dt, 'RADAR_MODE', 1) # 0 = OFF, 1 = STBY, 2 = OPER, 3 = TEST
	
	pushSeqCmd(dt, 'RWR_PWR', 1)
	
	# Retract speed brake
	pushSeqCmd(dt, 'SPEED', 1)
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

	# IFF controls not working in DCS BIOS?? Doesn't matter, as not functional anyway...
	#pushSeqCmd(dt, 'IFF4_CONTROL', 1)
	
	pushSeqCmd(dt, 'PITOT_HEATER', 1)
	
	pushSeqCmd(dt, 'EMER_JETT_COVER', 1)
	
	pushSeqCmd(dt, 'scriptSpeech', "Manual steps remaining: Lights, Radios, If carrying drop tanks set Fuel EXTERNAL PYLON switches, Set pitch trim for takeoff, see kneeboard.")
	
	return seq


def HotStart(config):
	seq = []
	seqTime = 0
	dt = 0.2

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

	# IFF controls not working in DCS BIOS?? Doesn't matter, as not functional anyway...
	#pushSeqCmd(dt, 'IFF4_CONTROL', 1)
	
	pushSeqCmd(dt, 'EMER_JETT_COVER', 1)
	
	pushSeqCmd(dt, 'scriptSpeech', "Manual steps remaining: Lights, Radios, If carrying drop tanks set Fuel EXTERNAL PYLON switches, Set pitch trim for takeoff, see kneeboard.")
	
	return seq
