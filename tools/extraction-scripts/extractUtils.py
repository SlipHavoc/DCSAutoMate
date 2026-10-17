"""Shared helpers for per-module native extractors.

## Deterministic device→command-table mapping

The DCS Lua source declares each command table as a global (e.g.
`ctrl_commands = { TOTrimSw = 10346, ... }`) and `clickabledata.lua` binds
each clickable element with an explicit reference like
`devices.CONTROL_INTERFACE, ctrl_commands.TOTrimSw`.  That literal source-level
link between a device and a command table is exactly what we need to avoid
the fuzzy name-scoring tiebreakers the generator used to rely on.

Capturing it requires solving two problems:

1. **Which table is each `.field` access on?**  We install a `__newindex`
   metatable on `_G` that fires when `command_defs.lua` assigns any
   `*_commands = {...}` global, transparently wrapping the table in a proxy
   whose `__index` logs `(tableName, cmdName, cmdId)`.
2. **Which element does each access belong to?**  Cmd ids alone aren't
   sufficient — every command table starts at id 3000, so id 3001 exists in
   baroaltimeter_commands, clock_commands, etc. simultaneously.  We also
   wrap the `elements` table so each `elements[k] = default_button(...)`
   assignment records the span of access-log indices captured during that
   constructor's argument evaluation.  The accesses in element k's span
   name the exact table(s) that k's cmd ids came from.

After `clickabledata.lua` finishes, `deriveDeviceTableMap` joins the element
spans + access log + element device ids into `{deviceId: tableName}`, exact
for every device that appears in at least one clickable element.

Devices driven only by `Input/*/default.lua` (keyboard/joystick bindings) or
only by indicators will not appear in the map; the generator falls back to
its existing name-similarity + evidence heuristics for those.

## Call order (per extractor)

    lua = createLuaRuntime(scriptsDir)
    installCmdAccessLogger(lua)                    # before clickabledata
    lua.execute(f'dofile("{clickableDataPath}")')
    accessLog    = readCmdAccessLog(lua)
    elementSpans = readElementAccessSpans(lua)
    uninstallCmdAccessLogger(lua)                  # restore plain tables
    ...
    elements = extractElements(lua)                # already works
    deviceTableMap = deriveDeviceTableMap(elements, accessLog, elementSpans)
"""

import json
import math
import os
import sys

import lupa
from lupa import lua51


def portableUserPath(path, userProfile):
	"""path with a leading userProfile folder replaced by %USERPROFILE%, so extraction JSON doesn't record the user's name."""
	if not userProfile:
		return path
	normalized = os.path.normpath(path)
	profile = os.path.normpath(userProfile)
	if normalized.lower() == profile.lower():
		return '%USERPROFILE%'
	prefix = profile.rstrip('\\') + '\\'
	if normalized.lower().startswith(prefix.lower()):
		return '%USERPROFILE%\\' + normalized[len(prefix):]
	return path


def luaTableToList(luaTable):
	"""Convert a Lua table (used as a 1-indexed array) to a Python list.

	Nil holes become None so entries stay aligned with their sub-control
	index: DCS writes e.g. `relative = {nil, true}` for a BTN+LEV element.
	"""
	if luaTable is None:
		return []
	length = 0
	for key in luaTable.keys():
		# lua51 runtimes return numeric keys as floats.
		if isinstance(key, (int, float)) and not isinstance(key, bool) and key >= 1 and key == int(key):
			length = max(length, int(key))
	# Also probe past the raw keys, for array values served via __index.
	while luaTable[length + 1] is not None:
		length += 1
	result = []
	for i in range(1, length + 1):
		val = luaTable[i]
		if lupa.lua_type(val) == 'table':
			val = luaTableToList(val)
		result.append(val)
	return result


