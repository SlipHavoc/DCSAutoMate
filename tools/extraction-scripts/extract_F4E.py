#!/usr/bin/env python3
"""Extract native control data from F-4E Phantom II DCS module Lua files.

Self-contained extraction script that uses lupa to execute the F-4E's native
Lua files in a sandboxed environment.  Extracts: devices, command tables,
clickable elements, indicator definitions, text field names, and gauges/lamps.

Reads: F-4E/Cockpit/ (clickabledata.lua, clickable_dsl.lua, command_defs.lua,
       devices.lua, device_init.lua, draw_args.lua, sounds.lua,
       mainpanel_init.lua, indicator page files)
Writes: config/nativeExtractions/F-4E.json

Usage:
	python extract_F4E.py [--dcs-dir <path>] [--output <path>]

The --dcs-dir flag overrides the default DCS install path.  The default is:
	C:/Games/DCS World

The F-4E command architecture differs from most modules: instead of per-device
*_commands globals, it uses a single device_subcommands nested table (keyed by
device name) plus a device_commands metatable proxy that searches across all
sub-tables.  extractCommandTables() reads device_subcommands directly via lupa,
so the access logger (used by other extractors to infer device→table mapping) is
not needed — the mapping is exact by construction.
"""

import argparse
import json
import os
import sys

import lupa

from extractUtils import (
	luaTableToList,
	installHelperTagger,
	installEquipmentPropsMock, extractEquipmentProperties,
	extractIndicatorsFromLuaGlobals, extractTextFieldsLupa,
	extractKeybindings,
	extractListenedCommands,
)


# Map class_type integer values back to names.
classTypeNames = {
	0: 'BTN',
	1: 'TUMB',
	2: 'LEV',
	3: 'MOVABLE_LEV',
	4: 'BTN_FIX',
	5: 'MULTY_TUMB',
}

# Default DCS install path.
defaultDcsDir = 'C:/Games/DCS World'

# Relative path from DCS install root to the F-4E cockpit directory.
# Unlike FA-18C/AH-64D (Cockpit/Scripts/), F-4E has Lua files directly in Cockpit/.
scriptsRelPath = 'Mods/aircraft/F-4E/Cockpit'


def luaTableToDict(luaTable):
	"""Convert a Lua table (used as a dictionary) to a Python dict."""
	if luaTable is None:
		return {}
	result = {}
	for key in luaTable:
		val = luaTable[key]
		if lupa.lua_type(val) == 'table':
			val = luaTableToDict(val)
		result[str(key)] = val
	return result


