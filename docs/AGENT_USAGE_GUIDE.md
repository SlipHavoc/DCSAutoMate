# How to Use AGENTS.md: A Guide for You

This is a guide for *you* (the human) on how to work with your coding agent in this repository, and how to get the benefits of Simon Willison's agentic engineering patterns in a project that wasn't built this way from the start.

It's the counterpart to `AGENTS.md`, which is what the agent reads. That file tells the agent what to do. This file tells you what you should do.

---

## The mental model shifts

Two things to internalize before you start.

**Writing code is cheap now, but good code still has a cost.** The cost has moved from typing to reviewing, testing, deciding what to build, and maintaining quality over time. Treat every line of agent-generated code with the scrutiny you would give a PR from a competent but new contributor — one who doesn't yet know your taste, your codebase's history, or what you actually meant.

**Tests prove what they test, not that your code is correct.** This is where I'd push back on Simon slightly. When an agent writes the implementation and the tests from the same prompt, the tests can happily confirm the agent's misunderstanding of your intent. 100% line coverage from AI-written tests is not the same epistemic object as 100% coverage from human-written tests. For critical paths, you should still occasionally read the actual implementation, not just trust the green checkmark. Tests are a necessary safety net, not a sufficient proof of correctness.

---

## Retrofit plan: bootstrapping an existing project

Your project wasn't built with this workflow in mind. Before you do real agentic engineering on it, invest a short amount of time making it *legible* to agents. Think of this as sharpening the saw — skipping it will cost you more time later than doing it costs now.

**Step 1: Get the agent to describe your project to you.**
Start a session and say:

> Read the repository and give me a summary of what this project does, how it's organized, and what the main components are. Don't change anything yet.

Read the summary. If it's wrong or confused in specific places, note those — those are the areas the agent will struggle with until you clarify them.

**Step 2: Inventory the tests.**
Say `First run the tests`. Note the count, the pass rate, and which parts of the codebase have no coverage. If you have few or no tests, that's your next priority — not new features.

**Step 3: Backfill tests on the critical path.**
Pick the three or four parts of the codebase that would hurt the most if they broke silently. Have the agent write *characterization tests* for them — tests that pin down the current behavior as it is today, whether or not that behavior is "correct." These become your safety net for everything that follows. Prompt example:

> Write characterization tests for `<module>`. Don't change the code. The goal is to capture the current behavior so we can safely refactor it later. Focus on inputs and outputs; don't test internal implementation details.

Do this *before* asking the agent to refactor or add features to that code.

**Step 4: Have the agent draft an `ARCHITECTURE.md`.**
Then *you* edit it. This gives future sessions (and future you) a map. Keep it to one page. Include: what the project does, the main modules and their responsibilities, any important constraints or conventions, and things that would surprise a newcomer.

**Step 5: Create the `.agent/` directory and seed it.**
Make the subdirectories listed in `AGENTS.md`. Seed `.agent/decisions/` with two or three design decisions you already know about — the kind of thing you would want to explain to a new contributor on day one. For example: "We use library X instead of Y because…" or "This module deliberately avoids pattern Z because…"

**Step 6: Drop `AGENTS.md` into the repo root.**
If you use Claude Code, also symlink or copy it to `CLAUDE.md`. If you use Copilot, copy it to `.github/copilot-instructions.md`.

Only after all six steps should you start using the agent for new features or substantial refactors. This whole sequence should take a few hours to a day for a typical small-to-medium project, not weeks.

---

## The short prompts worth memorizing

Simon's guide leans on the fact that modern models recognize certain phrases as dense shorthand for whole workflows. Learn these; they are high-leverage per keystroke.

- **`First run the tests.`** Use at the start of every session on an existing codebase. Forces the agent to orient itself and primes it for a testing mindset.
- **`Use red/green TDD.`** Use for any new function or non-trivial change. Forces write-test-first, watch-it-fail, implement, watch-it-pass.
- **`Reproduce this bug with a failing test first, then fix it.`** Use for bug reports. Prevents silent regressions.
- **`Explore two or three approaches before we commit to one.`** Use when you're not sure of the right design. Cheap now; used to be expensive.
- **`Propose a plan before touching any code.`** Use for anything non-trivial. Much cheaper to correct a wrong plan than a wrong implementation.
- **`Summarize what you changed and why.`** Use at the end of a session before reviewing. Good catch for scope creep.

---

## Your workflow loop

For each task, roughly:

