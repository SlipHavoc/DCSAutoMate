# AV-8B & Mi-24P Conversion — Retrospective

**Date:** 2026-04-16
**Branch:** `eliminate-dcs-bios`

## Goal

Convert AV-8B Harrier (AV8BNA) and Mi-24P Hind scripts from DCS BIOS conventions to unified control mapping format. Run the full extraction/mapping/migration pipeline for each, verify in-game.

## What Worked

- **Pipeline is now repeatable**: The 3-step pipeline (extract → BIOS mapping → control mapping) worked smoothly for both modules with no code changes needed to any of the tools.
- **extractControlsLupa.py cycle fix**: The Harrier's `default_button_lever_cycled()` factory function produces `cycle = {false, true}` as a Lua table. Added detection and conversion via `luaTableToList()`. This fix was needed once and benefits all subsequent modules.
- **Per-module migration scripts**: Keeping these individual (not generalized) was the right call. Each module had different quirks:
  - AV8BNA: raw int16 value for RWR_VOL, BIOS relative string for BINGO_SET
  - Mi-24P: string-concat relative for throttles (`'-'+str(int16())`), string relative increments (`'+3000'`)
- **All scripts verified in-game**: AV8BNA (Cold Start, Hot Start, Shutdown) and Mi-24P (Cold Start, Hot Start, Shutdown) — all passed.
- **Test suite stable**: 683 passed, 32 skipped throughout.

## What Didn't Work

- **Nothing major failed.** The pipeline is maturing. Minor bumps:
  - Had to remember to restart the app after generating new control mapping JSON (warning: "Found commands with no description" appears otherwise).
  - Harrier's `clickabledata.lua` is in `Cockpit/` not `Cockpit/Scripts/` — just a path difference, not a code issue.

## Key Learnings

- **Cockpit directory structure varies by module.** Documented in `.agent/research/module-conversion-pipeline.md`. Need to check each module before running extraction.
- **Relative control values**: DCS BIOS uses `'-'+str(65535)` for full-reverse and `'+3000'` as step increments. Native equivalents are `-1.0` and `3000/65535 ≈ 0.0458`. The formula is always `biosValue / 65535`.
- **Continuous control values**: `int16(X)` → just `X`. The int16 wrapper was scaling 0-1 to 0-65535; native format uses 0-1 directly.
- **C-101 has variant subdirectories**: `Cockpit/C-101CC/` and `Cockpit/C-101EB/` each have their own `clickabledata.lua`, referencing `../Common/` for shared definitions. Will need special handling.

## Instruction Update Candidates

None — the existing AGENTS.md instructions are working well for this workflow. The `.agent/research/module-conversion-pipeline.md` file captures the accumulated knowledge for future sessions.
