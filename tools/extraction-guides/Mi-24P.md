# DCS Native Control Extraction — Mi-24P Hind

Module-specific extraction notes for the Mi-24P Hind. Read `general.md` first for universal patterns.

## File Locations

- **Scripts directory:** `<DCS Install>/Mods/aircraft/Mi-24P/Cockpit/Scripts/`
- **clickabledata.lua:** `Scripts/clickabledata.lua`
- **clickable_defs.lua:** `Scripts/clickable_defs.lua`
- **devices.lua:** `Scripts/devices.lua`
- **command_defs.lua:** `Scripts/command_defs.lua`
- **device_init.lua:** `Scripts/device_init.lua`
- **sounds.lua:** `Scripts/sounds.lua`
- **mainpanel_init.lua:** `Scripts/mainpanel_init.lua`
- **lamps.lua:** `Scripts/lamps.lua` (loaded by mainpanel_init.lua)

Uses the standard `Cockpit/Scripts/` path, same as FA-18C.

## Devices

73 devices total. Standard `counter()` pattern in `devices.lua`.

This is a dual-seat helicopter (pilot rear, operator/gunner front). Several device pairs share command tables but are distinguished by _P/_O suffixes in the device name:

| Device Name | ID | Notes |
|---|---|---|
| ELEC_INTERFACE | 1 | Electrical system |
| FUELSYS_INTERFACE | 2 | Fuel system |
| ENGINE_INTERFACE | 3 | Engine/rotor/APU |
| HYDRO_SYS_INTERFACE | 4 | Hydraulic system |
| EJECT_SYS_INTERFACE | 5 | Ejection system |
| WEAP_SYS | 6 | Weapons system (pilot + operator controls) |
| I9K113 | 7 | 9K113 Shturm ATGM guidance |
| DISS_15 | 8 | Doppler navigator |
| ASO_2V | 9 | Countermeasures |
| AUTOPILOT | 10 | Autopilot |
| CPT_MECH | 11 | Cockpit mechanics (doors, fans, wipers) |
| RADAR_ALTIMETER | 12 | RV-5 radar altimeter |
| FIRE_EXTING_INTERFACE | 13 | Fire extinguisher |
| MISC_SYSTEMS_INTERFACE | 14 | Miscellaneous |
| EXT_LIGHTS_SYSTEM | 15 | External lights |
| ASP_17V | 16 | ASP-17V gunsight |
| PKV | 17 | PKV operator sight |
| UKT_2 | 18 | UKT-2 |
| SPUU_52 | 19 | SPUU-52 tail rotor pitch limiter |
| SOUND_SYSTEM | 20 | Sound system |
| KNEEBOARD | 21 | Kneeboard |
| HEAD_WRAPPER | 22 | Head tracker |
| INT_LIGHTS_SYSTEM | 23 | Internal lights |
| MGV1SU | 24 | Gyro platform common |
| MGV1SU_1 | 25 | Gyro platform 1 |
| MGV1SU_2 | 26 | Gyro platform 2 |
| GREBEN | 27 | Greben compass system |
| ID6 | 28 | ID-6 |
| ECS_INTERFACE | 29 | Environmental control |
| HELPER_AI | 30 | Petrovich AI helper |
| OXYGEN_INTERFACE | 31 | Oxygen system |
| PKP72M_P | 32 | PKP-72M pilot ADI |
| PKP72M_O | 33 | PKP-72M operator ADI |
| PKP72M_INTERFACE | 34 | PKP-72M interface |
| CLOCK_P | 35 | Pilot clock |
| CLOCK_O | 36 | Operator clock |
| FM_PROXY | 37 | Flight model proxy |
| IAS_P | 38 | Pilot airspeed indicator |
| IAS_O | 39 | Operator airspeed indicator |
| VARIOMETER | 40 | Variometer |
| BAROALT_P | 41 | Pilot barometric altimeter |
| BAROALT_O | 42 | Operator barometric altimeter |
| RMI2_P | 43 | Pilot RMI-2 |
| RMI2_O | 44 | Operator RMI-2 |
| MAP_DISPLAY | 45 | Map display |
| ARC_15 | 46 | ARC-15 radio common |
| ARC_15_PANEL_P | 47 | ARC-15 pilot panel |
| ARC_15_PANEL_O | 48 | ARC-15 operator panel |
| R_863 | 49 | R-863 radio |
| JADRO_1I | 50 | Jadro-1I HF radio |
| EUCALYPT_M24 | 51 | R-828 Eucalyptus radio |
| R_852 | 52 | R-852 radio |
| G_Meter | 53 | G-meter |
| ARC_U2 | 54 | ARC-U2 radio |
| SPU_8 | 55 | SPU-8 intercom |
| RS_Proxy | 56 | RS proxy |
| IFF | 57 | IFF transponder |
| Recorder_MC61 | 58 | MC-61 flight recorder |
| VMS | 59 | Voice message system (RI-65) |
| ANTI_ICE_INTERFACE | 60 | Anti-icing system |
| EXT_CARGO_EQUIPMENT | 61 | External cargo |
| SARPP12I1 | 62 | SARPP flight recorder |
| SIGHT_DOORS | 63 | Sight doors |
| SIGNAL_FLARES | 64 | Signal flares |
| MACROS | 65 | Macros |
| STANDBY_COMPASS | 66 | Standby compass |
| SPO_10 | 67 | SPO-10 RWR |
| KM_2 | 68 | KM-2 compass |
| NVG | 69 | Night vision goggles |
| TIMER | 70 | Timer |
| EXTERNAL_CARGO_SPEECH | 71 | External cargo speech |
| CREW_INDICATOR | 72 | Crew indicator |
| R60_INTERFACE | 73 | R-60 missile interface |

