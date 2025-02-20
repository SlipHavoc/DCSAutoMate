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
			#{
			#	'name': 'Test',
			#	'function': 'Test',
			#	'vars': {},
			#},
		],
	}

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

	pushSeqCmd(0, '', '', "Running Cold Start sequence")

	# Set intercom mode knob to INT, allows rearming.
	pushSeqCmd(dt, 'INT_MODE', 1) # 0 = PVT, 1 = INT, 2 = 1, 3 = 2, 4 = 3, 5 = 4

	# Doors ... Toggle
	pushSeqCmd(dt, 'DOOR_L_PTR', 1)
	pushSeqCmd(dt, 'DOOR_R_PTR', 1)

	# AC VOLTMETER ... AC PHASE
	pushSeqCmd(dt, 'AC_VM_SRC', 1) # 0 = AB, 1 = AC PHASE, 2 = BC

	# INVERTER ... OFF
	pushSeqCmd(dt, 'INVERTER_SW', 1) # 0 = MAIN ON, 1 = OFF, 2 = SPARE ON

	# MAIN GENERATOR ... ON
	pushSeqCmd(dt, 'MAIN_GEN_COVER', 1) # Cover open (it starts open on cold spawn)
	pushSeqCmd(dt, 'MAIN_GEN_SW', 0)  # 0 = ON, 1 = OFF, 2 = RESET
	pushSeqCmd(dt, 'MAIN_GEN_COVER', 0) # Cover close

	# DC VOLTMETER ... ESS BUS
	pushSeqCmd(dt, 'DC_VM_SRC', 3) # 0 = BAT, 1 = MAIN GEN, 2 = STBY GEN, 3 = ESS BUS, 4 = NON-ESS BUS

	# STARTER-GENERATOR ... START
	pushSeqCmd(dt, 'STARTER_GEN_SW', 1) # 0 = STBY GEN, 1 = START

	# BATTERY ... ON
	pushSeqCmd(dt, 'BAT_SW', 0) # 0 = ON, 1 = OFF

	# LOW RPM WARNING AUDIO ... OFF
	pushSeqCmd(dt, 'LOW_RPM_AUDIO', 0)

	# GOVERNOR ... AUTO
	pushSeqCmd(dt, 'EMER_GOV_SW', 1)

	# DE-ICE ... OFF
	pushSeqCmd(dt, 'ENG_DEICE', 0)

	# MAIN FUEL ... ON
	pushSeqCmd(dt, 'MAIN_FUEL_SW', 1)

	# HYDRAULIC CONTROL ... ON
	pushSeqCmd(dt, 'HYD_CONT_SW', 1)

	# FORCE TRIM ... ON
	pushSeqCmd(dt, 'FORCE_TRIM_SW', 1)

	# CHIP DETECTOR ... BOTH
	pushSeqCmd(dt, 'CHIP_DET_SW', 1)

	"""
	Correct engine start procedure:
	1. Throttle to start position (just on the decrease side of the idle stop).
	2. Press and hold the start button.  The rotor should start turning when the N1 (gas producer) RPM reaches 15%.
	3. Keep holding the start button for 40 seconds, or until 40% N1, whichever comes first, then release the start button.
	4. Increase the throttle to the idle stop position.  Let the engine spool up to idle (68-72% N1, 40% Engine RPM).
	5. Slowly increase the throttle to max.

	DCS start procedure has to be modified because the gauge values in DCS BIOS "wrap around" from 0 to 65535 several times, so there's no way to tell their absolute position.  Also, having the throttle at idle seems to work fine.  Here's the modified startup sequence:
	1. Set throttle to idle stop.
	2. Press and hold the start button.
	3. Keep holding the start button for 40 seconds.  This is longer than it needs, but the roter should be fully spun up to idle very soon afterwards.
	4. Release the start button.
	5. Increase the throttle to max.
	"""

	# THROTTLE ... SET TO IDLE POSITION
	pushSeqCmd(dt, 'THROTTLE', 46810) # 0 = Max throttle, 46810 = Idle stop, ~50000 = Engine start position, 65535 = Min throttle
	# START ENGINE (40s)
	pushSeqCmd(dt, 'scriptKeyboard', 'home down') # Press
	pushSeqCmd(40, '', '', "Engine started, releasing START button.")
	pushSeqCmd(dt, 'scriptKeyboard', 'home up') # Release

	# INVERTER ... MAIN ON
	pushSeqCmd(dt, 'INVERTER_SW', 0) # 0 = MAIN ON, 1 = OFF, 2 = SPARE ON

	# STARTER-GENERATOR ... STBY GEN
	pushSeqCmd(dt, 'STARTER_GEN_SW', 0) # 0 = STBY GEN, 1 = START

	# DC VOLTMETER ... MAIN GEN
	pushSeqCmd(dt, 'DC_VM_SRC', 1) # 0 = BAT, 1 = MAIN GEN, 2 = STBY GEN, 3 = ESS BUS, 4 = NON-ESS BUS

	# THROTTLE ... SET TO FULL
	for throttlePos in range(46810, 0, -1000):
		pushSeqCmd(dt, 'THROTTLE', throttlePos)
	pushSeqCmd(dt, 'THROTTLE', 0) # Make sure the throttle is set to full (0) at the end.

	# LOW RPM WARNING AUDIO ... ON
	# NOTE This is a magnetically held switch, and turns back on automatically as the rotor spins up.
	#pushSeqCmd(dt, 'LOW_RPM_AUDIO', 1)

	# MASTER CAUTION ... RESET
	pushSeqCmd(dt, 'CLP_RESET_TEST_SW', 2)
	pushSeqCmd(dt, 'CLP_RESET_TEST_SW', 1)

	# IFF MASTER knob ... NORM
	pushSeqCmd(dt, 'IFF_MASTER', 3) # 0 = OFF, 1 = STBY, 2 = LOW, 3 = NORM, 4 = EMER
	# IFF CODE knob ... A
	# NOTE This control doesn't support directly setting the position, so to be idempotent, decrement all the way, then increment.
	pushSeqCmd(dt, 'IFF_CODE', 'DEC')
	pushSeqCmd(dt, 'IFF_CODE', 'DEC')
	pushSeqCmd(dt, 'IFF_CODE', 'INC')
	pushSeqCmd(dt, 'IFF_CODE', 'INC')
	# IFF ON OUT switch ... ON
	pushSeqCmd(dt, 'IFF_ON_OUT', 1) # 0 = OUT, 1 = ON

	# RADAR ALTIMETER circuit breaker switch... ON (overhead panel far rear)
	pushSeqCmd(dt, 'RADAR_ALT_PWR', 1)
	# Turn on Radar Altimeter by setting the low altitude above 0.
	for i in range(5):
		pushSeqCmd(dt, 'RADAR_ALT_LO', '+3200')

	# ARC-51BX UHF RADIO (COM1) ... T/R
	pushSeqCmd(dt, 'UHF_FUNCTION', 1)

	# ARC-134 VHF AM RADIO (COM2) ... ON
	pushSeqCmd(dt, 'VHFCOMM_PWR', 1)

	# ARC-131 VHF FM RADIO (COM3) ... T/R
	pushSeqCmd(dt, 'VHFFM_MODE', 1)

	# MASTER ARM ... ON
	pushSeqCmd(dt, 'MASTER_ARM_SW', 2)

	# ROCKET PAIRS ... 1
	pushSeqCmd(dt, 'ROCKET_PAIR', 1)

	# FLARE DISPENSER ... ARM
	pushSeqCmd(dt, 'CM_ARM_SW', 1)

	# FLARE DISPENSER COUNT ... 30
	for i in range(30):
		pushSeqCmd(dt, 'CM_FLARECNT', 'INC')

	pushSeqCmd(dt, 'scriptSpeech', "Manual steps remaining: Syncronize HSI compass (backup compass shows current heading).  Set lights, tune radios.")

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

	pushSeqCmd(0, '', '', "Running Hot Start sequence")

	# Set intercom mode knob to INT, allows rearming.
	pushSeqCmd(dt, 'INT_MODE', 1) # 0 = PVT, 1 = INT, 2 = 1, 3 = 2, 4 = 3, 5 = 4

	# AC VOLTMETER ... AC PHASE
	pushSeqCmd(dt, 'AC_VM_SRC', 1) # 0 = AB, 1 = AC PHASE, 2 = BC

	# IFF MASTER knob ... NORM
	pushSeqCmd(dt, 'IFF_MASTER', 3) # 0 = OFF, 1 = STBY, 2 = LOW, 3 = NORM, 4 = EMER
	# IFF CODE knob ... A
	# NOTE This control doesn't support directly setting the position, so to be idempotent, decrement all the way, then increment.
	pushSeqCmd(dt, 'IFF_CODE', 'DEC')
	pushSeqCmd(dt, 'IFF_CODE', 'DEC')
	pushSeqCmd(dt, 'IFF_CODE', 'INC')
	pushSeqCmd(dt, 'IFF_CODE', 'INC')
	# IFF ON OUT switch ... ON
	pushSeqCmd(dt, 'IFF_ON_OUT', 1) # 0 = OUT, 1 = ON

	# ARC-51BX UHF RADIO (COM1) ... T/R
	pushSeqCmd(dt, 'UHF_FUNCTION', 1)

	# ARC-134 VHF AM RADIO (COM2) ... ON
	pushSeqCmd(dt, 'VHFCOMM_PWR', 1)

	# ARC-131 VHF FM RADIO (COM3) ... T/R
	pushSeqCmd(dt, 'VHFFM_MODE', 1)

	# MASTER ARM ... ON
	pushSeqCmd(dt, 'MASTER_ARM_SW', 2)

	# ROCKET PAIRS ... 1
	pushSeqCmd(dt, 'ROCKET_PAIR', 1)

	# FLARE DISPENSER ... ARM
	pushSeqCmd(dt, 'CM_ARM_SW', 1)

	# FLARE DISPENSER COUNT ... 30
	for i in range(30):
		pushSeqCmd(dt, 'CM_FLARECNT', 'INC')

	pushSeqCmd(dt, 'scriptSpeech', "Manual steps remaining: Check HSI compass sync (backup compass shows current heading).  Set lights, tune radios.")

	return seq


