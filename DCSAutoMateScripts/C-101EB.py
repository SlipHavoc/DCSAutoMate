# Return a Dictionary of script data.  The 'scripts' key is a list of scripts that users will be selecting from.  Each script has an associated 'function', which is the name of the function in this file that will be called to generate the command sequence, and a dictionary of 'vars' that the user will be prompted to choose from before running the script, and will be passed into the sequence generating function.
def getScriptData():
	return {
		'moduleName': 'C-101EB',
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


	#print(seq)
	return seq


def ColdStart(config, vars, helper, *args, **kwargs):
	seq = []
	dt = 0.2

	pushSeqCmd = helper.makePushSeqCmd(seq)

	tarsynSyncTime = 2 * 60 + 5 # TARSYN sync time, 2m5s, starts when Inverter switch is set to NORM.

	def resetMasterCaution():
		# Reset MASTER WARNING and MASTER CAUTION
		# MASTER WARNING - Reset
		pushSeqCmd(dt, 'SYSTEMS.PNT-FALLO-CP', 1)
		pushSeqCmd(dt, 'SYSTEMS.PNT-FALLO-CP', 0)
		# MASTER CAUTION - Reset
		pushSeqCmd(dt, 'SYSTEMS.PNT-AVISO-CP', 1)
		pushSeqCmd(dt, 'SYSTEMS.PNT-AVISO-CP', 0)

	"""
	def turnOffRadios():
		# ARC-164(V) radio, front instrument panel
		# ARC-164(V) UHF radio - Off
		pushSeqCmd(dt, 'ARC164.PNT-UHF-MS-CP', 0) # 0 = OFF, 1 = MAIN, 2 = BOTH, 3 = ADF

		# ARC-134 radio, right console
		# ARC-134 VHF radio - Off
		pushSeqCmd(dt, 'ARC134.PNT-VHF-PWR-RP', 0)

	"""

	##################################################
	##################################################
	# Start sequence
	pushSeqCmd(0, '', '', "Running Cold Start sequence")
	pushSeqCmd(dt, 'scriptSpeech', 'Set throttle to minimum.')

	# Internal lights
	if vars.get('time') == 'day':
		pushSeqCmd(dt, 'LIGHTS.PNT-INTR-KNB-RP', 1.0)
		pushSeqCmd(dt, 'LIGHTS.PNT-CNS-KNB-RP', 1.0)
		pushSeqCmd(dt, 'LIGHTS.PNT-INTR-KNB-RP-BACK', 1.0)
		pushSeqCmd(dt, 'LIGHTS.PNT-CNS-KNB-RP-BACK', 1.0)
	else:
		pushSeqCmd(dt, 'LIGHTS.PNT-INTR-KNB-RP', 0.5)
		pushSeqCmd(dt, 'LIGHTS.PNT-CNS-KNB-RP', 0.5)
		pushSeqCmd(dt, 'LIGHTS.PNT-INTR-KNB-RP-BACK', 0.5)
		pushSeqCmd(dt, 'LIGHTS.PNT-CNS-KNB-RP-BACK', 0.5)

	# External lights
	# All external lights default to off, so no need to set.

	# Ignition - Off
	pushSeqCmd(dt, 'SYSTEMS.PNT-START-SW-LP', 1) # 0 = CONT (back), 1 = OFF (middle), 2 = START (forward)

	# Parking brake - Set
	pushSeqCmd(dt, 'SYSTEMS.PNT-PARKING-CPL', 1)

	# Ground power supply - On (waiting 13s)
	pushSeqCmd(dt, 'scriptSimCommand', 'ICommandMenuItem12') # Reset comms menu to top level
	pushSeqCmd(dt, 'scriptSimCommand', 'ICommandMenuItem8') # F8 Ground crew
	pushSeqCmd(dt, 'scriptSimCommand', 'ICommandMenuItem2') # F2 Ground power
	pushSeqCmd(dt, 'scriptSimCommand', 'ICommandMenuItem1') # F1 On
	pushSeqCmd(13, '', '', "Ground power is on")

	# Accelerometer - Reset
	pushSeqCmd(dt, 'SYSTEMS.PNT-ACELKNB-CP', 1)
	pushSeqCmd(dt, 'SYSTEMS.PNT-ACELKNB-CP', 0)

	# Oxygen valve lever (Front seat) - Open
	pushSeqCmd(dt, 'SYSTEMS.PNT-OXIGENE-RP', 1)
	# Oxygen valve lever (Rear seat) - Open
	pushSeqCmd(dt, 'SYSTEMS.PNT-OXIGENE-RP-BACK', 1)

	###- START UP
	# Battery switch - On
	pushSeqCmd(dt, 'SYSTEMS.PNT-BATTERY-CPR', 1)

	# Reset MASTER WARNING and MASTER CAUTION
	resetMasterCaution()

	# Radios
	# ARC-164(V) radio, front instrument panel
	# ARC-164(V) UHF radio - On
	pushSeqCmd(dt, 'ARC164.PNT-UHF-MS-CP', 1) # 0 = OFF, 1 = MAIN, 2 = BOTH, 3 = ADF

	# ARC-134 radio, right console
	# ARC-134 VHF radio - On
	pushSeqCmd(dt, 'ARC134.PNT-VHF-PWR-RP', 1)

	# Ground power on
	# GPU - On (3s)
	pushSeqCmd(dt, 'SYSTEMS.PNT-GPU-LP', 1)
	pushSeqCmd(dt, 'SYSTEMS.PNT-GPU-LP', 0)
	pushSeqCmd(3, '', '', "Ground power supply is revved up")

	# Bus tie switch - On
	pushSeqCmd(dt, 'SYSTEMS.PNT-UNIONB-CPR', 1)

	# Reset MASTER WARNING and MASTER CAUTION
	resetMasterCaution()

	# Inverter switch - Normal
	pushSeqCmd(dt, 'SYSTEMS.PNT-CONV-CPR', 1)
	# Waiting for TARSYN syncronization (2m5s)
	pushSeqCmd(dt, 'scriptTimerStart', name='tarsynTimer', duration=tarsynSyncTime)

	# Transfer pump switches - Auto
	pushSeqCmd(dt, 'SYSTEMS.PNT-TRANSF02-LP', 1)
	pushSeqCmd(dt, 'SYSTEMS.PNT-TRANSF03-LP', 1)
	pushSeqCmd(dt, 'SYSTEMS.PNT-TRANSF01-LP', 1)
	pushSeqCmd(dt, 'SYSTEMS.PNT-TRANSF04-LP', 1)

	# Fuselage tank pump button - On
	pushSeqCmd(dt, 'SYSTEMS.PNT-CBOMSUM-LP', 1) # Cover open
	pushSeqCmd(dt, 'SYSTEMS.PNT-BOMSUM-LP', 1)
	pushSeqCmd(dt, 'SYSTEMS.PNT-BOMSUM-LP', 0)
	pushSeqCmd(dt, 'SYSTEMS.PNT-CBOMSUM-LP', 0) # Cover close

	# Fuel shutoff valve button - On (fuel flow enabled)
	pushSeqCmd(dt, 'SYSTEMS.PNT-CLLAVCOM-LP', 1) # Cover open
	pushSeqCmd(dt, 'SYSTEMS.PNT-LLAVCOM-LP', 1)
	pushSeqCmd(dt, 'SYSTEMS.PNT-LLAVCOM-LP', 0)
	pushSeqCmd(dt, 'SYSTEMS.PNT-CLLAVCOM-LP', 0) # Cover close

	# STARTING ENGINE (37s)

	# Ignition switch - Start (2s)
	pushSeqCmd(dt, 'SYSTEMS.PNT-START-SW-LP', 2)
	pushSeqCmd(2, 'SYSTEMS.PNT-START-SW-LP', 1)

	# At 10% N2: power lever - Idle
	pushSeqCmd(5, '', '', "Engine start - 10% N2")
	pushSeqCmd(dt, 'SYSTEMS.PNT-THRT-LP', 1) # 0 = STOP, 1 = IDLE

	# Wait for engine instruments to stabilize (30s)
	pushSeqCmd(30, '', '', "Engine instruments - Stabilized")

	# Ground power off
	# GPU - Off
	pushSeqCmd(dt, 'SYSTEMS.PNT-GPU-LP', 1)
	pushSeqCmd(dt, 'SYSTEMS.PNT-GPU-LP', 0)
	# Ground power supply is off

	# Ground power supply - Off
	pushSeqCmd(dt, 'scriptSimCommand', 'ICommandMenuItem12') # Reset comms menu to top level
	pushSeqCmd(dt, 'scriptSimCommand', 'ICommandMenuItem8') # F8 Ground crew
	pushSeqCmd(dt, 'scriptSimCommand', 'ICommandMenuItem2') # F2 Ground power
	pushSeqCmd(dt, 'scriptSimCommand', 'ICommandMenuItem2') # F2 Off
	pushSeqCmd(13, '', '', "Ground power is off")

	# Generator - Reset, then On
	pushSeqCmd(dt, 'SYSTEMS.PNT-GENL-CPR', 0)
	pushSeqCmd(dt, 'SYSTEMS.PNT-GENL-CPR', 2)

	# IFF
	# IFF Master switch - NORM
	pushSeqCmd(dt, 'SYSTEMS.PNT-MST-KNB-CPD', 1) # 0 = EMER, 1 = NORM, 2 = LOW, 3 = STBY, 4 = OFF
	# IFF Mode 4 switch - ON
	pushSeqCmd(dt, 'SYSTEMS.PNT-IFFCS-CPD', 1)

	# Standby artificial horizon - Uncage
	pushSeqCmd(dt, 'SYSTEMS.PNT-BKADI-K02-CP_arg41', 0) # Misspelling, "BNT" is correct.
	pushSeqCmd(dt, 'SYSTEMS.PNT-BKADI-K02-CP_arg533', 0.5)

	# Flaps - Takeoff
	pushSeqCmd(dt, 'SYSTEMS.PNT-FLAPSH-LP', 1)

	# Canopy - Close and lock
	pushSeqCmd(dt, 'SYSTEMS.PNT-HND-CNPY', 1) # Canopy safety latch
	pushSeqCmd(3.2, 'SYSTEMS.PNT-LOCK-CNPY', 1)

	# Air conditioning - Reset and On
	pushSeqCmd(dt, 'SYSTEMS.PNT-AC-ACOND-RP', 0)
	pushSeqCmd(dt, 'SYSTEMS.PNT-AC-ACOND-RP', 1)
	pushSeqCmd(dt, 'SYSTEMS.PNT-AC-ACOND-RP', 2)

	# Ejection seat safety pin (Front seat) - Remove
	pushSeqCmd(dt, 'SYSTEMS.PNT-SC-ES-ST', 1)
	# Ejection seat safety pin (Rear seat) - Remove
	pushSeqCmd(dt, 'SYSTEMS.PNT-SC-ES-ST-BACK', 1)

	# Wait until the TARSYN sync is complete.
	pushSeqCmd(dt, 'scriptTimerEnd', name='tarsynTimer')

	manualSteps = "Manual steps remaining: Set lights.  Tune radios.  Set navigation system.  Set altimeter to Q F E or Q N H."
	pushSeqCmd(dt, 'scriptSpeech', manualSteps)

	return seq


def HotStart(config, vars, helper, *args, **kwargs):
	seq = []
	dt = 0.2

	pushSeqCmd = helper.makePushSeqCmd(seq)

	pushSeqCmd(0, '', '', "Running Hot Start sequence")

	# Accelerometer - Reset
	pushSeqCmd(dt, 'SYSTEMS.PNT-ACELKNB-CP', 1)
	pushSeqCmd(dt, 'SYSTEMS.PNT-ACELKNB-CP', 0)

	# Radios
	# ARC-164(V) radio, front instrument panel
	# ARC-164(V) UHF radio - On
	pushSeqCmd(dt, 'ARC164.PNT-UHF-MS-CP', 1) # 0 = OFF, 1 = MAIN, 2 = BOTH, 3 = ADF

	# ARC-134 radio, right console
	# ARC-134 VHF radio - On
	pushSeqCmd(dt, 'ARC134.PNT-VHF-PWR-RP', 1)

	# Flaps - Takeoff
	pushSeqCmd(dt, 'SYSTEMS.PNT-FLAPSH-LP', 1)

	manualSteps = "Manual steps remaining: Set lights.  Tune radios.  Set navigation system.  Set altimeter to Q F E or Q N H."
	pushSeqCmd(dt, 'scriptSpeech', manualSteps)

	return seq
