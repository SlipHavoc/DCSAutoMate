# Eliminate DCS BIOS Dependency

Replace all DCS BIOS dependency with native DCS communication.  The core
infrastructure (TCP protocol, export Lua, DCSDirectManager, value translation,
unified control mapping format, canonical/alias naming, native extraction
pipeline) is **complete** and four modules are fully migrated and live-validated.
Remaining work: convert the other ~15 modules, migrate DCSMonitor, final doc/cleanup pass.

Detailed history of the completed work (Phases 1–6) is in `archive/replace-dcs-bios.md`.

---

## Completed Milestones

- **TCP protocol** — `DCSAutoMateExport.lua` handles C:/S:/Q:/W:/X:/T:/E:/I: commands.
- **DCSDirectManager** — TCP replacement for DCSBIOSExportManager (archived).
- **Value translation** — discrete (position index → native float), continuous (clamp to argLim), relative (passthrough).
- **Unified control mapping format** — flat `controls` dict, 3 types (discrete/continuous/relative), canonical `<deviceName>.<cmdName>` keys, field presence determines capabilities.
- **Canonical naming** — control mappings keyed by verbatim Lua names (`<deviceName>.<cmdName>`).  Alias layer fully removed; scripts use canonical names directly.
- **Shared generator** — `tools/generateControlMapping.py` is module-agnostic and produces all four modules' mappings.  All four per-module generators deleted.
- **Deterministic device→command-table mapping** — captured at extraction time via a Lupa `__index` metatable on every `*_commands` global.  Replaced brittle `inferDeviceTableMapByEvidence` heuristic.
- **Shared extractor helper** — `tools/extractUtils.py` centralizes the Lua mock environment, `dofile` re-sweep, and `deviceTableMap` capture used by all per-module extractors.
- **FA-18C vertical slice** — script migrated, controls renamed to canonical names, cold/hot/air/shutdown verified in-game.
- **AV8BNA + Mi-24P** — scripts migrated and verified (cold/hot/shutdown).
- **AH-64D** — extraction script, control mapping (626 controls), script renamed, SAI cage knob fixed (S:13:3004 ITER, -0.75 per step), cold start verified.
- **BIOS artifacts archived** — generateBiosMapping.py, biosMappings/, nativeControls/, migrate*Script.py, DCSBIOSExportManager → `archive/`.
- **sendProtocol override** — `DCSDirectManager.sendControl()` supports per-control `sendProtocol` field (needed for ITER commands like SAI cage knob).
- **monitorArgs.py tool** — Standalone TCP polling tool for live arg value monitoring during development.
- **Research notes** — Section 11 in dcs-native-control-types.md: EXT/ITER/AXIS command variants, protocol×command test matrix, SAI cage knob case study.
- **validateControlMapping.py** — Standalone TCP validation tool that smoke-tests every control in a module's mapping against live DCS.  Tests discrete (position cycling), continuous (0%/25%/50%/75%/100%), relative (increment), and read-only (arg query / indication field).  Two-tier retry at 4× and 16× delay handles DCS animation timing.  Guard/cover auto-opening and closing.
- **remapAliasKeys.py** — Rewrites alias-file keys by `(deviceId, commandId)` fingerprint.  Standard tool for canonical renames.
- **All 4 modules live-validated** — AH-64D 614/626, FA-18C 472/491+4skip, AV8BNA ~256/277, Mi-24P 1002/30+162skip.  All failures documented in `tools/validation-notes/`.

---

## Phase A: Native Extraction Pipeline — DONE

Replaces the BIOS-dependent extraction with per-module scripts that read DCS Lua
files directly via lupa, sharing `tools/extractUtils.py`.

| Step | Status | Description |
|------|--------|-------------|
| A1. General extraction guide | ✅ Done | `tools/extraction-guides/general.md` |
| A2. FA-18C extraction guide | ✅ Done | `tools/extraction-guides/FA-18C.md` |
| A2b. AV8BNA extraction guide | ✅ Done | `tools/extraction-guides/AV8BNA.md` |
| A2c. AH-64D extraction guide | ✅ Done | `tools/extraction-guides/AH-64D.md` |
| A2d. Mi-24P extraction guide | ✅ Done | `tools/extraction-guides/Mi-24P.md` |
| A3. FA-18C extraction script | ✅ Done | `tools/extract_FA18C.py` → `config/nativeExtractions/FA-18C.json` |
| A3b. AV8BNA extraction script | ✅ Done | `tools/extract_AV8BNA.py` → `config/nativeExtractions/AV8BNA.json` |
| A3c. AH-64D extraction script | ✅ Done | `tools/extract_AH64D.py` → `config/nativeExtractions/AH-64D.json` |
| A3d. Mi-24P extraction script | ✅ Done | `tools/extract_Mi24P.py` → `config/nativeExtractions/Mi-24P.json` |
| A4. Shared generator | ✅ Done | `tools/generateControlMapping.py` handles all modules.  All per-module generators deleted. |
| A5. End-to-end verification | ✅ Done | FA-18C 334, AV8BNA zero-diff, AH-64D 626, Mi-24P 1194. |
| A6. Additional extractors | In progress | 4/~19 done.  Next: F-16C, then Ka-50_3. |
| A7. Archive old extractors | Not started | `tools/extractControlsLupa.py`, `tools/extractControlsFromDCS.py` → `archive/`. |