### Dual-seat device pairs

Several instruments and panels are duplicated for pilot (P) and operator (O). These pairs share a command table, so the generator produces prefixed names to disambiguate:

| Pilot Device | Operator Device | Shared Table |
|---|---|---|
| CLOCK_P (35) | CLOCK_O (36) | `timers_commands` |
| IAS_P (38) | IAS_O (39) | (none — unmatched, uses global unique) |
| BAROALT_P (41) | BAROALT_O (42) | `baroaltimeter_commands` |
| PKP72M_P (32) | PKP72M_O (33) | `pkp72m_commands` |
| RMI2_P (43) | RMI2_O (44) | `rmi2_commands` |
| ARC_15_PANEL_P (47) | ARC_15_PANEL_O (48) | `arc15_commands` |

## Command Tables

50 tables total: 49 standard `*_commands` tables plus a `Keys` table (global key commands with fixed integer IDs, 487 entries). All `*_commands` tables use the `counter()` pattern with `start_command = 3000`.

| Table | Count | Notes |
|---|---|---|
| `ARC_U2_commands` | 10 | ARC-U2 radio |
| `AntiIceSys_commands` | 20 | Anti-icing system |
| `G_Meter_commands` | 2 | G-meter |
| `IFF_6201_commands` | 15 | IFF transponder |
| `Keys` | 487 | Global key commands (fixed IDs, **not** start_command pattern) |
| `R60_commands` | 7 | R-60 missile |
| `RI65_commands` | 6 | RI-65 voice message system |
| `RecorderMC61_commands` | 9 | MC-61 recorder |
| `SARPP_commands` | 1 | SARPP recorder |
| `SPO_commands` | 7 | SPO-10 RWR |
| `SPU_8_Mi24_commands` | 32 | SPU-8 intercom |
| `arc15_commands` | 27 | ARC-15 radio |
| `asp_commands` | 51 | ASP-17V gunsight |
| `autopilot_commands` | 72 | Autopilot |
| `avASO_2V_commands` | 14 | ASO-2V countermeasures |
| `avKM_2_commands` | 5 | KM-2 compass |
| `baroaltimeter_commands` | 2 | Barometric altimeter |
| `cockpit_mechanics_commands` | 56 | Doors, fans, wipers |
| `device_commands` | 120 | Generic Button_1..Button_120 (loop generated) |
| `diss_commands` | 31 | DISS-15 Doppler |
| `ecs_commands` | 23 | Environmental control |
| `elec_commands` | 132 | Electrical system |
| `engine_commands` | 91 | Engine/rotor/APU |
| `eucalypt_commands` | 14 | R-828 Eucalyptus radio |
| `ext_cargo_equipment_commands` | 24 | External cargo |
| `ext_lights_commands` | 27 | External lights |
| `fire_commands` | 30 | Fire protection |
| `fmproxy_commands` | 3 | Flight model proxy |
| `fuel_commands` | 43 | Fuel system |
| `greben_commands` | 16 | Greben compass |
| `headwrapper_commands` | 13 | Head tracker |
| `helperai_commands` | 19 | Petrovich AI helper |
| `hydraulic_commands` | 35 | Hydraulic system |
| `i9K113_commands` | 72 | 9K113 Shturm ATGM |
| `int_lights_commands` | 51 | Internal lights |
| `jadro_commands` | 29 | Jadro-1I HF radio |
| `map_display_commands` | 12 | Map display |
| `mgv1su_commands` | 6 | Gyro platform |
| `pki_commands` | 8 | PKI/PKV operator sight |
| `pkp72m_commands` | 3 | PKP-72M ADI |
| `pkp72m_interface_commands` | 9 | PKP-72M interface |
| `r852_commands` | 6 | R-852 radio |
| `r863_commands` | 20 | R-863 radio |
| `ralt_commands` | 7 | Radar altimeter |
| `rmi2_commands` | 6 | RMI-2 |
| `signal_flares_commands` | 20 | Signal flares |
| `spuu_commands` | 12 | SPUU-52 |
| `timers_commands` | 14 | Clocks/timers |
| `ukt2_commands` | 3 | UKT-2 |
| `weapon_commands` | 113 | Weapons system |

