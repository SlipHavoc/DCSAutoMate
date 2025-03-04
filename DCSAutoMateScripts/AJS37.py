# Return a Dictionary of script data.  The 'scripts' key is a list of scripts that users will be selecting from.  Each script has an associated 'function', which is the name of the function in this file that will be called to generate the command sequence, and a dictionary of 'vars' that the user will be prompted to choose from before running the script, and will be passed into the sequence generating function.
def getScriptData():
	return {
		'scripts': [
			{
				'name': 'Cold Start',
				'function': 'ColdStart',
				'vars': {
					#'Time': ['Day', 'Night'],
				},
			},
			{
				'name': 'Hot Start',
				'function': 'HotStart',
				'vars': {
					#'Time': ['Day', 'Night'],
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
			#		'Time': ['Day', 'Night'],
			#	},
			#},
		],
	}


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

	pushSeqCmd(0, '', '', "Running Cold Start sequence")

	# Pre-start switch positions
	# Main power (HUVUDSTRÖM) - OFF
	pushSeqCmd(dt, 'MAIN_ELECTRIC_POWER', 0)
	# Low-pressure fuel valve (LT-KRAN) - OFF
	pushSeqCmd(dt, 'LOW_PRES_FUEL_VALVE', 0)

	# Generator - OFF
	pushSeqCmd(dt, 'GENERATOR', 0)
	# High-pressure fuel valve (HT-KRAN) - OFF
	pushSeqCmd(dt, 'HIGH_PRES_FUEL_VALVE', 0)
	# Master mode knob - BER
	pushSeqCmd(dt, 'MASTER_MODE_SELECT', 1) # 0 = FK, 1 = BER, 2 = NAV, 3 = ANF, 4 = SPA, 5 = LANDNING NAV, 6 = LANDNING PO

	# Begin startup

	# Main power (HUVUDSTRÖM) - ON
	pushSeqCmd(dt, 'MAIN_ELECTRIC_POWER', 1)
	# Master Caution - Cancel
	pushSeqCmd(dt, 'MASTER_CAUTION_RESET', 1) # Press
	pushSeqCmd(dt, 'MASTER_CAUTION_RESET', 0) # Release
	# Low-pressure fuel valve (LT-KRAN) - ON
	pushSeqCmd(dt, 'LOW_PRES_FUEL_VALVE', 1)

	# Instrument lights - 100%
	pushSeqCmd(dt, 'INSTRUMENT_LIGHTS', int16())
	# Panel lights - 100%
	pushSeqCmd(dt, 'PANEL_LIGHTS', int16())
	# Canopy - Close (10s)
	pushSeqCmd(dt, 'CANOPY_OPEN_CLOSE', 2) # Canopy lever forward
	pushSeqCmd(10, 'CANOPY_OPEN_CLOSE', 1) # Canopy lever neutral

	# Engine start (35s)
	# Generator - ON
	pushSeqCmd(dt, 'GENERATOR', 1)
	# High-pressure fuel valve (HT-KRAN) - ON
	pushSeqCmd(dt, 'HIGH_PRES_FUEL_VALVE', 1)
	# Engine Start switch - ON
	pushSeqCmd(dt, 'START_SYSTEM', 1)
	pushSeqCmd(35, '', '', "Engine started, wait for systems to power up (25s)")
	pushSeqCmd(25, '', '', "Systems powered up")

	# Oxygen / Suit air valve (SYRGAS) - ON
	pushSeqCmd(dt, 'OXYGEN_LEVER', 1)

	# LOADING DATA CARTRIDGE
	# Data Cartridge - REMOVE
	pushSeqCmd(dt, 'DATA_CARTRIDGE', 0)
	pushSeqCmd(2, '', '', "Data Cartridge removed")
	# Data Cartridge - INSERT
	pushSeqCmd(dt, 'DATA_CARTRIDGE', 1)
	pushSeqCmd(2, '', '', "Data Cartridge inserted")

	# Data selector knob - REF/LOLA, IN
	pushSeqCmd(dt, 'DATAPANEL_SELECTOR', 5) # Datapanel selector knob, 0 = ID-NR, 1 = TAKT, 2 = TID, 3 = VIND RUTA MAL, 4 = BANA GRANS, 5 = REF LOLA, 6 = AKT POS
	pushSeqCmd(dt, 'DATA_IN_OUT', 1) # In/Out switch, 1 = IN, 2 = OUT
	# Enter data - 9099, LS/SKU
	pushSeqCmd(dt, 'DATAPANEL_KEY_9', 1) # Press
	pushSeqCmd(dt, 'DATAPANEL_KEY_9', 0) # Release
	pushSeqCmd(dt, 'DATAPANEL_KEY_0', 1) # Press
	pushSeqCmd(dt, 'DATAPANEL_KEY_0', 0) # Release
	pushSeqCmd(dt, 'DATAPANEL_KEY_9', 1) # Press
	pushSeqCmd(dt, 'DATAPANEL_KEY_9', 0) # Release
	pushSeqCmd(dt, 'DATAPANEL_KEY_9', 1) # Press
	pushSeqCmd(dt, 'DATAPANEL_KEY_9', 0) # Release
	pushSeqCmd(dt, 'NAV_SELECT_BTN_LS', 1) # Press
	pushSeqCmd(dt, 'NAV_SELECT_BTN_LS', 0) # Release
	# Wait for cartridge to be read (7s)
	pushSeqCmd(7, '', '', "Data loaded")
	# Data selector knob - AKT/POS, OUT
	pushSeqCmd(dt, 'DATAPANEL_SELECTOR', 6) # Datapanel selector knob, 0 = ID-NR, 1 = TAKT, 2 = TID, 3 = VIND RUTA MAL, 4 = BANA GRANS, 5 = REF LOLA, 6 = AKT POS
	pushSeqCmd(dt, 'DATA_IN_OUT', 0) # In/Out switch, 1 = IN, 2 = OUT

	# Ejection seat - ARM
	pushSeqCmd(dt, 'EJECTION_SEAT_ARM', 1)
	# Master mode knob - NAV
	pushSeqCmd(dt, 'MASTER_MODE_SELECT', 2) # 0 = FK, 1 = BER, 2 = NAV, 3 = ANF, 4 = SPA, 5 = LANDNING NAV, 6 = LANDNING PO
	# Slav SI switch - F
	pushSeqCmd(dt, 'SLAV_SI', 0) # 0 = F, 1 = T
	# Parking brake - OFF
	pushSeqCmd(dt, 'PARKING_BRAKE', 'TOGGLE')

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

	pushSeqCmd(0, '', '', "Running Hot Start sequence")

	# Instrument lights - 100%
	pushSeqCmd(dt, 'INSTRUMENT_LIGHTS', int16())
	# Panel lights - 100%
	pushSeqCmd(dt, 'PANEL_LIGHTS', int16())

	# LOADING DATA CARTRIDGE
	# Data Cartridge - REMOVE
	pushSeqCmd(dt, 'DATA_CARTRIDGE', 0)
	pushSeqCmd(2, '', '', "Data Cartridge removed")
	# Data Cartridge - INSERT
	pushSeqCmd(dt, 'DATA_CARTRIDGE', 1)
	pushSeqCmd(2, '', '', "Data Cartridge inserted")

	# Data selector knob - REF/LOLA, IN
	pushSeqCmd(dt, 'DATAPANEL_SELECTOR', 5) # Datapanel selector knob, 0 = ID-NR, 1 = TAKT, 2 = TID, 3 = VIND RUTA MAL, 4 = BANA GRANS, 5 = REF LOLA, 6 = AKT POS
	pushSeqCmd(dt, 'DATA_IN_OUT', 1) # In/Out switch, 1 = IN, 2 = OUT
	# Enter data - 9099, LS/SKU
	pushSeqCmd(dt, 'DATAPANEL_KEY_9', 1) # Press
	pushSeqCmd(dt, 'DATAPANEL_KEY_9', 0) # Release
	pushSeqCmd(dt, 'DATAPANEL_KEY_0', 1) # Press
	pushSeqCmd(dt, 'DATAPANEL_KEY_0', 0) # Release
	pushSeqCmd(dt, 'DATAPANEL_KEY_9', 1) # Press
	pushSeqCmd(dt, 'DATAPANEL_KEY_9', 0) # Release
	pushSeqCmd(dt, 'DATAPANEL_KEY_9', 1) # Press
	pushSeqCmd(dt, 'DATAPANEL_KEY_9', 0) # Release
	pushSeqCmd(dt, 'NAV_SELECT_BTN_LS', 1) # Press
	pushSeqCmd(dt, 'NAV_SELECT_BTN_LS', 0) # Release
	# Wait for cartridge to be read (7s)
	pushSeqCmd(7, '', '', "Data loaded")
	# Data selector knob - AKT/POS, OUT
	pushSeqCmd(dt, 'DATAPANEL_SELECTOR', 6) # Datapanel selector knob, 0 = ID-NR, 1 = TAKT, 2 = TID, 3 = VIND RUTA MAL, 4 = BANA GRANS, 5 = REF LOLA, 6 = AKT POS
	pushSeqCmd(dt, 'DATA_IN_OUT', 0) # In/Out switch, 1 = IN, 2 = OUT

	# Slav SI switch - F
	pushSeqCmd(dt, 'SLAV_SI', 0) # 0 = F, 1 = T

	return seq


def ReloadDataCartridge(config, vars):
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

	pushSeqCmd(0, '', '', "Reloading Data Cartridge")

	# LOADING DATA CARTRIDGE
	# Data Cartridge - REMOVE
	pushSeqCmd(dt, 'DATA_CARTRIDGE', 0)
	pushSeqCmd(2, '', '', "Data Cartridge removed")
	# Data Cartridge - INSERT
	pushSeqCmd(dt, 'DATA_CARTRIDGE', 1)
	pushSeqCmd(2, '', '', "Data Cartridge inserted")

	# Data selector knob - REF/LOLA, IN
	pushSeqCmd(dt, 'DATAPANEL_SELECTOR', 5) # Datapanel selector knob, 0 = ID-NR, 1 = TAKT, 2 = TID, 3 = VIND RUTA MAL, 4 = BANA GRANS, 5 = REF LOLA, 6 = AKT POS
	pushSeqCmd(dt, 'DATA_IN_OUT', 1) # In/Out switch, 1 = IN, 2 = OUT
	# Enter data - 9099, LS/SKU
	pushSeqCmd(dt, 'DATAPANEL_KEY_9', 1) # Press
	pushSeqCmd(dt, 'DATAPANEL_KEY_9', 0) # Release
	pushSeqCmd(dt, 'DATAPANEL_KEY_0', 1) # Press
	pushSeqCmd(dt, 'DATAPANEL_KEY_0', 0) # Release
	pushSeqCmd(dt, 'DATAPANEL_KEY_9', 1) # Press
	pushSeqCmd(dt, 'DATAPANEL_KEY_9', 0) # Release
	pushSeqCmd(dt, 'DATAPANEL_KEY_9', 1) # Press
	pushSeqCmd(dt, 'DATAPANEL_KEY_9', 0) # Release
	pushSeqCmd(dt, 'NAV_SELECT_BTN_LS', 1) # Press
	pushSeqCmd(dt, 'NAV_SELECT_BTN_LS', 0) # Release
	# Wait for cartridge to be read (7s)
	pushSeqCmd(7, '', '', "Data loaded")
	# Data selector knob - AKT/POS, OUT
	pushSeqCmd(dt, 'DATAPANEL_SELECTOR', 6) # Datapanel selector knob, 0 = ID-NR, 1 = TAKT, 2 = TID, 3 = VIND RUTA MAL, 4 = BANA GRANS, 5 = REF LOLA, 6 = AKT POS
	pushSeqCmd(dt, 'DATA_IN_OUT', 0) # In/Out switch, 1 = IN, 2 = OUT

	return seq
