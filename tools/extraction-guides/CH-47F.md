# DCS Native Control Extraction — CH-47F Chinook

Module-specific extraction notes for the CH-47F Chinook (Block 1). Read `general.md` first for
universal patterns.

## File Locations

- **Scripts directory:** `<DCS Install>/Mods/aircraft/CH-47F/Cockpit/Scripts/`
- **GCBase scripts directory:** `<DCS Install>/Mods/aircraft/GCBase/Cockpit/Scripts/`
  (a separate shared module that CH-47F depends on — see Quirks below)
- **clickabledata.lua:** `Scripts/clickabledata.lua`
- **devices.lua:** `Scripts/devices.lua`
- **command_defs.lua:** `Scripts/command_defs.lua`
- **device_init.lua:** `Scripts/device_init.lua`
- **mainpanel_init.lua:** `Scripts/mainpanel_init.lua`
- **config.lua:** `Scripts/config.lua`
- **sounds.lua:** `Scripts/sounds.lua`
- **VR_config.lua:** `Scripts/VR_config.lua`

There is no `clickable_defs.lua` — helper functions are defined inline in `clickabledata.lua`.

## DCS Module Name

- **Install directory:** `CH-47F`
- **DCS aircraft type (runtime):** `CH-47Fbl1` (from `entry.lua` line 55: `type = "CH-47Fbl1"`)
- **Extraction output filename:** `config/nativeExtractions/CH-47Fbl1.json`
- **Control mapping filename:** `config/controlMappings/CH-47Fbl1.json`

Always use `CH-47Fbl1` (not `CH-47F`) for module name references in JSON files and
`--module` arguments to validation tools.

## Devices

78 devices total. Standard `counter()` pattern in `devices.lua`.
27 of the 78 devices appear in `clickabledata.lua` and have deterministic `deviceTableMap` entries.
The remaining 51 devices are indicator-only or input-only and do not appear as clickable elements.

## Command Tables

Only **2** command tables (much simpler than most modules):

| Table | Count | Notes |
|-------|-------|-------|
| `device_commands` | 300 | Single generic table: `Button_1` through `Button_300`, all at base offset 3000 |
| `Keys` | 4 | Standard DCS keys table |

Unlike most modern modules, CH-47F has no per-system named command tables
(`elec_commands`, `fuel_commands`, etc.). All commands go through the single generic
`device_commands` table. This means all canonical names take the form
`DEVICE_NAME.Button_N` rather than `DEVICE_NAME.CommandName`.

## Elements

907 clickable elements. Standard extraction from `lua.globals().elements`.

Deterministic `deviceTableMap`: 27/78 devices resolved from 1109 logged accesses and 907 element
spans.

## Hint Text Localization (CH-47F-specific quirk)

CH-47F uses **localization keys** as hint text in `clickabledata.lua`, not plain English.
For example:
```lua
elements["OCLP_MODE"] = animated_multiposition_switch_limited_small(
    ..., _("Cockpit.CH47.OCLP.MODE_SW"), ...)
```

The in-cockpit tooltip reads "MODE SEL Switch" — but that string is **not** in the aircraft
module's own `l10n/` folder. It lives in the DCS engine's global catalog:

```
<DCS Install>/l10n/en/LC_MESSAGES/dcs.mo
```

This `.mo` file has 400+ CH-47-specific entries (keys matching `Cockpit.CH47.*`). The engine's
`_()` function resolves keys across all loaded catalogs at runtime.

The extractor handles this by calling `loadDcsTranslations(dcsDir)` to read `dcs.mo` via Python's
`gettext.GNUTranslations`. For each element, if the raw hint key resolves to a different string:
- `hint` is replaced with the human-readable label (e.g. `"MODE SEL Switch"`)
- `hintKey` is added with the original Lua key (e.g. `"Cockpit.CH47.OCLP.MODE_SW"`)

This means:
- Searching the control mapping for "MODE SEL Switch" works (matches the tooltip)
- Searching `clickabledata.lua` for "Cockpit.CH47.OCLP.MODE_SW" finds the native definition

Elements with plain-English hints (some radio/CDU buttons use literal strings) have no `hintKey`.
Total elements with resolved `hintKey`: ~819 of 907.

## GCBase Dependency

`device_init.lua` calls `get_sim_plugin_path("GCBase")` to load the GCBase shared module, which
provides base CDU, MFD, and indicator infrastructure. The extractor must:

1. Point `LockOn_Options.common_script_path` at `GCBase/Cockpit/Scripts/` (not the CH-47F scripts
   dir) so that `dofile(LockOn_Options.common_script_path .. "tools.lua")` resolves correctly.
2. Compute the GCBase **module root** (two levels above Scripts:
   `Scripts/ → Cockpit/ → GCBase/`) and return it from `get_sim_plugin_path("GCBase")`.
   The subsequent path construction `path .. "/Cockpit/Scripts/"` then yields the correct GCBase
   scripts path.

Getting the GCBase path wrong (e.g. one level instead of two) causes `dofile` failures and
silent indicator extraction errors.

## `devices.WEAPON_SYS` Missing

