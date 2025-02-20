# Return a Dictionary of script data.  The 'scripts' key is a list of scripts that users will be selecting from.  Each script has an associated 'function', which is the name of the function in this file that will be called to generate the command sequence, and a dictionary of 'vars' that the user will be prompted to choose from before running the script, and will be passed into the sequence generating function.
def getScriptData():
	return {
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
		],
	}

def getInfo():
	return ''

# Returns 0-65535 scaled by multiple (0-1), eg for 50% call int16(0.5)
def int16(mult = 1):
	int16 = 65535
	return int(mult * int16)


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

	inuAlignTime = 3 * 60  # 3m00s

	# Start sequence
	pushSeqCmd(0, '', '', "Running Cold Start sequence.")
	pushSeqCmd(dt, '', '', 'Set collective full down.')
	pushSeqCmd(dt, 'scriptSpeech', 'Set collective full down.')

	# SPU-9 radio selector knob - Ground Crew (allows rearming)
	pushSeqCmd(dt, 'RADIO_SELECTOR', 3)

	# Cockpit door - Close
	pushSeqCmd(dt, 'scriptKeyboard', 'RCtrl down')
	pushSeqCmd(dt, 'scriptKeyboard', 'c')
	pushSeqCmd(dt, 'scriptKeyboard', 'RCtrl up')

	# Voice message system (Betty) - On
	pushSeqCmd(dt, 'VOICE_MSG_EMER', 1)

	# Battery 1 - On
	pushSeqCmd(dt, 'ELEC_BATTERY_1_COVER', 1) # Cover open
	pushSeqCmd(dt, 'ELEC_BATTERY_1', 1) # Switch
	pushSeqCmd(dt, 'ELEC_BATTERY_1_COVER', 0) # Cover close
	# Battery 2 - On
	pushSeqCmd(dt, 'ELEC_BATTERY_2_COVER', 1) # Cover open
	pushSeqCmd(dt, 'ELEC_BATTERY_2', 1) # Switch
	pushSeqCmd(dt, 'ELEC_BATTERY_2_COVER', 0) # Cover close

	# ABRIS power, turn on as soon as possible so it finishes booting up by the time we're done.
	# ABRIS power - On
	pushSeqCmd(dt, 'ABRIS_POWER', 1)

	# Begin "accelerated" alignment (3 mins), see manual p.330
	# K-041 targeting-navigation system power - On # Left console in front of collective
	pushSeqCmd(dt, 'K041_POWER', 1)
	# PVI NAV master mode knob - OPER
	pushSeqCmd(dt, 'PVI_MODES', 3) # 0 = OFF, 1 = CHECK, 2 = ENT, 3 = OPER, 4 = STM, 5 = K-1, 6 = K-2
	# PVI NAV datalink power - On
	pushSeqCmd(dt, 'PVI_POWER', 1)
	# INU heat - On # Right rear wall
	pushSeqCmd(dt, 'PPK800_INU_HEAT', 1)
	# INU power - On # Right rear wall
	pushSeqCmd(dt, 'PPK800_INU_POWER', 1)
	pushSeqCmd(dt, 'scriptTimerStart', name='alignTimer', duration=inuAlignTime)
	# INU accelerated alignment in process (3m)
	# SAI power - On # Right wall
	pushSeqCmd(dt, 'SAI_POWER', 1)


	# Right wall radio switches:
	# Fuel gauge power - On
	pushSeqCmd(dt, 'FUEL_METER_POWER', 1)
	# Intercom (SPU-9) power - On
	pushSeqCmd(dt, 'COMM_INTERCOM_POWER', 1)
	# VHF-1 (R-828) power - On
	pushSeqCmd(dt, 'COMM_VHF1_POWER', 1)
	# VHF-2 (R-800) power - On
	pushSeqCmd(dt, 'COMM_VHF2_POWER', 1)
	# Datalink radio (TLK) power - On
	pushSeqCmd(dt, 'COMM_DATALINK_TLK_POWER', 1)
	# VHF-TLK power - On
	pushSeqCmd(dt, 'COMM_DATALINK_VHF_TLK_POWER', 1)
	# NOTE: SA-TLF switch has no function in game.

	# Various avionics systems
	# K-041 targeting-navigation system power - On # Left console in front of collective
	pushSeqCmd(dt, 'NAV_POWER', 1)
	# EKRAN HYD TRANS PWR switch - AUTO BASE # Right rear wall, black guarded switch
	pushSeqCmd(dt, 'ELEC_HYD_TRAN_EKRAN_POWER', 0) # Switch
	pushSeqCmd(dt, 'ELEC_HYD_TRAN_EKRAN_POWER_COVER', 0) # FIXME Doesn't matter what value you send, the cover is always toggled, not set to a specific state.  Since it starts open on cold start, only toggle it after flipping the switch.  On shutdown, toggle it back open again and leave it open.

	# UV-26 countermeasures dispenser (CMD) power - On # Right rear wall, black guarded switch
	pushSeqCmd(dt, 'UV26_POWER_COVER', 1) # Cover open
	pushSeqCmd(dt, 'UV26_POWER', 1) # Switch
	pushSeqCmd(dt, 'UV26_POWER_COVER', 1) # Cover close
	# L-140 laser warning (LWS) power - On # Right rear wall
	pushSeqCmd(dt, 'LWS_POWER', 1)
	# Fire extinguishers - On # Right wall upper row, black guarded switch
	pushSeqCmd(dt, 'FIREEXT_EXT_MODE_COVER', 1) # Cover open
	pushSeqCmd(dt, 'FIREEXT_EXT_MODE', 2) # Switch
	pushSeqCmd(dt, 'FIREEXT_EXT_MODE_COVER', 0) # Cover close

	# APU fuel shut-off valve - On
	pushSeqCmd(dt, 'FUEL_APU_VLV_COVER', 1) # Cover toggle
	pushSeqCmd(dt, 'FUEL_APU_VLV', 1) # Switch
	# Forward fuel tank pump - On
	pushSeqCmd(dt, 'FUEL_FORWARD_PUMP_POWER', 1)
	# Aft fuel tank pump - On
	pushSeqCmd(dt, 'FUEL_AFT_PUMP_POWER', 1)

	# Master Caution Light - Reset
	pushSeqCmd(dt, 'SC_MASTER_CAUTION_BTN', 1) # Press
	pushSeqCmd(dt, 'SC_MASTER_CAUTION_BTN', 0) # Release

	# APU start
	# Engine selector switch - APU
	pushSeqCmd(dt, 'ENG_SELECTOR', 0) # 0 = APU, 1 = LH ENG, 2 = RH ENG, 3 = TURBO GEAR
	# APU - Starting (20s)
	pushSeqCmd(dt, 'ENG_START', 1) # Press
	pushSeqCmd(dt, 'ENG_START', 0) # Release
	pushSeqCmd(20, '', '', "APU started")

	# Prepare for engine start
	# Rotor brake - Off
	pushSeqCmd(dt, 'ENG_ROTOR_BREAK', 0) # NOTE Misspelling, "ENG_ROTOR_BREAK" is the DCS BIOS command.
	# Left engine fuel shut-off switch - On
	pushSeqCmd(dt, 'FUEL_L_ENG_VLV_COVER', 0) # Cover toggle
	pushSeqCmd(dt, 'FUEL_L_ENG_VLV', 1) # Switch
	pushSeqCmd(dt, 'FUEL_L_ENG_VLV_COVER', 0) # Cover toggle
	# Right engine fuel shut-off switch - On
	pushSeqCmd(dt, 'FUEL_R_ENG_VLV_COVER', 0) # Cover toggle
	pushSeqCmd(dt, 'FUEL_R_ENG_VLV', 1) # Switch
	pushSeqCmd(dt, 'FUEL_R_ENG_VLV_COVER', 0) # Cover toggle
	# Left engine EEG - On
	pushSeqCmd(dt, 'ENG_L_ENG_EEG_COVER', 1) # Cover open
	pushSeqCmd(dt, 'ENG_L_ENG_EEG', 1) # Switch
	pushSeqCmd(dt, 'ENG_L_ENG_EEG_COVER', 0) # Cover close
	# Right engine EEG - On
	pushSeqCmd(dt, 'ENG_R_ENG_EEG_COVER', 1) # Cover open
	pushSeqCmd(dt, 'ENG_R_ENG_EEG', 1) # Switch
	pushSeqCmd(dt, 'ENG_R_ENG_EEG_COVER', 0) # Cover close

	# Left engine start
	# Engine selector switch - Left engine
	pushSeqCmd(dt, 'ENG_SELECTOR', 1) # 0 = APU, 1 = LH ENG, 2 = RH ENG, 3 = TURBO GEAR
	# Left engine - Starting (50s)
	pushSeqCmd(dt, 'ENG_START', 1) # Press
	pushSeqCmd(dt, 'ENG_START', 0) # Release
	pushSeqCmd(15, '', '', "Left engine at 20% RPM: cut-off valve - Open")
	pushSeqCmd(dt, 'ENG_L_CUTOFF_VLV_HANDLE', 1)
	pushSeqCmd(45, '', '', "Left engine - Started")

	# Right engine start
	# Engine selector switch - Right engine
	pushSeqCmd(dt, 'ENG_SELECTOR', 2) # 0 = APU, 1 = LH ENG, 2 = RH ENG, 3 = TURBO GEAR
	# Right engine - Starting (50s)
	pushSeqCmd(dt, 'ENG_START', 1) # Press
	pushSeqCmd(dt, 'ENG_START', 0) # Release
	pushSeqCmd(15, '', '', "Right engine at 20% RPM: cut-off valve - Open")
	pushSeqCmd(dt, 'ENG_R_CUTOFF_VLV_HANDLE', 1)
	pushSeqCmd(45, '', '', "Right engine - Started")

	# APU - Stop
	pushSeqCmd(dt, 'ENG_APU_STOP', 1)
	pushSeqCmd(dt, 'ENG_APU_STOP', 0)
	# APU fuel shut-off valve - Off
	pushSeqCmd(dt, 'FUEL_APU_VLV', 0) # Switch
	pushSeqCmd(dt, 'FUEL_APU_VLV_COVER', 1) # Cover toggle

	# Left and right throttles - Auto (10s)
	pushSeqCmd(dt, 'scriptKeyboard', 'pgup')
	pushSeqCmd(dt, 'scriptKeyboard', 'pgup') # Needs two "presses" to get to Auto.
	pushSeqCmd(10, '', '', "Engines - spooled up")

	# Left AC generator - On
	pushSeqCmd(dt, 'ELEC_AC_L_GEN', 1)
	# Right AC generator - On
	pushSeqCmd(dt, 'ELEC_AC_R_GEN', 1)
	# Engine anti-ice/dust protection - As needed
	pushSeqCmd(dt, 'scriptSpeech', 'Set anti dust as needed')

	# Heading source selector (needed after DCS v.2.8)
	# Gyro/Mag/Manual heading switch - GYRO (middle)
	pushSeqCmd(dt, 'NAV_GYRO_MAG_MAN_HDG', 1) # 0 = MH, 1 = GYRO, 2 = MAN

	# PVI and datalink, right console forward
	# Datalink master mode knob - WINGM
	pushSeqCmd(dt, 'DLNK_MASTER_MODE', 2) # 0 = OFF, 1 = REC, 2 = WINGM, 3 = COM

	# Ejection system - On
	pushSeqCmd(dt, 'EJECT_POWER_COVER', 1) # Cover open
	pushSeqCmd(dt, 'EJECT_POWER_1', 1) # Switch 1
	pushSeqCmd(dt, 'EJECT_POWER_2', 1) # Switch 2
	pushSeqCmd(dt, 'EJECT_POWER_3', 1) # Switch 3
	pushSeqCmd(dt, 'EJECT_POWER_COVER', 0) # Cover close

	# Weapons control system power - On # Right wall lower row, next to ejection system switches
	pushSeqCmd(dt, 'WEAPONS_POWER_COVER', 1) # Cover open
	pushSeqCmd(dt, 'WEAPONS_POWER', 1) # Switch
	pushSeqCmd(dt, 'WEAPONS_POWER_COVER', 0) # Cover open

	# Lights, uncomment as needed
	# Anticollision beacon - On
	#pushSeqCmd(dt, NAVLIGHT_SYSTEM, 3003, 1)
	# Blade tip lights - On
	#pushSeqCmd(dt, NAVLIGHT_SYSTEM, 3001, 1)
	# Formation lights -
	#pushSeqCmd(dt, NAVLIGHT_SYSTEM, 3002, 0) # Off (center switch position)
	#pushSeqCmd(dt, NAVLIGHT_SYSTEM, 3002, value = 0.1) # 10%
	#pushSeqCmd(dt, NAVLIGHT_SYSTEM, 3002, value = 0.2) # 30%
	#pushSeqCmd(dt, NAVLIGHT_SYSTEM, 3002, value = 0.3) # 100%
	# Nav lights - On # Front upper canopy frame, left side
	#pushSeqCmd(dt, NAVLIGHT_SYSTEM, 3004, 0) # Off (center switch position)
	#pushSeqCmd(dt, NAVLIGHT_SYSTEM, 3004, value = 0.1) # 10%
	#pushSeqCmd(dt, NAVLIGHT_SYSTEM, 3004, value = 0.2) # 30%
	#pushSeqCmd(dt, NAVLIGHT_SYSTEM, 3004, value = 0.3) # 100%

	# IFF power - On
	pushSeqCmd(dt, 'IFF_POWER_COVER', 1) # Cover open
	pushSeqCmd(dt, 'IFF_POWER', 1) # Switch
	pushSeqCmd(dt, 'IFF_POWER_COVER', 0) # Cover close
	# SAI - Uncage and center
	pushSeqCmd(dt, 'SAI_CTRL_ROT', int16(-0.03))
	pushSeqCmd(dt, 'SAI_CTRL_ROT', int16(-0.03))
	pushSeqCmd(dt, 'SAI_CTRL_ROT', int16(-0.03))
	pushSeqCmd(dt, 'SAI_CTRL_ROT', int16(-0.03))
	pushSeqCmd(dt, 'SAI_CTRL_ROT', int16(-0.03))
	pushSeqCmd(dt, 'SAI_CTRL_ROT', int16(-0.03))
	pushSeqCmd(dt, 'SAI_CTRL_ROT', int16(-0.03))
	pushSeqCmd(dt, 'SAI_CTRL_ROT', int16(-0.03))

	# Default startup done, doing post-startup tasks.
	# Laser rangefinder - Arm
	pushSeqCmd(dt, 'LASER_STANDBY', 1)
	# Master Arm - Arm
	pushSeqCmd(dt, 'WEAPONS_MASTER_ARM', 1)
	# Man/Auto weapon - Man
	pushSeqCmd(dt, 'WEAPONS_MANUAL_AUTO', 1)

	# UV-26 countermeasures dispenser
	# UV-26 Dispenser - Both sides
	pushSeqCmd(dt, 'UV26_DISPENSERS_SELECTOR', 1) # Switch to middle
	# UV-26 Program - Reset (to default program 110)
	pushSeqCmd(dt, 'UV26_RESET', 1) # Press
	pushSeqCmd(dt, 'UV26_RESET', 0) # Release
	# UV-26 Num of sequences - 4
	pushSeqCmd(dt, 'UV26_SERIES', 1) # Press
	pushSeqCmd(dt, 'UV26_SERIES', 0) # Release
	pushSeqCmd(dt, 'UV26_SERIES', 1) # Press
	pushSeqCmd(dt, 'UV26_SERIES', 0) # Release
	pushSeqCmd(dt, 'UV26_SERIES', 1) # Press
	pushSeqCmd(dt, 'UV26_SERIES', 0) # Release
	# UV-26 Dispense interval - 1 SEC
	pushSeqCmd(dt, 'UV26_INTERVAL', 1) # Press
	pushSeqCmd(dt, 'UV26_INTERVAL', 0) # Release

	# Set up ABRIS
	# ABRIS - Geo grid off, UTM grid (10 km grid) on
	pushSeqCmd(dt, 'ABRIS_BTN_1', 1) # OPTION
	pushSeqCmd(dt, 'ABRIS_BTN_1', 0) # release
	pushSeqCmd(dt, 'ABRIS_BTN_1', 1) # SETUP
	pushSeqCmd(dt, 'ABRIS_BTN_1', 0) # release
	pushSeqCmd(dt, 'ABRIS_BTN_3', 1) # Up arrow to wrap around
	pushSeqCmd(dt, 'ABRIS_BTN_3', 0) # release
	pushSeqCmd(dt, 'ABRIS_BTN_1', 1) # CHART
	pushSeqCmd(dt, 'ABRIS_BTN_1', 0) # release
	for i in range(24):
		pushSeqCmd(dt, 'ABRIS_BTN_2', 1) # Down arrow
		pushSeqCmd(dt, 'ABRIS_BTN_2', 0) # release
	pushSeqCmd(dt, 'ABRIS_BTN_4', 1) # CHANGE
	pushSeqCmd(dt, 'ABRIS_BTN_4', 0) # release
	pushSeqCmd(dt, 'ABRIS_BTN_2', 1) # Down arrow
	pushSeqCmd(dt, 'ABRIS_BTN_2', 0) # release
	pushSeqCmd(dt, 'ABRIS_BTN_4', 1) # CHANGE
	pushSeqCmd(dt, 'ABRIS_BTN_4', 0) # release
	# Return to main setup screen.
	pushSeqCmd(dt, 'ABRIS_BTN_1', 1) # SETUP
	pushSeqCmd(dt, 'ABRIS_BTN_1', 0) # release
	pushSeqCmd(dt, 'ABRIS_BTN_2', 1) # Down arrow
	pushSeqCmd(dt, 'ABRIS_BTN_2', 0) # release
	pushSeqCmd(dt, 'ABRIS_BTN_1', 1) # SETUP
	pushSeqCmd(dt, 'ABRIS_BTN_1', 0) # release
	# Go to map.
	pushSeqCmd(dt, 'ABRIS_BTN_5', 1) # MENU
	pushSeqCmd(dt, 'ABRIS_BTN_5', 0) # release
	pushSeqCmd(dt, 'ABRIS_BTN_5', 1) # NAV
	pushSeqCmd(dt, 'ABRIS_BTN_5', 0) # release
	pushSeqCmd(dt, 'ABRIS_BTN_2', 1) # MAP
	pushSeqCmd(dt, 'ABRIS_BTN_2', 0) # release

	pushSeqCmd(dt, 'scriptTimerEnd', name='alignTimer')
	pushSeqCmd(dt, '', '', "INU Accelerated Alignment - Complete")

	# Autopilot buttons
	# Autopilot bank hold - On
	pushSeqCmd(dt, 'AP_BANK_HOLD_BTN', 1)
	pushSeqCmd(dt, 'AP_BANK_HOLD_BTN', 0)
	# Autopilot pitch hold - On
	pushSeqCmd(dt, 'AP_PITCH_HOLD_BTN', 1)
	pushSeqCmd(dt, 'AP_PITCH_HOLD_BTN', 0)
	# Autopilot heading hold - On
	pushSeqCmd(dt, 'AP_HDG_HOLD_BTN', 1)
	pushSeqCmd(dt, 'AP_HDG_HOLD_BTN', 0)

	pushSeqCmd(dt, 'scriptSpeech', "Manual steps remaining:  Set lights.  Tune radios.  Set unguided weapon pylon ballistic knob to match rockets (middle knob on right rear wall).  Set altimeter to Q F E or Q N H.")

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

	# Start sequence
	pushSeqCmd(0, '', '', "Running Hot Start sequence.")

	# SPU-9 radio selector knob - Ground Crew (allows rearming)
	pushSeqCmd(dt, 'RADIO_SELECTOR', 3)

	# Voice message system (Betty) - On
	pushSeqCmd(dt, 'VOICE_MSG_EMER', 1)

	# Engine anti-ice/dust protection - As needed
	pushSeqCmd(dt, 'scriptSpeech', 'Set anti dust as needed')

	# Heading source selector (needed after v.2.8)
	# Gyro/Mag/Manual heading switch - GYRO (middle)
	pushSeqCmd(dt, 'NAV_GYRO_MAG_MAN_HDG', 1) # 0 = MH, 1 = GYRO, 2 = MAN

	# PVI and datalink, right console forward
	# Datalink master mode knob - WINGM
	pushSeqCmd(dt, 'DLNK_MASTER_MODE', 2) # 0 = OFF, 1 = REC, 2 = WINGM, 3 = COM

	# Lights, uncomment as needed
	## Anticollision beacon - On
	#pushSeqCmd(dt, NAVLIGHT_SYSTEM, 3003, 1)
	# Blade tip lights - On
	#pushSeqCmd(dt, NAVLIGHT_SYSTEM, 3001, 1)
	# Formation lights -
	#pushSeqCmd(dt, NAVLIGHT_SYSTEM, 3002, 0) # Off (center switch position)
	#pushSeqCmd(dt, NAVLIGHT_SYSTEM, 3002, value = 0.1) # 10%
	#pushSeqCmd(dt, NAVLIGHT_SYSTEM, 3002, value = 0.2) # 30%
	#pushSeqCmd(dt, NAVLIGHT_SYSTEM, 3002, value = 0.3) # 100%
	# Nav lights - On # Front upper canopy frame, left side
	#pushSeqCmd(dt, NAVLIGHT_SYSTEM, 3004, 0) # Off (center switch position)
	#pushSeqCmd(dt, NAVLIGHT_SYSTEM, 3004, value = 0.1) # 10%
	#pushSeqCmd(dt, NAVLIGHT_SYSTEM, 3004, value = 0.2) # 30%
	#pushSeqCmd(dt, NAVLIGHT_SYSTEM, 3004, value = 0.3) # 100%

	# Default startup done, doing post-startup tasks.
	# Laser rangefinder - Arm
	pushSeqCmd(dt, 'LASER_STANDBY', 1)
	# Master Arm - Arm
	pushSeqCmd(dt, 'WEAPONS_MASTER_ARM', 1)
	# Man/Auto weapon - Man
	pushSeqCmd(dt, 'WEAPONS_MANUAL_AUTO', 1)

	# UV-26 countermeasures dispenser to "411" (4 flares, 1 second apart)
	# UV-26 Dispenser - Both sides
	pushSeqCmd(dt, 'UV26_DISPENSERS_SELECTOR', 1) # Switch to middle
	# UV-26 Program - Reset (to default program 110)
	pushSeqCmd(dt, 'UV26_RESET', 1) # Press
	pushSeqCmd(dt, 'UV26_RESET', 0) # Release
	# UV-26 Num of sequences - 4
	pushSeqCmd(dt, 'UV26_SERIES', 1) # Press
	pushSeqCmd(dt, 'UV26_SERIES', 0) # Release
	pushSeqCmd(dt, 'UV26_SERIES', 1) # Press
	pushSeqCmd(dt, 'UV26_SERIES', 0) # Release
	pushSeqCmd(dt, 'UV26_SERIES', 1) # Press
	pushSeqCmd(dt, 'UV26_SERIES', 0) # Release
	# UV-26 Dispense interval - 1 SEC
	pushSeqCmd(dt, 'UV26_INTERVAL', 1) # Press
	pushSeqCmd(dt, 'UV26_INTERVAL', 0) # Release

	# Set up ABRIS
	# ABRIS - Geo grid off, UTM grid (10 km grid) on
	pushSeqCmd(dt, 'ABRIS_BTN_1', 1) # OPTION
	pushSeqCmd(dt, 'ABRIS_BTN_1', 0) # release
	pushSeqCmd(dt, 'ABRIS_BTN_1', 1) # SETUP
	pushSeqCmd(dt, 'ABRIS_BTN_1', 0) # release
	pushSeqCmd(dt, 'ABRIS_BTN_3', 1) # Up arrow to wrap around
	pushSeqCmd(dt, 'ABRIS_BTN_3', 0) # release
	pushSeqCmd(dt, 'ABRIS_BTN_1', 1) # CHART
	pushSeqCmd(dt, 'ABRIS_BTN_1', 0) # release
	for i in range(24):
		pushSeqCmd(dt, 'ABRIS_BTN_2', 1) # Down arrow
		pushSeqCmd(dt, 'ABRIS_BTN_2', 0) # release
	pushSeqCmd(dt, 'ABRIS_BTN_4', 1) # CHANGE
	pushSeqCmd(dt, 'ABRIS_BTN_4', 0) # release
	pushSeqCmd(dt, 'ABRIS_BTN_2', 1) # Down arrow
	pushSeqCmd(dt, 'ABRIS_BTN_2', 0) # release
	pushSeqCmd(dt, 'ABRIS_BTN_4', 1) # CHANGE
	pushSeqCmd(dt, 'ABRIS_BTN_4', 0) # release
	# Return to main setup screen.
	pushSeqCmd(dt, 'ABRIS_BTN_1', 1) # SETUP
	pushSeqCmd(dt, 'ABRIS_BTN_1', 0) # release
	pushSeqCmd(dt, 'ABRIS_BTN_2', 1) # Down arrow
	pushSeqCmd(dt, 'ABRIS_BTN_2', 0) # release
	pushSeqCmd(dt, 'ABRIS_BTN_1', 1) # SETUP
	pushSeqCmd(dt, 'ABRIS_BTN_1', 0) # release
	# Go to map.
	pushSeqCmd(dt, 'ABRIS_BTN_5', 1) # MENU
	pushSeqCmd(dt, 'ABRIS_BTN_5', 0) # release
	pushSeqCmd(dt, 'ABRIS_BTN_5', 1) # NAV
	pushSeqCmd(dt, 'ABRIS_BTN_5', 0) # release
	pushSeqCmd(dt, 'ABRIS_BTN_2', 1) # MAP
	pushSeqCmd(dt, 'ABRIS_BTN_2', 0) # release

	pushSeqCmd(dt, 'scriptSpeech', "Manual steps remaining:  Set lights.  Tune radios.  Set unguided weapon pylon ballistic knob to match rockets (middle knob on right rear wall).  Set altimeter to Q F E or Q N H.")

	return seq