### The Keys table

Unlike `*_commands` tables, the `Keys` table in `command_defs.lua` uses fixed integer IDs (not `counter()`). It contains 487 global key commands like `iCommandPlaneEject`, `iCommandPlaneAutopilot`, etc. The extraction script detects it by name (`Keys`) rather than the `*_commands` suffix pattern.

### Device-table matching

The generator matches 51 of 73 devices to command tables. The 22 unmatched devices fall into these categories:

1. **Instrument-only devices** with no matching command table name: CLOCK_P/O, IAS_P/O, BAROALT_P/O, VARIOMETER, STANDBY_COMPASS. Their elements still resolve via global unique command ID lookup.
2. **System devices** with no clickable elements: SOUND_SYSTEM, KNEEBOARD, NVG, MACROS, RS_Proxy, EXTERNAL_CARGO_SPEECH, CREW_INDICATOR, SIGHT_DOORS, VMS.
3. **Devices with dissimilar table names**: EJECT_SYS_INTERFACE, MISC_SYSTEMS_INTERFACE, PKV, ID6, OXYGEN_INTERFACE. These resolve via global unique lookup.

The `TABLE_ABBREV` map handles the main cross-naming gaps:

```python
TABLE_ABBREV = {
    'cockpitmechanics': 'cptmech',     # cockpit_mechanics_commands → CPT_MECH
    'hydraulic': 'hydrosys',            # hydraulic_commands → HYDRO_SYS_INTERFACE
    'weapon': 'weapsys',                # weapon_commands → WEAP_SYS
    'ralt': 'radaraltimeter',           # ralt_commands → RADAR_ALTIMETER
    'avaso2v': 'aso2v',                 # avASO_2V_commands → ASO_2V
    'avkm2': 'km2',                     # avKM_2_commands → KM_2
}
```

## Elements

514 clickable elements. Standard extraction from `lua.globals().elements`.

### Crew member access

Mi-24P elements include a `crew_member_access` field (0 = pilot, 1 = operator) that distinguishes which seat can interact with the control. The existing mapping uses `plt`/`op` prefixes to reflect this.

### Heavily used suffixes

command_defs.lua makes extensive use of `_EXT` and `_ITER` suffixes for alternative input methods. The generator strips these suffixes and prefers the base name. For example:
- `ACGroundPower` (base) + `ACGroundPowerEXT` + `ACGroundPowerITER`
- Only `ACGroundPower` is used for naming.

## Indicators

10 indicators total: 9 standard + 1 bake (MapDisplay).