def createLuaRuntime(scriptsDir):
	"""Create a Lua runtime with mocked DCS environment primitives.

	Provides enough of the DCS Lua environment to execute clickabledata.lua
	and device_init.lua.  Mocks all C++ engine functions that these files
	call so the Lua code runs to completion.
	"""
	lua = lupa.LuaRuntime(unpack_returned_tuples=True)
	scriptsPath = scriptsDir.replace('\\', '/').rstrip('/') + '/'

	lua.execute(f'''
		LockOn_Options = {{
			script_path = "{scriptsPath}",
			common_script_path = "{scriptsPath}",
			flight = {{ easy_radar = false, auto_lockon = false }},
		}}
	''')

	lua.execute('''
		class_type = {
			BTN = 0,
			TUMB = 1,
			LEV = 2,
			MOVABLE_LEV = 3,
			BTN_FIX = 4,
			MULTY_TUMB = 5,
		}
	''')

	lua.execute('''
		BOX_SIDE_X_top = 1
		BOX_SIDE_X_bottom = 2
		BOX_SIDE_Y_top = 3
		BOX_SIDE_Y_bottom = 4
		BOX_SIDE_Z_top = 5
		BOX_SIDE_Z_bottom = 6
	''')

	lua.execute('''
		function get_option_value(key, scope)
			return false
		end
	''')

	lua.execute('''
		local realRequire = require
		function require(modName)
			if modName == "i_18n" then
				return { translate = function(s) return s end }
			end
			return realRequire(modName)
		end
	''')

	lua.execute('''
		local originalDofile = dofile
		function dofile(path)
			local f, err = loadfile(path)
			if f then
				local ok, result = pcall(f)
				if ok then
					return result
				else
					io.stderr:write("Warning: Error executing " .. tostring(path) .. ": " .. tostring(result) .. "\\n")
				end
			else
				io.stderr:write("Warning: Could not load " .. tostring(path) .. ": " .. tostring(err) .. "\\n")
			end
		end
	''')

	# Mocks needed for device_init.lua execution.
	lua.execute('''
		function mount_vfs_model_path() end
		function mount_vfs_texture_path() end
		function mount_vfs_liveries_path() end
		function mount_vfs_texture_archives() end
		function writeParameter() end

		function get_param_handle(name)
			return { set = function(self, val) end, get = function(self) return 0 end }
		end

		function get_aircraft_property_or_nil(name)
			return nil
		end

		render_purpose = { GENERAL = 0, BAKE = 1, HUD_ONLY_VIEW = 2, SCREENSPACE = 3 }
		indicator_types = { COMMON = 0 }

		function update_screenspace_displacement() end
		function try_find_assigned_viewport() return nil end
		function Copy(t) return t end

		kneeboard_implementation = ""
		disable_kneeboard_render_target = false
	''')

	# Mocks needed for indicator init files (devices_defs.lua content).
	lua.execute('''
		function create_material_type_table()
			return setmetatable({}, { __index = function(t, k)
				rawset(t, k, k)
				return k
			end })
		end

		function set_material_type(name, mtype) end

		function clear_mode_table(t, l1, l2, l3)
			for i = 1, l1 do
				t[i] = {}
				for j = 1, l2 do
					t[i][j] = {}
					for k = 1, l3 do
						t[i][j][k] = {}
					end
				end
			end
		end

		function get_page_by_mode_global(pages_by_mode, init_pageID, master, L2, L3, L4)
			return init_pageID
		end
	''')

	# Mocks needed for mainpanel_init.lua execution (gauges and lamps).
	lua.execute('''
		function get_aircraft_type() return '' end
	''')

	# Mocks for indicator/page scripts that call DCS engine functions.
	lua.execute('''
		local _guidCounter = 0
		function create_guid_string()
			_guidCounter = _guidCounter + 1
			return 'guid-' .. tostring(_guidCounter)
		end
	''')

	lua.execute('''
		_extractedGauges = {}
		_gaugeCounter = 0
		function CreateGauge(optArg)
			_gaugeCounter = _gaugeCounter + 1
			local g = { _gaugeId = _gaugeCounter }
			_extractedGauges[_gaugeCounter] = g
			return g
		end

		function LoRegisterPanelControls()
			return setmetatable({}, { __index = function(t, k)
				t[k] = k
				return k
			end })
		end

		SnapViews = { [1] = { [1] = { vAngle = 0, x_trans = 0, y_trans = 0, z_trans = 0 }, [13] = { vAngle = 0, x_trans = 0, y_trans = 0, z_trans = 0 } } }
		ViewSettings = { Cockpit = { [1] = { EyePoint = { [1] = 0 } } } }

		function find_custom_livery(name, default) return "" end
	''')

	# Execute sounds.lua to define SOUND_* and NONE constants before clickable_dsl.lua needs them.
	soundsPath = os.path.join(scriptsDir, 'sounds.lua').replace('\\', '/')
	if os.path.exists(soundsPath):
		lua.execute(f'dofile("{soundsPath}")')
	else:
		print(f'Warning: {soundsPath} not found, SOUND constants may be undefined', file=sys.stderr)

	# Safety fallback: clickable_dsl.lua uses NONE as a sound constant; define it if sounds.lua
	# didn't already do so.
	lua.execute('''
		if NONE == nil then NONE = 0 end
	''')

	installEquipmentPropsMock(lua)
	return lua


def extractDevices(lua):
	"""Extract devices table -> {name: id}."""
	devices = lua.globals().devices
	if devices is None:
		return {}
	result = {}
	for key in devices:
		result[str(key)] = int(devices[key])
	return result


