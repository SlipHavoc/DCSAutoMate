# DCS Native Control Extraction — Mi-8MTV2 Hip

Module-specific extraction notes for the Mi-8MTV2 Hip.  Read `general.md` first for universal patterns.

## File Locations

- **Scripts directory:** `<DCS Install>/Mods/aircraft/Mi-8MTV2/Cockpit/Scripts/`
- **clickabledata.lua:** `Scripts/clickabledata.lua`
- **clickable_defs.lua:** `Scripts/clickable_defs.lua`
- **devices.lua:** `Scripts/devices.lua`
- **command_defs.lua:** `Scripts/command_defs.lua`
- **device_init.lua:** `Scripts/device_init.lua`
- **sounds.lua:** `Scripts/sounds.lua`
- **mainpanel_init.lua:** `Scripts/mainpanel_init.lua`
- **lamps.lua:** `Scripts/Devices_specs/MainPanel/lamps.lua` (loaded by mainpanel_init.lua)

Uses the standard `Cockpit/Scripts/` path, same as Mi-24P / FA-18C / F-16C.

## Module name mismatch

The extraction reads from `Mods/aircraft/Mi-8MTV2/...` and writes `module: 'Mi-8MTV2'` into `config/nativeExtractions/Mi-8MTV2.json`, but the canonical control mapping is named `Mi-8MT.json` and uses `moduleName: 'Mi-8MT'` because that is the name DCS reports via `LoGetSelfData().Name` for the Mi-8.  Same situation as AH-64D vs `AH-64D_BLK_II`: the file is renamed and the `moduleName` field rewritten after generation.  See the mismatch table in `module-conversion-pipeline.md`.

## Devices

60 devices total.  Standard `counter()` pattern in `devices.lua`.

Notable groupings (single-seat helicopter, no pilot/operator split):

| Device Name | ID | Notes |
|---|---|---|
| ELEC_INTERFACE | 1 | Electrical system, AZS circuit-breaker bank |
| FUELSYS_INTERFACE | 2 | Fuel system |
| ANTI_ICE_INTERFACE | 3 | Anti-icing |
| ENGINE_INTERFACE | 4 | Engine/rotor/APU |
| HYDRO_SYS_INTERFACE | 5 | Hydraulic system |
| ANY_DEVICE | 5 | (alias) |
| AUTOPILOT | 8 | Autopilot panel |
| FIRE_PROTECTION_SYS | 9 | Fire detection / extinguisher |
| LIGHT_SYSTEM | 10 | Interior lights (left/right console panels) |
| WEAPON_SYS | 12 | Weapons panel |
| NAVLIGHT_SYSTEM | 14 | Exterior navigation lights |
| DISS_15 | 15 | DISS-15 Doppler navigator |
| GMK1A | 16 | GMK-1A gyrocompass |
| AGB_3K_LEFT / RIGHT | — | ADI cage/zero-pitch knobs |
| RV5_RADAR_ALT | — | RV-5 radar altimeter |
| SAS | — | SAS / autopilot trim |
| SPU_7 | 36 | SPU-7 intercom |
| JADRO_1A | 37 | YaDRO-1A HF radio |
| R_863 | 38 | R-863 VHF/UHF |
| R_828 | 39 | R-828 secure radio |
| ARC_9 | 40 | ARC-9 ADF |
| ARC_UD | 41 | ARC-UD search/rescue ADF |
| UV_26 | — | UV-26 countermeasures dispenser |
| PKV | — | PKV operator sight (rotary) |
| CPT_MECH | — | Cockpit mechanics (wipers, doors, fans) |
| CLOCK_AChS_1 | 45 | AChS-1 clock |
| HELMET_DEVICE | 49 | Helmet/HUD |

There is **no pilot/operator split** in the Mi-8 — all controls live on a single device set.  Contrast Mi-24P, where 6 device pairs (`*_P` / `*_O`) duplicate panels for the two seats.

## Command Tables

**Only 2 command tables**, in stark contrast to Mi-24P's 50:

