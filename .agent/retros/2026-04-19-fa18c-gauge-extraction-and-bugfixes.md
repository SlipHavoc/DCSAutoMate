# Session Retrospective — FA-18C Gauge Extraction & In-Game Bugfixes

**Date:** 2026-04-19
**Branch:** eliminate-dcs-bios

## Goal

Complete the FA-18C extraction pipeline by adding gauge/lamp extraction from mainpanel_init.lua, integrate into the control mapping generator, and verify all FA-18C scripts in-game.

## What Worked

- **Gauge/lamp extraction via lupa** — Mocking `CreateGauge` in the Lua runtime to capture arg numbers worked cleanly. 160 gauges/lamps extracted (90 named globals, 64 CautionLights enum, 6 fallback gauge_arg_*). The pattern of collecting args in a `_extractedGauges` list via the mock's side-effect was straightforward.

- **Generator integration** — Adding `processGaugesAndLamps()` to `generateControlMapping.py` was clean. Arg-overlap detection correctly skipped 3 gauge args that already had clickable element entries (e.g., canopy arg 181 has both a clickable and a gauge). This meant read-only gauges only supplement the mapping, never overwrite commandable controls.

- **Cross-module collision diagnosis** — When the battery switch failed in-game, tracing through `sendControl()` → `_lookupControl()` → iterating all modules revealed `battSw` existed in both AV8BNA and FA-18C_hornet. The fix was a one-line change passing `moduleName` from script metadata through to sendControl(). Clean and minimal.

- **DCS macro sequences as reference** — Reading `Macro_sequencies.lua` from the DCS module files gave the exact native command sequence for complex multi-step controls (parking brake). This is a reliable source of truth for how DCS itself operates these controls.

## What Didn't Work

- **isinstance check for gauge IDs** — The lupa runtime's permissive `__index` metamethod on table objects meant that accessing `controllers['_gaugeId']` on a table without that key returned the string `'_gaugeId'` instead of raising an error. This silently passed through and produced bad data until caught. Fix: always use `isinstance(value, (int, float))` when reading numeric fields from lupa table objects.

- **Parking brake positionMap values** — The `emergParkHandleSelectPark` control has a 3-position positionMap where position 1 is null (release). The "set brake ON" code used position 1 thinking it was "select park," but it was actually the null/release position. Position 2 is "select park." The DCS macro sequence in Macro_sequencies.lua confirmed the correct pattern: rotate to park (pos 2) → release (pos 1) → pull handle out.

## Key Learnings

1. **Always pass moduleName when sending commands from scripts.** Scripts always know their module. Global search should only be used for diagnostic/monitoring tools (like DCSMonitor), not for script execution.

2. **Multi-command positionMap controls require careful reading.** The position indices don't always map intuitively to the physical action. Always verify against the clickabledata.lua element definition and, when available, the Macro_sequencies.lua autostart sequence.

3. **Lupa table objects have permissive metamethods.** Never trust direct key access on lupa-bridged tables for optional fields. Always validate the type of the returned value.

4. **DCS's Macro_sequencies.lua is a gold-standard reference** for how multi-step cockpit controls should be operated programmatically. Check it when debugging control sequences.

## Instruction Update Candidates

1. **Add to AGENTS.md:** "When debugging control command sequences, check `Macro_sequencies.lua` in the DCS module's `Cockpit/Scripts/` directory — it contains the autostart/autostop sequences that DCS itself uses."

2. **Add to dcsautomate.instructions.md:** "When sending commands from scripts, always scope to the module. The `moduleName` from `scriptData` must be passed through to `sendControl()` to avoid cross-module name collisions."
