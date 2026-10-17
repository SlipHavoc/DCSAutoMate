# Retro: Validator fixes and Ka-50 Blackshark III script conversion

**Date:** 2026-04-30
**Branch:** eliminate-dcs-bios

## Goal

1. Fix a restore bug in `testDiscrete` that caused false validation failures on `animated_guard_switch` toggle covers.
2. Fix a false failure in `testDiscretePositionMap` for position 0 when the control starts at its default state.
3. Convert `DCSAutoMateScripts/Ka-50 Blackshark III.py` from DCS BIOS `SCREAMING_SNAKE` control names to canonical `Device.Command` names, matching the pattern already established in `Ka-50 Blackshark II.py`.

## What worked

- **Read-before-restore guard for `testDiscrete` was the right fix.** Querying the arg before sending the restore command, and skipping the send if it's already correct, is both correct for toggle covers and harmless for regular discrete controls. The logic is self-documenting with a clear comment explaining *why*.

- **Conditioning the positionMap unchanged-check on `preNative`** was minimal and accurate. One extra `and not valuesMatch(preNative, value)` clause was all that was needed — no structural changes.

- **Using `Ka-50 Blackshark II.py` as the reference** for the III conversion was the right call. The two cockpits are nearly identical and the II was already fully converted. It provided both the canonical name mapping and the `coverSet()` pattern without needing to re-derive either.

- **`coverSet()` helper eliminates a whole class of idempotency bugs** in startup scripts. Because toggle covers flip on every command regardless of value, a bare `pushSeqCmd` is state-dependent. The `scriptLoopUntilStart` / `scriptLoopUntilEnd` wrapper makes it an absolute set. Worth using in any module with `animated_guard_switch` covers.

- **Ka-50_3 validation result (536 pass, 8 fail) held through the validator fixes.** The 8 remaining failures are confirmed edge-cases unrelated to the cover restore bug (18 → 8 improvement from the fix).

- **Ejection switch polarity note was critical.** Ka-50 ejection switches are `0 = ON (armed)`, `1 = DISABLED`. ColdStart arms them (0), Shutdown disables them (1). The original III script had this wrong for Shutdown (was sending 0 to "disable" them). Caught and fixed during conversion.

## What didn't work

- **Initial `multi_replace_string_in_file` batch on ColdStart had 4 failures** because ColdStart and HotStart have several identical code blocks (NAVLIGHT section, VOICE_MSG_EMER, the "Default startup done" UV26/weapons section). The tool correctly refused to apply those replacements to avoid ambiguity. Fix was to replace the HotStart block as a single large replacement using the unique `"Running Hot Start sequence."` anchor, then replace the identical ColdStart blocks separately using the `"Running Cold Start sequence."` + `'Set collective full down.'` anchor context. This worked cleanly.

- **EKRAN cover in the original III script had a misleading FIXME comment** ("Doesn't matter what value you send, the cover is always toggled"). The comment accurately described the problem but the old "solution" (raw toggles with a disclaimer) was fragile. Replaced with `coverSet()`.

## Instruction update candidates

- Add to the "Things to NOT do" section or a new "Script conversion" section: *When ColdStart and HotStart contain identical code blocks, do not attempt to replace them in a single batch. Replace HotStart first using the unique "Running Hot Start sequence." anchor, then ColdStart with its unique anchor. The tool will refuse ambiguous multi-match replacements — this is correct behavior, not a bug.*

- Consider adding: *For `animated_guard_switch` covers in startup scripts, always use the `coverSet()` pattern (see `.agent/snippets/cover-set-helper-ka50.md`). A bare `pushSeqCmd` for a toggle cover is state-dependent and will produce wrong behavior if the cockpit isn't in the expected initial state.*

## Files changed

- `tools/validateControlMapping.py` — testDiscrete restore guard, testDiscretePositionMap pos-0 fix
- `tests/test_validateControlMapping.py` — two new `TestDiscreteRestore` regression tests
- `DCSAutoMateScripts/Ka-50 Blackshark III.py` — full conversion from BIOS names to canonical names, `int16()` removed, `coverSet()` added, ejection polarity fixed
