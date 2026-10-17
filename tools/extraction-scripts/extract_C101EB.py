#!/usr/bin/env python3
"""Extract native control data from C-101EB Aviojet DCS module Lua files.

Self-contained extraction script that uses lupa to execute the C-101EB's native
Lua files in a sandboxed environment.  Extracts: devices, command tables,
clickable elements, indicator definitions, and text field names.

The C-101 module has a two-variant architecture:
  - Cockpit/Common/        — shared devices, command defs, helper functions, elements
  - Cockpit/C-101CC/       — CC-specific devices (radios/nav), CC-specific elements
  - Cockpit/C-101EB/       — EB-specific devices (ARC134, ARC164, ARN118, ARN127)

The dofile chain rooted at C-101EB/clickabledata.lua pulls in Common/ automatically,
so pointing scriptsDir at C-101EB/ and dofile'ing clickabledata.lua is sufficient.

Reads: C-101/Cockpit/C-101EB/ and C-101/Cockpit/Common/
  Key files: clickabledata.lua, devices.lua, device_init.lua, mainpanel_init.lua,
             Common/clickabledata_common.lua, Common/command_defs.lua,
             Common/devices_common.lua, Common/sounds_common.lua
Writes: config/nativeExtractions/C-101EB.json

Usage:
	python extract_C101EB.py [--dcs-dir <path>] [--output <path>]

The --dcs-dir flag overrides the default DCS install path.  The default is:
	C:/Games/DCS World
"""

import argparse
import gettext
import json
import os
import sys

import lupa

