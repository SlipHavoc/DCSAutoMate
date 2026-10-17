# DCS Native Control Extraction — UH-1H Huey

Module-specific extraction notes for the UH-1H Huey. Read `general.md` first for universal patterns.

## File Locations

- **Scripts directory:** `<DCS Install>/Mods/aircraft/Uh-1H/Cockpit/Scripts/`
  - Note: install directory is `Uh-1H` (mixed case), not `UH-1H`. DCS-reported module name is `UH-1H`.
- **clickabledata.lua:** `Scripts/clickabledata.lua` (930 lines, no separate clickable_defs.lua — all helper functions defined inline at the top)
- **devices.lua:** `Scripts/devices.lua`
- **command_defs.lua:** `Scripts/command_defs.lua`
- **device_init.lua:** `Scripts/device_init.lua`
- **mainpanel_init.lua:** `Scripts/mainpanel_init.lua`
- **sounds.lua:** `Scripts/sounds.lua`
- **VR_config.lua:** `Scripts/VR_config.lua`
- **config.lua:** `Scripts/config.lua` (only 2 lines: `shape` and `new_infrared_debug`)
- **main_panel_commands.lua:** `Scripts/main_panel_commands.lua` (key command bindings, loaded by device_init.lua)

No separate `clickable_defs.lua` — all factory functions (`default_button`, `default_2_position_tumb`, `multiposition_switch`, etc.) are defined directly at the top of `clickabledata.lua`.

## Devices

57 devices total. Standard `counter()` pattern in `devices.lua`. Device 53 is skipped (a comment says `-- 53 to preserve tracks (rip "synch")`), so IDs jump from 52 to 54.

Key devices with clickable controls:

| Device Name | ID | Notes |
|---|---|---|
| ELEC_INTERFACE | 1 | Electrical system, battery, generators, circuit breakers |
| FUELSYS_INTERFACE | 2 | Fuel system |
| ENGINE_INTERFACE | 3 | Engine, starter, governor, de-ice |
| HYDRO_SYS_INTERFACE | 4 | Hydraulic system |
| ADI_PILOT | 5 | Pilot ADI |
| ADI_OPERATOR | 6 | Copilot ADI |
| NAVLIGHT_SYSTEM | 7 | Navigation lights |
| WEAPON_SYS | 9 | Weapons system (armament selector, gun selector, rockets) |
| GMCS | 10 | GMCS gyro magnetic compass |
| CPT_MECH | 12 | Cockpit mechanics (doors, fans) |
| RADAR_ALTIMETER | 13 | Radar altimeter |
| SYS_CONTROLLER | 15 | System controller |
| IFF | 17 | IFF transponder |
| AAU7 | 18 | Right barometric altimeter |
| AAU32 | 19 | Left barometric altimeter |
| VHF_ARC_134 | 20 | ARC-134 VHF AM radio (COM2) |
| INTERCOM | 21 | Intercom system |
| UHF_ARC_51 | 22 | ARC-51BX UHF radio (COM1) |
| VHF_ARC_131 | 23 | ARC-131 VHF FM radio (COM3) |
| ARN_82 | 25 | ARN-82 VHF navigation radio |
| MARKER_BEACON | 26 | Marker beacon |
| ADF_ARN_83 | 27 | ADF ARN-83 |
| COURSE_IND | 29 | Course indicator |
| CLOCK | 30 | Clock |
| FLEX_SIGHT | 32 | Copilot flexible sighting station (minigun aiming) |
| CONTROL_SYSTEM | 41 | Flight control system |
| HEATING_SYSTEM | 47 | Heating/ventilation |
| PILOT_SIGHT | 49 | Pilot sighting station |
| XM_130 | 50 | XM-130 countermeasures (flare dispenser) |
| EXT_CARGO_EQUIPMENT | 52 | External cargo equipment |

Non-clickable devices (no elements): SOUND_SYSTEM (8), VARIOMETER_PILOT (11), MISC_SYSTEMS_INTERFACE (14), HELMET_DEVICE (16), ILS (24), REMOTE_COMPASS (28), FM_PROXY (31), TURN_IND (33), NAVIGATION_RELAY (34), MD_1_GYRO (35), ROOF_AIRSPEED (36), NOSE_AIRSPEED (37), COPILOT_RMI (38), STANDBY_COMPASS (39), VARIOMETER_COPILOT (40), MACROS (42), ARCADE (43), PADLOCK (44), KNEEBOARD (45), HEAD_WRAPPER (46), CARGO_CAM (48), EXTERNAL_CARGO_VIEW (51), EXTERNAL_CARGO_SPEECH (54), CREWE (55), OXYGEN_INTERFACE (56), HEARING_SENS (57), NET_SYNC (58).

