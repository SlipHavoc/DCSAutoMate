# Return a Dictionary of script data.  The 'scripts' key is a list of scripts that users will be selecting from.  Each script has an associated 'function', which is the name of the function in this file that will be called to generate the command sequence, and a dictionary of 'vars' that the user will be prompted to choose from before running the script, and will be passed into the sequence generating function.
def getScriptData():
	return {
		'moduleName': 'AJS37',
		'scripts': [
			{
				'name': 'Cold Start',
				'function': 'ColdStart',
				'vars': {
					#'time': {
					#	'label': 'Time',
					#	'options': {
					#		'day': 'Day',
					#		'night': 'Night',
					#	},
					#},
				},
			},
			{
				'name': 'Hot Start',
				'function': 'HotStart',
				'vars': {
					#'time': {
					#	'label': 'Time',
					#	'options': {
					#		'day': 'Day',
					#		'night': 'Night',
					#	},
					#},
				},
			},
			{
				'name': 'Reload Data Cartridge',
				'function': 'ReloadDataCartridge',
				'vars': {}
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


def ColdStart(config, vars, helper, *args, **kwargs):
	seq = []
	dt = 0.3

	pushSeqCmd = helper.makePushSeqCmd(seq)

	pushSeqCmd(0, '', '', "Running Cold Start sequence")

	# Pre-start switch positions
	# Main power (HUVUDSTRÖM) - OFF
	pushSeqCmd(dt, 'ELECTRICSYSTEM.HuvudS-PTR', 0)
	# Low-pressure fuel valve (LT-KRAN) - OFF
	pushSeqCmd(dt, 'ENGINEPANEL.Button_2', 0)

	# Generator - OFF
	pushSeqCmd(dt, 'ELECTRICSYSTEM.Gen-PTR', 0)
	# High-pressure fuel valve (HT-KRAN) - OFF
	pushSeqCmd(dt, 'ENGINEPANEL.Button_4', 0)
	# Master mode knob - BER
	pushSeqCmd(dt, 'FLIGHTDATAUNIT.Button_107', 1) # 0 = FK, 1 = BER, 2 = NAV, 3 = ANF, 4 = SPA, 5 = LANDNING NAV, 6 = LANDNING PO

	# Begin startup

	# Main power (HUVUDSTRÖM) - ON
	pushSeqCmd(dt, 'ELECTRICSYSTEM.HuvudS-PTR', 1)
	# Master Caution - Cancel
	pushSeqCmd(dt, 'ERRORPANEL.MasterC-PTR', 1) # Press
	pushSeqCmd(dt, 'ERRORPANEL.MasterC-PTR', 0) # Release
	# Low-pressure fuel valve (LT-KRAN) - ON
	pushSeqCmd(dt, 'ENGINEPANEL.Button_2', 1)

	# Instrument lights - 100%
	pushSeqCmd(dt, 'LIGHTS.PNT_394', 1.0)
	# Panel lights - 100%
	pushSeqCmd(dt, 'LIGHTS.PNT_392', 1.0)
	# Canopy - Close (10s)
	pushSeqCmd(dt, 'FLIGHTDATAUNIT.cmd_3406', 2) # Canopy lever forward
	pushSeqCmd(10, 'FLIGHTDATAUNIT.cmd_3406', 1) # Canopy lever neutral

	# Engine start (35s)
	# Generator - ON
	pushSeqCmd(dt, 'ELECTRICSYSTEM.Gen-PTR', 1)
	# High-pressure fuel valve (HT-KRAN) - ON
	pushSeqCmd(dt, 'ENGINEPANEL.Button_4', 1)
	# Engine Start switch - ON
	pushSeqCmd(dt, 'ENGINEPANEL.Button_1', 1)
	pushSeqCmd(35, 'scriptText', "Engine started, wait for systems to power up (25s)")
	pushSeqCmd(25, 'scriptText', "Systems powered up")

	# Oxygen / Suit air valve (SYRGAS) - ON
	pushSeqCmd(dt, 'FLIGHTDATAUNIT.cmd_3718', 1)

	# LOADING DATA CARTRIDGE
	# Data Cartridge - REMOVE
	pushSeqCmd(dt, 'ENGINEPANEL.cmd_3925', 0)
	pushSeqCmd(2, 'scriptText', "Data Cartridge removed")
	# Data Cartridge - INSERT
	pushSeqCmd(dt, 'ENGINEPANEL.cmd_3925', 1)
	pushSeqCmd(2, 'scriptText', "Data Cartridge inserted")

	# Data selector knob - REF/LOLA, IN
	pushSeqCmd(dt, 'NAVIGATIONPANEL.Datarot-PTR', 5) # Datapanel selector knob, 0 = ID-NR, 1 = TAKT, 2 = TID, 3 = VIND RUTA MAL, 4 = BANA GRANS, 5 = REF LOLA, 6 = AKT POS
	pushSeqCmd(dt, 'NAVIGATIONPANEL.DatapanelINUT-PTR', 1) # In/Out switch, 1 = IN, 2 = OUT
	# Enter data - 9099, LS/SKU
	pushSeqCmd(dt, 'NAVIGATION.Datapanel09-PTR', 1) # Press
	pushSeqCmd(dt, 'NAVIGATION.Datapanel09-PTR', 0) # Release
	pushSeqCmd(dt, 'NAVIGATION.Datapanel00-PTR', 1) # Press
	pushSeqCmd(dt, 'NAVIGATION.Datapanel00-PTR', 0) # Release
	pushSeqCmd(dt, 'NAVIGATION.Datapanel09-PTR', 1) # Press
	pushSeqCmd(dt, 'NAVIGATION.Datapanel09-PTR', 0) # Release
	pushSeqCmd(dt, 'NAVIGATION.Datapanel09-PTR', 1) # Press
	pushSeqCmd(dt, 'NAVIGATION.Datapanel09-PTR', 0) # Release
	pushSeqCmd(dt, 'NAVIGATION.NavselLS-PTR', 1) # Press
	pushSeqCmd(dt, 'NAVIGATION.NavselLS-PTR', 0) # Release
	# Wait for cartridge to be read (7s)
	pushSeqCmd(7, 'scriptText', "Data loaded")
	# Data selector knob - AKT/POS, OUT
	pushSeqCmd(dt, 'NAVIGATIONPANEL.Datarot-PTR', 6) # Datapanel selector knob, 0 = ID-NR, 1 = TAKT, 2 = TID, 3 = VIND RUTA MAL, 4 = BANA GRANS, 5 = REF LOLA, 6 = AKT POS
	pushSeqCmd(dt, 'NAVIGATIONPANEL.DatapanelINUT-PTR', 0) # In/Out switch, 1 = IN, 2 = OUT

	# Ejection seat - ARM
	pushSeqCmd(dt, 'FLIGHTDATAUNIT.cmd_3405', 1)
	# Master mode knob - NAV
	pushSeqCmd(dt, 'FLIGHTDATAUNIT.Button_107', 2) # 0 = FK, 1 = BER, 2 = NAV, 3 = ANF, 4 = SPA, 5 = LANDNING NAV, 6 = LANDNING PO
	# Slav SI switch - F
	pushSeqCmd(dt, 'FLIGHTDATAUNIT.cmd_3201', 0) # 0 = F, 1 = T
	# Parking brake - OFF
	pushSeqCmd(dt, 'FLIGHTDATAUNIT.cmd_3408', 0)

	return seq


def HotStart(config, vars, helper, *args, **kwargs):
	seq = []
	dt = 0.3

	pushSeqCmd = helper.makePushSeqCmd(seq)

	pushSeqCmd(0, 'scriptText', "Running Hot Start sequence")

	# Instrument lights - 100%
	pushSeqCmd(dt, 'LIGHTS.PNT_394', 1.0)
	# Panel lights - 100%
	pushSeqCmd(dt, 'LIGHTS.PNT_392', 1.0)

	# LOADING DATA CARTRIDGE
	# Data Cartridge - REMOVE
	pushSeqCmd(dt, 'ENGINEPANEL.cmd_3925', 0)
	pushSeqCmd(2, 'scriptText', "Data Cartridge removed")
	# Data Cartridge - INSERT
	pushSeqCmd(dt, 'ENGINEPANEL.cmd_3925', 1)
	pushSeqCmd(2, 'scriptText', "Data Cartridge inserted")

	# Data selector knob - REF/LOLA, IN
	pushSeqCmd(dt, 'NAVIGATIONPANEL.Datarot-PTR', 5) # Datapanel selector knob, 0 = ID-NR, 1 = TAKT, 2 = TID, 3 = VIND RUTA MAL, 4 = BANA GRANS, 5 = REF LOLA, 6 = AKT POS
	pushSeqCmd(dt, 'NAVIGATIONPANEL.DatapanelINUT-PTR', 1) # In/Out switch, 1 = IN, 2 = OUT
	# Enter data - 9099, LS/SKU
	pushSeqCmd(dt, 'NAVIGATION.Datapanel09-PTR', 1) # Press
	pushSeqCmd(dt, 'NAVIGATION.Datapanel09-PTR', 0) # Release
	pushSeqCmd(dt, 'NAVIGATION.Datapanel00-PTR', 1) # Press
	pushSeqCmd(dt, 'NAVIGATION.Datapanel00-PTR', 0) # Release
	pushSeqCmd(dt, 'NAVIGATION.Datapanel09-PTR', 1) # Press
	pushSeqCmd(dt, 'NAVIGATION.Datapanel09-PTR', 0) # Release
	pushSeqCmd(dt, 'NAVIGATION.Datapanel09-PTR', 1) # Press
	pushSeqCmd(dt, 'NAVIGATION.Datapanel09-PTR', 0) # Release
	pushSeqCmd(dt, 'NAVIGATION.NavselLS-PTR', 1) # Press
	pushSeqCmd(dt, 'NAVIGATION.NavselLS-PTR', 0) # Release
	# Wait for cartridge to be read (7s)
	pushSeqCmd(7, 'scriptText', "Data loaded")
	# Data selector knob - AKT/POS, OUT
	pushSeqCmd(dt, 'NAVIGATIONPANEL.Datarot-PTR', 6) # Datapanel selector knob, 0 = ID-NR, 1 = TAKT, 2 = TID, 3 = VIND RUTA MAL, 4 = BANA GRANS, 5 = REF LOLA, 6 = AKT POS
	pushSeqCmd(dt, 'NAVIGATIONPANEL.DatapanelINUT-PTR', 0) # In/Out switch, 1 = IN, 2 = OUT

	# Slav SI switch - F
	pushSeqCmd(dt, 'FLIGHTDATAUNIT.cmd_3201', 0) # 0 = F, 1 = T

	return seq


def ReloadDataCartridge(config, vars, helper, *args, **kwargs):
	seq = []
	dt = 0.3

	pushSeqCmd = helper.makePushSeqCmd(seq)

	pushSeqCmd(0, 'scriptText', "Reloading Data Cartridge")

	# LOADING DATA CARTRIDGE
	# Data Cartridge - REMOVE
	pushSeqCmd(dt, 'ENGINEPANEL.cmd_3925', 0)
	pushSeqCmd(2, 'scriptText', "Data Cartridge removed")
	# Data Cartridge - INSERT
	pushSeqCmd(dt, 'ENGINEPANEL.cmd_3925', 1)
	pushSeqCmd(2, 'scriptText', "Data Cartridge inserted")

	# Data selector knob - REF/LOLA, IN
	pushSeqCmd(dt, 'NAVIGATIONPANEL.Datarot-PTR', 5) # Datapanel selector knob, 0 = ID-NR, 1 = TAKT, 2 = TID, 3 = VIND RUTA MAL, 4 = BANA GRANS, 5 = REF LOLA, 6 = AKT POS
	pushSeqCmd(dt, 'NAVIGATIONPANEL.DatapanelINUT-PTR', 1) # In/Out switch, 1 = IN, 2 = OUT
	# Enter data - 9099, LS/SKU
	pushSeqCmd(dt, 'NAVIGATION.Datapanel09-PTR', 1) # Press
	pushSeqCmd(dt, 'NAVIGATION.Datapanel09-PTR', 0) # Release
	pushSeqCmd(dt, 'NAVIGATION.Datapanel00-PTR', 1) # Press
	pushSeqCmd(dt, 'NAVIGATION.Datapanel00-PTR', 0) # Release
	pushSeqCmd(dt, 'NAVIGATION.Datapanel09-PTR', 1) # Press
	pushSeqCmd(dt, 'NAVIGATION.Datapanel09-PTR', 0) # Release
	pushSeqCmd(dt, 'NAVIGATION.Datapanel09-PTR', 1) # Press
	pushSeqCmd(dt, 'NAVIGATION.Datapanel09-PTR', 0) # Release
	pushSeqCmd(dt, 'NAVIGATION.NavselLS-PTR', 1) # Press
	pushSeqCmd(dt, 'NAVIGATION.NavselLS-PTR', 0) # Release
	# Wait for cartridge to be read (7s)
	pushSeqCmd(7, 'scriptText', "Data loaded")
	# Data selector knob - AKT/POS, OUT
	pushSeqCmd(dt, 'NAVIGATIONPANEL.Datarot-PTR', 6) # Datapanel selector knob, 0 = ID-NR, 1 = TAKT, 2 = TID, 3 = VIND RUTA MAL, 4 = BANA GRANS, 5 = REF LOLA, 6 = AKT POS
	pushSeqCmd(dt, 'NAVIGATIONPANEL.DatapanelINUT-PTR', 0) # In/Out switch, 1 = IN, 2 = OUT

	return seq
