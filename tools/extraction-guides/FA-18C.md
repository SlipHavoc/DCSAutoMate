# DCS Native Control Extraction — FA-18C Hornet

Module-specific extraction notes for the FA-18C Hornet. Read `general.md` first for universal patterns.

## File Locations

- **Scripts directory:** `<DCS Install>/Mods/aircraft/FA-18C/Cockpit/Scripts/`
- **clickabledata.lua:** `Scripts/clickabledata.lua`
- **clickable_defs.lua:** `Scripts/clickable_defs.lua`
- **devices.lua:** `Scripts/devices.lua`
- **command_defs.lua:** `Scripts/command_defs.lua`
- **device_init.lua:** `Scripts/device_init.lua`
- **config.lua:** `Scripts/config.lua`

## Devices

71 devices total. Standard `counter()` pattern in `devices.lua`.

## Command Tables

36 tables, all using `counter()` pattern with `start_command = 3000`:

| Table | Count | Notes |
|-------|-------|-------|
| `device_commands` | 70 | Generic Button_1..Button_70 (loop generated) |
| `hotas_commands` | 54 | |
| `ctrl_commands` | 26 | |
| `elec_commands` | 62 | |
| `hydro_commands` | 2 | |
| `gear_commands` | 14 | |
| `fuel_commands` | 8 | |
| `cpt_commands` | 21 | |
| `extlights_commands` | 11 | |
| `cptlights_commands` | 28 | |
| `oxygen_commands` | 6 | |
| `ECS_commands` | 24 | |
| `engines_commands` | 20 | |
| `aau52_commands` | 1 | |
| `id2163a_commands` | 2 | |
| `sai_commands` | 7 | |
| `SMS_commands` | 18 | |
| `HUD_commands` | 22 | |
| `MDI_commands` | 27 | Includes MDI_PB_1..MDI_PB_20 loop |
| `AMPCD_commands` | 27 | Includes AMPCD_PB_1..AMPCD_PB_20 loop |
| `IFEI_commands` | 8 | |
| `clock_commands` | 3 | |
| `UFC_commands` | 37 | |
| `RADAR_commands` | 4 | |
| `INS_commands` | 2 | |
| `intercom_commands` | 44 | |
| `ky58_commands` | 10 | |
| `antsel_commands` | 4 | |
| `rwr_commands` | 13 | |
| `cmds_commands` | 4 | |
| `ASPJ_commands` | 2 | |
| `tgp_commands` | 7 | |
| `hmd_commands` | 4 | |
| `helmet_commands` | 2 | |
| `head_wrapper_commands` | 1 | |
| `mdl_commands` | 1 | |

Detection: iterate Lua globals, find tables whose values are all integers and whose names end in `_commands`.

## Elements

~285 clickable elements. Standard extraction from `lua.globals().elements`.

## Indicators

### Static indicators (always present):

| Lua Index | Indication ID | C++ Class | Init File | Device |
|-----------|--------------|-----------|-----------|--------|
| 1 | 0 | `F18::ccControlsIndicator_F18` | `ControlsIndicator/ControlsIndicator.lua` | `CONTROL_INTERFACE` |
| 2 | 1 | `F18::ccHUD_AVQ32_F18` | `Multipurpose_Display_Group/HUD_AVQ32/indicator/AVQ32_init.lua` | `HUD` |
| 3 | 2 | `F18::ccMPD_F18` | `Multipurpose_Display_Group/MDI_IP1556A/indicator/MDI_left_init.lua` | `MDI_LEFT` |
| 4 | 3 | `F18::ccMPD_F18` | `Multipurpose_Display_Group/MDI_IP1556A/indicator/MDI_right_init.lua` | `MDI_RIGHT` |
| 5 | 4 | `F18::ccAMPCD_F18` | `Multipurpose_Display_Group/AMPCD/indicator/AMPCD_init.lua` | `AMPCD` |
| 6 | 5 | `F18::ccIFEI_F18` | `IFEI/indicator/IFEI_init.lua` | `IFEI` |
| 7 | 6 | `F18::ccUFC_F18` | `UFC/indicator/UFC_init.lua` | `UFC` |
| 8 | 7 | `F18::ccRWR_ALR67_F18` | `TEWS/indicator/RWR_ALR67_init.lua` | `RWR` |