def extractCommandTables(lua):
	"""Extract device_subcommands -> {deviceName: {cmdName: id}}.

	The F-4E uses a device_subcommands nested Lua table (keyed by device name)
	rather than per-device *_commands globals.  A device_commands metatable proxy
	allows elements in clickabledata.lua to reference commands without knowing
	which device owns them, but device_subcommands is the canonical source.

	We read device_subcommands directly via lupa, so the device→table mapping is
	exact by construction (no access logger or name-similarity heuristic needed).
	"""
	g = lua.globals()
	deviceSubcmds = g._f4eDeviceSubcmds
	if deviceSubcmds is None:
		print('Warning: _f4eDeviceSubcmds not captured — command tables will be empty', file=sys.stderr)
		return {}

	result = {}
	for deviceName in deviceSubcmds:
		deviceNameStr = str(deviceName)
		subTable = deviceSubcmds[deviceName]
		if lupa.lua_type(subTable) != 'table':
			continue
		commands = {}
		for cmdName in subTable:
			val = subTable[cmdName]
			if isinstance(val, (int, float)):
				commands[str(cmdName)] = int(val)
		if commands:
			result[deviceNameStr] = commands
	return result


def extractElements(lua):
	"""Extract the clickable elements table -> {key: controlData}.

	F-4E elements include crew_member_access for pilot/WSO distinction.
	"""
	elements = lua.globals().elements
	if elements is None:
		return {}

	controls = {}
	for key in elements:
		element = elements[key]
		if lupa.lua_type(element) != 'table':
			continue

		hint = element.hint
		device = element.device
		action = luaTableToList(element.action) if element.action else []
		arg = luaTableToList(element.arg) if element.arg else []
		argValue = luaTableToList(element.arg_value) if element.arg_value else []
		argLim = luaTableToList(element.arg_lim) if element.arg_lim else []
		classTypes = luaTableToList(element['class']) if element['class'] else []
		stopAction = luaTableToList(element.stop_action) if element.stop_action else []
		cycle = element.cycle if element.cycle is not None else None
		gain = luaTableToList(element.gain) if element.gain else []
		relative = luaTableToList(element.relative) if element.relative else []
		useReleaseMessage = luaTableToList(element.use_release_message) if element.use_release_message else []
		helperTag = element._helper

		# F-4E specific: crew_member_access is a Lua table like {0} (pilot), {1} (WSO), or {0,1} (both).
		crewAccess = luaTableToList(element.crew_member_access) if element.crew_member_access else []

		classNames = [classTypeNames.get(int(c), str(c)) if c is not None else None for c in classTypes]

		if device is not None:
			device = int(device)
		action = [int(a) for a in action if a is not None]
		arg = [int(a) if a is not None else 0 for a in arg]
		argValue = [float(v) for v in argValue if v is not None]

		processedArgLim = []
		for lim in argLim:
			if isinstance(lim, list) and len(lim) == 2:
				processedArgLim.append([float(lim[0]), float(lim[1])])
			elif isinstance(lim, (int, float)):
				processedArgLim.append(float(lim))
			else:
				processedArgLim.append(lim)
		argLim = processedArgLim

		gain = [float(g) if g is not None else None for g in gain]
		relative = [bool(r) for r in relative]

		if cycle is not None and lupa.lua_type(cycle) == 'table':
			cycle = [bool(v) for v in luaTableToList(cycle)]

		controlData = {
			'hint': str(hint) if hint else '',
			'device': device,
			'action': action,
			'arg': arg,
			'argValue': argValue,
			'argLim': argLim,
			'controlClass': classNames,
		}

		if stopAction:
			controlData['stopAction'] = [int(a) if a is not None else 0 for a in stopAction]
		if cycle is not None:
			controlData['cycle'] = cycle
		if gain:
			controlData['gain'] = gain
		if relative:
			controlData['relative'] = relative
		if useReleaseMessage:
			controlData['useReleaseMessage'] = [bool(u) for u in useReleaseMessage]
		if crewAccess:
			controlData['crewAccess'] = [int(c) for c in crewAccess]
		if helperTag:
			controlData['helper'] = str(helperTag)

		controls[str(key)] = controlData

	return controls


