# DCS Native Control Extraction — AV-8B Night Attack Harrier

Module-specific extraction notes for the AV-8B N/A Harrier. Read `general.md` first for universal patterns.

## File Locations

- **Scripts directory:** `<DCS Install>/Mods/aircraft/AV8BNA/Cockpit/`
- **clickabledata.lua:** `Cockpit/clickabledata.lua`
- **clickable_defs.lua:** `Cockpit/clickable_defs.lua`
- **devices.lua:** `Cockpit/devices.lua`
- **command_defs.lua:** `Cockpit/command_defs.lua`
- **device_init.lua:** `Cockpit/device_init.lua`
- **sounds.lua:** `Cockpit/sounds.lua`
- **mainpanel_init.lua:** `Cockpit/mainpanel_init.lua`

**Important:** Unlike FA-18C (which uses `Cockpit/Scripts/`), the AV8BNA has all Lua files directly in `Cockpit/`. The extraction script sets `scriptsRelPath = 'Mods/aircraft/AV8BNA/Cockpit'`.

## Devices

44 devices total. Standard `counter()` pattern in `devices.lua`.

| Device Name | ID | Notes |
|---|---|---|
| ELECTRIC | 1 | |
| COMM1 | 2 | |
| COMM2 | 3 | |
| INTERCOM | 4 | |
| TACAN | 5 | |
| AWLS | 6 | |
| RSC | 7 | |
| ACNIP | 8 | |
| DECS | 9 | |
| ADC | 10 | |
| NAV_INS | 11 | |
| MSC | 12 | |
| VREST | 13 | |
| NAVFLIR | 14 | |
| TGTPOD | 15 | |
| DMT | 16 | |
| RWR | 17 | |
| RWRCONTROL | 18 | |
| FLIGHTINSTRUMENTS | 19 | |
| EDP | 20 | |
| FQIS | 21 | |
| HUDCONTROL | 22 | |
| UFCCONTROL | 23 | |
| ODUCONTROL | 24 | |
| EHSD_MAP | 25 | |
| MPCD_LEFT | 26 | |
| MPCD_RIGHT | 27 | |
| FLIGHTCONTROLS | 28 | |
| SMC | 29 | Stores Management Computer |
| EWS | 30 | |
| CBTSYST | 31 | |
| TVWPNS | 32 | |
| LTEXT | 33 | External lights |
| LTINT | 34 | Internal lights |
| LTWCA | 35 | Warning/caution/advisory lights |
| ECS | 36 | |
| HYDRAULIC | 37 | |
| NETWORKINTERFACE | 38 | |
| ANVIS9 | 39 | NVG |
| AUTOSTART | 40 | |
| DAMAGE_CONTROL | 41 | |
| ATHS | 42 | |
| IRHSD | 43 | |
| DATAPARAMS | 44 | |

## Command Tables

26 tables, all using `counter()` pattern with `start_command = 3000`:

| Table | Count | Notes |
|---|---|---|
| `acnip_commands` | 15 | |
| `ecs_commands` | 5 | |
| `edp_commands` | 2 | |
| `elec_commands` | 7 | |
| `engine_commands` | 37 | |
| `ext_light_commands` | 15 | |
| `fcs_commands` | 25 | Flight control system |
| `fqi_commands` | 2 | Fuel quantity indication |
| `hotas_commands` | 5 | |
| `hud_commands` | 10 | |
| `inst_commands` | 4 | |
| `int_light_commands` | 15 | |
| `misc_commands` | 20 | |
| `mpcd_l_commands` | 29 | Left MPCD |
| `mpcd_r_commands` | 29 | Right MPCD |
| `msc_commands` | 6 | |
| `odu_commands` | 5 | Option Display Unit |
| `psp_commands` | 3 | |
| `radio_commands` | 7 | |
| `rear_right_panel_commands` | 6 | |
| `rwr_commands` | 3 | |
| `smc_commands` | 22 | Stores Management Computer |
| `stores_commands` | 1 | |
| `ufc_commands` | 34 | Up-Front Controller |
| `vrs_commands` | 2 | |
| `wc_lights_commands` | 2 | Warning/caution lights |

Detection: iterate Lua globals, find tables whose values are all integers and whose names end in `_commands`.

## Elements

248 clickable elements. Standard extraction from `lua.globals().elements`.

## Indicators

### All indicators (no conditional or bake indicators):

| Lua Index | Indication ID | C++ Class | Init File | Device | Fields |
|---|---|---|---|---|---|
| 1 | 0 | `Displays::ccHUDM` | (HUD main) | — | 0 |
| 2 | 1 | `Displays::ccHUDRL` | (HUD repeater left) | — | 0 |
| 3 | 2 | `Displays::ccHUDRR` | (HUD repeater right) | — | 0 |
| 4 | 3 | `Displays::ccMPCDL` | (MPCD left) | MPCD_LEFT | 0 |
| 5 | 4 | `Displays::ccMPCDR` | (MPCD right) | MPCD_RIGHT | 0 |
| 6 | 5 | `Displays::ccUFC` | (UFC display) | — | 4 |
| 7 | 6 | `Displays::ccODU` | (ODU display) | — | 10 |
| 8 | 7 | `Displays::ccUVHF` | (UHF/VHF radio) | — | 13 |
| 9 | 8 | `ccControlsIndicatorAV8B` | (controls indicator) | — | 0 |