### Conditional indicators — helmet (index 9+, depends on `get_aircraft_property_or_nil("HelmetMountedDevice")`):

The `helmet_option` variable controls which HMD indicators are added. Only one set is active per mission configuration.

| Value | Meaning | Function Called | Indicators Added |
|-------|---------|----------------|-----------------|
| `nil` (default) | Defaults to `1` | `maintenance_setup_HMS()` | HMS indicators |
| `0` | VISOR | `maintenance_setup_VISOR()` | VISOR indicators |
| `1` | HMS | `maintenance_setup_HMS()` | HMS/HMD indicators |
| `2` | NVG | `maintenance_setup_NVG()` | NVG indicators |

Since the default is HMS (nil → 1), the extraction script uses `helmet_option = 1` which yields 1 HMS indicator at index 9 (indication ID 8). We could also leave it nil and get the same result.

The `maintenance_setup_*()` functions are called via `add_inds()` which appends to the `indicators[]` array. The exact content of these functions varies and needs to be confirmed; for the extraction script, we set `helmet_option = 1` and let device_init.lua execute normally.

### Conditional indicators — bake (after helmet, depends on `bakeIndicators` and `bakeHUD` from config.lua):

`config.lua` sets `bakeIndicators = true` and `bakeHUD = false`.

With these defaults:

| Rel. Index | C++ Class | Init File (relative to Scripts/) | Device | Condition |
|------------|-----------|-----------|--------|-----------|
| — | `F18::ccMDG_IndicatorBake_F18` | `Multipurpose_Display_Group/HUD_AVQ32/indicator/BAKE/HUD_AVQ32_bake_init.lua` | `HUD` | `bakeIndicators AND bakeHUD` — **skipped** (bakeHUD is false) |
| +1 | `F18::ccMDG_IndicatorBake_F18` | `Multipurpose_Display_Group/MDI_IP1556A/indicator/BAKE/MDI_left_bake_init.lua` | `MDI_LEFT` | `bakeIndicators` |
| +2 | `F18::ccMDG_IndicatorBake_F18` | `Multipurpose_Display_Group/MDI_IP1556A/indicator/BAKE/MDI_right_bake_init.lua` | `MDI_RIGHT` | `bakeIndicators` |
| +3 | `F18::ccMDG_IndicatorBake_F18` | `Multipurpose_Display_Group/AMPCD/indicator/BAKE/AMPCD_bake_init.lua` | `AMPCD` | `bakeIndicators` |
| +4 | `F18::ccRWR_ALR67_Bake_F18` | `TEWS/indicator/BAKE/RWR_ALR67_bake_init.lua` | `RWR` | `bakeIndicators` |

With defaults (bakeIndicators=true, bakeHUD=false), 4 bake indicators are added. The HUD bake is skipped.

### Default total indicator count: 8 static + 1 helmet (HMS) + 4 bake = 13

### Known useful indication IDs:

| Indication ID | Indicator | Used By Scripts? |
|---------------|-----------|-----------------|
| 5 | IFEI | Yes (RPM L/R readings) |
| 6 | UFC | Possible (scratchpad, option displays) |

## Text Field Extraction

### IFEI (indication ID 5)

Init file: `IFEI/indicator/IFEI_init.lua`

Page files and text fields (via `addStrPoly("name", ...)`):

**IFEI_MAIN_page.lua** (20 fields):
- `txt_RPM_R`, `txt_RPM_L`
- `txt_TEMP_R`, `txt_TEMP_L`
- `txt_FF_R`, `txt_FF_L`
- `txt_OilPress_R`, `txt_OilPress_L`
- `txt_FUEL_UP`, `txt_FUEL_DOWN`, `txt_FUEL_L`, `txt_FUEL_R`
- `txt_BINGO`
- `txt_CLOCK_H`, `txt_CLOCK_M`, `txt_CLOCK_S`
- `txt_TIMER_H`, `txt_TIMER_M`, `txt_TIMER_S`
- `txt_Z`

