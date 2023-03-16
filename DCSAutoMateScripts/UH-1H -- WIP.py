# Return a Dictionary of script titles and their corresponding function names.  This is a list of scripts that users will be selecting from.  The module may have other utility functions that will not be run directly by the users.
def getScriptFunctions():
	return {
		'Cold Start': 'ColdStart',
		'Test': 'Test',
	}

# Returns 0-65535 scaled by multiple (0-1), eg for 50% call int16(0.5)
def int16(mult = 1):
	int16 = 65535
	return int(mult * int16)

# Some settings change depending on whether you're starting from the ground or from a carrier.
def Test(config):
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
		
	def getLastSeqTime():
		nonlocal seq
		return float(seq[len(seq) - 1]['time'])

	canopyCloseTime = 9
	apuStartTime = 15
	engineCrankTime = 7 # Seconds until engine is at 15% after setting crank switch.
	engineStartTime = 35 # Seconds until engine is fully started after moving throttle to idle.
	insAlignTime = 1 * 60 + 55 # 1m55s
	
	#pushSeqCmd(dt, '', '', "THROTTLE - SET TO START POSITION")
	pushSeqCmd(dt, 'THROTTLE', int16()) # 0 = Max throttle, 26375 = Idle stop, 46810 = Min throttle
	pushSeqCmd(dt, 'THROTTLE_STOP', 1)
	pushSeqCmd(dt, 'THROTTLE', 26375) # 0 = Max throttle, 26375 = Idle stop, 46810 = Min throttle
	#pushSeqCmd(dt, 'THROTTLE', 26375) # 0 = Max throttle, 26375 = Idle stop, 46810 = Min throttle
	return seq