| Table | Count | Notes |
|---|---|---|
| `device_commands` | 130 | Generic `Button_1..Button_130` (loop-generated) |
| `Keys` | 497 | Global key commands with fixed integer IDs |

Every clickable element in `clickabledata.lua` references `device_commands.Button_N` regardless of which device the element belongs to.  The owning device's command handler dispatches based on the button number.  This is the legacy ED pattern; the Mi-24P (and most newer modules) replaced it with a per-system `*_commands` table.

### Implications for control naming

Because there is only one command table and it contains generic `Button_N` names, the generator cannot derive meaningful control names from `cmdNameToCamelCase` the way it does for Mi-24P.  Instead, the Mi-8 mapping uses **device-prefixed names derived from the cockpit element's role**, e.g.:

- `BATT.BATT1_Switch` (Battery 1 toggle, device 1 = ELEC_INTERFACE — but BATT here is the cockpit element / sub-panel name, not the device name)
- `ENGINE_INTERFACE.PTR_CPE_TMB_ENGSTART_LFTRGT` (3-pos engine selector)
- `JADRO_1A.PTR_ADDSECPLT_LVR_DIG12` (a wheel display arg)

Names follow the pattern `<DEVICE_OR_PANEL>.<ELEMENT_NAME>` where `<ELEMENT_NAME>` is taken from the `clickabledata.lua` element identifier (often a `PTR_*` Cyrillic transliteration prefix).  The names are long and not pretty, but they are stable and unambiguous.

### Device-table matching

`deviceTableMap` resolves all 42 commandable devices to `device_commands`.  No `TABLE_ABBREV` overrides are needed because there is only one table to match against.

## Elements

420 clickable elements.  Standard extraction from `lua.globals().elements`.

### `radio_wheel_1` and `radio_wheel_double` helpers

Used heavily by Mi-8 radio panels (R-863, R-828, JADRO-1A, ARC-9, ARC-UD).  These helper functions in `clickable_defs.lua` define multi-arg controls with master/slave display-arg coupling: writes go to a *command-pulse* arg, but cockpit-visible state lives on one or more separate *display* args (e.g. JADRO-1A 1MHz selector: master = ones digit, slave = tens digit).  The extraction script captures these via `extractSlaveAnimation()`.

See `.agent/research/radio-wheel-display-args.md` and `.agent/decisions/wheel-controls-and-displayArgs.md` for the schema and rationale.  Mi-8 and Mi-24P are the only two modules currently using this helper pattern.

### No crew_member_access

Single-seat module — elements have no `crew_member_access` field, unlike Mi-24P.

## Indicators

8 indicators total.  All use generic display init files and have no extracted text fields (the Mi-8 cockpit uses analog instruments and CRT/LCD displays whose state is read via gauge args rather than indicator-side text fields).

The GunCamera indicator entry has a `viewport`/`options` table shape that the extraction script handles specifically — see the relevant `extract_Mi8MTV2.py` comment.

## Gauges and Lamps

317 gauges and lamps extracted from mainpanel_init.lua.  Smaller than Mi-24P (460) but still substantial due to the Mi-8's analog instrument suite and warning panels.

`lamps.lua` defines `Warning_Lights` and `Cabin_Lights` enum tables that the extraction script reverse-maps to name gauges, same pattern as Mi-24P and AH-64D.

## Equipment Properties

None.  The Mi-8MTV2 does not use `get_aircraft_property_or_nil()` in `device_init.lua`.

## Generator Output

- **Total canonical controls:** 813 (428 commandable, 385 read-only `arg.N`)
- **By type:** 370 discrete, 25 relative, 33 continuous, 385 read-only
- **positionMaps:** 5
- **Inferred entries:** 0 (all controls have a clickable cockpit element backing them)

## Mi-8MTV2-Specific Extraction Notes

### Single shared `device_commands` table