**No conditional indicators.** Unlike the FA-18C (which has conditional helmet and bake indicators), the AV8BNA has a fixed set of 9 indicators. No equipment properties are checked, so there's no branching logic in device_init.lua.

**No bake indicators.** The AV8BNA doesn't use bake rendering for any of its displays.

### Default total indicator count: 9 (all static)

## Text Field Extraction

Only 3 of the 9 indicators have text fields (27 total fields across the three).

### UFC (indication ID 5) — 4 fields

| Field Name | Purpose |
|---|---|
| `ufc_left_position` | Left scratchpad display |
| `ufc_right_position` | Right scratchpad display |
| `ufc_right_alpha_position` | Right alpha display |
| `ufc_numeric_output` | Numeric output display |

### ODU (indication ID 6) — 10 fields

| Field Name | Purpose |
|---|---|
| `ODU_Option_1_Slc` | Option 1 selection cue |
| `ODU_Option_1_Text` | Option 1 text |
| `ODU_Option_2_Slc` | Option 2 selection cue |
| `ODU_Option_2_Text` | Option 2 text |
| `ODU_Option_3_Slc` | Option 3 selection cue |
| `ODU_Option_3_Text` | Option 3 text |
| `ODU_Option_4_Slc` | Option 4 selection cue |
| `ODU_Option_4_Text` | Option 4 text |
| `ODU_Option_5_Slc` | Option 5 selection cue |
| `ODU_Option_5_Text` | Option 5 text |

### UVHF (indication ID 7) — 13 fields

| Field Name | Purpose |
|---|---|
| `uvhf_left_position` | Left display |
| `uvhf_channel` | Channel number |
| `uvhf_freq_left` | Frequency left portion |
| `uvhf_freq_scolon` | Frequency separator |
| `uvhf_freq_right` | Frequency right portion |
| `acnip_1_label_mode` | ACNIP 1 mode label |
| `acnip_1_mode` | ACNIP 1 mode value |
| `acnip_1_label_code` | ACNIP 1 code label |
| `acnip_1_code` | ACNIP 1 code value |
| `acnip_2_label_mode` | ACNIP 2 mode label |
| `acnip_2_mode` | ACNIP 2 mode value |
| `acnip_2_label_code` | ACNIP 2 code label |
| `acnip_2_code` | ACNIP 2 code value |

Note: The UVHF indicator combines radio frequency display with ACNIP (IFF) fields in a single display panel.

## Gauges and Lamps

Only 1 gauge extracted from mainpanel_init.lua:

| Name | Arg | Input | Output | Controller |
|---|---|---|---|---|
| `mirrors_draw` | 983 | [0, 1] | [1, 0] | `mirrors_draw` |

The AV8BNA's mainpanel_init.lua is minimal. There are no CautionLights or InternalLights enum tables to reverse-map (unlike the FA-18C), though the extraction script handles them generically if they ever appear.

## Equipment Properties

None. The AV8BNA does not use `get_aircraft_property_or_nil()` in its device_init.lua.

## AV8BNA-Specific Extraction Notes

### Cockpit directory structure

The most important difference from FA-18C: Lua files live directly in `Cockpit/`, not `Cockpit/Scripts/`. The extraction script's `scriptsRelPath` must be `'Mods/aircraft/AV8BNA/Cockpit'` rather than `'Mods/aircraft/AV8BNA/Cockpit/Scripts'`.

### Additional lupa mocks needed

Beyond the standard mocks (see `general.md`):
- **`sounds.lua`** — Must be executed before clickable_defs.lua to define `SOUND_*` constants. The extraction script does `dofile("sounds.lua")` during `createLuaRuntime()`.
- **`SnapViews` / `ViewSettings`** — Stub tables needed for mainpanel_init.lua execution.
- **`find_custom_livery()`** — No-op function returning empty string, needed for mainpanel_init.lua.
- **`LoRegisterPanelControls()`** — Returns an auto-vivifying metatable, needed for mainpanel_init.lua.
- **`kneeboard_implementation`** and **`disable_kneeboard_render_target`** — Simple global stubs.
- **`require("i_18n")`** — Intercepted to return `{ translate = function(s) return s end }`.

### Command table naming

The generator script uses `TABLE_ABBREV` to map abbreviated command table names to device names for device↔table matching. Currently only 3 generic abbreviations are defined: `ctrl` → `control`, `hydro` → `hydraulic`, `antsel` → `antennaselector`. The AV8BNA tables generally match their device names closely enough that these mappings aren't critical, but the fuzzy matching handles cases like `mpcd_l_commands` → `MPCD_LEFT`.

### Known quirks from migration

From the module conversion pipeline notes:
- **RWR_VOL** — Originally extracted as raw int16 value. Verify the generated mapping handles volume controls correctly.
- **BINGO_SET** — Originally came through as a relative string value. Check that the generator assigns the correct control type.

### No conditional logic

Unlike the FA-18C (which has conditional helmet indicators and bake rendering), the AV8BNA extraction is straightforward: no branching in device_init.lua, no equipment property checks, no bake indicators. This makes it the simplest module to extract among those currently supported.
