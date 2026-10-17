# Return a Dictionary of script data.  The 'scripts' key is a list of scripts that users will be selecting from.  Each script has an associated 'function', which is the name of the function in this file that will be called to generate the command sequence, and a dictionary of 'vars' that the user will be prompted to choose from before running the script, and will be passed into the sequence generating function.
import cmd
import math
import pprint


def getScriptData():
	return {
		'moduleName': 'FA-18C_hornet',
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
					'location': {
						'label': 'Location',
						'options': {
							'ground': 'Ground',
							'carrier': 'Carrier',
						},
					},
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
					'location': {
						'label': 'Location',
						'options': {
							'ground': 'Ground',
							'carrier': 'Carrier',
						},
					},
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
					'usePrecise': {
						'label': 'Use PRECISE',
						'options': {
							'yes': 'Yes',
							'no': 'No',
						},
					},
					'mfd': {
						'label': 'MFD to use',
						'options': {
							'left': 'Left',
							'center': 'Center',
							'right': 'Right',
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
					'usePrecise': {
						'label': 'Use PRECISE',
						'options': {
							'yes': 'Yes',
							'no': 'No',
						},
					},
					'mfd': {
						'label': 'MFD to use',
						'options': {
							'left': 'Left',
							'center': 'Center',
							'right': 'Right',
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
			#		'location': {
			#			'label': 'Location',
			#			'options': {
			#				'ground': 'Ground',
			#				'carrier': 'Carrier',
			#			},
			#		},
			#		'hmd': {
			#			'label': 'HMD',
			#			'options': {
			#				'withJhmcs': 'With JHMCS',
			#				'noJhmcs': 'NVG or none',
			#			},
			#		},
			#	},
			#},
		],
	}

#def getDetectedVars(exportData):
#	vars = {
#		'time': '',
#		'location': '',
#		'hmd': '',
#	}
#	try:
#		#moduleName = exportData['LoGetSelfData']['Name']

#		altMSL = exportData['LoGetAltitudeAboveSeaLevel']
#		altAGL = exportData['LoGetAltitudeAboveGroundLevel']
#		#airspeedTAS = exportData['LoGetTrueAirSpeed']

#		missionTimeHHMMSS = exportData['missionTimeHHMMSS']
#		if missionTimeHHMMSS >= '06:00:00' and missionTimeHHMMSS <= '20:00:00':
#			vars['time'] = 'day'
#		else:
#			vars['time'] = 'night'

#		if altAGL < 5:
#			vars['location'] = 'ground'
#		elif altAGL - altMSL < 2 and altMSL > 15 and altMSL < 25:
#			vars['location'] = 'carrier'
#		else:
#			vars['location'] = 'air'

#		# Single-engined planes will only have RPM for left engine.
#		if exportData['LoGetEngineInfo']['RPM']['left'] > 0:
#			vars['Engines'] = 'Hot'
#		else:
#			vars['Engines'] = 'Cold'

#		return vars

#	except Exception as e:
#		return vars


def getInfo():
	return ''


def autoSelect(context):
	kit = context.read('arg.PLT_HelmetMountedKit')['arg.PLT_HelmetMountedKit'] # 0 = JHMCS, 0.5 = none, 1 = NVG
	if kit is None:
		return {}
	return {'vars': {'hmd': 'withJhmcs' if kit < 0.25 else 'noJhmcs'}}



def Test(config, vars, helper, *args, **kwargs):
	seq = []
	dt = 0.3

	pushSeqCmd = helper.makePushSeqCmd(seq)

	# Test code here...
	pushSeqCmd(0, '', '', "Running Test sequence")



	#print(seq)
	return seq


# Some settings change depending on whether you're starting from the ground or from a carrier.
def ColdStart(config, vars, helper, *args, **kwargs):
	seq = []
	dt = 0.3

	pushSeqCmd = helper.makePushSeqCmd(seq)

	# Helper function to press and release a button.
	def pushSeqCmdBtn(dt, cmd, msg=''):
		nonlocal seq
		if msg:
			pushSeqCmd(dt, cmd, 1, msg)  # Press with message
		else:
			pushSeqCmd(dt, cmd, 1)  # Press
		pushSeqCmd(dt, cmd, 0)  # Release

	insAlignTime = 1 * 60 + 55 # 1m55s
	cvInsAlignTime = 2 * 60 + 20 # 2m20s

	pushSeqCmd(0, '', '', "Running Cold Start sequence")

	pushSeqCmd(dt, 'ELEC_INTERFACE.BattSw', 2, 'BATT switch - On')

	# Exterior light switch ... OFF
	pushSeqCmd(dt, 'HOTAS.THROTTLE_EXTERIOR_LIGHTS', 0) # 0 = OFF, 1 = ON
	# Other lights
	if vars.get('time') == 'day':
		pushSeqCmd(dt, 'CPT_LIGHTS.Consoles', 1.0)
		pushSeqCmd(dt, 'CPT_LIGHTS.InstPnl', 1.0)
	else:
		pushSeqCmd(dt, 'CPT_LIGHTS.Consoles', 0.5)
		pushSeqCmd(dt, 'CPT_LIGHTS.InstPnl', 0.5)

	# Start APU
	pushSeqCmd(dt, 'ENGINES_INTERFACE.APU_ControlSw', 1, 'APU switch - On')

	# Close canopy while waiting for APU
	pushSeqCmd(dt, 'CPT_MECHANICS.CanopySwitchClose', 0)
	pushSeqCmd(dt, 'scriptCockpitState', control='FA-18C_hornet/arg.Canopy', value=0) # Wait for canopy to close.
	pushSeqCmd(dt, 'CPT_MECHANICS.CanopySwitchClose', 1) # Turn off canopy switch after canopy is closed.

	pushSeqCmd(dt, 'scriptCockpitState', control='FA-18C_hornet/arg.CautionLights.CPT_LTS_APU_READY', value=1) # Wait for APU light to turn on
	# APU started

	# All MFDs on
	if vars.get('time') == 'day':
		pushSeqCmd(dt, 'MDI_LEFT.MDI_off_night_day', 2) # DAY
		pushSeqCmd(dt, 'MDI_RIGHT.MDI_off_night_day', 2) # DAY
		pushSeqCmd(dt, 'AMPCD.AMPCD_off_brightness', 1.0)
	else:
		pushSeqCmd(dt, 'MDI_LEFT.MDI_off_night_day', 1) # NIGHT
		pushSeqCmd(dt, 'MDI_RIGHT.MDI_off_night_day', 1) # NIGHT
		pushSeqCmd(dt, 'AMPCD.AMPCD_off_brightness', 0.5)

	# HUD, UFC, IFEI brightness
	if vars.get('time') == 'day':
		pushSeqCmd(dt, 'HUD.HUD_SymbBrightCtrl', 1.0)
		pushSeqCmd(dt, 'HUD.HUD_SymbBrightSelKnob', 1) # 0 = NIGHT, 1 = DAY
		pushSeqCmd(dt, 'UFC.BrtDim', 1.0)
		pushSeqCmd(dt, 'IFEI.IFEI_Brightness', 1.0) # IFEI brightness to max
	else:
		pushSeqCmd(dt, 'HUD.HUD_SymbBrightCtrl', 0.5)
		pushSeqCmd(dt, 'HUD.HUD_SymbBrightSelKnob', 0) # 0 = NIGHT, 1 = DAY
		pushSeqCmd(dt, 'UFC.BrtDim', 0.5)
		pushSeqCmd(dt, 'IFEI.IFEI_Brightness', 0.0) # IFEI brightness to min

	# Radio volume
	pushSeqCmd(dt, 'UFC.Comm1Vol', 0.8, 'COMM 1 vol - 80%')
	pushSeqCmd(dt, 'UFC.Comm2Vol', 0.8, 'COMM 2 vol - 80%')

	# RIGHT ENGINE
	pushSeqCmd(dt, 'ENGINES_INTERFACE.EngineCrankLSw', 2) # Right
	pushSeqCmd(dt, 'scriptCockpitState', control='telemetry/LoGetEngineInfo.RPM.right', condition='>=', value=15) # Wait for RPM >= 15%.
	pushSeqCmd(dt, 'scriptSimCommand', 'iCommandRightEngineStart', 'Right throttle IDLE') # Right throttle IDLE
	pushSeqCmd(dt, 'scriptCockpitState', control='telemetry/LoGetEngineInfo.RPM.right', condition='>=', value=63, duration=5) # Wait for RPM >= 63% for 5 seconds.  In extreme cold, idle speed can be as low as 63%.
	pushSeqCmd(dt, 'ENGINES_INTERFACE.EngineCrankLSw', 1, 'Engine Crank switch - Off')
	# END RIGHT ENGINE

	# FIXME The engine monitor instrument doesn't pick up the cockpit lighting mode switch position unless it's set after the right engine starts.
	if vars.get('time') == 'day':
		pushSeqCmd(dt, 'CPT_LIGHTS.ModeSw', 0) # 0 = DAY (default), 1 = NITE, 2 = NVG
	else:
		pushSeqCmd(dt, 'CPT_LIGHTS.ModeSw', 1) # 0 = DAY (default), 1 = NITE, 2 = NVG

	# HMD knob - ON
	if vars.get('hmd') == 'withJhmcs':
		if vars.get('time') == 'day':
			pushSeqCmd(dt, 'HMD_INTERFACE.BrtKnob', 1.0)
		else:
			pushSeqCmd(dt, 'HMD_INTERFACE.BrtKnob', 0.5)

	# BLEED AIR KNOB - CYCLE THRU OFF TO NORM
	pushSeqCmd(dt, 'ECS_INTERFACE.BleedAirSw', 3)
	pushSeqCmd(dt, 'ECS_INTERFACE.BleedAirSw', 0)
	pushSeqCmd(dt, 'ECS_INTERFACE.BleedAirSw', 1)
	pushSeqCmd(dt, 'ECS_INTERFACE.BleedAirSw', 2)

	# RADAR ALTIMETER - ON, SET TO 50 FT
	pushSeqCmd(dt, 'ID2163A.ID2163A_SetMinAlt', -3.125) # All the way off
	pushSeqCmd(dt, 'ID2163A.ID2163A_SetMinAlt', 0.28) # Turn knob up 28% of one turn to get 50 ft.

	# RADAR KNOB - OPR
	pushSeqCmd(dt, 'RADAR.RADAR_SwitchChange', 2)
	# FCS RESET BUTTON - PUSH
	pushSeqCmdBtn(dt, 'CONTROL_INTERFACE.ResetSw')

	# FLAP SWITCH - HALF
	pushSeqCmd(dt, 'CONTROL_INTERFACE.FlapSw', 1)
	# T/O TRIM BUTTON - PRESS UNTIL TRIM ADVISORY DISPLAYED (only momentary press actually necessary??)
	pushSeqCmdBtn(dt, 'CONTROL_INTERFACE.TOTrimSw')

	# STANDBY ATTITUDE REFERENCE INDICATOR - UNCAGE
	pushSeqCmd(dt, 'SAI.SAI_rotate', -0.015)
	pushSeqCmd(dt, 'SAI.SAI_rotate', 0.015)

	# ATT SWITCH - STBY
	pushSeqCmd(dt, 'HUD.HUD_AttitudeSelSw', 0)
	# ATT SWITCH - AUTO
	pushSeqCmd(dt, 'HUD.HUD_AttitudeSelSw', 1)
	# OBOGS CONTROL SWITCH - ON
	pushSeqCmd(dt, 'OXYGEN_INTERFACE.OBOGS_ControlSw', 1)

	if vars.get('location') == 'ground':
		# HOOK BYPASS switch - FIELD
		pushSeqCmd(dt, 'CPT_LIGHTS.HookBypass', 1)
		# ANTI-SKID switch - ON'
		pushSeqCmd(dt, 'GEAR_INTERFACE.AntiSkidSw', 1)
	else:
		# HOOK BYPASS switch - CARRIER
		pushSeqCmd(dt, 'CPT_LIGHTS.HookBypass', 0)
		# ANTI-SKID switch - OFF
		pushSeqCmd(dt, 'GEAR_INTERFACE.AntiSkidSw', 0)

	# HUD ALT SWITCH - RDR
	pushSeqCmd(dt, 'HUD.HUD_AltitudeSw', 0)
	# IR COOL SWITCH - NORM
	pushSeqCmd(dt, 'SMS.IRCoolingSw', 1)
	# DISPENSER SWITCH - ON
	pushSeqCmd(dt, 'CMDS.Dispenser', 1)
	# ECM - REC
	pushSeqCmd(dt, 'ASPJ.ASPJ_SwitchChange', 3)
	# RWR POWER - ON
	pushSeqCmd(dt, 'RWR.Power', 1)

	# BEGIN INS START ALIGN
	if vars.get('location') == 'ground':
		pushSeqCmd(dt, 'scriptTimerStart', name='alignTimer', duration=insAlignTime) # Starts a timer at the current time, with a duration.
		# INS KNOB - GND
		pushSeqCmd(dt, 'INS.INS_SwitchChange', 2)
	else:
		pushSeqCmd(dt, 'scriptTimerStart', name='alignTimer', duration=cvInsAlignTime) # Starts a timer at the current time, with a duration.
		# INS KNOB - CV
		pushSeqCmd(dt, 'INS.INS_SwitchChange', 1)
	# Select stored heading alignment.
	pushSeqCmdBtn(dt, 'AMPCD.AMPCD_PB_19') # STD HDG OSB
	# END INS START ALIGN

	# After the AMPCD (center MFD) powers on, set it to night mode if doing night start.
	if vars.get('time') == 'day':
		pass
	else:
		pushSeqCmd(dt, 'AMPCD.AMPCD_nite_day_DAY', 0) # Press
		pushSeqCmd(dt, 'AMPCD.AMPCD_nite_day_DAY', 1) # Release

	# LEFT ENGINE
	pushSeqCmd(dt, 'ENGINES_INTERFACE.EngineCrankLSw', 0) # Left
	pushSeqCmd(dt, 'scriptCockpitState', control='telemetry/LoGetEngineInfo.RPM.left', condition='>=', value=15) # Wait for RPM >= 15%.
	pushSeqCmd(dt, 'scriptSimCommand', 'iCommandLeftEngineStart', 'Left throttle IDLE') # Left throttle IDLE
	pushSeqCmd(dt, 'scriptCockpitState', control='telemetry/LoGetEngineInfo.RPM.left', condition='>=', value=63, duration=5) # Wait for RPM >= 63% for 5 seconds.  In extreme cold, idle speed can be as low as 63%.
	pushSeqCmd(dt, 'ENGINES_INTERFACE.EngineCrankLSw', 1, 'Engine Crank switch - Off')
	# END LEFT ENGINE

	# Shut down APU
	pushSeqCmd(dt, 'ENGINES_INTERFACE.APU_ControlSw', 0, 'APU switch - Off')

	# BIT STOP
	# We start on the BIT page by default, but just in case the user hits a button, select it manually.
	pushSeqCmdBtn(dt, 'MDI_RIGHT.MDI_PB_18') # MENU OSB
	pushSeqCmdBtn(dt, 'MDI_RIGHT.MDI_PB_18') # MENU OSB
	pushSeqCmdBtn(dt, 'MDI_RIGHT.MDI_PB_8') # BIT OSB
	pushSeqCmdBtn(dt, 'MDI_RIGHT.MDI_PB_10') # BIT page STOP OSB

	# EW page...
	# Dispenser mode MAN 1
	pushSeqCmdBtn(dt, 'MDI_RIGHT.MDI_PB_18') # MENU OSB
	pushSeqCmdBtn(dt, 'MDI_RIGHT.MDI_PB_17') # EW OSB
	pushSeqCmdBtn(dt, 'MDI_RIGHT.MDI_PB_8') # ALE-47 OSB
	pushSeqCmdBtn(dt, 'MDI_RIGHT.MDI_PB_19') # MODE OSB
	# RWR display to HUD
	pushSeqCmdBtn(dt, 'MDI_RIGHT.MDI_PB_14') # HUD OSB

	# RWR show on SA page
	pushSeqCmdBtn(dt, 'MDI_RIGHT.MDI_PB_18') # MENU OSB
	pushSeqCmdBtn(dt, 'MDI_RIGHT.MDI_PB_13') # SA OSB
	pushSeqCmdBtn(dt, 'MDI_RIGHT.MDI_PB_5') # SENSR OSB
	pushSeqCmdBtn(dt, 'MDI_RIGHT.MDI_PB_7') # RWR OSB
	# Add RWR contacts from friendly units as well (max 4 RWR contacts shown, priority is detections from ownship).
	pushSeqCmdBtn(dt, 'MDI_RIGHT.MDI_PB_8') # FRIEND OSB
	pushSeqCmdBtn(dt, 'MDI_RIGHT.MDI_PB_8') # FRIEND OSB
	pushSeqCmdBtn(dt, 'MDI_RIGHT.MDI_PB_10') # SA OSB

	# Set waypoint 59 as bullseye.
	pushSeqCmdBtn(dt, 'MDI_RIGHT.MDI_PB_18') # MENU OSB
	pushSeqCmdBtn(dt, 'MDI_RIGHT.MDI_PB_18') # MENU OSB
	pushSeqCmdBtn(dt, 'MDI_RIGHT.MDI_PB_2') # HSI OSB
	pushSeqCmdBtn(dt, 'MDI_RIGHT.MDI_PB_10') # DATA OSB
	for i in range(10): # Press Down Arrow 10 times to get to waypoint 59.
		pushSeqCmdBtn(dt, 'MDI_RIGHT.MDI_PB_13') # Down Arrow OSB
	pushSeqCmdBtn(dt, 'MDI_RIGHT.MDI_PB_2') # A/A WP OSB
	for i in range(10): # Press Up Arrow 10 times to return to waypoint 0.
		pushSeqCmdBtn(dt, 'MDI_RIGHT.MDI_PB_12') # Up Arrow OSB
	pushSeqCmdBtn(dt, 'MDI_RIGHT.MDI_PB_10') # HSI OSB

	# Turn off radar declutter (adds artificial horizon symbology to radar display).
	pushSeqCmdBtn(dt, 'MDI_RIGHT.MDI_PB_18') # MENU OSB
	pushSeqCmdBtn(dt, 'MDI_RIGHT.MDI_PB_4') # RDR ATTK OSB
	pushSeqCmdBtn(dt, 'MDI_RIGHT.MDI_PB_16') # DATA OSB
	pushSeqCmdBtn(dt, 'MDI_RIGHT.MDI_PB_17') # DCLTR OSB
	pushSeqCmdBtn(dt, 'MDI_RIGHT.MDI_PB_16') # DATA OSB

	if vars.get('hmd') == 'withJhmcs':
		# Prepare for HMD align
		pushSeqCmdBtn(dt, 'MDI_RIGHT.MDI_PB_18') # MENU OSB
		pushSeqCmdBtn(dt, 'MDI_RIGHT.MDI_PB_18') # MENU OSB
		pushSeqCmdBtn(dt, 'MDI_RIGHT.MDI_PB_8') # BIT OSB
		pushSeqCmdBtn(dt, 'MDI_RIGHT.MDI_PB_11') # DISPLAYS OSB
		pushSeqCmdBtn(dt, 'MDI_RIGHT.MDI_PB_11') # HMD OSB
		pushSeqCmd(8, '', '', "HMD test complete")
		pushSeqCmdBtn(dt, 'MDI_RIGHT.MDI_PB_10') # STOP OSB
		pushSeqCmdBtn(dt, 'MDI_RIGHT.MDI_PB_18') # MENU OSB
		pushSeqCmdBtn(dt, 'MDI_RIGHT.MDI_PB_18') # MENU OSB
		pushSeqCmdBtn(dt, 'MDI_RIGHT.MDI_PB_3') # HMD OSB
		# Set HMD symbology range to 100 nmi (default is 35 nmi).
		pushSeqCmdBtn(dt, 'MDI_RIGHT.MDI_PB_19') # REJECT SETUP OSB
		for i in range(13): # Press Up Arrow 13 times to set range to 100 nmi (max).
			pushSeqCmdBtn(dt, 'MDI_RIGHT.MDI_PB_14') # Up Arrow OSB
		pushSeqCmdBtn(dt, 'MDI_RIGHT.MDI_PB_19') # RETURN OSB
		# Align HMD.
		pushSeqCmdBtn(dt, 'MDI_RIGHT.MDI_PB_20') # ALIGN OSB
		pushSeqCmd(dt, 'scriptSpeech', 'Press and hold uncage to align.  Press and release uncage to go to next mode, use T D C to align.  Unbox align O S B when complete.')

	# SET BINGO FUEL - 3000 LBS
	pushSeqCmd(dt, 'IFEI.IFEI_BTN_UP_ARROW', 1)
	pushSeqCmd(4.25, 'IFEI.IFEI_BTN_UP_ARROW', 0) # Release after 4.25 seconds to get 3000 lbs.

	# IFF - ON
	pushSeqCmdBtn(dt, 'UFC.FuncSwIFF') # UFC IFF button
	pushSeqCmd(dt, 'UFC.FuncSwOnOff', 1) # UFC ON/OFF button
	pushSeqCmd(1, 'UFC.FuncSwOnOff', 0) # release after 1 second

	#DATALINK - Link 4 ON
	pushSeqCmdBtn(dt, 'UFC.FuncSwDL') # UFC D/L button
	pushSeqCmd(dt, 'UFC.FuncSwOnOff', 1) # UFC ON/OFF button
	pushSeqCmd(1, 'UFC.FuncSwOnOff', 0) # release after 1 second
	# DATALINK - Link 16 ON
	pushSeqCmdBtn(dt, 'UFC.FuncSwDL') # UFC D/L button, press again to go to the second D/L page
	pushSeqCmd(dt, 'UFC.FuncSwOnOff', 1) # UFC ON/OFF button
	pushSeqCmd(1, 'UFC.FuncSwOnOff', 0) # release after 1 second

	# Wait until alignment timer is done.
	pushSeqCmd(dt, 'scriptTimerEnd', name='alignTimer') # Pause here until the timer's duration has passed.
	#INS KNOB - IFA
	pushSeqCmd(dt, 'INS.INS_SwitchChange', 4)

	# AMPCD GAIN - DOWN TO MIN FOR VR
	# NOTE Should be done after INS alignement is complete.
	pushSeqCmd(dt, 'AMPCD.AMPCD_gain_UP', 0) # Down
	pushSeqCmd(3, 'AMPCD.AMPCD_gain_UP', 1) # Center after 3 seconds

	# Show local time in HUD
	# IMPORTANT If you are doing a CV alignment, this must be done either before starting alignment, or after alignment is complete and INS knob is set to IFA.  That is because when doing a CV alignment, PB 17 says MAN instead of TIMEUFC, and if pressed, it turns off the STD HDG.  Once the INS knob is set to NAV, PB 17 will show TIMEUFC again.  We'll do this on the center MFD because it will already have the HSI on it for the alignment.
	pushSeqCmdBtn(dt, 'AMPCD.AMPCD_PB_17') # TIMEUFC OSB
	pushSeqCmdBtn(dt, 'UFC.OptSw5') # LTOD OSB
	pushSeqCmdBtn(dt, 'AMPCD.AMPCD_PB_17') # TIMEUFC OSB

	# Put left MFD on STORES page (it should already be on the TAC menu)
	pushSeqCmdBtn(dt, 'MDI_LEFT.MDI_PB_5') # STORES OSB

	# PARK BRK HANDLE - FULLY STOWED
	pushSeqCmd(dt, 'GEAR_INTERFACE.EmergParkHandleSelectEmerg', 2)
	pushSeqCmd(dt, 'GEAR_INTERFACE.EmergParkHandleOnOff', 1)
	pushSeqCmd(dt, 'GEAR_INTERFACE.EmergParkHandleSelectEmerg', 0)

	# MASTER ARM - ARM
	pushSeqCmd(dt, 'SMS.MasterArmSw', 1)

	# EJECTION SEAT SAFE/ARM HANDLE - ARM
	pushSeqCmd(dt, 'CPT_MECHANICS.EjectionSeatSafeArmedHandle', 0)

	if vars.get('location') == 'ground':
		pushSeqCmd(dt, 'scriptSpeech', "Manual steps remaining: Set laser codes.  Tune radios.")
	else:
		# For carrier takeoff, you need at least +16 elevator trim.
		pushSeqCmd(dt, 'scriptSpeech', "Manual steps remaining: Set takeoff trim, FCS page, STAB up 16, or more if heavy.  Set laser codes.  Tune radios.")

	return seq


# Some settings change depending on whether you're starting from the ground or from a carrier.
def HotStart(config, vars, helper, *args, **kwargs):
	seq = []
	dt = 0.3

	pushSeqCmd = helper.makePushSeqCmd(seq)

	# Helper function to press and release a button.
	def pushSeqCmdBtn(dt, cmd, msg=''):
		nonlocal seq
		if msg:
			pushSeqCmd(dt, cmd, 1, msg)  # Press with message
		else:
			pushSeqCmd(dt, cmd, 1)  # Press
		pushSeqCmd(dt, cmd, 0)  # Release

	pushSeqCmd(0, '', '', "Running Hot Start sequence")

	# Exterior light switch ... OFF
	pushSeqCmd(dt, 'HOTAS.THROTTLE_EXTERIOR_LIGHTS', 0) # 0 = OFF, 1 = ON
	# Other lights
	if vars.get('time') == 'day':
		pushSeqCmd(dt, 'CPT_LIGHTS.Consoles', 1.0)
		pushSeqCmd(dt, 'CPT_LIGHTS.InstPnl', 1.0)
	else:
		pushSeqCmd(dt, 'CPT_LIGHTS.Consoles', 0.5)
		pushSeqCmd(dt, 'CPT_LIGHTS.InstPnl', 0.5)
		pushSeqCmd(dt, 'CPT_LIGHTS.ModeSw', 1) # 0 = DAY (default), 1 = NITE, 2 = NVG

	# All MFDs on
	if vars.get('time') == 'day':
		pushSeqCmd(dt, 'MDI_LEFT.MDI_off_night_day', 2) # DAY
		pushSeqCmd(dt, 'MDI_RIGHT.MDI_off_night_day', 2) # DAY
		pushSeqCmd(dt, 'AMPCD.AMPCD_off_brightness', 1.0)
	else:
		pushSeqCmd(dt, 'MDI_LEFT.MDI_off_night_day', 1) # NIGHT
		pushSeqCmd(dt, 'MDI_RIGHT.MDI_off_night_day', 1) # NIGHT
		pushSeqCmd(dt, 'AMPCD.AMPCD_off_brightness', 0.5)

	# HUD, UFC, IFEI brightness
	if vars.get('time') == 'day':
		pushSeqCmd(dt, 'HUD.HUD_SymbBrightCtrl', 1.0)
		pushSeqCmd(dt, 'HUD.HUD_SymbBrightSelKnob', 1) # 0 = NIGHT, 1 = DAY
		pushSeqCmd(dt, 'UFC.BrtDim', 1.0)
		pushSeqCmd(dt, 'IFEI.IFEI_Brightness', 1.0) # IFEI brightness to max
	else:
		pushSeqCmd(dt, 'HUD.HUD_SymbBrightCtrl', 0.5)
		pushSeqCmd(dt, 'HUD.HUD_SymbBrightSelKnob', 0) # 0 = NIGHT, 1 = DAY
		pushSeqCmd(dt, 'UFC.BrtDim', 0.5)
		pushSeqCmd(dt, 'IFEI.IFEI_Brightness', 0.0) # IFEI brightness to min

	# Radio volume
	pushSeqCmd(dt, 'UFC.Comm1Vol', 0.8, 'COMM 1 vol - 80%')
	pushSeqCmd(dt, 'UFC.Comm2Vol', 0.8, 'COMM 2 vol - 80%')

	# HMD knob - ON
	if vars.get('hmd') == 'withJhmcs':
		if vars.get('time') == 'day':
			pushSeqCmd(dt, 'HMD_INTERFACE.BrtKnob', 1.0)
		else:
			pushSeqCmd(dt, 'HMD_INTERFACE.BrtKnob', 0.5)

	# RADAR ALTIMETER - ON, SET TO 50 FT
	pushSeqCmd(dt, 'ID2163A.ID2163A_SetMinAlt', -3.125) # All the way off
	pushSeqCmd(dt, 'ID2163A.ID2163A_SetMinAlt', 0.28) # Turn knob up 28% of one turn to get 50 ft.

	# FLAP SWITCH - HALF
	pushSeqCmd(dt, 'CONTROL_INTERFACE.FlapSw', 1)
	# T/O TRIM BUTTON - PRESS UNTIL TRIM ADVISORY DISPLAYED
	pushSeqCmdBtn(dt, 'CONTROL_INTERFACE.TOTrimSw')

	if vars.get('location') == 'ground':
		# HOOK BYPASS switch - FIELD
		pushSeqCmd(dt, 'CPT_LIGHTS.HookBypass', 1)
		# ANTI-SKID switch - ON
		pushSeqCmd(dt, 'GEAR_INTERFACE.AntiSkidSw', 1)
	else:
		# HOOK BYPASS switch - CARRIER
		pushSeqCmd(dt, 'CPT_LIGHTS.HookBypass', 0)
		# ANTI-SKID switch - OFF
		pushSeqCmd(dt, 'GEAR_INTERFACE.AntiSkidSw', 0)

	# HUD ALT SWITCH - RDR
	pushSeqCmd(dt, 'HUD.HUD_AltitudeSw', 0)
	# IR COOL SWITCH - NORM
	pushSeqCmd(dt, 'SMS.IRCoolingSw', 1)
	# DISPENSER SWITCH - ON
	pushSeqCmd(dt, 'CMDS.Dispenser', 1)
	# ECM - REC
	pushSeqCmd(dt, 'ASPJ.ASPJ_SwitchChange', 3)
	# RWR POWER - ON
	pushSeqCmd(dt, 'RWR.Power', 1)

	# After the AMPCD (center MFD) powers on, set it to night mode if doing night start.
	if vars.get('time') == 'day':
		pushSeqCmd(dt, 'AMPCD.AMPCD_nite_day_DAY', 2) # Press
		pushSeqCmd(dt, 'AMPCD.AMPCD_nite_day_DAY', 1) # Release
	else:
		pushSeqCmd(dt, 'AMPCD.AMPCD_nite_day_DAY', 0) # Press
		pushSeqCmd(dt, 'AMPCD.AMPCD_nite_day_DAY', 1) # Release

	# EW page...
	# Dispenser mode MAN 1
	pushSeqCmdBtn(dt, 'MDI_RIGHT.MDI_PB_18') # MENU OSB
	pushSeqCmdBtn(dt, 'MDI_RIGHT.MDI_PB_17', 1) # EW OSB
	pushSeqCmd(dt, '', '', 'Waiting for ALE-47 self test to complete')
	pushSeqCmd(15, '', '', 'ALE-47 self test complete')
	pushSeqCmdBtn(dt, 'MDI_RIGHT.MDI_PB_8', 1) # ALE-47 OSB
	pushSeqCmdBtn(dt, 'MDI_RIGHT.MDI_PB_19', 1) # MODE OSB
	# RWR display to HUD
	pushSeqCmdBtn(dt, 'MDI_RIGHT.MDI_PB_14', 1) # HUD OSB

	# RWR show on SA page
	pushSeqCmdBtn(dt, 'MDI_RIGHT.MDI_PB_18') # MENU OSB
	pushSeqCmdBtn(dt, 'MDI_RIGHT.MDI_PB_13') # SA OSB
	pushSeqCmdBtn(dt, 'MDI_RIGHT.MDI_PB_5') # SENSR OSB
	pushSeqCmdBtn(dt, 'MDI_RIGHT.MDI_PB_7') # RWR OSB
	# Add RWR contacts from friendly units as well (max 4 RWR contacts shown, priority is detections from ownship).
	pushSeqCmdBtn(dt, 'MDI_RIGHT.MDI_PB_8') # FRIEND OSB
	pushSeqCmdBtn(dt, 'MDI_RIGHT.MDI_PB_8') # FRIEND OSB
	pushSeqCmdBtn(dt, 'MDI_RIGHT.MDI_PB_10') # SA OSB

	# Turn off radar declutter (adds artificial horizon symbology to radar display).
	pushSeqCmdBtn(dt, 'MDI_RIGHT.MDI_PB_18') # MENU OSB
	pushSeqCmdBtn(dt, 'MDI_RIGHT.MDI_PB_4') # RDR ATTK OSB
	pushSeqCmdBtn(dt, 'MDI_RIGHT.MDI_PB_16') # DATA OSB
	pushSeqCmdBtn(dt, 'MDI_RIGHT.MDI_PB_17') # DCLTR OSB
	pushSeqCmdBtn(dt, 'MDI_RIGHT.MDI_PB_16') # DATA OSB

	# Show local time in HUD
	pushSeqCmdBtn(dt, 'MDI_RIGHT.MDI_PB_18') # MENU OSB
	pushSeqCmdBtn(dt, 'MDI_RIGHT.MDI_PB_18') # MENU OSB
	pushSeqCmdBtn(dt, 'MDI_RIGHT.MDI_PB_2') # HSI OSB
	pushSeqCmdBtn(dt, 'MDI_RIGHT.MDI_PB_17') # TIMEUFC OSB
	pushSeqCmdBtn(dt, 'UFC.OptSw5') # LTOD OSB
	pushSeqCmdBtn(dt, 'MDI_RIGHT.MDI_PB_17') # TIMEUFC OSB

	if vars.get('hmd') == 'withJhmcs':
		# Set HMD symbology range to 100 nmi (default is 35 nmi).
		pushSeqCmdBtn(dt, 'MDI_RIGHT.MDI_PB_18') # MENU OSB
		pushSeqCmdBtn(dt, 'MDI_RIGHT.MDI_PB_18') # MENU OSB
		pushSeqCmdBtn(dt, 'MDI_RIGHT.MDI_PB_3') # HMD OSB
		pushSeqCmdBtn(dt, 'MDI_RIGHT.MDI_PB_19') # REJECT SETUP OSB
		for i in range(13): # Press Up Arrow 13 times to set range to 100 nmi (max).
			pushSeqCmdBtn(dt, 'MDI_RIGHT.MDI_PB_14') # Up Arrow OSB
		pushSeqCmdBtn(dt, 'MDI_RIGHT.MDI_PB_19') # RETURN OSB
		pushSeqCmdBtn(dt, 'MDI_RIGHT.MDI_PB_18') # MENU OSB

	# SET BINGO FUEL - 3000 LBS
	pushSeqCmd(dt, 'IFEI.IFEI_BTN_UP_ARROW', 1)
	pushSeqCmd(4.25, 'IFEI.IFEI_BTN_UP_ARROW', 0) # Release after 4.25 seconds to get 3000 lbs.

	# DATALINK - Link 4 ON
	pushSeqCmdBtn(dt, 'UFC.FuncSwDL') # UFC D/L button
	pushSeqCmd(dt, 'UFC.FuncSwOnOff', 1) # UFC ON/OFF button
	pushSeqCmd(1, 'UFC.FuncSwOnOff', 0) # release after 1 second
	# DATALINK - Link 16 ON
	pushSeqCmdBtn(dt, 'UFC.FuncSwDL') # UFC D/L button, press again to go to the second D/L page
	pushSeqCmd(dt, 'UFC.FuncSwOnOff', 1) # UFC ON/OFF button
	pushSeqCmd(1, 'UFC.FuncSwOnOff', 0) # release after 1 second

	# NOTE Should be done after INS alignement is complete.
	# AMPCD GAIN - DOWN TO MIN FOR VR
	pushSeqCmd(dt, 'AMPCD.AMPCD_gain_UP', 0) # Down
	pushSeqCmd(3, 'AMPCD.AMPCD_gain_UP', 1) # Center after 3 seconds

	# MASTER ARM - ARM
	pushSeqCmd(dt, 'SMS.MasterArmSw', 1)

	if vars.get('location') == 'ground':
		pushSeqCmd(dt, 'scriptSpeech', "Manual steps remaining: Set laser codes.  Tune radios.")
	else:
		# For carrier takeoff, you need at least +16 elevator trim.
		pushSeqCmd(dt, 'scriptSpeech', "Manual steps remaining: Set takeoff trim, FCS page, STAB up 16, or more if heavy.  Set laser codes.  Tune radios.")

	return seq


def AirStart(config, vars, helper, *args, **kwargs):
	seq = []
	dt = 0.3

	pushSeqCmd = helper.makePushSeqCmd(seq)

	# Helper function to press and release a button.
	def pushSeqCmdBtn(dt, cmd, msg=''):
		nonlocal seq
		if msg:
			pushSeqCmd(dt, cmd, 1, msg)  # Press with message
		else:
			pushSeqCmd(dt, cmd, 1)  # Press
		pushSeqCmd(dt, cmd, 0)  # Release

	pushSeqCmd(0, '', '', "Running Air Start sequence")

	# Exterior light switch ... OFF
	pushSeqCmd(dt, 'HOTAS.THROTTLE_EXTERIOR_LIGHTS', 0) # 0 = OFF, 1 = ON
	# Other lights
	if vars.get('time') == 'day':
		pushSeqCmd(dt, 'CPT_LIGHTS.Consoles', 1.0)
		pushSeqCmd(dt, 'CPT_LIGHTS.InstPnl', 1.0)
	else:
		pushSeqCmd(dt, 'CPT_LIGHTS.Consoles', 0.5)
		pushSeqCmd(dt, 'CPT_LIGHTS.InstPnl', 0.5)

	# All MFDs on
	if vars.get('time') == 'day':
		pushSeqCmd(dt, 'AMPCD.AMPCD_off_brightness', 1.0)
	else:
		pushSeqCmd(dt, 'AMPCD.AMPCD_off_brightness', 0.5)

	# HUD, UFC, IFEI brightness
	if vars.get('time') == 'day':
		pushSeqCmd(dt, 'HUD.HUD_SymbBrightCtrl', 1.0)
		pushSeqCmd(dt, 'HUD.HUD_SymbBrightSelKnob', 1) # 0 = NIGHT, 1 = DAY
		pushSeqCmd(dt, 'UFC.BrtDim', 1.0)
		pushSeqCmd(dt, 'IFEI.IFEI_Brightness', 1.0) # IFEI brightness to max
	else:
		pushSeqCmd(dt, 'HUD.HUD_SymbBrightCtrl', 0.5)
		pushSeqCmd(dt, 'HUD.HUD_SymbBrightSelKnob', 0) # 0 = NIGHT, 1 = DAY
		pushSeqCmd(dt, 'UFC.BrtDim', 0.5)
		pushSeqCmd(dt, 'IFEI.IFEI_Brightness', 0.0) # IFEI brightness to min

	# Radio volume
	pushSeqCmd(dt, 'UFC.Comm1Vol', 0.8, 'COMM 1 vol - 80%')
	pushSeqCmd(dt, 'UFC.Comm2Vol', 0.8, 'COMM 2 vol - 80%')

	# FIXME The engine monitor instrument doesn't pick up the cockpit lighting mode switch position unless it's set after the right engine starts.
	if vars.get('time') == 'day':
		pushSeqCmd(dt, 'CPT_LIGHTS.ModeSw', 0) # 0 = DAY (default), 1 = NITE, 2 = NVG
	else:
		pushSeqCmd(dt, 'CPT_LIGHTS.ModeSw', 1) # 0 = DAY (default), 1 = NITE, 2 = NVG

	# HMD knob - ON
	if vars.get('hmd') == 'withJhmcs':
		if vars.get('time') == 'day':
			pushSeqCmd(dt, 'HMD_INTERFACE.BrtKnob', 1.0)
		else:
			pushSeqCmd(dt, 'HMD_INTERFACE.BrtKnob', 0.5)

	# RADAR ALTIMETER - ON, SET TO 50 FT
	pushSeqCmd(dt, 'ID2163A.ID2163A_SetMinAlt', -3.125) # All the way off
	pushSeqCmd(dt, 'ID2163A.ID2163A_SetMinAlt', 0.28) # Turn knob up 28% of one turn to get 50 ft.

	# HUD ALT SWITCH - RDR
	pushSeqCmd(dt, 'HUD.HUD_AltitudeSw', 0)
	# IR COOL SWITCH - NORM
	pushSeqCmd(dt, 'SMS.IRCoolingSw', 1)
	# DISPENSER SWITCH - ON
	pushSeqCmd(dt, 'CMDS.Dispenser', 1)
	# ECM - REC
	pushSeqCmd(dt, 'ASPJ.ASPJ_SwitchChange', 3)
	# RWR POWER - ON
	pushSeqCmd(dt, 'RWR.Power', 1)

	# EW page...
	# Dispenser mode MAN 1
	pushSeqCmdBtn(dt, 'MDI_RIGHT.MDI_PB_18') # MENU OSB
	pushSeqCmdBtn(dt, 'MDI_RIGHT.MDI_PB_17') # EW OSB
	pushSeqCmdBtn(dt, 'MDI_RIGHT.MDI_PB_8') # ALE-47 OSB
	pushSeqCmdBtn(dt, 'MDI_RIGHT.MDI_PB_19') # MODE OSB

	# RWR show on SA page
	pushSeqCmdBtn(dt, 'MDI_RIGHT.MDI_PB_18') # MENU OSB
	pushSeqCmdBtn(dt, 'MDI_RIGHT.MDI_PB_13') # SA OSB
	pushSeqCmdBtn(dt, 'MDI_RIGHT.MDI_PB_5') # SENSR OSB
	pushSeqCmdBtn(dt, 'MDI_RIGHT.MDI_PB_7') # RWR OSB
	# Add RWR contacts from friendly units as well (max 4 RWR contacts shown, priority is detections from ownship).
	pushSeqCmdBtn(dt, 'MDI_RIGHT.MDI_PB_8') # FRIEND OSB
	pushSeqCmdBtn(dt, 'MDI_RIGHT.MDI_PB_8') # FRIEND OSB
	pushSeqCmdBtn(dt, 'MDI_RIGHT.MDI_PB_10') # SA OSB

	if vars.get('hmd') == 'withJhmcs':
		# Set HMD symbology range to 100 nmi (default is 35 nmi).
		pushSeqCmdBtn(dt, 'MDI_RIGHT.MDI_PB_18') # MENU OSB
		pushSeqCmdBtn(dt, 'MDI_RIGHT.MDI_PB_18') # MENU OSB
		pushSeqCmdBtn(dt, 'MDI_RIGHT.MDI_PB_3') # HMD OSB
		pushSeqCmdBtn(dt, 'MDI_RIGHT.MDI_PB_19') # REJECT SETUP OSB
		for i in range(13): # Press Up Arrow 13 times to set range to 100 nmi (max).
			pushSeqCmdBtn(dt, 'MDI_RIGHT.MDI_PB_14') # Up Arrow OSB
		pushSeqCmdBtn(dt, 'MDI_RIGHT.MDI_PB_19') # RETURN OSB
		pushSeqCmdBtn(dt, 'MDI_RIGHT.MDI_PB_18') # MENU OSB

	# Turn off radar declutter (adds artificial horizon symbology to radar display).
	pushSeqCmdBtn(dt, 'MDI_RIGHT.MDI_PB_18') # MENU OSB
	pushSeqCmdBtn(dt, 'MDI_RIGHT.MDI_PB_4') # RDR ATTK OSB
	pushSeqCmdBtn(dt, 'MDI_RIGHT.MDI_PB_16') # DATA OSB
	pushSeqCmdBtn(dt, 'MDI_RIGHT.MDI_PB_17') # DCLTR OSB
	pushSeqCmdBtn(dt, 'MDI_RIGHT.MDI_PB_16') # DATA OSB

	# SET BINGO FUEL - 3000 LBS
	pushSeqCmd(dt, 'IFEI.IFEI_BTN_UP_ARROW', 1)
	pushSeqCmd(4.25, 'IFEI.IFEI_BTN_UP_ARROW', 0) # Release after 4.25 seconds to get 3000 lbs.

	#DATALINK - Link 4 ON
	pushSeqCmdBtn(dt, 'UFC.FuncSwDL') # UFC D/L button
	pushSeqCmd(dt, 'UFC.FuncSwOnOff', 1) # UFC ON/OFF button
	pushSeqCmd(1, 'UFC.FuncSwOnOff', 0) # release after 1 second

	# AMPCD GAIN - DOWN TO MIN FOR VR
	# NOTE Should be done after INS alignement is complete.
	pushSeqCmd(dt, 'AMPCD.AMPCD_gain_UP', 0) # Down
	pushSeqCmd(3, 'AMPCD.AMPCD_gain_UP', 1) # Center after 3 seconds

	# Show local time in HUD
	pushSeqCmdBtn(dt, 'AMPCD.AMPCD_PB_17') # TIMEUFC OSB
	pushSeqCmdBtn(dt, 'UFC.OptSw5') # LTOD OSB
	pushSeqCmdBtn(dt, 'AMPCD.AMPCD_PB_17') # TIMEUFC OSB

	# EJECTION SEAT SAFE/ARM HANDLE - ARM
	pushSeqCmd(dt, 'CPT_MECHANICS.EjectionSeatSafeArmedHandle', 0)

	return seq


def Shutdown(config, vars, helper, *args, **kwargs):
	seq = []
	dt = 0.3

	pushSeqCmd = helper.makePushSeqCmd(seq)

	pushSeqCmd(0, '', '', "Running Shutdown sequence")

	# EJECTION SEAT SAFE/ARM HANDLE - SAFE
	pushSeqCmd(dt, 'CPT_MECHANICS.EjectionSeatSafeArmedHandle', 1)

	# OBOGS CONTROL SWITCH - OFF
	pushSeqCmd(dt, 'OXYGEN_INTERFACE.OBOGS_ControlSw', 0)

	# FLAP SWITCH - FULL
	pushSeqCmd(dt, 'CONTROL_INTERFACE.FlapSw', 0)

	# T/O TRIM BUTTON - PRESS UNTIL TRIM ADVISORY DISPLAYED
	pushSeqCmd(dt, 'CONTROL_INTERFACE.TOTrimSw', 1)
	pushSeqCmd(dt, 'CONTROL_INTERFACE.TOTrimSw', 0)

	# PARK BRK HANDLE - ON
	pushSeqCmd(dt, 'GEAR_INTERFACE.EmergParkHandleSelectEmerg', 2)
	pushSeqCmd(dt, 'GEAR_INTERFACE.EmergParkHandleSelectEmerg', 1)
	pushSeqCmd(dt, 'GEAR_INTERFACE.EmergParkHandleOnOff', 0)

	# INS KNOB - OFF
	pushSeqCmd(dt, 'INS.INS_SwitchChange', 0)

	# STANDBY ATTITUDE REFERENCE INDICATOR - CAGE
	pushSeqCmd(dt, 'SAI.SAI_pull', 1) # Pull knob.
	pushSeqCmd(dt, 'SAI.SAI_rotate', 0.015) # Rotate CW slightly to hold.
	pushSeqCmd(dt, 'SAI.SAI_pull', 0) # Push knob.

	# RADAR KNOB - OFF
	pushSeqCmd(dt, 'RADAR.RADAR_SwitchChange', 0)

	#RADAR ALTIMETER - OFF
	pushSeqCmd(dt, 'ID2163A.ID2163A_SetMinAlt', -3.125) # All the way off

	# HUD ALT SWITCH - BARO
	pushSeqCmd(dt, 'HUD.HUD_AltitudeSw', 1)

	# IR COOL SWITCH - OFF
	pushSeqCmd(dt, 'SMS.IRCoolingSw', 0)

	# DISPENSER SWITCH - OFF
	pushSeqCmd(dt, 'CMDS.Dispenser', 0)
	# ECM - OFF
	pushSeqCmd(dt, 'ASPJ.ASPJ_SwitchChange', 0)

	# CANOPY - OPEN
	pushSeqCmd(dt, 'CPT_MECHANICS.CanopySwitchClose', 2)
	pushSeqCmd(9, 'CPT_MECHANICS.CanopySwitchClose', 1, 'Canopy closed') # Turn off canopy switch 9 seconds later.

	# Left engine off
	pushSeqCmd(dt, 'scriptSimCommand', 'iCommandLeftEngineStop', 'Left throttle OFF') # Left throttle OFF

	# MFDs - OFF
	pushSeqCmd(dt, 'MDI_LEFT.MDI_off_night_day', 0)
	pushSeqCmd(dt, 'MDI_RIGHT.MDI_off_night_day', 0)
	pushSeqCmd(dt, 'AMPCD.AMPCD_off_brightness', 0)

	# HUD - OFF
	pushSeqCmd(dt, 'HUD.HUD_SymbBrightCtrl', 0)
	pushSeqCmd(dt, 'HUD.HUD_SymbBrightSelKnob', 1) # 0 = NIGHT, 1 = DAY

	# UFC BRIGHTNESS - OFF
	pushSeqCmd(dt, 'UFC.BrtDim', 0)

	# HMD knob - OFF
	pushSeqCmd(dt, 'HMD_INTERFACE.BrtKnob', 0)

	# Right engine off
	pushSeqCmd(dt, 'scriptSimCommand', 'iCommandRightEngineStop', 'Right throttle OFF') # Right throttle OFF

	# Exterior lights off
	pushSeqCmd(dt, 'EXT_LIGHTS.Formation', 0)
	pushSeqCmd(dt, 'EXT_LIGHTS.Position', 0)
	pushSeqCmd(dt, 'EXT_LIGHTS.Strobe', 0)
	pushSeqCmd(dt, 'EXT_LIGHTS.LdgTaxi', 0)

	# Interior lights off
	pushSeqCmd(dt, 'CPT_LIGHTS.ModeSw', 0) # 0 = DAY (default), 1 = NITE, 2 = NVG
	pushSeqCmd(dt, 'CPT_LIGHTS.Consoles', 0)
	pushSeqCmd(dt, 'CPT_LIGHTS.InstPnl', 0)
	pushSeqCmd(dt, 'CPT_LIGHTS.Flood', 0)
	pushSeqCmd(dt, 'CPT_LIGHTS.Chart', 0)

	pushSeqCmd(dt, 'ELEC_INTERFACE.BattSw', 1, 'BATT switch - OFF')

	return seq


###############################################################################
###############################################################################
def LoadRoute(config, vars, helper, *args, **kwargs):
	seq = []
	dt = 0.3

	pushSeqCmd = helper.makePushSeqCmd(seq)

	def pressMfdButton(mfd, btn):
		aliasToPbNumber = {
			'L1': 5,
			'L2': 4,
			'L3': 3,
			'L4': 2,
			'L5': 1,
			'T1': 6,
			'T2': 7,
			'T3': 8,
			'T4': 9,
			'T5': 10,
			'R1': 11,
			'R2': 12,
			'R3': 13,
			'R4': 14,
			'R5': 15,
			'B1': 20,
			'B2': 19,
			'B3': 18,
			'B4': 17,
			'B5': 16,
		}

		btnText = str(btn).strip().upper()
		if btnText.startswith('PB_'):
			pbNum = btnText[3:]
		elif btnText.startswith('PB'):
			pbNum = btnText[2:]
		elif btnText in aliasToPbNumber:
			pbNum = str(aliasToPbNumber[btnText])
		elif btnText.isdigit():
			pbNum = btnText
		else:
			raise ValueError(f'Unknown right MFD OSB: {btn!r}')

		if int(pbNum) < 1 or int(pbNum) > 20:
			raise ValueError(f'Right MFD OSB number out of range: {pbNum}')

		if mfd.lower() == 'left':
			prefix = 'MDI_LEFT.MDI_PB_'
		elif mfd.lower() == 'right':
			prefix = 'MDI_RIGHT.MDI_PB_'
		else:
			prefix = 'AMPCD.AMPCD_PB_'
		pbCmd = f'{prefix}{int(pbNum)}'
		pushSeqCmd(dt, pbCmd, 1)
		pushSeqCmd(dt, pbCmd, 0)
		return

	def pressUfcButton(btn):
		btn = str(btn).upper()
		aliases = {
			'N': '2',
			'S': '8',
			'E': '6',
			'W': '4',
			'-': '0',
		}
		if btn in aliases:
			cmd = aliases[btn]
		else:
			cmd = btn
		controlName = 'UFC.OptSw' + cmd[2:] if cmd.startswith('OS') else 'UFC.KbdSw' + cmd
		pushSeqCmd(dt, controlName, 1) # Press
		pushSeqCmd(dt, controlName, 0) # Release

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
	pprint.pprint(waypoints)

	# The plane must be set up in the correct configuration before proceeding.
	pushSeqCmd(dt, 'scriptSpeech', 'Attention, check configuration before proceeding')
	precise = vars.get('usePrecise', 'no')
	preciseText = 'PRECISE boxed' if precise == 'yes' else 'PRECISE not boxed'
	mfd = vars.get('mfd').lower()
	pushSeqCmd(dt, 'scriptText', f'Required config: {mfd.title()} MFD on HSI -> DATA page, {preciseText}.  Waypoints will overwrite starting from your currently selected point.  When ready, click Resume.')
	pushSeqCmd(dt, 'scriptPause')

	pushSeqCmd(dt, 'scriptSpeech', f'Do not use any functions on UFC or {mfd} MFD until waypoint entry is complete.')

	# Start entering waypoints.
	pressMfdButton(mfd, 'L1') # UFC

	waypointCount = len(waypoints)
	for waypointIndex, waypoint in enumerate(waypoints):
		pushSeqCmd(dt, '', '', f'Entering waypoint {waypointIndex + 1}/{waypointCount}')
		latLonDDM = waypoint['latLonDDM']

		pressUfcButton('OS1') # POSN

		if vars.get('usePrecise') == 'yes':
			# Enter latitude in DDM format, 4 decimal places.
			# If lat is positive, N; if negative, S.
			if latLonDDM['lat']['deg'] >= 0:
				enterUfcSequence('N')
			else:
				enterUfcSequence('S')
			deg = latLonDDM['lat']['deg']
			min = latLonDDM['lat']['min']
			wholeMin, fracMin = str(min).split('.')
			enterUfcSequence(str(deg)) # No leading zeros needed.
			enterUfcSequence(wholeMin.zfill(2)) # Pad with leading zeros to 2 digits.
			pressUfcButton('ENT')
			enterUfcSequence(fracMin[0:4].zfill(4)) # Get the first 4 digits, pad with leading zeros to 4 digits.
			pressUfcButton('ENT')

			# Enter longitude in DDM format, 4 decimal places.
			# If lon is positive, E; if negative, W.
			if latLonDDM['lon']['deg'] >= 0:
				enterUfcSequence('E')
			else:
				enterUfcSequence('W')
			deg = latLonDDM['lon']['deg']
			min = latLonDDM['lon']['min']
			wholeMin, fracMin = str(min).split('.')
			enterUfcSequence(str(deg).zfill(3)) # Pad with leading zeros to 2 digits.
			enterUfcSequence(wholeMin.zfill(2)) # Pad with leading zeros to 2 digits.
			pressUfcButton('ENT')
			enterUfcSequence(fracMin[0:4].zfill(4)) # Get the first 4 digits, pad with leading zeros to 4 digits.
			pressUfcButton('ENT')
		else:
			# Enter latitude in DDM format, 2 decimal places.
			# If lat is positive, N; if negative, S.
			if latLonDDM['lat']['deg'] >= 0:
				enterUfcSequence('N')
			else:
				enterUfcSequence('S')
			deg = latLonDDM['lat']['deg']
			min = latLonDDM['lat']['min']
			wholeMin, fracMin = str(min).split('.')
			enterUfcSequence(str(deg))
			enterUfcSequence(wholeMin.zfill(2) + fracMin[0:2].zfill(2)) # Whole mins padded to 2 digits + first 2 decimal places padded to 2 digits, no decimal point.
			pressUfcButton('ENT')

			# Enter longitude in DDM format, 2 decimal places.
			# If lon is positive, E; if negative, W.
			if latLonDDM['lon']['deg'] >= 0:
				enterUfcSequence('E')
			else:
				enterUfcSequence('W')
			deg = latLonDDM['lon']['deg']
			min = latLonDDM['lon']['min']
			wholeMin, fracMin = str(min).split('.')
			enterUfcSequence(str(deg).zfill(3))
			enterUfcSequence(wholeMin.zfill(2) + fracMin[0:2].zfill(2)) # Whole mins padded to 2 digits + first 2 decimal places padded to 2 digits, no decimal point.
			pressUfcButton('ENT')

		# Enter altitude in feet.
		pressUfcButton('OS3') # ELEV
		pressUfcButton('OS1') # FEET
		if vars.get('altitude') == 'forceGround':
			altFeet = round(waypoint['groundAltFeet'])
		else:
			altFeet = round(waypoint.get('altFeet', 0))
		enterUfcSequence(altFeet)
		pressUfcButton('ENT')

		# If we're not on the last waypoint, increment to the next waypoint.
		if waypointIndex != waypointCount - 1:
			pressMfdButton(mfd, 'R2') # Up arrow

	return seq


###############################################################################
###############################################################################
def LoadScratchpad(config, vars, helper, *args, **kwargs):
	seq = []
	dt = 0.3

	pushSeqCmd = helper.makePushSeqCmd(seq)

	def pressMfdButton(mfd, btn):
		aliasToPbNumber = {
			'L1': 5,
			'L2': 4,
			'L3': 3,
			'L4': 2,
			'L5': 1,
			'T1': 6,
			'T2': 7,
			'T3': 8,
			'T4': 9,
			'T5': 10,
			'R1': 11,
			'R2': 12,
			'R3': 13,
			'R4': 14,
			'R5': 15,
			'B1': 20,
			'B2': 19,
			'B3': 18,
			'B4': 17,
			'B5': 16,
		}

		btnText = str(btn).strip().upper()
		if btnText.startswith('PB_'):
			pbNum = btnText[3:]
		elif btnText.startswith('PB'):
			pbNum = btnText[2:]
		elif btnText in aliasToPbNumber:
			pbNum = str(aliasToPbNumber[btnText])
		elif btnText.isdigit():
			pbNum = btnText
		else:
			raise ValueError(f'Unknown right MFD OSB: {btn!r}')

		if int(pbNum) < 1 or int(pbNum) > 20:
			raise ValueError(f'Right MFD OSB number out of range: {pbNum}')

		if mfd.lower() == 'left':
			prefix = 'MDI_LEFT.MDI_PB_'
		elif mfd.lower() == 'right':
			prefix = 'MDI_RIGHT.MDI_PB_'
		else:
			prefix = 'AMPCD.AMPCD_PB_'
		pbCmd = f'{prefix}{int(pbNum)}'
		pushSeqCmd(dt, pbCmd, 1)
		pushSeqCmd(dt, pbCmd, 0)
		return

	def pressUfcButton(btn):
		btn = str(btn).upper()
		aliases = {
			'N': '2',
			'S': '8',
			'E': '6',
			'W': '4',
			'-': '0',
		}
		if btn in aliases:
			cmd = aliases[btn]
		else:
			cmd = btn
		controlName = 'UFC.OptSw' + cmd[2:] if cmd.startswith('OS') else 'UFC.KbdSw' + cmd
		pushSeqCmd(dt, controlName, 1) # Press
		pushSeqCmd(dt, controlName, 0) # Release

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

	# The plane must be set up in the correct configuration before proceeding.
	pushSeqCmd(dt, 'scriptSpeech', 'Attention, check configuration before proceeding')
	precise = vars.get('usePrecise', 'no')
	preciseText = 'PRECISE boxed' if precise == 'yes' else 'PRECISE not boxed'
	mfd = vars.get('mfd').lower()
	pushSeqCmd(dt, 'scriptText', f'Required config: {mfd.title()} MFD on HSI -> DATA page, {preciseText}.  Waypoints will overwrite starting from your currently selected point.  When ready, click Resume.')
	pushSeqCmd(dt, 'scriptPause')

	pushSeqCmd(dt, 'scriptSpeech', f'Do not use any functions on UFC or {mfd} MFD until waypoint entry is complete.')

	# Start entering waypoints.
	pressMfdButton(mfd, 'L1') # UFC

	waypointCount = len(waypoints)
	for waypointIndex, waypoint in enumerate(waypoints):
		pushSeqCmd(dt, '', '', f'Entering waypoint {waypointIndex + 1}/{waypointCount}')
		latLonDDM = waypoint['latLonDDM']

		pressUfcButton('OS1') # POSN

		if vars.get('usePrecise') == 'yes':
			# Enter latitude in DDM format, 4 decimal places.
			# If lat is positive, N; if negative, S.
			if latLonDDM['lat']['deg'] >= 0:
				enterUfcSequence('N')
			else:
				enterUfcSequence('S')
			deg = latLonDDM['lat']['deg']
			min = latLonDDM['lat']['min']
			wholeMin, fracMin = str(min).split('.')
			enterUfcSequence(str(deg)) # No leading zeros needed.
			enterUfcSequence(wholeMin.zfill(2)) # Pad with leading zeros to 2 digits.
			pressUfcButton('ENT')
			enterUfcSequence(fracMin[0:4].zfill(4)) # Get the first 4 digits, pad with leading zeros to 4 digits.
			pressUfcButton('ENT')

			# Enter longitude in DDM format, 4 decimal places.
			# If lon is positive, E; if negative, W.
			if latLonDDM['lon']['deg'] >= 0:
				enterUfcSequence('E')
			else:
				enterUfcSequence('W')
			deg = latLonDDM['lon']['deg']
			min = latLonDDM['lon']['min']
			wholeMin, fracMin = str(min).split('.')
			enterUfcSequence(str(deg).zfill(3)) # Pad with leading zeros to 2 digits.
			enterUfcSequence(wholeMin.zfill(2)) # Pad with leading zeros to 2 digits.
			pressUfcButton('ENT')
			enterUfcSequence(fracMin[0:4].zfill(4)) # Get the first 4 digits, pad with leading zeros to 4 digits.
			pressUfcButton('ENT')
		else:
			# Enter latitude in DDM format, 2 decimal places.
			# If lat is positive, N; if negative, S.
			if latLonDDM['lat']['deg'] >= 0:
				enterUfcSequence('N')
			else:
				enterUfcSequence('S')
			deg = latLonDDM['lat']['deg']
			min = latLonDDM['lat']['min']
			wholeMin, fracMin = str(min).split('.')
			enterUfcSequence(str(deg))
			enterUfcSequence(wholeMin.zfill(2) + fracMin[0:2].zfill(2)) # Whole mins padded to 2 digits + first 2 decimal places padded to 2 digits, no decimal point.
			pressUfcButton('ENT')

			# Enter longitude in DDM format, 2 decimal places.
			# If lon is positive, E; if negative, W.
			if latLonDDM['lon']['deg'] >= 0:
				enterUfcSequence('E')
			else:
				enterUfcSequence('W')
			deg = latLonDDM['lon']['deg']
			min = latLonDDM['lon']['min']
			wholeMin, fracMin = str(min).split('.')
			enterUfcSequence(str(deg).zfill(3))
			enterUfcSequence(wholeMin.zfill(2) + fracMin[0:2].zfill(2)) # Whole mins padded to 2 digits + first 2 decimal places padded to 2 digits, no decimal point.
			pressUfcButton('ENT')

		# Enter altitude in feet.
		pressUfcButton('OS3') # ELEV
		pressUfcButton('OS1') # FEET
		if vars.get('altitude') == 'forceGround':
			altFeet = round(waypoint['groundAltFeet'])
		else:
			altFeet = round(waypoint.get('altFeet'))
		enterUfcSequence(altFeet)
		pressUfcButton('ENT')

		# If we're not on the last waypoint, increment to the next waypoint.
		if waypointIndex != waypointCount - 1:
			pressMfdButton(mfd, 'R2') # Up arrow

	return seq
