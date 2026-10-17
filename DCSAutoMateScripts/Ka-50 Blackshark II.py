# Return a Dictionary of script data.  The 'scripts' key is a list of scripts that users will be selecting from.  Each script has an associated 'function', which is the name of the function in this file that will be called to generate the command sequence, and a dictionary of 'vars' that the user will be prompted to choose from before running the script, and will be passed into the sequence generating function.
def getScriptData():
	return {
		'moduleName': 'Ka-50',
		'scripts': [
			{
				'name': 'Cold Start',
				'function': 'ColdStart',
				'vars': {},
			},
			{
				'name': 'Hot Start',
				'function': 'HotStart',
				'vars': {},
			},
			#{
			#	'name': 'Test',
			#	'function': 'Test',
			#	'vars': {},
			#},
		],
	}

def getInfo():
	return ''

def Test(config, vars, helper, *args, **kwargs):
	seq = []
	dt = 0.3

	pushSeqCmd = helper.makePushSeqCmd(seq)

	# Cover helper.  Most Ka-50 cover commands behave as toggles: sending any value just flips the cover, regardless of the value sent.  (Only ADI.TEST-COVER-IKP-PTR, LASERRANGER.LD-LDP-COVER-PTR, and CPT_MECH.AVAR-GEAR-COVER-PTR use absolute values, the rest are toggles.)  This helper makes a cover behave like an absolute set.  We read the cover's current arg value, and toggle it once if needed.
	def coverSet(name, targetValue):
		fullName = f'Ka-50/{name}'
		pushSeqCmd(0, 'scriptLoopUntilStart', control=fullName, condition='=', value=targetValue, maxIterations=1)
		pushSeqCmd(dt, name, 1) # Toggle (value ignored by toggle covers).
		pushSeqCmd(0, 'scriptLoopUntilEnd')

	# Test code here...
	pushSeqCmd(0, '', '', "Running Test sequence")

	#print(seq)
	return seq


