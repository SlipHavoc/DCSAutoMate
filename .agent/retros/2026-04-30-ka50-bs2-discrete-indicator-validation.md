# Retro: Ka-50 BS2 discrete-indicator validation

## Goal

Apply the Ka-50_3 discrete-indicator lessons back to Ka-50 Blackshark II by rerunning extraction, regenerating the control mapping, and live-validating the result.

## What worked

- The existing Ka-50 extractor ran cleanly against the current DCS install. Its warnings matched the known harmless extraction-guide warnings.
- Structured JSON comparison separated real mapping changes from native-extraction object-order churn. The extraction was semantically unchanged; the mapping had exactly 46 `indicatorArgLim` additions and no other control changes.
- The discrete-indicator validator path worked as intended. Shared-arg discrete controls passed as indicator-range controls without exact send/read matching.
- Live validation completed against Ka-50 BS2 with 537 pass, 6 fail, 108 skip, 0 error after a rerun with all 23 guards/covers verified open.
- Focused fire-extinguisher tests clarified the initial validation anomaly. `FIRE_EXTING_INTERFACE.FIREEXT-COVER-PTR` behaves as a toggle when sent its current value, but the second full validation started from the expected closed state, opened all covers, and both the cover and `FIRE_EXTING_INTERFACE.FIREEXT-PTR` passed.
- `HSI.ROTARY-ZPU-PTR` also passed on the second full validation, so its earlier failure was state-sensitive rather than a persistent mapping/script issue.
- No behavioral changes were needed in `DCSAutoMateScripts/Ka-50 Blackshark II.py`; the existing `coverSet()` helper remains the right startup-script pattern for toggle covers.

## What didn't

- `config/nativeExtractions/Ka-50.json` rewrote with different JSON object ordering even though it is semantically identical. This creates noisy diffs after regeneration.
- The remaining 6 live-validation failures still need either accepted-failure documentation or future targeted fixes. Several are likely command/readback scale asymmetries or cover animation/timing behavior rather than startup-script problems.
- The validator JSON schema uses `details`, not `message`; quick analysis scripts should read `details` when summarizing failures.
- Guard pre-opening can be state-sensitive for toggle covers. A robust future validator improvement would query a guard arg before sending and only toggle when it is not already at the desired open value, matching the script-side `coverSet()` pattern.

## Instruction update candidates

Consider adding: When reviewing regenerated extraction JSON, use structured JSON comparison against `HEAD` before interpreting the text diff. DCS extraction output can reorder JSON object keys without semantic data changes.

Consider adding: Validation result JSON stores per-control explanation text under `details`, not `message`.

Consider adding: For `animated_guard_switch` validation, classify toggle-vs-absolute behavior with a read-send-current-reread probe before assuming a command value is an absolute target.
