# Retro: Sibling synthesis (`_ITER`/`_AXIS`/`_EXT`) + `.canonical.json` cleanup + SAI fix

**Date:** 2026-04-25
**Branch:** `eliminate-dcs-bios` (3 commits added this session)
**Outcome:** Shipped. AH-64D SAI cage knob live-validated with two independent sequences (`_ITER` stepping and base-command staging). All 705 tests passing.

## Goal

The control mapping generator only emitted entries for commands referenced by `clickabledata.lua` (i.e. controls clickable in the cockpit). Native commands defined in `command_defs.lua` but only reachable via keyboard/external input — the `_EXT`, `_ITER`, and `_AXIS` siblings — were invisible to scripts. The AH-64D SAI cage knob was the forcing case: `CageKnobRotate_ITER` (cmd 3004) is the only protocol that reliably rotates the SAI without desync, but it had to be hand-added to the mapping.

Three sub-goals fell out:

1. Synthesize sibling entries automatically during extraction.
2. Drop the `.canonical.json` staging suffix now that `preserveExistingSendProtocol` makes hand-edits unnecessary — generator should write `<module>.json` directly.
3. Fix the wrong `sendProtocol: 'C'` default that was being emitted on synthesized `_ITER` siblings (carried over from the clickable-relative convention; wrong because `_ITER` needs `S:`).

## What worked

- **`emitSiblingControls` + `_meta` block** in `tools/generateControlMapping.py` — for each base command, look up its `command_defs.lua` entry, emit any `<Base>_ITER` / `_AXIS` / `_EXT` siblings as `inferred: true` with a `siblingOf` back-reference. Tagging makes them filterable downstream and lets `preserveExistingSendProtocol` skip them so wrong defaults can't be locked in.
- **Drop the suffix in one focused commit** — generator output path → `<module>.json`, `--existing` defaults to the output path, `DCSDirectManager._loadControlMapping` filter removed, `.canonical.json` files deleted, all 5 modules regenerated in place. Diffed against prior output to confirm `sendProtocol` preservation was working as intended before deleting the staging files.
- **`_ITER` `sendProtocol` fix landed cleanly once I caught the second-order bug** (see below). One-line removal in `emitSiblingControls`; `_ITER` falls through to the runtime default `relative → S:`, which is exactly what DCS BIOS PR #550 says it needs.
- **Live validation with two independent sequences** confirmed the model:
  - `SAI.CageKnobRotate_ITER` × 15 with arg `-0.75` (DCSControlPanel and Test script): rotated correctly, auto-pulled `CageKnobPull`, centered.
  - Base `SAI.CageKnobRotate` with explicit pull-in cycle (`0.792 → CageKnobPull=0 → 0.432`): also worked. This is a useful new data point — the base command isn't broken in absolute terms; it just doesn't trigger the state-machine side-effect the keyboard handler triggers.
- **Tests written for `emitSiblingControls` before completing the implementation** (9 new tests). The `'sendProtocol' not in entry` assertion in `test_iterSiblingInheritsArgFromBase` would have caught the bad default if it had been there from the start.

## What didn't (or needed a second try)

- **Wrong `sendProtocol: 'C'` default on synthesized `_ITER` siblings.** First implementation copied the convention from clickable-relative entries. But `_ITER` is the keyboard input path: it's invoked via `SetCommand` (`S:`), not `performClickableAction` (`C:`). Caught by reading the user's question — *"do we still need the sendProtocol override on the SAI cage knob?"* — not by tests. Lesson: when synthesizing entries from a different code path, don't reflexively copy defaults from the original path.
- **Preservation locked in the bad default across regenerations.** After fixing `emitSiblingControls`, the regenerated mapping *still* had `sendProtocol: 'C'` on `SAI.CageKnobRotate_ITER`. Root cause: `preserveExistingSendProtocol` reads the previous file and re-applies any `sendProtocol` it finds. The previous file had the wrong value because of the previous (buggy) generator run. **Fix:** make `preserveExistingSendProtocol` skip entries with `inferred: true` — preservation should only apply to hand-curated entries, never to entries the generator owns end-to-end. This is a generally useful invariant, not just an SAI fix.
- **Massive deletion in the final commit's diff** (684 lines deleted) was startling at first but explainable: previous regenerations had been preserving the wrong `sendProtocol: 'C'` on dozens of `_ITER` siblings across all 5 modules. The fix to `preserveExistingSendProtocol` cleared all of them on the next regen. Confirmed by spot-checking that the deletions were exclusively `"sendProtocol": "C"` lines on `inferred: true` entries.

## Instruction update candidates

One pattern worth adding to `AGENTS.md` or a research note (not yet decided which is the better home):

> **When introducing a new "owned by generator" entry class, decide up front whether preservation logic should apply to it.** Preservation that re-reads the previous output is a footgun: any wrong default the generator emits once gets locked in across all subsequent runs, and tests that compare to the previous output won't catch it. Tag generator-owned entries (`inferred: true`, or similar) and have preservation skip them.

Otherwise the existing machinery worked: the user's "do we still need the override?" question caught the bug, retro-driven `.agent/research/` notes carried the SAI history forward, and live validation closed the loop.
