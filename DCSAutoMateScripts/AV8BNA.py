# Return a Dictionary of script data.  The 'scripts' key is a list of scripts that users will be selecting from.  Each script has an associated 'function', which is the name of the function in this file that will be called to generate the command sequence, and a dictionary of 'vars' that the user will be prompted to choose from before running the script, and will be passed into the sequence generating function.
def getScriptData():
	return {
		'scripts': [
			{
				'name': 'Cold Start',
				'function': 'ColdStart',
				'vars': {
					'Time': ['Day', 'Night'],
				},
			},
			{
				'name': 'Hot Start',
				'function': 'HotStart',
				'vars': {
					'Time': ['Day', 'Night'],
				},
			},
			{
				'name': 'Shutdown',
				'function': 'Shutdown',
				'vars': {},
			},
			#{
			#	'name': 'Test',
			#	'function': 'Test',
			#	'vars': {
			#		'Time': ['Day', 'Night'],
			#	},
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

	pushSeqCmd(0, '', '', "Running Test sequence")
	# Test steps here...

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
	pushSeqCmd(dt, 'scriptSpeech', 'Set throttle to minimum.')

	# Canopy - Close (locks automatically)
	pushSeqCmd(dt, 'CANOPY_HAND_L', 1) # Toggle state
	# DECS - ON
	pushSeqCmd(dt, 'DECS_SW', 1)
	# FUEL SHUTOFF - ON
	pushSeqCmd(dt, 'FUEL_SHUTOFF', 1)
	# OXY switch - ON
	pushSeqCmd(dt, 'O2_SW', 1)
	# Flaps power switch - ON
	pushSeqCmd(dt, 'FLAP_POWER', 1)

	# BATT switch - BATT
	pushSeqCmd(dt, 'BATT_SW', 2) # 0 = ALERT, 1 = OFF, 2 = BATT

	# Internal lights
	if vars.get('Time') == 'Day':
		# INST PNL
		pushSeqCmd(dt, 'INST_LIGHTS', int16())
		# CONSL
		pushSeqCmd(dt, 'CONSOLE_LIGHTS', int16())
		# Left MFD
		pushSeqCmd(dt, 'MPCD_L_BRIGHT', int16())
		# Right MFD
		pushSeqCmd(dt, 'MPCD_R_BRIGHT', int16())
		# HUD
		pushSeqCmd(dt, 'HUD_BRIGHT', int16())
		# UFC
		pushSeqCmd(dt, 'UFC_BRIGHT', int16())
		# EDP (Engine Display Panel)
		pushSeqCmd(dt, 'EDP_BRIGHT', int16())
		# HUD MODE switch - DAY
		pushSeqCmd(dt, 'HUD_MODE', 0) # 0 = DAY, 1 = AUTO, 2 = NIGHT
	else:
		# INST PNL
		pushSeqCmd(dt, 'INST_LIGHTS', int16(0.33))
		# CONSL
		pushSeqCmd(dt, 'CONSOLE_LIGHTS', int16(0.33))
		# Left MFD
		pushSeqCmd(dt, 'MPCD_L_BRIGHT', int16(0.5))
		# Right MFD
		pushSeqCmd(dt, 'MPCD_R_BRIGHT', int16(0.5))
		# HUD
		pushSeqCmd(dt, 'HUD_BRIGHT', int16(0.5))
		# UFC
		pushSeqCmd(dt, 'UFC_BRIGHT', int16(0.33))
		# EDP (Engine Display Panel)
		pushSeqCmd(dt, 'EDP_BRIGHT', int16(0.33))
		# HUD MODE switch - NIGHT
		pushSeqCmd(dt, 'HUD_MODE', 2) # 0 = DAY, 1 = AUTO, 2 = NIGHT
		# Dim MPCDs for night.  FIXME The switch is pressed, but nothing changes; you have to press it manually.
		#pushSeqCmd(dt, 'MPCD_L_DAY_NIGHT', 2) # Press NGT
		#pushSeqCmd(dt, 'MPCD_L_DAY_NIGHT', 1) # Center switch
		#pushSeqCmd(dt, 'MPCD_R_DAY_NIGHT', 2) # Press NGT
		#pushSeqCmd(dt, 'MPCD_R_DAY_NIGHT', 1) # Center switch

	# External lights
	pushSeqCmd(dt, 'EXT_LIGHTS', 0) # 0 = OFF, 1 = NVG, 2 = NORM

	# Radio volume
	pushSeqCmd(dt, 'UFC_COM1_VOL', int16(0.5))
	pushSeqCmd(dt, 'UFC_COM2_VOL', int16(0.5))

	# ICS GND and AUX volume
	# Volume 68% is about lined up with the little mark.
	pushSeqCmd(dt, 'ICS_GND_VOL', int16(0.68))
	pushSeqCmd(dt, 'ICS_AUX_VOL', int16(0.68))

	# Starting engine
	# ENG ST switch - ENG ST
	pushSeqCmd(dt, 'ENG_START_SW', 1)
	# Master Caution - Reset
	pushSeqCmd(dt, 'M_Caution', 1) # NOTE Case sensitive
	pushSeqCmd(dt, 'M_Caution', 0)

	# Wait for 20 seconds for engine starter to spool up...
	pushSeqCmd(20, '', '', 'Engine starter spooled up.')

	# Bump throttle forward past detent.  Note, must hold key down for a bit.
	pushSeqCmd(dt, 'scriptKeyboard', 'add down') # Numpad +
	pushSeqCmd(1, 'scriptKeyboard', 'add up') # Numpad +.  Release after 1 second.

	# Then wait for engine to spool up.
	# Wait for 25 seconds for engine to spool up...
	pushSeqCmd(25, '', '', 'Engine started.')

	# Go to EHSD screen or Left MFD.
	pushSeqCmd(dt, 'MPCD_L_2', 1) # EHSD OSB
	pushSeqCmd(dt, 'MPCD_L_2', 0) # release

	# Set INS to IFA, going through all the other positions on the way.
	for i in range(5):
		pushSeqCmd(dt, 'INS_MODE', i)
	# Master Caution - Reset
	pushSeqCmd(dt, 'M_Caution', 1) # NOTE Case sensitive
	pushSeqCmd(dt, 'M_Caution', 0)

	# Set EHSD color to be readable in VR.  Leave it at the default color for night.
	if vars.get('Time') == 'Day':
		pushSeqCmd(dt, 'MPCD_L_3', 1) # MAPM OSB
		pushSeqCmd(dt, 'MPCD_L_3', 0) # release
		pushSeqCmd(dt, 'MPCD_L_17', 1) # COLOR OSB
		pushSeqCmd(dt, 'MPCD_L_17', 0) # release
		pushSeqCmd(dt, 'MPCD_L_17', 1) # COLOR OSB
		pushSeqCmd(dt, 'MPCD_L_17', 0) # release
		pushSeqCmd(dt, 'MPCD_L_17', 1) # COLOR OSB
		pushSeqCmd(dt, 'MPCD_L_17', 0) # release
		pushSeqCmd(dt, 'MPCD_L_17', 1) # COLOR OSB
		pushSeqCmd(dt, 'MPCD_L_17', 0) # release
		pushSeqCmd(dt, 'MPCD_L_3', 1) # MAPM OSB
		pushSeqCmd(dt, 'MPCD_L_3', 0) # release

	# Turn on FLIR, DMT, and chaff/flare dispenser.
	pushSeqCmd(dt, 'FLIR', 1)
	pushSeqCmd(dt, 'DMT', 1)
	pushSeqCmd(dt, 'DECOY_CONTROL', 1) # 0 = OFF, 1 = AUT, 2 = UP, 3 = DWN, 4 = RWR
	# Volume 11141 is equivalent to one mousewheel-up on the knob (powered on, minimum volume)
	pushSeqCmd(dt, 'RWR_VOL', 11141)

	# Program chaff and flare dispensers to 10x, 1 second intervals
	pushSeqCmd(dt, 'MPCD_L_18', 1) # Menu OSB
	pushSeqCmd(dt, 'MPCD_L_18', 0) # release
	pushSeqCmd(dt, 'MPCD_L_15', 1) # EW OSB
	pushSeqCmd(dt, 'MPCD_L_15', 0) # release
	pushSeqCmd(dt, 'MPCD_L_5', 1) # CHF OSB, changes mode from S (single) to P (program)
	pushSeqCmd(dt, 'MPCD_L_5', 0) # release
	pushSeqCmd(dt, 'MPCD_L_4', 1) # FLR OSB, changes mode from S (single) to P (program), other modes are M, G, R, unknown function
	pushSeqCmd(dt, 'MPCD_L_4', 0) # release
	pushSeqCmd(dt, 'MPCD_L_2', 1) # PROG OSB
	pushSeqCmd(dt, 'MPCD_L_2', 0) # release
	# PROG page starts with CHF selected.  Set salvo quantity to 10.
	pushSeqCmd(dt, 'ODU_OPT5', 1) # SQTY ODU OSB
	pushSeqCmd(dt, 'ODU_OPT5', 0) # release
	pushSeqCmd(dt, 'UFC_B1', 1) # UFC button 1
	pushSeqCmd(dt, 'UFC_B1', 0) # release
	pushSeqCmd(dt, 'UFC_B0', 1) # UFC button 0
	pushSeqCmd(dt, 'UFC_B0', 0) # release
	pushSeqCmd(dt, 'UFC_ENTER', 1) # UFC button 0
	pushSeqCmd(dt, 'UFC_ENTER', 0) # release
	# Then change to FLR and set quantity to 10.
	pushSeqCmd(dt, 'MPCD_L_8', 1) # FLR OSB
	pushSeqCmd(dt, 'MPCD_L_8', 0) # release
	pushSeqCmd(dt, 'ODU_OPT4', 1) # QTY ODU OSB
	pushSeqCmd(dt, 'ODU_OPT4', 0) # release
	pushSeqCmd(dt, 'UFC_B1', 1) # UFC button 1
	pushSeqCmd(dt, 'UFC_B1', 0) # release
	pushSeqCmd(dt, 'UFC_B0', 1) # UFC button 0
	pushSeqCmd(dt, 'UFC_B0', 0) # release
	pushSeqCmd(dt, 'UFC_ENTER', 1) # UFC button 0
	pushSeqCmd(dt, 'UFC_ENTER', 0) # release
	# Exit PROG mode
	pushSeqCmd(dt, 'MPCD_L_2', 1) # PROG OSB
	pushSeqCmd(dt, 'MPCD_L_2', 0) # release
	# Return to EHSD page.
	pushSeqCmd(dt, 'MPCD_L_18', 1) # Menu OSB
	pushSeqCmd(dt, 'MPCD_L_18', 0) # release
	pushSeqCmd(dt, 'MPCD_L_2', 1) # EHSD OSB
	pushSeqCmd(dt, 'MPCD_L_2', 0) # release

	# Set Low Altitude Warning to 50 ft.
	pushSeqCmd(dt, 'UFC_ALT', 1) # UFC ALT button
	pushSeqCmd(dt, 'UFC_ALT', 0) # release
	pushSeqCmd(dt, 'UFC_B5', 1) # UFC button 5
	pushSeqCmd(dt, 'UFC_B5', 0) # release
	pushSeqCmd(dt, 'UFC_B0', 1) # UFC button 0
	pushSeqCmd(dt, 'UFC_B0', 0) # release
	pushSeqCmd(dt, 'UFC_ENTER', 1) # UFC button 0
	pushSeqCmd(dt, 'UFC_ENTER', 0) # release

	# Fuel totalizer to TOT
	pushSeqCmd(dt, 'FUEL_SEL', 1) # Actual values: 0 = INT, 1 = TOT, 2 = FEED, 3 = BIT.  Should be: 0 = OUTBD, 1 = INBD, 2 = WING, 3 = INT, 4 = TOT, 5 = FEED, 6 = BIT

	# Increment 25 times to set bingo to 2500 lbs
	for i in range(25):
		pushSeqCmd(dt, 'BINGO_SET', '+3200')

	# External lights - NORM (means external light controls will work as expected)
	pushSeqCmd(dt, 'EXT_LIGHTS', 2) # 0 = OFF, 1 = NVG, 2 = NORM

	# Ejection seat - Arm
	pushSeqCmd(dt, 'SEAT_SAFE_LEVER', 1)

	scriptCompleteSpeech = "Manual steps remaining: Tune radios.  Set laser codes.  Set map markers and import target points."
	if vars.get('Time') != 'Day':
		scriptCompleteSpeech += "  Set MFDs to night mode."
	pushSeqCmd(dt, 'scriptSpeech', scriptCompleteSpeech)

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

	# Internal lights
	if vars.get('Time') == 'Day':
		pushSeqCmd(dt, 'INST_LIGHTS', int16())
		pushSeqCmd(dt, 'CONSOLE_LIGHTS', int16())
		pushSeqCmd(dt, 'MPCD_L_BRIGHT', int16())
		pushSeqCmd(dt, 'MPCD_R_BRIGHT', int16())
		pushSeqCmd(dt, 'HUD_BRIGHT', int16())
		pushSeqCmd(dt, 'UFC_BRIGHT', int16())
		pushSeqCmd(dt, 'EDP_BRIGHT', int16())
	else:
		pushSeqCmd(dt, 'INST_LIGHTS', int16(0.5))
		pushSeqCmd(dt, 'CONSOLE_LIGHTS', int16(0.5))
		pushSeqCmd(dt, 'MPCD_L_BRIGHT', int16())
		pushSeqCmd(dt, 'MPCD_R_BRIGHT', int16())
		pushSeqCmd(dt, 'HUD_BRIGHT', int16(0.5))
		pushSeqCmd(dt, 'UFC_BRIGHT', int16(0.5))
		pushSeqCmd(dt, 'EDP_BRIGHT', int16(0.5))
		# HUD MODE switch
		pushSeqCmd(dt, 'HUD_MODE', 0) # 0 = NIGHT, 1 = AUTO, 2 = DAY
		# Dim MPCDs for night.  FIXME The switch is pressed, but nothing changes; you have to press it manually.
		#pushSeqCmd(dt, 'MPCD_L_DAY_NIGHT', 2) # Press NGT
		#pushSeqCmd(dt, 'MPCD_L_DAY_NIGHT', 1) # Center switch
		#pushSeqCmd(dt, 'MPCD_R_DAY_NIGHT', 2) # Press NGT
		#pushSeqCmd(dt, 'MPCD_R_DAY_NIGHT', 1) # Center switch

	# External lights
	pushSeqCmd(dt, 'EXT_LIGHTS', 0) # 0 = OFF, 1 = NVG, 2 = NORM

	# Volume 68% is about lined up with the little mark.
	pushSeqCmd(dt, 'ICS_GND_VOL', int16(0.68))
	pushSeqCmd(dt, 'ICS_AUX_VOL', int16(0.68))

	# Set EHSD color to be readable in VR.  Leave it at the default color for night.
	if vars.get('Time') == 'Day':
		pushSeqCmd(dt, 'MPCD_L_3', 1) # MAPM OSB
		pushSeqCmd(dt, 'MPCD_L_3', 0) # release
		pushSeqCmd(dt, 'MPCD_L_17', 1) # COLOR OSB
		pushSeqCmd(dt, 'MPCD_L_17', 0) # release
		pushSeqCmd(dt, 'MPCD_L_17', 1) # COLOR OSB
		pushSeqCmd(dt, 'MPCD_L_17', 0) # release
		pushSeqCmd(dt, 'MPCD_L_17', 1) # COLOR OSB
		pushSeqCmd(dt, 'MPCD_L_17', 0) # release
		pushSeqCmd(dt, 'MPCD_L_17', 1) # COLOR OSB
		pushSeqCmd(dt, 'MPCD_L_17', 0) # release
		pushSeqCmd(dt, 'MPCD_L_3', 1) # MAPM OSB
		pushSeqCmd(dt, 'MPCD_L_3', 0) # release

	# Turn on FLIR, DMT, and chaff/flare dispenser.
	pushSeqCmd(dt, 'DECOY_CONTROL', 1) # 0 = OFF, 1 = AUT, 2 = UP, 3 = DWN, 4 = RWR
	# Volume 11141 is equivalent to one mousewheel-up on the knob (powered on, minimum volume)
	pushSeqCmd(dt, 'RWR_VOL', 11141)

	# Program chaff and flare dispensers to 10x, 1 second intervals
	pushSeqCmd(dt, 'MPCD_L_18', 1) # Menu OSB
	pushSeqCmd(dt, 'MPCD_L_18', 0) # release
	pushSeqCmd(dt, 'MPCD_L_15', 1) # EW OSB
	pushSeqCmd(dt, 'MPCD_L_15', 0) # release
	pushSeqCmd(dt, 'MPCD_L_5', 1) # CHF OSB, changes mode from S (single) to P (program)
	pushSeqCmd(dt, 'MPCD_L_5', 0) # release
	pushSeqCmd(dt, 'MPCD_L_4', 1) # FLR OSB, changes mode from S (single) to P (program), other modes are M, G, R, unknown function
	pushSeqCmd(dt, 'MPCD_L_4', 0) # release
	pushSeqCmd(dt, 'MPCD_L_2', 1) # PROG OSB
	pushSeqCmd(dt, 'MPCD_L_2', 0) # release
	# PROG page starts with CHF selected.  Set salvo quantity to 10.
	pushSeqCmd(dt, 'ODU_OPT5', 1) # SQTY ODU OSB
	pushSeqCmd(dt, 'ODU_OPT5', 0) # release
	pushSeqCmd(dt, 'UFC_B1', 1) # UFC button 1
	pushSeqCmd(dt, 'UFC_B1', 0) # release
	pushSeqCmd(dt, 'UFC_B0', 1) # UFC button 0
	pushSeqCmd(dt, 'UFC_B0', 0) # release
	pushSeqCmd(dt, 'UFC_ENTER', 1) # UFC button 0
	pushSeqCmd(dt, 'UFC_ENTER', 0) # release
	# Then change to FLR and set quantity to 10.
	pushSeqCmd(dt, 'MPCD_L_8', 1) # FLR OSB
	pushSeqCmd(dt, 'MPCD_L_8', 0) # release
	pushSeqCmd(dt, 'ODU_OPT4', 1) # QTY ODU OSB
	pushSeqCmd(dt, 'ODU_OPT4', 0) # release
	pushSeqCmd(dt, 'UFC_B1', 1) # UFC button 1
	pushSeqCmd(dt, 'UFC_B1', 0) # release
	pushSeqCmd(dt, 'UFC_B0', 1) # UFC button 0
	pushSeqCmd(dt, 'UFC_B0', 0) # release
	pushSeqCmd(dt, 'UFC_ENTER', 1) # UFC button 0
	pushSeqCmd(dt, 'UFC_ENTER', 0) # release
	# Exit PROG mode
	pushSeqCmd(dt, 'MPCD_L_2', 1) # PROG OSB
	pushSeqCmd(dt, 'MPCD_L_2', 0) # release
	# Return to EHSD page.
	pushSeqCmd(dt, 'MPCD_L_18', 1) # Menu OSB
	pushSeqCmd(dt, 'MPCD_L_18', 0) # release
	pushSeqCmd(dt, 'MPCD_L_2', 1) # EHSD OSB
	pushSeqCmd(dt, 'MPCD_L_2', 0) # release

	# Set Low Altitude Warning to 50 ft.
	pushSeqCmd(dt, 'UFC_ALT', 1) # UFC ALT button
	pushSeqCmd(dt, 'UFC_ALT', 0) # release
	pushSeqCmd(dt, 'UFC_B5', 1) # UFC button 5
	pushSeqCmd(dt, 'UFC_B5', 0) # release
	pushSeqCmd(dt, 'UFC_B0', 1) # UFC button 0
	pushSeqCmd(dt, 'UFC_B0', 0) # release
	pushSeqCmd(dt, 'UFC_ENTER', 1) # UFC button 0
	pushSeqCmd(dt, 'UFC_ENTER', 0) # release

	# Fuel totalizer to TOT
	pushSeqCmd(dt, 'FUEL_SEL', 1) # Actual values: 0 = INT, 1 = TOT, 2 = FEED, 3 = BIT.  Should be: 0 = OUTBD, 1 = INBD, 2 = WING, 3 = INT, 4 = TOT, 5 = FEED, 6 = BIT

	# Increment 25 times to set bingo to 2500 lbs
	for i in range(25):
		pushSeqCmd(dt, 'BINGO_SET', '+3200')

	# External lights
	pushSeqCmd(dt, 'EXT_LIGHTS', 2) # 0 = OFF, 1 = NVG, 2 = NORM

	scriptCompleteSpeech = "Manual steps remaining: Tune radios.  Set laser codes.  Set map markers and import target points."
	if vars.get('Time') != 'Day':
		scriptCompleteSpeech += "  Set MFDs to night mode."
	pushSeqCmd(dt, 'scriptSpeech', scriptCompleteSpeech)

	return seq


def Shutdown(config, vars):
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
	pushSeqCmd(dt, 'scriptSpeech', 'Set throttle to minimum.')

	# Ejection seat - Safe
	pushSeqCmd(dt, 'SEAT_SAFE_LEVER', 0)

	# Internal lights
	# INST PNL
	pushSeqCmd(dt, 'INST_LIGHTS', 0)
	# CONSL
	pushSeqCmd(dt, 'CONSOLE_LIGHTS', 0)
	# Left MFD
	pushSeqCmd(dt, 'MPCD_L_BRIGHT', 0)
	# Right MFD
	pushSeqCmd(dt, 'MPCD_R_BRIGHT', 0)
	# HUD
	pushSeqCmd(dt, 'HUD_BRIGHT', 0)
	# UFC
	pushSeqCmd(dt, 'UFC_BRIGHT', 0)
	# EDP (Engine Display Panel)
	pushSeqCmd(dt, 'EDP_BRIGHT', 0)
	# HUD MODE switch - DAY
	pushSeqCmd(dt, 'HUD_MODE', 0) # 0 = DAY, 1 = AUTO, 2 = NIGHT

	# Radio volume
	pushSeqCmd(dt, 'UFC_COM1_VOL', 0)
	pushSeqCmd(dt, 'UFC_COM2_VOL', 0)

	# ICS GND and AUX volume
	pushSeqCmd(dt, 'ICS_GND_VOL', 0)
	pushSeqCmd(dt, 'ICS_AUX_VOL', 0)

	# Turn off FLIR, DMT, and chaff/flare dispenser.
	pushSeqCmd(dt, 'FLIR', 0)
	pushSeqCmd(dt, 'DMT', 0)
	pushSeqCmd(dt, 'DECOY_CONTROL', 0) # 0 = OFF, 1 = AUT, 2 = UP, 3 = DWN, 4 = RWR
	pushSeqCmd(dt, 'RWR_VOL', 0)

	# Set INS to OFF, going through all the other positions on the way.
	for i in reversed(range(5)):
		pushSeqCmd(dt, 'INS_MODE', i)

	# Throttle - Cutoff
	pushSeqCmd(dt, 'scriptKeyboard', 'RWin down')
	pushSeqCmd(dt, 'scriptKeyboard', 't')
	pushSeqCmd(dt, 'scriptKeyboard', 'RWin up')

	# ENG ST switch - OFF
	pushSeqCmd(dt, 'ENG_START_SW', 0)

	# Flaps power switch - OFF
	pushSeqCmd(dt, 'FLAP_POWER', 0)

	# OXY switch - OFF
	pushSeqCmd(dt, 'O2_SW', 0)

	# FUEL SHUTOFF - OFF
	pushSeqCmd(dt, 'FUEL_SHUTOFF', 0) # FIXME This should work, but requires that the "Fuel Shutoff Lever Release Lock" command be pressed first, and there's no default mapping for that command.

	# DECS - OFF
	pushSeqCmd(dt, 'DECS_SW', 0)

	pushSeqCmd(20, '', '', 'Wait for engine to spool down.')

	# BATT switch - OFF
	pushSeqCmd(dt, 'BATT_SW', 1) # 0 = ALERT, 1 = OFF, 2 = BATT

	# Canopy - Unlock
	pushSeqCmd(dt, 'CANOPY_LOCK', 0)

	# Canopy - Open
	pushSeqCmd(dt, 'CANOPY_HAND_L', 1) # Toggle state

	return seq
