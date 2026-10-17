# Lupa-Based Native Extraction — Findings

**Date:** 2026-04-18
**Context:** Replacing DCS BIOS pipeline with per-module native extraction scripts.

## Architecture Decision

Per-module self-contained extraction scripts (e.g. `tools/extract_FA18C.py`) instead of one unified script with module-specific branches. Rationale:

- Modules diverge significantly in command definition patterns (counter() vs hardcoded Keys), indicator layout, text field creation patterns, and required lupa mocks.
- Self-contained scripts are easier to debug and maintain — each one is ~400 lines and fully readable.
- Output format is standardized (`config/nativeExtractions/<module>.json`), so downstream consumers don't care which script produced it.

## Lupa Mock Requirements

### Always needed (clickabledata.lua chain):
- `LockOn_Options` (script_path, common_script_path)
- `class_type` (BTN=0, TUMB=1, LEV=2, MOVABLE_LEV=3, BTN_FIX=4, MULTY_TUMB=5)
- `BOX_SIDE_*` constants (X_top=1..Z_bottom=6)
- `get_option_value()` → returns false
- `require("i_18n")` → `{translate = identity}`
- Error-tolerant `dofile()` override

### Additional mocks for device_init.lua:
- `mount_vfs_model_path()`, `mount_vfs_texture_path()`, `mount_vfs_liveries_path()` — no-ops
- `get_param_handle(name)` → stub with `:set()` and `:get()` methods
- `get_aircraft_property_or_nil(name)` → `nil` (uses module defaults)
- `render_purpose` table (`GENERAL=0, BAKE=1, HUD_ONLY_VIEW=2, SCREENSPACE=3`)
- `indicator_types` table (`COMMON=0`)
- `update_screenspace_displacement()`, `try_find_assigned_viewport()`, `Copy()` — no-ops/identity

### Critical: dofile must tolerate runtime errors
The `dofile` override must use `pcall()` to catch runtime errors, not just loadfile failures. Reason: `device_init.lua` loads `materials.lua` → `fonts.lua` which references globals from missing font definition files (e.g. `symbol` from `symbols_locale.lua`). Without pcall, the entire device_init execution aborts before reaching the indicators section.

```lua
function dofile(path)
    local f, err = loadfile(path)
    if f then
        local ok, result = pcall(f)
        if ok then return result
        else io.stderr:write("Warning: Error executing " .. path .. ": " .. result .. "\n")
        end
    else
        io.stderr:write("Warning: Could not load " .. path .. ": " .. err .. "\n")
    end
end
```

## Indicator Extraction via Lupa (not regex)

Initial attempt used regex to parse `indicators[#indicators + 1] = {...}` from device_init.lua. This failed because:
- Multi-line entries with varying whitespace didn't match reliably
- Helmet indicators are added via `add_inds(maintenance_setup_HMS())` function calls, not direct array assignments — regex can't execute functions
- Bake conditionals depend on runtime config values

**Solution:** Execute device_init.lua via lupa and read the populated `indicators[]` table directly. This correctly handles:
- All conditional branches (helmet_option, bakeIndicators, bakeHUD)
- Function-based indicator additions (maintenance_setup_*)
- Runtime config values from config.lua

## Text Field Extraction (still regex)

Text fields from indicator page files are still extracted via regex, because page files use rendering APIs (CreateElement, Add, use_mipfilter) that would require extensive additional mocking. The regex approach works well here because the naming patterns are simple and consistent:
- `addStrPoly("name", ...)` — FA-18C IFEI
- `.name = "base"..format_expr` — FA-18C UFC (loop-generated names)
- Other patterns documented in `tools/extraction-guides/general.md`

## FA-18C Extraction Results

| Metric | Count |
|--------|-------|
| Devices | 71 |
| Command tables | 36 |
| Elements | 285 |
| Indicators | 13 (8 static + 1 HMS + 4 bake) |
| IFEI text fields | 24 |
| UFC text fields | 15 |
| Equipment properties | 1 (HelmetMountedDevice) |

Default config: `bakeIndicators=true`, `bakeHUD=false` → HUD bake excluded, 4 bake indicators added.
Default helmet: `nil` → defaults to 1 (HMS) → 1 HMD indicator added at index 8.

## F-4E Command Architecture

