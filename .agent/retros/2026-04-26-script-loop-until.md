# Retro: scriptLoopUntilStart / scriptLoopUntilEnd

**Date:** 2026-04-26
**Branch:** eliminate-dcs-bios

## Goal

Add a paired-marker control flow primitive to DCSAutoMate scripts so a block of commands can be repeated until a cockpit-state condition is met.  Original todo: *"Add the ability to have do-loops that execute until a cockpit state condition has been met. E.g. 'do until bingo fuel value = 3000: press bingo increment button' or 'do until attitude indicator position is X: turn attitude indicator adjustment knob'."*

## What worked

- **Pair markers, not nested-list syntax.**  `scriptLoopUntilStart` and `scriptLoopUntilEnd` are emitted into the same flat `seq` list as every other command.  A pre-pass in `validateSequence()` and a second pre-pass in `execute()` build a `{startRow → endRow}` map so the executor can jump between paired rows without restructuring the sequence.  Authoring stays as `pushSeqCmd(...)` calls — no new builder API, no nested closures.  See [engine/DCSSeqExecute.py](engine/DCSSeqExecute.py#L186) (validation) and [engine/DCSSeqExecute.py](engine/DCSSeqExecute.py#L271) (executor pre-pass).
- **Both pre-test and post-test semantics on the same primitive.**  Putting `control` / `condition` / `value` on the Start marker yields `while`-style (skip body if already met).  Putting them on the End marker yields `do…while`-style (always run body once).  No second keyword needed.  Documented in [README.md](README.md#L112).
- **Reused `scriptCockpitState`'s comparison logic.**  Factored the existing operator-and-coercion code into `_evaluateCondition(controlState, condition, value, valueType)` so the loop markers could call it directly.  No risk of subtle divergence between the two surfaces (e.g. how an empty-string display from an unpowered gauge is handled — both now treat it as "not yet readable, try again later").
- **`maxIterations` and `timeout` are budget caps, not failure modes.**  When exceeded the loop exits with a warning message and execution continues.  This matches the project's convention that DCSAutoMate scripts are best-effort: a failed loop should not abort a long cold-start sequence.
- **Script validation catches missing partner markers** before execution starts (Start without End, End without Start), with row numbers.  Ran into one bug during dev where a typo'd marker silently worked; added the pairing pass to [validateSequence](engine/DCSSeqExecute.py#L196).

## What didn't

- **Initial design tried `scriptLoopUntil` as a single command containing a nested list of commands.**  Required a new authoring API and a second execute() implementation for the nested list.  Discarded in favor of the flat-marker design above.  Lesson: *if a feature would force two execute() paths, consider whether a marker-pair design lets it reuse the existing path.*
- **First pass of `_evaluateCondition` returned `False` for unreadable controls.**  In a tight loop this caused infinite spin until `maxIterations`/`timeout` exhaustion.  Fixed by returning `None` (sentinel for "try again later") and treating `None` the same as a not-yet-met condition without counting it as an iteration toward the budget.  Now matches `scriptCockpitState`'s long-standing behavior.
- **Test coverage was thin at first** — only the happy path.  Added 170 lines to [tests/test_sequenceExecute.py](tests/test_sequenceExecute.py) covering: pre-test skip, post-test always-runs-once, `maxIterations` exit, nested loops, mismatched markers, unreadable control mid-loop.

## Future work

- **Multi-condition AND/OR**.  Currently a single `(control, condition, value)` triple per marker.  See deferred entry in [todos/todo.md](todos/todo.md).  Multi-condition is rare enough that nested loops handle the common cases; defer until real demand surfaces.
- **General "auto-confirm every command" mode** (the original dynamic-timing todo).  scriptLoopUntil is a building block for this — a future per-command mode could synthesize a 1-iteration loop around each DCS command — but it is a separate feature with its own design questions.

## Instruction update candidates

Nothing for `AGENTS.md`.  The README section and the test file are the right home for these notes.
