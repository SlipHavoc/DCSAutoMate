# Return a Dictionary of script data.  The 'scripts' key is a list of scripts that users will be selecting from.  Each script has an associated 'function', which is the name of the function in this file that will be called to generate the command sequence, and a dictionary of 'vars' that the user will be prompted to choose from before running the script, and will be passed into the sequence generating function.
def getScriptData():
	return {
		'moduleName': 'A-4E-C',
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
		],
	}

def ColdStart(config, vars, helper, *args, **kwargs):
	seq = []

	pushSeqCmd = helper.makePushSeqCmd(seq)

	dt = 0.3

	pushSeqCmd(0, '', '', "Running Cold Start sequence")
	# Ground power supply - On
	pushSeqCmd(dt, 'scriptSimCommand', 'ICommandMenuItem12') # Reset comms menu to top level
	pushSeqCmd(dt, 'scriptSimCommand', 'ICommandMenuItem8') # F8 Ground crew
	pushSeqCmd(dt, 'scriptSimCommand', 'ICommandMenuItem2') # F2 Ground power
	pushSeqCmd(dt, 'scriptSimCommand', 'ICommandMenuItem1') # F1 On
	pushSeqCmd(15, '', '', "Ground power is on")

	# Interior lights
	pushSeqCmd(dt, 'AVIONICS.PNT_106', 1.0)
	pushSeqCmd(dt, 'AVIONICS.PNT_107', 1.0)

	# Start engine
	pushSeqCmd(dt, 'ENGINE.PNT_100', 1)
	pushSeqCmd(5, 'ENGINE.PNT_80', 1) # IGN at 5% RPM (5 seconds)
	pushSeqCmd(10, 'ENGINE.PNT_80', 2) # IDLE at 15% RPM (10 seconds)
	pushSeqCmd(20, '', '', "Engine at 40% RPM")

	# Ground power supply - Off
	pushSeqCmd(dt, 'scriptSimCommand', 'ICommandMenuItem12') # Reset comms menu to top level
	pushSeqCmd(dt, 'scriptSimCommand', 'ICommandMenuItem8') # F8 Ground crew
	pushSeqCmd(dt, 'scriptSimCommand', 'ICommandMenuItem2') # F2 Ground power
	pushSeqCmd(dt, 'scriptSimCommand', 'ICommandMenuItem2') # F2 Off
	pushSeqCmd(15, '', '', "Ground power is off")

	# NOTE Leave canopy open for rearming.
	#pushSeqCmd(dt, 'Canopy', 0) # Note Propercase, not lowercase.

	pushSeqCmd(dt, 'AVIONICS.PNT_125', 1)
	pushSeqCmd(dt, 'AFCS.PNT_160', 1)
	pushSeqCmd(dt, 'AFCS.PNT_165', 1)
	pushSeqCmd(dt, 'RADAR.PNT_120', 1) # 0 = OFF, 1 = STBY, 2 = SRCH, 3 = TC, 4 = A/G

	# CM, RWR, and ECM
	pushSeqCmd(dt, 'COUNTERMEASURES.PNT_530', 1) # Countermeasures system (chaff)
	pushSeqCmd(dt, 'RWR.PNT_504', 1)
	pushSeqCmd(dt, 'RWR.PNT_501', 1)
	#pushSeqCmd(dt, 'ECM_AUDIO', 1) # 0 = APR 25, 1 = AUDIO ALQ (APR 27)
	pushSeqCmd(dt, 'RWR.PNT_506', 0.5)
	pushSeqCmd(dt, 'RWR.PNT_505', 0.5)
	pushSeqCmd(dt, 'RWR.PNT_502', 2) # 0 = OFF, 1 = STBY, 2 = REC, 3 = RPT

	# UHF radio
	pushSeqCmd(dt, 'RADIO.PNT_372', 1) # 0 = OFF, 1 = T/R, 2 = T/R+G, 3 = ADF

	#for i in range(88):
	#	pushSeqCmd(dt, 'RADAR_ALT_INDEX', -1000)
	pushSeqCmd(dt, 'scriptSpeech', 'Set radar altimeter index')
	pushSeqCmd(3, '', '', 'Waiting for speech to finish')

	# APR-153 Doppler nav
	pushSeqCmd(dt, 'NAV.PNT_170', 1) # 0 = OFF, 1 = STBY, 2 = LAND, 3 = SEA, 4 = TEST
	pushSeqCmd(dt, 'NAV.PNT_176', 2) # 0 = TEST, 1 = OFF, 2 = STBY, 3 = D1, 4 = D2

	pushSeqCmd(dt, 'NAV.PNT_724', 2) # 0 = NAV PAC, 1 = TACAN, 2 = NAV CMPTR
	pushSeqCmd(dt, 'ELECTRIC_SYSTEM.PNT_1251', 1) # 0 = RAM, 1 = NORM
	# ICLS?? Right console far rear, aft of MCL CHNL knob.
	pushSeqCmd(dt, 'MCL.PNT_253', 1)

	pushSeqCmd(dt, 'scriptSpeech', 'Close canopy after rearming.')

	return seq


def HotStart(config, vars, helper, *args, **kwargs):
	seq = []

	pushSeqCmd = helper.makePushSeqCmd(seq)

	dt = 0.3

	pushSeqCmd(0, '', '', "Running Hot Start sequence")
	# Interior lights
	pushSeqCmd(dt, 'AVIONICS.PNT_106', 1.0)
	pushSeqCmd(dt, 'AVIONICS.PNT_107', 1.0)

	# NOTE Canopy needs to be open for rearming.
	pushSeqCmd(dt, 'scriptSpeech', 'Open canopy manually for rearming.')
	# FIXME There doesn't seem to be a mapping for the Canopy Lever in DCS BIOS.  There is a CANOPY_POS, which shows the position, and a CANOPY_SW, but that doesn't change with the cockpit lever position.
	#pushSeqCmd(dt, 'Canopy', 1) # Note Propercase not lowercase.

	# CM, RWR, and ECM
	pushSeqCmd(dt, 'COUNTERMEASURES.PNT_530', 1) # Countermeasures system (chaff)
	pushSeqCmd(dt, 'RWR.PNT_504', 1)
	pushSeqCmd(dt, 'RWR.PNT_501', 1)
	#pushSeqCmd(dt, 'ECM_AUDIO', 1) # 0 = APR 25, 1 = AUDIO ALQ (APR 27)
	pushSeqCmd(dt, 'RWR.PNT_506', 0.25)
	pushSeqCmd(dt, 'RWR.PNT_505', 0.25)
	pushSeqCmd(dt, 'RWR.PNT_502', 2) # 0 = OFF, 1 = STBY, 2 = REC, 3 = RPT

	# UHF radio
	pushSeqCmd(dt, 'RADIO.PNT_372', 1) # 0 = OFF, 1 = T/R, 2 = T/R+G, 3 = ADF

	#for i in range(88):
	#	pushSeqCmd(dt, 'RADAR_ALT_INDEX', -1000)
	pushSeqCmd(dt, 'scriptSpeech', 'Set radar altimeter index')
	pushSeqCmd(3, '', '', 'Waiting for speech to finish')

	pushSeqCmd(dt, 'NAV.PNT_724', 2) # 0 = NAV PAC, 1 = TACAN, 2 = NAV CMPTR
	pushSeqCmd(dt, 'ELECTRIC_SYSTEM.PNT_1251', 1) # 0 = RAM, 1 = NORM

	return seq
