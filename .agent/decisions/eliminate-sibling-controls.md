# ADR: Eliminate sibling control synthesis (`_EXT`/`_ITER`/`_AXIS`)

**Date:** 2026-05-01
**Branch:** `eliminate-dcs-bios`
**Status:** Accepted

## Context

The control mapping generator synthesises "sibling" entries for commands that appear in `command_defs.lua` but are not referenced by `clickabledata.lua`. These fall into three suffixed categories: `_ITER` (keyboard increment/decrement), `_AXIS` (joystick analog), and `_EXT` (all other external commands, typically DCS BIOS protocol).

After a full FA-18C validation run (644 pass / 20 fail / 40 skip), a systematic failure analysis revealed:

1. **`_EXT` siblings have unfixable structural failures.** Many TUMB-class switches produce a zero-delta command value (`argLim[0] + step * posIndex = 0`) for at least one position, which DCS treats as a no-op. Some `_EXT` commands are BIOS input commands that are silently ignored without BIOS loaded. These failures cannot be fixed without either loading DCS BIOS at validation time or adding special-case logic per control.

2. **Zero runtime usage.** Neither `DCSAutoMate.py` nor `DCSMonitor.py` references any sibling control by name. The startup scripts reference only base clickable commands or hand-named controls. Siblings are present in the JSON but never dispatched to.

3. **Disproportionate maintenance cost.** 212 sibling entries (28% of all FA-18C controls) require ~186 lines of generator logic, ~92 lines of validator logic, 13 of 19 generator unit tests, and a full separate `parseInputFiles.py` module. The same structural failures would recur for every new module added.

4. **The forcing case (SAI cage knob) is already solved differently.** The original motivation for `_ITER` synthesis was `SAI.CageKnobRotate_ITER` — the only BIOS protocol that reliably rotates the SAI without desync. Analysis showed the base command with explicit pull-in staging (`Option B`) works equally well and is already used by the shipped scripts. `CageKnobRotate_ITER` can be hand-added if ever needed.

## Decision

Remove all sibling control synthesis from the generator (`emitSiblingControls` and all supporting scaffolding), validator, runtime, tests, and JSON mappings.

- **Delete** `tools/parseInputFiles.py` and `tools/commandVariants.py` (only served sibling synthesis).
- **Remove** `testInferredCycleDiscrete()` and `readbackArgLim` branch from the validator.
- **Remove** `readbackArgLim` handling from `DCSDirectManager._reverseTranslateValue()`.
- **Remove** `siblingOf` step-lookup from `DCSControlPanel._defaultStep()`.
- **Delete** 13 sibling-focused generator tests; keep the 6 `annotateIndicatorArgLim` tests.
- **Regenerate** all 8 module JSON files without sibling entries.

## Consequences

### Positive
- ~380 lines of generator + validator code removed.
- 13 test functions removed; test suite becomes more focused.
- No more `_EXT` zero-delta or BIOS commandId failures cluttering validation output.
- Validation skip count drops from ~40 to near zero for FA-18C.
- JSON files are ~28% smaller for FA-18C; proportionally for other modules.

### Neutral
- `_AXIS` siblings (46 in FA-18C) are also removed. No joystick-analog control is currently used by any script, so there is no practical loss. If a future script needs joystick-axis output, add the control to the JSON by hand with the appropriate `argLim` and `sendProtocol`.
- `_ITER` siblings (56 in FA-18C) are removed. The only shipped use case (SAI cage knob) is covered by the base-command Option B approach. If a future script needs step-increment control for a specific switch, the entry can be hand-added.

### Risk
- If a future module has a control whose ONLY workable send protocol is `_ITER` (no clickable base command), it must be hand-added. This is an acceptable maintenance burden compared to synthesising 200+ broken entries per module.

## Revisit condition

If more than ~3 hand-added sibling entries accumulate across all modules in any 6-month period, reconsider targeted `_ITER`-only synthesis for that specific pattern.
