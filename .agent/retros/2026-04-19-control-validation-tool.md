# Session Retrospective — Control Validation Tool & AH-64D Validation

**Date:** 2026-04-19
**Branch:** eliminate-dcs-bios

## Goal

Create a standalone validation tool that smoke-tests every control in a module's
mapping against a running DCS instance, then use it to validate the AH-64D mapping.

## What Worked

- **TCP-based validation approach** — Connecting to DCS's TCP port 7780 and
  cycling each control through its positions, then querying arg values to verify,
  was straightforward and effective. 614 of 626 AH-64D controls pass.

- **Two-tier retry logic** — DCS animates controls at varying speeds (50ms to
  1.28s). A default 80ms delay catches ~95% of controls; retrying at 4× (320ms)
  and 16× (1.28s) catches the rest. This eliminated all animation-related false
  failures without needing per-control configuration.

- **Guard/cover auto-opening** — Scanning for 'cover'/'guard' in control names,
  opening all guards before testing, and closing them after. All guarded buttons
  (fire suppression, APU start, CMWS jettison) passed once their covers were open.
  Pattern: guard/cover controls are always discrete, 2-position, argLim [0,1].

- **Incremental testing with --only/--skip** — Being able to test subsets of
  controls made diagnosis much faster than running all 626 every time.

- **Pure-function unit tests** — 38 tests covering translateToNative,
  reverseTranslateFromNative, valuesMatch, parseIndication. These caught edge
  cases before live testing and ran in 0.04s.

## What Didn't Work

- **Initial 50ms delay was too short** — About 60 controls needed more time.
  Bumping to 80ms and adding retry logic fixed this, but the initial run had
  many false failures that obscured real issues.

- **Relative controls can't be validated generically** — The cageKnobRotate
  (SAI cage knob) uses ITER command 3004 with specific step values (-0.75).
  The generic relative test sends a small increment and checks for change,
  which doesn't match the expected step size. Relative controls may need
  per-control step values in the mapping to validate properly.

- **Safety-blocked controls are invisible** — M4 triggers don't move because
  the M4 safety is engaged, but there's no way to detect this from the mapping
  alone. Unlike guard/covers (which have obvious naming), safety dependencies
  are module-specific knowledge.

## Key Learnings

1. **Animation timing is the #1 source of false failures.** Any validation tool
   for DCS needs retry logic with increasing delays. The 4×/16× multiplier
   pattern works well.

2. **Guard/cover controls follow a consistent pattern** across modules: discrete,
   2-position, step 1.0, argLim [0,1], name contains 'cover' or 'guard'. This
   makes auto-detection reliable.

3. **Power levers have DCS-enforced travel limits** (idle cutoff / emergency
   power lockouts). The mapping shows full [0,1] range but DCS clamps to
   ~[0.25, 0.9]. The validation tool now reports actual vs expected range.

4. **Spring-loaded buttons return to 0 regardless of delay.** They need a
   different validation strategy (check arg changed during press, not after).

5. **Module name matters** — the FA-18C mapping file must use `FA-18C_hornet`
   (the DCS internal module name), not `FA-18C` (the folder name). The
   `generate_FA18C.py` had this wrong, producing an unused duplicate.

## Instruction Update Candidates

1. **Add to AGENTS.md or dcsautomate.instructions.md:** "When creating or
   regenerating control mappings, verify that the moduleName matches the DCS
   internal module name (returned by the `I` TCP command), not the filesystem
   folder name. These often differ (e.g., FA-18C_hornet vs FA-18C)."

2. **Add to AGENTS.md:** "After adding new tooling, run the validation tool
   against at least one module to verify the tool works end-to-end before
   considering the feature complete."
