# Retro: 32-bit float precision fix — `resolution` parameter

**Date:** 2026-05-20
**Branch:** cockpit-highlight

## Goal

Fix `scriptCockpitState` silently never firing for the F-86F canopy-open condition (`value=0.9, condition='>='`) even though the canopy was fully open.  DCSControlPanel showed `0.900`, so the cause was not immediately obvious.

## Root cause

DCS's Lua engine stores continuous control positions as 32-bit (single-precision) floats.  When serialized to a string over the TCP export connection, the fully-open canopy value `0.9f` becomes `'0.89999997615814'`.  Python's `float('0.89999997615814') >= 0.9` evaluates to `False` because Python uses 64-bit doubles and the serialized value is genuinely less than the 64-bit `0.9`.

DCSControlPanel masked this by formatting with `:.4f` — both `0.89999997615814` and `0.9` display as `0.9000` at that precision, so the display looks fine while the comparison fails.

This is a systematic artifact of the DCS protocol, not a bug in a specific aircraft.  Any `arg.*` control that nominally hits a round decimal value (e.g. `0.1`, `0.25`, `0.5`, `0.9`) may exhibit it.

## What worked

- **`round(float(controlState), resolution)` with `resolution=5` default.**  `round(0.89999997615814, 5)` → `0.9`.  The artifact is ~2×10⁻⁸; 5 decimal places (resolution 1×10⁻⁵) absorbs it while preserving all cockpit-meaningful precision.  Comparable to DCS BIOS's 16-bit integer resolution (~1.5×10⁻⁵).
- **Only round the DCS-returned value, not the user-specified `value`.**  The imprecision is entirely on the DCS side; user thresholds should remain exact.
- **Exposing `resolution` as an optional script parameter** (defaulting to `5`) covers edge cases where a control genuinely needs finer comparison.  Added to `scriptCockpitState`, `scriptLoopUntilStart`, and `scriptLoopUntilEnd`.
- **Diagnosis via live TCP query** (`Q:0:181` → `R:0:181:0.89999997615814`) confirmed the exact serialized value.  Without this, it would have been very hard to find.
- **Temporary workaround first, proper fix after.**  Shipping `value=0.89, condition='>'` to unblock the shutdown script while designing the engine fix was the right sequencing.  The workaround was reverted once the fix was in.

## What didn't

- **Nothing major failed** — the implementation was straightforward once the root cause was known.  The hard part was diagnosis.

## Tests added

Three tests in `TestCockpitStateLive`:
- `test_dcs32bitFloatPrecision` — mock returns `'0.89999997615814'`; asserts condition fires with default resolution.  This was the exact failing case.
- `test_customResolutionCoarser` — `resolution=3`; same artifact value; asserts fires (coarser rounding also absorbs it).
- `test_customResolutionFiner` — `resolution=10`; artifact does *not* fire; asserts condition only fires when `'0.9'` actually arrives and that at least 4 calls were made.

## Future work

Consider auditing other aircraft scripts for ad-hoc workarounds (e.g. `value=0.89` instead of `value=0.9`) that were written to paper over this artifact before the fix existed.  F-86F is the only confirmed case but others may exist.

## Instruction update candidates

Add to `AGENTS.md` or user tooling notes: **DCS 32-bit float artifact** — `arg.*` continuous controls that nominally hit round decimal values (0.1, 0.25, 0.5, 0.9, etc.) will serialize over TCP as values slightly below the exact decimal (e.g. `0.89999997615814`).  The `resolution=5` default in `_evaluateCondition` absorbs this.  If authoring a new script and a round-decimal threshold never fires, run a live TCP query (`Q:device:arg`) to confirm the actual serialized value before debugging the script logic.