---

## Phase B: Module Script Migration (Vertical Slice)

Each module is done end-to-end before moving to the next.  Per-module steps:

1. **Extract** — Write extraction guide + script, produce `config/nativeExtractions/<module>.json`.
2. **Generate control mapping** — Run `tools/generateControlMapping.py` to produce `<module>.json` (canonical keys) and `<module>` alias file.
3. **Rename script controls** — Update alias file with any renames; `remapAliasKeys.py` handles canonical-key rewrites by (deviceId, commandId) fingerprint.
4. **Verify** — Full pytest suite, then live-validate with `tools/validateControlMapping.py`, then in-game verification (cold start at minimum).

| Module | Extracted | Control Map | Script Renamed | Verified |
|--------|-----------|-------------|----------------|----------|
| FA-18C | ✅ | ✅ | ✅ | Cold/Hot/Air/Shutdown |
| AV8BNA | ✅ | ✅ | ✅ | Cold/Hot/Shutdown |
| Mi-24P | ✅ | ✅ | ✅ | Cold/Hot/Shutdown |
| AH-64D | ✅ | ✅ | ✅ | Cold start |
| **F-16C** | — | — | — | **next target** |
| Ka-50_3 | | | | |
| F-15E | | | | dynamic name: `'F_UFC_' + cmd` |
| F-4E | ✅ | ✅ | — | 533/584 pass; 39 fail (mostly state-dependent ind fields); see `tools/validation-notes/F-4E-45MC.md` |
| Mi-8MTV2 | | | | |
| Ka-50 BS II | ✅ | ✅ | ✅ | Live validation 537/651 pass, 6 fail, 108 skip — see `tools/validation-notes/Ka-50.md` |
| CH-47F | | | | |
| A-10C | | | | |
| A-10C_2 | | | | |
| AJS37 | | | | |
| F-5E | | | | |
| F-86F | | | | |
| M-2000C | | | | |
| OH-58D | | | | |
| UH-1H | ✅ | ✅ | ✅ | Cold/Hot/Shutdown ✅ 2026-05-13 |
| A-4E | | | | not installed |
| C-101CC | | | | variant dirs |
| C-101EB | | | | variant dirs |

Migration patterns documented in `.agent/research/script-migration-patterns.md`.

---

## Phase B2: Live Control Validation — DONE for all 4 converted modules

Validate each converted module's control mapping against a running DCS instance
using `tools/validateControlMapping.py`.  Run hot start, active pause.

| Module | Controls | Pass | Fail | Skip | Notes |
|--------|----------|------|------|------|-------|
| AH-64D_BLK_II | 626 | 614 | 12 | 0 | 98.1% — all failures investigated, see `tools/validation-notes/AH-64D_BLK_II.md` |
| FA-18C_hornet | 491 | 472 | 15 | 4 | All remaining failures documented — `tools/validation-notes/FA-18C_hornet.md` (state-dependent IFEI fields, RAZBAM-style quirks). |
| AV8BNA | 277 | ~256 | ~21 | 0 | All remaining failures documented — `tools/validation-notes/AV8BNA.md` (RAZBAM quirks: STO stop lever, spring-loaded AFC, mirror rendering toggles). |
| Mi-24P | 1194 | 1002 | 30 | 162 | All remaining failures documented — `tools/validation-notes/Mi-24P.md` and `.agent/research/delta-only-commands.md`.  Zero regressions through the 2026-04-21 generator unification. |

---

## Phase C: Verification & Polish