By far the biggest difference from other modules.  Because every command goes through one 130-entry `Button_N` table, the extraction tooling cannot use command-table membership to identify which device owns a command — it must infer ownership from the clickable element that *uses* the command.  The general extraction utilities already handle this correctly (the `deviceTableMap` simply has all devices pointing to `device_commands`), but it is worth knowing if you debug name-generation issues.

### Additional lupa mocks needed

Same set as Mi-24P (see `Mi-24P.md` "Additional lupa mocks needed" — `sounds.lua` pre-execution, `SnapViews`/`ViewSettings` stubs, `find_custom_livery()`, `LoRegisterPanelControls()`, `kneeboard_implementation`, `require("i_18n")`, `clear_mode_table()`, `get_page_by_mode_global()`, `create_material_type_table()`, `set_material_type()`).

### DCS BIOS migration of `Mi-8MTV2.py`

The cold start / hot start / shutdown script in `DCSAutoMateScripts/Mi-8MTV2.py` was originally written against DCS BIOS SCREAMING_SNAKE control names.  Migration to the canonical mapping was done in two stages:

1. **`tools/buildBiosNameMap_Mi8MT.py`** — parses the DCS BIOS `Mi-8MT.lua` source, joins each `Mi_8MT:defineXXX(BIOS_NAME, dev, cmd, arg, ...)` against `config/controlMappings/Mi-8MT.json` on the `(deviceId, commandId, arg)` triple, and emits:
   - `tools/biosNameMap_Mi-8MT.json` — confident BIOS_NAME → canonical map (410 entries, 95.6 % coverage of the 429 BIOS defines)
   - `tools/biosNameMap_Mi-8MT.unmapped.json` — 19 BIOS entries with no canonical match (none of these were used by the script)
   - `tools/biosNameMap_Mi-8MT.audit.md` — multi-position discrete controls with their BIOS position labels and canonical positionMap, for human verification
2. **`tools/applyNameMap.py`** — applies the name map with longest-first word-boundary regex replacement, then standard cleanup per `.agent/research/script-migration-patterns.md` (remove `int16()` helper, rewrite `int16(X)` → `X`, replace raw int16 literals like `17427` → `0.2659`).

After live-testing in DCS, **all multi-position discrete switches behaved identically under the new positionMap** — i.e. the BIOS position index and the canonical position index resolved to the same cockpit-visible state.  The `# TODO: verify position N (BIOS=<label>) under canonical positionMap of <name>` comments inserted during migration were resolved without value changes.  This matches the experience reported on every prior module migration (FA-18C, AH-64D, AV8BNA, Mi-24P), suggesting that as long as the extraction tooling enumerates positions in cockpit-natural order, it converges on the same order DCS BIOS used.

### Module-specific quirks worth noting

- **Raw int16 literal**: The script used `pushSeqCmd(dt, 'SGHT_KNOB', 17427)` to set the PKV gunsight rotary to ~26.6 % of full-scale.  Translated to `0.2659` (17427 / 65535) per the universal int16 conversion rule.
- **No string-format relatives**: Unlike Mi-24P (`'+3000'`, `'-'+str(int16())`) or AV8BNA (`'+3200'`).
- **Two BIOS spelling typos** (`FUEL_RIGTH_SHUTOFF`, `FUEL_RIGTH_PUMP`) carry through to the canonical mapping intact — they are matched on `(dev, cmd, arg)`, not on name spelling, so the typos are harmless.
- **Wheel display args** for radio frequency selectors require the new `displayArgs` schema (master/slave) to read back cockpit-visible digit values.  See radio_wheel research notes.

### No DCS-BIOS-name-construction patterns

Unlike F-15E (`'F_UFC_' + cmd`) or F-16C (`'ICP_BTN_' + btn`), `Mi-8MTV2.py` has no dynamic name construction.  Every control reference is a literal string, so the bulk-rename was straightforward.

### Harmless warnings during extraction

Same set as Mi-24P: missing font files, missing common scripts (`devices_defs.lua`, `tools.lua`), missing kneeboard device file.  All are pre-mocked or fail silently and have no impact on output.
