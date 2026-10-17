# Module Conversion Pipeline — Reference

**Date:** 2026-04-16 (updated 2026-04-18)
**Context:** Fully native extraction pipeline — no DCS BIOS dependency. See git history (commit `ce119b5`) for the old BIOS-dependent pipeline if needed.

## Pipeline Steps (per module)

1. **Extract native controls** — `python tools/extract_<module>.py [--dcs-dir <path>]` → writes `config/nativeExtractions/<module>.json`
2. **Generate control mapping** — `python tools/generateControlMapping.py <nativeExtraction>` → writes `config/controlMappings/<module>.json` *(to be rewritten)*
3. **Run tests** — `python -m pytest --tb=short -q`

Per-module extraction scripts are self-contained. Guides: `tools/extraction-guides/general.md` and `tools/extraction-guides/<module>.md`. See `.agent/research/lupa-native-extraction.md` for technical details.

Steps 1–2 produce stable artifacts that only need re-running if the DCS module itself changes.  After a DCS update, `python tools/checkDcsUpdate.py` re-runs both for every module and reports the changes against HEAD (about 20 s); `config/dcsVersionChecked.json` records the DCS version the committed artifacts match.

## Key Directory Mappings

### scriptsDir (for extract_<module>.py)

Point at whichever directory contains `clickabledata.lua`:

| Layout | Path pattern | Modules |
|--------|-------------|---------|
| Cockpit/Scripts/ | `C:/Games/DCS World/Mods/aircraft/<dir>/Cockpit/Scripts` | A-10C, A-10C_2, AH-64D, AJS37, CH-47F, F-16C, F-5E, F-86, Ka-50, Ka-50_3, Mi-24P, Mi-8MTV2, Uh-1H |
| Cockpit/ | `C:/Games/DCS World/Mods/aircraft/<dir>/Cockpit` | AV8BNA, F-15E, F-4E, M-2000C, OH-58D |
| Cockpit/<variant>/ | `C:/Games/DCS World/Mods/aircraft/C-101/Cockpit/C-101CC` (or C-101EB) | C-101CC, C-101EB |

### DCS directory name mismatches (script name → DCS dir)

- F-86F → `F-86`
- UH-1H → `Uh-1H` (note lowercase 'h')
- Ka-50 Blackshark III → `Ka-50_3`
- C-101CC / C-101EB → `C-101` (shared, with variant subdirectories)
- A-4E → `A-4E-C`
- C-101CC / C-101EB → `C-101`
- F-16C → `F-16C_50`
- F-5E → `F-5E-3`
- F-86F → `F-86F Sabre`
- FA-18C → `FA-18C_hornet`
- Ka-50 Blackshark II / III → `Ka-50`
- M-2000C -- WIP → `M-2000C`
- Mi-8MTV2 → `Mi-8MT`
- OH-58D → `OH58D`

### BIOS files location

- Lua: `C:/Workspace/DCS related/DCS-BIOS from Saved Games/DCS-BIOS/lib/modules/aircraft_modules/<stem>.lua`
- JSON: `C:/Workspace/DCS related/DCS-BIOS from Saved Games/DCS-BIOS/doc/json/<stem>.json` (generated at runtime by installing DCS BIOS into DCS)

Note: The JSON files are NOT in the git repo — they are generated when DCS BIOS runs inside DCS.

### Module name mismatches (BIOS name → DCS-reported name)

Some modules use a different name in DCS BIOS than DCS reports via `LoGetSelfData().Name`. The generated control mapping JSON must use the DCS-reported name. Fix by renaming the output file and updating the `moduleName` field inside it.

| BIOS module name | DCS-reported name |
|---|---|
| AH-64D | AH-64D_BLK_II |
| Mi-8MT | Mi-8MTV2 (extraction) / Mi-8MT (mapping) |
| OH-58D | OH-58D (extraction) / OH58D (mapping) |

Note on Mi-8: the native extraction reads `Mods/aircraft/Mi-8MTV2/...` and writes `Mi-8MTV2.json`, but the canonical mapping is `config/controlMappings/Mi-8MT.json` with `moduleName: 'Mi-8MT'` because that is the name DCS reports for the Mi-8.  The OH-58D is the same: DCS reports `OH58D` (no dash), so its mapping is `OH58D.json`, and a mismatch shows up as Auto Select failing with "No script file found for DCS module".