def extractIndicators(lua, scriptsDir, devices):
	"""Extract indicators by executing device_init.lua via lupa.

	Returns a list of indicator dicts with 0-based indication IDs.
	"""
	deviceInitPath = os.path.join(scriptsDir, 'device_init.lua').replace('\\', '/')
	if not os.path.exists(deviceInitPath):
		print(f'Warning: {deviceInitPath} not found, skipping indicators', file=sys.stderr)
		return [], []

	lua.execute(f'dofile("{deviceInitPath}")')
	indicators = extractIndicatorsFromLuaGlobals(lua, scriptsDir, devices)
	equipmentProperties = extractEquipmentProperties(lua)
	return indicators, equipmentProperties


def extractGaugesAndLamps(lua, scriptsDir):
	"""Extract gauges and lamps by executing mainpanel_init.lua via lupa.

	Returns a list of gauge dicts.
	"""
	mainpanelPath = os.path.join(scriptsDir, 'mainpanel_init.lua').replace('\\', '/')
	if not os.path.exists(mainpanelPath):
		print(f'Warning: {mainpanelPath} not found, skipping gauges/lamps', file=sys.stderr)
		return []

	lua.execute(f'dofile("{mainpanelPath}")')

	g = lua.globals()

	# Build gaugeId -> global variable name map.
	namedGauges = {}
	for key in g:
		val = g[key]
		if lupa.lua_type(val) == 'table':
			gaugeId = val['_gaugeId']
			if gaugeId is not None and isinstance(gaugeId, (int, float)):
				namedGauges[int(gaugeId)] = str(key)

	# Build reverse maps for Warning_Lights and Cabin_Lights enum tables.
	warningLightsReverse = {}
	warningLights = g.Warning_Lights
	if warningLights and lupa.lua_type(warningLights) == 'table':
		for name in warningLights:
			warningLightsReverse[int(warningLights[name])] = str(name)

	cabinLightsReverse = {}
	cabinLights = g.Cabin_Lights
	if cabinLights and lupa.lua_type(cabinLights) == 'table':
		for name in cabinLights:
			cabinLightsReverse[int(cabinLights[name])] = str(name)

	extractedGauges = g._extractedGauges
	result = []
	i = 1
	while True:
		gauge = extractedGauges[i]
		if gauge is None:
			break

		argNumber = gauge.arg_number
		if argNumber is None:
			i += 1
			continue

		argNumber = int(argNumber)
		gaugeId = int(gauge['_gaugeId'])

		if gaugeId in namedGauges:
			name = namedGauges[gaugeId]
		else:
			controller = gauge.controller
			params = gauge.params
			paramVal = None
			if params and lupa.lua_type(params) == 'table':
				paramVal = params[1]
				if paramVal is not None:
					paramVal = int(paramVal)

			if controller == 'WarningLights' and paramVal is not None and paramVal in warningLightsReverse:
				name = warningLightsReverse[paramVal]
			elif controller == 'CockpitLights' and paramVal is not None and paramVal in cabinLightsReverse:
				name = cabinLightsReverse[paramVal]
			else:
				name = f'gauge_arg_{argNumber}'

		entry = {
			'name': name,
			'arg': argNumber,
		}

		if gauge.input:
			entry['input'] = luaTableToList(gauge.input)
		if gauge.output:
			entry['output'] = luaTableToList(gauge.output)
		externalArg = gauge.external_arg
		if externalArg is not None:
			entry['externalArg'] = int(externalArg)
		if gauge.controller:
			entry['controller'] = str(gauge.controller)
		if gauge.params and lupa.lua_type(gauge.params) == 'table':
			entry['params'] = luaTableToList(gauge.params)

		result.append(entry)
		i += 1

	return result


