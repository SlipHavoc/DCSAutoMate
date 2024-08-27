# Return a Dictionary of script titles and their corresponding function names.  This is a list of scripts that users will be selecting from.  The module may have other utility functions that will not be run directly by the users.
def getScriptFunctions():
	return {
		'Cold Start': 'ColdStart',
		'Hot Start': 'HotStart',
	}

# Returns 0-65535 scaled by multiple (0-1), eg for 50% call int16(0.5)
def int16(mult = 1):
	int16 = 65535
	return int(mult * int16)

def ColdStart(config):
	seq = []
	seqTime = 0
	
	def pushSeqCmd(dt, cmd, arg, msg = ''):
		nonlocal seq, seqTime
		seqTime += dt
		seq.append({
			'time': round(seqTime, 2),
			'cmd': cmd,
			'arg': arg,
			'msg': msg,
		})
	
	dt = 0.3
	
	pushSeqCmd(0, '', '', "Running Cold Start sequence")
	# Ground power supply - On
	pushSeqCmd(dt, 'scriptKeyboard', '{\ down}{\ up}') # Must have separate down and up to register key press.
	pushSeqCmd(dt, 'scriptKeyboard', '{F8}')
	pushSeqCmd(dt, 'scriptKeyboard', '{F2}')
	pushSeqCmd(dt, 'scriptKeyboard', '{F1}')
	pushSeqCmd(15, '', '', "Ground power is on")

	# Interior lights
	pushSeqCmd(dt, 'LIGHT_INT_INSTR', int16())
	pushSeqCmd(dt, 'LIGHT_INT_CONSOLE', int16())
	
	# Start engine
	pushSeqCmd(dt, 'STARTER_BTN', 1)
	pushSeqCmd(5, 'THROTTLE_CLICK', 1) # IGN at 5% RPM (5 seconds)
	pushSeqCmd(10, 'THROTTLE_CLICK', 2) # IDLE at 15% RPM (10 seconds)
	pushSeqCmd(20, '', '', "Engine at 40% RPM")

	# Ground power supply - Off
	pushSeqCmd(dt, 'scriptKeyboard', '{\ down}{\ up}') # Must have separate down and up to register key press.
	pushSeqCmd(dt, 'scriptKeyboard', '{F8}')
	pushSeqCmd(dt, 'scriptKeyboard', '{F2}')
	pushSeqCmd(dt, 'scriptKeyboard', '{F2}')
	pushSeqCmd(15, '', '', "Ground power is off")

	# NOTE Leave canopy open for rearming.
	#pushSeqCmd(dt, 'Canopy', 0) # Note Propercase, not lowercase.

	pushSeqCmd(dt, 'OXY_SW', 1)
	pushSeqCmd(dt, 'AFCS_STBY', 1)
	pushSeqCmd(dt, 'AFCS_STAB_AUG', 1)
	pushSeqCmd(dt, 'RADAR_MODE', 1) # 0 = OFF, 1 = STBY, 2 = SRCH, 3 = TC, 4 = A/G
	
	# CM, RWR, and ECM
	pushSeqCmd(dt, 'CM_PWR', 1) # Countermeasures system (chaff)
	pushSeqCmd(dt, 'ECM_APR25_PW', 1)
	pushSeqCmd(dt, 'ECM_APR27_PW', 1)
	#pushSeqCmd(dt, 'ECM_AUDIO', 1) # 0 = APR 25, 1 = AUDIO ALQ (APR 27)
	pushSeqCmd(dt, 'ECM_PRF_VOL', int16(0.5))
	pushSeqCmd(dt, 'ECM_MSL_VOL', int16(0.5))
	pushSeqCmd(dt, 'ECM_SEL', 2) # 0 = OFF, 1 = STBY, 2 = REC, 3 = RPT
	
	# UHF radio
	pushSeqCmd(dt, 'ARC51_MODE', 1) # 0 = OFF, 1 = T/R, 2 = T/R+G, 3 = ADF
	
	#for i in range(88):
	#	pushSeqCmd(dt, 'RADAR_ALT_INDEX', -1000)
	pushSeqCmd(dt, 'scriptSpeech', 'Set radar altimeter index')
	pushSeqCmd(3, '', '', 'Waiting for speech to finish')

	# APR-153 Doppler nav
	pushSeqCmd(dt, 'DOPPLER_SEL', 1) # 0 = OFF, 1 = STBY, 2 = LAND, 3 = SEA, 4 = TEST
	pushSeqCmd(dt, 'NAV_SEL', 2) # 0 = TEST, 1 = OFF, 2 = STBY, 3 = D1, 4 = D2

	pushSeqCmd(dt, 'BDHI_MODE', 2) # 0 = NAV PAC, 1 = TACAN, 2 = NAV CMPTR
	pushSeqCmd(dt, 'CABIN_PRESS', 1) # 0 = RAM, 1 = NORM
	# ICLS?? Right console far rear, aft of MCL CHNL knob.
	pushSeqCmd(dt, 'MCL_PWR', 1)

	pushSeqCmd(dt, 'scriptSpeech', 'Close canopy after rearming.')

	return seq

	
def HotStart(config):
	seq = []
	seqTime = 0
	
	def pushSeqCmd(dt, cmd, arg, msg = ''):
		nonlocal seq, seqTime
		seqTime += dt
		seq.append({
			'time': round(seqTime, 2),
			'cmd': cmd,
			'arg': arg,
			'msg': msg,
		})
	
	dt = 0.3
	
	pushSeqCmd(0, '', '', "Running Hot Start sequence")
	# Interior lights
	pushSeqCmd(dt, 'LIGHT_INT_INSTR', int16())
	pushSeqCmd(dt, 'LIGHT_INT_CONSOLE', int16())
	
	# NOTE Canopy open for rearming.
	pushSeqCmd(dt, 'Canopy', 1) # Note Propercase, not lowercase.

	# CM, RWR, and ECM
	pushSeqCmd(dt, 'CM_PWR', 1) # Countermeasures system (chaff)
	pushSeqCmd(dt, 'ECM_APR25_PW', 1)
	pushSeqCmd(dt, 'ECM_APR27_PW', 1)
	#pushSeqCmd(dt, 'ECM_AUDIO', 1) # 0 = APR 25, 1 = AUDIO ALQ (APR 27)
	pushSeqCmd(dt, 'ECM_PRF_VOL', int16(0.25))
	pushSeqCmd(dt, 'ECM_MSL_VOL', int16(0.25))
	pushSeqCmd(dt, 'ECM_SEL', 2) # 0 = OFF, 1 = STBY, 2 = REC, 3 = RPT
	
	# UHF radio
	pushSeqCmd(dt, 'ARC51_MODE', 1) # 0 = OFF, 1 = T/R, 2 = T/R+G, 3 = ADF
	
	#for i in range(88):
	#	pushSeqCmd(dt, 'RADAR_ALT_INDEX', -1000)
	pushSeqCmd(dt, 'scriptSpeech', 'Set radar altimeter index')
	pushSeqCmd(3, '', '', 'Waiting for speech to finish')

	pushSeqCmd(dt, 'BDHI_MODE', 2) # 0 = NAV PAC, 1 = TACAN, 2 = NAV CMPTR
	pushSeqCmd(dt, 'CABIN_PRESS', 1) # 0 = RAM, 1 = NORM

	pushSeqCmd(dt, 'scriptSpeech', 'Close canopy after rearming.')

	return seq
	