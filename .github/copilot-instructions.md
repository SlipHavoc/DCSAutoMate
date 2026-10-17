# Agent Instructions

This file defines how coding agents (Claude Code, Codex, Cursor, Copilot, etc.) should work in this repository. It is based on Simon Willison's [Agentic Engineering Patterns](https://simonwillison.net/guides/agentic-engineering-patterns/), adapted for an existing project being retrofitted with agent-assisted development practices.

If you are a coding agent reading this file: follow these instructions for every session in this repository. If any of them conflict with what the user just asked, ask before proceeding — do not silently override either one.

> **Tool-specific note:** Claude Code reads `CLAUDE.md` by preference and `AGENTS.md` as a fallback. If you are using Claude Code, either rename this file to `CLAUDE.md` or symlink it. Cursor can be pointed at it via `.cursor/rules/`. GitHub Copilot reads `.github/copilot-instructions.md`. The content is the same; pick whichever your tool expects.

---

## Start every session by running the tests

Before making any changes, run the project's test suite. Report:

- How many tests exist
- Whether they all pass
- How long they took

If there is no test runner configured yet, say so and ask the user how they'd like to proceed. Do not silently skip this step.

This serves three purposes: it tells you how to run the tests (you will need this later), it gives you a rough sense of the project's scale and shape, and it ensures you start from a known-good baseline so that any failure you see later is attributable to *your* changes.

The skip count depends on whether DCS is running: the live tests in `tests/test_sequenceExecute.py` skip without it.  When the count changes, list skip reasons (`pytest -rs`) before assuming a regression.

---

## Check for todos and keep the list current

Before starting work, check for any TODOs in the codebase that might be relevant to the task at hand. If you find any, report them to the user and ask if they should be addressed as part of this task.  Look for todo files that are named after the current git branch.

When you encounter a new TODO during your work, add it to the appropriate file in the `todos/` directory with a clear description and context. Do not leave TODOs as comments in the code; they should be tracked in the `todos/` files.

---

## The code quality bar

"Good code" in this repository means *all* of the following. These are not aspirational — they are the minimum bar for any change you propose:

- **It works.** Not "the logic looks right" — you have actually run it and confirmed it behaves correctly.
- **It is covered by tests that encode behavior that matters** — not tests that restate what the code currently does. A test that would still pass if the implementation were subtly wrong is worse than no test; it creates false confidence and locks in accidents of the current structure. Prefer tests at the boundary where correctness is observable (end-to-end behavior, pure-function input/output) over tests that assert on internal state or rely on heavy mocking. If a test requires extensive mocking to set up, the code under test is probably entangled with state that should be pushed to the edge — surface that rather than papering over it with mocks.
- **It solves the right problem.** If a request reveals a mismatch between what the user asked for and what they seem to actually need, stop and ask.
- **It handles error cases gracefully.** Failures should produce informative errors, not silent wrong answers or bare `except:` blocks.
- **It is simple and minimal (YAGNI).** Do not add configuration options, abstraction layers, plugin systems, or "future-proofing" that isn't needed right now.
- **It does not break existing functionality.** Run the full test suite after every change and confirm everything still passes.
- **It matches the existing style** of nearby code — naming conventions, formatting, module structure, error handling idioms. Infer style from neighboring files rather than imposing new conventions.
- **It is documented where appropriate,** and existing documentation is updated if behavior changes.

If you cannot meet this bar for a requested change, say so explicitly rather than delivering something worse and hoping nobody notices.

---

## Use red/green TDD for new functionality

When adding new functions, classes, or behaviors:

1. Write the tests first.
2. Run them and confirm they fail *for the right reason* (red phase). A test that fails because of an import error is not a valid red phase.
3. Implement the change.
4. Run the tests and confirm they pass (green phase).
5. Run the full suite to confirm nothing else broke.

Use red/green TDD when the desired behavior is already clear — bug fixes, well-specified features, adding a function with a known contract. Do not use TDD while exploring or prototyping; tests written before you know what you want tend to lock in the first thing that occurred to you. Once exploration converges on an approach, then write tests around the behavior you want to keep. If the user explicitly says "use red/green TDD" or "TDD this", treat it as a hard requirement regardless of where you are in the exploration.

---

## For bug fixes: reproduce first

When fixing a bug:

1. Write a test that reproduces the bug.
2. Run it. Confirm it fails, and that the failure matches the reported symptom.
3. Fix the bug.
4. Confirm the new test passes.
5. Run the full suite to confirm nothing else broke.

This guarantees the bug cannot silently return later.

---

## Test shape

Prefer tests at two levels: end-to-end tests that exercise whole flows and verify observable behavior, and unit tests around pure functions with no hidden state. Be sparing with tests in the middle tier — stateful helper objects, partially-mocked module integrations. If that layer is thick enough to need heavy testing, that is a signal the architecture needs attention, not more tests.

