# Return a Dictionary of script data.  The 'scripts' key is a list of scripts that users will be selecting from.  Each script has an associated 'function', which is the name of the function in this file that will be called to generate the command sequence, and a dictionary of 'vars' that the user will be prompted to choose from before running the script, and will be passed into the sequence generating function.
import math


def getScriptData():
	return {
		'moduleName': 'F-16C_50',
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
					#'alignment': {
					#	'label': 'Alignment',
					#	'options': {
					#		'storhdg': 'STOR HDG (1.5 mins)',
					#		'norm': 'NORM (8 mins)',
					#	},
					#},
					'hmd': {
						'label': 'HMD',
						'options': {
							'withJhmcs': 'With JHMCS',
							'noJhmcs': 'NVG or none',
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
				'name': 'Air Start',
				'function': 'AirStart',
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
			{
				'name': 'Load Route',
				'function': 'LoadRoute',
				'vars': {
					'routeFile': {
						'label': 'Route File',
						'type': 'dropdown',
						'function': 'getRouteFiles',
					},
					'routeName': {
						'label': 'Route Name',
						'type': 'dropdown',
						'function': 'getRouteNames',
						'params': ['routeFile'],
					},
					'altitude': {
						'label': 'Altitude',
						'options': {
							'forceGround': 'Force Ground',
							'useWaypointAltitudes': 'Use Waypoint Altitudes',
						},
					},
					'startingWaypoint': {
						'label': 'Starting Waypoint',
						'type': 'text',
						'default': '1',
					},
				},
			},
			{
				'name': 'Load Scratchpad',
				'function': 'LoadScratchpad',
				'vars': {
					'scratchpadFile': {
						'label': 'Scratchpad File',
						'type': 'dropdown',
						'function': 'getScratchpadFiles',
					},
					'startingWaypoint': {
						'label': 'Starting Waypoint',
						'type': 'text',
						'default': '1',
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

def getInfo():
	return """"""


def autoSelect(context):
	kit = context.read('arg.PLT_HelmetMountedKit')['arg.PLT_HelmetMountedKit'] # 0 = JHMCS, 0.5 = none, 1 = NVG
	if kit is None:
		return {}
	return {'vars': {'hmd': 'withJhmcs' if kit < 0.25 else 'noJhmcs'}}


# Starting state should be NAV Master Mode, not in the menu screen for the left MFD's B3 OSB.
def setupMFDs(dt, seq, pushSeqCmd):
	# Set up MFDs in all modes (NAV, A-A, A-G, DGFT, MSL).  Left MFD: FCR, HAD, WPN.  Right MFD: SMS, HSD, TGP
	# NAV mode (default)
	# Left MFD
	pushSeqCmd(dt, 'MFD_LEFT.OSB_13', 1) # B3 OSB
	pushSeqCmd(dt, 'MFD_LEFT.OSB_13', 0) # release
	pushSeqCmd(dt, 'MFD_LEFT.OSB_13', 1) # B3 OSB
	pushSeqCmd(dt, 'MFD_LEFT.OSB_13', 0) # release
	pushSeqCmd(dt, 'MFD_LEFT.OSB_2', 1) # HAD
	pushSeqCmd(dt, 'MFD_LEFT.OSB_2', 0) # release
	pushSeqCmd(dt, 'MFD_LEFT.OSB_12', 1) # B4 OSB
	pushSeqCmd(dt, 'MFD_LEFT.OSB_12', 0) # release
	pushSeqCmd(dt, 'MFD_LEFT.OSB_12', 1) # B4 OSB
	pushSeqCmd(dt, 'MFD_LEFT.OSB_12', 0) # release
	pushSeqCmd(dt, 'MFD_LEFT.OSB_18', 1) # WPN
	pushSeqCmd(dt, 'MFD_LEFT.OSB_18', 0) # release
	# Right MFD
	pushSeqCmd(dt, 'MFD_RIGHT.OSB_12', 1) # B4 OSB
	pushSeqCmd(dt, 'MFD_RIGHT.OSB_12', 0) # release
	pushSeqCmd(dt, 'MFD_RIGHT.OSB_12', 1) # B4 OSB
	pushSeqCmd(dt, 'MFD_RIGHT.OSB_12', 0) # release
	pushSeqCmd(dt, 'MFD_RIGHT.OSB_19', 1) # TGP
	pushSeqCmd(dt, 'MFD_RIGHT.OSB_19', 0) # release
	# Select FCR/HSD
	pushSeqCmd(dt, 'MFD_LEFT.OSB_14', 1) # B3 OSB
	pushSeqCmd(dt, 'MFD_LEFT.OSB_14', 0) # release
	pushSeqCmd(dt, 'MFD_RIGHT.OSB_13', 1) # B3 OSB
	pushSeqCmd(dt, 'MFD_RIGHT.OSB_13', 0) # release

	# A-A mode
	pushSeqCmd(dt, 'UFC.AA', 1) # Switch to A-A Master Mode
	pushSeqCmd(dt, 'UFC.AA', 0)
	pushSeqCmd(dt, 'MFD_LEFT.OSB_13', 1) # B3 OSB
	pushSeqCmd(dt, 'MFD_LEFT.OSB_13', 0) # release
	pushSeqCmd(dt, 'MFD_LEFT.OSB_13', 1) # B3 OSB
	pushSeqCmd(dt, 'MFD_LEFT.OSB_13', 0) # release
	pushSeqCmd(dt, 'MFD_LEFT.OSB_2', 1) # HAD
	pushSeqCmd(dt, 'MFD_LEFT.OSB_2', 0) # release
	pushSeqCmd(dt, 'MFD_LEFT.OSB_12', 1) # B4 OSB
	pushSeqCmd(dt, 'MFD_LEFT.OSB_12', 0) # release
	pushSeqCmd(dt, 'MFD_LEFT.OSB_12', 1) # B4 OSB
	pushSeqCmd(dt, 'MFD_LEFT.OSB_12', 0) # release
	pushSeqCmd(dt, 'MFD_LEFT.OSB_18', 1) # WPN
	pushSeqCmd(dt, 'MFD_LEFT.OSB_18', 0) # release
	# Right MFD
	pushSeqCmd(dt, 'MFD_RIGHT.OSB_12', 1) # B4 OSB
	pushSeqCmd(dt, 'MFD_RIGHT.OSB_12', 0) # release
	pushSeqCmd(dt, 'MFD_RIGHT.OSB_12', 1) # B4 OSB
	pushSeqCmd(dt, 'MFD_RIGHT.OSB_12', 0) # release
	pushSeqCmd(dt, 'MFD_RIGHT.OSB_19', 1) # TGP
	pushSeqCmd(dt, 'MFD_RIGHT.OSB_19', 0) # release
	# Select FCR/HSD
	pushSeqCmd(dt, 'MFD_LEFT.OSB_14', 1) # B3 OSB
	pushSeqCmd(dt, 'MFD_LEFT.OSB_14', 0) # release
	pushSeqCmd(dt, 'MFD_RIGHT.OSB_13', 1) # B3 OSB
	pushSeqCmd(dt, 'MFD_RIGHT.OSB_13', 0) # release

	# A-G mode
	pushSeqCmd(dt, 'UFC.AG', 1) # Switch to A-G Master Mode
	pushSeqCmd(dt, 'UFC.AG', 0)
	pushSeqCmd(dt, 'MFD_LEFT.OSB_13', 1) # B3 OSB
	pushSeqCmd(dt, 'MFD_LEFT.OSB_13', 0) # release
	pushSeqCmd(dt, 'MFD_LEFT.OSB_13', 1) # B3 OSB
	pushSeqCmd(dt, 'MFD_LEFT.OSB_13', 0) # release
	pushSeqCmd(dt, 'MFD_LEFT.OSB_2', 1) # HAD
	pushSeqCmd(dt, 'MFD_LEFT.OSB_2', 0) # release
	pushSeqCmd(dt, 'MFD_LEFT.OSB_12', 1) # B4 OSB
	pushSeqCmd(dt, 'MFD_LEFT.OSB_12', 0) # release
	pushSeqCmd(dt, 'MFD_LEFT.OSB_12', 1) # B4 OSB
	pushSeqCmd(dt, 'MFD_LEFT.OSB_12', 0) # release
	pushSeqCmd(dt, 'MFD_LEFT.OSB_18', 1) # WPN
	pushSeqCmd(dt, 'MFD_LEFT.OSB_18', 0) # release
	# Right MFD
	pushSeqCmd(dt, 'MFD_RIGHT.OSB_12', 1) # B4 OSB
	pushSeqCmd(dt, 'MFD_RIGHT.OSB_12', 0) # release
	pushSeqCmd(dt, 'MFD_RIGHT.OSB_12', 1) # B4 OSB
	pushSeqCmd(dt, 'MFD_RIGHT.OSB_12', 0) # release
	pushSeqCmd(dt, 'MFD_RIGHT.OSB_19', 1) # TGP
	pushSeqCmd(dt, 'MFD_RIGHT.OSB_19', 0) # release
	# Select FCR/HSD
	pushSeqCmd(dt, 'MFD_LEFT.OSB_14', 1) # B3 OSB
	pushSeqCmd(dt, 'MFD_LEFT.OSB_14', 0) # release
	pushSeqCmd(dt, 'MFD_RIGHT.OSB_13', 1) # B3 OSB
	pushSeqCmd(dt, 'MFD_RIGHT.OSB_13', 0) # release

	# Return to NAV mode
	pushSeqCmd(dt, 'UFC.AG', 1) # Switch back to NAV Master Mode (we were in A-G mode)
	pushSeqCmd(dt, 'UFC.AG', 0)

	# DGFT OVRD mode
	pushSeqCmd(dt, 'HOTAS.THROTTLE_DOG_FIGHT', 1) # 1 = DOGFIGHT, 0 = CENTER, -1 = MISSILE OVERRIDE
	pushSeqCmd(dt, 'MFD_LEFT.OSB_13', 1) # B3 OSB
	pushSeqCmd(dt, 'MFD_LEFT.OSB_13', 0) # release
	pushSeqCmd(dt, 'MFD_LEFT.OSB_13', 1) # B3 OSB
	pushSeqCmd(dt, 'MFD_LEFT.OSB_13', 0) # release
	pushSeqCmd(dt, 'MFD_LEFT.OSB_2', 1) # HAD
	pushSeqCmd(dt, 'MFD_LEFT.OSB_2', 0) # release
	pushSeqCmd(dt, 'MFD_LEFT.OSB_12', 1) # B4 OSB
	pushSeqCmd(dt, 'MFD_LEFT.OSB_12', 0) # release
	pushSeqCmd(dt, 'MFD_LEFT.OSB_12', 1) # B4 OSB
	pushSeqCmd(dt, 'MFD_LEFT.OSB_12', 0) # release
	pushSeqCmd(dt, 'MFD_LEFT.OSB_18', 1) # WPN
	pushSeqCmd(dt, 'MFD_LEFT.OSB_18', 0) # release
	# Select FCR/SMS
	pushSeqCmd(dt, 'MFD_RIGHT.OSB_13', 1) # B3 OSB
	pushSeqCmd(dt, 'MFD_RIGHT.OSB_13', 0) # release
	pushSeqCmd(dt, 'MFD_RIGHT.OSB_13', 1) # B3 OSB
	pushSeqCmd(dt, 'MFD_RIGHT.OSB_13', 0) # release
	pushSeqCmd(dt, 'MFD_RIGHT.OSB_7', 1) # HSD
	pushSeqCmd(dt, 'MFD_RIGHT.OSB_7', 0) # release
	pushSeqCmd(dt, 'MFD_RIGHT.OSB_12', 1) # B4 OSB
	pushSeqCmd(dt, 'MFD_RIGHT.OSB_12', 0) # release
	pushSeqCmd(dt, 'MFD_RIGHT.OSB_12', 1) # B4 OSB
	pushSeqCmd(dt, 'MFD_RIGHT.OSB_12', 0) # release
	pushSeqCmd(dt, 'MFD_RIGHT.OSB_19', 1) # TGP
	pushSeqCmd(dt, 'MFD_RIGHT.OSB_19', 0) # release
	# Select FCR/HSD
	pushSeqCmd(dt, 'MFD_LEFT.OSB_14', 1) # B3 OSB
	pushSeqCmd(dt, 'MFD_LEFT.OSB_14', 0) # release
	pushSeqCmd(dt, 'MFD_RIGHT.OSB_13', 1) # B3 OSB
	pushSeqCmd(dt, 'MFD_RIGHT.OSB_13', 0) # release
	# Return to NAV mode
	pushSeqCmd(dt, 'HOTAS.THROTTLE_DOG_FIGHT', 0) # CENTER

	# MSL OVRD mode
	pushSeqCmd(dt, 'HOTAS.THROTTLE_DOG_FIGHT', -1) # 1 = DOGFIGHT, 0 = CENTER, -1 = MISSILE OVERRIDE
	pushSeqCmd(dt, 'MFD_LEFT.OSB_13', 1) # B3 OSB
	pushSeqCmd(dt, 'MFD_LEFT.OSB_13', 0) # release
	pushSeqCmd(dt, 'MFD_LEFT.OSB_13', 1) # B3 OSB
	pushSeqCmd(dt, 'MFD_LEFT.OSB_13', 0) # release
	pushSeqCmd(dt, 'MFD_LEFT.OSB_2', 1) # HAD
	pushSeqCmd(dt, 'MFD_LEFT.OSB_2', 0) # release
	pushSeqCmd(dt, 'MFD_LEFT.OSB_12', 1) # B4 OSB
	pushSeqCmd(dt, 'MFD_LEFT.OSB_12', 0) # release
	pushSeqCmd(dt, 'MFD_LEFT.OSB_12', 1) # B4 OSB
	pushSeqCmd(dt, 'MFD_LEFT.OSB_12', 0) # release
	pushSeqCmd(dt, 'MFD_LEFT.OSB_18', 1) # WPN
	pushSeqCmd(dt, 'MFD_LEFT.OSB_18', 0) # release
	# Right MFD
	pushSeqCmd(dt, 'MFD_RIGHT.OSB_13', 1) # B3 OSB
	pushSeqCmd(dt, 'MFD_RIGHT.OSB_13', 0) # release
	pushSeqCmd(dt, 'MFD_RIGHT.OSB_13', 1) # B3 OSB
	pushSeqCmd(dt, 'MFD_RIGHT.OSB_13', 0) # release
	pushSeqCmd(dt, 'MFD_RIGHT.OSB_7', 1) # HSD
	pushSeqCmd(dt, 'MFD_RIGHT.OSB_7', 0) # release
	pushSeqCmd(dt, 'MFD_RIGHT.OSB_12', 1) # B4 OSB
	pushSeqCmd(dt, 'MFD_RIGHT.OSB_12', 0) # release
	pushSeqCmd(dt, 'MFD_RIGHT.OSB_12', 1) # B4 OSB
	pushSeqCmd(dt, 'MFD_RIGHT.OSB_12', 0) # release
	pushSeqCmd(dt, 'MFD_RIGHT.OSB_19', 1) # TGP
	pushSeqCmd(dt, 'MFD_RIGHT.OSB_19', 0) # release
	# Select FCR/HSD
	pushSeqCmd(dt, 'MFD_LEFT.OSB_14', 1) # B3 OSB
	pushSeqCmd(dt, 'MFD_LEFT.OSB_14', 0) # release
	pushSeqCmd(dt, 'MFD_RIGHT.OSB_13', 1) # B3 OSB
	pushSeqCmd(dt, 'MFD_RIGHT.OSB_13', 0) # release
	# Return to NAV mode
	pushSeqCmd(dt, 'HOTAS.THROTTLE_DOG_FIGHT', 0) # CENTER
	return seq

def Test(config, vars, helper, *args, **kwargs):
	seq = []
	dt = 0.3

	pushSeqCmd = helper.makePushSeqCmd(seq)

	# Test code here...
	pushSeqCmd(0, '', '', "Running Test sequence")

	pushSeqCmd(dt, 'HOTAS.THROTTLE_DOG_FIGHT', 1) # 1 = DOGFIGHT, 0 = CENTER, -1 = MISSILE OVERRIDE

	return seq


def ColdStart(config, vars, helper, *args, **kwargs):
	seq = []
	dt = 0.3

	pushSeqCmd = helper.makePushSeqCmd(seq)

	pushSeqCmd(0, '', '', "Running Cold Start sequence")
	pushSeqCmd(dt, 'scriptSpeech', 'Do not rearm until alignment complete.')

	# Interior lights
	if vars.get('time') == 'day':
		pushSeqCmd(dt, 'CPTLIGHTS_SYSTEM.Consoles', 1.0)
		pushSeqCmd(dt, 'CPTLIGHTS_SYSTEM.IntsPnl', 1.0)
		pushSeqCmd(dt, 'CPTLIGHTS_SYSTEM.IndBrtAoA', 1.0)
		pushSeqCmd(dt, 'CPTLIGHTS_SYSTEM.IndBrtAR', 1.0)
		pushSeqCmd(dt, 'HMCS.IntKnob', 1.0, "HMCS BRIGHTNESS - MAX")
		pushSeqCmd(dt, 'UFC.SYM_Knob', 1.0, "HUD BRIGHTNESS - MAX")
	else:
		pushSeqCmd(dt, 'CPTLIGHTS_SYSTEM.Consoles', 0.5)
		pushSeqCmd(dt, 'CPTLIGHTS_SYSTEM.IntsPnl', 0.5)
		pushSeqCmd(dt, 'CPTLIGHTS_SYSTEM.IndBrtAoA', 0.5)
		pushSeqCmd(dt, 'CPTLIGHTS_SYSTEM.IndBrtAR', 0.5)
		# Cockpit flood lights start on at night, so turn them off.
		pushSeqCmd(dt, 'CPTLIGHTS_SYSTEM.ConsolesFlood', 0)
		pushSeqCmd(dt, 'CPTLIGHTS_SYSTEM.InstPnlFlood', 0)
		pushSeqCmd(dt, 'HMCS.IntKnob', 0.5, "HMCS BRIGHTNESS - 50%")
		pushSeqCmd(dt, 'UFC.SYM_Knob', 0.5, "HUD BRIGHTNESS - 50%")

	# Exterior lights
	pushSeqCmd(dt, 'EXTLIGHTS_SYSTEM.Master', 0) # 0 = OFF, 1 = ALL, 2 = A-C, 3 = FORM, 4 = NORM

	pushSeqCmd(dt, 'ELEC_INTERFACE.MainPwrSw', 2, "MAIN PWR SWITCH - ON") # 0 = OFF, 1 = BATT, 2 = MAIN PWR
	pushSeqCmd(dt, 'GEAR_INTERFACE.AntiSkidSw', 2, "PARKING BRAKE/ANTI-SKID SWITCH - PARKING BRAKE") # 0 = OFF, 1 = ANTI-SKID, 2 = PARKING BRAKE

	# Starting Engine
	# SPOOL UP  - 20% RPM MINIMUM
	pushSeqCmd(dt, 'ENGINE_INTERFACE.JfsSwStart2', 0, "JFS SWITCH - START 2") # 0 = START 2, 1 = OFF, 2 = START 1
	pushSeqCmd(dt, 'ENGINE_INTERFACE.JfsSwStart2', 1, "JFS SWITCH - OFF") # 0 = START 2, 1 = OFF, 2 = START 1

	# Close canopy while we wait
	#pushSeqCmd(dt, '', '', "CANOPY - CLOSE AND LOCK
	pushSeqCmd(dt, 'CPT_MECH.CanopyHandle', 0) # Unlock, up
	pushSeqCmd(dt, 'CPT_MECH.CanopySwitchClose', 0)
	pushSeqCmd(dt, 'scriptCockpitState', control='F-16C_50/arg.CanopyLock', value=0) # Wait for canopy to close and lock.
	pushSeqCmd(dt, 'CPT_MECH.CanopySwitchClose', 1)
	pushSeqCmd(dt, 'CPT_MECH.CanopyHandle', 1) # Lock, down

	#pushSeqCmd(dt, 'scriptCockpitState', control='F-16C_50/ENGINE_TACHOMETER', condition='>=', value=7500) # Wait for engine RPMs to be over 20%.
	pushSeqCmd(dt, 'scriptCockpitState', control='F-16C_50/arg.CautionLights.SEC', value=0) # Wait for SEC caution light to go off.  This indicates engine is ready to start.
	pushSeqCmd(dt, '', '', 'Engine at 20%')

	# ENGINE START
	# THROTTLE - IDLE
	pushSeqCmd(dt, 'scriptSimCommand', 'iCommandLeftEngineStart') # Throttle IDLE
	#pushSeqCmd(dt, 'scriptCockpitState', control='F-16C_50/ENGINE_TACHOMETER', condition='>=', value=25000) # Wait for engine to reach idle.
	pushSeqCmd(dt, 'scriptCockpitState', control='F-16C_50/arg.CautionLights.ELEC_SYS', value=0) # Wait for ELEC SYS caution light to go off.  This indicates engine has started.
	pushSeqCmd(dt, '', '', 'Engine started')

	# AVIONICS POWER panel
	pushSeqCmd(dt, 'MMC.MmcPwr', 1, "MMC SWITCH - ON")
	pushSeqCmd(dt, 'SMS.StStaSw', 1, "ST STA SWITCH - ON")
	pushSeqCmd(dt, 'MMC.MFD', 1, "MFD SWITCH - ON")
	pushSeqCmd(dt, 'UFC.UFC_Sw', 1, "UFC SWITCH - ON")
	#pushSeqCmd(dt, 'MAP.PwrSw', 1, "MAP SWITCH - ON") # Not used.
	pushSeqCmd(dt, 'GPS.PwrSw', 1, "GPS SWITCH - ON")
	#pushSeqCmd(dt, 'IDM.PwrSw', 1, "DL SWITCH - ON") # Not used, see MDS LVT knob for datalink.
	# NOTE Leave MIDS LVT knob off until INS is aligned and GPS time is being received.

	# Begin alignment, takes 90 seconds for STOR HDG, or 8 minutes for NORM.
	if vars.get('alignment') == 'norm':
		pushSeqCmd(dt, 'INS.ModeKnob', 2, "INS KNOB - STOR HDG") # 0 = OFF, 1 = STOR HDG, 2 = NORM, 3 = NAV, 4 = CAL, 5 = IN FLT ALIGN, 6 = ATT
		pushSeqCmd(3, '', '', "VERIFYING INITIAL COORDINATES ON DED")
		# Accept LAT
		pushSeqCmd(dt, 'UFC.ENTR', 1)
		pushSeqCmd(dt, 'UFC.ENTR', 0)
		pushSeqCmd(dt, 'UFC.DCS_DOWN', 1) # Press DN
		pushSeqCmd(0.5, 'UFC.DCS_DOWN', 0) # Release
		# Accent LNG
		pushSeqCmd(dt, 'UFC.ENTR', 1)
		pushSeqCmd(dt, 'UFC.ENTR', 0)
		pushSeqCmd(dt, 'UFC.DCS_DOWN', 1) # Press DN
		pushSeqCmd(0.5, 'UFC.DCS_DOWN', 0) # Release
		# Accept SALT (System Altitude)
		pushSeqCmd(dt, 'UFC.ENTR', 1)
		pushSeqCmd(dt, 'UFC.ENTR', 0)
	else:
		pushSeqCmd(dt, 'INS.ModeKnob', 1, "INS KNOB - STOR HDG") # 0 = OFF, 1 = STOR HDG, 2 = NORM, 3 = NAV, 4 = CAL, 5 = IN FLT ALIGN, 6 = ATT

	# SNSR PWR panel
	pushSeqCmd(dt, 'FCR.PwrSw', 1, "FCR SWITCH - ON")
	pushSeqCmd(dt, 'RALT.PwrSw', 1, "RDR ALT SWITCH - ON")

	pushSeqCmd(dt, 'SAI.reference', 0.5, "STANDBY ATTITUDE INDICATOR - UNCAGE AND CENTER")

	# UHF Radio
	pushSeqCmd(dt, 'UHF_CONTROL_PANEL.FunctionKnob', 1, "UHF FUNCTION KNOB - MAIN") # 0 = OFF, 1 = MAIN, 2 = BOTH, 3 = ADF

	# IFF
	pushSeqCmd(dt, 'IFF_CONTROL_PANEL.MasterKnob', 3, "IFF MASTER KNOB - NORM") # 0 = OFF, 1 = STBY, 2 = LOW, 3 = NORM, 4 = EMER

	# CMDS panel
	pushSeqCmd(dt, 'CMDS.RwrSrc', 1, "CMDS RWR SWITCH - ON")
	pushSeqCmd(dt, 'CMDS.JmrSrc', 1, "CMDS JMR SWITCH - ON")
	pushSeqCmd(dt, 'CMDS.ChExp', 1, "CMDS CH SWITCH - ON")
	pushSeqCmd(dt, 'CMDS.FlExp', 1, "CMDS FL SWITCH - ON")
	pushSeqCmd(dt, 'CMDS.Mode', 2, "CMDS MODE KNOB - MAN (MANUAL CHAFF/FLARES)") # 0 = OFF, 1 = STBY, 2 = MAN, 3 = SEMI, 4 = AUTO, 5 = BYP

	# Left and right hardpoints on
	pushSeqCmd(dt, 'SMS.LeftHDPT', 1)
	pushSeqCmd(dt, 'SMS.RightHDPT', 1)

	# RWR
	pushSeqCmd(dt, 'RWR.Power', 1, "RWR INDICATOR CONTROL POWER - ON") # Press only
	pushSeqCmd(dt, 'RWR.Search', 1, "RWR INDICATOR SEARCH BUTTON - ON") # Press only

	# Set up the MFDs while we wait for alignment to complete.
	setupMFDs(dt, seq, pushSeqCmd)

	pushSeqCmd(dt, 'scriptSpeech', 'Don\'t rearm until alignment complete.') # Reminder not to rearm until alignment is complete.
	# Ensure we're on the DED LIST page: LIST > 6INS.
	pushSeqCmd(dt, 'UFC.LIST', 1)
	pushSeqCmd(dt, 'UFC.LIST', 0)
	pushSeqCmd(dt, 'UFC.DIG6_TIME', 1)
	pushSeqCmd(dt, 'UFC.DIG6_TIME', 0)

	pushSeqCmd(dt, 'scriptCockpitState', control='F-16C_50/ind.6.INS_AlignStatusCode', condition='=', value='10', duration=3) # Wait for INS alignment to finish (status code 10 = ready).
	pushSeqCmd(dt, '', '', 'INS alignment complete')

	# INS Knob - NAV after aligning
	pushSeqCmd(dt, 'INS.ModeKnob', 3, "INS KNOB - NAV") # 0 = OFF, 1 = STOR HDG, 2 = NORM, 3 = NAV, 4 = CAL, 5 = IN FLT ALIGN, 6 = ATT
	pushSeqCmd(dt, 'scriptSpeech', 'Alignment complete, you may now rearm.')

	# RETURN TO MAIN DED PAGE
	pushSeqCmd(dt, 'UFC.DCS_RTN', 1) # Press RTN
	pushSeqCmd(0.5, 'UFC.DCS_RTN', 0) # Release

	# ECM
	# ECM POWER SWITCH - ON
	pushSeqCmd(dt, 'ECM_INTERFACE.PwrSw', 1) # Must go through center position first.  0 = OFF, 1 = STBY, 2 = OPR
	pushSeqCmd(dt, 'ECM_INTERFACE.PwrSw', 2)
	# ECM modules ON
	pushSeqCmd(dt, 'ECM_INTERFACE.OneBtn', 1, "ECM 1 MODULE - ON")
	pushSeqCmd(dt, 'ECM_INTERFACE.TwoBtn', 1, "ECM 2 MODULE - ON")
	pushSeqCmd(dt, 'ECM_INTERFACE.ThreeBtn', 1, "ECM 3 MODULE - ON")
	pushSeqCmd(dt, 'ECM_INTERFACE.FourBtn', 1, "ECM 4 MODULE - ON")
	pushSeqCmd(dt, 'ECM_INTERFACE.FiveBtn', 1, "ECM 5 MODULE - ON")
	pushSeqCmd(dt, 'ECM_INTERFACE.SixBtn', 1, "ECM 6 MODULE - ON")

	if vars.get('hmd') == 'withJhmcs':
		# Prepare HMCS for alignment
		pushSeqCmd(dt, 'UFC.LIST', 1)
		pushSeqCmd(dt, 'UFC.LIST', 0)
		pushSeqCmd(dt, 'UFC.DIG0_M_SEL', 1) # MISC in DED
		pushSeqCmd(dt, 'UFC.DIG0_M_SEL', 0)
		pushSeqCmd(dt, 'UFC.RCL', 1) # HMCS in DED
		pushSeqCmd(dt, 'UFC.RCL', 0)
		pushSeqCmd(dt, 'UFC.DCS_SEQ', 1) # HMCS ALIGN - Press SEQ
		pushSeqCmd(0.5, 'UFC.DCS_SEQ', 0) # Release
		pushSeqCmd(dt, 'UFC.DIG0_M_SEL', 1) # COARSE in DED
		pushSeqCmd(dt, 'UFC.DIG0_M_SEL', 0)
		pushSeqCmd(dt, 'scriptSpeech', 'Press shift T D C press to align.  Press M SELL (zero) twice to go to next mode, use T D C to align, then go to next mode and align.  When all modes are aligned press Return on Dobber to exit align.')

	# Laser arm switch - ARM
	pushSeqCmd(dt, 'SMS.LaserSw', 1)

	# Master arm switch - ARM
	pushSeqCmd(dt, 'MMC.MasterArmSw', 2)

	pushSeqCmd(dt, 'CPT_MECH.EjectionSafetyLever', 1, "EJECTION SAFETY LEVER - ARM (DOWN)")
	pushSeqCmd(dt, 'GEAR_INTERFACE.AntiSkidSw', 1, "PARKING BRAKE/ANTI-SKID SWITCH - ANTI-SKID") # 0 = OFF, 1 = ANTI-SKID, 2 = PARKING BRAKE

	# MIDS LVT knob - ON
	# MIDS LVT requirements: INS alignment complete and in NAV mode, and if using GPS for network time reference, GPS must be on and receiving a time..
	pushSeqCmd(dt, 'MIDS.PwrSw', 2, "MDS LVT KNOB - ON") # Required for Link16 to work. 0 = ZERO, 1 = OFF, 2 = ON

	# Probe Heat (only when icing conditions on the ground, must take off within 5 minutes to prevent overheat)
	#FIXME: pushSeqCmd(dt, ELEC_INTERFACE, action = elec_commands.ProbeHeatSw, 1)
	pushSeqCmd(dt, 'scriptSpeech', 'Manual steps remaining: Set cat 1 or cat 3.')

	return seq


def HotStart(config, vars, helper, *args, **kwargs):
	seq = []
	dt = 0.3

	pushSeqCmd = helper.makePushSeqCmd(seq)

	pushSeqCmd(0, '', '', "Running Hot Start sequence")

	# Interior lights
	if vars.get('time') == 'day':
		pushSeqCmd(dt, 'CPTLIGHTS_SYSTEM.Consoles', 1.0)
		pushSeqCmd(dt, 'CPTLIGHTS_SYSTEM.IntsPnl', 1.0)
		pushSeqCmd(dt, 'CPTLIGHTS_SYSTEM.IndBrtAoA', 1.0)
		pushSeqCmd(dt, 'CPTLIGHTS_SYSTEM.IndBrtAR', 1.0)
		pushSeqCmd(dt, 'HMCS.IntKnob', 1.0, "HMCS BRIGHTNESS - MAX")
		pushSeqCmd(dt, 'UFC.SYM_Knob', 1.0, "HUD BRIGHTNESS - MAX")
	else:
		pushSeqCmd(dt, 'CPTLIGHTS_SYSTEM.Consoles', 0.5)
		pushSeqCmd(dt, 'CPTLIGHTS_SYSTEM.IntsPnl', 0.5)
		pushSeqCmd(dt, 'CPTLIGHTS_SYSTEM.IndBrtAoA', 0.5)
		pushSeqCmd(dt, 'CPTLIGHTS_SYSTEM.IndBrtAR', 0.5)
		# Cockpit flood lights start on at night, so turn them off.
		pushSeqCmd(dt, 'CPTLIGHTS_SYSTEM.ConsolesFlood', 0)
		pushSeqCmd(dt, 'CPTLIGHTS_SYSTEM.InstPnlFlood', 0)
		pushSeqCmd(dt, 'HMCS.IntKnob', 0.5, "HMCS BRIGHTNESS - 50%")
		pushSeqCmd(dt, 'UFC.SYM_Knob', 0.5, "HUD BRIGHTNESS - 50%")

	# Exterior lights
	pushSeqCmd(dt, 'EXTLIGHTS_SYSTEM.Master', 0) # 0 = OFF, 1 = ALL, 2 = A-C, 3 = FORM, 4 = NORM

	# UHF Radio
	pushSeqCmd(dt, 'UHF_CONTROL_PANEL.FunctionKnob', 1, "UHF FUNCTION KNOB - MAIN") # 0 = OFF, 1 = MAIN, 2 = BOTH, 3 = ADF

	# CMDS panel
	pushSeqCmd(dt, 'CMDS.Mode', 2, "CMDS MODE KNOB - MAN (MANUAL CHAFF/FLARES)") # 0 = OFF, 1 = STBY, 2 = MAN, 3 = SEMI, 4 = AUTO, 5 = BYP

	# Left and right hardpoints on
	pushSeqCmd(dt, 'SMS.LeftHDPT', 1)
	pushSeqCmd(dt, 'SMS.RightHDPT', 1)

	# RWR
	pushSeqCmd(dt, 'RWR.Power', 1, "RWR INDICATOR CONTROL POWER - ON") # Press only
	pushSeqCmd(dt, 'RWR.Search', 1, "RWR INDICATOR SEARCH BUTTON - ON") # Press only

	# ECM
	# ECM POWER SWITCH - ON
	pushSeqCmd(dt, 'ECM_INTERFACE.PwrSw', 1) # Must go through center position first.  0 = OFF, 1 = STBY, 2 = OPR
	pushSeqCmd(dt, 'ECM_INTERFACE.PwrSw', 2)
	# ECM XMIT SWITCH - 3 (BARRAGE JAMMING)
	#pushSeqCmd(dt, 'ECM_INTERFACE.XmitSw', 1) # Must go through center position first.  0 = 3, 1 = 2, 2 = 1
	#pushSeqCmd(dt, 'ECM_INTERFACE.XmitSw', 2)
	pushSeqCmd(dt, 'ECM_INTERFACE.OneBtn', 1, "ECM 1 MODULE - ON")
	pushSeqCmd(dt, 'ECM_INTERFACE.TwoBtn', 1, "ECM 2 MODULE - ON")
	pushSeqCmd(dt, 'ECM_INTERFACE.ThreeBtn', 1, "ECM 3 MODULE - ON")
	pushSeqCmd(dt, 'ECM_INTERFACE.FourBtn', 1, "ECM 4 MODULE - ON")
	pushSeqCmd(dt, 'ECM_INTERFACE.FiveBtn', 1, "ECM 5 MODULE - ON")
	pushSeqCmd(dt, 'ECM_INTERFACE.SixBtn', 1, "ECM 6 MODULE - ON")

	setupMFDs(dt, seq, pushSeqCmd)

	# Laser arm switch - ARM
	pushSeqCmd(dt, 'SMS.LaserSw', 1)

	# Master arm switch - ARM
	pushSeqCmd(dt, 'MMC.MasterArmSw', 2)

	pushSeqCmd(dt, 'scriptSpeech', 'Manual steps remaining: Set cat 1 or cat 3.')

	return seq


def AirStart(config, vars, helper, *args, **kwargs):
	seq = []
	dt = 0.3

	pushSeqCmd = helper.makePushSeqCmd(seq)

	pushSeqCmd(0, '', '', "Running Air Start sequence")

	# Interior lights
	if vars.get('time') == 'day':
		pushSeqCmd(dt, 'CPTLIGHTS_SYSTEM.Consoles', 1.0)
		pushSeqCmd(dt, 'CPTLIGHTS_SYSTEM.IntsPnl', 1.0)
		pushSeqCmd(dt, 'CPTLIGHTS_SYSTEM.IndBrtAoA', 1.0)
		pushSeqCmd(dt, 'CPTLIGHTS_SYSTEM.IndBrtAR', 1.0)
		pushSeqCmd(dt, 'HMCS.IntKnob', 1.0, "HMCS BRIGHTNESS - MAX")
		pushSeqCmd(dt, 'UFC.SYM_Knob', 1.0, "HUD BRIGHTNESS - MAX")
	else:
		pushSeqCmd(dt, 'CPTLIGHTS_SYSTEM.Consoles', 0.5)
		pushSeqCmd(dt, 'CPTLIGHTS_SYSTEM.IntsPnl', 0.5)
		pushSeqCmd(dt, 'CPTLIGHTS_SYSTEM.IndBrtAoA', 0.5)
		pushSeqCmd(dt, 'CPTLIGHTS_SYSTEM.IndBrtAR', 0.5)
		# Cockpit flood lights start on at night, so turn them off.
		pushSeqCmd(dt, 'CPTLIGHTS_SYSTEM.ConsolesFlood', 0)
		pushSeqCmd(dt, 'CPTLIGHTS_SYSTEM.InstPnlFlood', 0)
		pushSeqCmd(dt, 'HMCS.IntKnob', 0.5, "HMCS BRIGHTNESS - 50%")
		pushSeqCmd(dt, 'UFC.SYM_Knob', 0.5, "HUD BRIGHTNESS - 50%")

	# Exterior lights
	pushSeqCmd(dt, 'EXTLIGHTS_SYSTEM.Master', 0) # 0 = OFF, 1 = ALL, 2 = A-C, 3 = FORM, 4 = NORM

	# UHF Radio
	pushSeqCmd(dt, 'UHF_CONTROL_PANEL.FunctionKnob', 1, "UHF FUNCTION KNOB - MAIN") # 0 = OFF, 1 = MAIN, 2 = BOTH, 3 = ADF

	# Left and right hardpoints on
	pushSeqCmd(dt, 'SMS.LeftHDPT', 1)
	pushSeqCmd(dt, 'SMS.RightHDPT', 1)

	# RWR
	pushSeqCmd(dt, 'RWR.Search', 1, "RWR INDICATOR SEARCH BUTTON - ON") # Press only

	# ECM
	pushSeqCmd(dt, 'ECM_INTERFACE.OneBtn', 1, "ECM 1 MODULE - ON")
	pushSeqCmd(dt, 'ECM_INTERFACE.TwoBtn', 1, "ECM 2 MODULE - ON")
	pushSeqCmd(dt, 'ECM_INTERFACE.ThreeBtn', 1, "ECM 3 MODULE - ON")
	pushSeqCmd(dt, 'ECM_INTERFACE.FourBtn', 1, "ECM 4 MODULE - ON")
	pushSeqCmd(dt, 'ECM_INTERFACE.FiveBtn', 1, "ECM 5 MODULE - ON")
	pushSeqCmd(dt, 'ECM_INTERFACE.SixBtn', 1, "ECM 6 MODULE - ON")

	setupMFDs(dt, seq, pushSeqCmd)

	# Laser arm switch - ARM
	pushSeqCmd(dt, 'SMS.LaserSw', 1)

	# Master arm switch - ARM
	pushSeqCmd(dt, 'MMC.MasterArmSw', 2)

	pushSeqCmd(dt, 'scriptSpeech', 'Manual steps remaining: Set cat 1 or cat 3.')

	return seq


def Shutdown(config, vars, helper, *args, **kwargs):
	seq = []
	dt = 0.3

	pushSeqCmd = helper.makePushSeqCmd(seq)

	pushSeqCmd(0, '', '', "Running Shutdown sequence")

	# AVIONICS POWER panel
	pushSeqCmd(dt, 'MMC.MmcPwr', 0) # MMC SWITCH - OFF
	pushSeqCmd(dt, 'SMS.StStaSw', 0) # ST STA SWITCH - OFF
	pushSeqCmd(dt, 'MMC.MFD', 0) # MFD SWITCH - OFF
	pushSeqCmd(dt, 'UFC.UFC_Sw', 0) #, "UFC SWITCH - OFF
	#pushSeqCmd(dt, 'MAP.PwrSw', 0) # MAP SWITCH - OFF (not used)
	pushSeqCmd(dt, 'GPS.PwrSw', 0) # GPS SWITCH - OFF
	#pushSeqCmd(dt, 'IDM.PwrSw', 0) # DL SWITCH - OFF (not used)
	pushSeqCmd(dt, 'MIDS.PwrSw', 0) # MDS LVT KNOB - OFF

	# INS off
	pushSeqCmd(dt, 'INS.ModeKnob', 0) # INS KNOB - OFF # 0 = OFF, 1 = STOR HDG, 2 = NORM, 3 = NAV, 4 = CAL, 5 = IN FLT ALIGN, 6 = ATT

	# SNSR PWR panel
	pushSeqCmd(dt, 'FCR.PwrSw', 0) # FCR SWITCH - OFF
	pushSeqCmd(dt, 'RALT.PwrSw', 0) # RDR ALT SWITCH - OFF

	pushSeqCmd(dt, 'HMCS.IntKnob', 0)
	pushSeqCmd(dt, 'UFC.SYM_Knob', 0)

	#pushSeqCmd(dt, 'SAI.reference', 0.5, "STANDBY ATTITUDE INDICATOR - UNCAGE AND CENTER")

	# UHF Radio
	pushSeqCmd(dt, 'UHF_CONTROL_PANEL.FunctionKnob', 0) # 0 = OFF, 1 = MAIN, 2 = BOTH, 3 = ADF

	# IFF
	pushSeqCmd(dt, 'IFF_CONTROL_PANEL.MasterKnob', 0) # 0 = OFF, 1 = STBY, 2 = LOW, 3 = NORM, 4 = EMER

	# CMDS panel
	pushSeqCmd(dt, 'CMDS.RwrSrc', 0, "CMDS RWR SWITCH - OFF")
	pushSeqCmd(dt, 'CMDS.JmrSrc', 0, "CMDS JMR SWITCH - OFF")
	pushSeqCmd(dt, 'CMDS.ChExp', 0, "CMDS CH SWITCH - OFF")
	pushSeqCmd(dt, 'CMDS.FlExp', 0, "CMDS FL SWITCH - OFF")
	pushSeqCmd(dt, 'CMDS.Mode', 0, "CMDS MODE KNOB - MAN (MANUAL CHAFF/FLARES)") # 0 = OFF, 1 = STBY, 2 = MAN, 3 = SEMI, 4 = AUTO, 5 = BYP

	# Left and right hardpoints off
	pushSeqCmd(dt, 'SMS.LeftHDPT', 0)
	pushSeqCmd(dt, 'SMS.RightHDPT', 0)

	# RWR
	pushSeqCmd(dt, 'RWR.Power', 1, "RWR INDICATOR CONTROL POWER - OFF") # Press only
	pushSeqCmd(dt, 'RWR.Search', 1, "RWR INDICATOR SEARCH BUTTON - OFF") # Press only

	# ECM
	# ECM POWER SWITCH - OFF
	pushSeqCmd(dt, 'ECM_INTERFACE.PwrSw', 1) # Must go through center position first.  0 = OFF, 1 = STBY, 2 = OPR
	pushSeqCmd(dt, 'ECM_INTERFACE.PwrSw', 0)
	# ECM modules OFF
	pushSeqCmd(dt, 'ECM_INTERFACE.OneBtn', 0, "ECM 1 MODULE - OFF")
	pushSeqCmd(dt, 'ECM_INTERFACE.TwoBtn', 0, "ECM 2 MODULE - OFF")
	pushSeqCmd(dt, 'ECM_INTERFACE.ThreeBtn', 0, "ECM 3 MODULE - OFF")
	pushSeqCmd(dt, 'ECM_INTERFACE.FourBtn', 0, "ECM 4 MODULE - OFF")
	pushSeqCmd(dt, 'ECM_INTERFACE.FiveBtn', 0, "ECM 5 MODULE - OFF")
	pushSeqCmd(dt, 'ECM_INTERFACE.SixBtn', 0, "ECM 6 MODULE - OFF")

	pushSeqCmd(dt, 'CPT_MECH.EjectionSafetyLever', 0, "EJECTION SAFETY LEVER - SAFE (UP)")
	pushSeqCmd(dt, 'GEAR_INTERFACE.AntiSkidSw', 2, "PARKING BRAKE/ANTI-SKID SWITCH - PARKING BRAKE") # 0 = OFF, 1 = ANTI-SKID, 2 = PARKING BRAKE

	# Probe Heat
	#FIXME: pushSeqCmd(dt, ELEC_INTERFACE, action = elec_commands.ProbeHeatSw, 0)

	# Interior lights
	pushSeqCmd(dt, 'CPTLIGHTS_SYSTEM.Consoles', 0)
	pushSeqCmd(dt, 'CPTLIGHTS_SYSTEM.IntsPnl', 0)
	pushSeqCmd(dt, 'CPTLIGHTS_SYSTEM.IndBrtAoA', 0)
	pushSeqCmd(dt, 'CPTLIGHTS_SYSTEM.IndBrtAR', 0)
	pushSeqCmd(dt, 'CPTLIGHTS_SYSTEM.ConsolesFlood', 0)
	pushSeqCmd(dt, 'CPTLIGHTS_SYSTEM.InstPnlFlood', 0)

	# Open canopy
	pushSeqCmd(dt, 'CPT_MECH.CanopyHandle', 0) # Unlock, up
	pushSeqCmd(dt, 'CPT_MECH.CanopySwitchClose', 2)
	pushSeqCmd(11, 'CPT_MECH.CanopySwitchClose', 1)

	# THROTTLE - OFF
	pushSeqCmd(dt, 'scriptSimCommand', 'iCommandLeftEngineStop') # Throttle OFF

	pushSeqCmd(dt, 'ELEC_INTERFACE.MainPwrSw', 0, "MAIN PWR SWITCH - ON") # 0 = OFF, 1 = BATT, 2 = MAIN PWR

	return seq


###############################################################################
###############################################################################
def LoadRoute(config, vars, helper, *args, **kwargs):
	seq = []
	dt = 0.3

	pushSeqCmd = helper.makePushSeqCmd(seq)

	def pressUfcButton(btn):
		btn = str(btn).upper()

		aliases = {
			'ENTR': 'UFC.ENTR',
			'RCL': 'UFC.RCL',
			'LIST': 'UFC.LIST',
			'N': 'UFC.DIG2_ALOW',
			'S': 'UFC.DIG8_FIX',
			'E': 'UFC.DIG6_TIME',
			'W': 'UFC.DIG4_STPT',
			'0': 'UFC.DIG0_M_SEL',
			'1': 'UFC.DIG1_T_ILS',
			'2': 'UFC.DIG2_ALOW',
			'3': 'UFC.DIG3',
			'4': 'UFC.DIG4_STPT',
			'5': 'UFC.DIG5_CRUS',
			'6': 'UFC.DIG6_TIME',
			'7': 'UFC.DIG7_MARK',
			'8': 'UFC.DIG8_FIX',
			'9': 'UFC.DIG9_A_CAL',
		}

		if btn == 'RTN':
			pushSeqCmd(dt, 'UFC.DCS_RTN', 1) # Press
			pushSeqCmd(dt, 'UFC.DCS_RTN', 0) # Release
		elif btn == 'SEQ':
			pushSeqCmd(dt, 'UFC.DCS_SEQ', 1) # Press
			pushSeqCmd(dt, 'UFC.DCS_SEQ', 0) # Release
		elif btn == 'UP':
			pushSeqCmd(dt, 'UFC.DCS_UP', 1) # Press
			pushSeqCmd(dt, 'UFC.DCS_UP', 0) # Release
		elif btn == 'DN':
			pushSeqCmd(dt, 'UFC.DCS_DOWN', 1) # Press
			pushSeqCmd(dt, 'UFC.DCS_DOWN', 0) # Release
		elif btn == 'INCR':
			pushSeqCmd(dt, 'UFC.DED_INC', 1) # Press
			pushSeqCmd(dt, 'UFC.DED_INC', 0) # Release
		elif btn == 'DECR':
			pushSeqCmd(dt, 'UFC.DED_DEC', 1) # Press
			pushSeqCmd(dt, 'UFC.DED_DEC', 0) # Release
		elif btn in aliases:
			pushSeqCmd(dt, aliases[btn], 1) # Press
			pushSeqCmd(dt, aliases[btn], 0) # Release
		else:
			raise ValueError(f'No ICP button for {btn!r}')

	def ddmDigits(deg, minutes, degreeDigits):
		# Round the whole value to 0.001 min so e.g. 59.9996 min carries into the degrees.
		wholeDeg, thousandths = divmod(round((abs(deg) * 60 + minutes) * 1000), 60000)
		return str(wholeDeg).zfill(degreeDigits) + str(thousandths).zfill(5)

	def enterUfcSequence(input):
		input = str(input).upper()
		for char in input:
			pressUfcButton(char)

	# Start sequence
	pushSeqCmd(0, '', '', 'Loading waypoints from file')
	routeData = helper.getRouteData(vars.get('routeFile'), vars.get('routeName'))
	if not routeData:
		pushSeqCmd(dt, '', '', 'Route selection cancelled.')
		return seq

	waypoints = routeData['waypoints']
	if not waypoints:
		pushSeqCmd(dt, '', '', 'No waypoints in route.')
		return seq

	pushSeqCmd(dt, 'scriptSpeech', f'Do not use any functions on UFC until waypoint entry is complete.')

	# Start entering waypoints.
	pressUfcButton('RTN') # Return to main UFC page.
	pressUfcButton('4') # STPT

	# Get the starting waypoint number from the user.
	startingWaypointNumber = vars.get('startingWaypoint')
	if startingWaypointNumber is None or int(startingWaypointNumber) < 1 or int(startingWaypointNumber) > 25:
		pushSeqCmd(dt, '', '', 'Waypoint entry cancelled.')
		return seq
	currentWaypointNumber = int(startingWaypointNumber)

	# Enter the starting waypoint, then move the cursor to the LAT field.
	enterUfcSequence(str(currentWaypointNumber))
	pressUfcButton('ENTR')
	pressUfcButton('DN')
	pressUfcButton('DN')

	waypointCount = len(waypoints)
	for waypointIndex, waypoint in enumerate(waypoints):
		pushSeqCmd(dt, 'scriptText', f'Entering waypoint {waypointIndex + 1}/{waypointCount} as waypoint {currentWaypointNumber}.')
		latLonDDM = waypoint['latLonDDM']

		# Enter latitude in DDM format.
		# If lat is positive, N; if negative, S.
		if latLonDDM['lat']['deg'] >= 0:
			pressUfcButton('N')
		else:
			pressUfcButton('S')
		enterUfcSequence(ddmDigits(latLonDDM['lat']['deg'], latLonDDM['lat']['min'], 2)) # DDMMmmm, no sign or decimal point.
		pressUfcButton('ENTR')
		pressUfcButton('DN')

		# Enter longitude in DDM format.
		# If lon is positive, E; if negative, W.
		if latLonDDM['lon']['deg'] >= 0:
			pressUfcButton('E')
		else:
			pressUfcButton('W')
		enterUfcSequence(ddmDigits(latLonDDM['lon']['deg'], latLonDDM['lon']['min'], 3)) # DDDMMmmm, no sign or decimal point.
		pressUfcButton('ENTR')
		pressUfcButton('DN')

		# Enter altitude in feet.
		if vars.get('altitude') == 'forceGround':
			altFeet = round(waypoint['groundAltFeet'])
		else:
			altFeet = round(waypoint.get('altFeet'))
		enterUfcSequence(altFeet)
		pressUfcButton('ENTR')
		pressUfcButton('UP')
		pressUfcButton('UP') # Set cursor back to LAT for next waypoint.

		# If we're not on the last waypoint, increment to the next waypoint.
		if waypointIndex != waypointCount - 1:
			currentWaypointNumber += 1
			pressUfcButton('INCR') # Up arrow

	return seq


###############################################################################
###############################################################################
def LoadScratchpad(config, vars, helper, *args, **kwargs):
	seq = []
	dt = 0.3

	pushSeqCmd = helper.makePushSeqCmd(seq)

	def pressUfcButton(btn):
		btn = str(btn).upper()

		aliases = {
			'ENTR': 'UFC.ENTR',
			'RCL': 'UFC.RCL',
			'LIST': 'UFC.LIST',
			'N': 'UFC.DIG2_ALOW',
			'S': 'UFC.DIG8_FIX',
			'E': 'UFC.DIG6_TIME',
			'W': 'UFC.DIG4_STPT',
			'0': 'UFC.DIG0_M_SEL',
			'1': 'UFC.DIG1_T_ILS',
			'2': 'UFC.DIG2_ALOW',
			'3': 'UFC.DIG3',
			'4': 'UFC.DIG4_STPT',
			'5': 'UFC.DIG5_CRUS',
			'6': 'UFC.DIG6_TIME',
			'7': 'UFC.DIG7_MARK',
			'8': 'UFC.DIG8_FIX',
			'9': 'UFC.DIG9_A_CAL',
		}

		if btn == 'RTN':
			pushSeqCmd(dt, 'UFC.DCS_RTN', 1) # Press
			pushSeqCmd(dt, 'UFC.DCS_RTN', 0) # Release
		elif btn == 'SEQ':
			pushSeqCmd(dt, 'UFC.DCS_SEQ', 1) # Press
			pushSeqCmd(dt, 'UFC.DCS_SEQ', 0) # Release
		elif btn == 'UP':
			pushSeqCmd(dt, 'UFC.DCS_UP', 1) # Press
			pushSeqCmd(dt, 'UFC.DCS_UP', 0) # Release
		elif btn == 'DN':
			pushSeqCmd(dt, 'UFC.DCS_DOWN', 1) # Press
			pushSeqCmd(dt, 'UFC.DCS_DOWN', 0) # Release
		elif btn == 'INCR':
			pushSeqCmd(dt, 'UFC.DED_INC', 1) # Press
			pushSeqCmd(dt, 'UFC.DED_INC', 0) # Release
		elif btn == 'DECR':
			pushSeqCmd(dt, 'UFC.DED_DEC', 1) # Press
			pushSeqCmd(dt, 'UFC.DED_DEC', 0) # Release
		elif btn in aliases:
			pushSeqCmd(dt, aliases[btn], 1) # Press
			pushSeqCmd(dt, aliases[btn], 0) # Release
		else:
			raise ValueError(f'No ICP button for {btn!r}')

	def ddmDigits(deg, minutes, degreeDigits):
		# Round the whole value to 0.001 min so e.g. 59.9996 min carries into the degrees.
		wholeDeg, thousandths = divmod(round((abs(deg) * 60 + minutes) * 1000), 60000)
		return str(wholeDeg).zfill(degreeDigits) + str(thousandths).zfill(5)

	def enterUfcSequence(input):
		input = str(input).upper()
		for char in input:
			pressUfcButton(char)

	# Start sequence
	pushSeqCmd(0, '', '', 'Loading waypoints from file')
	waypoints = helper.getScratchpadData(vars.get('scratchpadFile'))
	if not waypoints:
		pushSeqCmd(dt, 'scriptText', 'No waypoints found.')
		return seq

	pushSeqCmd(dt, 'scriptSpeech', f'Do not use any functions on UFC until waypoint entry is complete.')

	# Start entering waypoints.
	pressUfcButton('RTN') # Return to main UFC page.
	pressUfcButton('4') # STPT

	# Get the starting waypoint number from the user.
	startingWaypointNumber = vars.get('startingWaypoint')
	if startingWaypointNumber is None or int(startingWaypointNumber) < 1 or int(startingWaypointNumber) > 25:
		pushSeqCmd(dt, '', '', 'Waypoint entry cancelled.')
		return seq
	currentWaypointNumber = int(startingWaypointNumber)

	# Enter the starting waypoint, then move the cursor to the LAT field.
	enterUfcSequence(str(currentWaypointNumber))
	pressUfcButton('ENTR')
	pressUfcButton('DN')
	pressUfcButton('DN')

	waypointCount = len(waypoints)
	for waypointIndex, waypoint in enumerate(waypoints):
		pushSeqCmd(dt, 'scriptText', f'Entering waypoint {waypointIndex + 1}/{waypointCount} as waypoint {currentWaypointNumber}.')
		latLonDDM = waypoint['latLonDDM']

		# Enter latitude in DDM format.
		# If lat is positive, N; if negative, S.
		if latLonDDM['lat']['deg'] >= 0:
			pressUfcButton('N')
		else:
			pressUfcButton('S')
		enterUfcSequence(ddmDigits(latLonDDM['lat']['deg'], latLonDDM['lat']['min'], 2)) # DDMMmmm, no sign or decimal point.
		pressUfcButton('ENTR')
		pressUfcButton('DN')

		# Enter longitude in DDM format.
		# If lon is positive, E; if negative, W.
		if latLonDDM['lon']['deg'] >= 0:
			pressUfcButton('E')
		else:
			pressUfcButton('W')
		enterUfcSequence(ddmDigits(latLonDDM['lon']['deg'], latLonDDM['lon']['min'], 3)) # DDDMMmmm, no sign or decimal point.
		pressUfcButton('ENTR')
		pressUfcButton('DN')

		# Enter altitude in feet.
		if vars.get('altitude') == 'forceGround':
			altFeet = round(waypoint['groundAltFeet'])
		else:
			altFeet = round(waypoint.get('altFeet'))
		enterUfcSequence(altFeet)
		pressUfcButton('ENTR')
		pressUfcButton('UP')
		pressUfcButton('UP') # Set cursor back to LAT for next waypoint.

		# If we're not on the last waypoint, increment to the next waypoint.
		if waypointIndex != waypointCount - 1:
			currentWaypointNumber += 1
			pressUfcButton('INCR') # Up arrow

	return seq
