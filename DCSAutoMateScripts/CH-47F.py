# Return a Dictionary of script data.  The 'scripts' key is a list of scripts that users will be selecting from.  Each script has an associated 'function', which is the name of the function in this file that will be called to generate the command sequence, and a dictionary of 'vars' that the user will be prompted to choose from before running the script, and will be passed into the sequence generating function.
def getScriptData():
	return {
		'moduleName': 'CH-47Fbl1',
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


def getInfo():
	return ''

def Test(config, vars, helper, *args, **kwargs):
	seq = []
	dt = 0.3

	pushSeqCmd = helper.makePushSeqCmd(seq)

	# Test code here...
	pushSeqCmd(0, '', '', "Running Test sequence")

	return seq


###############################################################################
###############################################################################
def ColdStart(config, vars, helper, *args, **kwargs):
	seq = []
	dt = 0.3

	pushSeqCmd = helper.makePushSeqCmd(seq)


	# Start sequence
	pushSeqCmd(0, '', '', "Running Cold Start sequence")
	pushSeqCmd(dt, 'scriptSpeech', 'Set collective full down.')

	# MFDs default to NORM on cold start.  For night, set to NVG.
	if vars['time'] == 'day':
		# Set MFDs to NORM
		# Pilot Inboard MFD
		pushSeqCmd(dt, 'MFD_PILOT_INBOARD.MFD-PL-PWR-902', 2)   # 0 = OFF, 1 = NVG, 2 = NORM
		# Pilot Outboard MFD
		pushSeqCmd(dt, 'MFD_PILOT_OUTBOARD.MFD-PR-PWR-938', 2)  # 0 = OFF, 1 = NVG, 2 = NORM
		# Copilot Inboard MFD
		pushSeqCmd(dt, 'MFD_COPILOT_INBOARD.MFD-CR-PWR-830', 2) # 0 = OFF, 1 = NVG, 2 = NORM
		# Copilot Outboard MFD
		pushSeqCmd(dt, 'MFD_COPILOT_OUTBOARD.MFD-CL-PWR-794', 2)# 0 = OFF, 1 = NVG, 2 = NORM
		# Center MFD
		pushSeqCmd(dt, 'MFD_CENTER.MFD-CTR-PWR-866', 2)   # 0 = OFF, 1 = NVG, 2 = NORM
	else:
		# Set MFDs to NVG
		# Pilot Inboard MFD
		pushSeqCmd(dt, 'MFD_PILOT_INBOARD.MFD-PL-PWR-902', 1)   # 0 = OFF, 1 = NVG, 2 = NORM
		# Pilot Outboard MFD
		pushSeqCmd(dt, 'MFD_PILOT_OUTBOARD.MFD-PR-PWR-938', 1)  # 0 = OFF, 1 = NVG, 2 = NORM
		# Copilot Inboard MFD
		pushSeqCmd(dt, 'MFD_COPILOT_INBOARD.MFD-CR-PWR-830', 1) # 0 = OFF, 1 = NVG, 2 = NORM
		# Copilot Outboard MFD
		pushSeqCmd(dt, 'MFD_COPILOT_OUTBOARD.MFD-CL-PWR-794', 1)# 0 = OFF, 1 = NVG, 2 = NORM
		# Center MFD
		pushSeqCmd(dt, 'MFD_CENTER.MFD-CTR-PWR-866', 1)   # 0 = OFF, 1 = NVG, 2 = NORM

	# FADEC LOAD SHARE switch ... TRQ
	pushSeqCmd(dt, 'OVERHEAD_CONSOLE.OCFC_LOAD', 1) # 0 = PTIT (Power Turbine Inlet Temperature), 1 = TRQ

	# BATT switch ... ON
	pushSeqCmd(dt, 'OVERHEAD_CONSOLE.OCEP_BATT', 1)
	# Verify UTIL PRES light ... ON
	# FIXME: 'ELECTRICAL_UTILITY_PRESSURE' (arg 562) has no named variable in the native DCS Lua files; cannot use scriptCockpitState.
	#pushSeqCmd(dt,'scriptCockpitState', control='CH-47Fbl1/ELECTRICAL_UTILITY_PRESSURE', condition='>=', value=1)
	# APU switch ... RUN for 5 seconds
	pushSeqCmd(dt, 'OVERHEAD_CONSOLE.OCEP_APU', 1) # 0 = OFF, 1 = RUN, 2 = START
	# 5 seconds later, APU switch ... START for 2 seconds
	pushSeqCmd(5, 'OVERHEAD_CONSOLE.OCEP_APU', 2) # 0 = OFF, 1 = RUN, 2 = START
	# 2 seconds later, APU switch ... back to RUN
	pushSeqCmd(2, 'OVERHEAD_CONSOLE.OCEP_APU', 1) # 0 = OFF, 1 = RUN, 2 = START
	# Wait for APU RDY light ON
	# FIXME: 'ELECTRICAL_APU_READY' (arg 563) has no named variable in the native DCS Lua files; cannot use scriptCockpitState.
	#pushSeqCmd(dt,'scriptCockpitState', control='CH-47Fbl1/ELECTRICAL_APU_READY', condition='>=', value=1)
	pushSeqCmd(10, 'scriptText', 'APU RDY light should be on.')
	# Wait for UTIL PRES light OFF
	# FIXME: 'ELECTRICAL_UTILITY_PRESSURE' (arg 562) has no named variable in the native DCS Lua files; cannot use scriptCockpitState.
	#pushSeqCmd(dt,'scriptCockpitState', control='CH-47Fbl1/ELECTRICAL_UTILITY_PRESSURE', value=0)
	pushSeqCmd(2, 'scriptText', 'UTIL PRES light should be on.')
	# GEN APU switch ON
	pushSeqCmd(dt, 'OVERHEAD_CONSOLE.OCEP_GEN_APU', 2) # 0 = TEST, 1 = OFF/RESET, 2 = ON

	# Pilot and Copilot Inboard MFDs default to INST display on cold start.

	# Main and Aux fuel pumps ... ON
	# Engine 1 forward main fuel pump ... ON
	pushSeqCmd(dt, 'OVERHEAD_CONSOLE.OCFC_ENG1_MAIN1', 1)  # 0 = OFF, 1 = ON
	# Engine 1 aft main fuel pump ... ON
	pushSeqCmd(dt, 'OVERHEAD_CONSOLE.OCFC_ENG1_MAIN2', 1)  # 0 = OFF, 1 = ON
	# Engine 1 forward aux fuel pump ... ON
	pushSeqCmd(dt, 'OVERHEAD_CONSOLE.OCFC_ENG1_FWDAUX', 1)   # 0 = OFF, 1 = ON
	# Engine 1 aft aux fuel pump ... ON
	pushSeqCmd(dt, 'OVERHEAD_CONSOLE.OCFC_ENG1_AFTAUX', 1)   # 0 = OFF, 1 = ON
	# Engine 2 forward main fuel pump ... ON
	pushSeqCmd(dt, 'OVERHEAD_CONSOLE.OCFC_ENG2_MAIN1', 1)  # 0 = OFF, 1 = ON
	# Engine 2 aft main fuel pump ... ON
	pushSeqCmd(dt, 'OVERHEAD_CONSOLE.OCFC_ENG2_MAIN2', 1)  # 0 = OFF, 1 = ON
	# Engine 2 forward aux fuel pump ... ON
	pushSeqCmd(dt, 'OVERHEAD_CONSOLE.OCFC_ENG2_FWDAUX', 1)   # 0 = OFF, 1 = ON
	# Engine 2 aft aux fuel pump ... ON
	pushSeqCmd(dt, 'OVERHEAD_CONSOLE.OCFC_ENG2_AFTAUX', 1)   # 0 = OFF, 1 = ON

	# Start engine 1
	# Engine 1 COND lever ... GROUND
	pushSeqCmd(dt, 'OVERHEAD_CONSOLE.OCEC_ENG1_arg534', 0.5188)
	# ENG START switch ... 1 and hold
	pushSeqCmd(dt, 'OVERHEAD_CONSOLE.OCFC_ENG_START', 0)  # 0 = engine 1, 1 = OFF, 2 = engine 2
	# Wait for Engine 1 NG >= 12%.
	# FIXME DCS BIOS does not currently output engine NG values, so we need to use fixed time delays.
	pushSeqCmd(dt, 'scriptText', 'Waiting for Engine 1 NG > 12%...')
	pushSeqCmd(6, 'scriptText', 'Engine 1 started.')
	# ENG START switch ... Release to center
	pushSeqCmd(dt, 'OVERHEAD_CONSOLE.OCFC_ENG_START', 1)  # 0 = engine 1, 1 = OFF, 2 = engine 2
	# Wait for Engine 1 to reach idle, 63% NG.
	pushSeqCmd(dt, 'scriptText', 'Waiting for Engine 1 to reach idle, 63% NG...')
	pushSeqCmd(25, 'scriptText', 'Engine 1 at idle.')

	# Start engine 2
	# Engine 2 COND lever ... GROUND
	pushSeqCmd(dt, 'OVERHEAD_CONSOLE.OCEC_ENG2_arg535', 0.5188)
	# ENG START switch ... 2 and hold
	pushSeqCmd(dt, 'OVERHEAD_CONSOLE.OCFC_ENG_START', 2)  # 0 = engine 1, 1 = OFF, 2 = engine 2
	# Wait for Engine 2 NG >= 12%.
	# FIXME DCS BIOS does not currently output engine NG values, so we need to use fixed time delays.
	pushSeqCmd(dt, 'scriptText', 'Waiting for Engine 2 NG > 12%...')
	pushSeqCmd(6, 'scriptText', 'Engine 2 started.')
	# ENG START switch ... Release to center
	pushSeqCmd(dt, 'OVERHEAD_CONSOLE.OCFC_ENG_START', 1)  # 0 = engine 1, 1 = OFF, 2 = engine 2
	# Wait for Engine 2 to reach idle, 63% NG.
	pushSeqCmd(dt, 'scriptText', 'Waiting for Engine 2 to reach idle, 63% NG...')
	pushSeqCmd(25, 'scriptText', 'Engine 2 at idle.')

	# Engine 1 COND lever ... FLIGHT
	pushSeqCmd(dt, 'OVERHEAD_CONSOLE.OCEC_ENG1_arg534', 1.0)
	# Engine 2 COND lever ... FLIGHT
	pushSeqCmd(dt, 'OVERHEAD_CONSOLE.OCEC_ENG2_arg535', 1.0)
	# Wait for NR to reach 100%
	pushSeqCmd(dt, 'scriptText', 'Waiting for NR to reach 100%...')
	pushSeqCmd(10, 'scriptText', 'NR at 100%.')

	# GEN 1 and 2 switches ... ON
	pushSeqCmd(dt, 'OVERHEAD_CONSOLE.OCEP_GEN_1', 2)  # 0 = TEST, 1 = OFF/RESET, 2 = ON
	pushSeqCmd(dt, 'OVERHEAD_CONSOLE.OCEP_GEN_2', 2)  # 0 = TEST, 1 = OFF/RESET, 2 = ON
	# GEN APU switch ... OFF
	pushSeqCmd(dt, 'OVERHEAD_CONSOLE.OCEP_GEN_APU', 1) # 0 = TEST, 1 = OFF/RESET, 2 = ON
	# APU switch ... OFF
	pushSeqCmd(dt, 'OVERHEAD_CONSOLE.OCEP_APU', 0) # 0 = OFF, 1 = RUN, 2 = START

	# SYSTEM SEL knob ... BOTH
	pushSeqCmd(dt, 'CANTED_CONSOLE.AFCS_SYSTEM', 2) # 0 = OFF, 1 = 1, 2 = BOTH, 3 = 2, 4 = OFF

	# Set Pilot CDU to INDEX page
	pushSeqCmd(dt, 'CDU_RIGHT.CDU-RIGHT-KEY-420', 1) # Press
	pushSeqCmd(dt, 'CDU_RIGHT.CDU-RIGHT-KEY-420', 0) # Release
	# POWER page
	pushSeqCmd(dt, 'CDU_RIGHT.CDU-RIGHT-LSK-L1-424', 1) # Press
	pushSeqCmd(dt, 'CDU_RIGHT.CDU-RIGHT-LSK-L1-424', 0) # Release
	# RWR ... ON
	pushSeqCmd(dt, 'CDU_RIGHT.CDU-RIGHT-LSK-L3-426', 1) # Press
	pushSeqCmd(dt, 'CDU_RIGHT.CDU-RIGHT-LSK-L3-426', 0) # Release
	# ATIRCM/CMWS ... ON
	pushSeqCmd(dt, 'CDU_RIGHT.CDU-RIGHT-LSK-R6-435', 1) # Press
	pushSeqCmd(dt, 'CDU_RIGHT.CDU-RIGHT-LSK-R6-435', 0) # Release
	# Return to INDEX page
	pushSeqCmd(dt, 'CDU_RIGHT.CDU-RIGHT-KEY-420', 1) # Press
	pushSeqCmd(dt, 'CDU_RIGHT.CDU-RIGHT-KEY-420', 0) # Release

	# ASE (countermeasures)
	pushSeqCmd(dt, 'AN_ALE47.ASE_BYPASS1', 1) # 0= NORMAL, 1 = BYPASS
	pushSeqCmd(dt, 'AN_ALE47.ASE_VOL', 0.5)
	pushSeqCmd(dt, 'AN_ALE47.ASE_ARM', 1) # 0 = SAFE, 1 = ARM

	# Radar altimeter ... ON
	#pushSeqCmd(dt, 'RAD_ALT_SET_LO', "+3200")
	# FIXME: Radar altimeter DCS BIOS commands not yet implemented.
	pushSeqCmd(dt, 'scriptSpeech', 'Set radar altimeter low bug manually.')

	return seq


###############################################################################
###############################################################################
def HotStart(config, vars, helper, *args, **kwargs):
	seq = []
	dt = 0.3

	pushSeqCmd = helper.makePushSeqCmd(seq)


	# Start sequence
	pushSeqCmd(0, '', '', "Running Hot Start sequence")

	# MFDs default to NORM on cold start.  For night, set to NVG.
	if vars['time'] == 'day':
		# Set MFDs to NORM
		# Pilot Inboard MFD
		pushSeqCmd(dt, 'MFD_PILOT_INBOARD.MFD-PL-PWR-902', 2)   # 0 = OFF, 1 = NVG, 2 = NORM
		# Pilot Outboard MFD
		pushSeqCmd(dt, 'MFD_PILOT_OUTBOARD.MFD-PR-PWR-938', 2)  # 0 = OFF, 1 = NVG, 2 = NORM
		# Copilot Inboard MFD
		pushSeqCmd(dt, 'MFD_COPILOT_INBOARD.MFD-CR-PWR-830', 2) # 0 = OFF, 1 = NVG, 2 = NORM
		# Copilot Outboard MFD
		pushSeqCmd(dt, 'MFD_COPILOT_OUTBOARD.MFD-CL-PWR-794', 2)# 0 = OFF, 1 = NVG, 2 = NORM
		# Center MFD
		pushSeqCmd(dt, 'MFD_CENTER.MFD-CTR-PWR-866', 2)   # 0 = OFF, 1 = NVG, 2 = NORM
	else:
		# Set MFDs to NVG
		# Pilot Inboard MFD
		pushSeqCmd(dt, 'MFD_PILOT_INBOARD.MFD-PL-PWR-902', 1)   # 0 = OFF, 1 = NVG, 2 = NORM
		# Pilot Outboard MFD
		pushSeqCmd(dt, 'MFD_PILOT_OUTBOARD.MFD-PR-PWR-938', 1)  # 0 = OFF, 1 = NVG, 2 = NORM
		# Copilot Inboard MFD
		pushSeqCmd(dt, 'MFD_COPILOT_INBOARD.MFD-CR-PWR-830', 1) # 0 = OFF, 1 = NVG, 2 = NORM
		# Copilot Outboard MFD
		pushSeqCmd(dt, 'MFD_COPILOT_OUTBOARD.MFD-CL-PWR-794', 1)# 0 = OFF, 1 = NVG, 2 = NORM
		# Center MFD
		pushSeqCmd(dt, 'MFD_CENTER.MFD-CTR-PWR-866', 1)   # 0 = OFF, 1 = NVG, 2 = NORM

	# ASE (countermeasures)
	pushSeqCmd(dt, 'AN_ALE47.ASE_BYPASS1', 1) # 0= NORMAL, 1 = BYPASS
	pushSeqCmd(dt, 'AN_ALE47.ASE_VOL', 0.5)
	pushSeqCmd(dt, 'AN_ALE47.ASE_ARM', 1) # 0 = SAFE, 1 = ARM

	return seq


###############################################################################
###############################################################################
def Shutdown(config, vars, helper, *args, **kwargs):
	seq = []
	dt = 0.3

	pushSeqCmd = helper.makePushSeqCmd(seq)

	# Start sequence
	pushSeqCmd(0, '', '', "Running Shutdown sequence")

	# ASE (countermeasures)
	pushSeqCmd(dt, 'AN_ALE47.ASE_ARM', 0) # 0 = SAFE, 1 = ARM

	# SYSTEM SEL knob ... OFF
	pushSeqCmd(dt, 'CANTED_CONSOLE.AFCS_SYSTEM', 0) # 0 = OFF, 1 = 1, 2 = BOTH, 3 = 2, 4 = OFF

	# APU switch ... RUN for 5 seconds
	pushSeqCmd(dt, 'OVERHEAD_CONSOLE.OCEP_APU', 1) # 0 = OFF, 1 = RUN, 2 = START
	# 5 seconds later, APU switch ... START for 2 seconds
	pushSeqCmd(5, 'OVERHEAD_CONSOLE.OCEP_APU', 2) # 0 = OFF, 1 = RUN, 2 = START
	# 2 seconds later, APU switch ... back to RUN
	pushSeqCmd(2, 'OVERHEAD_CONSOLE.OCEP_APU', 1) # 0 = OFF, 1 = RUN, 2 = START
	# Wait for APU RDY light ON
	# FIXME: 'ELECTRICAL_APU_READY' (arg 563) has no named variable in the native DCS Lua files; cannot use scriptCockpitState.
	#pushSeqCmd(dt,'scriptCockpitState', control='CH-47Fbl1/ELECTRICAL_APU_READY', condition='>=', value=1)
	pushSeqCmd(10, 'scriptText', 'APU RDY light should be on.')
	# GEN APU switch ON
	pushSeqCmd(dt, 'OVERHEAD_CONSOLE.OCEP_GEN_APU', 2) # 0 = TEST, 1 = OFF/RESET, 2 = ON

	# GEN 1 and 2 switches ... OFF
	pushSeqCmd(dt, 'OVERHEAD_CONSOLE.OCEP_GEN_1', 1)  # 0 = TEST, 1 = OFF/RESET, 2 = ON
	pushSeqCmd(dt, 'OVERHEAD_CONSOLE.OCEP_GEN_2', 1)  # 0 = TEST, 1 = OFF/RESET, 2 = ON

	# Engine 1 COND lever ... GROUND
	pushSeqCmd(dt, 'OVERHEAD_CONSOLE.OCEC_ENG1_arg534', 0.5188)
	# Engine 2 COND lever ... GROUND
	pushSeqCmd(dt, 'OVERHEAD_CONSOLE.OCEC_ENG2_arg535', 0.5188)

	# XFEED switch ... OFF
	pushSeqCmd(dt, 'OVERHEAD_CONSOLE.OCFC_XFEED', 0)  # 0 = OFF, 1 = ON

	pushSeqCmd(dt, 'scriptText', 'Waiting for engines to spool down...')
	pushSeqCmd(5, 'scriptText', 'Engines at idle.')

	# Engine 1 COND lever ... OFF
	pushSeqCmd(dt, 'OVERHEAD_CONSOLE.OCEC_ENG1_arg534', 0)
	# Engine 2 COND lever ... OFF
	pushSeqCmd(dt, 'OVERHEAD_CONSOLE.OCEC_ENG2_arg535', 0)

	# FADEC B/U PWR switch ... OFF
	pushSeqCmd(dt, 'OVERHEAD_CONSOLE.OCFC_BU_PWR', 0)  # 0 = OFF, 1 = ON
	# PWR XFER 1 and PWR XFER 2 switches ... OFF
	pushSeqCmd(dt, 'OVERHEAD_CONSOLE.OCHC_PTU_1', 0)  # 0 = OFF, 1 = ON
	pushSeqCmd(dt, 'OVERHEAD_CONSOLE.OCHC_PTU_2', 0)  # 0 = OFF, 1 = ON

	# Main and Aux fuel pumps ... OFF
	# Engine 1 forward main fuel pump ... OFF
	pushSeqCmd(dt, 'OVERHEAD_CONSOLE.OCFC_ENG1_MAIN1', 0)  # 0 = OFF, 1 = ON
	# Engine 1 aft main fuel pump ... OFF
	pushSeqCmd(dt, 'OVERHEAD_CONSOLE.OCFC_ENG1_MAIN2', 0)  # 0 = OFF, 1 = ON
	# Engine 1 forward aux fuel pump ... OFF
	pushSeqCmd(dt, 'OVERHEAD_CONSOLE.OCFC_ENG1_FWDAUX', 0)   # 0 = OFF, 1 = ON
	# Engine 1 aft aux fuel pump ... OFF
	pushSeqCmd(dt, 'OVERHEAD_CONSOLE.OCFC_ENG1_AFTAUX', 0)   # 0 = OFF, 1 = ON
	# Engine 2 forward main fuel pump ... OFF
	pushSeqCmd(dt, 'OVERHEAD_CONSOLE.OCFC_ENG2_MAIN1', 0)  # 0 = OFF, 1 = ON
	# Engine 2 aft main fuel pump ... OFF
	pushSeqCmd(dt, 'OVERHEAD_CONSOLE.OCFC_ENG2_MAIN2', 0)  # 0 = OFF, 1 = ON
	# Engine 2 forward aux fuel pump ... OFF
	pushSeqCmd(dt, 'OVERHEAD_CONSOLE.OCFC_ENG2_FWDAUX', 0)   # 0 = OFF, 1 = ON
	# Engine 2 aft aux fuel pump ... OFF
	pushSeqCmd(dt, 'OVERHEAD_CONSOLE.OCFC_ENG2_AFTAUX', 0)   # 0 = OFF, 1 = ON

	# GEN APU switch ... OFF
	pushSeqCmd(dt, 'OVERHEAD_CONSOLE.OCEP_GEN_APU', 1) # 0 = TEST, 1 = OFF/RESET, 2 = ON
	# APU switch ... OFF
	pushSeqCmd(dt, 'OVERHEAD_CONSOLE.OCEP_APU', 0) # 0 = OFF, 1 = RUN, 2 = START

	# BATT switch ... OFF
	pushSeqCmd(dt, 'OVERHEAD_CONSOLE.OCEP_BATT', 0)

	# MASTER CAUTION ... Reset
	pushSeqCmd(dt, 'GRIPS.MAIN_MCAUTION_R', 1)  # Press
	pushSeqCmd(dt, 'GRIPS.MAIN_MCAUTION_R', 0)  # Release

	return seq