**IFEI_SP_page.lua** (2 fields):
- `txt_Codes`
- `txt_SP`

**IFEI_TIME_SET_page.lua** (5 fields):
- `txt_T`
- `txt_TimeSetMode`
- `txt_CLOCK_H`, `txt_CLOCK_M`, `txt_CLOCK_S`

**Deduplicated unique fields** (24): txt_RPM_R, txt_RPM_L, txt_TEMP_R, txt_TEMP_L, txt_FF_R, txt_FF_L, txt_OilPress_R, txt_OilPress_L, txt_FUEL_UP, txt_FUEL_DOWN, txt_FUEL_L, txt_FUEL_R, txt_BINGO, txt_CLOCK_H, txt_CLOCK_M, txt_CLOCK_S, txt_TIMER_H, txt_TIMER_M, txt_TIMER_S, txt_Z, txt_Codes, txt_SP, txt_T, txt_TimeSetMode

### UFC (indication ID 6)

Init file: `UFC/indicator/UFC_init.lua`

Single page file: `UFC/indicator/UFC_main_page.lua`

Text fields (via `.name = "..."` on `CreateElement "ceStringPoly"`):
- `UFC_OptionDisplay1` through `UFC_OptionDisplay5` (loop: `"UFC_OptionDisplay"..display_id`)
- `UFC_OptionCueing1` through `UFC_OptionCueing5` (loop: `"UFC_OptionCueing"..display_id`)
- `UFC_ScratchPadString1Display`
- `UFC_ScratchPadString2Display`
- `UFC_ScratchPadNumberDisplay`
- `UFC_Comm1Display`
- `UFC_Comm2Display`

**Non-text elements** (exclude from field list):
- `UFC_MainDummy` (ceSimple)
- `UFC_mask` (ceMeshPoly)

**Note on loop-generated names:** The base names in the source code are `"UFC_OptionDisplay"` and `"UFC_OptionCueing"`. At runtime they become `UFC_OptionDisplay1`..`5` and `UFC_OptionCueing1`..`5` via Lua string concatenation with the loop index. The extraction script regex captures the base name only. We handle this by either:
1. Regex-matching the concatenation pattern (`"name"..expr`) and expanding it
2. Hardcoding the known loop range (1-5) when the base name pattern is detected
3. Simply listing the full names in the module guide (preferred — we already know them)

## Equipment Properties

Only one property is checked:
- `HelmetMountedDevice` — values: nil (→1), 0 (VISOR), 1 (HMS), 2 (NVG)

## FA-18C-Specific Extraction Notes

### Additional lupa mocks needed:
- `bakeIndicators` and `bakeHUD` globals — set by config.lua, can be pre-set or loaded via dofile
- `render_purpose` table — used in device_init.lua
- `indicator_types` table — used in device_init.lua
- `writeParameter()` — no-op, called to record indicator indices
- `get_aircraft_property_or_nil()` — return nil (lets default HMS be selected)
- `maintenance_setup_HMS/NVG/VISOR()` — defined earlier in device_init.lua, will be available if we execute from the top
- `add_inds()` / `add_devs()` — defined in device_init.lua, will be available if we execute from the top

### Command table identification:
All 36 tables use `counter()` with `start_command = 3000`. They are all global after executing clickabledata.lua (which dofile's command_defs.lua). Detect by iterating globals, checking for tables with all-integer values and names matching `*_commands`.

### Config.lua defaults:
```lua
bakeIndicators = true
bakeHUD = false
```

### writeParameter calls and their values:
These record indicator indices for cross-references:
- `HUD_INDICATOR_INDEX` = 1 (before HUD indicator is added → indicates next index)
- `LMDI_INDICATOR_INDEX` = 2
- `RMDI_INDICATOR_INDEX` = 3
- `AMPCD_INDICATOR_INDEX` = 4
- `RWR_INDICATOR_INDEX` = 7 (before RWR is added)
