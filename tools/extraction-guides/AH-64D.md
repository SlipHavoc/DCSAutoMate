# DCS Native Control Extraction — AH-64D Apache

Module-specific extraction notes for the AH-64D Block II Apache. Read `general.md` first for universal patterns.

## File Locations

- **Scripts directory:** `<DCS Install>/Mods/aircraft/AH-64D/Cockpit/Scripts/`
- **clickabledata.lua:** `Scripts/clickabledata.lua`
- **clickable_defs.lua:** `Scripts/clickable_defs.lua`
- **devices.lua:** `Scripts/devices.lua`
- **command_defs.lua:** `Scripts/command_defs.lua`
- **device_init.lua:** `Scripts/device_init.lua`
- **sounds.lua:** `Scripts/sounds.lua`
- **mainpanel_init.lua:** `Scripts/mainpanel_init.lua`
- **lamps.lua:** `Scripts/MainPanel/lamps.lua` (loaded by mainpanel_init.lua)

Uses the standard `Cockpit/Scripts/` path.

## Devices

91 devices total. Standard `counter()` pattern in `devices.lua`.

This is a dual-seat helicopter (pilot rear, CPG front). Many devices are tripled — a PLT instance, a CPG instance, and an INPUT instance — because each crew station has its own display/keyboard unit but shares the same command table.

| Device Name | ID | Notes |
|---|---|---|
| FM_PROXY | 1 | Flight model proxy |
| CONTROL_INTERFACE | 2 | Flight controls |
| ELEC_INTERFACE | 3 | Electrical system |
| FUEL_INTERFACE | 4 | Fuel system |
| HYDRO_INTERFACE | 5 | Hydraulic system |
| ENGINE_INTERFACE | 6 | Engine/rotor/APU |
| GEAR_INTERFACE | 7 | Landing gear |
| OXYGEN_INTERFACE | 8 | Oxygen system |
| CPT_MECH | 9 | Cockpit mechanics (doors, canopy) |
| EXTLIGHTS_SYSTEM | 10 | External lights |
| CPTLIGHTS_SYSTEM | 11 | Internal lights (**note:** mapped to `intlights_commands` via device name override) |
| ECS_INTERFACE | 12 | Environmental control |
| SAI | 13 | Standby attitude indicator |
| IAS | 14 | Indicated airspeed |
| BARO_ALTIMETER | 15 | Barometric altimeter |
| STANDBY_COMPASS | 16 | Standby compass |
| FATgage | 17 | Free air temperature gauge |
| GPS1 | 18 | GPS 1 |
| GPS2 | 19 | GPS 2 |
| EGI1 | 20 | EGI 1 |
| EGI2 | 21 | EGI 2 |
| MUX | 22 | Multiplexer bus |
| HOTAS_PLT | 23 | Pilot HOTAS |
| HOTAS_CPG | 24 | CPG HOTAS |
| HOTAS_INPUT | 25 | HOTAS input |
| IHADSS | 26 | IHADSS helmet display |
| SP_PLT | 27 | Signal processor pilot |
| SP_CPG | 28 | Signal processor CPG |
| KU_PLT | 29 | Keyboard unit pilot |
| KU_CPG | 30 | Keyboard unit CPG |
| KU_INPUT | 31 | Keyboard unit input |
| ELC1 | 32 | Electronic limiter 1 |
| ELC2 | 33 | Electronic limiter 2 |
| HIADC | 34 | HI ADC |
| FMC | 35 | Flight management computer |
| WP1 | 36 | Weapons processor 1 |
| WP2 | 37 | Weapons processor 2 |
| DP_PLT | 38 | Display processor pilot |
| DP_CPG | 39 | Display processor CPG |
| HMD | 40 | Helmet mounted display |
| HMD_INPUT | 41 | HMD input |
| MFD_PLT_LEFT | 42 | Pilot left MPD (**note:** MFD in code, MPD in Apache nomenclature) |
| MFD_PLT_RIGHT | 43 | Pilot right MPD |
| MFD_CPG_LEFT | 44 | CPG left MPD |
| MFD_CPG_RIGHT | 45 | CPG right MPD |
| MFD_INPUT_LEFT | 46 | MPD input left |
| MFD_INPUT_RIGHT | 47 | MPD input right |
| EUFD_PLT | 48 | Pilot EUFD |
| EUFD_CPG | 49 | CPG EUFD |
| EUFD_INPUT | 50 | EUFD input |
| TEDAC | 51 | TEDAC (CPG sensor display) |
| TEDAC_INPUT | 52 | TEDAC input |
| DRVS_ASN157 | 53 | Doppler navigation |
| RADALT | 54 | Radar altimeter |
| ADF_ARN_149 | 55 | ADF ARN-149 |
| EMERGENCY_PANEL | 56 | Emergency panel |
| UHF_RADIO | 57 | UHF radio |
| VHF_AM_RADIO | 58 | VHF AM radio |
| FM1 | 59 | FM radio 1 |
| FM2 | 60 | FM radio 2 |
| HF_RADIO | 61 | HF radio |
| COMM_PANEL_CPG | 62 | CPG comm panel |
| COMM_PANEL_PLT | 63 | Pilot comm panel |
| COMM_PANEL_INPUT | 64 | Comm panel input |
| CIU | 65 | Communications interface unit |
| IFF | 66 | IFF transponder |
| INTERCOM | 67 | Intercom |
| TADS | 68 | TADS (target acquisition) |
| PNVS | 69 | PNVS (pilot night vision) |
| PNVS_TURRET_CONTROL | 70 | PNVS turret control |
| FCR | 71 | Fire control radar |
| RFI | 72 | Radar frequency interferometer |
| GUN_TURRET_CONTROL | 73 | Gun turret control |
| PYLONS_INPUT | 74 | Pylon input |
| JETT_PANEL_PLT | 75 | Pilot jettison panel |
| JETT_PANEL_CPG | 76 | CPG jettison panel |
| JETT_PANEL_INPUT | 77 | Jettison panel input |
| HELLFIRE_INTERFACE | 78 | Hellfire missile interface |
| AN_APR39 | 79 | AN/APR-39 RWR |
| CMWS | 80 | CMWS countermeasures |
| BRU_PLT | 81 | Pilot BRU |
| BRU_CPG | 82 | CPG BRU |
| MACROS | 83 | Macros |
| KNEEBOARD | 84 | Kneeboard |
| ARCADE | 85 | Arcade mode |
| NVG | 86 | Night vision goggles |
| PrestonAI | 87 | AI copilot (George) |
| HEAD_WRAPPER | 88 | Head tracker |
| DATA_TRANSFER_UNIT | 89 | Data transfer unit |
| IDM | 90 | Improved data modem |
| AN_AVR2A | 91 | AN/AVR-2A laser warning |

