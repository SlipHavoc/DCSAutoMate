# Return a Dictionary of script titles and their corresponding function names.  This is a list of scripts that users will be selecting from.  The module may have other utility functions that will not be run directly by the users.
def getScriptFunctions():
	return {
		'Cold Start': 'ColdStart',
	}

def ColdStart(config):
	seq = []
	seqTime = 0
	dt = 0.3
	
	def pushSeqCmd(dt, cmd, arg, msg = ''):
		nonlocal seq, seqTime
		seqTime += dt
		seq.append({
			'time': round(seqTime, 2),
			'cmd': cmd,
			'arg': arg,
			'msg': msg,
		})
	
	int16 = 65535
	
	pushSeqCmd(0, '', '', "Running Cold Start sequence")
	pushSeqCmd(dt, 'CANOPY_HAND_L', 1)
	pushSeqCmd(dt, 'DECS_SW', 1)
	pushSeqCmd(dt, 'FUEL_SHUTOFF', 1)
	pushSeqCmd(dt, 'O2_SW', 1)
	#pushSeqCmd(dt, 'FUEL_PUMP_L', 2)
	#pushSeqCmd(dt, 'FUEL_PUMP_R', 2)
	#pushSeqCmd(dt, 'YAW_TRIM_SW', 1)
	#pushSeqCmd(dt, 'ANTI_SKID', 1)
	pushSeqCmd(dt, 'FLAP_POWER', 1)
	
	pushSeqCmd(dt, 'BATT_SW', 2)
	# Internal lights
	pushSeqCmd(dt, 'INST_LIGHTS', int16)
	pushSeqCmd(dt, 'CONSOLE_LIGHTS', int16)
	
	pushSeqCmd(dt, 'MPCD_L_BRIGHT', int16)
	pushSeqCmd(dt, 'MPCD_R_BRIGHT', int16)
	pushSeqCmd(dt, 'HUD_BRIGHT', int(int16 * 0.5))
	pushSeqCmd(dt, 'UFC_BRIGHT', int16)
	pushSeqCmd(dt, 'EDP_BRIGHT', int16)
	pushSeqCmd(dt, 'UFC_COM1_VOL', int(int16 * 0.5))
	pushSeqCmd(dt, 'UFC_COM2_VOL', int(int16 * 0.5))
	
	# Volume 68% is about lined up with the little mark.
	pushSeqCmd(dt, 'ICS_GND_VOL', int(int16 * 0.68))
	pushSeqCmd(dt, 'ICS_AUX_VOL', int(int16 * 0.68))
	
	# Starting engine
	pushSeqCmd(dt, 'ENG_START_SW', 1)
	pushSeqCmd(dt, 'M_Caution', 1) # NOTE Case sensitive
	pushSeqCmd(dt, 'M_Caution', 0)
	
	#pushSeqCmd(dt, '', '', 'Wait for 20 seconds for engine starter to spool up...')
	pushSeqCmd(20, '', '', 'Engine starter spooled up.')
	
	# Bump throttle forward past detent.  Note, must hold key down for a bit.
	pushSeqCmd(dt, 'scriptKeyboard', '{VK_ADD down}')
	pushSeqCmd(1, 'scriptKeyboard', '{VK_ADD up}') # Release after 1 second.
	
	# Then wait for engine to spool up.
	#pushSeqCmd(dt, '', '', 'Wait for 25 seconds for engine to spool up...')
	pushSeqCmd(25, '', '', 'Engine started.')
	
	# Go to EHSD screen.
	pushSeqCmd(dt, 'MPCD_L_2', 1)
	pushSeqCmd(dt, 'MPCD_L_2', 0)
	
	# Set INS to IFA, going through all the other positions on the way.
	for i in range(5):
		pushSeqCmd(dt, 'INS_MODE', i)
		
	pushSeqCmd(dt, 'M_Caution', 1) # NOTE Case sensitive
	pushSeqCmd(dt, 'M_Caution', 0)
	
	# Turn on FLIR, DMT, and chaff/flare dispenser.
	pushSeqCmd(dt, 'FLIR', 1)
	pushSeqCmd(dt, 'DMT', 1)
	pushSeqCmd(dt, 'DECOY_CONTROL', 1)
	# Volume 11141 is equivalent to one mousewheel-up on the knob (powered on, minimum volume)
	pushSeqCmd(dt, 'RWR_VOL', 11141)
	
	# Increment 25 times to set bingo to 2500 lbs
	for i in range(25):
		pushSeqCmd(dt, 'BINGO_SET', 'INC')
	
	# External lights
	pushSeqCmd(dt, 'EXT_LIGHTS', 2)
	
	pushSeqCmd(dt, 'SEAT_SAFE_LEVER', 1)
	
	return seq
	