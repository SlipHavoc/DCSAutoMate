# Return a Dictionary of script data.  The 'scripts' key is a list of scripts that users will be selecting from.  Each script has an associated 'function', which is the name of the function in this file that will be called to generate the command sequence, and a dictionary of 'vars' that the user will be prompted to choose from before running the script, and will be passed into the sequence generating function.
def getScriptData():
	return {
		'moduleName': 'AV8BNA',
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
			{
				'name': 'Shutdown',
				'function': 'Shutdown',
				'vars': {},
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

	pushSeqCmd(0, '', '', "Running Test sequence")
	# Test steps here...

	return seq


def ColdStart(config, vars, helper, *args, **kwargs):
	seq = []
	dt = 0.3

	pushSeqCmd = helper.makePushSeqCmd(seq)

	pushSeqCmd(0, '', '', "Running Cold Start sequence")
	pushSeqCmd(dt, 'scriptSpeech', 'Set throttle to minimum.')

	# Canopy - Close (locks automatically)
	pushSeqCmd(dt, 'FLIGHTCONTROLS.canopy_left_handle', 1) # Toggle state
	# DECS - ON
	pushSeqCmd(dt, 'DECS.Switch_DECS', 1)
	# FUEL SHUTOFF - ON
	pushSeqCmd(dt, 'DECS.Handle_FUEL_SHUT_OFF', 1)
	# OXY switch - ON
	pushSeqCmd(dt, 'ECS.Switch_OXY', 1)
	# Flaps power switch - ON
	pushSeqCmd(dt, 'VREST.Switch_FLAP_PWR', 1)

	# BATT switch - BATT
	pushSeqCmd(dt, 'ELECTRIC.Switch_BATT', 2) # 0 = ALERT, 1 = OFF, 2 = BATT

	# Internal lights
	if vars.get('time') == 'day':
		# INST PNL
		pushSeqCmd(dt, 'LTINT.Knob_Instr_Lights', 1.0)
		# CONSL
		pushSeqCmd(dt, 'LTINT.Knob_Console_Lights', 1.0)
		# Left MFD
		pushSeqCmd(dt, 'MPCD_LEFT.Knob_OFF_BRT', 1.0)
		# Right MFD
		pushSeqCmd(dt, 'MPCD_RIGHT.Knob_OFF_BRT', 1.0)
		# HUD
		pushSeqCmd(dt, 'HUDCONTROL.DisplayBRTKnob', 1.0)
		# UFC
		pushSeqCmd(dt, 'UFCCONTROL.Knob_BRT', 1.0)
		# EDP (Engine Display Panel)
		pushSeqCmd(dt, 'EDP.BRT_Knob', 1.0)
		# HUD MODE switch - DAY
		pushSeqCmd(dt, 'HUDCONTROL.DisplayModeSwitch', 0) # 0 = DAY, 1 = AUTO, 2 = NIGHT
	else:
		# INST PNL
		pushSeqCmd(dt, 'LTINT.Knob_Instr_Lights', 0.33)
		# CONSL
		pushSeqCmd(dt, 'LTINT.Knob_Console_Lights', 0.33)
		# Left MFD
		pushSeqCmd(dt, 'MPCD_LEFT.Knob_OFF_BRT', 0.5)
		# Right MFD
		pushSeqCmd(dt, 'MPCD_RIGHT.Knob_OFF_BRT', 0.5)
		# HUD
		pushSeqCmd(dt, 'HUDCONTROL.DisplayBRTKnob', 0.5)
		# UFC
		pushSeqCmd(dt, 'UFCCONTROL.Knob_BRT', 0.33)
		# EDP (Engine Display Panel)
		pushSeqCmd(dt, 'EDP.BRT_Knob', 0.33)
		# HUD MODE switch - NIGHT
		pushSeqCmd(dt, 'HUDCONTROL.DisplayModeSwitch', 2) # 0 = DAY, 1 = AUTO, 2 = NIGHT
		# Dim MPCDs for night.  FIXME The switch is pressed, but nothing changes; you have to press it manually.
		#pushSeqCmd(dt, 'MPCD_LEFT.Switch_DAY_MODE', 2) # Press NGT
		#pushSeqCmd(dt, 'MPCD_LEFT.Switch_DAY_MODE', 1) # Center switch
		#pushSeqCmd(dt, 'MPCD_RIGHT.Switch_DAY_MODE', 2) # Press NGT
		#pushSeqCmd(dt, 'MPCD_RIGHT.Switch_DAY_MODE', 1) # Center switch

	# External lights
	pushSeqCmd(dt, 'LTEXT.Switch_EXT_LT_NORM_NVG', 0) # 0 = OFF, 1 = NVG, 2 = NORM

	# Radio volume
	pushSeqCmd(dt, 'UFCCONTROL.Knob_Comm1_Vol', 0.5)
	pushSeqCmd(dt, 'UFCCONTROL.Knob_Comm2_Vol', 0.5)

	# ICS GND and AUX volume
	# Volume 68% is about lined up with the little mark.
	pushSeqCmd(dt, 'INTERCOM.Knob_GND_VOL', 0.68)
	pushSeqCmd(dt, 'INTERCOM.Knob_AUX_VOL', 0.68)

	# Starting engine
	# ENG ST switch - ENG ST
	pushSeqCmd(dt, 'ELECTRIC.Switch_ENG_START', 1)
	# Master Caution - Reset
	pushSeqCmd(dt, 'LTWCA.Switch_Master_Caution', 1)
	pushSeqCmd(dt, 'LTWCA.Switch_Master_Caution', 0)

	# Wait for 20 seconds for engine starter to spool up...
	pushSeqCmd(20, '', '', 'Engine starter spooled up.')

	# Bump throttle forward past detent.  NOTE Each call only advances a small amount, must repeat 11 times to put the throttle in the correct position.
	for i in range(11):
		pushSeqCmd(dt, 'scriptSimCommand', 'iCommandThrottleIncrease') # Throttle up (Numpad +)

	# Then wait for engine to spool up.
	# Wait for 25 seconds for engine to spool up...
	pushSeqCmd(25, '', '', 'Engine started.')

	# Go to EHSD screen or Left MFD.
	pushSeqCmd(dt, 'MPCD_LEFT.Button_02', 1) # EHSD OSB
	pushSeqCmd(dt, 'MPCD_LEFT.Button_02', 0) # release

	# Set INS to IFA, going through all the other positions on the way.
	for i in range(5):
		pushSeqCmd(dt, 'NAV_INS.Knob_INS_Mode', i)
	# Master Caution - Reset
	pushSeqCmd(dt, 'LTWCA.Switch_Master_Caution', 1)
	pushSeqCmd(dt, 'LTWCA.Switch_Master_Caution', 0)

	# Set EHSD color to be readable in VR.  Leave it at the default color for night.
	if vars.get('time') == 'day':
		pushSeqCmd(dt, 'MPCD_LEFT.Button_03', 1) # MAPM OSB
		pushSeqCmd(dt, 'MPCD_LEFT.Button_03', 0) # release
		pushSeqCmd(dt, 'MPCD_LEFT.Button_17', 1) # COLOR OSB
		pushSeqCmd(dt, 'MPCD_LEFT.Button_17', 0) # release
		pushSeqCmd(dt, 'MPCD_LEFT.Button_17', 1) # COLOR OSB
		pushSeqCmd(dt, 'MPCD_LEFT.Button_17', 0) # release
		pushSeqCmd(dt, 'MPCD_LEFT.Button_17', 1) # COLOR OSB
		pushSeqCmd(dt, 'MPCD_LEFT.Button_17', 0) # release
		pushSeqCmd(dt, 'MPCD_LEFT.Button_17', 1) # COLOR OSB
		pushSeqCmd(dt, 'MPCD_LEFT.Button_17', 0) # release
		pushSeqCmd(dt, 'MPCD_LEFT.Button_03', 1) # MAPM OSB
		pushSeqCmd(dt, 'MPCD_LEFT.Button_03', 0) # release

	# Turn on FLIR, DMT, and chaff/flare dispenser.
	pushSeqCmd(dt, 'NAVFLIR.Switch_FLIR_Power', 1)
	pushSeqCmd(dt, 'DMT.Switch_DMT_Power', 1)
	pushSeqCmd(dt, 'EWS.Knob_EXP', 1) # 0 = OFF, 1 = AUT, 2 = UP, 3 = DWN, 4 = RWR
	# Volume 11141 is equivalent to one mousewheel-up on the knob (powered on, minimum volume)
	pushSeqCmd(dt, 'RWRCONTROL.Knob_RWR', 0.17)

	# Program chaff and flare dispensers to 10x, 1 second intervals
	pushSeqCmd(dt, 'MPCD_LEFT.Button_18', 1) # Menu OSB
	pushSeqCmd(dt, 'MPCD_LEFT.Button_18', 0) # release
	pushSeqCmd(dt, 'MPCD_LEFT.Button_15', 1) # EW OSB
	pushSeqCmd(dt, 'MPCD_LEFT.Button_15', 0) # release
	pushSeqCmd(dt, 'MPCD_LEFT.Button_05', 1) # CHF OSB, changes mode from S (single) to P (program)
	pushSeqCmd(dt, 'MPCD_LEFT.Button_05', 0) # release
	pushSeqCmd(dt, 'MPCD_LEFT.Button_04', 1) # FLR OSB, changes mode from S (single) to P (program), other modes are M, G, R, unknown function
	pushSeqCmd(dt, 'MPCD_LEFT.Button_04', 0) # release
	pushSeqCmd(dt, 'MPCD_LEFT.Button_02', 1) # PROG OSB
	pushSeqCmd(dt, 'MPCD_LEFT.Button_02', 0) # release
	# PROG page starts with CHF selected.  Set salvo quantity to 10.
	pushSeqCmd(dt, 'ODUCONTROL.Button_5', 1) # SQTY ODU OSB
	pushSeqCmd(dt, 'ODUCONTROL.Button_5', 0) # release
	pushSeqCmd(dt, 'UFCCONTROL.Button_1', 1) # UFC button 1
	pushSeqCmd(dt, 'UFCCONTROL.Button_1', 0) # release
	pushSeqCmd(dt, 'UFCCONTROL.Button_0', 1) # UFC button 0
	pushSeqCmd(dt, 'UFCCONTROL.Button_0', 0) # release
	pushSeqCmd(dt, 'UFCCONTROL.Button_ENT', 1) # UFC button 0
	pushSeqCmd(dt, 'UFCCONTROL.Button_ENT', 0) # release
	# Then change to FLR and set quantity to 10.
	pushSeqCmd(dt, 'MPCD_LEFT.Button_08', 1) # FLR OSB
	pushSeqCmd(dt, 'MPCD_LEFT.Button_08', 0) # release
	pushSeqCmd(dt, 'ODUCONTROL.Button_4', 1) # QTY ODU OSB
	pushSeqCmd(dt, 'ODUCONTROL.Button_4', 0) # release
	pushSeqCmd(dt, 'UFCCONTROL.Button_1', 1) # UFC button 1
	pushSeqCmd(dt, 'UFCCONTROL.Button_1', 0) # release
	pushSeqCmd(dt, 'UFCCONTROL.Button_0', 1) # UFC button 0
	pushSeqCmd(dt, 'UFCCONTROL.Button_0', 0) # release
	pushSeqCmd(dt, 'UFCCONTROL.Button_ENT', 1) # UFC button 0
	pushSeqCmd(dt, 'UFCCONTROL.Button_ENT', 0) # release
	# Exit PROG mode
	pushSeqCmd(dt, 'MPCD_LEFT.Button_02', 1) # PROG OSB
	pushSeqCmd(dt, 'MPCD_LEFT.Button_02', 0) # release
	# Return to EHSD page.
	pushSeqCmd(dt, 'MPCD_LEFT.Button_18', 1) # Menu OSB
	pushSeqCmd(dt, 'MPCD_LEFT.Button_18', 0) # release
	pushSeqCmd(dt, 'MPCD_LEFT.Button_02', 1) # EHSD OSB
	pushSeqCmd(dt, 'MPCD_LEFT.Button_02', 0) # release

	# Set Low Altitude Warning to 50 ft.
	pushSeqCmd(dt, 'UFCCONTROL.Button_ALT', 1) # UFC ALT button
	pushSeqCmd(dt, 'UFCCONTROL.Button_ALT', 0) # release
	pushSeqCmd(dt, 'UFCCONTROL.Button_5', 1) # UFC button 5
	pushSeqCmd(dt, 'UFCCONTROL.Button_5', 0) # release
	pushSeqCmd(dt, 'UFCCONTROL.Button_0', 1) # UFC button 0
	pushSeqCmd(dt, 'UFCCONTROL.Button_0', 0) # release
	pushSeqCmd(dt, 'UFCCONTROL.Button_ENT', 1) # UFC button 0
	pushSeqCmd(dt, 'UFCCONTROL.Button_ENT', 0) # release

	# Fuel totalizer to TOT
	pushSeqCmd(dt, 'FQIS.FuelSelector', 1) # Actual values: 0 = INT, 1 = TOT, 2 = FEED, 3 = BIT.  Should be: 0 = OUTBD, 1 = INBD, 2 = WING, 3 = INT, 4 = TOT, 5 = FEED, 6 = BIT

	# Increment 25 times to set bingo to 2500 lbs
	for i in range(25):
		pushSeqCmd(dt, 'FQIS.BingoSet', 0.0488)

	# External lights - NORM (means external light controls will work as expected)
	pushSeqCmd(dt, 'LTEXT.Switch_EXT_LT_NORM_NVG', 2) # 0 = OFF, 1 = NVG, 2 = NORM

	# Ejection seat - Arm
	pushSeqCmd(dt, 'MSC.Seat_SFTY_LVR', 1)

	scriptCompleteSpeech = "Manual steps remaining: Tune radios.  Set laser codes.  Set map markers and import target points."
	if vars.get('time') != 'day':
		scriptCompleteSpeech += "  Set MFDs to night mode."
	pushSeqCmd(dt, 'scriptSpeech', scriptCompleteSpeech)

	return seq


def HotStart(config, vars, helper, *args, **kwargs):
	seq = []
	dt = 0.3

	pushSeqCmd = helper.makePushSeqCmd(seq)

	pushSeqCmd(0, '', '', "Running Hot Start sequence")

	# Internal lights
	if vars.get('time') == 'day':
		pushSeqCmd(dt, 'LTINT.Knob_Instr_Lights', 1.0)
		pushSeqCmd(dt, 'LTINT.Knob_Console_Lights', 1.0)
		pushSeqCmd(dt, 'MPCD_LEFT.Knob_OFF_BRT', 1.0)
		pushSeqCmd(dt, 'MPCD_RIGHT.Knob_OFF_BRT', 1.0)
		pushSeqCmd(dt, 'HUDCONTROL.DisplayBRTKnob', 1.0)
		pushSeqCmd(dt, 'UFCCONTROL.Knob_BRT', 1.0)
		pushSeqCmd(dt, 'EDP.BRT_Knob', 1.0)
	else:
		pushSeqCmd(dt, 'LTINT.Knob_Instr_Lights', 0.5)
		pushSeqCmd(dt, 'LTINT.Knob_Console_Lights', 0.5)
		pushSeqCmd(dt, 'MPCD_LEFT.Knob_OFF_BRT', 1.0)
		pushSeqCmd(dt, 'MPCD_RIGHT.Knob_OFF_BRT', 1.0)
		pushSeqCmd(dt, 'HUDCONTROL.DisplayBRTKnob', 0.5)
		pushSeqCmd(dt, 'UFCCONTROL.Knob_BRT', 0.5)
		pushSeqCmd(dt, 'EDP.BRT_Knob', 0.5)
		# HUD MODE switch
		pushSeqCmd(dt, 'HUDCONTROL.DisplayModeSwitch', 0) # 0 = NIGHT, 1 = AUTO, 2 = DAY
		# Dim MPCDs for night.  FIXME The switch is pressed, but nothing changes; you have to press it manually.
		#pushSeqCmd(dt, 'MPCD_LEFT.Switch_DAY_MODE', 2) # Press NGT
		#pushSeqCmd(dt, 'MPCD_LEFT.Switch_DAY_MODE', 1) # Center switch
		#pushSeqCmd(dt, 'MPCD_RIGHT.Switch_DAY_MODE', 2) # Press NGT
		#pushSeqCmd(dt, 'MPCD_RIGHT.Switch_DAY_MODE', 1) # Center switch

	# External lights
	pushSeqCmd(dt, 'LTEXT.Switch_EXT_LT_NORM_NVG', 0) # 0 = OFF, 1 = NVG, 2 = NORM

	# Volume 68% is about lined up with the little mark.
	pushSeqCmd(dt, 'INTERCOM.Knob_GND_VOL', 0.68)
	pushSeqCmd(dt, 'INTERCOM.Knob_AUX_VOL', 0.68)

	# Set EHSD color to be readable in VR.  Leave it at the default color for night.
	if vars.get('time') == 'day':
		pushSeqCmd(dt, 'MPCD_LEFT.Button_03', 1) # MAPM OSB
		pushSeqCmd(dt, 'MPCD_LEFT.Button_03', 0) # release
		pushSeqCmd(dt, 'MPCD_LEFT.Button_17', 1) # COLOR OSB
		pushSeqCmd(dt, 'MPCD_LEFT.Button_17', 0) # release
		pushSeqCmd(dt, 'MPCD_LEFT.Button_17', 1) # COLOR OSB
		pushSeqCmd(dt, 'MPCD_LEFT.Button_17', 0) # release
		pushSeqCmd(dt, 'MPCD_LEFT.Button_17', 1) # COLOR OSB
		pushSeqCmd(dt, 'MPCD_LEFT.Button_17', 0) # release
		pushSeqCmd(dt, 'MPCD_LEFT.Button_17', 1) # COLOR OSB
		pushSeqCmd(dt, 'MPCD_LEFT.Button_17', 0) # release
		pushSeqCmd(dt, 'MPCD_LEFT.Button_03', 1) # MAPM OSB
		pushSeqCmd(dt, 'MPCD_LEFT.Button_03', 0) # release

	# Turn on FLIR, DMT, and chaff/flare dispenser.
	pushSeqCmd(dt, 'EWS.Knob_EXP', 1) # 0 = OFF, 1 = AUT, 2 = UP, 3 = DWN, 4 = RWR
	# Volume 11141 is equivalent to one mousewheel-up on the knob (powered on, minimum volume)
	pushSeqCmd(dt, 'RWRCONTROL.Knob_RWR', 0.17)

	# Program chaff and flare dispensers to 10x, 1 second intervals
	pushSeqCmd(dt, 'MPCD_LEFT.Button_18', 1) # Menu OSB
	pushSeqCmd(dt, 'MPCD_LEFT.Button_18', 0) # release
	pushSeqCmd(dt, 'MPCD_LEFT.Button_15', 1) # EW OSB
	pushSeqCmd(dt, 'MPCD_LEFT.Button_15', 0) # release
	pushSeqCmd(dt, 'MPCD_LEFT.Button_05', 1) # CHF OSB, changes mode from S (single) to P (program)
	pushSeqCmd(dt, 'MPCD_LEFT.Button_05', 0) # release
	pushSeqCmd(dt, 'MPCD_LEFT.Button_04', 1) # FLR OSB, changes mode from S (single) to P (program), other modes are M, G, R, unknown function
	pushSeqCmd(dt, 'MPCD_LEFT.Button_04', 0) # release
	pushSeqCmd(dt, 'MPCD_LEFT.Button_02', 1) # PROG OSB
	pushSeqCmd(dt, 'MPCD_LEFT.Button_02', 0) # release
	# PROG page starts with CHF selected.  Set salvo quantity to 10.
	pushSeqCmd(dt, 'ODUCONTROL.Button_5', 1) # SQTY ODU OSB
	pushSeqCmd(dt, 'ODUCONTROL.Button_5', 0) # release
	pushSeqCmd(dt, 'UFCCONTROL.Button_1', 1) # UFC button 1
	pushSeqCmd(dt, 'UFCCONTROL.Button_1', 0) # release
	pushSeqCmd(dt, 'UFCCONTROL.Button_0', 1) # UFC button 0
	pushSeqCmd(dt, 'UFCCONTROL.Button_0', 0) # release
	pushSeqCmd(dt, 'UFCCONTROL.Button_ENT', 1) # UFC button 0
	pushSeqCmd(dt, 'UFCCONTROL.Button_ENT', 0) # release
	# Then change to FLR and set quantity to 10.
	pushSeqCmd(dt, 'MPCD_LEFT.Button_08', 1) # FLR OSB
	pushSeqCmd(dt, 'MPCD_LEFT.Button_08', 0) # release
	pushSeqCmd(dt, 'ODUCONTROL.Button_4', 1) # QTY ODU OSB
	pushSeqCmd(dt, 'ODUCONTROL.Button_4', 0) # release
	pushSeqCmd(dt, 'UFCCONTROL.Button_1', 1) # UFC button 1
	pushSeqCmd(dt, 'UFCCONTROL.Button_1', 0) # release
	pushSeqCmd(dt, 'UFCCONTROL.Button_0', 1) # UFC button 0
	pushSeqCmd(dt, 'UFCCONTROL.Button_0', 0) # release
	pushSeqCmd(dt, 'UFCCONTROL.Button_ENT', 1) # UFC button 0
	pushSeqCmd(dt, 'UFCCONTROL.Button_ENT', 0) # release
	# Exit PROG mode
	pushSeqCmd(dt, 'MPCD_LEFT.Button_02', 1) # PROG OSB
	pushSeqCmd(dt, 'MPCD_LEFT.Button_02', 0) # release
	# Return to EHSD page.
	pushSeqCmd(dt, 'MPCD_LEFT.Button_18', 1) # Menu OSB
	pushSeqCmd(dt, 'MPCD_LEFT.Button_18', 0) # release
	pushSeqCmd(dt, 'MPCD_LEFT.Button_02', 1) # EHSD OSB
	pushSeqCmd(dt, 'MPCD_LEFT.Button_02', 0) # release

	# Set Low Altitude Warning to 50 ft.
	pushSeqCmd(dt, 'UFCCONTROL.Button_ALT', 1) # UFC ALT button
	pushSeqCmd(dt, 'UFCCONTROL.Button_ALT', 0) # release
	pushSeqCmd(dt, 'UFCCONTROL.Button_5', 1) # UFC button 5
	pushSeqCmd(dt, 'UFCCONTROL.Button_5', 0) # release
	pushSeqCmd(dt, 'UFCCONTROL.Button_0', 1) # UFC button 0
	pushSeqCmd(dt, 'UFCCONTROL.Button_0', 0) # release
	pushSeqCmd(dt, 'UFCCONTROL.Button_ENT', 1) # UFC button 0
	pushSeqCmd(dt, 'UFCCONTROL.Button_ENT', 0) # release

	# Fuel totalizer to TOT
	pushSeqCmd(dt, 'FQIS.FuelSelector', 1) # Actual values: 0 = INT, 1 = TOT, 2 = FEED, 3 = BIT.  Should be: 0 = OUTBD, 1 = INBD, 2 = WING, 3 = INT, 4 = TOT, 5 = FEED, 6 = BIT

	# Increment 25 times to set bingo to 2500 lbs
	for i in range(25):
		pushSeqCmd(dt, 'FQIS.BingoSet', 0.0488)

	# External lights
	pushSeqCmd(dt, 'LTEXT.Switch_EXT_LT_NORM_NVG', 2) # 0 = OFF, 1 = NVG, 2 = NORM

	scriptCompleteSpeech = "Manual steps remaining: Tune radios.  Set laser codes.  Set map markers and import target points."
	if vars.get('time') != 'day':
		scriptCompleteSpeech += "  Set MFDs to night mode."
	pushSeqCmd(dt, 'scriptSpeech', scriptCompleteSpeech)

	return seq


def Shutdown(config, vars, helper, *args, **kwargs):
	seq = []
	dt = 0.3

	pushSeqCmd = helper.makePushSeqCmd(seq)

	pushSeqCmd(0, '', '', "Running Shutdown sequence")
	pushSeqCmd(dt, 'scriptSpeech', 'Set throttle to minimum.')

	# Ejection seat - Safe
	pushSeqCmd(dt, 'MSC.Seat_SFTY_LVR', 0)

	# Internal lights
	# INST PNL
	pushSeqCmd(dt, 'LTINT.Knob_Instr_Lights', 0)
	# CONSL
	pushSeqCmd(dt, 'LTINT.Knob_Console_Lights', 0)
	# Left MFD
	pushSeqCmd(dt, 'MPCD_LEFT.Knob_OFF_BRT', 0)
	# Right MFD
	pushSeqCmd(dt, 'MPCD_RIGHT.Knob_OFF_BRT', 0)
	# HUD
	pushSeqCmd(dt, 'HUDCONTROL.DisplayBRTKnob', 0)
	# UFC
	pushSeqCmd(dt, 'UFCCONTROL.Knob_BRT', 0)
	# EDP (Engine Display Panel)
	pushSeqCmd(dt, 'EDP.BRT_Knob', 0)
	# HUD MODE switch - DAY
	pushSeqCmd(dt, 'HUDCONTROL.DisplayModeSwitch', 0) # 0 = DAY, 1 = AUTO, 2 = NIGHT

	# Radio volume
	pushSeqCmd(dt, 'UFCCONTROL.Knob_Comm1_Vol', 0)
	pushSeqCmd(dt, 'UFCCONTROL.Knob_Comm2_Vol', 0)

	# ICS GND and AUX volume
	pushSeqCmd(dt, 'INTERCOM.Knob_GND_VOL', 0)
	pushSeqCmd(dt, 'INTERCOM.Knob_AUX_VOL', 0)

	# Turn off FLIR, DMT, and chaff/flare dispenser.
	pushSeqCmd(dt, 'NAVFLIR.Switch_FLIR_Power', 0)
	pushSeqCmd(dt, 'DMT.Switch_DMT_Power', 0)
	pushSeqCmd(dt, 'EWS.Knob_EXP', 0) # 0 = OFF, 1 = AUT, 2 = UP, 3 = DWN, 4 = RWR
	pushSeqCmd(dt, 'RWRCONTROL.Knob_RWR', 0)

	# Set INS to OFF, going through all the other positions on the way.
	for i in reversed(range(5)):
		pushSeqCmd(dt, 'NAV_INS.Knob_INS_Mode', i)

	# Throttle - Cutoff
	pushSeqCmd(dt, 'DECS.Handle_THROTTLE_CUTOFF', 1) # Throttle cutoff lever (RWin+T), 0 = normal, 1 = cutoff

	# ENG ST switch - OFF
	pushSeqCmd(dt, 'ELECTRIC.Switch_ENG_START', 0)

	# Flaps power switch - OFF
	pushSeqCmd(dt, 'VREST.Switch_FLAP_PWR', 0)

	# OXY switch - OFF
	pushSeqCmd(dt, 'ECS.Switch_OXY', 0)

	# FUEL SHUTOFF - OFF
	pushSeqCmd(dt, 'DECS.Handle_FUEL_SHUT_OFF', 0) # FIXME This should work, but requires that the "Fuel Shutoff Lever Release Lock" command be pressed first, and there's no default mapping for that command.

	# DECS - OFF
	pushSeqCmd(dt, 'DECS.Switch_DECS', 0)

	pushSeqCmd(20, '', '', 'Wait for engine to spool down.')

	# BATT switch - OFF
	pushSeqCmd(dt, 'ELECTRIC.Switch_BATT', 1) # 0 = ALERT, 1 = OFF, 2 = BATT

	# Canopy - Unlock
	pushSeqCmd(dt, 'FLIGHTCONTROLS.canopy_lock_lever', 0)

	# Canopy - Open
	pushSeqCmd(dt, 'FLIGHTCONTROLS.canopy_left_handle', 1) # Toggle state

	return seq