| Index | C++ Class | Device | Init File | Fields | Notes |
|---|---|---|---|---|---|
| 0 | `Mi24::cc9K113` | I9K113 | `9K113_CAM/9K113_CAM_init.lua` | 4 | Shturm ATGM camera |
| 1 | `Mi24::ccPKV` | PKV | `PKV/Indicator/PKV_init.lua` | 0 | Operator sight |
| 2 | `Mi24::ccASP17` | ASP_17V | `ASP17V/Indicator/ASP_17V_init.lua` | 0 | Pilot gunsight |
| 3 | `Mi24::ccControlsIndicator` | AUTOPILOT | `ControlsIndicator/ControlsIndicator.lua` | 14 | Autopilot/controls display |
| 4 | `Mi24::ccMapDisplay_Mi24` | MAP_DISPLAY | `MapDisplay/MapDisplay.lua` | 3 | Navigation map |
| 5 | `ccIndicator` | (none) | `MapDisplay/bake/init.lua` | 0 | Bake indicator for map display |
| 6 | `Mi24::ccHelperAIIndicator_Mi24` | HELPER_AI | `HelperAI/HelperAI_indicator.lua` | 0 | Petrovich AI overlay |
| 7 | `Mi24::ccHelperAIIndicator_Mi24` | HELPER_AI | `HelperAI/HelperAI_indicator_VR.lua` | 0 | Petrovich AI overlay (VR) |
| 8 | `Mi24::ccGunnersCPanel` | WEAP_SYS | `AI/ControlPanel/g_panel.lua` | 8 | Gunner's control panel |
| 9 | `Mi24::ccCrewIndicator` | CREW_INDICATOR | `CrewIndicator/crew_indicator_init.lua` | 0 | Crew indicator |

**No conditional indicators.** The Mi-24P does not use `get_aircraft_property_or_nil()` in device_init.lua. All 10 indicators are always present.

**One bake indicator** (index 5): MapDisplay bake. Skipped by the generator since bake indicators are rendering-only.

## Text Field Extraction

29 text fields across 3 indicators:

### 9K113 Camera (indication ID 0) — 4 fields

| Field Name | Purpose |
|---|---|
| `txt_NABLTips` | ATGM observation tooltips |
| `BG_9k113_Orange` | Orange status background |
| `BG_9k113_Green` | Green status background |
| `txt_Tips` | General tooltips |

### Controls Indicator (indication ID 3) — 14 fields

| Field Name | Purpose |
|---|---|
| `txt_brakes` | Brake status |
| `wheel_brake_mask` | Wheel brake mask |
| `wheel_brake` | Wheel brake indicator |
| `txt_autopilot` | Autopilot status |
| `txt_autopilot_hover` | Autopilot hover mode |
| `autopilot_base` | Autopilot base indicator |
| `txt_goes_left` | Left trim indicator |
| `txt_goes_right` | Right trim indicator |
| `au_roll_position` | Roll position |
| `au_pitch_position` | Pitch position |
| `txt_chan_name0` | Channel name 0 |
| `txt_chan_name1` | Channel name 1 |
| `txt_chan_name2` | Channel name 2 |
| `txt_chan_name3` | Channel name 3 |

### Map Display (indication ID 4) — 3 fields

| Field Name | Purpose |
|---|---|
| `text_dist` | Distance readout |
| `text_time` | Time readout |
| `text_az` | Azimuth readout |

### Gunner's Control Panel (indication ID 8) — 8 fields

| Field Name | Purpose |
|---|---|
| `txt_Status` | Gunner status |
| `txt_Hints` | Gunner hints |
| `mem_base` | Memory base indicator |
| `txt_mem` | Memory text |
| `txt_status` | Status text |
| `txt_ammo` | Ammo count |
| `txt_burst` | Burst count |
| `txt_Gunner_Key` | Gunner key bindings |

## Gauges and Lamps

460 gauges and lamps extracted from mainpanel_init.lua. This is by far the largest gauge set of any extracted module, due to the Mi-24P's extensive analog instrument suite and warning light panels.

### Warning_Lights and Cabin_Lights enum tables

mainpanel_init.lua loads `lamps.lua` which defines two Lua enum tables used for naming gauges:

- **Warning_Lights** — Warning/caution panel lamp indices (e.g. `MASTER_CAUTION = 1`, `L_ENG_FIRE = 2`, etc.)
- **Cabin_Lights** — Cabin lighting indices