from extractUtils import (
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

# Default DCS install path.
defaultDcsDir = 'C:/Games/DCS World'

# Relative path from DCS install root to the C-101EB scripts directory.
scriptsRelPath = 'Mods/aircraft/C-101/Cockpit/C-101EB'


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

	C-101-specific notes:
	  - LockOn_Options.script_path points at C-101EB/ so that dofiles
	    using '../Common/...' resolve correctly to the shared Common/ dir.
	  - _LAST_CLICK_SOUND_ must be pre-seeded as 0 because Common/sounds_common.lua
	    initialises its counter with that global before defining SOUND_* constants.
	"""
	lua = lupa.LuaRuntime(unpack_returned_tuples=True)
	scriptsPath = scriptsDir.replace('\\', '/').rstrip('/') + '/'

	# Use a magic table for LockOn_Options so that any nested key access
	# auto-vivifies without raising an error.
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

		function get_livery_setting_from_plugin(module, list, default)
			return default or ""
		end
	''')

	# Mocks for indicator / mainpanel init files.
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

	# Mocks needed for mainpanel_init.lua (gauges).
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

	# C-101-specific: seed _LAST_CLICK_SOUND_ before Common/sounds_common.lua runs.
	# sounds_common.lua does `local count = _LAST_CLICK_SOUND_` to initialise its
	# sound-ID counter; without this mock it gets nil and arithmetic fails.
	lua.execute('_LAST_CLICK_SOUND_ = 0')

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
	"""Extract all *_commands tables from Lua globals.

	C-101 uses a single shared device_commands table (Button_1..Button_999,
	base 3000) for all devices in both variants.

	Returns {tableName: {name: id}}.
	"""
	g = lua.globals()
	result = {}
	for key in g:
		keyStr = str(key)
		if keyStr.endswith('_commands'):
			table = g[key]
			if lupa.lua_type(table) != 'table':
				continue
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
	"""Extract gauges by executing mainpanel_init.lua via lupa.

	The active C-101 gauges are PilotBody, InstructorBody, FrontSeat, BackSeat —
	all assigned to named globals.  Names are discovered from the global table
	by matching _gaugeId fields, following the same pattern as other extractors.
	"""
	mainpanelPath = os.path.join(scriptsDir, 'mainpanel_init.lua').replace('\\', '/')
	if not os.path.exists(mainpanelPath):
		print(f'Warning: {mainpanelPath} not found, skipping gauges/lamps', file=sys.stderr)
		return []

	lua.execute(f'dofile("{mainpanelPath}")')

	g = lua.globals()

	# Build gaugeId → global variable name map.
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
		if argNumber is not None:
			argNumber = int(argNumber)
			gaugeId = int(gauge['_gaugeId'])
			name = namedGauges.get(gaugeId, f'gauge_arg_{argNumber}')
			entry = {'name': name, 'arg': argNumber}
			if gauge.input:
				entry['input'] = luaTableToList(gauge.input)
			if gauge.output:
				entry['output'] = luaTableToList(gauge.output)
			if gauge.controller:
				entry['controller'] = str(gauge.controller)
			result.append(entry)
		i += 1

	return result


def loadDcsTranslations(dcsDir):
	"""Load the C-101 module's own localization catalog (messages.mo).

	C-101 clickabledata.lua wraps hint strings in _() — e.g. _("EJECTION HANDLE").
	At runtime DCS translates these using the module-specific catalog at
	CoreMods/aircraft/C-101/l10n/en/LC_MESSAGES/messages.mo, which maps e.g.
	'EJECTION HANDLE' -> 'Seat Firing Handle'.  Returns a dict {key: resolvedText}
	or {} on failure.
	"""
	moPath = os.path.join(dcsDir, 'CoreMods', 'aircraft', 'C-101', 'l10n', 'en', 'LC_MESSAGES', 'messages.mo')
	if not os.path.isfile(moPath):
		print(f'Warning: dcs.mo not found at {moPath}, hint labels will not be resolved', file=sys.stderr)
		return {}
	try:
		with open(moPath, 'rb') as f:
			translations = gettext.GNUTranslations(f)
		return translations._catalog
	except Exception as exc:
		print(f'Warning: could not load dcs.mo: {exc}', file=sys.stderr)
		return {}


def resolveHints(elements, catalog):
	"""Resolve _()-wrapped hint strings to human-readable labels.

	For controls whose raw Lua hint key resolves to a different string in the
	DCS catalog (e.g. _("EJECTION HANDLE") -> "Seat Firing Handle"), the raw
	key is saved in 'hintKey' so users can find the native Lua definition, and
	'hint' is replaced with the resolved label so users can search by the
	in-cockpit tooltip text.  Controls already using plain English (whose hint
	key equals the resolved value) are left unchanged with no 'hintKey' added.
	"""
	for elemData in elements.values():
		raw = elemData.get('hint', '')
		if not raw:
			continue
		resolved = catalog.get(raw, raw)
		if resolved and resolved != raw:
			elemData['hintKey'] = raw
			elemData['hint'] = resolved


def runExtraction(scriptsDir, dcsDir=None):
	"""Run the full C-101EB extraction pipeline."""
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

	# Resolve localization-key hints to human-readable labels from dcs.mo.
	if dcsDir:
		catalog = loadDcsTranslations(dcsDir)
		if catalog:
			resolveHints(elements, catalog)

	indicators, equipmentProperties = extractIndicators(lua, scriptsDir, devices)

	totalFields = 0
	for ind in indicators:
		fields = extractTextFieldsLupa(scriptsDir, ind['initFile'])
		ind['fields'] = fields
		totalFields += len(fields)

	gaugesAndLamps = extractGaugesAndLamps(lua, scriptsDir)

	inputDir = os.path.normpath(os.path.join(scriptsDir, '..', '..', 'Input', 'C-101EB'))
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
		'module': 'C-101EB',
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
	parser = argparse.ArgumentParser(description='Extract native control data from C-101EB Aviojet DCS module.')
	parser.add_argument('--dcs-dir', default=defaultDcsDir, help=f'DCS World install directory (default: {defaultDcsDir})')
	parser.add_argument('--output', '-o', help='Output JSON file path (default: config/nativeExtractions/C-101EB.json)')
	args = parser.parse_args()

	scriptsDir = os.path.join(args.dcs_dir, scriptsRelPath)
	scriptsDir = os.path.abspath(scriptsDir)
	dcsDir = os.path.abspath(args.dcs_dir)

	if not os.path.isdir(scriptsDir):
		print(f'Error: Scripts directory not found: {scriptsDir}', file=sys.stderr)
		print(f'Check that --dcs-dir points to your DCS World install.', file=sys.stderr)
		sys.exit(1)

	result = runExtraction(scriptsDir, dcsDir)

	if args.output:
		outputPath = args.output
	else:
		repoRoot = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
		outputPath = os.path.join(repoRoot, 'config', 'nativeExtractions', 'C-101EB.json')

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