_INSTALL_LUA = r'''
__dcsamCmdAccesses = {}
__dcsamCmdTableOrigs = {}    -- tableName -> original unwrapped command table
__dcsamElementsOrig = nil    -- original unwrapped elements table
__dcsamElementSpans = {}     -- elementKey -> { first = N, last = M } (1-indexed, inclusive)
__dcsamLastElementAccessIdx = 0


local function wrapCommandsTable(orig, tname)
	__dcsamCmdTableOrigs[tname] = orig
	local proxy = {}
	setmetatable(proxy, {
		__index = function(_, name)
			local id = rawget(orig, name)
			if id ~= nil then
				__dcsamCmdAccesses[#__dcsamCmdAccesses + 1] =
					{ tbl = tname, name = name, id = id }
			end
			return id
		end,
		__newindex = function(_, n, v) rawset(orig, n, v) end,
		__pairs    = function() return pairs(orig) end,
		__len      = function() return #orig end,
		__dcsamProxy = true,
	})
	return proxy
end


local function wrapElementsTable(orig)
	__dcsamElementsOrig = orig
	-- Discard any accesses logged before the `elements` table was created:
	-- command_defs.lua itself may do `x = *_commands.Foo` during setup
	-- (e.g. Mi-24P's `cb_start_cmd = device_commands.Button_31`), and those
	-- must not leak into the first element's span.
	__dcsamLastElementAccessIdx = #__dcsamCmdAccesses
	local proxy = {}
	setmetatable(proxy, {
		__index = function(_, k) return rawget(orig, k) end,
		__pairs = function() return pairs(orig) end,
		__len   = function() return #orig end,
		__newindex = function(_, k, v)
			if rawget(orig, k) == nil then
				local startIdx = __dcsamLastElementAccessIdx + 1
				local endIdx   = #__dcsamCmdAccesses
				if endIdx >= startIdx then
					__dcsamElementSpans[k] = { first = startIdx, last = endIdx }
					__dcsamLastElementAccessIdx = endIdx
				end
			end
			rawset(orig, k, v)
		end,
		__dcsamProxy = true,
	})
	return proxy
end


setmetatable(_G, {
	__newindex = function(t, k, v)
		if type(k) == 'string' and type(v) == 'table' then
			local existingMt = getmetatable(v)
			if not (existingMt and existingMt.__dcsamProxy) then
				if k == 'elements' then
					v = wrapElementsTable(v)
				elseif #k > 9 and k:sub(-9) == '_commands' then
					v = wrapCommandsTable(v, k)
				end
			end
		end
		rawset(t, k, v)
	end,
})


-- Wrap `dofile` so that after each invocation we sweep `_G` and re-wrap any
-- `*_commands` tables that were reassigned as plain tables.  This is needed
-- because once a global key exists in `_G`'s raw storage, subsequent
-- assignments use raw storage and bypass `__newindex`.  Some modules (e.g.
-- AH-64D's VR_config.lua) re-dofile command_defs.lua, which re-executes
-- `foo_commands = {}` and overwrites our proxy with a plain empty table.
__dcsamOrigDofile = dofile
function dofile(...)
	local results = { __dcsamOrigDofile(...) }
	for k, v in pairs(_G) do
		if type(k) == 'string' and type(v) == 'table'
				and #k > 9 and k:sub(-9) == '_commands' then
			local mt = getmetatable(v)
			if not (mt and mt.__dcsamProxy) then
				rawset(_G, k, wrapCommandsTable(v, k))
			end
		end
	end
	return table.unpack(results)
end
'''


_UNINSTALL_LUA = r'''
if __dcsamCmdTableOrigs then
	for tname, orig in pairs(__dcsamCmdTableOrigs) do
		rawset(_G, tname, orig)
	end
end
if __dcsamElementsOrig then
	rawset(_G, 'elements', __dcsamElementsOrig)
end
if __dcsamOrigDofile then
	dofile = __dcsamOrigDofile
end
setmetatable(_G, nil)
'''


def installCmdAccessLogger(lua):
	"""Install the _G metatable that wraps *_commands globals and `elements`
	in logging proxies.

	Must be called after the Lua runtime is built but before any Lua code
	that assigns the wrapped globals runs — i.e. before the extractor loads
	clickabledata.lua (which dofile's command_defs.lua internally and then
	assigns `elements = {}` before populating it).
	"""
	lua.execute(_INSTALL_LUA)


def uninstallCmdAccessLogger(lua):
	"""Restore original unwrapped `*_commands` tables and `elements` in `_G`.

	Call after all Lua code that reads the command tables has run and
	after `readCmdAccessLog` / `readElementAccessSpans` have captured the
	log.  Python-side iteration of the globals table uses `lua_next`, which
	does not honor `__pairs` metamethods on proxies, so the real tables
	must be put back first.
	"""
	lua.execute(_UNINSTALL_LUA)


_INSTALL_HELPER_TAGGER_LUA = r'''
-- Hook _G.__newindex to wrap every module-defined helper function so that its
-- returned table is tagged with `_helper = '<functionName>'` when the return
-- value looks like a DCS clickable element (has a non-nil `device` field, which
-- ALL factory-function-created elements have and other tables generally do not).
-- Using `device` rather than `arg` because some helpers (e.g. multiswitch_stop,
-- oil_flap_switch, base_btn_cycle3) accept an arg parameter but do not store it
-- in the returned table, so `result.arg` would be nil for those elements.
-- Exhaustive: every factory function gets tagged without an allowlist.
-- Layers on top of installCmdAccessLogger's __newindex hook via chaining.
local existingMt = getmetatable(_G) or {}
local existingNewindex = existingMt.__newindex
local function dcsamHelperNewindex(t, k, v)
	if type(v) == 'function' then
		local fnName = k
		local orig = v
		v = function(...)
			local result = orig(...)
			if type(result) == 'table' and (result.device ~= nil or result.arg ~= nil) then
				result._helper = fnName
			end
			return result
		end
	end
	if existingNewindex then
		existingNewindex(t, k, v)
	else
		rawset(t, k, v)
	end
end
existingMt.__newindex = dcsamHelperNewindex
setmetatable(_G, existingMt)
'''


