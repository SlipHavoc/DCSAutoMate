# DCS Native Control Extraction — AJS37 Viggen

Module-specific extraction notes for the AJS37 Viggen. Read `general.md` first for universal patterns.

## File Locations

- **Scripts directory:** `<DCS Install>/Mods/aircraft/AJS37/Cockpit/scripts/` (note: lowercase `scripts`)
- **clickabledata.lua:** `scripts/clickabledata.lua`
- **No separate clickable_defs.lua** — all factory helper functions are defined inline at the top of `clickabledata.lua`
- **devices.lua:** `scripts/devices.lua`
- **command_defs.lua:** `scripts/command_defs.lua`
- **device_init.lua:** `scripts/device_init.lua`
- **mainpanel_init.lua:** `scripts/mainpanel_init.lua`
- **sounds.lua:** `scripts/sounds.lua`
- **clickables.lua:** `scripts/clickables.lua` — auto-generated, dofile'd at end of clickabledata.lua

## Devices

41 devices total. Standard `counter()` pattern from 1.

**Important:** Comments in `devices.lua` show incorrect IDs (e.g. `--10`, `--14`, `--20`). The actual IDs are sequential counter values. Do not rely on comments; trust the counter.

Key devices:

| Device | Actual ID |
|--------|-----------|
| WEAPON_SYSTEM | 2 |
| ELECTRIC_SYSTEM | 3 |
| RADAR | 5 |
| REVERSAL | 7 |
| AIRBRAKE | 11 |
| NAVIGATION | 12 |
| ENGINE_MGMT | 13 |
| EP13 | 16 |
| LIGHTS | 17 |
| ENGINEPANEL | 18 |
| ELECTRICSYSTEM | 19 |
| RADARALT | 20 |
| DOPPLER | 21 |
| FLIGHTDATAUNIT | 22 |
| NAVIGATIONPANEL | 23 |
| RWR | 24 |
| ERRORPANEL | 26 |
| COUNTERMEASURE | 28 |
| FR22 | 30 |

## Command Tables

Only **2** command tables:

| Table | Count | Notes |
|-------|-------|-------|
| `device_commands` | 200 | `Button_1`..`Button_200`, base `start_command = 3000`. Gaps: `Button_71`–`Button_80`, `Button_81` starts again at 81 |
| `Keys` | 17 | Global keyboard commands (not device-specific) |

**Critical quirk:** Most elements in `clickabledata.lua` use **hardcoded numeric command IDs** (e.g. `3001`, `3406`, `3718`) directly rather than symbolic names from `device_commands`. Only a handful of elements use `device_commands.Button_N`. As a result, the `deriveDeviceTableMap` produces 0/41 device-to-table mappings — this is expected and not an error.

## Extracted Controls

- **178 elements** total
- **7 indicators** (some indicator page files fail to load due to missing `create_guid_string` DCS engine function — non-critical)
- **28 indication fields**
- **8 gauges/lamps**

### Helper distribution

| Helper | Count |
|--------|-------|
| `default_button` | 62 |
| `default_2_position_tumb` | 40 |
| `default_axis_limited` | 21 |
| `multiposition_switch_limited` | 9 |
| `default_animated_lever` | 9 |
| `default_3_position_tumb` | 8 |
| `default_2_position_tumb_altsound01` | 8 |
| `multiposition_switch_limited_metallic` | 6 |
| `default_2_way_spring_switch` | 5 |
| `default_2_position_tumb_flipcover` | 4 |
| `default_axis` | 4 |
| `default_1_position_tumb` | 1 |
| `NO_HELPER` | 1 |

The single `NO_HELPER` element is `AltsetL-PTR` — the altimeter knob, defined as a raw inline table (not a factory function call). It is handled via structural/STRUCTURAL_FALLBACK in the mapping phase.

## Notable Quirks

### Double elements = {} reset
`clickabledata.lua` calls `elements = {}` **twice**:
1. First, early in the file (inside a dead-code block with a no-op `for` loop)
2. Second, right before the actual element definitions begin

This causes the `installCmdAccessLogger` span-tracking proxy to wrap the *first* empty table; all actual elements are added to the *second* new table (which bypasses `__newindex` since `elements` already exists in `_G` raw storage). The standard extractor pattern calls `extractElements` *after* `uninstallCmdAccessLogger`, which would restore the first empty table — producing 0 elements.

**Fix applied in `extract_AJS37.py`:** Call `extractElements(lua)` BEFORE `uninstallCmdAccessLogger(lua)` so we read from the currently-live (populated) elements table.

### Factory functions inline in clickabledata.lua
Unlike most modules, there is no `clickable_defs.lua`. All factory functions (`default_button`, `default_2_position_tumb`, etc.) are defined at the top of `clickabledata.lua`. The `installHelperTagger` still tags them correctly since it wraps functions at call time.

### Auto-generated clickables.lua
A small (`clickables.lua`) file is auto-generated and `dofile`'d at the end of `clickabledata.lua`. It adds 3 elements with arg `-666` (the DCS sentinel for no physical argument). These are included in the extraction but are not actionable controls.

### Arg -666 sentinel
Many AJS37 elements have `arg = [-666]` — this is the module's convention for controls that have no associated cockpit animation arg (e.g., pure logic commands). These still produce valid controls in the mapping.

### Duplicate element key assignments
`clickabledata.lua` assigns some keys twice:
- `elements["PNT_464"]` (first: `default_button AFK 15 Deg Mode`, second: `default_button AFK Mode 3`)
- `elements["PNT_308"]` (first: `default_2_position_tumb IFF Power`, second: `multiposition_switch_limited IFF Code`)
- `elements["PNT_212"]` (first: `default_button Roll Centering`, second: `multiposition_switch_limited Anti Jamming Mode`)

In all cases the second assignment wins — this is standard Lua table behaviour and the extractor captures the final (second) value correctly.

### Missing DCS engine functions in indicator pages
Several indicator `indication_page.lua` files call `create_guid_string()` which has no mock. These files fail to load fully, producing warnings. The indicators themselves are still extracted at the `init.lua` level. No controls are lost; the `fields` lists for affected indicators may be incomplete.

### device 0 for mirrors
Three mirror-toggle elements use `device = 0` which is not in `devices.lua`. These are UI-only controls and are harmless in the extraction.