The F-4E is the only module (so far) that uses a single `device_subcommands` nested table instead
of per-device `*_commands` globals. A metatable proxy (`device_commands`) provides backward-compatible
lookup, but the canonical data is in `device_subcommands`, which is `local` to `command_defs.lua`.

Recovery technique: run this Lua snippet immediately after `dofile(clickabledata.lua)`:

```lua
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
```

This surfaces `device_subcommands` as a global that lupa can then read. The keys of
`device_subcommands` ARE the device names (matching `devices.lua`), so `deviceTableMap` is exact —
no access logger or name-similarity heuristic needed. 64/91 devices mapped exactly.

## `extraLuaSetup` pattern for `extractTextFieldsLupa()`

`extractTextFieldsLupa()` creates its own independent Lua sandbox (separate from `createLuaRuntime()`).
Mocks defined in `createLuaRuntime()` are NOT visible in that sandbox. Pass per-module extra mocks
via the `extraLuaSetup` parameter:

```python
f4eExtraSetup = '''
    local _guidCounter = 0
    function create_guid_string()
        _guidCounter = _guidCounter + 1
        return 'guid-' .. tostring(_guidCounter)
    end
    function GetRenderTarget() return 0 end
'''
# pass to every extractTextFieldsLupa() call for this module:
extractTextFieldsLupa(scriptsDir, initFile, extraLuaSetup=f4eExtraSetup)
```

The F-4E needs:
- `create_guid_string()` — called by `common_defs.lua` during page init.
- `GetRenderTarget()` returning `0` (a number, not a table) — F-4E pages do arithmetic on it
  (`GetRenderTarget() + 1`), unlike other modules that just call its `.width`/`.height` fields.

## Cross-Module Indicator Patterns

| Module | Static | Conditional | Bake | Text-bearing |
|--------|--------|-------------|------|-------------|
| FA-18C | 8 | 1 (helmet) | 4 | IFEI (24), UFC (15) |
| A-10C | 13 text-bearing (of 18 total) | 0 | 5 empty | CDU (1322), MFD×2 (727 each), HUD (1137), RWR (137), radios×4 (23 each), misc |
| F-16C | TBD | TBD (LCD) | TBD | DED, PFL |
| AH-64D | TBD | TBD (cameras) | TBD | EUFD, KU |
| Ka-50_3 | TBD | TBD | TBD | PVI, UV26 |
| F-4E | 18 total | 0 conditional | 2 bake (DSCG pilot/WSO) | 107 fields across 12 indicators |

## Output Files

- Extraction scripts: `tools/extract_<module>.py`
- Extraction guides: `tools/extraction-guides/general.md`, `tools/extraction-guides/<module>.md`
- Output JSON: `config/nativeExtractions/<module>.json`
- Schema documented in `tools/extraction-guides/general.md`

## Lua Array Tables With nil Holes (2026-10-04)

DCS clickable definitions often leave a slot `nil` when one sub-control has no value: Mi-24P `relative = {nil, true}`, F-15E `Mirror_Adjust_Control` `arg = {nil, 10}`, `stop_action = {nil, cmd}` on F-15E/F-4E/C-130J/A-4E-C, F-86F `class = {TUMB, nil, LEV}`.

- Do not walk a table with `t[i]` until the first `nil`: that silently drops everything after a leading hole (the Mi-24P radar altimeter knob lost `relative` and was mapped as `continuous`).  `extractUtils.luaTableToList` sizes the list by the largest positive integer key (`lupa` table `.keys()`; `lua51` runtimes return float keys) and keeps holes as `None`.
- Never filter `None` out of a per-sub-control list afterwards: that shifts later entries onto the wrong sub-control (the F-15E mirror's arg 10 moved from the LEV onto the BTN).  Map `None` to a neutral value instead (see `tools/extraction-guides/general.md`).
- `#t` on a table with holes is undefined in Lua, so DCS's own handling of a `nil` slot is not knowable from the Lua; the extraction keeps the slot and lets the generator treat it as absent.
- Audit trick: wrap each extractor module's `luaTableToList` reference, run its `main()` with `--output` to a temp file, and log every result that contains `None`.  On DCS 2.9.30 holes appear only in `stopAction`, `arg`, `relative`, `gain` and `controlClass`; `action` and `argValue` have none, so their `None` filters were left as-is.