def installHelperTagger(lua):
	"""Install a _G.__newindex hook that exhaustively tags all DCS helper functions.

	Wraps every function defined at global scope after this call. When the
	function is called and returns a table with a non-nil `arg` field (the
	hallmark of a DCS clickable element), injects `_helper = '<functionName>'`
	onto the returned table. Element extraction surfaces this as a `helper`
	field in the emitted control JSON.

	This is exhaustive: no allowlist is needed. Every factory function used by
	clickabledata.lua will be tagged, including module-specific helpers not in
	the former HELPER_NAMES_TO_TAG list.

	Note: the detection condition is `result.device ~= nil or result.arg ~= nil` rather than
	just `result.arg ~= nil`. Some Lua helpers (e.g. multiswitch_stop, oil_flap_switch,
	base_btn_cycle3) pass an arg to the function but do not store it in the returned table,
	so `result.arg` is nil for those elements. The `or result.device ~= nil` arm catches them.
	Some helpers (e.g. A-4E-C compass elements) return tables with device=nil but arg set,
	so `result.arg ~= nil` is still needed as well.

	Must be called AFTER installCmdAccessLogger (so we layer on top of its
	__newindex hook) and BEFORE clickabledata.lua is loaded.
	"""
	lua.execute(_INSTALL_HELPER_TAGGER_LUA)


_INSTALL_LAMP_ENUM_LOGGER_LUA = r'''
__dcsamLastEnumAccess = nil

-- Wrap CreateGauge to capture the most recent enum member access into
-- the gauge as _enumSource.  Must be called after the CreateGauge mock
-- is already defined in the runtime.
local _origCreateGauge = CreateGauge
function CreateGauge(optArg)
	local g = _origCreateGauge(optArg)
	if __dcsamLastEnumAccess ~= nil then
		g._enumSource = __dcsamLastEnumAccess
		__dcsamLastEnumAccess = nil
	end
	return g
end

-- Detect counter-pattern tables: values are exactly the set {0, 1, ..., n-1}
-- with no duplicates and no gaps.  This is the exact signature produced by
-- the counter() pattern used in DCS lamps.lua files.
local function isCounterPattern(t)
	local maxVal = -1
	local count = 0
	for _, v in pairs(t) do
		if type(v) ~= 'number' or v ~= math.floor(v) or v < 0 then
			return false
		end
		if v > maxVal then maxVal = v end
		count = count + 1
	end
	return count > 0 and maxVal == count - 1
end

-- Install _G __newindex to intercept counter-pattern table assignments and
-- replace them with proxies whose __index records the table+member name in
-- __dcsamLastEnumAccess before returning the value.  This lets CreateGauge
-- capture which enum entry was passed to the lamp creation function.
setmetatable(_G, {
	__newindex = function(t, k, v)
		if type(k) == 'string' and type(v) == 'table' then
			local mt = getmetatable(v)
			if not (mt and mt.__dcsamEnumProxy) and isCounterPattern(v) then
				local tableName = k
				local origTable = v
				v = setmetatable({}, {
					__index = function(_, member)
						local val = rawget(origTable, member)
						if val ~= nil then
							__dcsamLastEnumAccess = tableName .. '.' .. member
						end
						return val
					end,
					__newindex = function(_, m, val) rawset(origTable, m, val) end,
					__pairs = function(_) return pairs(origTable) end,
					__dcsamEnumProxy = true,
				})
			end
		end
		rawset(t, k, v)
	end,
})
'''


def installLampEnumLogger(lua):
	"""Install Lua instrumentation that records enum table member accesses
	into gauges created during mainpanel_init.lua execution.

	Must be called AFTER createLuaRuntime() (so the CreateGauge mock is
	already defined) and BEFORE dofile(mainpanel_init.lua).  Do NOT call
	while installCmdAccessLogger's _G metatable is still active — call after
	uninstallCmdAccessLogger, or in extractors that don't use the cmd logger
	for the mainpanel phase.

	After dofile(mainpanel_init.lua), each gauge in _extractedGauges that was
	created by a bare lamp call like `create_caution_lamp(634, CautionLights.ELEC_SYS)`
	will have `gauge._enumSource = 'CautionLights.ELEC_SYS'`.  Gauges created
	without a preceding enum access (named globals, brightness controls, etc.)
	will have no _enumSource field.
	"""
	lua.execute(_INSTALL_LAMP_ENUM_LOGGER_LUA)


def readCmdAccessLog(lua):
	"""Return the recorded command-table accesses as a list of dicts.

	Each entry: {'tbl': <tableName>, 'name': <cmdName>, 'id': <cmdId>}.
	Ordered by occurrence.  Call after clickabledata.lua has finished and
	before `uninstallCmdAccessLogger`.
	"""
	log = lua.globals().__dcsamCmdAccesses
	if log is None:
		return []
	result = []
	i = 1
	while True:
		entry = log[i]
		if entry is None:
			break
		result.append({
			'tbl':  str(entry.tbl),
			'name': str(entry.name),
			'id':   int(entry.id),
		})
		i += 1
	return result


def readElementAccessSpans(lua):
	"""Return {elementKey: (firstIdx, lastIdx)} access-log spans per element.

	Indices are 1-based inclusive into the list returned by
	`readCmdAccessLog` (so `accessLog[firstIdx-1 : lastIdx]` gives the
	Python slice).  Only elements that triggered at least one access appear.
	"""
	spans = lua.globals().__dcsamElementSpans
	if spans is None:
		return {}
	result = {}
	for key in spans:
		entry = spans[key]
		result[str(key)] = (int(entry.first), int(entry.last))
	return result