When a bug is hard to reach with an end-to-end test, consider whether the logic can be extracted into a pure function that is trivially testable, rather than building elaborate scaffolding to test it in place.

End-to-end tests are slower and less precise as diagnostics; pure-function unit tests are fast and localized. The two ends complement each other. The middle does not reliably do either job well.

---

## Refactoring is cheap now — surface opportunities, but ask first

If you encounter code that is obviously messy — bad naming, duplicated logic, a file that has grown too large, dead code, stale comments — **mention it**. If the user agrees, refactor it as part of the task, keeping the tests green throughout.

Do not silently embark on rewriting sprees the user didn't ask for. Always surface the refactor first, then wait for a go-ahead.

The cost of code improvements has dropped low enough to justify a zero-tolerance attitude toward minor code smells — but only when the user is in the loop.

---

## Exploratory prototyping

When the user is deciding between approaches, or says "try a few ways" or "explore options", build two or three small prototypes. Keep each one minimal — just enough to compare. Summarize the trade-offs at the end and let the user pick.

Prototypes belong in scratch files or a throwaway branch, not in the main tree, unless the user asks otherwise.

---

## Pattern matching on mixed-era code

This repository contains code written in three eras: hand-written code, early AI-assisted code, and recent agentic code. **The style is not perfectly uniform.** Before making changes:

- Look at files *near* the one you are editing, not arbitrary files from elsewhere in the repo.
- If you see a conflict between older and newer patterns, ask the user which to follow rather than guessing.
- When in doubt, prefer the pattern of the more recently modified files. You can check `git log -- <file>` if needed.

Do not attempt to "harmonize" the style of the whole repo without being explicitly asked.

---

## The `.agent/` directory

This repository uses a `.agent/` directory to accumulate knowledge across sessions:

- `.agent/snippets/` — small self-contained code examples of techniques used in this project.
- `.agent/research/` — markdown notes from prior investigations (libraries tried, approaches rejected and why, performance measurements).
- `.agent/decisions/` — short records of non-obvious design choices and the reasoning behind them (an ADR-lite format).
- `.agent/retros/` — session retrospectives (see below).

**At the start of any substantive task**, check whether `.agent/` contains anything relevant to what you are about to do. Specifically grep for keywords from the task description.

**At the end of any substantive task**, if you learned something that would help a future session — a library gotcha, a design constraint, a rejected approach and why — propose adding a note to the appropriate subdirectory.

---

## Retrospectives (the compound loop)

At the end of any session that produced non-trivial changes, write a short retrospective to `.agent/retros/YYYY-MM-DD-<slug>.md` containing:

- **Goal:** What was the user trying to accomplish?
- **What worked:** Which approaches landed on the first or second try.
- **What didn't:** Which approaches failed, and why (be honest — this is the most valuable part).
- **Instruction update candidates:** Is there anything that should be added to this `AGENTS.md` file so the next session goes more smoothly? Propose the exact wording.

This is the "compound engineering" loop. The instructions in this file should improve over time based on what was actually learned. If you never propose updates, something is wrong.

---

## Git discipline

- Never commit directly to `main` / `master` without explicit instruction.
- Make small, logically coherent commits with descriptive messages in the project's existing commit-message style.
- Before committing, run the full test suite one more time.
- If the user hasn't specified a branch, ask which branch they want the work on.
- If you are unsure whether something should be committed at all, ask.

---

## Things to NOT do

- **Do not disable, delete, or `@skip` failing tests to "make them pass".** If a test fails, either the test is wrong (explain why and ask) or the code is wrong (fix the code).
- **Do not weaken tests to make them pass** No relaxing an assertion, widening a tolerance, or changing the expected output to match the actual output. If a test fails after a change, either the change is wrong or the test was wrong for a reason you can articulate. "The test is now too strict" is not an articulated reason.
- **Do not add dependencies without asking.** Each new dependency is a maintenance commitment.
- **Do not make sweeping changes across many files** for a small requested change.
- **Do not invent requirements.** If the ask is ambiguous, pick the most plausible interpretation, proceed, and state your assumption clearly — but do not silently elaborate the feature beyond what was asked.
- **Do not claim a change works without having run it.** "The code looks correct" is not a substitute for execution.
- **Do not catch-and-swallow exceptions** to make errors go away. If you don't know how to handle an error, let it propagate and ask.
- **Do not delete or overwrite anything in `.agent/`** unless explicitly asked.
- **Do not edit this `AGENTS.md` file directly.** Propose changes in your retrospective; the user will apply them.

---

## Additional instructions

* When testing numeric translation/scaling functions, always include test cases where the identity function would produce incorrect results. E.g., for range scaling, don't only test with [0,1] ranges.

* When deleting files that contain institutional knowledge (migration scripts, one-time tools), capture the reusable patterns in `.agent/research/` before deletion.

* When running a subset of tests, list the files in alphabetical order, as the full suite runs them; some test files install a stub PySide6 that breaks later imports of the real one.
