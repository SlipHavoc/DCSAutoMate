# Retro: Eliminate Sibling Control Synthesis (_EXT/_ITER/_AXIS)

**Date:** 2026-05-02
**Branch:** `eliminate-dcs-bios`
**Commit:** `db48bbb`

## Goal

Remove the entire sibling-synthesis pipeline (`emitSiblingControls`) that inferred 212 extra controls (28% of FA-18C) from `command_defs.lua` suffixes.  These were tagged `inferred: true` / `siblingOf` and were never used at runtime.  Clean up all downstream references in the validator, runtime, UI, and tests, then regenerate all 8 module JSONs.

## What Worked

- **Phased plan executed cleanly:** A (docs+savepoint) → B (generator) → C (validator) → D (runtime+UI) → E (tests) → F (JSON regen) → G (delete scratch files) → H (pytest+commit).
- **Pytest count stayed at 738/32** throughout — the right 13 sibling tests were removed, no accidental collateral damage.
- **JSON regen was straightforward** once the extraction → moduleName → output filename mapping was confirmed (`config/nativeExtractions/<ext>.json` → `--module-name <DCS-name>` → `config/controlMappings/<DCS-name>.json`).
- **Grep verification** `grep -r "\"inferred\"\|\"siblingOf\"\|\"readbackArgLim\"" config/controlMappings/ | wc -l` = 0 gave clean confirmation.

## What Didn't

- **Replacing `testInferredCycleDiscrete` with its def-line shell:** The `replace_string_in_file` replacement accidentally pre-injected `def testReadOnlyArg(...)` in the middle of a refactor step rather than cleanly removing the body.  Ended up OK but required careful tracking.
- **First removal of `test_iterSiblingInheritsArgFromBase`:** The `newString` was set to just the following function's `def` line, which left the other 9 sibling tests still in the file with the `def test_buildCommandReverseStillPrefersBaseNames():` shell dangling above them.  Required 4 sequential targeted replacements to fully clean up — one per test group.  More precise scoping of the initial `oldString` would have avoided this.

## Lessons / Instruction Update Candidates

1. **When removing a contiguous block of tests, target the first line of the NEXT kept function** as the `newString` anchor.  Don't set `newString` to a later function's `def` line unless you've confirmed the `oldString` covers everything in between.

2. **For multi-module JSON regen, check `module` vs `moduleName` field name in extraction JSON first** (it's `module`, not `moduleName`) and confirm the existing control mapping file's `moduleName` before running `--module-name`.

3. **The `commandVariants.py` must NOT be deleted** — `inferDeviceTableMapByEvidence` is called in `main()` at line ~1235 for device-table evidence matching independently of sibling synthesis.  (Documented in session summary; noting here for future reference.)