The extraction script builds reverse maps from these enums to name gauges that use `WarningLights` or `CockpitLights` controllers with parameter indices. Gauges not matching either enum fall back to global variable name lookup or `gauge_arg_N` naming.

### Gauge overlap with elements

12 gauges overlap with clickable elements (same arg number). These are skipped during control mapping generation to avoid duplicates.

## Equipment Properties

None. The Mi-24P does not use `get_aircraft_property_or_nil()` in device_init.lua.

## Mi-24P-Specific Extraction Notes

### common_script_path mocking

mainpanel_init.lua loads `common_script_path.."devices_defs.lua"` and `common_script_path.."tools.lua"` which are at `Scripts/Aircrafts/_Common/Cockpit/`. The extraction script sets `common_script_path = script_path` so the dofile fails silently (the files are not at that location). All needed functions from those files (`indicator_types`, `render_purpose`, `clear_mode_table`, `get_page_by_mode_global`) are pre-mocked.

### Additional lupa mocks needed

Beyond the standard mocks (see `general.md`):
- **`sounds.lua`** — Must be executed before clickable_defs.lua to define `SOUND_*` constants.
- **`SnapViews` / `ViewSettings`** — Stub tables needed for mainpanel_init.lua execution.
- **`find_custom_livery()`** — No-op function returning empty string.
- **`LoRegisterPanelControls()`** — Returns an auto-vivifying metatable.
- **`kneeboard_implementation`** and **`disable_kneeboard_render_target`** — Simple global stubs.
- **`require("i_18n")`** — Intercepted to return `{ translate = function(s) return s end }`.
- **`clear_mode_table()`** — Used by indicator page files, pre-mocked.
- **`get_page_by_mode_global()`** — Used by indicator page files, pre-mocked.
- **`create_material_type_table()`** — Returns auto-vivifying metatable, used in indicator pages.
- **`set_material_type()`** — No-op.

### Harmless warnings during extraction

The following warnings appear during extraction and are expected:
- `Could not load .../Fonts/symbols_locale.lua` — Font file not present in module
- `Could not load .../Fonts/fonts_cmn.lua` — Font file not present in module
- `Error executing .../fonts.lua: ...attempt to index...` — Cyrillic font constant error, no impact
- `Could not load .../KNEEBOARD/declare_kneeboard_device.lua` — Kneeboard device file
- `Could not load .../devices_defs.lua` — Common script (pre-mocked)
- `Could not load .../tools.lua` — Common script (not needed)

### Generator name overrides

Three command names are too generic and need explicit overrides:

```python
CONTROL_NAME_OVERRIDES = {
    (19, 3010): 'spuuPower',    # spuu_commands On_Off → too generic
    (27, 3007): 'grebenMatch',  # greben_commands MATCH → too generic
    (16, 3015): 'usrPower',     # asp_commands USR → too short
}
```

### Leading abbreviation casing fix

The Mi-24P exposed a bug in `cmdNameToCamelCase` where PascalCase names with leading multi-character abbreviations were split wrong: `ACGeneratorLeft` became `aCGeneratorLeft` instead of `acGeneratorLeft`. The fix detects leading uppercase runs of 2+ chars followed by an uppercase+lowercase pair (e.g. `AC` + `Ge`) and lowercases the entire abbreviation prefix. This was applied in `generate_Mi24P.py` only (other modules should adopt it if they encounter similar names).

### Existing mapping had DCS BIOS plt/op prefixes

The old DCS BIOS mapping used `plt` and `op` prefixes (e.g. `pltDBattR`, `opFan`). The native extraction generates names based on Lua command names and device names, which naturally include pilot/operator distinction through the device name prefix mechanism (shared tables produce prefixed names like `arc15PanelPMode`, `arc15PanelOMode`). The nameMap contains 934 old→new renames.

### Weapon system controls span pilot and operator

WEAP_SYS (device 6) contains controls for both seats. Lua command names include `Pilot_*` and `Operator_*` prefixes (e.g. `Pilot_SWITCHER_FIRE_CONTROL`, `Operator_CHAIN_LENGTH_SHORT_MED_LONG`). The generator's `cmdNameToCamelCase` produces names like `pilotSwitcherFireControl`, `operatorChainLengthShortMedLong`. The old mapping used `pltPuvlCannonFireRate` / `opBurstLength` style — the nameMap bridges these.