def Shutdown(self, vars):
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

	pushSeqCmd(0, '', '', "Running Shutdown sequence")

	# THROTTLE ... SET TO IDLE POSITION
	pushSeqCmd(dt, 'THROTTLE', 46810) # 0 = Max throttle, 46810 = Idle stop, ~50000 = Engine start position, 65535 = Min throttle
	pushSeqCmd(3, '', '', 'Wait for engine to spool down a bit.')

	# LOW RPM WARNING AUDIO ... OFF
	pushSeqCmd(dt, 'LOW_RPM_AUDIO', 0)

	# IFF MASTER knob ... OFF
	pushSeqCmd(dt, 'IFF_MASTER', 0) # 0 = OFF, 1 = STBY, 2 = LOW, 3 = NORM, 4 = EMER
	# IFF ON OUT switch ... OUT
	pushSeqCmd(dt, 'IFF_ON_OUT', 0) # 0 = OUT, 1 = ON

	# RADAR ALTIMETER circuit breaker switch... OFF (overhead panel far rear)
	pushSeqCmd(dt, 'RADAR_ALT_PWR', 0)
	for i in range(11):
		pushSeqCmd(dt, 'RADAR_ALT_LO', '-50000')
	for i in range(11):
		pushSeqCmd(dt, 'RADAR_ALT_HI', '-50000')

	# ARC-51BX UHF RADIO (COM1) ... OFF
	pushSeqCmd(dt, 'UHF_FUNCTION', 0)

	# ARC-134 VHF AM RADIO (COM2) ... OFF
	pushSeqCmd(dt, 'VHFCOMM_PWR', 0)

	# ARC-131 VHF FM RADIO (COM3) ... OFF
	pushSeqCmd(dt, 'VHFFM_MODE', 0)

	# MASTER ARM ... SAFE
	pushSeqCmd(dt, 'MASTER_ARM_SW', 0)

	# ROCKET PAIRS ... 0
	pushSeqCmd(dt, 'ROCKET_PAIR', 0)

	# FLARE DISPENSER ... SAFE
	pushSeqCmd(dt, 'CM_ARM_SW', 0)

	# GOVERNOR ... AUTO
	pushSeqCmd(dt, 'EMER_GOV_SW', 1)

	# HYDRAULIC CONTROL ... OFF
	pushSeqCmd(dt, 'HYD_CONT_SW', 0)

	# FORCE TRIM ... OFF
	pushSeqCmd(dt, 'FORCE_TRIM_SW', 0)

	# Throttle ... Stop
	pushSeqCmd(dt, 'THROTTLE_STOP', 1)
	#pushSeqCmd(dt, 'THROTTLE_STOP2', 1)
	pushSeqCmd(dt, 'THROTTLE', int16())

	# MAIN FUEL ... OFF
	pushSeqCmd(dt, 'MAIN_FUEL_SW', 0)

	# INVERTER ... OFF
	pushSeqCmd(dt, 'INVERTER_SW', 1) # 0 = MAIN ON, 1 = OFF, 2 = SPARE ON

	# MAIN GENERATOR ... OFF
	pushSeqCmd(dt, 'MAIN_GEN_COVER', 1) # Cover open (it starts open on cold spawn)
	pushSeqCmd(dt, 'MAIN_GEN_SW', 1) # 0 = ON, 1 = OFF, 2 = RESET
	# Leave cover open.

	# STARTER-GENERATOR ... START
	pushSeqCmd(dt, 'STARTER_GEN_SW', 1) # 0 = STBY GEN, 1 = START

	# BATTERY ... OFF
	pushSeqCmd(dt, 'BAT_SW', 1) # 0 = ON, 1 = OFF

	# Doors ... Toggle
	pushSeqCmd(dt, 'DOOR_L_PTR', 1)
	pushSeqCmd(dt, 'DOOR_R_PTR', 1)

	return seq