def deriveDeviceTableMap(elements, accessLog, elementSpans):
	"""Join `elements`, access log, and per-element spans into
	`{deviceId: tableName}`.

	For each element:
	  - Collect the set of table names in its access span.
	For each device:
	  - If every element on that device pointed to the same single table,
	    take it as the deterministic answer.  Otherwise omit (the
	    generator's heuristic fallback handles the rest).
	"""
	deviceTableEvidence = {}  # deviceId → set of table names observed
	for key, el in elements.items():
		devId = el.get('device')
		if devId is None:
			continue
		span = elementSpans.get(key)
		if span is None:
			continue
		first, last = span
		for i in range(first - 1, last):
			if 0 <= i < len(accessLog):
				deviceTableEvidence.setdefault(devId, set()).add(accessLog[i]['tbl'])

	result = {}
	for devId, tables in deviceTableEvidence.items():
		if len(tables) == 1:
			result[devId] = next(iter(tables))
	return result


def extractSlaveAnimation(element, numSubElements):
	"""Walk the Lua `slave_animation` field on a clickable element.

	DCS helpers `radio_wheel_1` and `radio_wheel_double` set
	`slave_animation = {{slave = spec1}, {slave = spec1}, ...}` where each
	spec is a chain `{<masterArg>, <range>, <step>, slave = {<slaveArg>, ...,
	slave = {...}}}`.  The chain mirrors the digit-carry coupling of multi-
	digit cockpit displays: turning the wheel pulses the command's `arg`
	while the displayed master arg (and any slaves) update in lock-step.

	Returns a list aligned with sub-element index (1..numSubElements).  Each
	entry is a flat list of arg ints from the master/slave chain (or `[]`
	when the sub-element has no slave_animation entry, which is the common
	case for non-wheel elements).

	Implementation note: `lupa` is the standard tool for reading these
	tables.  We never re-parse Lua source text.
	"""
	import lupa
	out = []
	sa = element.slave_animation
	if sa is None or lupa.lua_type(sa) != 'table':
		return [[] for _ in range(numSubElements)]
	for i in range(1, numSubElements + 1):
		entry = sa[i]
		chain = []
		if entry is not None and lupa.lua_type(entry) == 'table':
			spec = entry.slave
			while spec is not None and lupa.lua_type(spec) == 'table':
				argEntry = spec[1]
				if argEntry is None:
					break
				chain.append(int(argEntry))
				spec = spec.slave
		out.append(chain)
	return out


def extractSlaveAnimationMeta(element, numSubElements):
	"""Walk the Lua `slave_animation` field and return per-arg range and scale.

	Each slave spec node has the form `{<arg>, <range>, <scale>, slave = ...}`
	where `<range>` is a two-element Lua table `{min, max}` and `<scale>` is
	a float multiplier relating the command-arg step to the display-arg step
	(displayStep = commandStep * scale).

	Returns a list parallel to extractSlaveAnimation.  Each entry is a list of
	[lim, scale] pairs where lim is [min, max] (or None if absent) and scale is
	a float (or None if absent).  [] when the sub-element has no slave_animation.

	Used by A-10C (and compatible) extractors to capture display-arg range and
	animation scale so the generator can emit correct argLim and step fields.
	"""
	import lupa
	out = []
	sa = element.slave_animation
	if sa is None or lupa.lua_type(sa) != 'table':
		return [[] for _ in range(numSubElements)]
	for i in range(1, numSubElements + 1):
		entry = sa[i]
		meta = []
		if entry is not None and lupa.lua_type(entry) == 'table':
			spec = entry.slave
			while spec is not None and lupa.lua_type(spec) == 'table':
				if spec[1] is None:
					break
				lim = None
				scale = None
				limEntry = spec[2]
				if limEntry is not None and lupa.lua_type(limEntry) == 'table':
					lim = [float(limEntry[1]), float(limEntry[2])]
				scaleEntry = spec[3]
				if scaleEntry is not None:
					scale = float(scaleEntry)
				meta.append([lim, scale])
				spec = spec.slave
		out.append(meta)
	return out


# ── Equipment properties mock ──────────────────────────────────────────────────

_EQUIPMENT_PROPS_LUA = r'''
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
'''


def loadArgsInitialState(lua, scriptsDir):
	"""Load config.lua (if it exists) and return the args_initial_state dict.

	The Lua global args_initial_state maps arg IDs to their non-zero initial
	values.  Args absent from the table default to 0.0 in DCS.
	Safe to call after clickabledata.lua has already been executed — it
	initialises args_initial_state to {} before running config.lua so any
	previous Lua state is not confused.
	"""
	lua.execute('args_initial_state = {}')
	configPath = os.path.join(scriptsDir, 'config.lua').replace('\\', '/')
	if os.path.exists(configPath):
		lua.execute(f'dofile("{configPath}")')
	ais = lua.globals().args_initial_state
	if ais is None or lupa.lua_type(ais) != 'table':
		return {}
	result = {}
	for k in ais:
		v = ais[k]
		if isinstance(k, (int, float)) and isinstance(v, (int, float)):
			result[int(k)] = float(v)
	return result


