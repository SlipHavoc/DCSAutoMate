# 2026-05-25 — C-101 RUDREG pedal adjuster controls

## Goal

Fix two bugs with the C-101 rudder pedal adjuster (`pedals_adj_control`):

1. **Type bug** — `MOVABLE_LEV` class was not recognised by `buttonOrAxis`,
   causing the pedal slider (`arg311` / `arg1202`) to be mapped as discrete
   instead of continuous.
2. **argLim bug** — the pull-handle (`arg1279` / `arg1280`) had `argLim =
   [1.0, 0.0]` from the Lua visual animation range, but the actual DCS arg
   value when the handle is pulled is `-1.0` (not `0.0`).
3. **step bug** — discovered during live DCS testing: after patching `argLim`
   to `[1.0, -1.0]`, the stored `step` was still `1.0`, causing the
   normalisation formula `round((native - argLim[0]) / step)` to return `-2`
   for native `=-1.0` instead of the correct `1`. DCSControlPanel displayed
   "Current: -2" when the handle was pulled.

## What worked

- **MOVABLE_LEV fix**: A one-line change in `mapUtils.py`
  (`cls == 'LEV'` → `cls in ('LEV', 'MOVABLE_LEV')`) fixed the type
  for all `MOVABLE_LEV` controls across every module immediately.
- **`c101PedalsAdjControl` wrapper**: Adding a post-processing wrapper in both
  `map_C101CC.py` and `map_C101EB.py` (delegating to `buttonOrAxis` then
  patching `argLim` and `step`) was the right architecture. Clean and
  localised.
- **Validation methodology**: Running `validateControlMapping.py` against live
  DCS confirmed both the original bugs and the fixes at each step.

## What didn't

- **argLim patch without step patch**: Patching `argLim` to `[1.0, -1.0]`
  without also updating `step` left the control in a half-broken state that
  passed validation (because DCS Direct sets args directly) but showed wrong
  "Current" values in DCSControlPanel. The display bug was only visible via
  live cockpit interaction, not via the validator.
- **Correct step formula not immediately obvious**: Required tracing the
  normalisation formula (`round((native - argLim[0]) / step)`) to realise
  the step must be the *signed* stride `argLim[1] - argLim[0]` (= `-2.0` for
  this inverted range). The formula `round(argValue - lim[0], 6)` computes
  this correctly once `argValue` is the patched `argLim[1]`.

## Key insight — signed step for inverted-range discrete controls

When `argLim[1] < argLim[0]` (inverted range), the step MUST be negative so
the send/receive formulas are consistent:

- **Send pos N:** `argLim[0] + step * N` (with step < 0, higher positions
  produce lower arg values — correct for this handle)
- **Receive native V:** `round((V - argLim[0]) / step)` (division by negative
  step flips the sign, mapping `V = argLim[1]` to position 1)

The `computeStepAndPositions` helper in `mapUtils.py` handles the case
`rng <= 0` by returning `(1.0, 2)` — always positive step, no sign inversion.
This is correct for range-less controls but wrong for inverted-range BTN
controls like this one. The patch in `c101PedalsAdjControl` overrides this
explicitly.

## Instruction update candidates

1. **Add to AGENTS.md** (under "Additional instructions"):

   > When patching `argLim` for a discrete control, always patch `step` at the
   > same time. The correct step for a 2-position control is
   > `argLim[1] - argLim[0]` (the signed stride). A positive `step` with an
   > inverted range like `[1.0, -1.0]` will cause `_reverseTranslateValue` to
   > return wrong position indices and DCSControlPanel to display garbage
   > "Current" values, even if validation passes (because DCS Direct sets args
   > directly rather than via the BTN animation mechanism).

2. Consider adding a consistency check in `validateControlMapping.py` or in
   the unit tests: for each discrete control, assert
   `abs(step) == abs(argLim[1] - argLim[0]) / (positions - 1)` within
   tolerance.
