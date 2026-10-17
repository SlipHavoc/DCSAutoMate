# Retro: CH-47F Full Migration (Phase 4–6)

**Date:** 2026-05-10
**Branch:** eliminate-dcs-bios

## Goal
Complete per-seat validation for all 6 CH-47F crew positions, then rewrite `CH-47F_dcsbios.py` → `CH-47F.py` using canonical names from the `CH-47Fbl1` controlMapping.

## What worked
- Per-seat validation for left gunner, right gunner, and ramp all came back 91/0/262 — clean passes with no surprises. Those seats share the same 7466 controls as the main crew.
- The DCS BIOS → canonical name mapping process worked cleanly: found command IDs in `CH-47F.lua`, cross-referenced against the controlMapping JSON, and produced a complete 1:1 table with no ambiguous collisions.
- The script rewrite was mechanical and straightforward once the mapping table was complete.

## What didn't
- Args 562 (`ELECTRICAL_UTILITY_PRESSURE`) and 563 (`ELECTRICAL_APU_READY`) are `defineFloat` lamps in DCS-BIOS defined only against raw arg numbers. They appear nowhere in the native CH-47F Lua files — not in `clickabledata.lua`, not in any `*_init.lua`, not in the `Systems/` subdirectory. There is no named Lua variable to extract, so they cannot be added to the `gaugesAndLamps` section of the extraction without hardcoding.
- Attempted searches in `arcade_indicator_init.lua`, `crew_indicator_init.lua`, `mainpanel_init.lua`, `IndicatorsCmn/`, `LPCAPs/`, and all `Systems/` files — all empty. The arg numbers simply jump from 561 (OCEP_APU_2) to 564 (OCFC_MODE_1) in the clickabledata, with 562/563 being shape-layer lamp args only.
- The `Test()` function had all its content commented out as FIXME (radar altimeter not in mapping), causing a test failure on first pass. Required a placeholder `scriptText` command.

## Decision: lamp args with no native Lua variable
When DCS-BIOS uses `defineFloat` against a raw arg number that has no corresponding named variable in any native Lua file, those controls are inaccessible via the native extraction pipeline. The correct action is to comment out the `scriptCockpitState` calls with a FIXME, not to hardcode entries into the extraction JSON.

## Instruction update candidates
- Add to the mode instructions (Phase 6, step f): "If a `scriptCockpitState` control references a `defineFloat` arg that has no named variable in the native Lua files, comment it out with `# FIXME: arg N has no named variable in native Lua — not extractable`. Do not hardcode entries into the extraction."
- Add to Phase 2: "After extracting gaugesAndLamps, cross-check against any `defineFloat` / `defineIndicatorLight` entries in the DCS-BIOS module Lua to identify any lamps that exist only as raw arg numbers. Document these in the extraction guide as 'lamp-only args with no native variable'."
