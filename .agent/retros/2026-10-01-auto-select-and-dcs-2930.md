# Retro: Auto Select, live loadout and seat reads, mission-time timers, and the DCS 2.9.30 check

**Goal:** Use the live-script machinery for things the scripts couldn't know before they started: Auto Select hooks (C-130J preflighted spawn, FA-18C/F-16C helmet), the AH-64D Longbow added from the rearming screen mid start-up, and the player's AH-64D seat.  Along the way: a control reference page, telemetry and sim commands in the Snapshot Tool, the total time on "Script complete", re-checking everything after DCS 2.9.30, its new `LoGet*` exports, timers that follow DCS's clock, and a one-command update check.  Branch `auto-select`, fast-forwarded to `master` and pushed in stages.

## What worked

- **Live DCS checks for anything the docs don't say.**  The user sat in each AH-64D seat while the agent read `LoGetPlayerSeat` (back = 0, front = 1), and the agent called each new 2.9.30 export once before cataloguing it.  Two minutes of the user's time replaced guessing at seat numbering.
- **Proposing, then asking, for design forks.**  Hashes vs a re-run tool, PC clock vs mission time vs acceleration factor, Auto Select vs run-time seat detection: laying out two or three options with a recommendation got a quick decision each time, and the user twice picked the option that made the feature simpler.
- **Replaying a real change to test a tool.**  Running `tools/checkDcsUpdate.py` in a temporary worktree at the commit before the Mi-24P re-extraction reproduced the 2.9.30 keybinding fix exactly, which is a better test of the "something changed" path than any fixture.
- **Pure functions under the UI:** `controlRows()` for the reference page, `changedRefs()` / `snapshotReport()` / `flattenTelemetry()` for the Snapshot Tool, `parseSimCommandEntry()`, `newScriptTimer()` / `scriptTimerElapsed()`, `dcsUpdateNotice()`.  Every UI change sat on top of tested logic, and the offscreen smoke runs only had to check the wiring.
- **Measuring before designing.**  Timing the reference data build (0.3 s) and the staleness check (6 ms) settled "regenerate at startup?" immediately; counting entry shapes across all 22 mappings before writing the generator found the `sendValue` / `readbackValue` position maps and partial bindings that the first sample didn't show.
- **Splitting finished work into one commit per feature** (README staged by hunk with `git apply --cached`), and checking each commit passes on its own in a throwaway worktree.

## What didn't

- **A multi-replace edit landed garbled** (the AH-64D Hot Start lost a closing paren and kept the old lines).  The full test run caught it at collection, but only because the suite imports every script.  Re-read the diff after any multi-location edit.
- **Duplicate context in multi-replace.**  `SnapshotPanel` and `IndicatorScanPanel` build an identical module row, so two replacements failed as ambiguous.  Include the class's own lines (`self._snapshotDone.connect(...)`) as context.
- **The integrated browser served a cached `file://` page,** so three CSS fixes appeared to do nothing.  Checking computed styles with Playwright showed the old rules; adding `?v=N` to the URL fixed it.
- **Offscreen Qt smoke scripts lost their output twice:** `os._exit(0)` skips flushing stdout.  Flush first.
- **Running a test subset in a non-alphabetical order** made `test_controlPanelHelpers.py` fail to import `QtGui`, because another test file installs a stub PySide6 first.  The full suite runs files alphabetically, so subsets should too.
- **Proposed an Auto Select hook for the AH-64D seat before checking where the var lives.**  Auto Select only sets vars on the start script it picks, and `seat` is only on Load Route / Load Scratchpad.  Caught before any code, but it cost a round trip.
- **Skip counts move with DCS:** 48 skipped with DCS running, 59 without (11 live tests in `test_sequenceExecute.py`).  Looked like a regression until the skip reasons were listed.

## Instruction update candidates

- Add to `dcsautomate.instructions.md`: "After a DCS update, run `python tools/checkDcsUpdate.py`, review the reported changes, and commit `config/nativeExtractions`, `config/controlMappings` and `config/dcsVersionChecked.json`."
- Add to `dcsautomate.instructions.md`: "Auto Select only sets vars on the script it picks (Cold / Hot / Air Start).  For a var that only exists on other scripts (e.g. AH-64D `seat`), read the value at run time in a live script instead."
- Add to "Start every session by running the tests": "The skip count depends on whether DCS is running: the live tests in `tests/test_sequenceExecute.py` skip without it.  When the count changes, list skip reasons (`pytest -rs`) before assuming a regression."
- Add to "Additional instructions": "When running a subset of tests, list the files in alphabetical order, as the full suite runs them; some test files install a stub PySide6 that breaks later imports of the real one."
