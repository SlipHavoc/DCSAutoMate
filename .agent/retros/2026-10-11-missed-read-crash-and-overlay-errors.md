# Script crash on a missed read, and in-game error reporting

**Goal:** Fix an `IndexError` that killed an F-4E Cold Start on an MP server during a `scriptCockpitState` wait (INS align light), and make crashes visible to a player who is only watching the in-game overlay.

**What worked:**
- Root cause: in `DCSDirectManager.getControlState`, the arg branch appends nothing when `queryArgumentValue` returns `None` (1 s timeout or unparseable reply), so the executor's `getControlState(control)[0][2]` raised.  `readControl` already guarded this; the cockpit-state wait, loop pre-test and loop-end check didn't.  All three now go through `readControlState()`, and `_evaluateCondition` returns `None` (unreadable, try again) for a `None` state.  Before, string conditions compared it as `'None'`, so `contains 'N'` would have been met.
- `runScript` was testable without the full app: `DCSAutoMateApp.runScript(MagicMock())` with `DCSSeqExecute` patched in the `DCSAutoMate` namespace.  The new `tests/test_appScriptErrors.py` sorts right after `test_appPaths.py` and imports the real PySide6, the same way `test_controlPanelHelpers.py` already does before any file that stubs it.
- Merging `settings-window-cleanup` was a fast-forward, so `master` plus the stashed changes was the same tree that had passed with DCS running.

**What didn't:**
- The first draft of the retry tests asserted exact read counts and were wrong: with `duration: 0`, `handleScriptCockpitState` reads `stateCurrentTime` before setting `stateStartTime`, so the first met read gives a slightly negative elapsed time and a second read is needed.  This also meant an end-to-end string test passed on the buggy code (the second read rescued it), so it wasn't a valid red phase.  It was replaced with a pure `_evaluateCondition(None, 'contains', 'N', 'str')` test.  The quirk is logged in `todos/todo.md`.
- The PowerShell `2>&1` false exit code from the previous retro bit again.  That instruction update hasn't been applied yet.
- `TestCockpitStateLive` tests (including the new retry test) skip when DCS isn't running, so they ran in one suite run and were skipped in the next after the user closed DCS.  `pytest -rs` showed why the counts changed.

**Instruction update candidates:**
- Add to AGENTS.md test section (repeat of the 2026-10-06 proposal): "In Windows PowerShell, `2>&1` turns the faulthandler 'Windows fatal exception: code 0xe0000002' dump from the TTS tests into an error record and a false non-zero exit.  Check the pytest summary line, or `$LASTEXITCODE` with stderr sent to `$null`."
- Add to the DCSAutoMate-specific instructions: "Any code that reads a cockpit value through `dbe.getControlState` must handle an empty result: DCS may not answer within the timeout, especially on MP servers.  Use `DCSSeqExecute.readControlState()`, which returns `None`, and treat `None` as 'not readable yet'."
- Add to the DCSAutoMate-specific instructions: "New tests in `TestCockpitStateLive` (and other classes gated on 'DCS is not running') only run while DCS is up.  For a red/green check without DCS, also cover the logic with a pure-function test."
