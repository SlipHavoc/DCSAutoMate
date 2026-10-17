# Retro: C-101CC Script Migration (BIOS → Native)

**Date:** 2026-05-25
**Branch:** cockpit-highlight

## Goal
Migrate `DCSAutoMateScripts/C-101CC_dcsbios.py` from DCS BIOS control names / int16 values to the canonical native format, producing `DCSAutoMateScripts/C-101CC.py`.

## What worked

- **Temp mapping script approach** worked cleanly again. `tools/temp_build_C101CC_map.py` parsed the DCS BIOS `C-101.lua` with regex (acceptable here — structured DSL, not complex Lua execution), built a `(deviceId, commandId)` lookup against `C-101CC.json`, and resolved all 42 names with zero missing. No manual lookup required.
- **Sort-by-length replacement** handled the two prefix-collision pairs correctly (`PUMP_COVER` before `PUMP`).
- **Migration transform script** (`tools/temp_migrate_C101CC.py`) applied all four mechanical steps (int16 removal, int16 call substitution, bulk rename, FIXME insertion) cleanly in one pass. Verification scan confirmed zero remaining `int16` calls and zero remaining SCREAMING_SNAKE names.
- **controlMapping JSON structure** reminder: top-level keys are `moduleName` and `controls`; `controls` is a flat dict keyed by `"CATEGORY.ELEMENT_NAME"`. Earlier sessions had this wrong.

## What didn't

- **FIXME indentation bug on first run:** The replacement string for the `'DEC'` BIOS relative value used `\n\t\t#pushSeqCmd` (double tab) but the original lines were `\t#pushSeqCmd` (single tab). Fixed by correcting `\t\t` → `\t` in the transform script and re-running. Trivial, but worth catching before committing.
- **positionMap None entries:** `C-101CC.json` positionMap arrays can contain `None` for positions with no command (e.g. centre detent). The mapping lookup loop needed a `if entry is None: continue` guard. This pattern has appeared before; should be added to the standard lookup template in `.agent/snippets/`.

## Instruction update candidates

1. **positionMap None guard** — add a note to `.agent/research/script-migration-patterns.md` under "Module-Specific Lessons" (or a general note) that positionMap arrays can contain `None` entries for no-command positions, and the lookup loop must skip them.
2. **controlMappings JSON structure** — clarify in the migration patterns doc that the control mapping JSON has `{"moduleName": "...", "controls": {"CAT.NAME": {...}, ...}}`, not a nested category structure.
