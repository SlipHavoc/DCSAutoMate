# Return a Dictionary of script titles and their corresponding function names.  This is a list of scripts that users will be selecting from.  The module may have other utility functions that will not be run directly by the users.
def getScriptFunctions():
	return {
		'Cold Start': 'ColdStart',
	}

# Returns 0-65535 scaled by multiple (0-1), eg for 50% call int16(0.5)
def int16(mult = 1):
	int16 = 65535
	return int(mult * int16)

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

	pushSeqCmd(0, '', '', "Running Cold Start sequence")
	
	# Pre-start switch positions
	#pushSeqCmd(dt, '', '',"Main power (HUVUDSTRÖM) - OFF")
	pushSeqCmd(dt, 'MAIN_ELECTRIC_POWER', 0)
	#pushSeqCmd(dt, '', '',"Low-pressure fuel valve (LT-KRAN) - OFF")
	pushSeqCmd(dt, 'LOW_PRES_FUEL_VALVE', 0)

	#pushSeqCmd(dt, '', '', "Generator - OFF")
	pushSeqCmd(dt, 'GENERATOR', 0)
	#pushSeqCmd(dt, '', '', "High-pressure fuel valve (HT-KRAN) - OFF")
	pushSeqCmd(dt, 'HIGH_PRES_FUEL_VALVE', 0)
	#pushSeqCmd(dt, '', '', "Master mode knob - BER")
	pushSeqCmd(dt, 'MASTER_MODE_SELECT', 1) # 0 = FK, 1 = BER, 2 = NAV, 3 = ANF, 4 = SPA, 5 = LANDNING NAV, 6 = LANDNING PO

	# Begin startup
	#pushSeqCmd(dt, '', '', "Startup")

	#pushSeqCmd(dt, '', '', "Main power (HUVUDSTRÖM) - ON")
	pushSeqCmd(dt, 'MAIN_ELECTRIC_POWER', 1)
	#pushSeqCmd(dt, '', '', "Master Caution - Cancel")
	pushSeqCmd(dt, 'MASTER_CAUTION_RESET', 1) # Press
	pushSeqCmd(dt, 'MASTER_CAUTION_RESET', 0) # Release
	#pushSeqCmd(dt, '', '', "Low-pressure fuel valve (LT-KRAN) - ON")
	pushSeqCmd(dt, 'LOW_PRES_FUEL_VALVE', 1)
	
	#pushSeqCmd(dt, '', '', "Instrument lights - 100%")
	pushSeqCmd(dt, 'INSTRUMENT_LIGHTS', int16())
	#pushSeqCmd(dt, '', '', "Panel lights - 100%")
	pushSeqCmd(dt, 'PANEL_LIGHTS', int16())
	#pushSeqCmd(dt, '', '', "Canopy - Close (10s)"), message_timeout = 10)
	pushSeqCmd(dt, 'CANOPY_OPEN_CLOSE', 2) # Canopy lever forward
	pushSeqCmd(10, 'CANOPY_OPEN_CLOSE', 1) # Canopy lever neutral

	#pushSeqCmd(dt, '', '', "Engine start (35s)"), message_timeout = 35)
	#pushSeqCmd(dt, '', '', "Generator - ON")
	pushSeqCmd(dt, 'GENERATOR', 1)
	#pushSeqCmd(dt, '', '', "High-pressure fuel valve (HT-KRAN) - ON")
	pushSeqCmd(dt, 'HIGH_PRES_FUEL_VALVE', 1)
	#pushSeqCmd(dt, '', '', "Engine Start switch - ON")
	pushSeqCmd(dt, 'START_SYSTEM', 1)
	pushSeqCmd(35, '', '', "Engine started, wait for systems to power up (25s)")
	pushSeqCmd(25, '', '', "Systems powered up")

	#pushSeqCmd(dt, '', '', "Oxygen / Suit air valve (SYRGAS) - ON")
	pushSeqCmd(dt, 'OXYGEN_LEVER', 1)

	#pushSeqCmd(dt, '', '', "LOADING DATA CARTRIDGE")
	#pushSeqCmd(dt, '', '', "Data Cartridge - REMOVE")
	pushSeqCmd(dt, 'DATA_CARTRIDGE', 0)
	pushSeqCmd(2, '', '', "Data Cartridge removed")
	#pushSeqCmd(dt, '', '', "Data Cartridge - INSERT")
	pushSeqCmd(dt, 'DATA_CARTRIDGE', 1)
	pushSeqCmd(2, '', '', "Data Cartridge inserted")
	
	#pushSeqCmd(dt, '', '', "Data selector knob - REF/LOLA, IN")
	pushSeqCmd(dt, 'DATAPANEL_SELECTOR', 5) # Datapanel selector knob, 0 = ID-NR, 1 = TAKT, 2 = TID, 3 = VIND RUTA MAL, 4 = BANA GRANS, 5 = REF LOLA, 6 = AKT POS
	pushSeqCmd(dt, 'DATA_IN_OUT', 1) # In/Out switch, 1 = IN, 2 = OUT
	#pushSeqCmd(dt, '', '', "Enter data - 9099, LS/SKU")
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
	#pushSeqCmd(dt, '', '', "Wait for cartridge to be read (7s)")
	pushSeqCmd(7, '', '', "Data loaded")
	#pushSeqCmd(dt, '', '', "Data selector knob - AKT/POS, OUT")
	pushSeqCmd(dt, 'DATAPANEL_SELECTOR', 6) # Datapanel selector knob, 0 = ID-NR, 1 = TAKT, 2 = TID, 3 = VIND RUTA MAL, 4 = BANA GRANS, 5 = REF LOLA, 6 = AKT POS
	pushSeqCmd(dt, 'DATA_IN_OUT', 0) # In/Out switch, 1 = IN, 2 = OUT

	#pushSeqCmd(dt, '', '', "Ejection seat - ARM")
	pushSeqCmd(dt, 'EJECTION_SEAT_ARM', 1)
	#pushSeqCmd(dt, '', '', "Master mode knob - NAV")
	pushSeqCmd(dt, 'MASTER_MODE_SELECT', 2) # 0 = FK, 1 = BER, 2 = NAV, 3 = ANF, 4 = SPA, 5 = LANDNING NAV, 6 = LANDNING PO
	#pushSeqCmd(dt, '', '', "Slav SI switch - F")
	pushSeqCmd(dt, 'SLAV_SI', 0) # 0 = F, 1 = T
	#pushSeqCmd(dt, '', '', "Parking brake - OFF")
	pushSeqCmd(dt, 'PARKING_BRAKE', 'TOGGLE') # FIXME This should work, but doesn't.  Brake must be released manually.
	pushSeqCmd(dt, 'scriptSpeech', 'Release parking brake.')

	return seq