1. **State the goal clearly** — what you want, what "done" looks like, any constraints the agent wouldn't otherwise know.
2. **Ask for a plan first.** Read it. Push back if the plan is wrong. Correcting the plan is an order of magnitude cheaper than correcting the code.
3. **Let the agent execute**, using TDD where appropriate.
4. **Review the diff.** Actually read it. For critical code, read it carefully. For scaffolding and tests, skim. (See "What to read" below.)
5. **Run the tests yourself**, not just trusting the agent's claim that they pass. This takes ten seconds and catches an embarrassing number of false victories.
6. **Try the feature manually** if it's user-facing. Agents can write passing tests for broken UX.
7. **Write the retrospective** (the agent can draft it; you edit). File it in `.agent/retros/`.
8. **Update `AGENTS.md`** if the session revealed a missing instruction or a recurring correction.

Step 8 is the compound engineering loop. It is where your setup gets better over time. Don't skip it. A `AGENTS.md` that never changes is a sign you're not learning from your sessions.

---

## Signs the agent has gone off the rails

Stop the session and reset if you see any of these:

- It's editing files far from the original scope for reasons it can't clearly justify.
- It's adding configuration flags, abstraction layers, or "future-proofing" you didn't ask for.
- It's disabling tests, catching exceptions without handling them, or sprinkling `# TODO` comments instead of doing the work.
- It claims a change works but didn't actually run it.
- It's confidently giving you the same wrong answer after you corrected it once.
- Its explanations are getting vaguer instead of sharper as the conversation continues.
- It's apologizing a lot. Repeated apologies in an agent session are usually a sign of context rot rather than a sign of improvement.

When this happens: revert, reset the context (start a new session), and try again with a tighter, more specific prompt. Do **not** try to salvage a session that has gone sideways by piling on more corrections. That path almost never converges.

---

## What to read carefully, and what to trust

A rough hierarchy of review effort for agent-generated code:

| Category | Review effort |
|---|---|
| Security-sensitive code (auth, secrets, input validation, file/network I/O boundaries) | Read every line. Do not outsource this. |
| Core business logic (the thing your project is actually *for*) | Read carefully. Run it manually, not just via tests. |
| Data model changes (schemas, migrations) | Read carefully. These are hard to roll back. |
| Tests | Skim for shape. Check that at least one test would fail if the implementation were wrong. Watch specifically for tests that assert against literal outputs the agent just generated — those prove nothing. |
| Scaffolding, glue code, boilerplate | Trust more, verify via the test suite. |
| Formatting, renaming, mechanical refactors | Trust, verify via the test suite. |

Calibrate this to your project's specific risks over time.

---

## On skill atrophy

If you find yourself unable to explain what a piece of your own code does, that is a warning sign, not a feature. The goal of this workflow is not to stop thinking about code — it's to stop *typing* code so you have more time to think about the parts that matter.

A reasonable self-check: once a week, pick a file the agent wrote recently and read it as if you were going to maintain it by hand with no AI. If you can't, slow down and have the agent walk you through it line by line. This is cheap and keeps your understanding of your own project from drifting away from the code.

The machinist analogy is apt but not a guarantee — CNC machinists adapted fine because the craft had decades to build new apprenticeship structures. We don't have decades. You are, to some extent, your own apprentice. Act accordingly.

---

## When to stop prompting and start thinking

Some situations deserve a notebook and a walk rather than another agent session:

- Anything where you don't yet know what you want. The agent will happily build the wrong thing very quickly.
- Anything where the failure mode is hard to reverse — data loss, breaking published APIs, crossing security boundaries.
- Anything where the agent has tried and failed twice. A third attempt usually won't work; the problem is that the spec is unclear in your own head.
- Architectural decisions that will shape the project for months.

The agent is a powerful tool for executing on clear intent. It is not a substitute for *having* clear intent.

---

## Things Simon is right about, and things to hold lightly

**Right, in my view:**
- Code is cheap; prototyping is nearly free.
- Refactoring should become habitual, not a quarterly event.
- Experience amplifies rather than depreciates with these tools.
- TDD fits agents unusually well — the feedback loop is exactly the shape agents thrive in.
- The "hoard" pattern (keeping snippets and research across projects) is genuinely valuable.
- The compound-engineering retro loop is the single best practice for getting better over time.

**Hold lightly:**
- The idea that you can stop reading code entirely. For critical code, no.
- The implicit claim that comprehensive tests prove correctness. They prove the code passes the tests.
- The "dark factory" framing. Factories don't tend to make beautiful things, and software is still partly a craft.
- The optimism about mid-career engineers "figuring it out." Some will; the pattern is recoverable but not automatic.

Your existing taste and judgment are not obsolete. They are exactly what makes this workflow produce good results instead of fast slop. Keep them sharp.
