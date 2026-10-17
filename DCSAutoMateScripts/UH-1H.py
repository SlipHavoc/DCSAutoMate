# Return a Dictionary of script data.  The 'scripts' key is a list of scripts that users will be selecting from.  Each script has an associated 'function', which is the name of the function in this file that will be called to generate the command sequence, and a dictionary of 'vars' that the user will be prompted to choose from before running the script, and will be passed into the sequence generating function.
def getScriptData():
	return {
		'moduleName': 'UH-1H',
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


def Test(config, vars, helper, *args, **kwargs):
	seq = []
	dt = 0.3

	pushSeqCmd = helper.makePushSeqCmd(seq)

	# Test code here...
	pushSeqCmd(0, '', '', "Running Test sequence")


	return seq


def ColdStart(config, vars, helper, *args, **kwargs):
	seq = []
	dt = 0.3

	pushSeqCmd = helper.makePushSeqCmd(seq)

	pushSeqCmd(0, '', '', "Running Cold Start sequence")

	# Set intercom mode knob to INT, allows rearming.
	pushSeqCmd(dt, 'INTERCOM.TRANSMIT-INTERPHONE-SWITCH-PTR', 1) # 0 = PVT, 1 = INT, 2 = 1, 3 = 2, 4 = 3, 5 = 4

	# Doors ... Toggle
	pushSeqCmd(dt, 'CPT_MECH.DOOR_L-PTR', 1)
	pushSeqCmd(dt, 'CPT_MECH.DOOR_R-PTR', 1)

	# AC VOLTMETER ... AC PHASE
	pushSeqCmd(dt, 'ELEC_INTERFACE.PHASE-SWITCHER-PTR', 1) # 0 = AB, 1 = AC PHASE, 2 = BC

	# INVERTER ... OFF
	pushSeqCmd(dt, 'ELEC_INTERFACE.INVTR-SWITCHER-PTR', 1) # 0 = MAIN ON, 1 = OFF, 2 = SPARE ON

	# MAIN GENERATOR ... ON
	pushSeqCmd(dt, 'ELEC_INTERFACE.MAIN-GEN-SWITCHER-COVER-PTR', 1) # Cover open (it starts open on cold spawn)
	pushSeqCmd(dt, 'ELEC_INTERFACE.MAIN-GEN-SWITCHER-PTR', 0)  # 0 = ON, 1 = OFF, 2 = RESET
	pushSeqCmd(dt, 'ELEC_INTERFACE.MAIN-GEN-SWITCHER-COVER-PTR', 0) # Cover close

	# DC VOLTMETER ... ESS BUS
	pushSeqCmd(dt, 'ELEC_INTERFACE.VM-SWITCHER-PTR', 3) # 0 = BAT, 1 = MAIN GEN, 2 = STBY GEN, 3 = ESS BUS, 4 = NON-ESS BUS

	# STARTER-GENERATOR ... START
	pushSeqCmd(dt, 'ELEC_INTERFACE.STARTER-GEN-SWITCHERr-PTR', 1) # 0 = STBY GEN, 1 = START

	# BATTERY ... ON
	pushSeqCmd(dt, 'ELEC_INTERFACE.BAT-SWITCHER-PTR', 0) # 0 = ON, 1 = OFF

	# LOW RPM WARNING AUDIO ... OFF
	pushSeqCmd(dt, 'ENGINE_INTERFACE.LOW-RPM-PTR', 0)

	# GOVERNOR ... AUTO
	pushSeqCmd(dt, 'ENGINE_INTERFACE.GOV-PTR', 1)

	# DE-ICE ... OFF
	pushSeqCmd(dt, 'ENGINE_INTERFACE.DE-ICE-PTR', 0)

	# MAIN FUEL ... ON
	pushSeqCmd(dt, 'FUELSYS_INTERFACE.FUEL-PTR', 1)

	# HYDRAULIC CONTROL ... ON
	pushSeqCmd(dt, 'HYDRO_SYS_INTERFACE.HYD-CONT-PTR', 1)

	# FORCE TRIM ... ON
	pushSeqCmd(dt, 'HYDRO_SYS_INTERFACE.FORCE-TRIM-PTR', 1)

	# CHIP DETECTOR ... BOTH
	pushSeqCmd(dt, 'ENGINE_INTERFACE.CHIP-DET-PTR', 1)

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
	pushSeqCmd(dt, 'ENGINE_INTERFACE.THROTTLE-1-PTR', 0.714) # 0.0 = Max throttle, 0.7143 = Idle stop, ~0.7630 = Engine start position, 1.0 = Min throttle
	# START ENGINE (40s)
	#pushSeqCmd(dt, 'scriptKeyboard', 'home down') # Press
	pushSeqCmd(dt, 'ENGINE_INTERFACE.Button_18', 1) # START button
	pushSeqCmd(dt, 'scriptText', 'Engine starting, holding START button for 40 seconds.')
	pushSeqCmd(40, '', '', "Engine started, releasing START button.")
	pushSeqCmd(dt, 'ENGINE_INTERFACE.Button_18', 0) # Release START button
	#pushSeqCmd(dt, 'scriptKeyboard', 'home up') # Release

	# INVERTER ... MAIN ON
	pushSeqCmd(dt, 'ELEC_INTERFACE.INVTR-SWITCHER-PTR', 0) # 0 = MAIN ON, 1 = OFF, 2 = SPARE ON

	# STARTER-GENERATOR ... STBY GEN
	pushSeqCmd(dt, 'ELEC_INTERFACE.STARTER-GEN-SWITCHERr-PTR', 0) # 0 = STBY GEN, 1 = START

	# DC VOLTMETER ... MAIN GEN
	pushSeqCmd(dt, 'ELEC_INTERFACE.VM-SWITCHER-PTR', 1) # 0 = BAT, 1 = MAIN GEN, 2 = STBY GEN, 3 = ESS BUS, 4 = NON-ESS BUS

	# THROTTLE ... SET TO FULL
	#for throttlePos in range(0.714, 0, -0.01):
	throttlePos = 0.714
	while throttlePos >= 0:
		pushSeqCmd(dt, 'ENGINE_INTERFACE.THROTTLE-1-PTR', throttlePos)
		throttlePos -= 0.02
	pushSeqCmd(dt, 'ENGINE_INTERFACE.THROTTLE-1-PTR', 0.0) # Make sure the throttle is set to full (0.0) at the end.

	# LOW RPM WARNING AUDIO ... ON
	# NOTE This is a magnetically held switch, and turns back on automatically as the rotor spins up.
	#pushSeqCmd(dt, 'ENGINE_INTERFACE.LOW-RPM-PTR', 1)

	# MASTER CAUTION ... RESET
	pushSeqCmd(dt, 'SYS_CONTROLLER.RESET-TEST-SWITCH-PTR', 2)
	pushSeqCmd(dt, 'SYS_CONTROLLER.RESET-TEST-SWITCH-PTR', 1)

	# IFF MASTER knob ... NORM
	pushSeqCmd(dt, 'IFF.MASTER-CONTROL-PTR', 3) # 0 = OFF, 1 = STBY, 2 = LOW, 3 = NORM, 4 = EMER
	# IFF CODE knob ... A
	# NOTE This control doesn't support directly setting the position, so to be idempotent, decrement all the way, then increment.
	pushSeqCmd(dt, 'IFF.CODE-PTR', -1.0)
	pushSeqCmd(dt, 'IFF.CODE-PTR', -1.0)
	pushSeqCmd(dt, 'IFF.CODE-PTR', 1.0)
	pushSeqCmd(dt, 'IFF.CODE-PTR', 1.0)
	# IFF ON OUT switch ... ON
	pushSeqCmd(dt, 'IFF.MODE-4-SWITCH-PTR', 1) # 0 = OUT, 1 = ON

	# RADAR ALTIMETER circuit breaker switch... ON (overhead panel far rear)
	pushSeqCmd(dt, 'RADAR_ALTIMETER.RADAR-ALT-PTR', 1)
	# Turn on Radar Altimeter by setting the low altitude above 0.
	for i in range(5):
		pushSeqCmd(dt, 'RADAR_ALTIMETER.PITCH-LO-ALT-PTR', 0.1)

	# ARC-51BX UHF RADIO (COM1) ... T/R
	pushSeqCmd(dt, 'UHF_ARC_51.FUNCTION-SELECT-SWITCH-PTR', 1)

	# ARC-134 VHF AM RADIO (COM2) ... ON
	pushSeqCmd(dt, 'VHF_ARC_134.MHZ-SELECTOR-PTR_arg5', 1)

	# ARC-131 VHF FM RADIO (COM3) ... T/R
	pushSeqCmd(dt, 'VHF_ARC_131.MODE-SWITCH-PTR', 1)

	# MASTER ARM ... ON
	pushSeqCmd(dt, 'WEAPON_SYS.ARMED-SWITCH-PTR', 2)

	# ROCKET PAIRS ... 1
	pushSeqCmd(dt, 'WEAPON_SYS.RKT-PAIR-PTR', 1)

	# FLARE DISPENSER ... ARM
	pushSeqCmd(dt, 'XM_130.CHAFF-ARM-SWITCH-PTR', 1)

	# FLARE DISPENSER COUNT ... 30
	for i in range(30):
		pushSeqCmd(dt, 'XM_130.FLARE-PTR_arg452', 0.03)

	pushSeqCmd(dt, 'scriptSpeech', "Manual steps remaining: Syncronize H S I compass (backup compass shows current heading).  Set lights, tune radios.")

	return seq


def HotStart(config, vars, helper, *args, **kwargs):
	seq = []
	dt = 0.3

	pushSeqCmd = helper.makePushSeqCmd(seq)

	pushSeqCmd(0, '', '', "Running Hot Start sequence")

	# Set intercom mode knob to INT, allows rearming.
	pushSeqCmd(dt, 'INTERCOM.TRANSMIT-INTERPHONE-SWITCH-PTR', 1) # 0 = PVT, 1 = INT, 2 = 1, 3 = 2, 4 = 3, 5 = 4

	# AC VOLTMETER ... AC PHASE
	pushSeqCmd(dt, 'ELEC_INTERFACE.PHASE-SWITCHER-PTR', 1) # 0 = AB, 1 = AC PHASE, 2 = BC

	# IFF MASTER knob ... NORM
	pushSeqCmd(dt, 'IFF.MASTER-CONTROL-PTR', 3) # 0 = OFF, 1 = STBY, 2 = LOW, 3 = NORM, 4 = EMER
	# IFF CODE knob ... A
	# NOTE This control doesn't support directly setting the position, so to be idempotent, decrement all the way, then increment.
	pushSeqCmd(dt, 'IFF.CODE-PTR', -1.0)
	pushSeqCmd(dt, 'IFF.CODE-PTR', -1.0)
	pushSeqCmd(dt, 'IFF.CODE-PTR', 1.0)
	pushSeqCmd(dt, 'IFF.CODE-PTR', 1.0)
	# IFF ON OUT switch ... ON
	pushSeqCmd(dt, 'IFF.MODE-4-SWITCH-PTR', 1) # 0 = OUT, 1 = ON

	# ARC-51BX UHF RADIO (COM1) ... T/R
	pushSeqCmd(dt, 'UHF_ARC_51.FUNCTION-SELECT-SWITCH-PTR', 1)

	# ARC-134 VHF AM RADIO (COM2) ... ON
	pushSeqCmd(dt, 'VHF_ARC_134.MHZ-SELECTOR-PTR_arg5', 1)

	# ARC-131 VHF FM RADIO (COM3) ... T/R
	pushSeqCmd(dt, 'VHF_ARC_131.MODE-SWITCH-PTR', 1)

	# MASTER ARM ... ON
	pushSeqCmd(dt, 'WEAPON_SYS.ARMED-SWITCH-PTR', 2)

	# ROCKET PAIRS ... 1
	pushSeqCmd(dt, 'WEAPON_SYS.RKT-PAIR-PTR', 1)

	# FLARE DISPENSER ... ARM
	pushSeqCmd(dt, 'XM_130.CHAFF-ARM-SWITCH-PTR', 1)

	# FLARE DISPENSER COUNT ... 30
	for i in range(30):
		pushSeqCmd(dt, 'XM_130.FLARE-PTR_arg452', 0.03)

	pushSeqCmd(dt, 'scriptSpeech', "Manual steps remaining: Check HSI compass sync (backup compass shows current heading).  Set lights, tune radios.")

	return seq


def Shutdown(config, vars, helper, *args, **kwargs):
	seq = []
	dt = 0.3

	pushSeqCmd = helper.makePushSeqCmd(seq)

	pushSeqCmd(0, '', '', "Running Shutdown sequence")

	# THROTTLE ... SET TO IDLE POSITION
	pushSeqCmd(dt, 'ENGINE_INTERFACE.THROTTLE-1-PTR', 0.714) # 0.0 = Max throttle, 0.7143 = Idle stop, ~0.7630 = Engine start position, 1.0 = Min throttle
	pushSeqCmd(3, '', '', 'Wait for engine to spool down a bit.')

	# LOW RPM WARNING AUDIO ... OFF
	pushSeqCmd(dt, 'ENGINE_INTERFACE.LOW-RPM-PTR', 0)

	# IFF MASTER knob ... OFF
	pushSeqCmd(dt, 'IFF.MASTER-CONTROL-PTR', 0) # 0 = OFF, 1 = STBY, 2 = LOW, 3 = NORM, 4 = EMER
	# IFF ON OUT switch ... OUT
	pushSeqCmd(dt, 'IFF.MODE-4-SWITCH-PTR', 0) # 0 = OUT, 1 = ON

	# RADAR ALTIMETER circuit breaker switch... OFF (overhead panel far rear)
	pushSeqCmd(dt, 'RADAR_ALTIMETER.RADAR-ALT-PTR', 0)
	for i in range(11):
		pushSeqCmd(dt, 'RADAR_ALTIMETER.PITCH-LO-ALT-PTR', -0.1)
	for i in range(11):
		pushSeqCmd(dt, 'RADAR_ALTIMETER.PITCH-HI-ALT-PTR_arg448', -0.1)

	# ARC-51BX UHF RADIO (COM1) ... OFF
	pushSeqCmd(dt, 'UHF_ARC_51.FUNCTION-SELECT-SWITCH-PTR', 0)

	# ARC-134 VHF AM RADIO (COM2) ... OFF
	pushSeqCmd(dt, 'VHF_ARC_134.MHZ-SELECTOR-PTR_arg5', 0)

	# ARC-131 VHF FM RADIO (COM3) ... OFF
	pushSeqCmd(dt, 'VHF_ARC_131.MODE-SWITCH-PTR', 0)

	# MASTER ARM ... SAFE
	pushSeqCmd(dt, 'WEAPON_SYS.ARMED-SWITCH-PTR', 0)

	# ROCKET PAIRS ... 0
	pushSeqCmd(dt, 'WEAPON_SYS.RKT-PAIR-PTR', 0)

	# FLARE DISPENSER ... SAFE
	pushSeqCmd(dt, 'XM_130.CHAFF-ARM-SWITCH-PTR', 0)

	# GOVERNOR ... AUTO
	pushSeqCmd(dt, 'ENGINE_INTERFACE.GOV-PTR', 1)

	# HYDRAULIC CONTROL ... OFF
	pushSeqCmd(dt, 'HYDRO_SYS_INTERFACE.HYD-CONT-PTR', 0)

	# FORCE TRIM ... OFF
	pushSeqCmd(dt, 'HYDRO_SYS_INTERFACE.FORCE-TRIM-PTR', 0)

	# Throttle ... Stop
	pushSeqCmd(dt, 'ENGINE_INTERFACE.ENGINE-BTN-1-PTR', 1) # Press
	pushSeqCmd(dt, 'ENGINE_INTERFACE.THROTTLE-1-PTR', 1.0) # 0.0 = Max throttle, 0.7143 = Idle stop, ~0.7630 = Engine start position, 1.0 = Min throttle
	pushSeqCmd(dt, 'ENGINE_INTERFACE.ENGINE-BTN-1-PTR', 0) # Release

	# MAIN FUEL ... OFF
	pushSeqCmd(dt, 'FUELSYS_INTERFACE.FUEL-PTR', 0)

	# INVERTER ... OFF
	pushSeqCmd(dt, 'ELEC_INTERFACE.INVTR-SWITCHER-PTR', 1) # 0 = MAIN ON, 1 = OFF, 2 = SPARE ON

	# MAIN GENERATOR ... OFF
	pushSeqCmd(dt, 'ELEC_INTERFACE.MAIN-GEN-SWITCHER-COVER-PTR', 1) # Cover open (it starts open on cold spawn)
	pushSeqCmd(dt, 'ELEC_INTERFACE.MAIN-GEN-SWITCHER-PTR', 1) # 0 = ON, 1 = OFF, 2 = RESET
	# Leave cover open.

	# STARTER-GENERATOR ... START
	pushSeqCmd(dt, 'ELEC_INTERFACE.STARTER-GEN-SWITCHERr-PTR', 1) # 0 = STBY GEN, 1 = START

	# BATTERY ... OFF
	pushSeqCmd(dt, 'ELEC_INTERFACE.BAT-SWITCHER-PTR', 1) # 0 = ON, 1 = OFF

	# Doors ... Toggle
	pushSeqCmd(dt, 'CPT_MECH.DOOR_L-PTR', 1)
	pushSeqCmd(dt, 'CPT_MECH.DOOR_R-PTR', 1)

	return seq