# Some settings change depending on whether you're starting from the ground or from a carrier.
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
		
	def getLastSeqTime():
		nonlocal seq
		return float(seq[len(seq) - 1]['time'])

	canopyCloseTime = 9
	apuStartTime = 15
	engineCrankTime = 7 # Seconds until engine is at 15% after setting crank switch.
	engineStartTime = 35 # Seconds until engine is fully started after moving throttle to idle.
	insAlignTime = 1 * 60 + 55 # 1m55s
	
	pushSeqCmd(0, '', '', "Running Cold Start sequence")
	#pushSeqCmd(dt, 'scriptSpeech', "Warning, uses non standard key bindings.")

	# Set intercom mode knob to INT, allows rearming.
	#pushSeqCmd(dt, '', '', "INTERCOM MODE KNOB - INT")
	pushSeqCmd(dt, 'INT_MODE', 1) # 0 = PVT, 1 = INT, 2 = 1, 3 = 2, 4 = 3, 5 = 4
	
	#pushSeqCmd(dt, '', '', "DOORS - CLOSE")
	pushSeqCmd(dt, 'DOOR_L-PTR', 1)
	pushSeqCmd(dt, 'DOOR_R-PTR', 1)
	
	#pushSeqCmd(dt, '', '', "AC VOLTMETER - AC PHASE")
	pushSeqCmd(dt, 'AC_VM_SRC', 1) # 0 = AB, 1 = AC PHASE, 2 = BC
	
	#pushSeqCmd(dt, '', '', "INVERTER - OFF")
	pushSeqCmd(dt, 'INVERTER_SW', 1) # 0 = MAIN ON, 1 = OFF, 2 = SPARE ON
	
	#pushSeqCmd(dt, '', '', "MAIN GENERATOR - ON")
	pushSeqCmd(dt, 'MAIN_GEN_COVER', 1) # Cover open (it starts open on cold spawn)
	pushSeqCmd(dt, 'MAIN_GEN_SW', 0) # Switch
	pushSeqCmd(dt, 'MAIN_GEN_COVER', 0) # Cover close
	
	#pushSeqCmd(dt, '', '', "DC VOLTMETER - ESS BUS")
	pushSeqCmd(dt, 'DC_VM_SRC', 3) # 0 = BAT, 1 = MAIN GEN, 2 = STBY GEN, 3 = ESS BUS, 4 = NON-ESS BUS
	
	#pushSeqCmd(dt, '', '', "STARTER-GENERATOR - START")
	pushSeqCmd(dt, 'STARTER_GEN_SW', 1) # 0 = STBY GEN, 1 = START
	
	#pushSeqCmd(dt, '', '', "BATTERY - ON")
	pushSeqCmd(dt, 'BAT_SW', 0) # 0 = ON, 1 = OFF
	
	#pushSeqCmd(dt, '', '', "LOW RPM WARNING AUDIO - OFF")
	pushSeqCmd(dt, 'LOW_RPM_AUDIO', 0)
	
	#pushSeqCmd(dt, '', '', "GOVERNOR - AUTO")
	pushSeqCmd(dt, 'EMER_GOV_SW', 1)
	
	#pushSeqCmd(dt, '', '', "DE-ICE - OFF")
	pushSeqCmd(dt, 'ENG_DEICE', 0)
	
	#pushSeqCmd(dt, '', '', "MAIN FUEL - ON")
	pushSeqCmd(dt, 'MAIN_FUEL_SW', 1)
	
	#pushSeqCmd(dt, '', '', "CAUTION PANEL LIGHTS TEST")
	pushSeqCmd(dt, 'CLP_RESET_TEST_SW', 0)
	pushSeqCmd(dt, 'CLP_RESET_TEST_SW', 1)
	
	#pushSeqCmd(dt, '', '', "HYDRAULIC CONTROL - ON")
	pushSeqCmd(dt, 'HYD_CONT_SW', 1)
	
	#pushSeqCmd(dt, '', '', "FORCE TRIM - ON")
	pushSeqCmd(dt, 'FORCE_TRIM_SW', 1)
	
	#pushSeqCmd(dt, '', '', "CHIP DETECTOR - BOTH")
	pushSeqCmd(dt, 'CHIP_DET_SW', 1)

	#pushSeqCmd(dt, '', '', "THROTTLE - SET TO START POSITION")
	pushSeqCmd(dt, 'THROTTLE_STOP', 1)
	pushSeqCmd(dt, 'THROTTLE', int16()) # 0 = Max throttle, 26375 = Idle stop, 46810 = Min throttle
	pushSeqCmd(dt, 'THROTTLE', 26375) # 0 = Max throttle, 26375 = Idle stop, 46810 = Min throttle
	
	#pushSeqCmd(dt, '', '', "START ENGINE (40s)")
	pushSeqCmd(dt, 'scriptKeyboard', '{VK_HOME} down') # Press
	pushSeqCmd(40, '', '', "ENGINE STARTED, RELEASING START BUTTON")
	pushSeqCmd(dt, 'scriptKeyboard', '{VK_HOME} up') # Press
	return seq
	"""
	#pushSeqCmd(dt, '', '', "INVERTER - MAIN ON")
	pushSeqCmd(dt, 'INVERTER_SW', 0) # 0 = MAIN ON, 1 = OFF, 2 = SPARE ON
	
	#pushSeqCmd(dt, '', '', "STARTER-GENERATOR - STBY GEN")
	pushSeqCmd(dt, 'STARTER_GEN_SW', 0) # 0 = STBY GEN, 1 = START
	
	#pushSeqCmd(dt, '', '', "DC VOLTMETER - MAIN GEN")
	pushSeqCmd(dt, 'DC_VM_SRC', 1) # 0 = BAT, 1 = MAIN GEN, 2 = STBY GEN, 3 = ESS BUS, 4 = NON-ESS BUS

	#pushSeqCmd(dt, '', '', "THROTTLE - SET TO FULL")
	#for i = 0.0, 20.0, 0.1 do
	#	pushSeqCmd(0.05, ENGINE_INTERFACE, Button_25, value = 0.5)
	#end
	pushSeqCmd(dt, 'THROTTLE', 0)
	#pushSeqCmd(dt, '', '', "WAIT FOR ROTOR TO SPOOL UP (15s)")
	pushSeqCmd(15, '', '', "ROTOR SPOOLED UP")
	
	#pushSeqCmd(dt, '', '', "LOW RPM WARNING AUDIO - ON")
	pushSeqCmd(dt, 'LOW_RPM_AUDIO', 1)
	
	#pushSeqCmd(dt, '', '', "MASTER CAUTION - RESET")
	pushSeqCmd(dt, 'CLP_RESET_TEST_SW', 2)
	pushSeqCmd(dt, 'CLP_RESET_TEST_SW', 1)
	
	#pushSeqCmd(dt, '', '', "IFF - NORM")
	pushSeqCmd(dt, 'IFF_MASTER', 4)
	
	#pushSeqCmd(dt, '', '', "RADAR ALTIMETER ON")
	pushSeqCmd(dt, 'RADAR_ALT_PWR', 1)
	#pushSeqCmd(dt, '', '', "RADAR ALTIMETER LOW ALT")
	#pushSeqCmd(dt, RADAR_ALTIMETER, Button_2, value = 0.6)
	#pushSeqCmd(dt, RADAR_ALTIMETER, Button_2, 1)
	#pushSeqCmd(dt, RADAR_ALTIMETER, Button_2, value = 0.8)
	
	#pushSeqCmd(dt, '', '', "RADAR ALTIMETER HIGH ALT")
	#pushSeqCmd(dt, RADAR_ALTIMETER, Button_3, 1)
	#pushSeqCmd(dt, RADAR_ALTIMETER, Button_3, 1)
	#pushSeqCmd(dt, RADAR_ALTIMETER, Button_3, 1)
	#pushSeqCmd(dt, RADAR_ALTIMETER, Button_3, 1)
	#pushSeqCmd(dt, RADAR_ALTIMETER, Button_3, 1)
	#pushSeqCmd(dt, RADAR_ALTIMETER, Button_3, value = 0.5)

	#pushSeqCmd(dt, '', '', "ARC-51BX UHF RADIO (COM1) - T/R")
	pushSeqCmd(dt, 'UHF_FUNCTION', 1)
	
	#pushSeqCmd(dt, '', '', "ARC-134 VHF AM RADIO (COM2) - ON")
	pushSeqCmd(dt, 'VHFCOMM_PWR', 1)
	
	#pushSeqCmd(dt, '', '', "ARC-131 VHF FM RADIO (COM3) - T/R")
	pushSeqCmd(dt, 'VHFFM_MODE', 1)
	
	#pushSeqCmd(dt, '', '', "MASTER ARM - ON")
	pushSeqCmd(dt, 'MASTER_ARM_SW', 2)
	
	#pushSeqCmd(dt, '', '', "ROCKET PAIRS - 1")
	pushSeqCmd(dt, 'ROCKET_PAIR', 1)
	
	#pushSeqCmd(dt, '', '', "FLARE DISPENSER - ARM")
	pushSeqCmd(dt, 'CM_ARM_SW', 1)
	
	#pushSeqCmd(dt, '', '', "FLARE DISPENSER COUNT - 30")
	for i in range(30):
		pushSeqCmd(dt, 'CM_FLARECNT', 'INC')
	
	#pushSeqCmd(dt, '', '', "HAVOC'S QUICK AUTOSTART IS COMPLETE")
	#pushSeqCmd(dt, '', '', "Manual steps remaining:")
	#pushSeqCmd(dt, '', '', "Syncronize HSI compass (backup compass shows current heading)")
	#pushSeqCmd(dt, '', '', "Radios ... As needed")
	# TODO:
	# Weapons ARM
	# Flares ARM
	# Reminder to sync compass

	return seq
	
end
doStartSequence()


##################################################
##################################################
# Stop sequence
local function doStopSequence()
	push_stop_command(0, {message = _("HAVOC'S QUICK AUTOSTOP IS RUNNING") # Message text and timeout will be modified by insertTimeRemaining function below.

	push_stop_command(dt, {message = _("ENGINE START BUTTON - OFF")
	push_stop_command(dt, ENGINE_INTERFACE, Button_12, 0)

	push_stop_command(dt, {message = _("THROTTLE - SET TO OFF")
	push_stop_command(dt, ENGINE_INTERFACE, Button_27, 1) # Throttle stop switch??
	for i = 0.0, 20.0, 0.2 do
		push_stop_command(0.1, ENGINE_INTERFACE, Button_25, value = -0.5)
	end
	push_stop_command(dt, ENGINE_INTERFACE, Button_27, 0) # Throttle stop switch??
	
	push_stop_command(dt, {message = _("LOW RPM WARNING AUDIO - OFF")
	push_stop_command(dt, ENGINE_INTERFACE, Button_21, 0)
	
	push_stop_command(dt, {message = _("Waiting for rotor to spin down (" .. math.floor(rotor_spin_down / 60) .."m".. rotor_spin_down % 60 .. "s) ..."), message_timeout = rotor_spin_down)
	local rotor_spin_down_timer = t_start # Start a timer for the alignment process at the current t_start value.

	push_stop_command(dt, {message = _("FORCE TRIM - OFF")
	push_stop_command(dt, HYDRO_SYS_INTERFACE, Button_4, 0)
	
	push_stop_command(dt, {message = _("STARTER-GENERATOR - START")
	push_stop_command(dt, ELEC_INTERFACE, Button_3, 1)
	
	push_stop_command(dt, {message = _("MAIN FUEL - OFF")
	push_stop_command(dt, FUELSYS_INTERFACE, Button_1, 0)
	push_stop_command(dt, ENGINE_INTERFACE, Button_21, 0)
	
	push_stop_command(dt, {message = _("AC VOLTMETER - AB")
	push_stop_command(dt, ELEC_INTERFACE, Button_7, 0)
	
	push_stop_command(dt, {message = _("DC VOLTMETER - MAIN GEN")
	push_stop_command(dt, ELEC_INTERFACE, Button_4, value = 0.3)
	
	push_stop_command(dt,{message = _("INVERTER - OFF")
	push_stop_command(dt, ELEC_INTERFACE, Button_8, 0)
	
	push_stop_command(dt, {message = _("MAIN GENERATOR - OFF")
	push_stop_command(dt, ELEC_INTERFACE, Button_19, 1) # Cover open
	push_stop_command(dt, ELEC_INTERFACE, Button_2, 0) # Switch
	push_stop_command(dt, ELEC_INTERFACE, Button_19, 0) # Cover close
	
	push_stop_command(dt, {message = _("PITOT HEATER - OFF")
	push_stop_command(dt, ELEC_INTERFACE, Button_16, 0)
	
	push_stop_command(dt, {message = _("BATTERY - OFF")
	push_stop_command(dt, ELEC_INTERFACE, Button_1, 1)
	
	push_stop_command(dt, {message = _("HYDRO CONTROL - OFF")
	push_stop_command(dt, HYDRO_SYS_INTERFACE, Button_3, 0)
			
	push_stop_command(dt, {message = _("ARC-51BX UHF RADIO (COM1) - OFF")
	push_stop_command(dt, UHF_ARC_51, Button_6, 0)
	
	push_stop_command(dt, {message = _("ARC-134 VHF AM RADIO (COM2) - OFF")
	push_stop_command(dt, VHF_ARC_134, Button_4, 0)
	
	push_stop_command(dt, {message = _("ARC-131 VHF FM RADIO (COM3) - OFF")
	push_stop_command(dt, VHF_ARC_131, Button_7, 0)
	
	push_stop_command(dt, {message = _("MASTER ARM - OFF")
	push_stop_command(dt, WEAPON_SYS, Button_8, value = -1.0)
	
	push_stop_command(dt, {message = _("ROCKET PAIRS - 0")
	push_stop_command(dt, WEAPON_SYS, Button_11, 0)
	
	push_stop_command(dt, {message = _("FLARE DISPENSER - SAFE")
	push_stop_command(dt, XM_130, Button_5, 0)
	
	push_stop_command(dt, {message = _("FLARE DISPENSER COUNT - 0")
	for i = 1, 30, 1 do
		push_stop_command(0.01, XM_130, Button_3, value = 0.1)
	end
	
	# Wait until the rotor has stopped (total process time minus the difference between now and when the process started).
	push_stop_command(rotor_spin_down - (t_start - rotor_spin_down_timer), {message = _("Rotor has stopped")
	
	push_stop_command(dt, {message = _("LOW RPM WARNING AUDIO - ON")
	push_stop_command(dt, ENGINE_INTERFACE, Button_21, 1)

	push_stop_command(dt, {message = _("OPENING COCKPIT DOORS")
	push_stop_command(dt, CPT_MECH, Button_7, 1)

	push_stop_command(dt, {message = _("HAVOC'S QUICK AUTOSTOP IS COMPLETE"), message_timeout = 60.0)
end
doStopSequence()
"""