### Dual-seat device triples

The AH-64D uses a PLT/CPG/INPUT triple pattern rather than just PLT/CPG pairs. The INPUT device typically handles the actual command routing, while PLT and CPG represent the crew-specific instances. These all share a single command table:

| PLT Device | CPG Device | INPUT Device | Shared Table |
|---|---|---|---|
| HOTAS_PLT (23) | HOTAS_CPG (24) | HOTAS_INPUT (25) | `hotas_commands` |
| KU_PLT (29) | KU_CPG (30) | KU_INPUT (31) | `KU_commands` |
| MFD_PLT_LEFT (42) | MFD_CPG_LEFT (44) | MFD_INPUT_LEFT (46) | `mpd_commands` |
| MFD_PLT_RIGHT (43) | MFD_CPG_RIGHT (45) | MFD_INPUT_RIGHT (47) | `mpd_commands` |
| EUFD_PLT (48) | EUFD_CPG (49) | EUFD_INPUT (50) | `eufd_commands` |
| COMM_PANEL_PLT (63) | COMM_PANEL_CPG (62) | COMM_PANEL_INPUT (64) | `comm_commands` |
| JETT_PANEL_PLT (75) | JETT_PANEL_CPG (76) | JETT_PANEL_INPUT (77) | `JETT_commands` |
| BRU_PLT (81) | BRU_CPG (82) | — | `BRU_commands` |

### MFD → MPD device name override

The DCS module uses `MFD_*` for internal device names, but the Apache's multi-purpose displays are correctly called MPDs. The generator uses `DEVICE_NAME_OVERRIDES` to remap:

