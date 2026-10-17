# Return a Dictionary of script data.  The 'scripts' key is a list of scripts that users will be selecting from.  Each script has an associated 'function', which is the name of the function in this file that will be called to generate the command sequence, and a dictionary of 'vars' that the user will be prompted to choose from before running the script, and will be passed into the sequence generating function.
def getScriptData():
	return {
		'moduleName': 'C-130J-30',
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
					'electronicCircuitBreakers': {
						'label': 'Electronic Circuit Breakers',
						'options': {
							'reset': 'Reset',
							'dontReset': 'Don\'t Reset',
						},
					},
					'apu': {
						'label': 'APU',
						'options': {
							'leaveOn': 'Leave on at the end',
							'turnOff': 'Turn off at the end',
						},
					},
				},
			},
			{
				'name': 'Cold Start with Preflight',
				'function': 'ColdStartPreflight',
				'vars': {
					'time': {
						'label': 'Time',
						'options': {
							'day': 'Day',
							'night': 'Night',
						},
					},
					'apu': {
						'label': 'APU',
						'options': {
							'leaveOn': 'Leave on at the end',
							'turnOff': 'Turn off at the end',
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
					'apu': {
						'label': 'APU',
						'options': {
							'leaveOn': 'Leave on at the end',
							'turnOff': 'Turn off at the end',
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
			#		'apu': {
			#			'label': 'APU',
			#			'options': {
			#				'leaveOn': 'Leave on at the end',
			#				'turnOff': 'Turn off at the end',
			#			},
			#		},
			#	},
			#},
		],
	}


def getInfo():
	return ''

# A "preflight complete" spawn has the battery, all four generators and the APU on; cold and dark has them all off.
PREFLIGHT_STATE = {
	'ENGINE_APU_CTRL.battery': 1,
	'ENGINE_APU_CTRL.gen_1': 1,
	'ENGINE_APU_CTRL.gen_2': 1,
	'ENGINE_APU_CTRL.gen_3': 1,
	'ENGINE_APU_CTRL.gen_4': 1,
	'ENGINE_APU_CTRL.ext_elec': 2, # 0 = EXT PWR, 1 = OFF, 2 = APU
}

def autoSelect(context):
	if context.script != 'Cold Start':
		return {}
	if context.read(*PREFLIGHT_STATE) == PREFLIGHT_STATE:
		return {'script': 'Cold Start with Preflight'}
	return {}

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

	pushSeqCmd(0, '', '', 'Running Cold Start sequence')
	pushSeqCmd(dt, 'scriptSpeech', 'Set throttles to ground idle.')

	# Oil Cooler Flap switches ... AUTO (rear overhead panel)
	pushSeqCmd(dt, 'MECH_INTERFACE.oil_flap_1_auto', 1)  # Engine 1 oil cooler flap ... AUTO
	pushSeqCmd(dt, 'MECH_INTERFACE.oil_flap_2_auto', 1)  # Engine 2 oil cooler flap ... AUTO
	pushSeqCmd(dt, 'MECH_INTERFACE.oil_flap_3_auto', 1)  # Engine 3 oil cooler flap ... AUTO
	pushSeqCmd(dt, 'MECH_INTERFACE.oil_flap_4_auto', 1)  # Engine 4 oil cooler flap ... AUTO

	# Generator switches 1-4 ... ON (forward overhead panel)
	pushSeqCmd(dt, 'ENGINE_APU_CTRL.gen_1', 1)  # GEN 1 switch ... ON
	pushSeqCmd(dt, 'ENGINE_APU_CTRL.gen_2', 1)  # GEN 2 switch ... ON
	pushSeqCmd(dt, 'ENGINE_APU_CTRL.gen_3', 1)  # GEN 3 switch ... ON
	pushSeqCmd(dt, 'ENGINE_APU_CTRL.gen_4', 1)  # GEN 4 switch ... ON

	# Battery switch ... ON
	pushSeqCmd(dt, 'ENGINE_APU_CTRL.battery', 1)  # BTRY switch ... ON

	# Wait 50 seconds for avionics to power up (APU will not start until then).
	pushSeqCmd(dt, 'scriptText', 'Waiting for avionics to power up (50 sec)...')
	pushSeqCmd(50, 'scriptText', 'Avionics should be powered up now.')

	# Master Caution ... Reset
	pushSeqCmd(dt, 'PILOT_REF_MODE_PANEL.master_caution', 1)  # press
	pushSeqCmd(dt, 'PILOT_REF_MODE_PANEL.master_caution', 0)  # release

	# APU start: hold START for 5 sec, then release to RUN
	# ENGINE_APU_CTRL.apu_selector: positive value steps: STOP -> RUN -> START; negative value steps: START -> RUN -> STOP
	# ENGINE_APU_CTRL.apu_select_stop: 1 = STOP, 0 = RUN
	pushSeqCmd(dt, 'ENGINE_APU_CTRL.apu_selector', 1) # APU start switch ... START, positive value steps: STOP -> RUN -> START; negative value steps: START -> RUN -> STOP
	pushSeqCmd(dt, 'ENGINE_APU_CTRL.apu_selector', 1) # APU start switch ... START, positive value steps: STOP -> RUN -> START; negative value steps: START -> RUN -> STOP
	pushSeqCmd(5, 'ENGINE_APU_CTRL.apu_selector', -1) # Release to RUN, positive value steps: STOP -> RUN -> START; negative value steps: START -> RUN -> STOP
	pushSeqCmd(dt, 'scriptText', 'APU starting. Waiting 30 sec for 100% RPM...')
	pushSeqCmd(30, 'scriptText', 'APU should be at 100% RPM.')

	# External Power/APU switch ... APU
	pushSeqCmd(dt, 'ENGINE_APU_CTRL.ext_elec', 2)  # 0 = EXT PWR, 1 = OFF, 2 = APU

	# NOTE: GPS acquisition starts when aircraft is on APU power.  Takes 1 minute, but we don't need a timer, because it'll have acquired by the time the engines are started.

	# Wait 8 seconds for the remaining avionics to power up.
	pushSeqCmd(dt, 'scriptText', 'Waiting for remaining avionics to power up (8 sec)...')
	pushSeqCmd(8, 'scriptText', 'Remaining avionics should be powered up now.')

	# Reset Electronic Circuit Breakers (if selected)
	if vars['electronicCircuitBreakers'] == 'reset':
		pushSeqCmd(dt, 'scriptSpeech', 'Resetting Electronic Circuit Breakers.')
		# Press CNBP ECB Key to open ECB page
		pushSeqCmd(dt, 'CNBP.cmd_3023', 1)  # ECB key ... press
		pushSeqCmd(dt, 'CNBP.cmd_3023', 0)  # release
		# Type 2 then press LSK L1 (HDD) to display ECBs on HDD 2
		pushSeqCmd(dt, 'CNBP.cmd_3003', 1)  # 2 key ... press
		pushSeqCmd(dt, 'CNBP.cmd_3003', 0)  # release
		pushSeqCmd(dt, 'CNBP.cmd_3013', 1)  # LSK L1 (HDD) ... press
		pushSeqCmd(dt, 'CNBP.cmd_3013', 0)  # release
		# Enter ECB circuit numbers: 481 482 483 902 108 109 609 613
		# 481
		pushSeqCmd(dt, 'CNBP.cmd_3005', 1);  pushSeqCmd(dt, 'CNBP.cmd_3005', 0)  # 4
		pushSeqCmd(dt, 'CNBP.cmd_3009', 1);  pushSeqCmd(dt, 'CNBP.cmd_3009', 0)  # 8
		pushSeqCmd(dt, 'CNBP.cmd_3002', 1);  pushSeqCmd(dt, 'CNBP.cmd_3002', 0)  # 1
		# 482
		pushSeqCmd(dt, 'CNBP.cmd_3005', 1);  pushSeqCmd(dt, 'CNBP.cmd_3005', 0)  # 4
		pushSeqCmd(dt, 'CNBP.cmd_3009', 1);  pushSeqCmd(dt, 'CNBP.cmd_3009', 0)  # 8
		pushSeqCmd(dt, 'CNBP.cmd_3003', 1);  pushSeqCmd(dt, 'CNBP.cmd_3003', 0)  # 2
		# 483
		pushSeqCmd(dt, 'CNBP.cmd_3005', 1);  pushSeqCmd(dt, 'CNBP.cmd_3005', 0)  # 4
		pushSeqCmd(dt, 'CNBP.cmd_3009', 1);  pushSeqCmd(dt, 'CNBP.cmd_3009', 0)  # 8
		pushSeqCmd(dt, 'CNBP.cmd_3004', 1);  pushSeqCmd(dt, 'CNBP.cmd_3004', 0)  # 3
		# 902
		pushSeqCmd(dt, 'CNBP.cmd_3010', 1);  pushSeqCmd(dt, 'CNBP.cmd_3010', 0)  # 9
		pushSeqCmd(dt, 'CNBP.cmd_3001', 1);  pushSeqCmd(dt, 'CNBP.cmd_3001', 0)  # 0
		pushSeqCmd(dt, 'CNBP.cmd_3003', 1);  pushSeqCmd(dt, 'CNBP.cmd_3003', 0)  # 2
		# 108
		pushSeqCmd(dt, 'CNBP.cmd_3002', 1);  pushSeqCmd(dt, 'CNBP.cmd_3002', 0)  # 1
		pushSeqCmd(dt, 'CNBP.cmd_3001', 1);  pushSeqCmd(dt, 'CNBP.cmd_3001', 0)  # 0
		pushSeqCmd(dt, 'CNBP.cmd_3009', 1);  pushSeqCmd(dt, 'CNBP.cmd_3009', 0)  # 8
		# 109
		pushSeqCmd(dt, 'CNBP.cmd_3002', 1);  pushSeqCmd(dt, 'CNBP.cmd_3002', 0)  # 1
		pushSeqCmd(dt, 'CNBP.cmd_3001', 1);  pushSeqCmd(dt, 'CNBP.cmd_3001', 0)  # 0
		pushSeqCmd(dt, 'CNBP.cmd_3010', 1);  pushSeqCmd(dt, 'CNBP.cmd_3010', 0)  # 9
		# 609
		pushSeqCmd(dt, 'CNBP.cmd_3007', 1);  pushSeqCmd(dt, 'CNBP.cmd_3007', 0)  # 6
		pushSeqCmd(dt, 'CNBP.cmd_3001', 1);  pushSeqCmd(dt, 'CNBP.cmd_3001', 0)  # 0
		pushSeqCmd(dt, 'CNBP.cmd_3010', 1);  pushSeqCmd(dt, 'CNBP.cmd_3010', 0)  # 9
		# 613
		pushSeqCmd(dt, 'CNBP.cmd_3007', 1);  pushSeqCmd(dt, 'CNBP.cmd_3007', 0)  # 6
		pushSeqCmd(dt, 'CNBP.cmd_3002', 1);  pushSeqCmd(dt, 'CNBP.cmd_3002', 0)  # 1
		pushSeqCmd(dt, 'CNBP.cmd_3004', 1);  pushSeqCmd(dt, 'CNBP.cmd_3004', 0)  # 3
		# Press LSK R1 (RESET) twice to reset and confirm
		pushSeqCmd(dt, 'CNBP.cmd_3017', 1)  # LSK R1 (RESET) ... press
		pushSeqCmd(dt, 'CNBP.cmd_3017', 0)  # release
		pushSeqCmd(dt, 'CNBP.cmd_3017', 1)  # Confirm ... press
		pushSeqCmd(dt, 'CNBP.cmd_3017', 0)  # release
		# Press LSK L1 again to turn off ECB page and restore HDD
		pushSeqCmd(dt, 'CNBP.cmd_3013', 1)  # LSK L1 (HDD/OFF) ... press
		pushSeqCmd(dt, 'CNBP.cmd_3013', 0)  # release

	# APU Bleed Air ... OPEN
	pushSeqCmd(dt, 'ENGINE_APU_CTRL.bleed_apu', 1) # Press
	pushSeqCmd(dt, 'ENGINE_APU_CTRL.bleed_apu', 0) # Release

	# ELEV TRIM TAB switch ... NORM
	pushSeqCmd(dt, 'MECH_INTERFACE.elev_trim', 2)  # 0 = EMER, 1 = OFF, 2 = NORM

	# Master Avionics - ON
	pushSeqCmd(dt, 'P_CNI.SELECT_10', 1) # MSTR AV ON
	pushSeqCmd(dt, 'P_CNI.SELECT_10', 0) # Release

	# Pilot Oxygen Diluter Lever ... NORMAL OXYGEN
	pushSeqCmd(dt, 'PLANE_ATM.cmd_3029', 0) # NORMAL OXYGEN
	# Copilot Oxygen Diluter Lever ... NORMAL OXYGEN
	pushSeqCmd(dt, 'PLANE_ATM.cmd_3034', 0) # NORMAL OXYGEN # NOTE The label for this is swapped with the 'Copilot Oxygen Supply Lever'.  This appears to be a bug.

	# Turn on and set up HUD for pilot and copilot.
	# Pilot HUD
	pushSeqCmd(dt, 'P_DISPLAYS.cmd_3023', 1) # Pilot HUD latch ... deploy (down)
	pushSeqCmd(dt, 'P_DISPLAYS.cmd_3025', 1) # Pilot HUD BRT knob ... pull ON
	pushSeqCmd(dt, 'P_DISPLAYS.cmd_3027', 1) # Pilot HUD NAV mode ... ON
	pushSeqCmd(dt, 'P_DISPLAYS.cmd_3027', 0) # release
	pushSeqCmd(dt, 'P_DISPLAYS.cmd_3028', 1) # Pilot HUD TACT mode ... ON
	pushSeqCmd(dt, 'P_DISPLAYS.cmd_3028', 0) # release
	pushSeqCmd(dt, 'P_DISPLAYS.cmd_3029', 1) # Pilot HUD UNCG ... uncage velocity vector
	pushSeqCmd(dt, 'P_DISPLAYS.cmd_3029', 0) # release
	# Copilot HUD
	pushSeqCmd(dt, 'C_DISPLAYS.cmd_3023', 1) # Copilot HUD latch ... deploy (down)
	pushSeqCmd(dt, 'C_DISPLAYS.cmd_3025', 1) # Copilot HUD BRT knob ... pull ON
	pushSeqCmd(dt, 'C_DISPLAYS.cmd_3027', 1) # Copilot HUD NAV mode ... ON
	pushSeqCmd(dt, 'C_DISPLAYS.cmd_3027', 0) # release
	pushSeqCmd(dt, 'C_DISPLAYS.cmd_3028', 1) # Copilot HUD TACT mode ... ON
	pushSeqCmd(dt, 'C_DISPLAYS.cmd_3028', 0) # release
	pushSeqCmd(dt, 'C_DISPLAYS.cmd_3029', 1) # Copilot HUD UNCG ... uncage velocity vector
	pushSeqCmd(dt, 'C_DISPLAYS.cmd_3029', 0) # release

	# Pressurization Mode knob ... AUTO
	pushSeqCmd(dt, 'PLANE_ATM.cmd_3012', 2) # 0 = CONST ALT, 1 = MAN, 2 = AUTO, 3 = NO PRESS, 4 = AUX VENT

	# Air Conditioning POWER buttons ... ON (forward overhead panel)
	pushSeqCmd(dt, 'PLANE_ATM.cmd_3001', 1) # Flight Station A/C Power ... ON
	pushSeqCmd(dt, 'PLANE_ATM.cmd_3001', 0) # Release
	pushSeqCmd(dt, 'PLANE_ATM.cmd_3002', 1) # Cargo Compartment A/C Power ... ON
	pushSeqCmd(dt, 'PLANE_ATM.cmd_3002', 0) # Release

	# Hydraulic system
	pushSeqCmd(dt, 'HYDRAULICS.aux_pump', 1) # AUX PUMP switch ... ON
	pushSeqCmd(dt, 'ENGINE_APU_CTRL.anti_skid', 1) # ANTI-SKID switch ... ON
	pushSeqCmd(dt, 'HYDRAULICS.suction_boost_pump_boost', 1) # SUCTION BOOST PUMP switch ... ON
	pushSeqCmd(dt, 'HYDRAULICS.suction_boost_pump_boost', 0) # Release
	pushSeqCmd(dt, 'HYDRAULICS.suction_boost_pump_util', 1) # UTILITY SUCTION BOOST PUMP switch ... ON
	pushSeqCmd(dt, 'HYDRAULICS.suction_boost_pump_util', 0) # Release

	# Exterior lighting (forward overhead panel left)
	#pushSeqCmd(dt, 'LIGHTING_PANELS.ext_nav', 0) # Navigation Light Mode switch ... STEADY, 0 = STEADY, 1 = OFF, 2 = FLASH
	#pushSeqCmd(dt, 'LIGHTING_PANELS.ext_strobe_top', 2) # Top Strobe Light switch ... RED, 0 = WHITE, 1 = OFF, 2 = RED
	#pushSeqCmd(dt, 'LIGHTING_PANELS.ext_strobe_btm', 2) # Bottom Strobe Light switch ... RED, 0 = WHITE, 1 = OFF, 2 = RED

	# Interior lighting
	if vars['time'] == 'night':
		pushSeqCmd(dt, 'LIGHTING_PANELS.pilot_side_panel', 0.5) # Pilot Panel Backlighting ... 50%
		pushSeqCmd(dt, 'LIGHTING_PANELS.pilot_side_flood', 0.3) # Pilot Panel Flood Lighting ... 30%
		pushSeqCmd(dt, 'LIGHTING_PANELS.copilot_side_panel', 0.5) # Copilot Panel Backlighting ... 50%
		pushSeqCmd(dt, 'LIGHTING_PANELS.copilot_side_flood', 0.3) # Copilot Panel Flood Lighting ... 30%
		pushSeqCmd(dt, 'LIGHTING_PANELS.cp_ctrl_cnsl', 0.5) # Center Console Backlighting ... 50%
		pushSeqCmd(dt, 'LIGHTING_PANELS.overhead', 0.5) # Overhead Panel Backlighting ... 50%

	# Backup ADI ... Uncage
	pushSeqCmd(dt, 'MECH_INTERFACE.pitch_bar', 0.25) # Move pitch bar down.
	pushSeqCmd(dt, 'MECH_INTERFACE.pitch_bar', 0.51) # Move pitch bar back up to uncage.  NOTE If you do it to 0.50 exactly, it will not uncage, it must be slightly more or less than 0.50.
	pushSeqCmd(dt, 'MECH_INTERFACE.pitch_bar', 0.5) # Move pitch bar to center.

	# Anti-Icing systems (ICE PROTECTION panel, rear overhead panel left)
	pushSeqCmd(dt, 'ENGINE_APU_CTRL.ice_prop_1', 1) # Propeller 1 Ice Protection switch ... AUTO, 0 = ON, 1 = AUTO, 2 = OFF
	pushSeqCmd(dt, 'ENGINE_APU_CTRL.ice_prop_2', 1) # Propeller 2 Ice Protection switch ... AUTO, 0 = ON, 1 = AUTO, 2 = OFF
	pushSeqCmd(dt, 'ENGINE_APU_CTRL.ice_prop_3', 1) # Propeller 3 Ice Protection switch ... AUTO, 0 = ON, 1 = AUTO, 2 = OFF
	pushSeqCmd(dt, 'ENGINE_APU_CTRL.ice_prop_4', 1) # Propeller 4 Ice Protection switch ... AUTO, 0 = ON, 1 = AUTO, 2 = OFF
	pushSeqCmd(dt, 'ENGINE_APU_CTRL.ice_pitot_c', 0) # Pilot Pitot Heat switch ... ON, 0 = ON, 1 = OFF
	pushSeqCmd(dt, 'ENGINE_APU_CTRL.ice_pitot_cp', 0) # Copilot Pitot Heat switch ... ON, 0 = ON, 1 = OFF
	pushSeqCmd(dt, 'ENGINE_APU_CTRL.ice_nesa_ctr', 0) # Center NESA Heat switch ... ON, 0 = ON, 1 = OFF
	pushSeqCmd(dt, 'ENGINE_APU_CTRL.ice_nesa_side', 0) # Side/Lower NESA Heat switch ... ON, 0 = ON, 1 = OFF

	# RADAR MASTER knob ... ON
	pushSeqCmd(dt, 'NAV_RADAR.master_mode', 1) # 0 = OFF, 1 = ON, 2 = TEST

	# Set throttles to GND IDLE and keep them there through engine startup.
	pushSeqCmd(dt, 'scriptSpeech', 'Holding throttles at ground idle for engine startup.')
	pushSeqCmd(dt, 'scriptSimCommand', 'iCommandPlaneThrustCommon', 'Throttles to GND IDLE', value=0.678, hold=True)

	# Engine 3 start: hold START for 5 sec, then release to RUN
	# ENGINE_APU_CTRL.engine_N_start_select: positive value steps: MOTOR -> STOP -> RUN -> START; negative value steps: START -> RUN -> STOP -> MOTOR
	pushSeqCmd(dt, 'scriptSpeech', 'Starting engine 3.')
	pushSeqCmd(dt, 'ENGINE_APU_CTRL.engine_3_start_select', 1) # STOP -> RUN
	pushSeqCmd(dt, 'ENGINE_APU_CTRL.engine_3_start_select', 1) # RUN -> START
	pushSeqCmd(5, 'ENGINE_APU_CTRL.engine_3_start_select', -1) # Release to RUN
	pushSeqCmd(dt, 'scriptText', 'Engine 3 starting. Waiting 45 sec for ground idle...')
	pushSeqCmd(45, 'scriptText', 'Engine 3 should be at ground idle.')

	# Start remaining engines together.
	pushSeqCmd(dt, 'scriptSpeech', 'Starting engines 1, 2, and 4.')
	pushSeqCmd(dt, 'ENGINE_APU_CTRL.engine_1_start_select', 1) # STOP -> RUN
	pushSeqCmd(dt, 'ENGINE_APU_CTRL.engine_1_start_select', 1) # RUN -> START
	pushSeqCmd(dt, 'ENGINE_APU_CTRL.engine_2_start_select', 1) # STOP -> RUN
	pushSeqCmd(dt, 'ENGINE_APU_CTRL.engine_2_start_select', 1) # RUN -> START
	pushSeqCmd(dt, 'ENGINE_APU_CTRL.engine_4_start_select', 1) # STOP -> RUN
	pushSeqCmd(dt, 'ENGINE_APU_CTRL.engine_4_start_select', 1) # RUN -> START
	pushSeqCmd(5, 'ENGINE_APU_CTRL.engine_1_start_select', -1) # Release to RUN
	pushSeqCmd(dt, 'ENGINE_APU_CTRL.engine_2_start_select', -1) # Release to RUN
	pushSeqCmd(dt, 'ENGINE_APU_CTRL.engine_4_start_select', -1) # Release to RUN
	pushSeqCmd(dt, 'scriptText', 'Engines 1, 2, and 4 starting. Waiting 45 sec for ground idle...')
	pushSeqCmd(35, 'scriptSpeech', 'Releasing throttles to your control in 10 seconds.  Set physical controls to ground idle position.')
	pushSeqCmd(10, 'scriptSimCommand', 'iCommandPlaneThrustCommon', release=True)
	pushSeqCmd(dt, 'scriptSpeech', 'Throttles are yours again.')

	# GPS acquisition takes 1 minute from when aircraft goes onto APU power.  By the time we get here (after engine start), it should have acquired.
	pushSeqCmd(dt, 'P_CNI.INDEX', 1) # INDX button
	pushSeqCmd(dt, 'P_CNI.INDEX', 0) # Release
	pushSeqCmd(dt, 'P_CNI.SELECT_1', 1) # POWER UP
	pushSeqCmd(dt, 'P_CNI.SELECT_1', 0) # Release
	pushSeqCmd(dt, 'P_CNI.SELECT_11', 1) # AUTONAV
	pushSeqCmd(dt, 'P_CNI.SELECT_11', 0) # Release

	# DEFENSIVE SYSTEMS MASTER switch ... OPR
	pushSeqCmd(dt, 'CMS_MGR.arm_toggle_cms', 1) # 0 = STBY, 1 = OPR
	# DEFENSIVE SYSTEMS ECM switch ... OPR
	pushSeqCmd(dt, 'CMS_MGR.mws_arm', 1) # 0 = STBY, 1 = OPR
	# DEFENSIVE SYSTEMS IRCM switch ... OPR
	pushSeqCmd(dt, 'CMS_MGR.ircm_toggle', 1) # 0 = STBY, 1 = OPR
	# DEFENSIVE SYSTEMS CMDS knob ... MAN or as desired
	pushSeqCmd(dt, 'CMS_MGR.cms_profile_mode', 1) # 0 = OFF, 1 = MAN, 2 = SEMI, 3 = AUTO, 4 = BYP

	# CDU MC IDX button ... Press
	pushSeqCmd(dt, 'P_CNI.MC_INDX', 1) # MC IDX
	pushSeqCmd(dt, 'P_CNI.MC_INDX', 0) # Release
	pushSeqCmd(dt, 'P_CNI.SELECT_7', 1) # DEF SYS
	pushSeqCmd(dt, 'P_CNI.SELECT_7', 0) # Release
	pushSeqCmd(dt, 'P_CNI.SELECT_1', 1) # MSTR PWR
	pushSeqCmd(dt, 'P_CNI.SELECT_1', 0) # Release
	# Return to INDEX screen.
	pushSeqCmd(dt, 'P_CNI.INDEX', 1) # INDX button
	pushSeqCmd(dt, 'P_CNI.INDEX', 0) # Release

	# Set GCAS to Tactical mode
	pushSeqCmd(dt, 'P_DISPLAYS.cmd_3008', 1) # GCAS/TAWS AND STALL
	pushSeqCmd(dt, 'P_DISPLAYS.cmd_3008', 0) # Release
	pushSeqCmd(dt, 'P_DISPLAYS.cmd_3011', 1) # NORMAL/TACTICAL (toggles)
	pushSeqCmd(dt, 'P_DISPLAYS.cmd_3011', 0) # Release
	pushSeqCmd(dt, 'P_DISPLAYS.cmd_3018', 1) # MAIN MENU
	pushSeqCmd(dt, 'P_DISPLAYS.cmd_3018', 0) # Release

	if vars['apu'] == 'turnOff':
		# APU shutdown
		pushSeqCmd(dt, 'ENGINE_APU_CTRL.ext_elec', 1) # External Power/APU switch ... OFF, 0 = EXT PWR, 1 = OFF, 2 = APU
		pushSeqCmd(dt, 'ENGINE_APU_CTRL.apu_selector', -1) # APU start switch ... RUN -> STOP

	# Parking brake is left set.
	pushSeqCmd(dt, 'scriptSpeech', 'Startup complete. Hold brakes and release parking brake when ready to taxi.')

	return seq


###############################################################################
###############################################################################
def ColdStartPreflight(config, vars, helper, *args, **kwargs):
	seq = []
	dt = 0.3

	pushSeqCmd = helper.makePushSeqCmd(seq)

	pushSeqCmd(0, '', '', 'Running Cold Start Preflight sequence')
	pushSeqCmd(dt, 'scriptSpeech', 'Set throttles to ground idle.')

	# Pilot Oxygen Diluter Lever ... NORMAL OXYGEN
	pushSeqCmd(dt, 'PLANE_ATM.cmd_3029', 0) # NORMAL OXYGEN
	# Copilot Oxygen Diluter Lever ... NORMAL OXYGEN
	pushSeqCmd(dt, 'PLANE_ATM.cmd_3034', 0) # NORMAL OXYGEN # NOTE The label for this is swapped with the 'Copilot Oxygen Supply Lever'.  This appears to be a bug.

	# DEFENSIVE SYSTEMS MASTER switch ... OPR
	pushSeqCmd(dt, 'CMS_MGR.arm_toggle_cms', 1) # 0 = STBY, 1 = OPR
	# DEFENSIVE SYSTEMS ECM switch ... OPR
	pushSeqCmd(dt, 'CMS_MGR.mws_arm', 1) # 0 = STBY, 1 = OPR
	# DEFENSIVE SYSTEMS IRCM switch ... OPR
	pushSeqCmd(dt, 'CMS_MGR.ircm_toggle', 1) # 0 = STBY, 1 = OPR
	# DEFENSIVE SYSTEMS CMDS knob ... MAN or as desired
	pushSeqCmd(dt, 'CMS_MGR.cms_profile_mode', 1) # 0 = OFF, 1 = MAN, 2 = SEMI, 3 = AUTO, 4 = BYP

	# CDU MC IDX button ... Press
	pushSeqCmd(dt, 'P_CNI.MC_INDX', 1) # MC IDX
	pushSeqCmd(dt, 'P_CNI.MC_INDX', 0) # Release
	pushSeqCmd(dt, 'P_CNI.SELECT_7', 1) # DEF SYS
	pushSeqCmd(dt, 'P_CNI.SELECT_7', 0) # Release
	pushSeqCmd(dt, 'P_CNI.SELECT_1', 1) # MSTR PWR
	pushSeqCmd(dt, 'P_CNI.SELECT_1', 0) # Release
	# NOTE Does this require you to have weight off wheels??

	# Turn on and set up HUD for pilot and copilot.
	# Pilot HUD
	pushSeqCmd(dt, 'P_DISPLAYS.cmd_3025', 1) # Pilot HUD BRT knob ... pull ON
	pushSeqCmd(dt, 'P_DISPLAYS.cmd_3029', 1) # Pilot HUD UNCG ... uncage velocity vector
	pushSeqCmd(dt, 'P_DISPLAYS.cmd_3029', 0) # release
	# Copilot HUD
	pushSeqCmd(dt, 'C_DISPLAYS.cmd_3025', 1) # Copilot HUD BRT knob ... pull ON
	pushSeqCmd(dt, 'C_DISPLAYS.cmd_3029', 1) # Copilot HUD UNCG ... uncage velocity vector
	pushSeqCmd(dt, 'C_DISPLAYS.cmd_3029', 0) # release

	# Air Conditioning POWER buttons ... ON (forward overhead panel)
	pushSeqCmd(dt, 'PLANE_ATM.cmd_3001', 1) # Flight Station A/C Power ... ON
	pushSeqCmd(dt, 'PLANE_ATM.cmd_3001', 0) # Release
	pushSeqCmd(dt, 'PLANE_ATM.cmd_3002', 1) # Cargo Compartment A/C Power ... ON
	pushSeqCmd(dt, 'PLANE_ATM.cmd_3002', 0) # Release

	# Hydraulic system
	pushSeqCmd(dt, 'HYDRAULICS.aux_pump', 1) # AUX PUMP switch ... ON
	pushSeqCmd(dt, 'HYDRAULICS.suction_boost_pump_boost', 1) # SUCTION BOOST PUMP switch ... ON
	pushSeqCmd(dt, 'HYDRAULICS.suction_boost_pump_boost', 0) # Release
	pushSeqCmd(dt, 'HYDRAULICS.suction_boost_pump_util', 1) # UTILITY SUCTION BOOST PUMP switch ... ON
	pushSeqCmd(dt, 'HYDRAULICS.suction_boost_pump_util', 0) # Release

	# Exterior lighting (forward overhead panel left)
	#pushSeqCmd(dt, 'LIGHTING_PANELS.ext_nav', 0) # Navigation Light Mode switch ... STEADY, 0 = STEADY, 1 = OFF, 2 = FLASH
	#pushSeqCmd(dt, 'LIGHTING_PANELS.ext_strobe_top', 2) # Top Strobe Light switch ... RED, 0 = WHITE, 1 = OFF, 2 = RED
	#pushSeqCmd(dt, 'LIGHTING_PANELS.ext_strobe_btm', 2) # Bottom Strobe Light switch ... RED, 0 = WHITE, 1 = OFF, 2 = RED

	# Interior lighting
	if vars['time'] == 'night':
		pushSeqCmd(dt, 'LIGHTING_PANELS.pilot_side_panel', 0.5) # Pilot Panel Backlighting ... 50%
		pushSeqCmd(dt, 'LIGHTING_PANELS.pilot_side_flood', 0.3) # Pilot Panel Flood Lighting ... 30%
		pushSeqCmd(dt, 'LIGHTING_PANELS.copilot_side_panel', 0.5) # Copilot Panel Backlighting ... 50%
		pushSeqCmd(dt, 'LIGHTING_PANELS.copilot_side_flood', 0.3) # Copilot Panel Flood Lighting ... 30%
		pushSeqCmd(dt, 'LIGHTING_PANELS.cp_ctrl_cnsl', 0.5) # Center Console Backlighting ... 50%
		pushSeqCmd(dt, 'LIGHTING_PANELS.overhead', 0.5) # Overhead Panel Backlighting ... 50%

	# RADAR MASTER knob ... ON
	pushSeqCmd(dt, 'NAV_RADAR.master_mode', 1) # 0 = OFF, 1 = ON, 2 = TEST

	# Set throttles to GND IDLE and keep them there through engine startup.
	pushSeqCmd(dt, 'scriptSpeech', 'Holding throttles at ground idle for engine startup.')
	pushSeqCmd(dt, 'scriptSimCommand', 'iCommandPlaneThrustCommon', 'Throttles to GND IDLE', value=0.678, hold=True)

	# Engine 3 start: hold START for 5 sec, then release to RUN
	# ENGINE_APU_CTRL.engine_N_start_select: positive value steps: MOTOR -> STOP -> RUN -> START; negative value steps: START -> RUN -> STOP -> MOTOR
	pushSeqCmd(dt, 'scriptSpeech', 'Starting engine 3.')
	pushSeqCmd(dt, 'ENGINE_APU_CTRL.engine_3_start_select', 1) # STOP -> RUN
	pushSeqCmd(dt, 'ENGINE_APU_CTRL.engine_3_start_select', 1) # RUN -> START
	pushSeqCmd(5, 'ENGINE_APU_CTRL.engine_3_start_select', -1) # Release to RUN
	pushSeqCmd(dt, 'scriptText', 'Engine 3 starting. Waiting 45 sec for ground idle...')
	pushSeqCmd(45, 'scriptText', 'Engine 3 should be at ground idle.')

	# Start remaining engines together.
	pushSeqCmd(dt, 'scriptSpeech', 'Starting engines 1, 2, and 4.')
	pushSeqCmd(dt, 'ENGINE_APU_CTRL.engine_1_start_select', 1) # STOP -> RUN
	pushSeqCmd(dt, 'ENGINE_APU_CTRL.engine_1_start_select', 1) # RUN -> START
	pushSeqCmd(dt, 'ENGINE_APU_CTRL.engine_2_start_select', 1) # STOP -> RUN
	pushSeqCmd(dt, 'ENGINE_APU_CTRL.engine_2_start_select', 1) # RUN -> START
	pushSeqCmd(dt, 'ENGINE_APU_CTRL.engine_4_start_select', 1) # STOP -> RUN
	pushSeqCmd(dt, 'ENGINE_APU_CTRL.engine_4_start_select', 1) # RUN -> START
	pushSeqCmd(5, 'ENGINE_APU_CTRL.engine_1_start_select', -1) # Release to RUN
	pushSeqCmd(dt, 'ENGINE_APU_CTRL.engine_2_start_select', -1) # Release to RUN
	pushSeqCmd(dt, 'ENGINE_APU_CTRL.engine_4_start_select', -1) # Release to RUN
	pushSeqCmd(dt, 'scriptText', 'Engines 1, 2, and 4 starting. Waiting 45 sec for ground idle...')
	pushSeqCmd(35, 'scriptSpeech', 'Releasing throttles to your control in 10 seconds.  Set physical controls to ground idle position.')
	pushSeqCmd(10, 'scriptSimCommand', 'iCommandPlaneThrustCommon', release=True)
	pushSeqCmd(dt, 'scriptSpeech', 'Throttles are yours again.')

	# Set GCAS to Tactical mode
	pushSeqCmd(dt, 'P_DISPLAYS.cmd_3008', 1) # GCAS/TAWS AND STALL
	pushSeqCmd(dt, 'P_DISPLAYS.cmd_3008', 0) # Release
	pushSeqCmd(dt, 'P_DISPLAYS.cmd_3011', 1) # NORMAL/TACTICAL (toggles)
	pushSeqCmd(dt, 'P_DISPLAYS.cmd_3011', 0) # Release
	pushSeqCmd(dt, 'P_DISPLAYS.cmd_3018', 1) # MAIN MENU
	pushSeqCmd(dt, 'P_DISPLAYS.cmd_3018', 0) # Release

	if vars['apu'] == 'turnOff':
		# APU shutdown
		pushSeqCmd(dt, 'ENGINE_APU_CTRL.ext_elec', 1) # External Power/APU switch ... OFF, 0 = EXT PWR, 1 = OFF, 2 = APU
		pushSeqCmd(dt, 'ENGINE_APU_CTRL.apu_selector', -1) # APU start switch ... RUN -> STOP

	# Parking brake is left set.
	pushSeqCmd(dt, 'scriptSpeech', 'Startup complete. Hold brakes and release parking brake when ready to taxi.')

	return seq


###############################################################################
###############################################################################
def HotStart(config, vars, helper, *args, **kwargs):
	seq = []
	dt = 0.3

	pushSeqCmd = helper.makePushSeqCmd(seq)

	pushSeqCmd(0, '', '', 'Running Hot Start sequence')

	# Defensive Systems
	pushSeqCmd(dt, 'CMS_MGR.mws_arm', 1)            # ECM switch ... OPR
	pushSeqCmd(dt, 'CMS_MGR.ircm_toggle', 1)        # IRCM switch ... OPR
	pushSeqCmd(dt, 'CMS_MGR.cms_profile_mode', 1) # 0 = OFF, 1 = MAN, 2 = SEMI, 3 = AUTO, 4 = BYP

	# Turn on and set up HUD for pilot and copilot.
	# Pilot HUD
	pushSeqCmd(dt, 'P_DISPLAYS.cmd_3029', 1) # Pilot HUD UNCG ... uncage velocity vector
	pushSeqCmd(dt, 'P_DISPLAYS.cmd_3029', 0) # release
	# Copilot HUD
	pushSeqCmd(dt, 'C_DISPLAYS.cmd_3029', 1) # Copilot HUD UNCG ... uncage velocity vector
	pushSeqCmd(dt, 'C_DISPLAYS.cmd_3029', 0) # release

	if vars['time'] == 'night':
		pushSeqCmd(dt, 'LIGHTING_PANELS.display_master', 0.5)
		pushSeqCmd(dt, 'LIGHTING_PANELS.copilot_display_master', 0.5)
		pushSeqCmd(dt, 'LIGHTING_PANELS.pilot_side_panel', 0.4)
		pushSeqCmd(dt, 'LIGHTING_PANELS.pilot_side_flood', 0.3)
		pushSeqCmd(dt, 'LIGHTING_PANELS.copilot_side_panel', 0.4)
		pushSeqCmd(dt, 'LIGHTING_PANELS.copilot_side_flood', 0.3)
		pushSeqCmd(dt, 'LIGHTING_PANELS.dome_light', 0.2)

	# Set GCAS to Tactical mode
	pushSeqCmd(dt, 'P_DISPLAYS.cmd_3008', 1) # GCAS/TAWS AND STALL
	pushSeqCmd(dt, 'P_DISPLAYS.cmd_3008', 0) # Release
	pushSeqCmd(dt, 'P_DISPLAYS.cmd_3011', 1) # NORMAL/TACTICAL (toggles)
	pushSeqCmd(dt, 'P_DISPLAYS.cmd_3011', 0) # Release
	pushSeqCmd(dt, 'P_DISPLAYS.cmd_3018', 1) # MAIN MENU
	pushSeqCmd(dt, 'P_DISPLAYS.cmd_3018', 0) # Release

	if vars['apu'] == 'turnOff':
		# APU shutdown
		pushSeqCmd(dt, 'ENGINE_APU_CTRL.ext_elec', 1) # External Power/APU switch ... OFF, 0 = EXT PWR, 1 = OFF, 2 = APU
		pushSeqCmd(dt, 'ENGINE_APU_CTRL.apu_selector', -1) # APU start switch ... RUN -> STOP

	return seq


###############################################################################
###############################################################################
def AirStart(config, vars, helper, *args, **kwargs):
	seq = []
	dt = 0.3

	pushSeqCmd = helper.makePushSeqCmd(seq)

	pushSeqCmd(0, '', '', 'Running Hot Start sequence')

	# Turn on and set up HUD for pilot and copilot.
	# Pilot HUD
	pushSeqCmd(dt, 'P_DISPLAYS.cmd_3029', 1) # Pilot HUD UNCG ... uncage velocity vector
	pushSeqCmd(dt, 'P_DISPLAYS.cmd_3029', 0) # release
	# Copilot HUD
	pushSeqCmd(dt, 'C_DISPLAYS.cmd_3029', 1) # Copilot HUD UNCG ... uncage velocity vector
	pushSeqCmd(dt, 'C_DISPLAYS.cmd_3029', 0) # release

	if vars['time'] == 'night':
		pushSeqCmd(dt, 'LIGHTING_PANELS.display_master', 0.5)
		pushSeqCmd(dt, 'LIGHTING_PANELS.copilot_display_master', 0.5)
		pushSeqCmd(dt, 'LIGHTING_PANELS.pilot_side_panel', 0.4)
		pushSeqCmd(dt, 'LIGHTING_PANELS.pilot_side_flood', 0.3)
		pushSeqCmd(dt, 'LIGHTING_PANELS.copilot_side_panel', 0.4)
		pushSeqCmd(dt, 'LIGHTING_PANELS.copilot_side_flood', 0.3)
		pushSeqCmd(dt, 'LIGHTING_PANELS.dome_light', 0.2)

	# Set GCAS to Tactical mode
	pushSeqCmd(dt, 'P_DISPLAYS.cmd_3008', 1) # GCAS/TAWS AND STALL
	pushSeqCmd(dt, 'P_DISPLAYS.cmd_3008', 0) # Release
	pushSeqCmd(dt, 'P_DISPLAYS.cmd_3011', 1) # NORMAL/TACTICAL (toggles)
	pushSeqCmd(dt, 'P_DISPLAYS.cmd_3011', 0) # Release
	pushSeqCmd(dt, 'P_DISPLAYS.cmd_3018', 1) # MAIN MENU
	pushSeqCmd(dt, 'P_DISPLAYS.cmd_3018', 0) # Release

	return seq


###############################################################################
###############################################################################
def Shutdown(config, vars, helper, *args, **kwargs):
	seq = []
	dt = 0.3

	pushSeqCmd = helper.makePushSeqCmd(seq)

	pushSeqCmd(0, '', '', 'Running Shutdown sequence')
	pushSeqCmd(dt, 'scriptSpeech', 'Set power levers to ground idle position.')

	# Radar Master ... OFF
	pushSeqCmd(dt, 'NAV_RADAR.master_mode', 0.0)  # RADAR MASTER switch ... OFF

	# Anti-Icing ... OFF
	pushSeqCmd(dt, 'ENGINE_APU_CTRL.ice_prop_1', 2) # Propeller 1 Ice Protection switch ... OFF, 0 = ON, 1 = AUTO, 2 = OFF
	pushSeqCmd(dt, 'ENGINE_APU_CTRL.ice_prop_2', 2) # Propeller 2 Ice Protection switch ... OFF, 0 = ON, 1 = AUTO, 2 = OFF
	pushSeqCmd(dt, 'ENGINE_APU_CTRL.ice_prop_3', 2) # Propeller 3 Ice Protection switch ... OFF, 0 = ON, 1 = AUTO, 2 = OFF
	pushSeqCmd(dt, 'ENGINE_APU_CTRL.ice_prop_4', 2) # Propeller 4 Ice Protection switch ... OFF, 0 = ON, 1 = AUTO, 2 = OFF
	pushSeqCmd(dt, 'ENGINE_APU_CTRL.ice_pitot_c', 1) # Pilot Pitot Heat ... OFF
	pushSeqCmd(dt, 'ENGINE_APU_CTRL.ice_pitot_cp', 1) # Copilot Pitot Heat ... OFF
	pushSeqCmd(dt, 'ENGINE_APU_CTRL.ice_nesa_ctr', 1) # Center NESA Heat ... OFF
	pushSeqCmd(dt, 'ENGINE_APU_CTRL.ice_nesa_side', 1) # Side NESA Heat ... OFF

	# Defensive Systems ... OFF
	pushSeqCmd(dt, 'CMS_MGR.arm_toggle_cms', 0) # CMS MASTER switch ... OFF
	pushSeqCmd(dt, 'CMS_MGR.mws_arm', 0) # ECM switch ... OFF
	pushSeqCmd(dt, 'CMS_MGR.ircm_toggle', 0) # IRCM switch ... OFF
	pushSeqCmd(dt, 'CMS_MGR.cms_profile_mode', 0) # 0 = OFF, 1 = MAN, 2 = SEMI, 3 = AUTO, 4 = BYP

	# Stow HUDs
	pushSeqCmd(dt, 'P_DISPLAYS.cmd_3025', 0) # Pilot HUD BRT knob ... push off
	pushSeqCmd(dt, 'P_DISPLAYS.cmd_3023', 0) # Pilot HUD latch ... stow (up)
	pushSeqCmd(dt, 'C_DISPLAYS.cmd_3025', 0) # Copilot HUD BRT knob ... push off
	pushSeqCmd(dt, 'C_DISPLAYS.cmd_3023', 0) # Copilot HUD latch ... stow (up)

	# Cage backup ADI
	pushSeqCmd(dt, 'MECH_INTERFACE.pitch_bar_cage', 1)  # Backup ADI cage knob ... pull (cage)
	pushSeqCmd(1, 'MECH_INTERFACE.pitch_bar_cage', 0) # release after 1 second

	# Hydraulics ... OFF
	pushSeqCmd(dt, 'HYDRAULICS.suction_boost_pump_boost', 0) # SUCTION BOOST PUMP switch ... OFF
	pushSeqCmd(dt, 'HYDRAULICS.suction_boost_pump_util', 0) # UTILITY SUCTION BOOST PUMP switch ... OFF
	pushSeqCmd(dt, 'HYDRAULICS.aux_pump', 0) # AUX PUMP switch ... OFF
	pushSeqCmd(dt, 'ENGINE_APU_CTRL.anti_skid', 0) # ANTI-SKID switch ... OFF

	# Stop engines (move start selects to STOP/GND to cut fuel)
	pushSeqCmd(dt, 'ENGINE_APU_CTRL.engine_1_start_select', -1) # Engine 1 start switch ... RUN -> STOP
	pushSeqCmd(dt, 'ENGINE_APU_CTRL.engine_2_start_select', -1) # Engine 2 start switch ... RUN -> STOP
	pushSeqCmd(dt, 'ENGINE_APU_CTRL.engine_3_start_select', -1) # Engine 3 start switch ... RUN ->	STOP
	pushSeqCmd(dt, 'ENGINE_APU_CTRL.engine_4_start_select', -1) # Engine 4 start switch ... RUN -> STOP

	# External Power/APU switch ... OFF
	pushSeqCmd(dt, 'ENGINE_APU_CTRL.ext_elec', 1) # EXT PWR/APU switch ... OFF

	# APU ... STOP
	pushSeqCmd(dt, 'ENGINE_APU_CTRL.apu_selector', -1) # APU start switch ... STOP

	# Exterior lights ... OFF
	pushSeqCmd(dt, 'LIGHTING_PANELS.ext_strobe_top', 1) # Top Strobe Light switch ... OFF
	pushSeqCmd(dt, 'LIGHTING_PANELS.ext_strobe_btm', 1) # Bottom Strobe Light switch ... OFF
	pushSeqCmd(dt, 'LIGHTING_PANELS.ext_nav', 1) # Navigation Light Mode switch ... OFF
	pushSeqCmd(dt, 'LIGHTING_PANELS.ext_master', 0) # Exterior Lighting Master switch ... NORM

	# Interior lights ... OFF
	pushSeqCmd(dt, 'LIGHTING_PANELS.display_master', 0.1)
	pushSeqCmd(dt, 'LIGHTING_PANELS.copilot_display_master', 0.1)
	pushSeqCmd(dt, 'LIGHTING_PANELS.pilot_side_panel', 0.1)
	pushSeqCmd(dt, 'LIGHTING_PANELS.pilot_side_flood', 0.1)
	pushSeqCmd(dt, 'LIGHTING_PANELS.copilot_side_panel', 0.1)
	pushSeqCmd(dt, 'LIGHTING_PANELS.copilot_side_flood', 0.1)
	pushSeqCmd(dt, 'LIGHTING_PANELS.dome_light', 0.1)

	# Generator switches 1-4 ... OFF (forward overhead panel)
	pushSeqCmd(dt, 'ENGINE_APU_CTRL.gen_1', 0)  # GEN 1 switch ... OFF
	pushSeqCmd(dt, 'ENGINE_APU_CTRL.gen_2', 0)  # GEN 2 switch ... OFF
	pushSeqCmd(dt, 'ENGINE_APU_CTRL.gen_3', 0)  # GEN 3 switch ... OFF
	pushSeqCmd(dt, 'ENGINE_APU_CTRL.gen_4', 0)  # GEN 4 switch ... OFF

	# Oil Cooler Flap switches ... FIXED (rear overhead panel)
	pushSeqCmd(dt, 'MECH_INTERFACE.oil_flap_1_fixed', 1)  # Engine 1 oil cooler flap ... FIXED
	pushSeqCmd(dt, 'MECH_INTERFACE.oil_flap_2_fixed', 1)  # Engine 2 oil cooler flap ... FIXED
	pushSeqCmd(dt, 'MECH_INTERFACE.oil_flap_3_fixed', 1)  # Engine 3 oil cooler flap ... FIXED
	pushSeqCmd(dt, 'MECH_INTERFACE.oil_flap_4_fixed', 1)  # Engine 4 oil cooler flap ... FIXED

	# Battery ... OFF
	pushSeqCmd(dt, 'ENGINE_APU_CTRL.battery', 0)  # BTRY switch ... OFF

	pushSeqCmd(dt, 'scriptSpeech', 'Shutdown complete.')

	return seq