- [ ] Text extraction verification — IFEI, UFC, other displays with systems powered on
- [x] Remaining FA-18C sequences — Hot Start, Air Start, Shutdown (verified 2026-04-19)
- [ ] Edge cases — DCS disconnection, mid-sequence recovery, module mismatch
- [ ] Update `tests/test_scriptFormat.py` for new control names
- [ ] Migrate `DCSMonitor.py` from `DCSBIOSExportManager` to `DCSDirectManager` (last remaining live BIOS reference outside `archive/`)
- [ ] **Revisit `sendProtocol` overrides** — audit every control that currently
  carries an explicit `sendProtocol` and determine whether it's actually
  required at runtime, or just cosmetic.  Recent FA-18C findings:
  - `SAI_rotate`: no override needed after all (the cage knob worked without it).
  - `Comm1Ch` knob: override needed for the *animation* of the knob, but the
    underlying radio channel changed correctly without it.  The knob's Lua
    `animate` flag was explicitly false, so the animation appears to be
    handled by the compiled DCS code rather than the Lua-visible click path.
  Goals (in order of preference):
  1. Eliminate `sendProtocol` overrides entirely if the runtime never needs them.
  2. Otherwise, derive the need for `C` vs `S` from a signal in the native
     Lua files (e.g. presence of a clickable handler, `animate` flag,
     `cycle` table shape, `_ITER` sibling presence) so we can stop
     determining them empirically.
  Also: `preserveExistingSendProtocol()` matches by `(deviceId, commandId)`
  alone, which silently propagated a FA-18C override onto an unrelated AV-8B
  switch when the wrong file got written to AV8BNA.json once.  Should also
  match on `moduleName` field of the existing file before importing overrides.

---

## Phase D: Final Cleanup

- [x] Update ARCHITECTURE.md — remove all BIOS references, reflect current native-only architecture
- [x] Update README.md — remove BIOS references, update setup/usage instructions
- [x] Update DEVELOPMENT.md — fix stale project-structure module list
- [x] Build control reference HTML page (replacement for DCS BIOS control-reference.html).
  Searchable, shows all controls in a module's controlMappings in a readable format for script authors.
  `type: "raw"` controls must be clearly delineated as 'use at your own risk' — no known argLim, step, or readback arg; script author must experiment to find correct values.
  Include a note pointing authors to the module's `Input/<variant>/keyboard/default.lua` and `Input/<variant>/joystick/default.lua` files, which contain `{device, action, value}` triples that often reveal the correct native value to pass for raw controls.
- [ ] Build control renaming utility — filter by device, batch add/remove prefix, rename positionMap controls.  Helps with human review of auto-generated names.  (`remapAliasKeys.py` covers the canonical-key case.)
- [ ] Remote logging toggle for export Lua (`L:1` command)
- [ ] Archive `tools/extractControlsLupa.py`, `tools/extractControlsFromDCS.py`

---

## Architecture Decisions

- **Per-module extractors + shared helper**: `tools/extract_<module>.py` calls into `tools/extractUtils.py` for the Lua mock environment, `dofile` wrapper, and `deviceTableMap` capture.  Module-specific quirks (command-table names, indicator structure, text-field patterns, bake/conditional detection) stay in the per-module script.
- **Extraction guide docs**: `tools/extraction-guides/general.md` (universal) + per-module.
- **Extraction output**: `config/nativeExtractions/<module>.json` — standardized schema consumed by `tools/generateControlMapping.py`.  Includes deterministic `deviceTableMap` captured via Lupa `__index` metatables.
- **Shared generator**: `tools/generateControlMapping.py` is module-agnostic.  No module-specific logic.
- **Categories**: Dropped (BIOS-only concept).
- **Control naming**: Canonical `<deviceName>.<cmdName>` verbatim from Lua.  No camelCase conversion, suffix stripping, or dedup.  Alias layer removed — scripts use canonical names directly.
- **Indications**: Extracted from device_init.lua `indicators[]` array.  Indication ID = array index − 1 (Lua 1-based → DCS 0-based).
- **Conditional indicators**: Include ALL variants.  Enables runtime equipment detection via T: command.
- **Bake indicators**: Flagged in extraction output, excluded from usable indication list.

---

## Relevant Reference Files

- `.agent/research/lupa-native-extraction.md` — architecture, mock requirements, pcall pattern
- `.agent/research/script-migration-patterns.md` — int16 conversion, SCREAMING_SNAKE→camelCase, per-module lessons
- `.agent/research/dcs-native-control-types.md` — value ranges, control behaviors, live test results
- `.agent/research/module-conversion-pipeline.md` — pipeline steps, directory mappings
- `.agent/research/delta-only-commands.md` — unresolved delta-only command category
- `.agent/decisions/canonical-alias-naming.md` — canonical/alias design decision
- `tools/extraction-guides/general.md` — universal DCS extraction patterns
- `tools/extraction-guides/FA-18C.md` / `AV8BNA.md` / `Mi-24P.md` — module-specific patterns
- `tools/extractUtils.py` — shared Lua mock / `dofile` wrapper / deviceTableMap capture
- `tools/validation-notes/*.md` — per-module live-validation results
- `config/controlMappings/*.json` — canonical control mappings
