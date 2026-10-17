#!/usr/bin/env python3
"""Extract native control data from A-4E-C Skyhawk DCS community mod Lua files.

Self-contained extraction script that uses lupa to execute the A-4E-C's native
Lua files in a sandboxed environment.  Extracts: devices, command tables,
clickable elements, indicator definitions, text field names, and gauges/lamps.

Reads: A-4E-C/Cockpit/Scripts/ (clickabledata.lua, command_defs.lua,
       devices.lua, device_init.lua, sounds.lua, mainpanel_init.lua)
Writes: config/nativeExtractions/A-4E-C.json

Usage:
	python extract_A4EC.py [--mod-dir <path>] [--output <path>]

The --mod-dir flag overrides the default A-4E-C module path.  The default is:
	%USERPROFILE%/Saved Games/DCS/Mods/aircraft/A-4E-C

A-4E-C-specific notes:
  - This is a community free mod, located in Saved Games rather than the
    DCS install directory.  Use --mod-dir to override if installed elsewhere.
  - command_defs.lua defines TWO separate tables: Keys (hardcoded integers for
    global key/EFM commands) and device_commands (auto-incremented from 3000).
    Both are extracted.
  - devices.lua does not define a 'COMPASS' device, but clickabledata.lua
    references devices.COMPASS.  Those elements will have device=nil and are
    mostly unimplemented placeholders.
  - sounds.lua uses a local counter() (globals: TOGGLECLICK_*, KNOBCLICK_*, etc.)
    and is loaded via dofile() inside clickabledata.lua.
  - clickable_defs.lua defines several unique helpers not seen in other modules:
    inverted_3_position_tumb, springloaded_forward_only_3_pos_tumb,
    springloaded_aft_only_3_pos_tumb, default_button_axis (two separate args),
    default_movable_axis, multiposition_switch_limited_inverted, default_button_tumb.
  - default_button_axis controls (PNT_602, PNT_662, PNT_177, PNT_183, etc.) have
    post-construction property overrides (.relative, .arg_lim, .class, etc.);
    lupa captures the final state, so these are handled correctly.
  - Some elements have arg=nil (e.g. PNT_MIRROR_LEFT, PNT_129 canopy lever at
    arg=0).  These are included but will have empty arg lists.
"""

import argparse
import json
import os
import sys

import lupa