`VR_config.lua` (dofile'd by `clickabledata.lua`) references `devices.WEAPON_SYS`, but this key
does not exist in `devices.lua`. The extractor injects a dummy value:
```python
lua.execute('if devices == nil then devices = {} end; devices.WEAPON_SYS = 999')
```
This is safe — VR_config.lua only uses it for a `send_to_device` field in VR_capture entries,
which are not extracted.

## `LockOn_Options.flight` Required

Both `device_init.lua` and `mainpanel_init.lua` access `LockOn_Options.flight.easy_radar` and
`LockOn_Options.flight.auto_lockon`. The extractor includes:
```python
LockOn_Options.flight = { easy_radar = false, auto_lockon = false }
```

## Indicators

28 indicators total.

The CDU, MFD, GH3000 altimeter, and APR-39 indicator init files call `get_sim_plugin_path`
recursively inside the `extractTextFieldsLupa` fresh Lua contexts, where it isn't mocked.
These 4 indicators yield 0 text fields. All 268 indication fields come from the other indicators
(VPM, cargo, interphone panels, etc.) and are correctly extracted.

### Notable indicators (partial):

| Index | C++ Class | Init File | Notes |
|-------|-----------|-----------|-------|
| 0, 1 | `CH47Fbl1::ccCDU_CH47Fbl1` | `GCBase/…/CDU/` | Yields 0 fields (get_sim_plugin_path in fresh context) |
| 2, 3 | `ccIndicator` | `GCBase/…/CDU/` | Yields 0 fields |
| 4 | `CH47Fbl1::ccVPM_CH47Fbl1` | `MFD/indicator/VPM/VPM_init.lua` | |

## Gauges and Lamps (mainpanel_init.lua)

53 gauges and lamps extracted from `mainpanel_init.lua` via the `CreateGauge` mock.

The two lamps for `ELECTRICAL_UTILITY_PRESSURE` (arg 562) and `ELECTRICAL_APU_READY` (arg 563)
referenced in `CH-47F_dcsbios.py` have **no corresponding entries in the native Lua files**. They
are not in `clickabledata.lua`, `device_init.lua`, or `mainpanel_init.lua`. Their arg numbers and
canonical names must be determined via live DCS arg monitoring (`tools/monitorArgs.py`) during
Phase 4 validation.

## Extractor-Specific Mocks Required

Beyond the standard mocks listed in `general.md`:

| Mock | Reason |
|------|--------|
| `LockOn_Options.flight = {easy_radar=false, auto_lockon=false}` | device_init.lua / mainpanel_init.lua |
| `get_sim_plugin_path("GCBase")` → GCBase module root | device_init.lua indicator chain |
| `LockOn_Options.common_script_path` → GCBase scripts path | tools.lua dofile resolution |
| `latin`, `materials`, `fonts`, `fontdescription`, `textures` — auto-keying proxy tables | fonts.lua, materials.lua (GCBase) |
| `devices.WEAPON_SYS = 999` | VR_config.lua |
| `sounds.lua` dofile'd before `clickabledata.lua` | Defines SOUND_* constants |
| `CreateGauge()`, `LoRegisterPanelControls()` | mainpanel_init.lua gauge extraction |
| `create_material_type_table()`, `set_material_type()`, `clear_mode_table()`, `get_page_by_mode_global()` | Indicator page init files |

## Radio Wheel Slave Animation (vhf_radio_wheel)

The CH-47F VHF-AM radio frequency selectors (`ARC186_FREQ1`–`ARC186_FREQ4`) use a
`vhf_radio_wheel` helper defined inline in `clickabledata.lua`. This helper sets up a
**master/slave display-arg pair** exactly like the A-10C `radio_wheel` helper:

- The **command arg** (e.g. 1225 for FREQ1) is the pulse counter used by `send_clickable_data`.
  Its `arg_value = {-0.1, 0.1}` gives the per-click increment sent to DCS.
- The **slave display arg** (e.g. 1229 for FREQ1) is what you see move in the cockpit. The
  `slave_animation` spec carries `{slaveArg, {lim0, lim1}, scale}` — e.g.
  `{1229, {0.125, 0.775}, 0.5}` means arg 1229 spans [0.125, 0.775] and moves at 0.5× the
  command value per click.

The extractor calls both `extractSlaveAnimation` (for arg numbers) and
`extractSlaveAnimationMeta` (for lim/scale) so the generator can compute:
- `argLim = [0.125, 0.775]` (display range, not [0,1])
- `step = |incValue| × scale = 0.1 × 0.5 = 0.05`
- `settleDelay` from `animationSpeed` (hardcoded 0.5 arg-units/sec → 0.1 s)

Without `extractSlaveAnimationMeta`, the generator falls back to `incValue` (0.1) as the
step and [0,1] as the argLim — both wrong for FREQ1. The other three selectors (FREQ2–4)
happen to have scale=1.0 and lim=[0,1], so they would look correct either way.

## Extractor Output

```
Devices: 78
Command tables: 2
Elements: 907
Indicators: 28
Indication fields: 268
Gauges and lamps: 53
```