def ColdStart(config, vars, helper, *args, **kwargs):
	seq = []
	dt = 0.3

	pushSeqCmd = helper.makePushSeqCmd(seq)

	# Cover helper.  Most Ka-50 cover commands behave as toggles: sending any value just flips the cover, regardless of the value sent.  (Only ADI.TEST-COVER-IKP-PTR, LASERRANGER.LD-LDP-COVER-PTR, and CPT_MECH.AVAR-GEAR-COVER-PTR use absolute values, the rest are toggles.)  This helper makes a cover behave like an absolute set.  We read the cover's current arg value, and toggle it once if needed.
	def coverSet(name, targetValue):
		fullName = f'Ka-50/{name}'
		pushSeqCmd(0, 'scriptLoopUntilStart', control=fullName, condition='=', value=targetValue, maxIterations=1)
		pushSeqCmd(dt, name, 1) # Toggle (value ignored by toggle covers).
		pushSeqCmd(0, 'scriptLoopUntilEnd')

	inuAlignTime = 3 * 60  # 3m00s

	# Start sequence
	pushSeqCmd(0, '', '', "Running Cold Start sequence.")
	pushSeqCmd(dt, '', '', 'Set collective full down.')
	pushSeqCmd(dt, 'scriptSpeech', 'Set collective full down.')

	# SPU-9 radio selector knob - Ground Crew (allows rearming)
	pushSeqCmd(dt, 'SPU_9.RADIO-RATE-PTR', 3)


	# Exterior lights
	# Anticollision beacon - Off # Right wall, lower middle
	pushSeqCmd(dt, 'NAVLIGHT_SYSTEM.FLASHER-PTR', 0)
	# Blade tip lights - Off # Right wall, lower rear
	pushSeqCmd(dt, 'NAVLIGHT_SYSTEM.CONTUR-LIGHT-PTR', 0)
	# Formation lights - Off # Right wall, lower rear
	pushSeqCmd(dt, 'NAVLIGHT_SYSTEM.FORMATION-PTR', 0)
	# Nav lights - On # Front upper canopy frame, left side
	pushSeqCmd(dt, 'NAVLIGHT_SYSTEM.ANO-PTR', 0)

	# Cockpit door - Close
	pushSeqCmd(dt, 'scriptSimCommand', 'iCommandPlaneFonar') # Open/close cockpit door (RCtrl+C)

	# Voice message system (Betty) - On
	pushSeqCmd(dt, 'VMS.SPEECH-INFO-AVAR-PTR', 1)

	# Battery 1 - On
	coverSet('ELEC_INTERFACE.ENERG-COVER-AKK1-PTR', 1) # Cover open
	pushSeqCmd(dt, 'ELEC_INTERFACE.ENERG-AKK1-PTR', 1) # Switch
	coverSet('ELEC_INTERFACE.ENERG-COVER-AKK1-PTR', 0) # Cover close
	# Battery 2 - On
	coverSet('ELEC_INTERFACE.ENERG-COVER-AKK2-PTR', 1) # Cover open
	pushSeqCmd(dt, 'ELEC_INTERFACE.ENERG-AKK2-PTR', 1) # Switch
	coverSet('ELEC_INTERFACE.ENERG-COVER-AKK2-PTR', 0) # Cover close

	# ABRIS power, turn on as soon as possible so it finishes booting up by the time we're done.
	# ABRIS power - On
	pushSeqCmd(dt, 'ABRIS.ABRIS-POWER_PTR', 1)

	# Begin "accelerated" alignment (3 mins), see manual p.330
	# K-041 targeting-navigation system power - On # Left console in front of collective
	pushSeqCmd(dt, 'K041.K-041-PTR', 1)
	# PVI NAV master mode knob - OPER
	pushSeqCmd(dt, 'PVI.PVI-SWITCH-PTR', 3) # 0 = OFF, 1 = CHECK, 2 = ENT, 3 = OPER, 4 = STM, 5 = K-1, 6 = K-2
	# PVI NAV datalink power - On
	pushSeqCmd(dt, 'DATALINK.PVI_VCU_PTR', 1)
	# INU heat - On # Right rear wall
	pushSeqCmd(dt, 'C061K.HEAT_IKV-PTR', 1)
	# INU power - On # Right rear wall
	pushSeqCmd(dt, 'C061K.IKV-PTR', 1)
	pushSeqCmd(dt, 'scriptTimerStart', name='alignTimer', duration=inuAlignTime)
	# INU accelerated alignment in process (3m)
	# SAI power - On # Right wall
	pushSeqCmd(dt, 'STBY_ADI.RES-AG-PTR', 1)


	# Right wall radio switches:
	# Fuel gauge power - On
	pushSeqCmd(dt, 'FUELSYS_INTERFACE.FUEL-METER-PTR', 1)
	# Intercom (SPU-9) power - On
	pushSeqCmd(dt, 'SPU_9.COMM-PWR-AVSK-PTR', 1)
	# VHF-1 (R-828) power - On
	pushSeqCmd(dt, 'R_828.COMM-PWR-UKV-1-PTR', 1)
	# VHF-2 (R-800) power - On
	pushSeqCmd(dt, 'R_800.COMM-PWR-UKV-2-PTR', 1)
	# Datalink radio (TLK) power - On
	pushSeqCmd(dt, 'DATALINK.COMM-PWR-TLK-PTR', 1)
	# VHF-TLK power - On
	pushSeqCmd(dt, 'DATALINK.COMM-PWR-UKV-TLK-PTR', 1)
	# NOTE: SA-TLF switch has no function in game.

	# Various avionics systems
	# K-041 targeting-navigation system power - On # Left console in front of collective
	pushSeqCmd(dt, 'K041.PNK-PTR', 1)
	# EKRAN HYD TRANS PWR switch - AUTO BASE # Right rear wall, black guarded switch
	pushSeqCmd(dt, 'CPT_MECH.P-CONTR-VMG-HYDRO-PTR', 0) # Switch
	coverSet('CPT_MECH.P-CONTR-VMG-HYDRO-COVER-PTR', 0) # Cover close (starts open on cold start)

	# UV-26 countermeasures dispenser (CMD) power - On # Right rear wall, black guarded switch
	coverSet('UV_26.UV26-POWER-COVER-PTR', 1) # Cover open
	pushSeqCmd(dt, 'UV_26.UV26-POWER-PTR', 1) # Switch
	coverSet('UV_26.UV26-POWER-COVER-PTR', 0) # Cover close
	# L-140 laser warning (LWS) power - On # Right rear wall
	pushSeqCmd(dt, 'LASER_WARNING_SYSTEM.L140-SWITCH', 1)
	# Fire extinguishers - On # Right wall upper row, black guarded switch
	coverSet('FIRE_EXTING_INTERFACE.FIREEXT-COVER-PTR', 1) # Cover open
	pushSeqCmd(dt, 'FIRE_EXTING_INTERFACE.FIREEXT-PTR', 2) # Switch
	coverSet('FIRE_EXTING_INTERFACE.FIREEXT-COVER-PTR', 0) # Cover close

	# APU fuel shut-off valve - On
	coverSet('FUELSYS_INTERFACE.PAV-CRANE-COVER-VSU-PTR', 1) # Cover open
	pushSeqCmd(dt, 'FUELSYS_INTERFACE.PAV-CRANE-VSU-PTR', 1) # Switch
	# Forward fuel tank pump - On
	pushSeqCmd(dt, 'FUELSYS_INTERFACE.FUEL-PUMP-FRONT-PTR', 1)
	# Aft fuel tank pump - On
	pushSeqCmd(dt, 'FUELSYS_INTERFACE.FUEL-PUMP-BACK-PTR', 1)

	# Master Caution Light - Reset
	pushSeqCmd(dt, 'SYST_CONTROLLER.CSO-PTR', 1) # Press
	pushSeqCmd(dt, 'SYST_CONTROLLER.CSO-PTR', 0) # Release

	# APU start
	# Engine selector switch - APU
	pushSeqCmd(dt, 'ENGINE_INTERFACE.START-ENGINE-SELECTOR-PTR', 0) # 0 = APU, 1 = LH ENG, 2 = RH ENG, 3 = TURBO GEAR
	# APU - Starting (20s)
	pushSeqCmd(dt, 'ENGINE_INTERFACE.START-PANEL-START-PTR', 1) # Press
	pushSeqCmd(dt, 'ENGINE_INTERFACE.START-PANEL-START-PTR', 0) # Release
	pushSeqCmd(20, '', '', "APU started")

	# Prepare for engine start
	# Rotor brake - Off
	pushSeqCmd(dt, 'ENGINE_INTERFACE.BRAKE-ROTOR-LOW-PTR01', 0)
	# Left engine fuel shut-off switch - On
	coverSet('FUELSYS_INTERFACE.PAV-CRANE-COVER-ENGINE-LEFT-PTR', 1) # Cover open
	pushSeqCmd(dt, 'FUELSYS_INTERFACE.PAV-CRANE-ENGINE-LEFT-PTR', 1) # Switch
	coverSet('FUELSYS_INTERFACE.PAV-CRANE-COVER-ENGINE-LEFT-PTR', 0) # Cover close
	# Right engine fuel shut-off switch - On
	coverSet('FUELSYS_INTERFACE.PAV-CRANE-COVER-ENGINE-RIGHT-PTR', 1) # Cover open
	pushSeqCmd(dt, 'FUELSYS_INTERFACE.PAV-CRANE-ENGINE-RIGHT-PTR', 1) # Switch
	coverSet('FUELSYS_INTERFACE.PAV-CRANE-COVER-ENGINE-RIGHT-PTR', 0) # Cover close
	# Left engine EEG - On
	coverSet('ENGINE_INTERFACE.ERD-LEFT-COVER-PTR', 1) # Cover open
	pushSeqCmd(dt, 'ENGINE_INTERFACE.ERD-LEFT-PTR', 1) # Switch
	coverSet('ENGINE_INTERFACE.ERD-LEFT-COVER-PTR', 0) # Cover close
	# Right engine EEG - On
	coverSet('ENGINE_INTERFACE.ERD-RIGHT-COVER-PTR', 1) # Cover open
	pushSeqCmd(dt, 'ENGINE_INTERFACE.ERD-RIGHT-PTR', 1) # Switch
	coverSet('ENGINE_INTERFACE.ERD-RIGHT-COVER-PTR', 0) # Cover close

	# Left engine start
	# Engine selector switch - Left engine
	pushSeqCmd(dt, 'ENGINE_INTERFACE.START-ENGINE-SELECTOR-PTR', 1) # 0 = APU, 1 = LH ENG, 2 = RH ENG, 3 = TURBO GEAR
	# Left engine - Starting (50s)
	pushSeqCmd(dt, 'ENGINE_INTERFACE.START-PANEL-START-PTR', 1) # Press
	pushSeqCmd(dt, 'ENGINE_INTERFACE.START-PANEL-START-PTR', 0) # Release
	pushSeqCmd(15, '', '', "Left engine at 20% RPM: cut-off valve - Open")
	pushSeqCmd(dt, 'ENGINE_INTERFACE.EMERGENCY-BRAKE ENGINE-LEFT-PTR', 1)
	pushSeqCmd(45, '', '', "Left engine - Started")

	# Right engine start
	# Engine selector switch - Right engine
	pushSeqCmd(dt, 'ENGINE_INTERFACE.START-ENGINE-SELECTOR-PTR', 2) # 0 = APU, 1 = LH ENG, 2 = RH ENG, 3 = TURBO GEAR
	# Right engine - Starting (50s)
	pushSeqCmd(dt, 'ENGINE_INTERFACE.START-PANEL-START-PTR', 1) # Press
	pushSeqCmd(dt, 'ENGINE_INTERFACE.START-PANEL-START-PTR', 0) # Release
	pushSeqCmd(15, '', '', "Right engine at 20% RPM: cut-off valve - Open")
	pushSeqCmd(dt, 'ENGINE_INTERFACE.EMERGENCY-BRAKE ENGINE-RIGHT-PTR', 1)
	pushSeqCmd(45, '', '', "Right engine - Started")

	# APU - Stop
	pushSeqCmd(dt, 'ENGINE_INTERFACE.START-PANEL-STOP-START-PTR01', 1)
	pushSeqCmd(dt, 'ENGINE_INTERFACE.START-PANEL-STOP-START-PTR01', 0)
	# APU fuel shut-off valve - Off
	pushSeqCmd(dt, 'FUELSYS_INTERFACE.PAV-CRANE-VSU-PTR', 0) # Switch
	coverSet('FUELSYS_INTERFACE.PAV-CRANE-COVER-VSU-PTR', 0) # Cover close

	# Left and right throttles - Auto (10s)
	pushSeqCmd(dt, 'scriptSimCommand', 'iCommandPlaneAUTIncreaseRegime') # Throttles up one notch (PgUp)
	pushSeqCmd(dt, 'scriptSimCommand', 'iCommandPlaneAUTIncreaseRegime') # Needs two notches to get to Auto.
	pushSeqCmd(10, '', '', "Engines - spooled up")

	# Left AC generator - On
	pushSeqCmd(dt, 'ELEC_INTERFACE.GEN-LEFT-PTR', 1)
	# Right AC generator - On
	pushSeqCmd(dt, 'ELEC_INTERFACE.GEN-RIGHT-PTR', 1)
	# Engine anti-ice/dust protection - As needed
	pushSeqCmd(dt, 'scriptSpeech', 'Set anti dust as needed')

	# Heading source selector (needed after DCS v.2.8)
	# Gyro/Mag/Manual heading switch - GYRO (middle)
	pushSeqCmd(dt, 'NAV_INTERFACE.GYRO-MAG-MAN-HEADING-PTR', 1) # 0 = MH, 1 = GYRO, 2 = MAN

	# PVI and datalink, right console forward
	# Datalink master mode knob - WINGM
	pushSeqCmd(dt, 'DATALINK.DTLK-MASTER-MODES-PTR', 2) # 0 = OFF, 1 = REC, 2 = WINGM, 3 = COM

	# Ejection system - On
	coverSet('EJECT_SYS_INTERFACE.RIGHT-COVER-EMERG-VACATION-PTR', 1) # Cover open
	pushSeqCmd(dt, 'EJECT_SYS_INTERFACE.RIGHT-EMERG-SW1-PTR', 0) # Switch 1, Inversed: 0 = ON, 1 = DISABLED
	pushSeqCmd(dt, 'EJECT_SYS_INTERFACE.RIGHT-EMERG-SW2-PTR', 0) # Switch 2, Inversed: 0 = ON, 1 = DISABLED
	pushSeqCmd(dt, 'EJECT_SYS_INTERFACE.RIGHT-EMERG-SW3-PTR', 0) # Switch 3, Inversed: 0 = ON, 1 = DISABLED
	coverSet('EJECT_SYS_INTERFACE.RIGHT-COVER-EMERG-VACATION-PTR', 0) # Cover close

	# Weapons control system power - On # Right wall lower row, next to ejection system switches
	coverSet('WEAP_INTERFACE.SUO-COVER-PTR', 1) # Cover open
	pushSeqCmd(dt, 'WEAP_INTERFACE.SUO-PTR', 1) # Switch, 0 = DISABLED, 1 = ON
	coverSet('WEAP_INTERFACE.SUO-COVER-PTR', 0) # Cover close

	# IFF power - On
	coverSet('IFF.COVER-SRO-PTR', 1) # Cover open
	pushSeqCmd(dt, 'IFF.SRO-PTR', 1) # Switch
	coverSet('IFF.COVER-SRO-PTR', 0) # Cover close
	# SAI - Uncage and center
	pushSeqCmd(dt, 'STBY_ADI.RES-AGD-PTR_arg597', -0.03)
	pushSeqCmd(dt, 'STBY_ADI.RES-AGD-PTR_arg597', -0.03)
	pushSeqCmd(dt, 'STBY_ADI.RES-AGD-PTR_arg597', -0.03)
	pushSeqCmd(dt, 'STBY_ADI.RES-AGD-PTR_arg597', -0.03)
	pushSeqCmd(dt, 'STBY_ADI.RES-AGD-PTR_arg597', -0.03)
	pushSeqCmd(dt, 'STBY_ADI.RES-AGD-PTR_arg597', -0.03)
	pushSeqCmd(dt, 'STBY_ADI.RES-AGD-PTR_arg597', -0.03)
	pushSeqCmd(dt, 'STBY_ADI.RES-AGD-PTR_arg597', -0.03)

	# Default startup done, doing post-startup tasks.
	# Laser rangefinder - Arm
	pushSeqCmd(dt, 'LASERRANGER.PVR-IZL-PTR', 1)
	# Master Arm - Arm
	pushSeqCmd(dt, 'WEAP_INTERFACE.MASTER-ARM-PTR', 1)
	# Man/Auto weapon - Man
	pushSeqCmd(dt, 'WEAP_INTERFACE.PUI800-AUTO-PTR', 1)

	# UV-26 countermeasures dispenser
	# UV-26 Dispenser - Both sides
	pushSeqCmd(dt, 'UV_26.UV26-BOARD-PTR', 1) # Switch to middle
	# UV-26 Program - Reset (to default program 110)
	pushSeqCmd(dt, 'UV_26.UV26-CANCELPRG-PTR', 1) # Press
	pushSeqCmd(dt, 'UV_26.UV26-CANCELPRG-PTR', 0) # Release
	# UV-26 Num of sequences - 4
	pushSeqCmd(dt, 'UV_26.UV26-SERIES-PTR', 1) # Press
	pushSeqCmd(dt, 'UV_26.UV26-SERIES-PTR', 0) # Release
	pushSeqCmd(dt, 'UV_26.UV26-SERIES-PTR', 1) # Press
	pushSeqCmd(dt, 'UV_26.UV26-SERIES-PTR', 0) # Release
	pushSeqCmd(dt, 'UV_26.UV26-SERIES-PTR', 1) # Press
	pushSeqCmd(dt, 'UV_26.UV26-SERIES-PTR', 0) # Release
	# UV-26 Dispense interval - 1 SEC
	pushSeqCmd(dt, 'UV_26.UV26-INTERVAL-PTR', 1) # Press
	pushSeqCmd(dt, 'UV_26.UV26-INTERVAL-PTR', 0) # Release

	# Set up ABRIS
	# ABRIS - Geo grid off, UTM grid (10 km grid) on
	pushSeqCmd(dt, 'ABRIS.PTR_BTN-ABRIS-01', 1) # OPTION
	pushSeqCmd(dt, 'ABRIS.PTR_BTN-ABRIS-01', 0) # release
	pushSeqCmd(dt, 'ABRIS.PTR_BTN-ABRIS-01', 1) # SETUP
	pushSeqCmd(dt, 'ABRIS.PTR_BTN-ABRIS-01', 0) # release
	pushSeqCmd(dt, 'ABRIS.PTR_BTN-ABRIS-03', 1) # Up arrow to wrap around
	pushSeqCmd(dt, 'ABRIS.PTR_BTN-ABRIS-03', 0) # release
	pushSeqCmd(dt, 'ABRIS.PTR_BTN-ABRIS-01', 1) # CHART
	pushSeqCmd(dt, 'ABRIS.PTR_BTN-ABRIS-01', 0) # release
	for i in range(24):
		pushSeqCmd(dt, 'ABRIS.PTR_BTN-ABRIS-02', 1) # Down arrow
		pushSeqCmd(dt, 'ABRIS.PTR_BTN-ABRIS-02', 0) # release
	pushSeqCmd(dt, 'ABRIS.PTR_BTN-ABRIS-04', 1) # CHANGE
	pushSeqCmd(dt, 'ABRIS.PTR_BTN-ABRIS-04', 0) # release
	pushSeqCmd(dt, 'ABRIS.PTR_BTN-ABRIS-02', 1) # Down arrow
	pushSeqCmd(dt, 'ABRIS.PTR_BTN-ABRIS-02', 0) # release
	pushSeqCmd(dt, 'ABRIS.PTR_BTN-ABRIS-04', 1) # CHANGE
	pushSeqCmd(dt, 'ABRIS.PTR_BTN-ABRIS-04', 0) # release
	# Return to main setup screen.
	pushSeqCmd(dt, 'ABRIS.PTR_BTN-ABRIS-01', 1) # SETUP
	pushSeqCmd(dt, 'ABRIS.PTR_BTN-ABRIS-01', 0) # release
	pushSeqCmd(dt, 'ABRIS.PTR_BTN-ABRIS-02', 1) # Down arrow
	pushSeqCmd(dt, 'ABRIS.PTR_BTN-ABRIS-02', 0) # release
	pushSeqCmd(dt, 'ABRIS.PTR_BTN-ABRIS-01', 1) # SETUP
	pushSeqCmd(dt, 'ABRIS.PTR_BTN-ABRIS-01', 0) # release
	# Go to map.
	pushSeqCmd(dt, 'ABRIS.PTR_BTN-ABRIS-05', 1) # MENU
	pushSeqCmd(dt, 'ABRIS.PTR_BTN-ABRIS-05', 0) # release
	pushSeqCmd(dt, 'ABRIS.PTR_BTN-ABRIS-05', 1) # NAV
	pushSeqCmd(dt, 'ABRIS.PTR_BTN-ABRIS-05', 0) # release
	pushSeqCmd(dt, 'ABRIS.PTR_BTN-ABRIS-02', 1) # MAP
	pushSeqCmd(dt, 'ABRIS.PTR_BTN-ABRIS-02', 0) # release

	pushSeqCmd(dt, 'scriptTimerEnd', name='alignTimer')
	pushSeqCmd(dt, '', '', "INU Accelerated Alignment - Complete")

	# Autopilot buttons
	# Autopilot bank hold - On
	pushSeqCmd(dt, 'AUTOPILOT.PPR-K-PTR01', 1)
	pushSeqCmd(dt, 'AUTOPILOT.PPR-K-PTR01', 0)
	# Autopilot pitch hold - On
	pushSeqCmd(dt, 'AUTOPILOT.PPR-T-PTR02', 1)
	pushSeqCmd(dt, 'AUTOPILOT.PPR-T-PTR02', 0)
	# Autopilot heading hold - On
	pushSeqCmd(dt, 'AUTOPILOT.PPR-N-PTR03', 1)
	pushSeqCmd(dt, 'AUTOPILOT.PPR-N-PTR03', 0)

	pushSeqCmd(dt, 'scriptSpeech', "Manual steps remaining:  Set lights.  Tune radios.  Set unguided weapon pylon ballistic knob to match rockets (middle knob on right rear wall).  Set altimeter to Q F E or Q N H.")

	return seq