from extractUtils import (
	portableUserPath,
	luaTableToList,
	installCmdAccessLogger, uninstallCmdAccessLogger,
	installHelperTagger,
	readCmdAccessLog, readElementAccessSpans, deriveDeviceTableMap,
	extractSlaveAnimation,
	installEquipmentPropsMock,
	extractEquipmentProperties,
	extractIndicatorsFromLuaGlobals,
	extractTextFieldsLupa,
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

# Default A-4E-C mod path (Saved Games, not DCS install).
userProfile = os.environ.get('USERPROFILE', os.path.expanduser('~'))
defaultModDir = os.path.join(userProfile, 'Saved Games', 'DCS', 'Mods', 'aircraft', 'A-4E-C')

# Relative path from mod root to the Scripts directory.
scriptsRelPath = 'Cockpit/Scripts'


def luaValueToList(luaArrayOrVal):
	"""Convert a Lua table or single value to a Python list."""
	if luaArrayOrVal is None:
		return []
	if lupa.lua_type(luaArrayOrVal) == 'table':
		return luaTableToList(luaArrayOrVal)
	return [luaArrayOrVal]


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

	A-4E-C quirk: devices.COMPASS is not defined in devices.lua but is
	referenced in clickabledata.lua.  We do NOT pre-define it — those elements
	will have device=nil and the extractor handles nil devices gracefully.
	"""
	lua = lupa.LuaRuntime(unpack_returned_tuples=True)
	scriptsPath = scriptsDir.replace('\\', '/').rstrip('/') + '/'

	# Use a magic table for LockOn_Options so that any nested key access
	# (e.g. LockOn_Options.flight.padlock) auto-vivifies without raising an error.
	lua.execute(f'''
		local function magicTable()
			local mt
			mt = {{
				__index = function(t, k)
					local sub = setmetatable({{}}, mt)
					rawset(t, k, sub)
					return sub
				end,
				__lt = function() return false end,
				__le = function() return false end,
				__eq = function() return false end,
				__add = function() return 0 end,
				__sub = function() return 0 end,
				__mul = function() return 0 end,
				__div = function() return 0 end,
				__mod = function() return 0 end,
				__pow = function() return 0 end,
				__unm = function() return 0 end,
				__concat = function() return "" end,
				__tostring = function() return "" end,
				__len = function() return 0 end,
				__call = function() return nil end,
			}}
			return setmetatable({{}}, mt)
		end
		LockOn_Options = magicTable()
		LockOn_Options.script_path = "{scriptsPath}"
		LockOn_Options.common_script_path = "{scriptsPath}"
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

	# Mocks needed for mainpanel_init.lua (gauges and lamps).
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
	"""Extract all *_commands tables and the Keys table from Lua globals.

	A-4E-C has:
	  - Keys: hardcoded global key/EFM command integers (not device-specific)
	  - device_commands: auto-incremented from 3000 (all cockpit controls use this)

	Returns {tableName: {name: id}}.
	"""
	g = lua.globals()
	result = {}
	for key in g:
		keyStr = str(key)
		if keyStr == 'Keys' or keyStr.endswith('_commands'):
			table = g[key]
			if lupa.lua_type(table) != 'table':
				continue
			commands = {}
			allNumeric = True
			for name in table:
				val = table[name]
				if not isinstance(val, (int, float)):
					allNumeric = False
					break
				commands[str(name)] = int(val)
			if allNumeric and commands:
				result[keyStr] = commands
	return result


def extractElements(lua):
	"""Extract the clickable elements table -> {key: controlData}."""
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
		action = luaValueToList(element.action) if element.action else []
		arg = luaValueToList(element.arg) if element.arg else []
		argValue = luaValueToList(element.arg_value) if element.arg_value else []
		argLim = luaValueToList(element.arg_lim) if element.arg_lim else []
		classTypes = luaValueToList(element['class']) if element['class'] else []
		stopAction = luaValueToList(element.stop_action) if element.stop_action else []
		cycle = element.cycle if element.cycle is not None else None
		gain = luaValueToList(element.gain) if element.gain else []
		relative = luaValueToList(element.relative) if element.relative else []
		useReleaseMessage = luaValueToList(element.use_release_message) if element.use_release_message else []

		helperTag = element._helper

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
		if helperTag:
			controlData['helper'] = str(helperTag)

		slaveAnim = extractSlaveAnimation(element, len(action))
		if any(chain for chain in slaveAnim):
			controlData['slaveAnimation'] = slaveAnim

		controls[str(key)] = controlData

	return controls


def extractIndicators(lua, scriptsDir, devices):
	"""Extract indicators by executing device_init.lua via lupa."""
	deviceInitPath = os.path.join(scriptsDir, 'device_init.lua').replace('\\', '/')
	if not os.path.exists(deviceInitPath):
		print(f'Warning: {deviceInitPath} not found, skipping indicators', file=sys.stderr)
		return [], []

	lua.execute(f'dofile("{deviceInitPath}")')
	indicators = extractIndicatorsFromLuaGlobals(lua, scriptsDir, devices)
	equipmentProperties = extractEquipmentProperties(lua)
	return indicators, equipmentProperties


def extractGaugesAndLamps(lua, scriptsDir):
	"""Extract gauges and lamps by executing mainpanel_init.lua via lupa."""
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


def runExtraction(scriptsDir):
	"""Run the full A-4E-C extraction pipeline."""
	print(f'Extracting from: {scriptsDir}', file=sys.stderr)

	lua = createLuaRuntime(scriptsDir)
	clickableDataPath = os.path.join(scriptsDir, 'clickabledata.lua').replace('\\', '/')
	if not os.path.exists(clickableDataPath):
		print(f'Error: {clickableDataPath} not found', file=sys.stderr)
		sys.exit(1)

	installCmdAccessLogger(lua)
	installHelperTagger(lua)
	lua.execute(f'dofile("{clickableDataPath}")')

	accessLog = readCmdAccessLog(lua)
	elementSpans = readElementAccessSpans(lua)
	uninstallCmdAccessLogger(lua)

	devices = extractDevices(lua)
	commandTables = extractCommandTables(lua)
	elements = extractElements(lua)

	deviceTableMap = deriveDeviceTableMap(elements, accessLog, elementSpans)
	print(f'Deterministic device→table mappings: {len(deviceTableMap)}/{len(devices)} '
	      f'devices (from {len(accessLog)} logged accesses, {len(elementSpans)} element spans)',
	      file=sys.stderr)

	indicators, equipmentProperties = extractIndicators(lua, scriptsDir, devices)

	totalFields = 0
	for ind in indicators:
		fields = extractTextFieldsLupa(scriptsDir, ind['initFile'])
		ind['fields'] = fields
		totalFields += len(fields)

	gaugesAndLamps = extractGaugesAndLamps(lua, scriptsDir)

	inputDir = os.path.normpath(os.path.join(scriptsDir, '..', '..', 'Input'))
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
		'module': 'A-4E-C',
		'scriptsDir': portableUserPath(scriptsDir, userProfile),
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
	parser = argparse.ArgumentParser(description='Extract native control data from A-4E-C Skyhawk DCS community mod.')
	parser.add_argument(
		'--mod-dir',
		default=defaultModDir,
		help=f'A-4E-C module directory (default: {defaultModDir})',
	)
	parser.add_argument(
		'--output', '-o',
		help='Output JSON file path (default: config/nativeExtractions/A-4E-C.json)',
	)
	args = parser.parse_args()

	scriptsDir = os.path.join(args.mod_dir, scriptsRelPath)
	scriptsDir = os.path.abspath(scriptsDir)

	if not os.path.isdir(scriptsDir):
		print(f'Error: Scripts directory not found: {scriptsDir}', file=sys.stderr)
		print(f'Check that --mod-dir points to your A-4E-C mod directory.', file=sys.stderr)
		sys.exit(1)

	result = runExtraction(scriptsDir)

	if args.output:
		outputPath = args.output
	else:
		repoRoot = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
		outputPath = os.path.join(repoRoot, 'config', 'nativeExtractions', 'A-4E-C.json')

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
	print(f'Gauges/lamps: {stats["totalGaugesAndLamps"]}', file=sys.stderr)
	print(f'Keybindings: {stats["totalKeybindings"]}', file=sys.stderr)
	print(f'Listened commands: {stats["totalListenedCommands"]}', file=sys.stderr)


if __name__ == '__main__':
	main()