## Command Tables

Only **2 command tables** — this is the key structural feature of the UH-1H:

| Table Name | Count | ID Range | Notes |
|---|---|---|---|
| `Keys` | 26 | 84–1033 | Global key commands (lights, trim, etc.) |
| `device_commands` | 70 | 3001–3070 | Shared button table: `Button_1`..`Button_70` |

`device_commands` is a single shared table used by **all** clickable devices. It is generated with a loop in `command_defs.lua`:

```lua
start_command   = 3000
device_commands = {}
for cmd_num = 1,70 do
    device_commands["Button_"..cmd_num] = start_command + cmd_num
end
```

Circuit breakers begin at `cb_start_cmd = device_commands.Button_21` (ID 3021) and run to `cb_end_cmd = cb_start_cmd + 63` (ID 3084). Note that 3084 exceeds the `device_commands` table's range of 3070 — the circuit breaker clickabledata references raw integer IDs beyond Button_70 using direct arithmetic on `cb_start_cmd`.

## Canonical Naming

Because all devices share the single `device_commands` table, the canonical key generator's **element-key substitution** fires for every named control: when `tableName == 'device_commands'` and an element key is available, the element key is used as the command name instead of `Button_N`. This produces meaningful names like:

- `ELEC_INTERFACE.BAT-SWITCHER-PTR`
- `ENGINE_INTERFACE.THROTTLE-PTR`
- `WEAPON_SYS.LRGUN-SWITCH-PTR`
- `XM_130.FLARE-PTR`

Raw stubs for unused `Button_N` slots still appear as `<deviceName>.Button_N`.

## Indicators and Gauges

10 indicators extracted, 69 indication fields total, 164 gauges/lamps.

**Indicator init failures (harmless):** Three indicator devices produce load-time errors because their init files call C++ functions we can't mock:

- `PilotSight/Indicator/PilotSight_init.lua` — `indicator_type = COLLIMATOR`. Fails at line 51 attempting to index a mode constant. This is the pilot's XM-26 gunsight crosshair display — a geometric collimator with no text fields.
- `FlexibleSight/Indicator/FlexibleSight_init.lua` — `indicator_type = COLLIMATOR`. Same failure. This is the copilot's flexible sighting station — also a crosshair with no text fields.
- `CARGO_CAM/CARGO_CAM_init.lua` — Calls `make_viewport()` (C++ host function). External cargo camera view — no useful text fields for scripting.
- `CrewIndicator/crew_indicator_page.lua` — Calls `populate()` (C++ host function). Crew life-bar display.

None of these contain text fields useful for `scriptCockpitState` queries, so their failures have zero impact on the extraction.

**Missing files (harmless):**

- `Fonts/symbols_locale.lua` — not present on disk; DCS loads it via a VFS path not available in our sandbox.
- `KNEEBOARD/declare_kneeboard_device.lua` — not present; kneeboard is a standard shared device, not module-specific.

## Extraction Quirks

1. **No `clickable_defs.lua`** — All factory helper functions are defined inline at the top of `clickabledata.lua`. The extractor needs to load only `clickabledata.lua` (which itself `dofile`s `command_defs.lua`, `devices.lua`, and `sounds.lua` at the top).

2. **Single shared command table** — The `device_commands` table is shared by all 30 clickable devices. The `installCmdAccessLogger` mechanism correctly attributes each element to the single `device_commands` table via its `__index` access log. All 30 devices deterministically map to `device_commands`.

3. **`LockOn_Options` magic table** — `mainpanel_init.lua` loads `VR_config.lua` which does nested field accesses on `LockOn_Options`. Using a magic auto-vivifying table (rather than the simple record used in Mi-24P) prevents nil-index errors.

4. **`sounds.lua` preload** — `clickabledata.lua` dofile's `sounds.lua` which defines `SOUND_*` constants used in some element definitions (e.g. `INVTR-SWITCHER-PTR.sound`). The extractor loads `sounds.lua` before starting the cmd-access logger so these constants are available.

5. **Unmatched devices are non-clickable** — 27 of 57 devices have no clickable elements (instruments, proxy objects, game systems). Their absence from the deviceTableMap is expected and harmless.