```python
DEVICE_NAME_OVERRIDES = {
    'MFD_PLT_LEFT': 'MPD_PLT_LEFT',
    'MFD_PLT_RIGHT': 'MPD_PLT_RIGHT',
    'MFD_CPG_LEFT': 'MPD_CPG_LEFT',
    'MFD_CPG_RIGHT': 'MPD_CPG_RIGHT',
    'MFD_INPUT_LEFT': 'MPD_INPUT_LEFT',
    'MFD_INPUT_RIGHT': 'MPD_INPUT_RIGHT',
    'CPTLIGHTS_SYSTEM': 'INTLIGHTS_SYSTEM',
}
```

## Command Tables

25 tables total. All use the standard `counter()` pattern with `start_command = 3000`. No `Keys` table (unlike Mi-24P and FA-18C).

| Table | Count | Notes |
|---|---|---|
| `BRU_commands` | 3 | BRU (shared PLT/CPG) |
| `CMWS_commands` | 24 | CMWS countermeasures |
| `DTU_commands` | 6 | Data transfer unit (**unmatched** — no device name match) |
| `JETT_commands` | 7 | Jettison panel (shared) |
| `KU_commands` | 52 | Keyboard unit (shared PLT/CPG/INPUT) |
| `baro_alt_commands` | 3 | Barometric altimeter |
| `comm_commands` | 84 | Comm panel (shared) |
| `cpt_mech_commands` | 25 | Cockpit mechanics |
| `ctrl_commands` | 14 | Flight controls (matched via `TABLE_ABBREV`: `ctrl` → `control`) |
| `device_commands` | 70 | Generic device commands (excluded from matching) |
| `electric_commands` | 43 | Electrical (**unmatched** — `ELEC_INTERFACE` doesn't normalize to `electric`) |
| `engine_commands` | 60 | Engine/rotor/APU |
| `eufd_commands` | 13 | EUFD (shared PLT/CPG/INPUT) |
| `extlights_commands` | 9 | External lights |
| `gear_commands` | 2 | Landing gear |
| `head_wrapper_commands` | 1 | Head tracker |
| `hmd_commands` | 10 | HMD |
| `hotas_commands` | 73 | HOTAS (shared PLT/CPG/INPUT) |
| `hydraulic_commands` | 9 | Hydraulic (**unmatched** — `HYDRO_INTERFACE` doesn't normalize to `hydraulic`) |
| `intercom_commands` | 18 | Intercom |
| `intlights_commands` | 31 | Internal lights (matched via `CPTLIGHTS_SYSTEM` → `INTLIGHTS_SYSTEM` override) |
| `mpd_commands` | 39 | MPD (shared across 6 MFD_* devices) |
| `preston_commands` | 9 | George AI copilot |
| `sai_commands` | 5 | Standby attitude indicator |
| `tedac_commands` | 98 | TEDAC (shared TEDAC/TEDAC_INPUT) |

### Device-table matching

The generator matches 39 of 91 devices to command tables. The 52 unmatched devices include:

1. **Avionics subsystem devices** with no clickable controls: GPS1/2, EGI1/2, MUX, ELC1/2, HIADC, FMC, WP1/2, DP_PLT/CPG, SP_PLT/CPG, CIU, IDM, DRVS_ASN157, RADALT.
2. **Sensor/weapon devices** with no command tables: TADS, PNVS, PNVS_TURRET_CONTROL, FCR, RFI, GUN_TURRET_CONTROL, PYLONS_INPUT, HELLFIRE_INTERFACE, AN_APR39, AN_AVR2A.
3. **System/utility devices**: MACROS, KNEEBOARD, NVG, ARCADE, FM_PROXY.
4. **Radio devices**: UHF_RADIO, VHF_AM_RADIO, FM1, FM2, HF_RADIO, ADF_ARN_149.
5. **Naming mismatches** (resolved via global unique lookup): ELEC_INTERFACE (`electric_commands`), HYDRO_INTERFACE (`hydraulic_commands`), DATA_TRANSFER_UNIT (`DTU_commands`), EMERGENCY_PANEL.

The `TABLE_ABBREV` map handles two cross-naming gaps:

```python
TABLE_ABBREV = {
    'ctrl': 'control',     # ctrl_commands → CONTROL_INTERFACE
    'hydro': 'hydraulic',  # hydraulic_commands → HYDRO_INTERFACE (note: this doesn't actually work — see unmatched)
}
```

Note: Despite `hydraulic` being in `TABLE_ABBREV`, the expansion goes from `hydro` → `hydraulic` while the device is `HYDRO_INTERFACE` (normalized to `hydrointerface`). The table `hydraulic_commands` normalizes to `hydraulic`, which doesn't match `hydrointerface`. These controls resolve via global unique command ID lookup instead.

### Shared table prefix strategy

Because MPD command names are very short (T1, T2, R1, L1, etc.), the generator uses the **full device name** as a prefix for disambiguation rather than a shortened diff. For example:
- `T1` on MFD_PLT_LEFT → `mpdPltLeftT1`
- `T1` on MFD_CPG_LEFT → `mpdCpgLeftT1`

This applies to all shared tables, producing prefixed names like `hotasPltTrigger`, `hotasCpgTrigger`, `commPltPltMasterZeroize`, etc.

## Elements

478 clickable elements. Standard extraction from `lua.globals().elements`.

### Crew member access

Like the Mi-24P, AH-64D elements include `crew_member_access` (0 = PLT, 1 = CPG).

### Suffix stripping

command_defs.lua uses `_EXT`, `_AXIS`, and `_ITER` suffixes for alternative input methods. The generator strips these and uses only the base command name.

### BOX_SIDE constants

The AH-64D clickable_defs.lua uses `BOX_SIDE_*` constants (6 values for VR interaction zones) in addition to standard `class_type`. These are mocked as:

```python
BOX_SIDE_X_top = 1, BOX_SIDE_X_bottom = 2
BOX_SIDE_Y_top = 3, BOX_SIDE_Y_bottom = 4
BOX_SIDE_Z_top = 5, BOX_SIDE_Z_bottom = 6
```

## Indicators

28 indicators total: no conditional, no bake indicators detected.

| Index | C++ Class | Device | Init File | Fields | Notes |
|---|---|---|---|---|---|
| 0 | `AH64::ccPNVS_CAM_AH64` | PNVS | `Cameras/PNVS/PNVS_CAM_init.lua` | 0 | PNVS camera |
| 1 | `AH64::ccTADS_CAM_AH64` | TADS | `Cameras/TADS/TADS_CAM_init.lua` | 0 | TADS camera |
| 2 | `AH64::ccRMAP_CAM_AH64` | FCR | `Cameras/RMAP/RMAP_CAM_init.lua` | 0 | Radar map camera |
| 3 | `AH64::ccMAP_CAM_AH64` | MFD_PLT_LEFT | `Cameras/MAP/MAP_CAM_init.lua` | 0 | Map camera (shared) |
| 4 | `AH64::ccMAP_CAM_AH64` | MFD_PLT_RIGHT | `Cameras/MAP/MAP_CAM_init.lua` | 0 | Map camera (shared) |
| 5 | `AH64::ccMAP_CAM_AH64` | MFD_CPG_LEFT | `Cameras/MAP/MAP_CAM_init.lua` | 0 | Map camera (shared) |
| 6 | `AH64::ccMAP_CAM_AH64` | MFD_CPG_RIGHT | `Cameras/MAP/MAP_CAM_init.lua` | 0 | Map camera (shared) |
| 7 | `AH64::ccMFD_AH64` | MFD_PLT_LEFT | `Displays/MFD/.../MFD_plt_left_init.lua` | 0 | Pilot left MPD |
| 8 | `AH64::ccMFD_LCD_AH64` | MFD_PLT_LEFT | `Displays/MFD/.../MPD_LCD_Plt_Left.lua` | 0 | Pilot left MPD LCD |
| 9 | `AH64::ccMFD_AH64` | MFD_PLT_RIGHT | `Displays/MFD/.../MFD_plt_right_init.lua` | 0 | Pilot right MPD |
| 10 | `AH64::ccMFD_LCD_AH64` | MFD_PLT_RIGHT | `Displays/MFD/.../MPD_LCD_Plt_Right.lua` | 0 | Pilot right MPD LCD |
| 11 | `AH64::ccMFD_AH64` | MFD_CPG_LEFT | `Displays/MFD/.../MFD_cpg_left_init.lua` | 0 | CPG left MPD |
| 12 | `AH64::ccMFD_LCD_AH64` | MFD_CPG_LEFT | `Displays/MFD/.../MPD_LCD_Cpg_Left.lua` | 0 | CPG left MPD LCD |
| 13 | `AH64::ccMFD_AH64` | MFD_CPG_RIGHT | `Displays/MFD/.../MFD_cpg_right_init.lua` | 0 | CPG right MPD |
| 14 | `AH64::ccMFD_LCD_AH64` | MFD_CPG_RIGHT | `Displays/MFD/.../MPD_LCD_Cpg_Right.lua` | 0 | CPG right MPD LCD |
| 15 | `AH64::ccKU_AH64` | KU_CPG | `Displays/KU/KU_init.lua` | 0 | CPG keyboard unit |
| 16 | `AH64::ccKU_AH64` | KU_PLT | `Displays/KU/KU_init.lua` | 0 | Pilot keyboard unit |
| 17 | `AH64::ccControlsIndicator_AH64` | CONTROL_INTERFACE | `ControlsIndicator/ControlsIndicator.lua` | 5 | Controls/autopilot indicator |
| 18 | `AH64::ccEUFD_AH64` | EUFD_PLT | `Displays/EUFD/EUFD_plt_init.lua` | 0 | Pilot EUFD |
| 19 | `AH64::ccEUFD_AH64` | EUFD_CPG | `Displays/EUFD/EUFD_cpg_init.lua` | 0 | CPG EUFD |
| 20 | `AH64::ccTEDAC_AH64` | TEDAC | `Displays/TEDAC/TEDAC_init.lua` | 0 | TEDAC display |
| 21 | `AH64::ccTEDAC_LCD_AH64` | TEDAC | `Displays/TEDAC/LCD/TEDAC_LCD_init.lua` | 0 | TEDAC LCD |
| 22 | `AH64::ccHMD_AH64` | HMD | `Displays/HMD/indicator/HMD_init.lua` | 0 | IHADSS HMD |
| 23 | `AH64::ccBRU_AH64` | BRU_PLT | `Displays/BRU/BRU_plt_init.lua` | 0 | Pilot BRU |
| 24 | `AH64::ccBRU_AH64` | BRU_CPG | `Displays/BRU/BRU_cpg_init.lua` | 0 | CPG BRU |
| 25 | `AH64::ccCMWS_AH64` | CMWS | `ASE/CMWS/CMWS_init.lua` | 0 | CMWS countermeasures |
| 26 | `AH64::ccPrestonAIIndicator_AH64` | PrestonAI | `AI/PrestonAI_indicator_noVR.lua` | 0 | George AI (non-VR) |
| 27 | `AH64::ccPrestonAIIndicator_AH64` | PrestonAI | `AI/PrestonAI_indicator_VR.lua` | 0 | George AI (VR) |

**No conditional indicators.** The AH-64D does not use `get_aircraft_property_or_nil()` in device_init.lua for indicator selection.

**No bake indicators.** Unlike the Mi-24P, the Apache's LCD displays use dedicated C++ classes (`ccMFD_LCD_AH64`, `ccTEDAC_LCD_AH64`) rather than generic bake indicators.

### Display indicator pairing

Most displays have two indicators: an MFD-class indicator for the display logic and an LCD-class indicator for the rendered output. For example, MFD_PLT_LEFT has both `ccMFD_AH64` (index 7) and `ccMFD_LCD_AH64` (index 8). The LCD indicators have no extractable text fields.

## Text Field Extraction

Only 5 text fields, all from the Controls Indicator (indication ID 17):

| Field Name | Purpose |
|---|---|
| `parking_brake_lbl` | Parking brake label |
| `txt_chan_name0` | Channel name 0 |
| `txt_chan_name1` | Channel name 1 |
| `txt_chan_name2` | Channel name 2 |
| `txt_chan_name3` | Channel name 3 |

The Apache's MPDs, EUFD, TEDAC, and KU displays render text via C++ code, not Lua text field objects. This is why only the controls indicator overlay has extractable fields.

### Page subsets pattern

The AH-64D indicator files use `page_subsets[X] = path` assignment syntax instead of inline tables. The text field extractor follows these path references to find text definitions in sub-pages.

## Gauges and Lamps

136 gauges and lamps extracted from mainpanel_init.lua.

### Controllers by type

| Controller | Count | Notes |
|---|---|---|
| WarningLights | 49 | Warning/caution panel lamps |
| (none) | 37 | Direct arg gauges (flight controls, engine, etc.) |
| CockpitLights | 9 | Interior lighting |
| BaroAltimeter | 6 | Altimeter components |
| sai | 6 | Standby attitude indicator |
| ShowCrewBody | 2 | Crew body visibility |
| Vibration1–5 | 5 | Vibration effects |
| Various crew controls | 16 | CollectivePLT/CPG, RudderPLT/CPG, StickPitch/RollPLT/CPG, ThrottlePLT/CPG, WheelBrakePLT/CPG |
| DoorPLT/CPG | 2 | Door positions |
| CanopyHandle | 1 | Canopy |
| FatGage | 1 | Free air temperature |
| ias | 1 | Indicated airspeed |
| mirrors_draw | 1 | Mirror rendering |

### Warning_Lights and Cabin_Lights enum tables

Like the Mi-24P, `lamps.lua` defines `Warning_Lights` and `Cabin_Lights` (called `CockpitLights` controller) enum tables. The extraction script builds reverse maps to name gauges that use these controllers.

### Gauge overlap with elements

4 gauges have arg numbers that overlap with clickable elements. These are skipped during control mapping generation to avoid duplicates.

## Equipment Properties

None. The AH-64D does not use `get_aircraft_property_or_nil()` in device_init.lua.

## Generator Output

- **Total controls:** 626 (492 commandable, 134 read-only)
- **Types:** 431 discrete, 61 continuous, 1 relative, 133 read-only
- **Position maps:** 24
- **nameMap entries:** 556 old→new renames

## AH-64D-Specific Extraction Notes

### Mocks needed beyond standard

Beyond the standard mocks (see `general.md`):
- **`BOX_SIDE_*` constants** — 6 VR interaction zone constants needed by clickable_defs.lua.
- **`sounds.lua`** — Must be executed before clickable_defs.lua to define `SOUND_*` constants.
- **`SnapViews` / `ViewSettings`** — Stub tables needed for mainpanel_init.lua execution.
- **`find_custom_livery()`** — No-op function returning empty string.
- **`LoRegisterPanelControls()`** — Returns an auto-vivifying metatable.
- **`kneeboard_implementation`** and **`disable_kneeboard_render_target`** — Simple global stubs.
- **`require("i_18n")`** — Intercepted to return `{ translate = function(s) return s end }`.
- **`writeParameter()`** — No-op.
- **`update_screenspace_displacement()`** — No-op.
- **`try_find_assigned_viewport()`** — Returns nil.
- **`Copy()`** — Identity function.
- **`create_material_type_table()`** — Returns auto-vivifying metatable.
- **`set_material_type()`** — No-op.
- **`clear_mode_table()`** — Clears nested table structure.
- **`get_page_by_mode_global()`** — Returns init page ID.

### No Keys table

Unlike the FA-18C and Mi-24P, the AH-64D does not have a `Keys` table in command_defs.lua. All commands use `*_commands` tables.

### Gauge name override

One gauge name needed manual override:

```python
GAUGE_NAME_OVERRIDES = {
    'APUPLT': 'apuPlt',  # Concatenated acronym that doesn't camelCase well
}
```

### No CONTROL_NAME_OVERRIDES needed

Unlike the Mi-24P, the AH-64D command names are sufficiently unique that no explicit control name overrides were needed.

### George AI (PrestonAI)

The AH-64D has an AI copilot ("George") represented by the `PrestonAI` device (ID 87) with `preston_commands` (9 commands) and two indicator overlays (VR and non-VR versions at indices 26–27).

### Many avionics subsystem devices

The AH-64D has a large number of devices (91) relative to command tables (25) because its avionics architecture models internal subsystems (MUX, EGI, ELC, HIADC, FMC, WP, DP, CIU, IDM, etc.) as separate devices. Most of these have no clickable controls and exist only for internal simulation logic.