## Migration Script Patterns

Keep per-module migration scripts (not generalized). Common steps in every migration script:

1. Remove `int16()` function definition (always the same 4-line block)
2. Handle module-specific value conversions (raw ints, string relatives, string-concat relatives)
3. Replace `int16()` → `1.0` and `int16(X)` → `X`
4. Bulk-replace SCREAMING_SNAKE names from nameMap (longest-first to avoid partial matches)
5. Verify no remaining int16 or SCREAMING_SNAKE names

Module-specific quirks encountered so far:
- **FA-18C**: RADALT_HEIGHT multi-line blocks, pressMfdButton/pressUfcButton dynamic construction, scriptCockpitState path refs, SAI_SET/SAI_CAGE string values, IFEI raw int
- **AV8BNA**: RWR_VOL raw int16 value, BINGO_SET relative string
- **Mi-24P**: Throttle string-concat relative (`'-'+str(int16())`), throttle string relative (`'+3000'`)
- **Mi-8MTV2**: Raw int16 literal `17427` (SGHT_KNOB → `0.2659`, similar to AV8BNA RWR_VOL pattern). No dynamic name construction. 159/159 used BIOS names mapped successfully; 0 unmappable in the script. All multi-position discrete positions preserved 1:1 from BIOS — no value remapping was needed (consistent with prior migrations).
- **Ka-50 Blackshark II**: Lua 5.5 rejects Lua 5.1-era `\%` escape sequences in `clickabledata.lua` and `Hint_localizer.lua` — extractor sanitises invalid backslash escapes via `dofile`/`loadfile` overrides. `LockOn_Options` deep-nested key access plus arithmetic comparisons (`LockOn_Options.time.hours <= 7`) needed a magic table with `__lt`/`__le`/`__add`/etc. metamethods. JSON I/O in `generateControlMapping.py` lacked `encoding='utf-8'` (latent bug exposed by Cyrillic hint strings). 8 SAI cage-knob `int16(-0.03)` calls cleaned up to `-0.03` (relative passthrough). 78 BIOS names → 191 replacements, 0 leftover unmapped names referenced by the script. Single-seat layout, 2 generic command tables (same legacy pattern as Mi-8). BSII and BSIII share the same BIOS module (`Module:new("Ka-50", 0x1800, { "Ka-50", "Ka-50_3" })`); BSIII would need its own extractor. The Ka-50 builder also gained positionMap-aware indexing (multi-pos discretes have null top-level dev/cmd), which should be backported to other module builders.

### Alternate naming approach: BIOS Lua → canonical name map

For modules where a script was originally written against DCS BIOS SCREAMING_SNAKE names, an alternative to a hand-curated `migrate_<module>.py` script is `tools/buildBiosNameMap_<module>.py` (Mi-8 example: `tools/buildBiosNameMap_Mi8MT.py`).

The script:
1. Regex-parses the BIOS `<module>.lua` source for `<Module>:defineXXX(BIOS_NAME, dev, cmd, arg, ...)` rows.
2. Joins each row against `config/controlMappings/<module>.json` on the `(deviceId, commandId, arg)` triple (with a fallback to `(dev, cmd)` pair-match).
3. Emits `tools/biosNameMap_<module>.json` (BIOS_NAME → canonical) plus an `unmapped.json` and `audit.md`.

Then `tools/applyNameMap.py` performs the longest-first word-boundary regex rename on the script, after which standard cleanup (remove `int16()` helper, raw-literal conversion) runs as usual. This is well-suited to modules where every BIOS define maps cleanly to a single canonical entry.

Modules with known dynamic name construction still to handle:
- **F-15E**: `'F_UFC_' + cmd`
- **F-16C**: `'ICP_BTN_' + btn`

Modules with scriptCockpitState path refs still to handle:
- A-10C, A-10C_2, AH-64D, CH-47F, F-16C, F-4E, F-86F, M-2000C

## Completed BIOS → canonical script migrations

- FA-18C
- AH-64D
- AV8BNA
- Mi-24P
- Mi-8MTV2
- Ka-50 Blackshark II