def correctMultiposArgLim(argLim, argValue, arg, argsInitialState):
	"""Correct argLim for multiposition switches to align positions with initial arg.

	multiposition_switch_limited uses its min_ parameter as the animation floor
	(the lower bound of the arg_lim range), NOT the first discrete position.
	DCS steps the arg by ±delta from whatever the initial arg value is (0 by
	default, or from args_initial_state).  If min_ is not a multiple of delta
	from the initial arg, the derived positions will be off.

	Formula: actual_min = initial - floor((initial - luaMin) / delta) * delta
	         actual_max = actual_min + (count - 1) * delta

	The correction is a no-op when luaMin is already aligned (the common case).
	"""
	corrected = []
	for i, lim in enumerate(argLim):
		if not (isinstance(lim, list) and len(lim) == 2):
			corrected.append(lim)
			continue
		if i >= len(argValue):
			corrected.append(lim)
			continue
		delta = abs(argValue[i])
		if delta == 0:
			corrected.append(lim)
			continue
		argId = arg[i] if i < len(arg) else None
		initial = float(argsInitialState.get(argId, 0.0)) if argId is not None else 0.0
		luaMin, luaMax = lim[0], lim[1]
		count = round((luaMax - luaMin) / delta) + 1
		if count < 2:
			corrected.append(lim)
			continue
		stepsDown = math.floor((initial - luaMin) / delta)
		actualMin = initial - stepsDown * delta
		actualMax = actualMin + (count - 1) * delta
		if abs(actualMin - luaMin) > 1e-9 or abs(actualMax - luaMax) > 1e-9:
			corrected.append([actualMin, actualMax])
		else:
			corrected.append(lim)
	return corrected


def installEquipmentPropsMock(lua):
	"""Install instrumented get_aircraft_property_or_nil that records every queried property name.

	Call from createLuaRuntime() just before returning, after device_init.lua
	is expected to run.  Read results back with extractEquipmentProperties(lua).
	"""
	lua.execute(_EQUIPMENT_PROPS_LUA)


def extractEquipmentProperties(lua):
	"""Read equipment property names captured by the instrumented mock.

	Returns the list of property name strings recorded during device_init.lua
	execution via the installEquipmentPropsMock() hook.
	"""
	props = lua.globals()._extractedEquipmentProps
	result = []
	if props is not None:
		i = 1
		while True:
			p = props[i]
			if p is None:
				break
			result.append(str(p))
			i += 1
	return result


# ── Indicator table extraction ─────────────────────────────────────────────────

def extractIndicatorsFromLuaGlobals(lua, scriptsDir, devices):
	"""Read the indicators[] global populated by device_init.lua.

	Assumes device_init.lua has already been executed in the given runtime.
	Returns a list of indicator dicts (0-based index, cppClass, initFile,
	deviceId, deviceName, bake, conditional).

	Bake indicators are detected purely from the cppClass name and initFile
	path — no regex scanning of the source text.
	"""
	luaIndicators = lua.globals().indicators
	if luaIndicators is None:
		return []

	deviceIdToName = {v: k for k, v in devices.items()}
	scriptsPath = scriptsDir.replace('\\', '/').rstrip('/') + '/'

	result = []
	i = 1
	while True:
		entry = luaIndicators[i]
		if entry is None:
			break

		cppClass = entry[1] or ''
		initFile = entry[2] or ''
		deviceRef = entry[3]

		if isinstance(initFile, str) and initFile.startswith(scriptsPath):
			initFile = initFile[len(scriptsPath):]

		try:
			deviceId = int(deviceRef) if deviceRef is not None else None
		except Exception:
			deviceId = None
		deviceName = deviceIdToName.get(deviceId) if deviceId is not None else None

		isBake = 'bake' in initFile.lower() or 'bake' in cppClass.lower()

		result.append({
			'index': i - 1,
			'cppClass': str(cppClass),
			'initFile': str(initFile),
			'deviceId': deviceId,
			'deviceName': deviceName,
			'conditional': None,
			'bake': isBake,
		})
		i += 1

	return result


# ── Text-field extraction via lupa ─────────────────────────────────────────────