def extractDrawArgs(lua, scriptsDir, existingArgNums):
	"""Extract cockpit_args constants from draw_args.lua as read-only gauge entries.

	Only reads the cockpit_args table (external_args uses the same integers for
	different external-model purposes and is not relevant to cockpit state polling).
	Returns a list of {"name": str, "arg": int} dicts sorted by arg number,
	skipping any arg values already present in existingArgNums (to avoid duplicating
	mainpanel_init gauges).
	"""
	g = lua.globals()

	# draw_args.lua is usually already loaded transitively by clickabledata.lua;
	# only execute it explicitly if the table isn't in scope yet.
	if lupa.lua_type(g.cockpit_args) != 'table':
		drawArgsPath = os.path.join(scriptsDir, 'draw_args.lua').replace('\\', '/')
		if not os.path.exists(drawArgsPath):
			print(f'Warning: {drawArgsPath} not found, skipping draw_args', file=sys.stderr)
			return []
		lua.execute(f'dofile("{drawArgsPath}")')

	tbl = g.cockpit_args
	result = []
	for name in tbl:
		val = tbl[name]
		if isinstance(val, (int, float)) and int(val) not in existingArgNums:
			result.append({'name': str(name), 'arg': int(val)})

	result.sort(key=lambda e: e['arg'])
	return result


def runExtraction(scriptsDir):
	"""Run the full F-4E extraction pipeline."""
	print(f'Extracting from: {scriptsDir}', file=sys.stderr)

	lua = createLuaRuntime(scriptsDir)
	clickableDataPath = os.path.join(scriptsDir, 'clickabledata.lua').replace('\\', '/')
	if not os.path.exists(clickableDataPath):
		print(f'Error: {clickableDataPath} not found', file=sys.stderr)
		sys.exit(1)

	# No access logger needed: F-4E uses device_subcommands (read directly in
	# extractCommandTables), so device→table mapping is exact without runtime logging.
	installHelperTagger(lua)
	lua.execute(f'dofile("{clickableDataPath}")')

	# device_subcommands is local to command_defs.lua (which clickabledata.lua dofile-loads).
	# Recover it from the closure upvalue of device_commands.__index via debug.getupvalue.
	lua.execute('''
		_f4eDeviceSubcmds = nil
		if device_commands then
			local mt = getmetatable(device_commands)
			if mt then
				local indexFn = rawget(mt, '__index')
				if type(indexFn) == 'function' then
					local i = 1
					while true do
						local name, val = debug.getupvalue(indexFn, i)
						if name == nil then break end
						if name == 'device_subcommands' then
							_f4eDeviceSubcmds = val
							break
						end
						i = i + 1
					end
				end
			end
		end
		if _f4eDeviceSubcmds == nil then
			io.stderr:write([[Warning: Could not capture device_subcommands via debug.getupvalue]] .. "\\n")
		end
	''')

	devices = extractDevices(lua)
	commandTables = extractCommandTables(lua)
	elements = extractElements(lua)

	# Build deviceTableMap directly from device_subcommands keys.  Each key in
	# commandTables is a device name that matches a devices.lua entry exactly.
	# Devices absent from device_subcommands (pure indicator/display devices) are
	# omitted; the generator falls back to its name-similarity heuristic for those.
	devIdByName = {name: devId for name, devId in devices.items()}
	deviceTableMap = {}
	for tableName in commandTables:
		devId = devIdByName.get(tableName)
		if devId is not None:
			deviceTableMap[str(devId)] = tableName
	print(f'Deterministic device→table mappings: {len(deviceTableMap)}/{len(devices)} devices', file=sys.stderr)

	indicators, equipmentProperties = extractIndicators(lua, scriptsDir, devices)

	# F-4E indicator pages use create_guid_string (a DCS engine function) and call
	# GetRenderTarget() as a plain number rather than the table that the shared sandbox
	# returns.  Pass these overrides to every extractTextFieldsLupa call.
	f4eExtraSetup = '''
		local _guidCtr = 0
		function create_guid_string()
			_guidCtr = _guidCtr + 1
			return 'guid-' .. tostring(_guidCtr)
		end
		function GetRenderTarget() return 0 end
		function SetRenderTarget(x) end
	'''

	totalFields = 0
	for ind in indicators:
		fields = extractTextFieldsLupa(scriptsDir, ind['initFile'], f4eExtraSetup)
		ind['fields'] = fields
		totalFields += len(fields)

	gaugesAndLamps = extractGaugesAndLamps(lua, scriptsDir)
	existingArgNums = {entry['arg'] for entry in gaugesAndLamps}
	drawArgsEntries = extractDrawArgs(lua, scriptsDir, existingArgNums)
	gaugesAndLamps.extend(drawArgsEntries)
	print(f'Draw args extracted: {len(drawArgsEntries)} (total gaugesAndLamps: {len(gaugesAndLamps)})', file=sys.stderr)

	inputDir = os.path.normpath(os.path.join(scriptsDir, '..', 'Input'))
	keybindings, keybindingFailures = extractKeybindings(inputDir)
	for source, message in keybindingFailures:
		print(f'Warning: keybinding file {source} failed: {message}', file=sys.stderr)

	listenedCommands, listenFailures = extractListenedCommands(lua, scriptsDir)
	for source, message in listenFailures:
		print(f'Warning: device script {source} failed: {message}', file=sys.stderr)

	stats = {
		'totalElements': len(elements),
		'totalDevices': len(devices),
		'totalCommandTables': len(commandTables),
		'totalIndicators': len(indicators),
		'totalIndicationFields': totalFields,
		'totalGaugesAndLamps': len(gaugesAndLamps),
		'totalKeybindings': len(keybindings),
		'totalListenedCommands': len(listenedCommands),
	}

	return {
		'module': 'F-4E-45MC',
		'scriptsDir': scriptsDir,
		'devices': devices,
		'commandTables': commandTables,
		'deviceTableMap': deviceTableMap,
		'elements': elements,
		'indicators': indicators,
		'equipmentProperties': equipmentProperties,
		'gaugesAndLamps': gaugesAndLamps,
		'keybindings': keybindings,
		'listenedCommands': listenedCommands,
		'stats': stats,
	}