def HotStart(config, vars, helper, *args, **kwargs):
	seq = []
	dt = 0.3

	pushSeqCmd = helper.makePushSeqCmd(seq)

	# Start sequence
	pushSeqCmd(0, '', '', "Running Hot Start sequence.")

	# SPU-9 radio selector knob - Ground Crew (allows rearming)
	pushSeqCmd(dt, 'SPU_9.RADIO-RATE-PTR', 3)

	# Exterior lights
	# Anticollision beacon - Off # Right wall, lower middle
	pushSeqCmd(dt, 'NAVLIGHT_SYSTEM.FLASHER-PTR', 0)
	# Blade tip lights - Off # Right wall, lower rear
	pushSeqCmd(dt, 'NAVLIGHT_SYSTEM.CONTUR-LIGHT-PTR', 0)
	# Formation lights - Off # Right wall, lower rear
	pushSeqCmd(dt, 'NAVLIGHT_SYSTEM.FORMATION-PTR', 0)
	# Nav lights - On # Front upper canopy frame, left side
	pushSeqCmd(dt, 'NAVLIGHT_SYSTEM.ANO-PTR', 0)

	# Voice message system (Betty) - On
	pushSeqCmd(dt, 'VMS.SPEECH-INFO-AVAR-PTR', 1)

	# Engine anti-ice/dust protection - As needed
	pushSeqCmd(dt, 'scriptSpeech', 'Set anti dust as needed')

	# Heading source selector (needed after v.2.8)
	# Gyro/Mag/Manual heading switch - GYRO (middle)
	pushSeqCmd(dt, 'NAV_INTERFACE.GYRO-MAG-MAN-HEADING-PTR', 1) # 0 = MH, 1 = GYRO, 2 = MAN

	# PVI and datalink, right console forward
	# Datalink master mode knob - WINGM
	pushSeqCmd(dt, 'DATALINK.DTLK-MASTER-MODES-PTR', 2) # 0 = OFF, 1 = REC, 2 = WINGM, 3 = COM

	# Default startup done, doing post-startup tasks.
	# Laser rangefinder - Arm
	pushSeqCmd(dt, 'LASERRANGER.PVR-IZL-PTR', 1)
	# Master Arm - Arm
	pushSeqCmd(dt, 'WEAP_INTERFACE.MASTER-ARM-PTR', 1)
	# Man/Auto weapon - Man
	pushSeqCmd(dt, 'WEAP_INTERFACE.PUI800-AUTO-PTR', 1)

	# UV-26 countermeasures dispenser to "411" (4 flares, 1 second apart)
	# UV-26 Dispenser - Both sides
	pushSeqCmd(dt, 'UV_26.UV26-BOARD-PTR', 1) # Switch to middle
	# UV-26 Program - Reset (to default program 110)
	pushSeqCmd(dt, 'UV_26.UV26-CANCELPRG-PTR', 1) # Press
	pushSeqCmd(dt, 'UV_26.UV26-CANCELPRG-PTR', 0) # Release
	# UV-26 Num of sequences - 4
	pushSeqCmd(dt, 'UV_26.UV26-SERIES-PTR', 1) # Press
	pushSeqCmd(dt, 'UV_26.UV26-SERIES-PTR', 0) # Release
	pushSeqCmd(dt, 'UV_26.UV26-SERIES-PTR', 1) # Press
	pushSeqCmd(dt, 'UV_26.UV26-SERIES-PTR', 0) # Release
	pushSeqCmd(dt, 'UV_26.UV26-SERIES-PTR', 1) # Press
	pushSeqCmd(dt, 'UV_26.UV26-SERIES-PTR', 0) # Release
	# UV-26 Dispense interval - 1 SEC
	pushSeqCmd(dt, 'UV_26.UV26-INTERVAL-PTR', 1) # Press
	pushSeqCmd(dt, 'UV_26.UV26-INTERVAL-PTR', 0) # Release

	# Set up ABRIS
	# ABRIS - Geo grid off, UTM grid (10 km grid) on
	pushSeqCmd(dt, 'ABRIS.PTR_BTN-ABRIS-01', 1) # OPTION
	pushSeqCmd(dt, 'ABRIS.PTR_BTN-ABRIS-01', 0) # release
	pushSeqCmd(dt, 'ABRIS.PTR_BTN-ABRIS-01', 1) # SETUP
	pushSeqCmd(dt, 'ABRIS.PTR_BTN-ABRIS-01', 0) # release
	pushSeqCmd(dt, 'ABRIS.PTR_BTN-ABRIS-03', 1) # Up arrow to wrap around
	pushSeqCmd(dt, 'ABRIS.PTR_BTN-ABRIS-03', 0) # release
	pushSeqCmd(dt, 'ABRIS.PTR_BTN-ABRIS-01', 1) # CHART
	pushSeqCmd(dt, 'ABRIS.PTR_BTN-ABRIS-01', 0) # release
	for i in range(24):
		pushSeqCmd(dt, 'ABRIS.PTR_BTN-ABRIS-02', 1) # Down arrow
		pushSeqCmd(dt, 'ABRIS.PTR_BTN-ABRIS-02', 0) # release
	pushSeqCmd(dt, 'ABRIS.PTR_BTN-ABRIS-04', 1) # CHANGE
	pushSeqCmd(dt, 'ABRIS.PTR_BTN-ABRIS-04', 0) # release
	pushSeqCmd(dt, 'ABRIS.PTR_BTN-ABRIS-02', 1) # Down arrow
	pushSeqCmd(dt, 'ABRIS.PTR_BTN-ABRIS-02', 0) # release
	pushSeqCmd(dt, 'ABRIS.PTR_BTN-ABRIS-04', 1) # CHANGE
	pushSeqCmd(dt, 'ABRIS.PTR_BTN-ABRIS-04', 0) # release
	# Return to main setup screen.
	pushSeqCmd(dt, 'ABRIS.PTR_BTN-ABRIS-01', 1) # SETUP
	pushSeqCmd(dt, 'ABRIS.PTR_BTN-ABRIS-01', 0) # release
	pushSeqCmd(dt, 'ABRIS.PTR_BTN-ABRIS-02', 1) # Down arrow
	pushSeqCmd(dt, 'ABRIS.PTR_BTN-ABRIS-02', 0) # release
	pushSeqCmd(dt, 'ABRIS.PTR_BTN-ABRIS-01', 1) # SETUP
	pushSeqCmd(dt, 'ABRIS.PTR_BTN-ABRIS-01', 0) # release
	# Go to map.
	pushSeqCmd(dt, 'ABRIS.PTR_BTN-ABRIS-05', 1) # MENU
	pushSeqCmd(dt, 'ABRIS.PTR_BTN-ABRIS-05', 0) # release
	pushSeqCmd(dt, 'ABRIS.PTR_BTN-ABRIS-05', 1) # NAV
	pushSeqCmd(dt, 'ABRIS.PTR_BTN-ABRIS-05', 0) # release
	pushSeqCmd(dt, 'ABRIS.PTR_BTN-ABRIS-02', 1) # MAP
	pushSeqCmd(dt, 'ABRIS.PTR_BTN-ABRIS-02', 0) # release

	pushSeqCmd(dt, 'scriptSpeech', "Manual steps remaining:  Set lights.  Tune radios.  Set unguided weapon pylon ballistic knob to match rockets (middle knob on right rear wall).  Set altimeter to Q F E or Q N H.")

	return seq