# Lua sandbox for extractTextFieldsLupa().  Stubs out enough of the DCS Lua
# environment that an indicator's init file (and the page files it references
# via page_subsets) can be executed end-to-end.  Captures every element passed
# to Add() so we can read back the real .name fields — including dynamically-
# constructed names that purely textual regex analysis cannot follow.
_textFieldsLuaInit = r'''
	LockOn_Options = {
		script_path = "__SCRIPTS_PATH__",
		common_script_path = "__SCRIPTS_PATH__",
		screen = { aspect = 1.7778, width = 1920, height = 1080, oculus_rift = false },
	}
	function get_multimonitor_preset_name() return "default" end
	function get_param_handle(name) return { set = function() end, get = function() return 0 end } end
	function get_aircraft_property_or_nil(name) return nil end
	function get_option_value(k, s) return false end
	function get_UIMainView() return 0, 0, 1920, 1080, 1.0 end
	function GetAspect() return 1.7778 end
	function GetScale() return 1.0 end
	function GetCustomScale() return 1.0 end
	function GetRenderTarget() return { width = 256, height = 256, aspect = 1.0 } end
	function MakeFont(...) return { _font = true } end
	function MakeStringDef(...) return {0.005, 0.005, 0, 0} end
	SelfWidth = 1.0; SelfHeight = 1.0; SelfAspect = 1.7778
	-- Stub the typo variant used by AV8BNA (missing 's' in displacement)
	function update_screenspace_diplacement(...) end
	-- Stub the _() localization shorthand used by several modules
	function _(s) return s end

	-- Stub require() so that modules like i_18n don't abort dofile chains.
	-- Returns a harmless stub table with a no-op translate function.
	local _requireStub = setmetatable({}, {
		__index = function(t, k) return function(...) return (...) end end,
	})
	_requireStub.translate = function(s) return s end
	local _origRequire = require
	function require(modname)
		local ok, result = pcall(_origRequire, modname)
		if ok then return result end
		return _requireStub
	end

	_capturedElements = {}
	_capturedCount = 0

	local function captureElement(obj)
		if type(obj) == 'table' then
			_capturedCount = _capturedCount + 1
			_capturedElements[_capturedCount] = obj
		end
	end

	function CreateElement(typeName) return { _elemType = typeName } end
	function Add(obj) captureElement(obj) end

	local function genericAdder(...)
		for _, a in ipairs({...}) do captureElement(a) end
	end

	function MakeMaterial(name, color) return { _matName = name } end

	local function magicMt(default)
		return { __index = function(t, k)
			local v = default
			if v == nil then v = k end
			rawset(t, k, v)
			return v
		end }
	end
	ScreenType = setmetatable({}, magicMt(nil))
	h_clip_relations = setmetatable({}, magicMt(nil))
	render_purpose = setmetatable({}, magicMt(0))
	indicator_types = setmetatable({}, magicMt(0))
	materials = setmetatable({}, { __index = function(t, k) local m = {_matName = k}; rawset(t, k, m); return m end })
	cyrillic = setmetatable({}, magicMt(nil))
	cp1251_after_128_due_192 = setmetatable({}, magicMt(0))

	default_box_indices = {}
	default_vertices = {{0,0},{1,0},{1,1},{0,1}}
	DEFAULT_LEVEL = 0
	HUD_DEFAULT_LEVEL = 0
	size = 1.0

	STC_GREEN = 0; STC_RED = 1; STC_WHITE = 2; STC_YELLOW = 3

	function update_screenspace_displacement() end
	function try_find_assigned_viewport() return nil end
	function Copy(t)
		if type(t) ~= 'table' then return t end
		local n = {}
		for k, v in pairs(t) do n[k] = v end
		return n
	end
	function mount_vfs_model_path() end
	function mount_vfs_texture_path() end

	function create_material_type_table()
		return setmetatable({}, { __index = function(t, k) rawset(t, k, k); return k end })
	end
	function set_material_type(name, mtype) end

	function clear_mode_table(t, l1, l2, l3)
		if type(t) ~= 'table' then return end
		l1 = l1 or 1; l2 = l2 or 1; l3 = l3 or 1
		for i = 1, l1 do
			t[i] = {}
			for j = 1, l2 do
				t[i][j] = {}
				for k = 1, l3 do t[i][j][k] = {} end
			end
		end
	end

	function get_page_by_mode_global(pages_by_mode, init_pageID, ...)
		return init_pageID
	end

	function SetScale(...) end
	function SetCustomScale(...) end

	local hudAdders = {
		'AddHUD_PKV_SIGHTTexElement', 'AddHUD_ASP17_FLEXSIGHTTexElement',
		'AddHUD_TexElement', 'AddHUD_StringElement', 'AddHUD_MeshElement',
		'AddElement_HUD', 'AddElement', 'Add_Radio_Element', 'Add_UFC_Element',
		'addStrPoly', 'addMeshPoly', 'addTexPoly',
	}
	for _, name in ipairs(hudAdders) do _G[name] = genericAdder end

	function dofile(path)
		path = path:gsub('\\', '/')
		local f, err = loadfile(path)
		if not f then return end
		local ok, result = pcall(f)
		if not ok then
			io.stderr:write("Warning: dofile error in " .. tostring(path) .. ": " .. tostring(result) .. "\n")
		end
		return result
	end
'''


