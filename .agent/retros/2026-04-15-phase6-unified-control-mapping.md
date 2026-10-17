# Phase 6: Unified Control Mapping — Retrospective

**Date:** 2026-04-15
**Branch:** `eliminate-dcs-bios`
**Commits:** `3e8ca4e` (Phases A/B/D), `f840646` (Phase C)

## Goal

Replace DCS BIOS architectural influence with a clean unified control mapping format:
- 14 BIOS control types → 3 (discrete, continuous, relative)
- int16 scaled values → native proportional floats (0.0–1.0)
- SCREAMING_SNAKE_CASE names → camelCase
- Split commands/stateReads dicts → single flat controls dict
- FA-18C vertical slice only

## What Worked

- **Migration tool approach**: Creating `generateControlMapping.py` to produce the unified JSON from the old biosMappings was the right call. Automated the tedious mapping of ~500 controls and generated a name map for the script migration.
- **positionMap design**: Multi-command controls (ENGINE_CRANK_SW, CANOPY_SW) cleanly handled with per-position `{deviceId, commandId, value}` arrays. No special-casing in the translation layer.
- **Proportional continuous convention**: Having scripts send 0.0–1.0 meaning "percentage of range" is a clean abstraction that matches the old int16 semantics perfectly. `int16(0.5)` = 50% of range → now just `0.5`.
- **Automated script migration**: `migrateFA18CScript.py` with 13 ordered transformation steps handled the bulk of FA-18C.py changes reliably. Longest-first name sorting prevented partial-match issues.
- **Test stability**: All 672 tests passed throughout. The existing test suite caught nothing because the refactor was API-compatible at the test level, which is correct behavior — the tests exercised the contract, not the implementation.

## What Didn't Work

- **Initial continuous value semantics**: First implementation of `_translateValue` for continuous controls just clamped to argLim range (treated script value as native DCS value). User correctly identified this breaks for controls with non-[0,1] argLim (e.g., hmdOffBrt [0.0, 0.75]). Had to add proportional scaling after the fact. Should have recognized earlier that int16's percentage-of-range behavior was semantically important, not just a conversion artifact.
- **Test fixtures too narrow**: All continuous test fixtures used argLim [0.0, 1.0], so the proportional-vs-native distinction was invisible. Added hmdOffBrt [0.0, 0.75] fixture to catch this. Lesson: when testing math, always include cases where the identity function would give wrong answers.

## Instruction Update Candidates

1. **Add to dcsautomate.instructions.md**: "Continuous control values in scripts are proportional (0.0 = minimum, 1.0 = maximum of the control's native range). The translation layer in DCSDirectManager scales these to actual argLim values. This matches the semantic intent of the old int16() convention."

2. **Add to dcsautomate.instructions.md**: "When migrating other aircraft scripts from BIOS to unified format, use `tools/migrateFA18CScript.py` as a template. The key transformations are: remove int16(), replace SCREAMING_SNAKE names from nameMap, convert special-case controls (relative types need native delta values, not BIOS-scaled strings)."

3. **Consider adding to AGENTS.md**: "When testing numeric translation/scaling functions, always include test cases where the identity function would produce incorrect results. E.g., for range scaling, don't only test with [0,1] ranges."
