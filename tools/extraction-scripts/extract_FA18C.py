#!/usr/bin/env python3
"""Extract native control data from FA-18C Hornet DCS module Lua files.

Self-contained extraction script that uses lupa to execute the FA-18C's native
Lua files in a sandboxed environment.  Extracts: devices, command tables,
clickable elements, indicator definitions, text field names, and gauges/lamps.

Reads: FA-18C/Cockpit/Scripts/ (clickabledata.lua, command_defs.lua,
       devices.lua, device_init.lua, config.lua, indicator page files,
       mainpanel_init.lua, MainPanel/lamps.lua)
Writes: config/nativeExtractions/FA-18C.json

Usage:
	python extract_FA18C.py [--dcs-dir <path>] [--output <path>]

The --dcs-dir flag overrides the default DCS install path.  The default is:
	C:/Games/DCS World
"""

import argparse
import json
import os
import sys

import lupa

from extractUtils import (
	luaTableToList,
	installCmdAccessLogger, uninstallCmdAccessLogger,
	installHelperTagger,
	readCmdAccessLog, readElementAccessSpans, deriveDeviceTableMap,
	installEquipmentPropsMock,
	extractEquipmentProperties,
	extractIndicatorsFromLuaGlobals,
	extractTextFieldsLupa,
	extractKeybindings,
	extractListenedCommands,
	installLampEnumLogger,
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

# Relative path from DCS install root to the FA-18C scripts directory.
scriptsRelPath = 'Mods/aircraft/FA-18C/Cockpit/Scripts'


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
	call (mount_vfs_model_path, get_param_handle, get_aircraft_property_or_nil,
	etc.) so the Lua code runs to completion.
	"""
	lua = lupa.LuaRuntime(unpack_returned_tuples=True)
	scriptsPath = scriptsDir.replace('\\', '/').rstrip('/') + '/'

	lua.execute(f'''
		LockOn_Options = {{
			script_path = "{scriptsPath}",
			common_script_path = "{scriptsPath}",
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

		-- get_param_handle returns a stub object with :set() and :get().
		function get_param_handle(name)
			return { set = function(self, val) end, get = function(self) return 0 end }
		end

		-- get_aircraft_property_or_nil: return nil (default config).
		-- For FA-18C, nil → helmet_option defaults to 1 (HMS).
		function get_aircraft_property_or_nil(name)
			return nil
		end

		-- Rendering constants used in device_init.lua.
		render_purpose = { GENERAL = 0, BAKE = 1, HUD_ONLY_VIEW = 2, SCREENSPACE = 3 }
		indicator_types = { COMMON = 0 }

		-- No-op stubs for display-related functions.
		function update_screenspace_displacement() end
		function try_find_assigned_viewport() return nil end
		function Copy(t) return t end

		-- Kneeboard/padlock globals that may be set before dofile.
		kneeboard_implementation = ""
		disable_kneeboard_render_target = false
	''')

	# Mocks needed for mainpanel_init.lua execution (gauges and lamps).
	lua.execute('''
		-- CreateGauge mock: collects all created gauge tables for later extraction.
		_extractedGauges = {}
		_gaugeCounter = 0
		function CreateGauge(optArg)
			_gaugeCounter = _gaugeCounter + 1
			local g = { _gaugeId = _gaugeCounter }
			_extractedGauges[_gaugeCounter] = g
			return g
		end

		-- LoRegisterPanelControls: returns table that maps key access to key name string.
		-- E.g. controllers.WCALights returns "WCALights", allowing us to identify controller types.
		function LoRegisterPanelControls()
			return setmetatable({}, { __index = function(t, k)
				t[k] = k
				return k
			end })
		end

		-- SnapViews / ViewSettings: fallback stubs for camera math at top of mainpanel_init.lua.
		-- If Views.lua loads successfully via dofile, these get overwritten with real values.
		SnapViews = { [1] = { [13] = { vAngle = 0, x_trans = 0, y_trans = 0, z_trans = 0 } } }
		ViewSettings = { Cockpit = { [1] = { EyePoint = { [1] = 0 } } } }

		-- find_custom_livery: called at end of mainpanel_init.lua via tools.lua.
		function find_custom_livery(name, default) return "" end
	''')

	installEquipmentPropsMock(lua)

	return lua


def extractDevices(lua):
	"""Extract devices table → {name: id}."""
	devices = lua.globals().devices
	if devices is None:
		return {}
	result = {}
	for key in devices:
		result[str(key)] = int(devices[key])
	return result


def extractCommandTables(lua):
	"""Extract all *_commands tables from Lua globals → {tableName: {name: id}}.

	After clickabledata.lua executes (which dofile's command_defs.lua), all
	command tables are available as globals.  We detect them by looking for
	tables whose name ends in '_commands' and whose values are all integers.
	"""
	g = lua.globals()
	result = {}
	for key in g:
		keyStr = str(key)
		if not keyStr.endswith('_commands'):
			continue
		table = g[key]
		if lupa.lua_type(table) != 'table':
			continue
		# Verify all values are integers.
		commands = {}
		allInts = True
		for name in table:
			val = table[name]
			if not isinstance(val, (int, float)):
				allInts = False
				break
			commands[str(name)] = int(val)
		if allInts and commands:
			result[keyStr] = commands
	return result


def extractElements(lua):
	"""Extract the clickable elements table → {key: controlData}."""
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

		controls[str(key)] = controlData

	return controls


def extractIndicators(lua, scriptsDir, devices):
	"""Extract indicators by executing device_init.lua via lupa.

	Executes device_init.lua in the same Lua runtime (after clickabledata.lua
	has already populated devices and commands).  Reads the resulting
	indicators[] global table.

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

	mainpanel_init.lua defines cockpit animation gauges and dofiles lamps.lua
	which defines caution/warning lamps.  Both use CreateGauge() internally,
	which our mock collects into _extractedGauges.

	Named globals (e.g. Canopy, StickPitch) are identified by scanning Lua
	globals for tables with a _gaugeId field.  Anonymous gauges (e.g. from
	create_caution_lamp calls whose return values are discarded) are named
	by reverse-mapping their params against the CautionLights or
	InternalLights enum tables.

	Returns a list of gauge dicts.
	"""
	mainpanelPath = os.path.join(scriptsDir, 'mainpanel_init.lua').replace('\\', '/')
	if not os.path.exists(mainpanelPath):
		print(f'Warning: {mainpanelPath} not found, skipping gauges/lamps', file=sys.stderr)
		return []

	# Install enum logger before dofile so counter-pattern tables defined in
	# lamps.lua are intercepted and their member accesses recorded on each gauge.
	installLampEnumLogger(lua)
	lua.execute(f'dofile("{mainpanelPath}")')

	g = lua.globals()

	# Build gaugeId -> global variable name map by scanning all globals.
	namedGauges = {}
	for key in g:
		val = g[key]
		if lupa.lua_type(val) == 'table':
			gaugeId = val['_gaugeId']
			if gaugeId is not None and isinstance(gaugeId, (int, float)):
				namedGauges[int(gaugeId)] = str(key)

	# First pass: collect all candidate names to detect within-table duplicates
	# (e.g. multiple args sharing a sentinel enum value like LIGHTS_MAX).
	# Duplicates fall back to gauge_arg_N so no key is silently lost.
	extractedGauges = g._extractedGauges
	candidateNames = {}  # gaugeId -> candidate name (before duplicate check)
	i = 1
	while True:
		gauge = extractedGauges[i]
		if gauge is None:
			break
		argNumber = gauge.arg_number
		if argNumber is not None:
			gaugeId = int(gauge['_gaugeId'])
			if gaugeId in namedGauges:
				candidateNames[gaugeId] = namedGauges[gaugeId]
			else:
				enumSource = gauge._enumSource
				if enumSource is not None:
					candidateNames[gaugeId] = str(enumSource)
				else:
					candidateNames[gaugeId] = f'gauge_arg_{int(argNumber)}'
		i += 1

	# Find names that appear more than once (duplicates must fall back).
	from collections import Counter
	nameCounts = Counter(candidateNames.values())
	duplicateNames = {n for n, c in nameCounts.items() if c > 1}

	# Second pass: build result, substituting gauge_arg_N for duplicates.
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

		name = candidateNames[gaugeId]
		if name in duplicateNames:
			name = f'gauge_arg_{argNumber}'

		# Build entry.
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
	"""Run the full FA-18C extraction pipeline."""
	print(f'Extracting from: {scriptsDir}', file=sys.stderr)

	# Step 1: Execute clickabledata.lua via lupa (loads devices, commands, elements).
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

	# Step 2: Extract structured data from Lua state.
	devices = extractDevices(lua)
	commandTables = extractCommandTables(lua)
	elements = extractElements(lua)

	deviceTableMap = deriveDeviceTableMap(elements, accessLog, elementSpans)
	print(f'Deterministic device→table mappings: {len(deviceTableMap)}/{len(devices)} '
	      f'devices (from {len(accessLog)} logged accesses, {len(elementSpans)} element spans)',
	      file=sys.stderr)

	# Step 3: Execute device_init.lua via lupa to extract indicators.
	indicators, equipmentProperties = extractIndicators(lua, scriptsDir, devices)

	# Step 4: For each indicator, extract text fields from its page files.
	totalFields = 0
	for ind in indicators:
		fields = extractTextFieldsLupa(scriptsDir, ind['initFile'])
		ind['fields'] = fields
		totalFields += len(fields)

	# Step 5: Execute mainpanel_init.lua via lupa to extract gauges and lamps.
	gaugesAndLamps = extractGaugesAndLamps(lua, scriptsDir)

	# Step 6: Execute the Input/ keybinding files via lupa.
	inputDir = os.path.normpath(os.path.join(scriptsDir, '..', '..', 'Input'))
	keybindings, keybindingFailures = extractKeybindings(inputDir)
	for source, message in keybindingFailures:
		print(f'Warning: keybinding file {source} failed: {message}', file=sys.stderr)

	# Step 7: Capture listen_command() registrations from scripted devices.
	listenedCommands, listenFailures = extractListenedCommands(lua, scriptsDir)
	for source, message in listenFailures:
		print(f'Warning: device script {source} failed: {message}', file=sys.stderr)

	# Build stats.
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
		'module': 'FA-18C_hornet',
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
	parser = argparse.ArgumentParser(description='Extract native control data from FA-18C Hornet DCS module.')
	parser.add_argument('--dcs-dir', default=defaultDcsDir, help=f'DCS World install directory (default: {defaultDcsDir})')
	parser.add_argument('--output', '-o', help='Output JSON file path (default: config/nativeExtractions/FA-18C.json)')
	args = parser.parse_args()

	scriptsDir = os.path.join(args.dcs_dir, scriptsRelPath)
	scriptsDir = os.path.abspath(scriptsDir)

	if not os.path.isdir(scriptsDir):
		print(f'Error: Scripts directory not found: {scriptsDir}', file=sys.stderr)
		print(f'Check that --dcs-dir points to your DCS World install.', file=sys.stderr)
		sys.exit(1)

	result = runExtraction(scriptsDir)

	# Default output path is relative to this script's repo root.
	if args.output:
		outputPath = args.output
	else:
		repoRoot = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
		outputPath = os.path.join(repoRoot, 'config', 'nativeExtractions', 'FA-18C.json')

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