def extractTextFieldsLupa(scriptsDir, initFileRelPath, extraLuaSetup=''):
	"""Extract text field names from an indicator's page files via lupa.

	Executes the indicator's init file in a sandboxed Lua runtime, then walks
	the resulting page_subsets table and executes each page file in the same
	runtime.  Every element added via Add()/AddElement()/AddHUD_*() is captured
	and its .name field harvested.

	extraLuaSetup: optional Lua code string executed after the standard sandbox
	setup, for module-specific stubs not covered by the shared sandbox.

	Returns a deduplicated list of field names in capture order.
	"""
	if not initFileRelPath:
		return []
	initFilePath = os.path.join(scriptsDir, initFileRelPath)
	if not os.path.exists(initFilePath):
		return []

	lua = lupa.LuaRuntime(unpack_returned_tuples=True)
	scriptsPath = scriptsDir.replace('\\', '/').rstrip('/') + '/'
	lua.execute(_textFieldsLuaInit.replace('__SCRIPTS_PATH__', scriptsPath))

	if extraLuaSetup:
		lua.execute(extraLuaSetup)

	luaDofile = lua.globals().dofile

	try:
		luaDofile(initFilePath.replace('\\', '/'))
	except Exception as e:
		print(f'Warning: extractTextFieldsLupa init exec failed for {initFileRelPath}: {e}', file=sys.stderr)

	pageSubsets = lua.globals().page_subsets
	pagePaths = []
	if pageSubsets is not None and lupa.lua_type(pageSubsets) == 'table':
		for key in pageSubsets:
			val = pageSubsets[key]
			if isinstance(val, str):
				pagePaths.append(val.replace('\\', '/'))

	for pagePath in pagePaths:
		try:
			luaDofile(pagePath)
		except Exception as e:
			print(f'Warning: extractTextFieldsLupa page exec failed for {pagePath}: {e}', file=sys.stderr)

	captured = lua.globals()._capturedElements
	fields = []
	seen = set()
	if captured is not None:
		i = 1
		while True:
			elem = captured[i]
			if elem is None:
				break
			name = elem.name
			if name is not None:
				nameStr = str(name)
				if nameStr and nameStr not in seen:
					seen.add(nameStr)
					fields.append(nameStr)
			i += 1

	return fields


# ── Keybinding extraction via lupa ─────────────────────────────────────────────

# Functions DCS provides to every Input/<profile>/<kind>/default.lua.  DCS's own
# Config/Input profiles (not on disk here) hold only simulator-level iCommand
# bindings with no cockpit_device_id, so an empty profile stands in for them.
_keybindingsLuaInit = r'''
	function _(s) return s end
	-- Like DCS, the loaded file gets its own globals (so its 'inputs' can't clobber the caller's) but sees the caller's folder.
	function external_profile(path)
		local f = io.open(path, 'r')
		if f == nil then return { keyCommands = {}, axisCommands = {}, forceFeedback = {} } end
		f:close()
		local chunk = assert(loadfile(path))
		setfenv(chunk, setmetatable({}, { __index = getfenv(2) }))
		return chunk()
	end
	function ignore_features(commands, features)
		local ignored = {}
		for _, feature in ipairs(features or {}) do ignored[feature] = true end
		for i = #commands, 1, -1 do
			for _, feature in ipairs(commands[i].features or {}) do
				if ignored[feature] then
					table.remove(commands, i)
					break
				end
			end
		end
	end
	function join(to, from)
		for _, v in ipairs(from or {}) do to[#to + 1] = v end
		return to
	end
	function defaultDeviceAssignmentFor(name) return nil end
	function MultiEngineDefaultDeviceAssignmentForThrust() return nil, nil, nil end
	function defaultFFB() return nil end
'''

_keybindingInputKinds = ('keyboard', 'joystick', 'mouse')


def _luaNumber(value):
	return float(value) if isinstance(value, (int, float)) and not isinstance(value, bool) else None


def _luaCategory(value):
	if isinstance(value, str):
		return value
	if value is not None and lua51.lua_type(value) == 'table':
		return [str(v) for v in value.values() if isinstance(v, str)]
	return None


def _readBinding(entry, kind):
	"""Convert one keyCommands/axisCommands entry, or return None if it targets no cockpit device."""
	deviceId = _luaNumber(entry.cockpit_device_id)
	if deviceId is None:
		return None
	binding = {'kind': kind, 'deviceId': int(deviceId)}
	commandFields = ('action',) if kind == 'axis' else ('down', 'up', 'pressed')
	for field in commandFields:
		commandId = _luaNumber(entry[field])
		if commandId is not None:
			binding[field] = int(commandId)
	if not any(field in binding for field in commandFields):
		return None
	for luaField, field in (('value_down', 'valueDown'), ('value_up', 'valueUp'), ('value_pressed', 'valuePressed')):
		value = _luaNumber(entry[luaField])
		if value is not None:
			binding[field] = value
	if isinstance(entry.name, str):
		binding['name'] = entry.name
	category = _luaCategory(entry.category)
	if category:
		binding['category'] = category
	return binding


