import math

# Return a Dictionary of script data.  The 'scripts' key is a list of scripts that users will be selecting from.  Each script has an associated 'function', which is the name of the function in this file that will be called to generate the command sequence, and a dictionary of 'vars' that the user will be prompted to choose from before running the script, and will be passed into the sequence generating function.
def getScriptData():
	return {
		'moduleName': 'AH-64D_BLK_II',
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
					'radar': {
						'label': 'Longbow Radar (FCR)',
						'options': {
							'detect': 'Check loadout at end',
							'equipped': 'Equipped',
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
					'radar': {
						'label': 'Longbow Radar (FCR)',
						'options': {
							'detect': 'Check loadout at end',
							'equipped': 'Equipped',
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
					'seat': {
						'label': 'Seat',
						'options': {
							'detect': 'Detect',
							'pilot': 'Pilot',
							'coPilot': 'Co-Pilot',
						},
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
					'seat': {
						'label': 'Seat',
						'options': {
							'detect': 'Detect',
							'pilot': 'Pilot',
							'coPilot': 'Co-Pilot',
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
			#		'radar': {
			#			'label': 'Longbow Radar (FCR)',
			#			'options': {
			#				'detect': 'Check loadout at end',
			#				'equipped': 'Equipped',
			#			},
			#		},
			#	},
			#},
		],
	}


def getInfo():
	return ''


def longbowEquipped(stations):
	"""True/False from LoGetPayloadInfo's Stations (a dict keyed by station number, or a list), or None if it isn't readable."""
	if isinstance(stations, dict):
		stations = stations.values()
	elif not isinstance(stations, list):
		return None
	return any(isinstance(station, dict) and station.get('CLSID') == '{AN_APG_78}' and station.get('count', 0) > 0 for station in stations)


def autoSelect(context):
	"""Set radar from the spawn loadout.  Without a radar, the start scripts check again at the end, in case one is added from the rearming screen."""
	payload = context.telemetry.get('LoGetPayloadInfo')
	equipped = longbowEquipped(payload.get('Stations') if isinstance(payload, dict) else None)
	if equipped is None:
		return {}
	if equipped:
		return {'vars': {'radar': 'equipped'}, 'reason': 'Longbow radar in the loadout'}
	return {'vars': {'radar': 'detect'}, 'reason': 'no Longbow radar in the loadout yet'}


def crewStation(vars, helper):
	"""'PLT' or 'CPG' for the seat var; for 'detect', from the player's seat in DCS (0 = pilot, 1 = CPG), or None if DCS didn't say.  Call in a live script."""
	seat = vars.get('seat')
	if seat == 'detect':
		seat = {0: 'pilot', 1: 'coPilot'}.get(helper.read('telemetry/LoGetPlayerSeat', default=None))
		if seat is None:
			return None
	return 'PLT' if seat == 'pilot' else 'CPG'


def pushFcrSteps(pushSeqCmd, dt, vars, helper):
	"""Turn on the FCR if the Longbow radar is fitted.  Call after a yield, as the last step, so a radar added during start-up is found."""
	if vars.get('radar') == 'equipped':
		equipped = True
	else:
		equipped = longbowEquipped(helper.read('telemetry/LoGetPayloadInfo.Stations', default=None))

	if equipped:
		pushSeqCmd(dt, 'scriptSpeech', "Longbow radar detected, powering on.")
		pushSeqCmd(dt, 'MFD_PLT_LEFT.FCR', 1) # FCR button
		pushSeqCmd(dt, 'MFD_PLT_LEFT.FCR', 0) # release
		pushSeqCmd(dt, 'MFD_PLT_LEFT.T6', 1) # UTIL
		pushSeqCmd(dt, 'MFD_PLT_LEFT.T6', 0) # release
		pushSeqCmd(dt, 'MFD_PLT_LEFT.R6', 1) # MMA PINNED (unbox)
		pushSeqCmd(dt, 'MFD_PLT_LEFT.R6', 0) # release
		pushSeqCmd(dt, 'MFD_PLT_LEFT.L4', 1) # FCR BIT OVERRIDE
		pushSeqCmd(dt, 'MFD_PLT_LEFT.L4', 0) # release
		pushSeqCmd(dt, 'MFD_PLT_LEFT.T6', 1) # UTIL
		pushSeqCmd(dt, 'MFD_PLT_LEFT.T6', 0) # release
		pushSeqCmd(dt, 'MFD_PLT_LEFT.VID', 1) # VID button to return to TADS video monitor page
		pushSeqCmd(dt, 'MFD_PLT_LEFT.VID', 0) # release
	else:
		pushSeqCmd(dt, 'scriptSpeech', "No Longbow radar detected. Power on FCR if equipped, FCR page, util, MMA pinned, FCR bit override.")


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

	alignTime = 4 * 60 # 4m0s
	engine1StartTime = 30
	engine2StartTime = 40

	# Function to reset Master Warning and Master Caution for both PLT and CPG.
	def resetMasterCautionWarning():
		# Reset Master Caution and Master Warning
		# PLT - MASTER WARNING - Reset
		pushSeqCmd(dt, 'CPTLIGHTS_SYSTEM.MasterWarningPLT', 1) # MSTR WARN
		pushSeqCmd(dt, 'CPTLIGHTS_SYSTEM.MasterWarningPLT', 0) # release
		# PLT - MASTER CAUTION - Reset
		pushSeqCmd(dt, 'CPTLIGHTS_SYSTEM.MasterCautionPLT', 1) # MSTR CAUT
		pushSeqCmd(dt, 'CPTLIGHTS_SYSTEM.MasterCautionPLT', 0) # release
		# CPG - MASTER WARNING - Reset
		pushSeqCmd(dt, 'CPTLIGHTS_SYSTEM.MasterWarningCPG', 1) # MSTR WARN
		pushSeqCmd(dt, 'CPTLIGHTS_SYSTEM.MasterWarningCPG', 0) # release
		# CPG - MASTER CAUTION - Reset
		pushSeqCmd(dt, 'CPTLIGHTS_SYSTEM.MasterCautionCPG', 1) # MSTR CAUT
		pushSeqCmd(dt, 'CPTLIGHTS_SYSTEM.MasterCautionCPG', 0) # release

	# Function to set all the PLT TSD SHOW options.
	def setPltTsdShowOptions():
		# PLT - TSD SHOW options - Set all ON (turn off as needed later)
		# Setting up NAV PHASE
		pushSeqCmd(dt, 'MFD_PLT_RIGHT.TSD', 1) # TSD
		pushSeqCmd(dt, 'MFD_PLT_RIGHT.TSD', 0) # release

		# NAV PHASE
		# SHOW page
		pushSeqCmd(dt, 'MFD_PLT_RIGHT.T3', 1) # SHOW
		pushSeqCmd(dt, 'MFD_PLT_RIGHT.T3', 0) # release
		pushSeqCmd(dt, 'MFD_PLT_RIGHT.L3', 1) # INACTIVE ZONES
		pushSeqCmd(dt, 'MFD_PLT_RIGHT.L3', 0) # release
		pushSeqCmd(dt, 'MFD_PLT_RIGHT.L5', 1) # CPG CURSOR
		pushSeqCmd(dt, 'MFD_PLT_RIGHT.L5', 0) # release
		pushSeqCmd(dt, 'MFD_PLT_RIGHT.L6', 1) # CURSOR INFO
		pushSeqCmd(dt, 'MFD_PLT_RIGHT.L6', 0) # release
		pushSeqCmd(dt, 'MFD_PLT_RIGHT.R4', 1) # HSI
		pushSeqCmd(dt, 'MFD_PLT_RIGHT.R4', 0) # release
		# THRT SHOW page
		pushSeqCmd(dt, 'MFD_PLT_RIGHT.T5', 1) # THRT SHOW
		pushSeqCmd(dt, 'MFD_PLT_RIGHT.T5', 0) # release
		pushSeqCmd(dt, 'MFD_PLT_RIGHT.R5', 1) # THREATS
		pushSeqCmd(dt, 'MFD_PLT_RIGHT.R5', 0) # release
		pushSeqCmd(dt, 'MFD_PLT_RIGHT.R6', 1) # TARGETS
		pushSeqCmd(dt, 'MFD_PLT_RIGHT.R6', 0) # release
		# COORD SHOW page
		pushSeqCmd(dt, 'MFD_PLT_RIGHT.T6', 1) # COORD SHOW
		pushSeqCmd(dt, 'MFD_PLT_RIGHT.T6', 0) # release
		pushSeqCmd(dt, 'MFD_PLT_RIGHT.L3', 1) # FRIENDLY UNITS
		pushSeqCmd(dt, 'MFD_PLT_RIGHT.L3', 0) # release
		pushSeqCmd(dt, 'MFD_PLT_RIGHT.L4', 1) # ENEMY UNITS
		pushSeqCmd(dt, 'MFD_PLT_RIGHT.L4', 0) # release
		pushSeqCmd(dt, 'MFD_PLT_RIGHT.L5', 1) # PLANNED TGTS/THREATS
		pushSeqCmd(dt, 'MFD_PLT_RIGHT.L5', 0) # release

		pushSeqCmd(dt, 'MFD_PLT_RIGHT.T6', 1) # COORD SHOW
		pushSeqCmd(dt, 'MFD_PLT_RIGHT.T6', 0) # release
		# now we're back to the TSD > SHOW page

		# ATK PHASE
		pushSeqCmd(dt, 'MFD_PLT_RIGHT.B2', 1) # PHASE (to ATK)
		pushSeqCmd(dt, 'MFD_PLT_RIGHT.B2', 0) # release
		# SHOW page
		pushSeqCmd(dt, 'MFD_PLT_RIGHT.L2', 1) # CURRENT ROUTE
		pushSeqCmd(dt, 'MFD_PLT_RIGHT.L2', 0) # release
		pushSeqCmd(dt, 'MFD_PLT_RIGHT.L5', 1) # CPG CURSOR
		pushSeqCmd(dt, 'MFD_PLT_RIGHT.L5', 0) # release
		pushSeqCmd(dt, 'MFD_PLT_RIGHT.L6', 1) # CURSOR INFO
		pushSeqCmd(dt, 'MFD_PLT_RIGHT.L6', 0) # release
		pushSeqCmd(dt, 'MFD_PLT_RIGHT.R4', 1) # HSI
		pushSeqCmd(dt, 'MFD_PLT_RIGHT.R4', 0) # release
		# THRT SHOW (already set from the NAV phase)
		# no action needed
		# COORD SHOW
		pushSeqCmd(dt, 'MFD_PLT_RIGHT.T6', 1) # COORD SHOW
		pushSeqCmd(dt, 'MFD_PLT_RIGHT.T6', 0) # release
		pushSeqCmd(dt, 'MFD_PLT_RIGHT.L4', 1) # ENEMY UNITS
		pushSeqCmd(dt, 'MFD_PLT_RIGHT.L4', 0) # release

		pushSeqCmd(dt, 'MFD_PLT_RIGHT.T3', 1) # SHOW
		pushSeqCmd(dt, 'MFD_PLT_RIGHT.T3', 0) # release
		# End TSD SHOW options, should now be back on the main TSD page.


	# Function to set all the CPG TSD SHOW options.
	def setCpgTsdShowOptions():
		# CPG - TSD SHOW options - Set all ON (turn off as needed later)
		# Setting up NAV PHASE
		pushSeqCmd(dt, 'MFD_CPG_RIGHT.TSD', 1) # TSD
		pushSeqCmd(dt, 'MFD_CPG_RIGHT.TSD', 0) # release

		# NAV PHASE
		# SHOW page
		pushSeqCmd(dt, 'MFD_CPG_RIGHT.T3', 1) # SHOW
		pushSeqCmd(dt, 'MFD_CPG_RIGHT.T3', 0) # release
		pushSeqCmd(dt, 'MFD_CPG_RIGHT.L3', 1) # INACTIVE ZONES
		pushSeqCmd(dt, 'MFD_CPG_RIGHT.L3', 0) # release
		pushSeqCmd(dt, 'MFD_CPG_RIGHT.L5', 1) # CPG CURSOR
		pushSeqCmd(dt, 'MFD_CPG_RIGHT.L5', 0) # release
		pushSeqCmd(dt, 'MFD_CPG_RIGHT.L6', 1) # CURSOR INFO
		pushSeqCmd(dt, 'MFD_CPG_RIGHT.L6', 0) # release
		pushSeqCmd(dt, 'MFD_CPG_RIGHT.R4', 1) # HSI
		pushSeqCmd(dt, 'MFD_CPG_RIGHT.R4', 0) # release
		# THRT SHOW page
		pushSeqCmd(dt, 'MFD_CPG_RIGHT.T5', 1) # THRT SHOW
		pushSeqCmd(dt, 'MFD_CPG_RIGHT.T5', 0) # release
		pushSeqCmd(dt, 'MFD_CPG_RIGHT.R5', 1) # THREATS
		pushSeqCmd(dt, 'MFD_CPG_RIGHT.R5', 0) # release
		pushSeqCmd(dt, 'MFD_CPG_RIGHT.R6', 1) # TARGETS
		pushSeqCmd(dt, 'MFD_CPG_RIGHT.R6', 0) # release
		# COORD SHOW
		pushSeqCmd(dt, 'MFD_CPG_RIGHT.T6', 1) # COORD SHOW
		pushSeqCmd(dt, 'MFD_CPG_RIGHT.T6', 0) # release
		pushSeqCmd(dt, 'MFD_CPG_RIGHT.L3', 1) # FRIENDLY UNITS
		pushSeqCmd(dt, 'MFD_CPG_RIGHT.L3', 0) # release
		pushSeqCmd(dt, 'MFD_CPG_RIGHT.L4', 1) # ENEMY UNITS
		pushSeqCmd(dt, 'MFD_CPG_RIGHT.L4', 0) # release
		pushSeqCmd(dt, 'MFD_CPG_RIGHT.L5', 1) # PLANNED TGTS/THREATS
		pushSeqCmd(dt, 'MFD_CPG_RIGHT.L5', 0) # release

		pushSeqCmd(dt, 'MFD_CPG_RIGHT.T6', 1) # COORD SHOW
		pushSeqCmd(dt, 'MFD_CPG_RIGHT.T6', 0) # release
		# now we're back to the TSD > SHOW page

		# ATK PHASE
		pushSeqCmd(dt, 'MFD_CPG_RIGHT.B2', 1) # PHASE (to ATK)
		pushSeqCmd(dt, 'MFD_CPG_RIGHT.B2', 0) # release
		# SHOW page
		pushSeqCmd(dt, 'MFD_CPG_RIGHT.L2', 1) # CURRENT ROUTE
		pushSeqCmd(dt, 'MFD_CPG_RIGHT.L2', 0) # release
		pushSeqCmd(dt, 'MFD_CPG_RIGHT.L5', 1) # CPG CURSOR
		pushSeqCmd(dt, 'MFD_CPG_RIGHT.L5', 0) # release
		pushSeqCmd(dt, 'MFD_CPG_RIGHT.L6', 1) # CURSOR INFO
		pushSeqCmd(dt, 'MFD_CPG_RIGHT.L6', 0) # release
		pushSeqCmd(dt, 'MFD_CPG_RIGHT.R4', 1) # HSI
		pushSeqCmd(dt, 'MFD_CPG_RIGHT.R4', 0) # release
		# THRT SHOW (already set from the NAV phase)
		# no action needed
		# COORD SHOW
		pushSeqCmd(dt, 'MFD_CPG_RIGHT.T6', 1) # COORD SHOW
		pushSeqCmd(dt, 'MFD_CPG_RIGHT.T6', 0) # release
		pushSeqCmd(dt, 'MFD_CPG_RIGHT.L4', 1) # ENEMY UNITS
		pushSeqCmd(dt, 'MFD_CPG_RIGHT.L4', 0) # release

		pushSeqCmd(dt, 'MFD_CPG_RIGHT.T3', 1) # SHOW
		pushSeqCmd(dt, 'MFD_CPG_RIGHT.T3', 0) # release
		# End TSD SHOW options, should now be back on the main TSD page.


	# Start sequence
	pushSeqCmd(0, '', '', "Running Cold Start sequence")
	pushSeqCmd(dt, 'scriptSpeech', 'Set collective full down.')

	# Canopy Door - Close
	pushSeqCmd(dt, 'CPT_MECH.PLT_Door_Lock', 0)
	pushSeqCmd(dt, 'CPT_MECH.CPG_Door_Lock', 0)

	# Parking Brake - SET
	pushSeqCmd(dt, 'GEAR_INTERFACE.AH64_ParkingBrake', 1)
	# RTR BRK switch - OFF
	pushSeqCmd(dt, 'HYDRO_INTERFACE.Rotor_Brake', 2)

	# Lights
	if vars.get('time') == 'day':
		# PLT Internal Lights
		pushSeqCmd(dt, 'CPTLIGHTS_SYSTEM.SignalPLT', 1.0)
		pushSeqCmd(dt, 'CPTLIGHTS_SYSTEM.PrimaryPLT', 1.0)
		pushSeqCmd(dt, 'CPTLIGHTS_SYSTEM.StbyInstPLT', 1.0)
		pushSeqCmd(dt, 'CPTLIGHTS_SYSTEM.FloodPLT', 0)
		# PLT External lights
		pushSeqCmd(dt, 'EXTLIGHTS_SYSTEM.NavLights', 1) # 0 = DIM, 1 = OFF, 2 = BRT
		pushSeqCmd(dt, 'EXTLIGHTS_SYSTEM.FormationLights', 0) # NOTE misspelling, 0 = off, int16 = full on
		pushSeqCmd(dt, 'EXTLIGHTS_SYSTEM.AntiCollLights', 1) # 0 = RED, 1 = OFF, 2 = WHT
		# PLT CMWS
		pushSeqCmd(dt, 'CMWS.CMWS_LAMP_KNOB', 1.0)
		# PLT IHADSS symbology brightness
		pushSeqCmd(dt, 'ELEC_INTERFACE.VCP_SYM_BRT_KNOB', 1.0)
		# PLT MPDs
		pushSeqCmd(dt, 'MFD_PLT_RIGHT.VID_KNOB', 0.25) # Makes the TSD page easier to read.

		# CPG Internal Lights
		pushSeqCmd(dt, 'CPTLIGHTS_SYSTEM.SignalCPG', 1.0)
		pushSeqCmd(dt, 'CPTLIGHTS_SYSTEM.PrimaryCPG', 1.0)
		# No CPG standby instruments light control.
		pushSeqCmd(dt, 'CPTLIGHTS_SYSTEM.FloodCPG', 0)
		#CPG MPDs
		pushSeqCmd(dt, 'MFD_CPG_RIGHT.VID_KNOB', 0.25) # Makes the TSD page easier to read.
	else:
		# PLT Internal Lights
		pushSeqCmd(dt, 'CPTLIGHTS_SYSTEM.SignalPLT', 0.5)
		pushSeqCmd(dt, 'CPTLIGHTS_SYSTEM.PrimaryPLT', 0.5)
		pushSeqCmd(dt, 'CPTLIGHTS_SYSTEM.StbyInstPLT', 0.5)
		pushSeqCmd(dt, 'CPTLIGHTS_SYSTEM.FloodPLT', 0)
		# PLT External lights
		pushSeqCmd(dt, 'EXTLIGHTS_SYSTEM.NavLights', 1) # 0 = DIM, 1 = OFF, 2 = BRT
		pushSeqCmd(dt, 'EXTLIGHTS_SYSTEM.FormationLights', 0) # NOTE misspelling, 0 = off, int16 = full on
		pushSeqCmd(dt, 'EXTLIGHTS_SYSTEM.AntiCollLights', 1) # 0 = RED, 1 = OFF, 2 = WHT
		# PLT MPDs
		pushSeqCmd(dt, 'MFD_PLT_LEFT.MODE_KNOB', 1) # 0 = MONO, 1 = NT, 2 = DAY
		pushSeqCmd(dt, 'MFD_PLT_LEFT.BRT_KNOB', 0.5)
		pushSeqCmd(dt, 'MFD_PLT_LEFT.VID_KNOB', 0.25)
		pushSeqCmd(dt, 'MFD_PLT_RIGHT.MODE_KNOB', 1) # 0 = MONO, 1 = NT, 2 = DAY
		pushSeqCmd(dt, 'MFD_PLT_RIGHT.BRT_KNOB', 0.5)
		pushSeqCmd(dt, 'MFD_PLT_RIGHT.VID_KNOB', 0.25)
		# PLT UFC
		pushSeqCmd(dt, 'EUFD_PLT.BRT', 0.25)
		# PLT KU
		pushSeqCmd(dt, 'KU_PLT.BrightnessKnob', 0.33)
		# PLT CMWS
		pushSeqCmd(dt, 'CMWS.CMWS_LAMP_KNOB', 0.25)
		# PLT FLIR Level (IHADSS FLIR brightness)
		pushSeqCmd(dt, 'ELEC_INTERFACE.VCP_FLIR_LEV_KNOB', 0.4)

		# CPG Internal Lights
		pushSeqCmd(dt, 'CPTLIGHTS_SYSTEM.SignalCPG', 0.5)
		pushSeqCmd(dt, 'CPTLIGHTS_SYSTEM.PrimaryCPG', 0.5)
		# No CPG standby instruments light control.
		pushSeqCmd(dt, 'CPTLIGHTS_SYSTEM.FloodCPG', 0)
		# CPG MPDs
		pushSeqCmd(dt, 'MFD_CPG_LEFT.MODE_KNOB', 1) # 0 = MONO, 1 = NT, 2 = DAY
		pushSeqCmd(dt, 'MFD_CPG_LEFT.BRT_KNOB', 0.5)
		pushSeqCmd(dt, 'MFD_CPG_LEFT.VID_KNOB', 0.25)
		pushSeqCmd(dt, 'MFD_CPG_RIGHT.MODE_KNOB', 1) # 0 = MONO, 1 = NT, 2 = DAY
		pushSeqCmd(dt, 'MFD_CPG_RIGHT.BRT_KNOB', 0.5)
		pushSeqCmd(dt, 'MFD_CPG_RIGHT.VID_KNOB', 0.25)
		# CPG UFC
		pushSeqCmd(dt, 'EUFD_CPG.BRT', 0.25)
		# CPG KU
		pushSeqCmd(dt, 'KU_CPG.BrightnessKnob', 0.33)
		# CPG FLIR Level (IHADSS FLIR brightness)
		# Controlled by buttons on TADS display.

	# MSTR IGN switch - BATT
	pushSeqCmd(dt, 'ELEC_INTERFACE.MIK', 1)

	# Radio volumes and squelch -- Do this immediately after turning on the battery so we don't get blasted by radio static while waiting for the APU.
	# PLT Radio squelch switches - ON (also squelches CPG radios)
	pushSeqCmd(dt, 'COMM_PANEL_PLT.VHF_SQL_OFF', 2)
	pushSeqCmd(dt, 'COMM_PANEL_PLT.VHF_SQL_OFF', 1)
	pushSeqCmd(dt, 'COMM_PANEL_PLT.UHF_SQL_OFF', 2)
	pushSeqCmd(dt, 'COMM_PANEL_PLT.UHF_SQL_OFF', 1)
	pushSeqCmd(dt, 'COMM_PANEL_PLT.FM1_SQL_OFF', 2)
	pushSeqCmd(dt, 'COMM_PANEL_PLT.FM1_SQL_OFF', 1)
	pushSeqCmd(dt, 'COMM_PANEL_PLT.FM2_SQL_OFF', 2)
	pushSeqCmd(dt, 'COMM_PANEL_PLT.FM2_SQL_OFF', 1)
	pushSeqCmd(dt, 'COMM_PANEL_PLT.HF_SQL_OFF', 2)
	pushSeqCmd(dt, 'COMM_PANEL_PLT.HF_SQL_OFF', 1)
	# PLT Radio RLWR volume - 75% # Already set by default.
	pushSeqCmd(dt, 'COMM_PANEL_PLT.RLWR_volume', 0.75)
	## CPG
	## CPG Radio squelch switches - ON
	#pushSeqCmd(dt, device = devices.COMM_PANEL_CPG, action = comm_commands.VHF_SQL, 1)
	#pushSeqCmd(dt, device = devices.COMM_PANEL_CPG, action = comm_commands.UHF_SQL, 1)
	#pushSeqCmd(dt, device = devices.COMM_PANEL_CPG, action = comm_commands.FM1_SQL, 1)
	#pushSeqCmd(dt, device = devices.COMM_PANEL_CPG, action = comm_commands.FM2_SQL, 1)
	#pushSeqCmd(dt, device = devices.COMM_PANEL_CPG, action = comm_commands.HF_SQL, 1)
	# CPG Radio RLWR volume - 75%
	pushSeqCmd(dt, 'COMM_PANEL_CPG.RLWR_volume', 0.75)

	# Starting APU (~30s)
	pushSeqCmd(dt, 'ENGINE_INTERFACE.APU_StartBtnCover', 1) # Cover open
	pushSeqCmd(dt, 'ENGINE_INTERFACE.APU_StartBtn', 1) # Press
	pushSeqCmd(dt, 'ENGINE_INTERFACE.APU_StartBtn', 0) # Release
	pushSeqCmd(dt, 'scriptCockpitState', control='AH-64D_BLK_II/arg.APUPLT', value=1) # Wait for APU Ready light to come on.

	# Alignment begins automatically after APU starts.
	# Waiting for EGI alignment, shows TSD chart background when finished (3m55s) ...
	pushSeqCmd(dt, 'scriptTimerStart', name='alignTimer', duration=alignTime)

	# After starting APU

	# TEDAC
	if vars.get('time') == 'day':
		pushSeqCmd(dt, 'TEDAC.TDU_MODE_KNOB', 2) # 0 = OFF, 1 = NT, 2 = DAY
	else:
		pushSeqCmd(dt, 'TEDAC.TDU_MODE_KNOB', 1) # 0 = OFF, 1 = NT, 2 = DAY

	# Use local time
	pushSeqCmd(dt, 'MFD_PLT_RIGHT.TSD', 1) # TSD
	pushSeqCmd(dt, 'MFD_PLT_RIGHT.TSD', 0) # release
	pushSeqCmd(dt, 'MFD_PLT_RIGHT.T6', 1) # UTIL
	pushSeqCmd(dt, 'MFD_PLT_RIGHT.T6', 0) # release
	pushSeqCmd(dt, 'MFD_PLT_RIGHT.R2', 1) # TIME
	pushSeqCmd(dt, 'MFD_PLT_RIGHT.R2', 0) # release
	pushSeqCmd(dt, 'MFD_PLT_RIGHT.T6', 1) # UTIL
	pushSeqCmd(dt, 'MFD_PLT_RIGHT.T6', 0) # release

	# TSD SHOW options
	setPltTsdShowOptions()
	setCpgTsdShowOptions()

	# CMWS
	# CMWS BYPASS/AUTO switch - BYPASS # Do this first to avoid any possibility of CMWS autodispensing countermeasures as soon as it's turned on, if there are emitters nearby.
	pushSeqCmd(dt, 'CMWS.CMWS_BYPASS_AUTO_SW', 1)
	# CMWS ARM/SAFE switch - ARM
	pushSeqCmd(dt, 'CMWS.CMWS_ARM_SAFE_SW', 1)
	# CMWS CMWS/NAV switch - CMWS
	pushSeqCmd(dt, 'CMWS.CMWS_CMWS_NAV_SW', 1)
	# CMWS PWR knob - ON
	pushSeqCmd(dt, 'CMWS.CMWS_PWR', 1)

	# GND ORIDE - ON (needed to arm chaff)
	pushSeqCmd(dt, 'ELEC_INTERFACE.GND_ORIDE_PLT_BTN', 1) # press
	pushSeqCmd(dt, 'ELEC_INTERFACE.GND_ORIDE_PLT_BTN', 0) # release

	# MASTER ARM - ON
	pushSeqCmd(dt, 'ELEC_INTERFACE.ARM_SAFE_PLT_BTN', 1) # press
	pushSeqCmd(dt, 'ELEC_INTERFACE.ARM_SAFE_PLT_BTN', 0) # release

	# ASE CHAFF - ARM
	pushSeqCmd(dt, 'MFD_PLT_LEFT.B1', 1) # MENU
	pushSeqCmd(dt, 'MFD_PLT_LEFT.B1', 0) # release
	pushSeqCmd(dt, 'MFD_PLT_LEFT.L3', 1) # ASE
	pushSeqCmd(dt, 'MFD_PLT_LEFT.L3', 0) # release
	pushSeqCmd(dt, 'MFD_PLT_LEFT.T1', 1) # CHAFF (to ARM)
	pushSeqCmd(dt, 'MFD_PLT_LEFT.T1', 0) # release
	# NOTE Set ASE AUTOPAGE - ACQUISITION at the end of the sequence.  If you start in a high-threat environment, it may autopage to the TSD while setting up other screens and mess up the startup sequence.

	# RLWR - ON
	pushSeqCmd(dt, 'MFD_PLT_LEFT.B1', 1) # MENU
	pushSeqCmd(dt, 'MFD_PLT_LEFT.B1', 0) # release
	pushSeqCmd(dt, 'MFD_PLT_LEFT.L3', 1) # ASE
	pushSeqCmd(dt, 'MFD_PLT_LEFT.L3', 0) # release
	pushSeqCmd(dt, 'MFD_PLT_LEFT.T6', 1) # UTIL
	pushSeqCmd(dt, 'MFD_PLT_LEFT.T6', 0) # release
	pushSeqCmd(dt, 'MFD_PLT_LEFT.R4', 1) # RLWR
	pushSeqCmd(dt, 'MFD_PLT_LEFT.R4', 0) # release

	# SAI
	# Standby Attitude Indicator - Uncage and center.
	pushSeqCmd(dt, 'SAI.CageKnobRotate', 0.5) # Rotate knob to center position.
	pushSeqCmd(dt, 'SAI.CageKnobPull', 0) # Push knob in.

	# Starting engines - PILOT
	# Starting engines (1m25s)
	# POWER levers - OFF
	pushSeqCmd(dt, 'ENGINE_INTERFACE.PLT_L_PowerLever', 0)
	pushSeqCmd(dt, 'ENGINE_INTERFACE.PLT_R_PowerLever', 0)

	# Go to ENG page
	pushSeqCmd(dt, 'MFD_PLT_LEFT.AC', 1) # A/C (goes directly to ENG page)
	pushSeqCmd(dt, 'MFD_PLT_LEFT.AC', 0) # release

	# Start first engine (30s)
	pushSeqCmd(dt, 'ENGINE_INTERFACE.Eng1IgnOrideSw', 2)
	pushSeqCmd(2, 'ENGINE_INTERFACE.Eng1IgnOrideSw', 1)
	pushSeqCmd(dt, 'scriptSimCommand', 'iCommandLeftEngineStart', 'Left throttle IDLE') # Left throttle IDLE
	pushSeqCmd(engine1StartTime, '','', "Engine 1 started")

	# Start second engine (40s)
	pushSeqCmd(dt, 'ENGINE_INTERFACE.Eng2IgnOrideSw', 2)
	pushSeqCmd(2, 'ENGINE_INTERFACE.Eng2IgnOrideSw', 1)
	pushSeqCmd(dt, 'scriptSimCommand', 'iCommandRightEngineStart', 'Right throttle IDLE') # Right throttle IDLE
	pushSeqCmd(engine2StartTime, '','', "Engine 2 started")

	# POWER levers - Smoothly to FLY
	powerLeverStart = 0.25 # Power levers start at 25% - IDLE.
	powerLeverEnd = 0.9 # Power levers end at 90% - FLY.
	powerLeverTime = 11 # Number of seconds to advance the power levers.  9 seconds is minimum to avoid "Rotor RPM Low" warning, ISA at sea level.  Default autostart is about 11 seconds.
	powerLeverDt = dt # Time between power lever steps.  If this is too fast, it could possibly lag or something on MP servers.
	powerLeverSteps = int((powerLeverTime / powerLeverDt) / 2) # Divide by 2 here because there are two power levers that need to be advanced.
	powerLeverIncrement = (powerLeverEnd - powerLeverStart) / powerLeverSteps # Increment (step size) is the total amount we need to go divided by the number of steps we're doing to get there.
	powerLeverPosition = powerLeverStart # Power lever starts at start position.
	for i in range(powerLeverSteps):
		powerLeverPosition += powerLeverIncrement # Add the step size to the lever position to make the next lever position.
		pushSeqCmd(powerLeverDt, 'ENGINE_INTERFACE.PLT_L_PowerLever', powerLeverPosition) # Lever position is absolute.
		pushSeqCmd(powerLeverDt, 'ENGINE_INTERFACE.PLT_R_PowerLever', powerLeverPosition) # Lever position is absolute.

	pushSeqCmd(7, '', '', "Np and Nr - Verify 101%")
	# APU - OFF
	pushSeqCmd(dt, 'ENGINE_INTERFACE.APU_StartBtn', 1) # Press
	pushSeqCmd(dt, 'ENGINE_INTERFACE.APU_StartBtn', 0) # Release
	pushSeqCmd(dt, 'ENGINE_INTERFACE.APU_StartBtnCover', 0) # Cover close
	# Engine start complete

	# After engine start
	# AUX fuel tank - ON (does nothing if AUX tank is not installed)
	pushSeqCmd(dt, 'MFD_PLT_LEFT.AC', 1) # A/C (goes directly to ENG page)
	pushSeqCmd(dt, 'MFD_PLT_LEFT.AC', 0) # release
	pushSeqCmd(dt, 'MFD_PLT_LEFT.T3', 1) # FUEL
	pushSeqCmd(dt, 'MFD_PLT_LEFT.T3', 0) # release
	pushSeqCmd(dt, 'MFD_PLT_LEFT.L2', 1) # C AUX
	pushSeqCmd(dt, 'MFD_PLT_LEFT.L2', 0) # release

	# WCA (Warning/Caution/Advisory) - RESET
	pushSeqCmd(dt, 'MFD_PLT_LEFT.B1', 1) # MENU
	pushSeqCmd(dt, 'MFD_PLT_LEFT.B1', 0) # release
	pushSeqCmd(dt, 'MFD_PLT_LEFT.B1', 1) # DMS
	pushSeqCmd(dt, 'MFD_PLT_LEFT.B1', 0) # release
	pushSeqCmd(dt, 'MFD_PLT_LEFT.B6', 1) # WCA
	pushSeqCmd(dt, 'MFD_PLT_LEFT.B6', 0) # release
	pushSeqCmd(dt, 'MFD_PLT_LEFT.B4', 1) # RESET
	pushSeqCmd(dt, 'MFD_PLT_LEFT.B4', 0) # release

	# PLT ACQ to TADS
	pushSeqCmd(dt, 'MFD_PLT_RIGHT.TSD', 1) # TSD
	pushSeqCmd(dt, 'MFD_PLT_RIGHT.TSD', 0) # release
	pushSeqCmd(dt, 'MFD_PLT_RIGHT.R6', 1) # ACQ
	pushSeqCmd(dt, 'MFD_PLT_RIGHT.R6', 0) # release
	pushSeqCmd(dt, 'MFD_PLT_RIGHT.B6', 1) # TADS
	pushSeqCmd(dt, 'MFD_PLT_RIGHT.B6', 0) # release

	# CPG ACQ to TADS
	pushSeqCmd(dt, 'MFD_CPG_RIGHT.TSD', 1) # TSD
	pushSeqCmd(dt, 'MFD_CPG_RIGHT.TSD', 0) # release
	pushSeqCmd(dt, 'MFD_CPG_RIGHT.R6', 1) # ACQ
	pushSeqCmd(dt, 'MFD_CPG_RIGHT.R6', 0) # release
	pushSeqCmd(dt, 'MFD_CPG_RIGHT.B6', 1) # TADS
	pushSeqCmd(dt, 'MFD_CPG_RIGHT.B6', 0) # release

	# PLT Weapon MAN RNG to 800 m (a more useful default)
	pushSeqCmd(dt, 'MFD_PLT_RIGHT.WPN', 1) # WPN
	pushSeqCmd(dt, 'MFD_PLT_RIGHT.WPN', 0) # release
	pushSeqCmd(dt, 'MFD_PLT_RIGHT.B6', 1) # MAN RNG>
	pushSeqCmd(dt, 'MFD_PLT_RIGHT.B6', 0) # release
	pushSeqCmd(dt, 'KU_PLT.key8', 1) # KU key press
	pushSeqCmd(dt, 'KU_PLT.key8', 0) # release
	pushSeqCmd(dt, 'KU_PLT.key0', 1) # KU key press
	pushSeqCmd(dt, 'KU_PLT.key0', 0) # release
	pushSeqCmd(dt, 'KU_PLT.key0', 1) # KU key press
	pushSeqCmd(dt, 'KU_PLT.key0', 0) # release
	pushSeqCmd(dt, 'KU_PLT.keyEnter', 1) # KU key press
	pushSeqCmd(dt, 'KU_PLT.keyEnter', 0) # release
	# Return to TSD.
	pushSeqCmd(dt, 'MFD_PLT_RIGHT.TSD', 1) # TSD
	pushSeqCmd(dt, 'MFD_PLT_RIGHT.TSD', 0) # release

	# CPG Weapon MAN RNG to 800 m (a more useful default)
	pushSeqCmd(dt, 'MFD_CPG_LEFT.WPN', 1) # WPN
	pushSeqCmd(dt, 'MFD_CPG_LEFT.WPN', 0) # release
	pushSeqCmd(dt, 'MFD_CPG_LEFT.B6', 1) # MAN RNG>
	pushSeqCmd(dt, 'MFD_CPG_LEFT.B6', 0) # release
	pushSeqCmd(dt, 'KU_CPG.key8', 1) # KU key press
	pushSeqCmd(dt, 'KU_CPG.key8', 0) # release
	pushSeqCmd(dt, 'KU_CPG.key0', 1) # KU key press
	pushSeqCmd(dt, 'KU_CPG.key0', 0) # release
	pushSeqCmd(dt, 'KU_CPG.key0', 1) # KU key press
	pushSeqCmd(dt, 'KU_CPG.key0', 0) # release
	pushSeqCmd(dt, 'KU_CPG.keyEnter', 1) # KU key press
	pushSeqCmd(dt, 'KU_CPG.keyEnter', 0) # release
	# CPG LASER - ON (enable laser) (start from WPN page)
	pushSeqCmd(dt, 'MFD_CPG_LEFT.T6', 1) # UTIL
	pushSeqCmd(dt, 'MFD_CPG_LEFT.T6', 0) # release
	pushSeqCmd(dt, 'MFD_CPG_LEFT.L6', 1) # LASER
	pushSeqCmd(dt, 'MFD_CPG_LEFT.L6', 0) # release
	pushSeqCmd(dt, 'MFD_CPG_LEFT.T6', 1) # UTIL
	pushSeqCmd(dt, 'MFD_CPG_LEFT.T6', 0) # release
	# leaves CPG on WPN page on left MFD

	# CPG TADS sensor select - TV for daytime, FLIR for night
	if vars.get('time') == 'day':
		pushSeqCmd(dt, 'TEDAC.LHG_TADS_SENSOR_SELECT_SW', 1) # 0 = DVO (not used), 1 = TV, 2 = FLIR (default)
	else:
		pushSeqCmd(dt, 'TEDAC.LHG_TADS_SENSOR_SELECT_SW', 2) # 0 = DVO (not used), 1 = TV, 2 = FLIR (default)

	# ASE AUTOPAGE - ACQUISITION (switches to TSD when being acquired/locked up)
	pushSeqCmd(dt, 'MFD_PLT_LEFT.B1', 1) # MENU
	pushSeqCmd(dt, 'MFD_PLT_LEFT.B1', 0) # release
	pushSeqCmd(dt, 'MFD_PLT_LEFT.L3', 1) # ASE
	pushSeqCmd(dt, 'MFD_PLT_LEFT.L3', 0) # release
	pushSeqCmd(dt, 'MFD_PLT_LEFT.R1', 1) # AUTOPAGE
	pushSeqCmd(dt, 'MFD_PLT_LEFT.R1', 0) # release
	pushSeqCmd(dt, 'MFD_PLT_LEFT.R2', 1) # ACQUISITION
	pushSeqCmd(dt, 'MFD_PLT_LEFT.R1', 0) # release

	# PLT Turn on C SCP
	pushSeqCmd(dt, 'MFD_PLT_LEFT.FCR', 1) # FCR
	pushSeqCmd(dt, 'MFD_PLT_LEFT.FCR', 0) # release
	pushSeqCmd(dt, 'MFD_PLT_LEFT.T1', 1) # C SCP
	pushSeqCmd(dt, 'MFD_PLT_LEFT.T1', 0) # release

	# PLT Show TADS video on left MFD
	pushSeqCmd(dt, 'MFD_PLT_LEFT.VID', 1) # VID
	pushSeqCmd(dt, 'MFD_PLT_LEFT.VID', 0) # release
	pushSeqCmd(dt, 'MFD_PLT_LEFT.R1', 1) # TADS
	pushSeqCmd(dt, 'MFD_PLT_LEFT.R1', 0) # release
	pushSeqCmd(dt, 'MFD_PLT_LEFT.T6', 1) # TADS
	pushSeqCmd(dt, 'MFD_PLT_LEFT.T6', 0) # release
	pushSeqCmd(dt, 'MFD_PLT_LEFT.L3', 1) # Z (zooms view)
	pushSeqCmd(dt, 'MFD_PLT_LEFT.L3', 0) # release

	# PLT IHADSS - Boresight
	pushSeqCmd(dt, 'MFD_PLT_RIGHT.WPN', 1) # WPN
	pushSeqCmd(dt, 'MFD_PLT_RIGHT.WPN', 0) # release
	pushSeqCmd(dt, 'MFD_PLT_RIGHT.L5', 1) # BORESIGHT
	pushSeqCmd(dt, 'MFD_PLT_RIGHT.L5', 0) # release
	pushSeqCmd(dt, 'MFD_PLT_RIGHT.L4', 1) # IHADSS
	pushSeqCmd(dt, 'MFD_PLT_RIGHT.L4', 0) # release

	yield # Run everything above, then check the loadout, in case the radar was added from the rearming screen during start-up.
	pushFcrSteps(pushSeqCmd, dt, vars, helper)

	pushSeqCmd(dt, 'scriptSpeech', "Manual steps remaining while waiting for alignment: Bore sight IHADSS. Set Hellfire seeker and laser designator codes.  Tune radios.  Set baro altitude.")

	# Wait until the alignment is complete (total process time minus the difference between now and when the process started).
	pushSeqCmd(dt, 'scriptTimerEnd', name='alignTimer')
	pushSeqCmd(dt, '', '', "Alignment should be complete.  If TSD map background is not showing, wait until it does.") # FIXME In some cases (high altitude?) the alignment may take longer.  There may be a way to check alignment status using cockpit indicators, but haven't investigated.

	return seq


###############################################################################
###############################################################################
def HotStart(config, vars, helper, *args, **kwargs):
	seq = []
	dt = 0.3

	pushSeqCmd = helper.makePushSeqCmd(seq)

	# Function to set all the PLT TSD SHOW options.
	def setPltTsdShowOptions():
		# PLT - TSD SHOW options - Set all ON (turn off as needed later)
		# Setting up NAV PHASE
		pushSeqCmd(dt, 'MFD_PLT_RIGHT.TSD', 1) # TSD
		pushSeqCmd(dt, 'MFD_PLT_RIGHT.TSD', 0) # release

		# NAV PHASE
		# SHOW page
		pushSeqCmd(dt, 'MFD_PLT_RIGHT.T3', 1) # SHOW
		pushSeqCmd(dt, 'MFD_PLT_RIGHT.T3', 0) # release
		pushSeqCmd(dt, 'MFD_PLT_RIGHT.L3', 1) # INACTIVE ZONES
		pushSeqCmd(dt, 'MFD_PLT_RIGHT.L3', 0) # release
		pushSeqCmd(dt, 'MFD_PLT_RIGHT.L5', 1) # CPG CURSOR
		pushSeqCmd(dt, 'MFD_PLT_RIGHT.L5', 0) # release
		pushSeqCmd(dt, 'MFD_PLT_RIGHT.L6', 1) # CURSOR INFO
		pushSeqCmd(dt, 'MFD_PLT_RIGHT.L6', 0) # release
		pushSeqCmd(dt, 'MFD_PLT_RIGHT.R4', 1) # HSI
		pushSeqCmd(dt, 'MFD_PLT_RIGHT.R4', 0) # release
		# THRT SHOW page
		pushSeqCmd(dt, 'MFD_PLT_RIGHT.T5', 1) # THRT SHOW
		pushSeqCmd(dt, 'MFD_PLT_RIGHT.T5', 0) # release
		pushSeqCmd(dt, 'MFD_PLT_RIGHT.R5', 1) # THREATS
		pushSeqCmd(dt, 'MFD_PLT_RIGHT.R5', 0) # release
		pushSeqCmd(dt, 'MFD_PLT_RIGHT.R6', 1) # TARGETS
		pushSeqCmd(dt, 'MFD_PLT_RIGHT.R6', 0) # release
		# COORD SHOW page
		pushSeqCmd(dt, 'MFD_PLT_RIGHT.T6', 1) # COORD SHOW
		pushSeqCmd(dt, 'MFD_PLT_RIGHT.T6', 0) # release
		pushSeqCmd(dt, 'MFD_PLT_RIGHT.L3', 1) # FRIENDLY UNITS
		pushSeqCmd(dt, 'MFD_PLT_RIGHT.L3', 0) # release
		pushSeqCmd(dt, 'MFD_PLT_RIGHT.L4', 1) # ENEMY UNITS
		pushSeqCmd(dt, 'MFD_PLT_RIGHT.L4', 0) # release
		pushSeqCmd(dt, 'MFD_PLT_RIGHT.L5', 1) # PLANNED TGTS/THREATS
		pushSeqCmd(dt, 'MFD_PLT_RIGHT.L5', 0) # release

		pushSeqCmd(dt, 'MFD_PLT_RIGHT.T6', 1) # COORD SHOW
		pushSeqCmd(dt, 'MFD_PLT_RIGHT.T6', 0) # release
		# now we're back to the TSD > SHOW page

		# ATK PHASE
		pushSeqCmd(dt, 'MFD_PLT_RIGHT.B2', 1) # PHASE (to ATK)
		pushSeqCmd(dt, 'MFD_PLT_RIGHT.B2', 0) # release
		# SHOW page
		pushSeqCmd(dt, 'MFD_PLT_RIGHT.L2', 1) # CURRENT ROUTE
		pushSeqCmd(dt, 'MFD_PLT_RIGHT.L2', 0) # release
		pushSeqCmd(dt, 'MFD_PLT_RIGHT.L5', 1) # CPG CURSOR
		pushSeqCmd(dt, 'MFD_PLT_RIGHT.L5', 0) # release
		pushSeqCmd(dt, 'MFD_PLT_RIGHT.L6', 1) # CURSOR INFO
		pushSeqCmd(dt, 'MFD_PLT_RIGHT.L6', 0) # release
		pushSeqCmd(dt, 'MFD_PLT_RIGHT.R4', 1) # HSI
		pushSeqCmd(dt, 'MFD_PLT_RIGHT.R4', 0) # release
		# THRT SHOW (already set from the NAV phase)
		# no action needed
		# COORD SHOW
		pushSeqCmd(dt, 'MFD_PLT_RIGHT.T6', 1) # COORD SHOW
		pushSeqCmd(dt, 'MFD_PLT_RIGHT.T6', 0) # release
		pushSeqCmd(dt, 'MFD_PLT_RIGHT.L4', 1) # ENEMY UNITS
		pushSeqCmd(dt, 'MFD_PLT_RIGHT.L4', 0) # release

		pushSeqCmd(dt, 'MFD_PLT_RIGHT.T3', 1) # SHOW
		pushSeqCmd(dt, 'MFD_PLT_RIGHT.T3', 0) # release
		# End TSD SHOW options, should now be back on the main TSD page.


	# Function to set all the CPG TSD SHOW options.
	def setCpgTsdShowOptions():
		# CPG - TSD SHOW options - Set all ON (turn off as needed later)
		# Setting up NAV PHASE
		pushSeqCmd(dt, 'MFD_CPG_RIGHT.TSD', 1) # TSD
		pushSeqCmd(dt, 'MFD_CPG_RIGHT.TSD', 0) # release

		# NAV PHASE
		# SHOW page
		pushSeqCmd(dt, 'MFD_CPG_RIGHT.T3', 1) # SHOW
		pushSeqCmd(dt, 'MFD_CPG_RIGHT.T3', 0) # release
		pushSeqCmd(dt, 'MFD_CPG_RIGHT.L3', 1) # INACTIVE ZONES
		pushSeqCmd(dt, 'MFD_CPG_RIGHT.L3', 0) # release
		pushSeqCmd(dt, 'MFD_CPG_RIGHT.L5', 1) # CPG CURSOR
		pushSeqCmd(dt, 'MFD_CPG_RIGHT.L5', 0) # release
		pushSeqCmd(dt, 'MFD_CPG_RIGHT.L6', 1) # CURSOR INFO
		pushSeqCmd(dt, 'MFD_CPG_RIGHT.L6', 0) # release
		pushSeqCmd(dt, 'MFD_CPG_RIGHT.R4', 1) # HSI
		pushSeqCmd(dt, 'MFD_CPG_RIGHT.R4', 0) # release
		# THRT SHOW page
		pushSeqCmd(dt, 'MFD_CPG_RIGHT.T5', 1) # THRT SHOW
		pushSeqCmd(dt, 'MFD_CPG_RIGHT.T5', 0) # release
		pushSeqCmd(dt, 'MFD_CPG_RIGHT.R5', 1) # THREATS
		pushSeqCmd(dt, 'MFD_CPG_RIGHT.R5', 0) # release
		pushSeqCmd(dt, 'MFD_CPG_RIGHT.R6', 1) # TARGETS
		pushSeqCmd(dt, 'MFD_CPG_RIGHT.R6', 0) # release
		# COORD SHOW
		pushSeqCmd(dt, 'MFD_CPG_RIGHT.T6', 1) # COORD SHOW
		pushSeqCmd(dt, 'MFD_CPG_RIGHT.T6', 0) # release
		pushSeqCmd(dt, 'MFD_CPG_RIGHT.L3', 1) # FRIENDLY UNITS
		pushSeqCmd(dt, 'MFD_CPG_RIGHT.L3', 0) # release
		pushSeqCmd(dt, 'MFD_CPG_RIGHT.L4', 1) # ENEMY UNITS
		pushSeqCmd(dt, 'MFD_CPG_RIGHT.L4', 0) # release
		pushSeqCmd(dt, 'MFD_CPG_RIGHT.L5', 1) # PLANNED TGTS/THREATS
		pushSeqCmd(dt, 'MFD_CPG_RIGHT.L5', 0) # release

		pushSeqCmd(dt, 'MFD_CPG_RIGHT.T6', 1) # COORD SHOW
		pushSeqCmd(dt, 'MFD_CPG_RIGHT.T6', 0) # release
		# now we're back to the TSD > SHOW page

		# ATK PHASE
		pushSeqCmd(dt, 'MFD_CPG_RIGHT.B2', 1) # PHASE (to ATK)
		pushSeqCmd(dt, 'MFD_CPG_RIGHT.B2', 0) # release
		# SHOW page
		pushSeqCmd(dt, 'MFD_CPG_RIGHT.L2', 1) # CURRENT ROUTE
		pushSeqCmd(dt, 'MFD_CPG_RIGHT.L2', 0) # release
		pushSeqCmd(dt, 'MFD_CPG_RIGHT.L5', 1) # CPG CURSOR
		pushSeqCmd(dt, 'MFD_CPG_RIGHT.L5', 0) # release
		pushSeqCmd(dt, 'MFD_CPG_RIGHT.L6', 1) # CURSOR INFO
		pushSeqCmd(dt, 'MFD_CPG_RIGHT.L6', 0) # release
		pushSeqCmd(dt, 'MFD_CPG_RIGHT.R4', 1) # HSI
		pushSeqCmd(dt, 'MFD_CPG_RIGHT.R4', 0) # release
		# THRT SHOW (already set from the NAV phase)
		# no action needed
		# COORD SHOW
		pushSeqCmd(dt, 'MFD_CPG_RIGHT.T6', 1) # COORD SHOW
		pushSeqCmd(dt, 'MFD_CPG_RIGHT.T6', 0) # release
		pushSeqCmd(dt, 'MFD_CPG_RIGHT.L4', 1) # ENEMY UNITS
		pushSeqCmd(dt, 'MFD_CPG_RIGHT.L4', 0) # release

		pushSeqCmd(dt, 'MFD_CPG_RIGHT.T3', 1) # SHOW
		pushSeqCmd(dt, 'MFD_CPG_RIGHT.T3', 0) # release
		# End TSD SHOW options, should now be back on the main TSD page.

	# Start sequence
	pushSeqCmd(0, '', '', "Running Hot Start sequence")

	# NOTE Advancing the power levers was sometime required in the past, but now doesn't seem to be, so commenting this section out, but leaving it in case its needed again.
	## POWER levers - Smoothly to FLY
	#powerLeverStart = 0.25 # Power levers start at 25% - IDLE.
	#powerLeverEnd = 0.9 # Power levers end at 90% - FLY.
	#powerLeverTime = 11 # Number of seconds to advance the power levers.  9 seconds is minimum to avoid "Rotor RPM Low" warning, ISA at sea level.  Default autostart is about 11 seconds.
	#powerLeverDt = dt # Time between power lever steps.  If this is too fast, it could possibly lag or something on MP servers.
	#powerLeverSteps = int((powerLeverTime / powerLeverDt) / 2) # Divide by 2 here because there are two power levers that need to be advanced.
	#powerLeverIncrement = (powerLeverEnd - powerLeverStart) / powerLeverSteps # Increment (step size) is the total amount we need to go divided by the number of steps we're doing to get there.
	#powerLeverPosition = powerLeverStart # Power lever starts at start position.
	#for i in range(powerLeverSteps):
	#	powerLeverPosition += powerLeverIncrement # Add the step size to the lever position to make the next lever position.
	#	pushSeqCmd(powerLeverDt, 'ENGINE_INTERFACE.PLT_L_PowerLever', powerLeverPosition) # Lever position is absolute.
	#	pushSeqCmd(powerLeverDt, 'ENGINE_INTERFACE.PLT_R_PowerLever', powerLeverPosition) # Lever position is absolute.

	# Lights
	if vars.get('time') == 'day':
		# PLT Internal Lights
		pushSeqCmd(dt, 'CPTLIGHTS_SYSTEM.SignalPLT', 1.0)
		pushSeqCmd(dt, 'CPTLIGHTS_SYSTEM.PrimaryPLT', 1.0)
		pushSeqCmd(dt, 'CPTLIGHTS_SYSTEM.StbyInstPLT', 1.0)
		pushSeqCmd(dt, 'CPTLIGHTS_SYSTEM.FloodPLT', 0)
		# PLT External lights
		pushSeqCmd(dt, 'EXTLIGHTS_SYSTEM.NavLights', 1) # 0 = DIM, 1 = OFF, 2 = BRT
		pushSeqCmd(dt, 'EXTLIGHTS_SYSTEM.FormationLights', 0) # NOTE misspelling, 0 = off, int16 = full on
		pushSeqCmd(dt, 'EXTLIGHTS_SYSTEM.AntiCollLights', 1) # 0 = RED, 1 = OFF, 2 = WHT
		# PLT CMWS
		pushSeqCmd(dt, 'CMWS.CMWS_LAMP_KNOB', 1.0)
		# PLT IHADSS symbology brightness
		pushSeqCmd(dt, 'ELEC_INTERFACE.VCP_SYM_BRT_KNOB', 1.0)
		# PLT MPDs
		pushSeqCmd(dt, 'MFD_PLT_RIGHT.VID_KNOB', 0.25) # Makes the TSD page easier to read.

		# CPG Internal Lights
		pushSeqCmd(dt, 'CPTLIGHTS_SYSTEM.SignalCPG', 1.0)
		pushSeqCmd(dt, 'CPTLIGHTS_SYSTEM.PrimaryCPG', 1.0)
		# No CPG standby instruments light control.
		pushSeqCmd(dt, 'CPTLIGHTS_SYSTEM.FloodCPG', 0)
		# CPG MPDs
		pushSeqCmd(dt, 'MFD_CPG_RIGHT.VID_KNOB', 0.25) # Makes the TSD page easier to read.

	else:
		# PLT Internal Lights
		pushSeqCmd(dt, 'CPTLIGHTS_SYSTEM.SignalPLT', 0.5)
		pushSeqCmd(dt, 'CPTLIGHTS_SYSTEM.PrimaryPLT', 0.5)
		pushSeqCmd(dt, 'CPTLIGHTS_SYSTEM.StbyInstPLT', 0.5)
		pushSeqCmd(dt, 'CPTLIGHTS_SYSTEM.FloodPLT', 0)
		# PLT External lights
		pushSeqCmd(dt, 'EXTLIGHTS_SYSTEM.NavLights', 1) # 0 = DIM, 1 = OFF, 2 = BRT
		pushSeqCmd(dt, 'EXTLIGHTS_SYSTEM.FormationLights', 0) # NOTE misspelling, 0 = off, int16 = full on
		pushSeqCmd(dt, 'EXTLIGHTS_SYSTEM.AntiCollLights', 1) # 0 = RED, 1 = OFF, 2 = WHT
		# PLT MPDs
		pushSeqCmd(dt, 'MFD_PLT_LEFT.MODE_KNOB', 1) # 0 = MONO, 1 = NT, 2 = DAY
		pushSeqCmd(dt, 'MFD_PLT_LEFT.BRT_KNOB', 0.5)
		pushSeqCmd(dt, 'MFD_PLT_LEFT.VID_KNOB', 0.25)
		pushSeqCmd(dt, 'MFD_PLT_RIGHT.MODE_KNOB', 1) # 0 = MONO, 1 = NT, 2 = DAY
		pushSeqCmd(dt, 'MFD_PLT_RIGHT.BRT_KNOB', 0.5)
		pushSeqCmd(dt, 'MFD_PLT_RIGHT.VID_KNOB', 0.25)
		# PLT UFC
		pushSeqCmd(dt, 'EUFD_PLT.BRT', 0.25)
		# PLT KU
		pushSeqCmd(dt, 'KU_PLT.BrightnessKnob', 0.33)
		# PLT CMWS
		pushSeqCmd(dt, 'CMWS.CMWS_LAMP_KNOB', 0.25)
		# PLT FLIR Level (IHADSS FLIR brightness)
		pushSeqCmd(dt, 'ELEC_INTERFACE.VCP_FLIR_LEV_KNOB', 0.4)

		# CPG Internal Lights
		pushSeqCmd(dt, 'CPTLIGHTS_SYSTEM.SignalCPG', 0.5)
		pushSeqCmd(dt, 'CPTLIGHTS_SYSTEM.PrimaryCPG', 0.5)
		# No CPG standby instruments light control.
		pushSeqCmd(dt, 'CPTLIGHTS_SYSTEM.FloodCPG', 0)
		# CPG MPDs
		pushSeqCmd(dt, 'MFD_CPG_LEFT.MODE_KNOB', 1) # 0 = MONO, 1 = NT, 2 = DAY
		pushSeqCmd(dt, 'MFD_CPG_LEFT.BRT_KNOB', 0.5)
		pushSeqCmd(dt, 'MFD_CPG_LEFT.VID_KNOB', 0.25)
		pushSeqCmd(dt, 'MFD_CPG_RIGHT.MODE_KNOB', 1) # 0 = MONO, 1 = NT, 2 = DAY
		pushSeqCmd(dt, 'MFD_CPG_RIGHT.BRT_KNOB', 0.5)
		pushSeqCmd(dt, 'MFD_CPG_RIGHT.VID_KNOB', 0.25)
		# CPG UFC
		pushSeqCmd(dt, 'EUFD_CPG.BRT', 0.25)
		# CPG KU
		pushSeqCmd(dt, 'KU_CPG.BrightnessKnob', 0.33)
		# CPG FLIR Level (IHADSS FLIR brightness)
		# Controlled by buttons on TADS display.

	# Radio volumes and squelch
	# PLT Radio RLWR volume - 75%
	pushSeqCmd(dt, 'COMM_PANEL_PLT.RLWR_volume', 0.75)
	# CPG Radio RLWR volume - 75%
	pushSeqCmd(dt, 'COMM_PANEL_CPG.RLWR_volume', 0.75)

	# TEDAC
	if vars.get('time') == 'day':
		pushSeqCmd(dt, 'TEDAC.TDU_MODE_KNOB', 2) # 0 = OFF, 1 = NT, 2 = DAY
	else:
		pushSeqCmd(dt, 'TEDAC.TDU_MODE_KNOB', 1) # 0 = OFF, 1 = NT, 2 = DAY

	# Use local time
	pushSeqCmd(dt, 'MFD_PLT_RIGHT.TSD', 1) # TSD
	pushSeqCmd(dt, 'MFD_PLT_RIGHT.TSD', 0) # release
	pushSeqCmd(dt, 'MFD_PLT_RIGHT.T6', 1) # UTIL
	pushSeqCmd(dt, 'MFD_PLT_RIGHT.T6', 0) # release
	pushSeqCmd(dt, 'MFD_PLT_RIGHT.R2', 1) # TIME
	pushSeqCmd(dt, 'MFD_PLT_RIGHT.R2', 0) # release
	pushSeqCmd(dt, 'MFD_PLT_RIGHT.T6', 1) # UTIL
	pushSeqCmd(dt, 'MFD_PLT_RIGHT.T6', 0) # release

	# TSD SHOW options
	setPltTsdShowOptions()
	setCpgTsdShowOptions()

	# CMWS
	# CMWS ARM/SAFE switch - ARM
	pushSeqCmd(dt, 'CMWS.CMWS_ARM_SAFE_SW', 1)
	# CMWS CMWS/NAV switch - CMWS
	pushSeqCmd(dt, 'CMWS.CMWS_CMWS_NAV_SW', 1)
	# CMWS BYPASS/AUTO switch - BYPASS
	pushSeqCmd(dt, 'CMWS.CMWS_BYPASS_AUTO_SW', 1)
	# CMWS PWR knob - ON
	pushSeqCmd(dt, 'CMWS.CMWS_PWR', 1)

	# GND ORIDE - ON (needed to arm chaff)
	pushSeqCmd(dt, 'ELEC_INTERFACE.GND_ORIDE_PLT_BTN', 1) # Press
	pushSeqCmd(dt, 'ELEC_INTERFACE.GND_ORIDE_PLT_BTN', 0) # Release

	# MASTER ARM - ON
	pushSeqCmd(dt, 'ELEC_INTERFACE.ARM_SAFE_PLT_BTN', 1) # press
	pushSeqCmd(dt, 'ELEC_INTERFACE.ARM_SAFE_PLT_BTN', 0) # release

	# ASE CHAFF - ARM
	pushSeqCmd(dt, 'MFD_PLT_LEFT.B1', 1) # MENU
	pushSeqCmd(dt, 'MFD_PLT_LEFT.B1', 0) # release
	pushSeqCmd(dt, 'MFD_PLT_LEFT.L3', 1) # ASE
	pushSeqCmd(dt, 'MFD_PLT_LEFT.L3', 0) # release
	pushSeqCmd(dt, 'MFD_PLT_LEFT.T1', 1) # CHAFF (to ARM)
	pushSeqCmd(dt, 'MFD_PLT_LEFT.T1', 0) # release
	# NOTE Set ASE AUTOPAGE - ACQUISITION at the end of the sequence.  If you start in a high-threat environment, it may autopage to the TSD while setting up other screens and mess up the startup sequence.

	# AUX fuel tank - ON (does nothing if AUX tank is not installed)
	pushSeqCmd(dt, 'MFD_PLT_LEFT.AC', 1) # A/C (goes directly to ENG page)
	pushSeqCmd(dt, 'MFD_PLT_LEFT.AC', 0) # release
	pushSeqCmd(dt, 'MFD_PLT_LEFT.T3', 1) # FUEL
	pushSeqCmd(dt, 'MFD_PLT_LEFT.T3', 0) # release
	pushSeqCmd(dt, 'MFD_PLT_LEFT.L2', 1) # C AUX
	pushSeqCmd(dt, 'MFD_PLT_LEFT.L2', 0) # release

	# CPG ACQ to TADS
	pushSeqCmd(dt, 'MFD_CPG_RIGHT.TSD', 1) # TSD
	pushSeqCmd(dt, 'MFD_CPG_RIGHT.TSD', 0) # release
	pushSeqCmd(dt, 'MFD_CPG_RIGHT.R6', 1) # ACQ
	pushSeqCmd(dt, 'MFD_CPG_RIGHT.R6', 0) # release
	pushSeqCmd(dt, 'MFD_CPG_RIGHT.B6', 1) # TADS
	pushSeqCmd(dt, 'MFD_CPG_RIGHT.B6', 0) # release

	# PLT Weapon MAN RNG to 800 m (a more useful default)
	pushSeqCmd(dt, 'MFD_PLT_RIGHT.WPN', 1) # WPN
	pushSeqCmd(dt, 'MFD_PLT_RIGHT.WPN', 0) # release
	pushSeqCmd(dt, 'MFD_PLT_RIGHT.B6', 1) # MAN RNG>
	pushSeqCmd(dt, 'MFD_PLT_RIGHT.B6', 0) # release
	pushSeqCmd(dt, 'KU_PLT.key8', 1) # KU key press
	pushSeqCmd(dt, 'KU_PLT.key8', 0) # release
	pushSeqCmd(dt, 'KU_PLT.key0', 1) # KU key press
	pushSeqCmd(dt, 'KU_PLT.key0', 0) # release
	pushSeqCmd(dt, 'KU_PLT.key0', 1) # KU key press
	pushSeqCmd(dt, 'KU_PLT.key0', 0) # release
	pushSeqCmd(dt, 'KU_PLT.keyEnter', 1) # KU key press
	pushSeqCmd(dt, 'KU_PLT.keyEnter', 0) # release
	# Return to TSD.
	pushSeqCmd(dt, 'MFD_PLT_RIGHT.TSD', 1) # TSD
	pushSeqCmd(dt, 'MFD_PLT_RIGHT.TSD', 0) # release

	# CPG Weapon MAN RNG to 800 m (a more useful default)
	pushSeqCmd(dt, 'MFD_CPG_LEFT.WPN', 1) # WPN
	pushSeqCmd(dt, 'MFD_CPG_LEFT.WPN', 0) # release
	pushSeqCmd(dt, 'MFD_CPG_LEFT.B6', 1) # MAN RNG>
	pushSeqCmd(dt, 'MFD_CPG_LEFT.B6', 0) # release
	pushSeqCmd(dt, 'KU_CPG.key8', 1) # KU key press
	pushSeqCmd(dt, 'KU_CPG.key8', 0) # release
	pushSeqCmd(dt, 'KU_CPG.key0', 1) # KU key press
	pushSeqCmd(dt, 'KU_CPG.key0', 0) # release
	pushSeqCmd(dt, 'KU_CPG.key0', 1) # KU key press
	pushSeqCmd(dt, 'KU_CPG.key0', 0) # release
	pushSeqCmd(dt, 'KU_CPG.keyEnter', 1) # KU key press
	pushSeqCmd(dt, 'KU_CPG.keyEnter', 0) # release

	# CPG Laser Tracker - OFF # FIXME This is a bug, it should start off, but currently starts on.  Should be fixed in DCS soon, at which point this command can be removed.
	pushSeqCmd(dt, 'TEDAC.RHG_LT_SW', 1) # 0 = M (manual), 1 = O (off), 2 = A (automatic)

	# CPG TADS sensor select - TV for daytime, FLIR for night
	if vars.get('time') == 'day':
		pushSeqCmd(dt, 'TEDAC.LHG_TADS_SENSOR_SELECT_SW', 1) # 0 = DVO (not used), 1 = TV, 2 = FLIR (default)
	else:
		pushSeqCmd(dt, 'TEDAC.LHG_TADS_SENSOR_SELECT_SW', 2) # 0 = DVO (not used), 1 = TV, 2 = FLIR (default)

	# ASE AUTOPAGE - ACQUISITION (switches to TSD when being acquired/locked up)
	pushSeqCmd(dt, 'MFD_PLT_LEFT.B1', 1) # MENU
	pushSeqCmd(dt, 'MFD_PLT_LEFT.B1', 0) # release
	pushSeqCmd(dt, 'MFD_PLT_LEFT.L3', 1) # ASE
	pushSeqCmd(dt, 'MFD_PLT_LEFT.L3', 0) # release
	pushSeqCmd(dt, 'MFD_PLT_LEFT.R1', 1) # AUTOPAGE
	pushSeqCmd(dt, 'MFD_PLT_LEFT.R1', 0) # release
	pushSeqCmd(dt, 'MFD_PLT_LEFT.R2', 1) # ACQUISITION
	pushSeqCmd(dt, 'MFD_PLT_LEFT.R1', 0) # release

	# PLT Turn on C SCP
	pushSeqCmd(dt, 'MFD_PLT_LEFT.FCR', 1) # FCR
	pushSeqCmd(dt, 'MFD_PLT_LEFT.FCR', 0) # release
	pushSeqCmd(dt, 'MFD_PLT_LEFT.T1', 1) # C SCP
	pushSeqCmd(dt, 'MFD_PLT_LEFT.T1', 0) # release

	# PLT Show TADS video on left MFD
	pushSeqCmd(dt, 'MFD_PLT_LEFT.VID', 1) # VID
	pushSeqCmd(dt, 'MFD_PLT_LEFT.VID', 0) # release
	pushSeqCmd(dt, 'MFD_PLT_LEFT.R1', 1) # TADS
	pushSeqCmd(dt, 'MFD_PLT_LEFT.R1', 0) # release
	pushSeqCmd(dt, 'MFD_PLT_LEFT.T6', 1) # TADS
	pushSeqCmd(dt, 'MFD_PLT_LEFT.T6', 0) # release
	pushSeqCmd(dt, 'MFD_PLT_LEFT.L3', 1) # Z (zooms view)
	pushSeqCmd(dt, 'MFD_PLT_LEFT.L3', 0) # release

	yield # Run everything above, then check the loadout, in case the radar was added from the rearming screen during start-up.
	pushFcrSteps(pushSeqCmd, dt, vars, helper)

	pushSeqCmd(dt, 'scriptSpeech', "Manual steps remaining: Set Hellfire seeker and laser designator codes.  Tune radios.")

	return seq


###############################################################################
###############################################################################
def Shutdown(config, vars, helper, *args, **kwargs):
	seq = []
	dt = 0.3

	pushSeqCmd = helper.makePushSeqCmd(seq)

	# Start sequence
	pushSeqCmd(0, '', '', "Running Shutdown sequence")
	#pushSeqCmd(dt, 'scriptSpeech', 'Set collective full down.')

	# Parking Brake - SET
	pushSeqCmd(dt, 'GEAR_INTERFACE.AH64_ParkingBrake', 1)

	# SAI
	# Standby Attitude Indicator - Cage.
	pushSeqCmd(dt, 'SAI.CageKnobPull', 1) # Pull knob to cage, and hold.
	pushSeqCmd(dt, 'SAI.CageKnobRotate', 0.9) # Rotate knob to max position (past cage point).
	pushSeqCmd(dt, 'SAI.CageKnobPull', 0) # Push knob in, but it will stay pulled out because it's rotated past the caged point.

	# Start APU to provide power during shutdown sequence.
	# Starting APU (~30s)
	pushSeqCmd(dt, 'ENGINE_INTERFACE.APU_StartBtnCover', 1) # Cover open
	pushSeqCmd(dt, 'ENGINE_INTERFACE.APU_StartBtn', 1) # Press
	pushSeqCmd(dt, 'ENGINE_INTERFACE.APU_StartBtn', 0) # Release
	pushSeqCmd(dt, 'scriptCockpitState', control='AH-64D_BLK_II/arg.APUPLT', value=1) # Wait for APU Ready light to come on.

	# POWER levers - IDLE
	pushSeqCmd(dt, 'ENGINE_INTERFACE.PLT_L_PowerLever', 0.25)
	pushSeqCmd(dt, 'ENGINE_INTERFACE.PLT_R_PowerLever', 0.25)
	pushSeqCmd(15, '', '', 'Wait 15 seconds for engines to spool down.')

	# Left engine OFF
	pushSeqCmd(dt, 'scriptSimCommand', 'iCommandLeftEngineStop', 'Left throttle OFF') # Left throttle OFF

	# Right engine OFF
	pushSeqCmd(dt, 'scriptSimCommand', 'iCommandRightEngineStop', 'Right throttle OFF') # Right throttle OFF

	# Lights
	# PLT Internal Lights
	pushSeqCmd(dt, 'CPTLIGHTS_SYSTEM.SignalPLT', 0)
	pushSeqCmd(dt, 'CPTLIGHTS_SYSTEM.PrimaryPLT', 0)
	pushSeqCmd(dt, 'CPTLIGHTS_SYSTEM.StbyInstPLT', 0)
	pushSeqCmd(dt, 'CPTLIGHTS_SYSTEM.FloodPLT', 0)
	# PLT External lights
	pushSeqCmd(dt, 'EXTLIGHTS_SYSTEM.NavLights', 1) # 0 = DIM, 1 = OFF, 2 = BRT
	pushSeqCmd(dt, 'EXTLIGHTS_SYSTEM.FormationLights', 0) # NOTE misspelling, 0 = off, int16 = full on
	pushSeqCmd(dt, 'EXTLIGHTS_SYSTEM.AntiCollLights', 1) # 0 = RED, 1 = OFF, 2 = WHT
	# PLT MPDs
	pushSeqCmd(dt, 'MFD_PLT_LEFT.MODE_KNOB', 2) # 0 = MONO, 1 = NT, 2 = DAY
	pushSeqCmd(dt, 'MFD_PLT_LEFT.BRT_KNOB', 1.0)
	pushSeqCmd(dt, 'MFD_PLT_LEFT.VID_KNOB', 0.5)
	pushSeqCmd(dt, 'MFD_PLT_RIGHT.MODE_KNOB', 2) # 0 = MONO, 1 = NT, 2 = DAY
	pushSeqCmd(dt, 'MFD_PLT_RIGHT.BRT_KNOB', 1.0)
	pushSeqCmd(dt, 'MFD_PLT_RIGHT.VID_KNOB', 0.5)
	# PLT UFC
	pushSeqCmd(dt, 'EUFD_PLT.BRT', 1.0)
	# PLT KU
	pushSeqCmd(dt, 'KU_PLT.BrightnessKnob', 1.0)
	# PLT CMWS
	pushSeqCmd(dt, 'CMWS.CMWS_LAMP_KNOB', 1.0)
	# PLT FLIR Level (IHADSS FLIR brightness)
	pushSeqCmd(dt, 'ELEC_INTERFACE.VCP_FLIR_LEV_KNOB', 0.75)

	# CPG Internal Lights
	pushSeqCmd(dt, 'CPTLIGHTS_SYSTEM.SignalCPG', 0)
	pushSeqCmd(dt, 'CPTLIGHTS_SYSTEM.PrimaryCPG', 0)
	# No CPG standby instruments light control.
	pushSeqCmd(dt, 'CPTLIGHTS_SYSTEM.FloodCPG', 0)
	# CPG MPDs
	pushSeqCmd(dt, 'MFD_CPG_LEFT.MODE_KNOB', 2) # 0 = MONO, 1 = NT, 2 = DAY
	pushSeqCmd(dt, 'MFD_CPG_LEFT.BRT_KNOB', 1.0)
	pushSeqCmd(dt, 'MFD_CPG_LEFT.VID_KNOB', 0.5)
	pushSeqCmd(dt, 'MFD_CPG_RIGHT.MODE_KNOB', 2) # 0 = MONO, 1 = NT, 2 = DAY
	pushSeqCmd(dt, 'MFD_CPG_RIGHT.BRT_KNOB', 1.0)
	pushSeqCmd(dt, 'MFD_CPG_RIGHT.VID_KNOB', 0.5)
	# CPG UFC
	pushSeqCmd(dt, 'EUFD_CPG.BRT', 1.0)
	# CPG KU
	pushSeqCmd(dt, 'KU_CPG.BrightnessKnob', 1.0)
	# CPG FLIR Level (IHADSS FLIR brightness)
	# Controlled by buttons on TADS display.

	# TEDAC
	pushSeqCmd(dt, 'TEDAC.TDU_MODE_KNOB', 0) # 0 = OFF, 1 = NT, 2 = DAY

	# CMWS
	# CMWS PWR knob - OFF
	pushSeqCmd(dt, 'CMWS.CMWS_PWR', 0)
	# CMWS ARM/SAFE switch - SAFE
	pushSeqCmd(dt, 'CMWS.CMWS_ARM_SAFE_SW', 0)
	# CMWS CMWS/NAV switch - NAV
	pushSeqCmd(dt, 'CMWS.CMWS_CMWS_NAV_SW', 0)
	# CMWS BYPASS/AUTO switch - AUTO
	pushSeqCmd(dt, 'CMWS.CMWS_BYPASS_AUTO_SW', 0)

	# APU - OFF
	pushSeqCmd(dt, 'ENGINE_INTERFACE.APU_StartBtn', 1) # Press
	pushSeqCmd(dt, 'ENGINE_INTERFACE.APU_StartBtn', 0) # Release
	pushSeqCmd(dt, 'ENGINE_INTERFACE.APU_StartBtnCover', 0) # Cover close

	# MSTR IGN switch - OFF
	pushSeqCmd(dt, 'ELEC_INTERFACE.MIK', 0)

	# RTR BRK switch - ON
	pushSeqCmd(dt, 'HYDRO_INTERFACE.Rotor_Brake', 1)

	# Canopy Door - Open
	pushSeqCmd(dt, 'CPT_MECH.CPG_Door_Lock', 1)
	pushSeqCmd(dt, 'CPT_MECH.PLT_Door_Lock', 1)

	return seq


###############################################################################
###############################################################################
def LoadRoute(config, vars, helper, *args, **kwargs):
	seq = []
	dt = 0.3

	pushSeqCmd = helper.makePushSeqCmd(seq)

	yield # A live script, so the seat can be read from DCS.
	seat = crewStation(vars, helper)
	if seat is None:
		pushSeqCmd(0, '', '', "Couldn't read your seat from DCS, so choose Pilot or Co-Pilot and run the script again.")
		return seq

	def pressMpdRButton(cmd, seat):
		pushSeqCmd(dt, f'MFD_{seat.upper()}_RIGHT.{cmd}', 1) # Press
		pushSeqCmd(dt, f'MFD_{seat.upper()}_RIGHT.{cmd}', 0) # Release

	def pressKuKey(btn, seat):
		btn = str(btn).upper()
		aliases = {
			'/': 'Slash',
			'.': 'Dot',
			'+': 'Plus',
			'-': 'Minus',
			'*': 'Multiply',
			' ': 'SPC',
			'ENT': 'Enter',
		}
		if btn in aliases:
			cmd = aliases[btn]
		else:
			cmd = btn
		pushSeqCmd(dt, f'KU_{seat.upper()}.key{cmd}', 1) # KU key press
		pushSeqCmd(dt, f'KU_{seat.upper()}.key{cmd}', 0) # release

	def enterKuSequence(input, seat):
		input = str(input).upper()
		for char in str(input).upper():
			pressKuKey(char, seat)

	# Start sequence
	pushSeqCmd(0, '', '', 'Loading waypoints from file')
	routeData = helper.getRouteData(vars.get('routeFile'), vars.get('routeName'))
	if not routeData:
		pushSeqCmd(dt, '', '', 'Route selection cancelled.')
		return seq

	waypoints = routeData.get('waypoints', []) if isinstance(routeData, dict) else []
	if not waypoints:
		pushSeqCmd(dt, '', '', 'No waypoints in route.')
		return seq

	pushSeqCmd(dt, 'scriptSpeech', 'Do not use any functions on Keyboard Unit or right MFD until waypoint entry is complete.')

	# Right MPD -> TSD -> POINT -> ADD -> WP
	pressMpdRButton('TSD', seat)
	pressMpdRButton('B6', seat) # POINT

	waypointCount = len(waypoints)
	for waypointIndex, waypoint in enumerate(waypoints):
		pushSeqCmd(dt, '', '', f'Entering waypoint {waypointIndex + 1}/{waypointCount}')
		mgrs = waypoint['mgrs8'].replace(' ', '') # Make sure there are no spaces.
		altFeet = round(waypoint['altFeet'])

		pressMpdRButton('L2', seat) # ADD
		pressMpdRButton('L3', seat) # WP
		pressMpdRButton('L1', seat) # IDENT
		pressKuKey('ENT', seat) # (for blank IDENT)
		pressKuKey('ENT', seat) # (for blank FREE)

		# Clear MGRS, enter MGRS, ENTER
		pressKuKey('CLR', seat)
		enterKuSequence(mgrs, seat)
		pressKuKey('ENT', seat)

		# Set altitude
		if vars.get('altitude') == 'useWaypointAltitudes':
			pressKuKey('CLR', seat)
			enterKuSequence(altFeet, seat)
		# Else using ground altitude (default in the Apache), so just press ENTER to accept.
		pressKuKey('ENT', seat)

	pressMpdRButton('B6', seat) # POINT (return to main screen)
	return seq


###############################################################################
###############################################################################
def LoadScratchpad(config, vars, helper, *args, **kwargs):
	seq = []
	dt = 0.3

	pushSeqCmd = helper.makePushSeqCmd(seq)

	yield # A live script, so the seat can be read from DCS.
	seat = crewStation(vars, helper)
	if seat is None:
		pushSeqCmd(0, '', '', "Couldn't read your seat from DCS, so choose Pilot or Co-Pilot and run the script again.")
		return seq

	def pressMpdRButton(cmd, seat):
		pushSeqCmd(dt, f'MFD_{seat.upper()}_RIGHT.{cmd}', 1) # Press
		pushSeqCmd(dt, f'MFD_{seat.upper()}_RIGHT.{cmd}', 0) # Release

	def pressKuKey(btn, seat):
		btn = str(btn).upper()
		aliases = {
			'/': 'Slash',
			'.': 'Dot',
			'+': 'Plus',
			'-': 'Minus',
			'*': 'Multiply',
			' ': 'SPC',
			'ENT': 'Enter',
		}
		if btn in aliases:
			cmd = aliases[btn]
		else:
			cmd = btn
		pushSeqCmd(dt, f'KU_{seat.upper()}.key{cmd}', 1) # KU key press
		pushSeqCmd(dt, f'KU_{seat.upper()}.key{cmd}', 0) # release

	def enterKuSequence(input, seat):
		input = str(input).upper()
		for char in str(input).upper():
			pressKuKey(char, seat)

	# Start sequence
	pushSeqCmd(0, '', '', 'Loading waypoints from file')
	waypoints = helper.getScratchpadData(vars.get('scratchpadFile'))
	if not waypoints:
		pushSeqCmd(dt, 'scriptText', 'No waypoints found.')
		return seq

	pushSeqCmd(dt, 'scriptSpeech', 'Do not use any functions on Keyboard Unit or right MFD until waypoint entry is complete.')

	# Right MPD -> TSD -> POINT -> ADD -> WP
	pressMpdRButton('TSD', seat)
	pressMpdRButton('B6', seat) # POINT

	waypointCount = len(waypoints)
	for waypointIndex, waypoint in enumerate(waypoints):
		pushSeqCmd(dt, '', '', f'Entering waypoint {waypointIndex + 1}/{waypointCount}')
		mgrs = waypoint['mgrs8'].replace(' ', '') # Make sure there are no spaces.
		altFeet = round(waypoint['altFeet'])

		pressMpdRButton('L2', seat) # ADD
		pressMpdRButton('L3', seat) # WP
		pressMpdRButton('L1', seat) # IDENT
		pressKuKey('ENT', seat) # (for blank IDENT)
		pressKuKey('ENT', seat) # (for blank FREE)

		# Clear MGRS, enter MGRS, ENTER
		pressKuKey('CLR', seat)
		enterKuSequence(mgrs, seat)
		pressKuKey('ENT', seat)

		# Set altitude
		if vars.get('altitude') == 'useWaypointAltitudes':
			pressKuKey('CLR', seat)
			enterKuSequence(altFeet, seat)
		# Else using ground altitude (default in the Apache), so just press ENTER to accept.
		pressKuKey('ENT', seat)

	pressMpdRButton('B6', seat) # POINT (return to main screen)
	return seq
