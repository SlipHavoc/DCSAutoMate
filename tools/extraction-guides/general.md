# DCS Native Control Extraction — General Guide

This document describes the universal patterns found across DCS World aircraft modules for extracting control definitions, indicator/display data, command names, and device mappings directly from the native Lua files. Each per-module extraction script should follow these patterns, adapting where the module diverges.

## Overview

Every DCS aircraft module has a `Cockpit/Scripts/` directory (sometimes just `Cockpit/`) containing Lua files that define the cockpit's interactive elements, devices, commands, and displays. The key files are:

| File | Purpose |
|------|---------|
| `clickabledata.lua` | Control element definitions (switches, buttons, knobs, axes) |
| `clickable_defs.lua` | Helper functions for creating control elements (dofile'd by clickabledata.lua) |
| `devices.lua` | Device name → device ID mapping |
| `command_defs.lua` | Command name → command ID tables |
| `device_init.lua` | Device controllers (`creators[]`), display indicators (`indicators[]`), equipment property checks |
| `config.lua` | Module configuration flags (bake settings, LCD flags, etc.) |

## Extraction Approach: Lupa

We use [lupa](https://github.com/scoder/lupa) (Python Lua runtime) to execute the DCS Lua files in a sandboxed environment. This is more reliable than regex parsing because it correctly handles:
- `counter()` auto-incrementing IDs
- `for` loops generating dynamic entries (e.g., MFD OSB buttons 1-20)
- `dofile()` chains across multiple files
- Conditional blocks (`if modification == "Ka-50_3" then ...`)
- String concatenation for dynamic names

The DCS Lua files depend on engine-provided globals that don't exist outside DCS, so we mock them.

## Required Lupa Mocks

### Always needed (for clickabledata.lua):
```python
# LockOn_Options — path configuration
LockOn_Options = {
    script_path = "<scriptsDir>/",
    common_script_path = "<scriptsDir>/",
}

# class_type — clickable element type constants
class_type = {
    BTN = 0, TUMB = 1, LEV = 2, MOVABLE_LEV = 3,
    BTN_FIX = 4, MULTY_TUMB = 5,
}

# BOX_SIDE — VR interaction zone constants
BOX_SIDE_X_top = 1, BOX_SIDE_X_bottom = 2,
BOX_SIDE_Y_top = 3, BOX_SIDE_Y_bottom = 4,
BOX_SIDE_Z_top = 5, BOX_SIDE_Z_bottom = 6

# get_option_value() — returns false
# require("i_18n") — returns { translate = identity }
# dofile() — override with error-tolerant version
```

### Additional mocks for device_init.lua:
```python
# indicators[] — must exist as a global table before device_init.lua runs
indicators = {}

# get_aircraft_property_or_nil() — return nil (default config)
# writeParameter() — no-op (records indicator index params)
# render_purpose — rendering mode constants
render_purpose = { GENERAL = 0, BAKE = 1, HUD_ONLY_VIEW = 2, SCREENSPACE = 3 }

# indicator_types — indicator type constants
indicator_types = { COMMON = 0 }

# update_screenspace_displacement() — no-op
# try_find_assigned_viewport() — no-op
# Copy() — identity function (used in some modules)
```

### Module-specific mocks:
Some modules need additional globals. Document these in the per-module extraction guide and add them inline in the extraction script.

## Data Extraction Steps

### Step 1: Extract devices (from devices.lua)

All modules use the same pattern:
```lua
local count = 0
local function counter() count = count + 1; return count end
devices = {}
devices["ELEC_INTERFACE"] = counter()  -- 1
devices["FUEL_INTERFACE"] = counter()  -- 2
-- ...
```

After executing via lupa, read `lua.globals().devices` and convert to `{name: id}` dict.

### Step 2: Extract elements (from clickabledata.lua)

`clickabledata.lua` typically does `dofile()` on `clickable_defs.lua`, `devices.lua`, `command_defs.lua`, and `sounds.lua`, then populates an `elements` table:
```lua
elements["GEAR-PTR"] = default_2_position_tumb("Landing gear", devices.GEAR_INTERFACE, gear_commands.GearHandle, 71)
```

After execution, iterate `lua.globals().elements` and extract per element:
- `hint` (string) — human-readable description
- `device` (int) — device ID
- `action` (list of int) — command IDs
- `arg` (list of int) — animation argument numbers
- `arg_value` (list of float) — step values per action
- `arg_lim` (list of [min, max]) — argument value limits
- `class` (list of int) — class_type values, map back to names (BTN, TUMB, LEV, etc.)
- `stop_action` (list of int, optional) — release command IDs
- `cycle` (bool or list, optional) — whether the control cycles
- `gain` (list of float, optional) — axis sensitivity
- `relative` (list of bool, optional) — whether the axis is relative
- `use_release_message` (list of bool, optional) — whether release sends a command

### Step 3: Extract command tables (from command_defs.lua)

**Modern modules** (FA-18C, F-16C, AH-64D) use `counter()` pattern:
```lua
start_command = 3000
local count = start_command
local function counter() count = count + 1; return count end
elec_commands = { BattSw = counter(); LGenSw = counter(); ... }
```

After executing clickabledata.lua (which dofile's command_defs.lua), iterate Lua globals looking for tables that contain only integer values and whose names end in `_commands`. Extract `{tableName: {commandName: commandId}}`.

**Legacy modules** (Ka-50_3) use hardcoded `Keys` table:
```lua
Keys = { PlaneGear = 68, PowerBattery1 = 309, ... }
```
Check for a `Keys` global table and extract if present.

### Step 4: Extract indicators (from device_init.lua)

The `indicators[]` array is a Lua 1-indexed array. Each entry is a table:
```lua
indicators[#indicators + 1] = {
    "F18::ccIFEI_F18",                              -- [1] C++ class name
    LockOn_Options.script_path.."IFEI/init.lua",    -- [2] init Lua file path
    devices.IFEI,                                    -- [3] device reference
    {viewports, options}                             -- [4] optional render config
}
```

**Indication ID = Lua array index - 1** (0-based). So `indicators[6]` → `list_indication(5)`.

To extract indicators, either:
1. Execute device_init.lua via lupa with additional mocks, then read the populated `indicators` table
2. Parse device_init.lua with regex (simpler, module-specific patterns can be hardcoded)

For the FA-18C extraction script, we use approach #2 (regex) because the additional lupa mocks needed for device_init.lua are extensive and module-specific. The indicator layout is stable (changes only on DCS updates).

### Step 5: Extract text field names from indicator page files

Each indicator's init file defines `page_subsets[]` pointing to page Lua files:
```lua
page_subsets[id_pagesubset.MAIN] = LockOn_Options.script_path.."IFEI/indicator/IFEI_MAIN_page.lua"
```

Page files create text elements using `ceStringPoly` with a name. The field name is what `list_indication(id)` returns at runtime.

**Known text element creation patterns** (across all investigated modules):

| Pattern | Example Module | Regex |
|---------|---------------|-------|
| `addStrPoly("name", ...)` | FA-18C IFEI | `addStrPoly\s*\(\s*"([^"]+)"` |
| `addText("name", ...)` | F-16C DED | `addText\s*\(\s*"([^"]+)"` |
| `AddText("name", ...)` | AH-64D EUFD | `AddText\s*\(\s*"([^"]+)"` |
| `AddTextTable("name", ...)` | AH-64D EUFD | `AddTextTable\s*\(\s*"([^"]+)"` |
| `MakeStringPoly("name")` | Ka-50_3 PVI | `MakeStringPoly\s*\(\s*"([^"]+)"` |
| `addBigText("name", ...)` | AH-64D TEDAC | `addBigText\s*\(\s*"([^"]+)"` |
| `.name = "fieldName"` | FA-18C UFC | `\.name\s*=\s*"([^"]+)"` |

**Combined regex** (use case-sensitive matching):
```
(?:addStrPoly|addText|AddText|AddTextTable|MakeStringPoly|addBigText)\s*\(\s*"([^"]+)"
```
Plus separately: `\.name\s*=\s*"([^"]+)"` for direct property assignments.

**Filtering:**
- Exclude names ending in `_back` (shadow layer duplicates in AH-64D TEDAC)
- Exclude `ceSimple` and `ceMeshPoly` element names (not text fields) — only include names associated with `ceStringPoly`
- Some names are generated dynamically in loops (e.g., `"UFC_OptionDisplay"..display_id`). The regex captures only the base name without the loop index. Note these in the per-module guide and handle in the extraction script.

## Standardized Output JSON Schema

All per-module extraction scripts must produce this schema:

```json
{
    "module": "<moduleName>",
    "scriptsDir": "<absolute path to Cockpit/Scripts>",
    "devices": {
        "<deviceName>": <deviceId>,
        ...
    },
    "commandTables": {
        "<tableName>": {
            "<commandName>": <commandId>,
            ...
        },
        ...
    },
    "elements": {
        "<elementKey>": {
            "hint": "<description>",
            "device": <deviceId>,
            "action": [<commandId>, ...],
            "arg": [<argNumber>, ...],
            "argValue": [<stepFloat>, ...],
            "argLim": [[<min>, <max>], ...],
            "controlClass": ["BTN"|"TUMB"|"LEV"|"MOVABLE_LEV"|"BTN_FIX"|"MULTY_TUMB", ...],
            "stopAction": [<commandId>, ...],
            "cycle": <bool>,
            "gain": [<float>, ...],
            "relative": [<bool>, ...],
            "useReleaseMessage": [<bool>, ...]
        },
        ...
    },
    "indicators": [
        {
            "index": <0-based indication ID>,
            "cppClass": "<C++ class name>",
            "initFile": "<relative path from scriptsDir>",
            "deviceId": <deviceId or null>,
            "deviceName": "<device name or null>",
            "fields": ["<fieldName>", ...],
            "conditional": "<condition description or null>",
            "bake": <bool>
        },
        ...
    ],
    "equipmentProperties": ["<propertyName>", ...],
    "stats": {
        "totalElements": <int>,
        "totalDevices": <int>,
        "totalCommandTables": <int>,
        "totalIndicators": <int>,
        "totalIndicationFields": <int>
    }
}
```

**Notes:**
- `elements` optional fields (`stopAction`, `cycle`, `gain`, `relative`, `useReleaseMessage`) are only included when present/non-default.
- `elements` lists stay index-aligned per sub-control even when the Lua table has `nil` holes (e.g. Mi-24P `relative = {nil, true}`, F-15E `arg = {nil, 10}`): a `nil` becomes `0` in `arg` (DCS's own "no arg" value) and `stopAction` (no stop action), `false` in `relative`/`useReleaseMessage`, and `null` in `gain` and `controlClass`.
- `indicators[].fields` contains deduplicated text field names found across all page files for that indicator.
- `indicators[].conditional` is a human-readable description of the condition (e.g., `"helmet_option == 1 (HMS)"`) or `null` if unconditional.
- `indicators[].bake` is `true` for render-to-texture indicators that should be excluded from `list_indication()` queries.
- `equipmentProperties` lists all `get_aircraft_property_or_nil()` property names found in device_init.lua.

## Bake Indicator Detection

Bake indicators are render-to-texture entries that pre-render displays for GPU performance. They should be flagged (`"bake": true`) but NOT excluded from the indicators array — their position affects the indices of subsequent indicators.

Detection strategies (varies by module):
- **Init file path contains "BAKE/"** (FA-18C, Ka-50_3)
- **Wrapped in `if USE_LCD_MFD` conditional** (F-16C)
- **Class name contains "Bake" or "LCD"** (FA-18C `ccMDG_IndicatorBake_F18`, AH-64D `ccMFD_LCD_AH64`)
- **Camera indicators** (AH-64D PNVS_CAM, TADS_CAM, RMAP_CAM, MAP_CAM — identifiable by "CAM" in class name or init path containing "Cameras/")

## Conditional Indicator Handling

Include ALL conditional variants in the indicators array. This means:
- For helmet options: include HMS, NVG, and VISOR indicators (whichever apply to the module)
- For LCD/bake conditionals: include both the main indicator and the LCD variant
- For modification variants: include all modification variants

The extraction script should document what each conditional is, but include all entries. At runtime, the T: command on an indicator index returns data if the indicator exists in the current mission, or null if not.

**Important:** When `get_aircraft_property_or_nil()` returns nil (our mock default), the script's conditional logic may skip adding some indicators. To capture ALL conditional indicators, either:
1. Run the extraction multiple times with different property values and merge results
2. Parse the conditional blocks via regex and hardcode the known indicator entries
3. Set the mock to return the value that includes the most indicators

Per-module scripts should document which approach they use.

## Cross-Module Patterns Reference

| Aspect | Modern (FA-18C, F-16C, AH-64D) | Legacy (Ka-50_3) |
|--------|------|--------|
| Command tables | `*_commands = { Name = counter() }` | `Keys = { Name = N }` hardcoded |
| Element commands | `*_commands.CommandName` | `device_commands.Button_N` |
| Naming source | Command table names | Hint text (fallback) |
| Device names | `devices["NAME"] = counter()` | Same |
| Indicator array | `indicators[#indicators+1] = {...}` | Same |

## Hint Text Localization

The `_()` wrapper in DCS Lua is a standard `gettext` localization function.  In most modules the
hint strings in `clickabledata.lua` are already plain English (e.g. `_("Battery switch")`), so
the `_()` call is a no-op identity and the hint text is the human-readable label.

**CH-47F exception:** CH-47F uses localization *keys* as hints (e.g. `_("Cockpit.CH47.OCLP.MODE_SW")`).
The human-readable label ("MODE SEL Switch") is resolved at engine runtime through the DCS localization
system.  It is **not** in the aircraft module's own `l10n/en/LC_MESSAGES/messages.mo` (that file only
has ~96 entries for mission names and UI strings).  Instead it lives in the **DCS engine's global
catalog**: `<DCS Install>/l10n/en/LC_MESSAGES/dcs.mo`, which contains 400+ CH-47-specific entries.

This file can be read from Python:
```python
import gettext
t = gettext.GNUTranslations(open(r'C:/Games/DCS World/l10n/en/LC_MESSAGES/dcs.mo', 'rb'))
label = t.gettext('Cockpit.CH47.OCLP.MODE_SW')  # → 'MODE SEL Switch'
catalog = t._catalog  # {key: resolved_text}
```

**Impact on extraction:** When a module uses localization keys as hints, the raw key is preserved in
`hintKey` (so users can search `clickabledata.lua` by the exact Lua key) while `hint` is replaced
with the resolved English label (so users can find controls by what they see in the cockpit tooltip).
Modules with plain-English hints do not have a `hintKey` field — their `hint` is already the label.
