# Retro: live scripts, sim commands, and the end of keyboard commands

**Goal:** Started as C-130J Auto Select (detect a preflighted spawn).  That needed live cockpit reads, which grew into live scripts; telling the player when they could leave the cockpit grew into lookahead; and replacing keystrokes grew into `scriptSimCommand` (LoSetCommand), DCS's own iCommand name table, comms menu support, and finally no keystrokes left in any aircraft script (M-2000C's old `_dcsbios` copy aside).  Branch `live-scripts`, 20 commits on top of `map-scripts-arch`.  Auto Select itself is still to do.

## What worked

- **Asking DCS for its own tables instead of guessing.**  `Input.getEnvTable().Actions` from the Hook gave all 2159 iCommand names and numbers in one mission start; `config/simCommands.json` is that output.  Every keystroke conversion after that was a lookup, not an experiment.
- **User testing each module in DCS before committing.**  It found everything the tests couldn't: `iCommandThrottleIncrease` latches in the Mi-8/Mi-24 but only steps in the AV-8B (11 sends to idle); the comms menu works with the menu closed, remembers its level, and resets with `ICommandMenuItem12`; `iCommandPlaneCollectiveDecrease` latches despite a `pressed` binding.
- **Before/after sequence snapshots for every bulk script edit.**  Generating every script function's sequence before and after (131 script/var combinations for the helper refactor, per-row equivalence for number-to-name) made "nothing else changed" a checked fact, and caught a regex that silently converted zero `\` rows.
- **Reusing the cockpit-warning machinery for the comms menu.**  Parametrizing the lookahead scanner with a step predicate gave the comms menu warning, its all-clear and live-script lookahead with a few lines, and the existing cockpit tests guarded the refactor.
- **Small pure functions at the edges:** `simCommandProblem()` for validation and execution alike, `isEngineRunning()` for Auto Select, `lastRowAfterLoops()` for all-clears.  All trivially unit-tested.

## What didn't

- **I inferred command behaviour from keybinding fields.**  I said a `pressed` binding meant the command must repeat, and built `hold=`/`stop=` (export-side per-frame repeat) for the Mi-8 collective.  The user's test showed a single send latches until the stop command.  The option stays, but nothing needs it yet.  Behaviour is per module and only a test in DCS says what it is.
- **Guessed occurrence counts in bulk-edit scripts.**  Twice an exact-count check failed (14 vs 12, 5 vs 4) and once a script stopped after writing some files but not others.  Count first, and validate every file before writing any.
- **Regex escaping of a literal backslash** (`'\\'` in Python source inside a regex) matched nothing; the verification step caught it, the edit step didn't.
- **Mapping named after the install folder, not the DCS name.**  `OH-58D.json` / `moduleName: 'OH-58D'` was self-consistent, so every test passed, but DCS reports `OH58D`, so Auto Select couldn't find the script.  Only a live run shows the reported name (telemetry "Aircraft:").
- **Terminal friction:** multi-line `python -c` gets mangled by bracketed paste; Git Bash `/tmp` isn't Windows Python's `/tmp`; the agent terminal sometimes injects `^C` into a command, so re-run rather than assume a result.
- **A todo note drifted from the decision.**  `todos/map-scripts-arch.md` still labelled the declarative option "A" after the user chose the `autoSelect()` function (also called "A" in a later message).  Now fixed; record choices by content, not letter.

## Instruction update candidates

- Add to "Additional instructions": "Never infer how a DCS command behaves (latching, stepping, needs repeating) from keybinding fields such as `down`/`pressed`/`up`; behaviour is defined per module.  Propose a small Test-script experiment and let the user confirm in DCS before converting scripts."
- Add to "Additional instructions": "For bulk edits, have the edit script compute and print occurrence counts rather than asserting hand-counted ones, and validate every file before writing any of them.  After a script bulk edit, compare every script function's generated sequence before and after."
- Add to `dcsautomate.instructions.md`: "A script's `moduleName` and its control mapping file must use the name DCS reports (`LoGetSelfData().Name`, shown as "Aircraft:" in the telemetry readout), not the install folder or DCS BIOS name.  Known differences: Mi-8MTV2 → Mi-8MT, OH-58D → OH58D, AH-64D → AH-64D_BLK_II."
- Add to "Additional instructions": "When writing a user's decision into a todo or note, describe the chosen option by what it is, not by its letter in a list of options."
