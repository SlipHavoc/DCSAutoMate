# OH-58D Kiowa Warrior — Extraction Guide

## File Locations

- **Module install dir**: `c:/Games/DCS World/Mods/aircraft/OH-58D/`
- **Scripts dir**: `c:/Games/DCS World/Mods/aircraft/OH-58D/Cockpit/` (no `Scripts/` subdirectory)
- **Key files** (all directly in `Cockpit/`):
  - `devices.lua` — device name → ID mapping (53 devices, counter-based)
  - `command_defs.lua` — single flat `device_commands` table, Button_1–Button_190
  - `clickable_defs.lua` — all helper function definitions
  - `clickabledata.lua` — all clickable element definitions (443 lines)
  - `arg_int.lua` — symbolic arg name → integer mapping (~445 lines)
  - `sounds.lua` — SOUND_* constant definitions (counter from -1, starts at 0)
  - `device_init.lua` — `creators[]` and `indicators[]` tables

## Script Path Quirk

**Unlike most DCS modules**, OH-58D has no `Cockpit/Scripts/` subdirectory.
All Lua files live directly in `Cockpit/`. The extractor must set:
```
LockOn_Options.script_path = "c:/Games/DCS World/Mods/aircraft/OH-58D/Cockpit/"
```

## Device Count

51 unique devices extracted (53 defined in devices.lua; two entries not referenced by any clickable element). Key device IDs:

| ID | Name             | Description                  |
|----|------------------|------------------------------|
|  1 | CONTROLS         | Flight controls              |
|  2 | FUEL             | Fuel system                  |
|  3 | SENSORS          | Sensors                      |
|  5 | ENGINE           | Engine                       |
|  7 | ELECTRIC         | Electrical system            |
|  8 | COCKPIT          | Cockpit systems              |
| 10 | MPD              | Multifunction Pilot Display  |
| 11 | RMFD             | Right MFD (pilot)            |
| 12 | SCAS             | Stability/Control Augmentation |
| 14 | MFK              | Multifunction Keyboard       |
| 17 | FADEC            | Full Authority Digital Engine Control |
| 21 | WEAPONS          | Weapons system               |
| 22 | MMS              | Mast-Mounted Sight           |
| 23 | LMFD             | Left MFD (copilot)           |
| 27 | RFD              | Radio/Frequency Display      |
| 36 | CI               | Communications/Interoperability |
| 37 | CMWS             | Common Missile Warning System |
| 42 | SYNC_CONTROLS    | Synchronized controls        |

## Command Table

Single flat table: `device_commands = { Button_N = start_command + N }` where `start_command = 3000`.

- **Button_1** = 3001, **Button_190** = 3190
- All devices share this one command table.

## Arg Numbers

All arg numbers are defined in `arg_int.lua` as `arg_int = { SymbolicName = N, ... }`.
Clickabledata.lua references them as `arg_int.SymbolicName`.
The `arg_int.lua` file must be dofile'd before any element definitions execute.

## Helper Functions

15 distinct helpers, all defined in `clickable_defs.lua`:

| Helper | Class | Description |
|--------|-------|-------------|
| `default_button` | BTN | Momentary push button, argLim={0,1} |
| `default_button_vr_all_sides` | BTN | Same as default_button, all VR sides |
| `default_2_position_tumb` | TUMB+TUMB | 2-position toggle, argLim={0,1} |
| `circuit_breaker` | TUMB+TUMB | Circuit breaker, same structure as default_2_position_tumb |
| `default_3_position_tumb` | TUMB+TUMB | 3-position switch, same command both sub-controls, argLim={-1,1} |
| `default_3_position_button` | BTN+BTN | 3-position button, same command both sub-controls, argLim={-1,1} |
| `default_axis` | LEV | Continuous axis, argLim={0,1} |
| `default_axis_limited` | LEV | Continuous axis with custom upper limit |
| `default_movable_axis` | MOVABLE_LEV | Movable lever axis |
| `multiposition_switch_limited` | TUMB+TUMB | N-position selector, step=1/N |
| `springloaded_3_pos_tumb` | BTN+BTN | Spring-loaded 3-pos, TWO different commands, argLim={{-1,0},{0,1}} |
| `default_button_tumb` | BTN+TUMB | Spring-loaded 3-pos, TWO different commands, 3 style variants |
| `default_button_axis` | BTN+LEV | Combined push button + axis, DIFFERENT args |
| `default_tumbler_axis` | TUMB+LEV | Combined toggle + axis, DIFFERENT args |
| `two_axis_lever` | LEV+LEV | Dual-axis lever (grease pencil), DIFFERENT args |

## Notable Quirks

### 1. Two-command 3-position elements

`default_button_tumb` (BTN+TUMB, 35 uses) and `springloaded_3_pos_tumb` (BTN+BTN, 1 use) both
use **two different commandIds** — one for each direction. These require `twoCommandSpringloaded`
archetype in the mapper, which produces a `positionMap` array with null at center.

`default_button_tumb` has three `style` variants affecting `stop_action` (spring-loaded vs steady),
but all produce the same two-command complementary-argLim shape the archetype expects.

### 2. `default_3_position_tumb` and `default_3_position_button` — same command

Both use **one commandId** for both sub-controls (argLim={-1,1} for both). This is NOT a
`twoCommandSpringloaded` pattern. `simpleDiscrete` produces the correct 3-position control
(argLim=[-1,1], step=1.0, positions=3).

### 3. Circuit breakers

74 uses. Structurally identical to `default_2_position_tumb` (same argLim, same class).
Different only in sound constant used. Maps to `simpleDiscrete`.

### 4. MFD indicator pages fail silently

`device_init.lua` dofiles many indicator init files under `MFDs/Indicator/`, `ODA/Indicator/`,
etc. These files reference layout constants defined in `definitions.lua` which fails due to
arithmetic on the magic-table mock. All these indicator page failures are logged as warnings
and can be ignored — they don't affect control extraction.

The `extractIndicatorsFromLuaGlobals` call still extracts 19 indicators from the top-level
`indicators` table successfully (display names, device IDs, file paths).

### 5. No DCS translations catalog

`clickabledata.lua` wraps hint strings in `_()` (via `require("i_18n")`), but the OH-58D module
does not ship a `.mo` catalog. The `_()` function is mocked to return the string unchanged,
so all hint strings are the raw English keys.

## Extraction Results

| Metric | Count |
|--------|-------|
| Devices extracted | 51 |
| Command tables | 1 (`device_commands`, 190 entries) |
| Elements extracted | 333 |
| Indicators | 19 |

## Control Mapping Results

| Metric | Count |
|--------|-------|
| Discrete controls | 309 |
| Continuous axes | 24 |
| Relative controls | 12 |
| positionMap controls | 36 |
| Raw (unbound) | 3428 |
| Total | 7508 |

Devices matched (have clickable elements): 20 of 51.
The 3428 raw controls come from `device_commands` entries for the 31 unmatched
(software-only) devices that have no clickable cockpit elements.