def main():
	parser = argparse.ArgumentParser(description='Extract native control data from F-4E Phantom II DCS module.')
	parser.add_argument('--dcs-dir', default=defaultDcsDir, help=f'DCS World install directory (default: {defaultDcsDir})')
	parser.add_argument('--output', '-o', help='Output JSON file path (default: config/nativeExtractions/F-4E.json)')
	args = parser.parse_args()

	scriptsDir = os.path.join(args.dcs_dir, scriptsRelPath)
	scriptsDir = os.path.abspath(scriptsDir)

	if not os.path.isdir(scriptsDir):
		print(f'Error: Scripts directory not found: {scriptsDir}', file=sys.stderr)
		print(f'Check that --dcs-dir points to your DCS World install.', file=sys.stderr)
		sys.exit(1)

	result = runExtraction(scriptsDir)

	if args.output:
		outputPath = args.output
	else:
		repoRoot = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
		outputPath = os.path.join(repoRoot, 'config', 'nativeExtractions', 'F-4E.json')

	os.makedirs(os.path.dirname(outputPath), exist_ok=True)

	with open(outputPath, 'w', encoding='utf-8') as f:
		json.dump(result, f, indent='\t', ensure_ascii=False, sort_keys=True)

	stats = result['stats']
	print(f'Wrote: {outputPath}', file=sys.stderr)
	print(f'Devices: {stats["totalDevices"]}', file=sys.stderr)
	print(f'Command tables: {stats["totalCommandTables"]}', file=sys.stderr)
	print(f'Elements: {stats["totalElements"]}', file=sys.stderr)
	print(f'Indicators: {stats["totalIndicators"]}', file=sys.stderr)
	print(f'Indication fields: {stats["totalIndicationFields"]}', file=sys.stderr)
	print(f'Gauges and lamps: {stats["totalGaugesAndLamps"]}', file=sys.stderr)
	print(f'Keybindings: {stats["totalKeybindings"]}', file=sys.stderr)
	print(f'Listened commands: {stats["totalListenedCommands"]}', file=sys.stderr)


if __name__ == '__main__':
	main()
