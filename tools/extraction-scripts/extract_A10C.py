#!/usr/bin/env python3
"""Extract native control data from A-10C Thunderbolt II DCS module Lua files.

Self-contained extraction script that uses lupa to execute the A-10C's native
Lua files in a sandboxed environment.  Extracts: devices, command tables,
clickable elements, and gauges/lamps.

Reads: A-10C/Cockpit/Scripts/ (clickabledata.lua, command_defs.lua, devices.lua,
       device_init.lua, mainpanel_init.lua)
Writes: config/nativeExtractions/A-10C.json

Usage:
	python extract_A10C.py [--dcs-dir <path>] [--output <path>]

The --dcs-dir flag overrides the default DCS install path.  The default is:
	C:/Games/DCS World

Notes:
	Equipment properties (get_aircraft_property_or_nil calls) are captured via
	a lupa-instrumented Lua mock rather than regex on source text.
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
	extractSlaveAnimation,
	extractSlaveAnimationMeta,
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

# Relative path from DCS install root to the A-10C scripts directory.
scriptsRelPath = 'Mods/aircraft/A-10C/Cockpit/Scripts'


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

	get_aircraft_property_or_nil is instrumented to record every property name
	it is called with into _extractedEquipmentProps, replacing regex-based
	extraction from source text.
	"""
	lua = lupa.LuaRuntime(unpack_returned_tuples=True)
	scriptsPath = scriptsDir.replace('\\', '/').rstrip('/') + '/'

	# A-10C device_init.lua references LockOn_Options.script_path and
	# LockOn_Options.common_script_path.  Make any nested key access auto-vivify
	# to a magic table.  Comparisons and arithmetic on unknown nested values
	# are handled by metamethods so they don't raise errors.
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

	# A-10C clickabledata.lua uses require("i_18n") and sets _ = gettext.translate.
	# Our mock returns the identity function as translate, so _("text") returns "text".
	lua.execute('''
		local realRequire = require
		function require(modName)
			if modName == "i_18n" then
				return {
					translate = function(s) return s end,
					get_locale = function() return "en", "RU" end,
				}
			end
			return realRequire(modName)
		end

		-- Fallback in case _ is called before require("i_18n") runs.
		function _(s) return s end
	''')

	# A-10C source files may contain Lua 5.1-era invalid escape sequences that
	# lupa's Lua 5.5 refuses to parse.  Override dofile/loadfile to read the source
	# as bytes, strip unknown backslash-escapes inside string literals so the
	# cleaned source loads cleanly.
	def _sanitizeLua(srcBytes):
		text = srcBytes.decode('utf-8', errors='replace')
		validNext = set('abfnrtv\\"\'\n0123456789xz')
		out = []
		i = 0
		L = len(text)
		while i < L:
			c = text[i]
			if c == '\\' and i + 1 < L and text[i+1] not in validNext:
				out.append(text[i+1])
				i += 2
			else:
				out.append(c)
				i += 1
		return ''.join(out)

	def _readAndSanitize(path):
		path = path.replace('\\', '/')
		try:
			with open(path, 'rb') as f:
				return _sanitizeLua(f.read())
		except OSError:
			return None
	lua.globals()._readAndSanitize = _readAndSanitize

	lua.execute('''
		function dofile(path)
			local src = _readAndSanitize(path)
			if not src then
				io.stderr:write("Warning: Could not read " .. tostring(path) .. "\\n")
				return
			end
			local f, err = load(src, "@" .. path)
			if not f then
				io.stderr:write("Warning: Could not load " .. tostring(path) .. ": " .. tostring(err) .. "\\n")
				return
			end
			local ok, result = pcall(f)
			if not ok then
				io.stderr:write("Warning: Error executing " .. tostring(path) .. ": " .. tostring(result) .. "\\n")
				return
			end
			return result
		end
		function loadfile(path)
			local src = _readAndSanitize(path)
			if not src then return nil, "could not read " .. tostring(path) end
			return load(src, "@" .. path)
		end
	''')

	# Mocks needed for device_init.lua execution.
	lua.execute('''
		function mount_vfs_model_path() end
		function mount_vfs_texture_path() end
		function mount_vfs_liveries_path() end
		function mount_vfs_texture_archives() end
		function mount_vfs_path_to_mount_point() end
		function writeParameter() end

		function get_param_handle(name)
			return { set = function(self, val) end, get = function(self) return 0 end }
		end

		-- device_init.lua calls get_terrain_related_data("TAD_vfs_archives") to
		-- optionally load terrain textures.  Return nil so the conditional block is
		-- skipped without error.
		function get_terrain_related_data(name)
			return nil
		end

		-- copyTable is defined in DCS common tools.lua which is not present in the
		-- A-10C scripts directory.  Mock it here so device_init.lua can call
		-- copyTable(MFCD_Links_left, MFCD_Links_right) without error.
		function copyTable(dst, src)
			for k, v in pairs(src) do dst[k] = v end
		end

		render_purpose = { GENERAL = 0, BAKE = 1, HUD_ONLY_VIEW = 2, SCREENSPACE = 3 }
		indicator_types = { COMMON = 0 }

		function update_screenspace_displacement() end
		function try_find_assigned_viewport() return nil end
		function Copy(t) return t end

		kneeboard_implementation = ""
		disable_kneeboard_render_target = false
	''')

	# Instrument get_aircraft_property_or_nil to record every property name it is
	# called with.  This replaces regex extraction from device_init.lua source text
	# and captures calls from any dofile'd sub-files as well.
	lua.execute('''
		_extractedEquipmentProps = {}
		function get_aircraft_property_or_nil(name)
			local already = false
			for _, v in ipairs(_extractedEquipmentProps) do
				if v == name then already = true; break end
			end
			if not already then
				_extractedEquipmentProps[#_extractedEquipmentProps + 1] = name
			end
			return nil
		end
	''')

	# Mocks needed for mainpanel_init.lua gauge extraction.
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

	# Execute sounds.lua to define SOUND_* constants before clickabledata.lua
	# needs them (clickabledata.lua also dofiles it, but pre-loading is safer).
	soundsPath = os.path.join(scriptsDir, 'sounds.lua').replace('\\', '/')
	if os.path.exists(soundsPath):
		lua.execute(f'dofile("{soundsPath}")')
	else:
		print(f'Warning: {soundsPath} not found, SOUND constants may be undefined', file=sys.stderr)

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

	A-10C has two kinds of command tables:
	- Standard *_commands tables (device-specific, start_command = 3000 base)
	- Keys table (global key commands with fixed integer IDs)

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
	"""Extract the clickable elements table -> {key: controlData}.

	A-10C is a single-seat aircraft; there is no crew_member_access field.
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
		# class_vr can contain nils in the middle (sparse table), so use
		# length-bounded index access rather than luaTableToList (which stops at nil).
		classVrTypes = []
		if element.class_vr:
			for j in range(1, len(classTypes) + 1):
				classVrTypes.append(element.class_vr[j])
		stopAction = luaTableToList(element.stop_action) if element.stop_action else []
		cycle = element.cycle if element.cycle is not None else None
		gain = luaTableToList(element.gain) if element.gain else []
		relative = luaTableToList(element.relative) if element.relative else []
		useReleaseMessage = luaTableToList(element.use_release_message) if element.use_release_message else []

		# `_helper` is set by installHelperTagger when a clickabledata helper
		# (e.g. animated_guard_switch) builds this element.  Surface it so the
		# generator can recognise covers / guards independently of structural
		# heuristics.  See extractUtils.HELPER_NAMES_TO_TAG.
		helperTag = element._helper

		classNames = [classTypeNames.get(int(c), str(c)) if c is not None else None for c in classTypes]
		classVrNames = [classTypeNames.get(int(c), str(c)) if c is not None else None for c in classVrTypes]

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

		if any(v is not None for v in classVrNames):
			controlData['classVr'] = classVrNames
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

		# slave_animation: master/slave display-arg chain for radio_wheel helpers.
		# Includes slaveArgLim and slaveArgScale (range and scale per display arg)
		# so the generator can emit correct argLim and step for wheel controls.
		slaveAnim = extractSlaveAnimation(element, len(action))
		if any(chain for chain in slaveAnim):
			controlData['slaveAnimation'] = slaveAnim
			slaveAnimMeta = extractSlaveAnimationMeta(element, len(action))
			slaveArgLim = [[pair[0] for pair in chainMeta] for chainMeta in slaveAnimMeta]
			slaveArgScale = [[pair[1] for pair in chainMeta] for chainMeta in slaveAnimMeta]
			if any(lim is not None for chain in slaveArgLim for lim in chain):
				controlData['slaveArgLim'] = slaveArgLim
			if any(scale is not None for chain in slaveArgScale for scale in chain):
				controlData['slaveArgScale'] = slaveArgScale

		# animationSpeed: per-sub-element animation rate (arg units per second).
		# Captured for radio_wheel elements (hardcoded {0.5,0.5} by that helper)
		# so the generator can compute per-control settle delays for slow knobs.
		animSpeedTable = element.animation_speed
		if animSpeedTable is not None and lupa.lua_type(animSpeedTable) == 'table':
			speeds = []
			for i in range(1, len(action) + 1):
				v = animSpeedTable[i]
				speeds.append(float(v) if v is not None else None)
			if any(s is not None and s != 0 for s in speeds):
				controlData['animationSpeed'] = speeds

		controls[str(key)] = controlData

	return controls


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

	# Build SystemsSignals reverse map: integer index -> signal name (e.g. 6 -> 'flag_ANTISKID').
	systemsSignalsReverse = {}
	if g.SystemsSignals:
		for k in g.SystemsSignals:
			v = g.SystemsSignals[k]
			if v is not None:
				try:
					systemsSignalsReverse[int(v)] = str(k)
				except (ValueError, TypeError):
					pass

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

		# Determine name: prefer named global var, then SystemsSignal enum name, then arg fallback.
		if gaugeId in namedGauges:
			name = namedGauges[gaugeId]
		elif gauge.controller == 'lamp_SystemsSignal' and gauge.params and lupa.lua_type(gauge.params) == 'table':
			paramsList = luaTableToList(gauge.params)
			signalKey = int(paramsList[0]) if paramsList else None
			name = systemsSignalsReverse.get(signalKey, f'gauge_arg_{argNumber}')
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
	"""Run the full A-10C extraction pipeline."""
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
	print(
		f'Deterministic device→table mappings: {len(deviceTableMap)}/{len(devices)} '
		f'devices (from {len(accessLog)} logged accesses, {len(elementSpans)} element spans)',
		file=sys.stderr,
	)

	# Execute device_init.lua to capture equipment properties via the instrumented
	# get_aircraft_property_or_nil mock.  A-10C uses the MainPanel/creators format
	# instead of an indicators global, so indicators extraction is skipped.
	deviceInitPath = os.path.join(scriptsDir, 'device_init.lua').replace('\\', '/')
	if os.path.exists(deviceInitPath):
		lua.execute(f'dofile("{deviceInitPath}")')
	else:
		print(f'Warning: {deviceInitPath} not found, skipping device_init', file=sys.stderr)

	equipmentProperties = extractEquipmentProperties(lua)

	indicators = extractIndicatorsFromLuaGlobals(lua, scriptsDir, devices)
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
		'module': 'A-10C',
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
	parser = argparse.ArgumentParser(description='Extract native control data from A-10C Thunderbolt II DCS module.')
	parser.add_argument('--dcs-dir', default=defaultDcsDir, help=f'DCS World install directory (default: {defaultDcsDir})')
	parser.add_argument('--output', '-o', help='Output JSON file path (default: config/nativeExtractions/A-10C.json)')
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
		outputPath = os.path.join(repoRoot, 'config', 'nativeExtractions', 'A-10C.json')

	os.makedirs(os.path.dirname(outputPath), exist_ok=True)

	with open(outputPath, 'w', encoding='utf-8') as f:
		json.dump(result, f, indent='\t', ensure_ascii=False, sort_keys=True)

	stats = result['stats']
	print(f'Wrote: {outputPath}', file=sys.stderr)
	print(f'Devices: {stats["totalDevices"]}', file=sys.stderr)
	print(f'Command tables: {stats["totalCommandTables"]}', file=sys.stderr)
	print(f'Elements: {stats["totalElements"]}', file=sys.stderr)
	print(f'Indicators: {stats["totalIndicators"]}', file=sys.stderr)
	print(f'Equipment properties: {len(result["equipmentProperties"])}', file=sys.stderr)
	print(f'Gauges and lamps: {stats["totalGaugesAndLamps"]}', file=sys.stderr)
	print(f'Keybindings: {stats["totalKeybindings"]}', file=sys.stderr)
	print(f'Listened commands: {stats["totalListenedCommands"]}', file=sys.stderr)


if __name__ == '__main__':
	main()