def extractKeybindings(inputDir, extraLuaSetup=''):
	"""Extract cockpit-device keybindings from a module's Input/<profile>/<kind>/default.lua files.

	Each file runs in a fresh lupa runtime with the functions DCS provides to binding
	files, plus extraLuaSetup for module-specific stubs.  Bindings without a
	cockpit_device_id (simulator iCommands) are dropped.  Identical bindings found in
	several files are merged, with every file recorded in 'sources'.

	Returns (bindings, failures): bindings sorted for stable output, and a list of
	(source, errorMessage) for files that could not be executed.
	"""
	merged = {}
	failures = []
	isSingleProfile = any(os.path.isfile(os.path.join(inputDir, kind, 'default.lua')) for kind in _keybindingInputKinds)
	profiles = [''] if isSingleProfile else sorted(os.listdir(inputDir))
	for profile in profiles:
		for kind in _keybindingInputKinds:
			filePath = os.path.join(inputDir, profile, kind, 'default.lua')
			if not os.path.isfile(filePath):
				continue
			source = f'{profile}/{kind}' if profile else kind
			lua = lua51.LuaRuntime(unpack_returned_tuples=True)
			lua.execute(_keybindingsLuaInit)
			lua.globals().folder = os.path.dirname(filePath).replace('\\', '/') + '/'
			if extraLuaSetup:
				lua.execute(extraLuaSetup)
			try:
				result = lua.globals().dofile(filePath.replace('\\', '/'))
			except Exception as e:
				failures.append((source, str(e)))
				continue
			if result is None or lua51.lua_type(result) != 'table':
				failures.append((source, 'file did not return a table'))
				continue
			for tableName, bindingKind in (('keyCommands', 'key'), ('axisCommands', 'axis')):
				entries = result[tableName]
				if entries is None or lua51.lua_type(entries) != 'table':
					continue
				for entry in entries.values():
					if lua51.lua_type(entry) != 'table':
						continue
					binding = _readBinding(entry, bindingKind)
					if binding is None:
						continue
					key = json.dumps(binding, sort_keys=True)
					merged.setdefault(key, (binding, set()))[1].add(source)

	bindings = []
	for binding, sources in merged.values():
		binding['sources'] = sorted(sources)
		bindings.append(binding)
	bindings.sort(key=lambda b: (b['deviceId'], b.get('down', b.get('action', 0)), b.get('name', ''), json.dumps(b, sort_keys=True)))
	return bindings, failures


# ── Listened-command extraction via lupa ───────────────────────────────────────

# Stand-ins for the engine API a device script sees.  GetSelf() records
# listen_command() calls; everything else returns an inert "magic" value that
# absorbs indexing, calls and arithmetic so system logic runs without effect.
_listenedCommandsLuaInit = r'''
	local function magic()
		local mt = {}
		mt.__index = function() return magic() end
		mt.__call = function() return magic() end
		mt.__add = function() return 0 end
		mt.__sub = function() return 0 end
		mt.__mul = function() return 0 end
		mt.__div = function() return 0 end
		mt.__unm = function() return 0 end
		mt.__concat = function() return '' end
		mt.__lt = function() return false end
		mt.__le = function() return false end
		mt.__len = function() return 0 end
		return setmetatable({}, mt)
	end
	_listened = {}
	local selfDevice = setmetatable({}, { __index = function(t, k)
		if k == 'listen_command' then
			return function(self, id) _listened[#_listened + 1] = id end
		end
		return function() return magic() end
	end })
	function GetSelf() return selfDevice end
	function GetDevice() return magic() end
	function get_base_data() return magic() end
	function get_param_handle() return magic() end
	function make_default_activity() end
	function _(s) return s end
	local realRequire = require
	function require(name)
		local ok, result = pcall(realRequire, name)
		if ok then return result end
		return setmetatable({ translate = function(s) return s end }, { __index = function() return function() return magic() end end })
	end
'''


def extractListenedCommands(lua, scriptsDir, extraLuaSetup=''):
	"""Capture the command IDs each scripted device registers with dev:listen_command().

	Reads the creators[] global left by device_init.lua in the given runtime and runs
	every creator that names a .lua script (avLuaDevice or a C++ class with a script)
	in a fresh sandbox, then calls post_initialize() if defined.  Non-numeric IDs
	(undefined sim-command globals) are dropped.

	Returns (listened, failures): sorted unique {deviceId, commandId} dicts, and
	(scriptFile, errorMessage) for scripts that raised; commands registered before
	the error are kept.
	"""
	creators = lua.globals().creators
	if creators is None:
		return [], []
	scriptsPath = scriptsDir.replace('\\', '/').rstrip('/') + '/'

	pairs = set()
	failures = []
	for deviceId in creators:
		entry = creators[deviceId]
		if lupa.lua_type(entry) != 'table' or not isinstance(entry[2], str) or not entry[2].endswith('.lua'):
			continue
		scriptPath = entry[2].replace('\\', '/')
		devLua = lupa.LuaRuntime(unpack_returned_tuples=True)
		devLua.execute(f'LockOn_Options = {{ script_path = "{scriptsPath}", common_script_path = "{scriptsPath}" }}')
		devLua.execute(_listenedCommandsLuaInit)
		if extraLuaSetup:
			devLua.execute(extraLuaSetup)
		try:
			devLua.globals().dofile(scriptPath)
			postInitialize = devLua.globals().post_initialize
			if postInitialize is not None:
				postInitialize()
		except Exception as e:
			failures.append((os.path.basename(scriptPath), str(e).splitlines()[0]))
		for commandId in devLua.globals()._listened.values():
			if isinstance(commandId, (int, float)) and not isinstance(commandId, bool):
				pairs.add((int(deviceId), int(commandId)))

	listened = [{'deviceId': deviceId, 'commandId': commandId} for deviceId, commandId in sorted(pairs)]
	return listened, failures
