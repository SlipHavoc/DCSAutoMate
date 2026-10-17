# Retro: radio_wheel modeling + master/slave display-arg capture

**Date:** 2026-04-26
**Branch:** `eliminate-dcs-bios` (2 commits: `0abfd5a`, `841e508`)
**Outcome:** Shipped. Mi-8 and Mi-24 wheel controls now expose visible cockpit position through `displayArgs[0]` and a debug row in DCSControlPanel. Live-verified DIG12 chain in both modules. 704 passed / 32 skipped baseline preserved throughout.

## Goal

Two related problems on `radio_wheel_1`-style cockpit controls (Mi-8 / Mi-24 frequency selectors, channel selectors):

1. The two TUMB sub-elements (CW click and CCW click) shared one (arg, command) and were each emitted as separate ill-formed entries with conflicting argValue signs. Scripts couldn't address them sensibly.
2. The pulse arg readback returned a click counter, not visible cockpit state. Master/slave digit-carry chains (e.g. JADRO DIG12: arg 751 = ones, arg 750 = tens) were invisible to scripts.

## What worked

- **`detectWheel()` in generateControlMapping** — the two-TUMB-with-shared-arg-and-command pattern was easy to detect from the existing extraction data, and emitting one `relative` + `wheel: True` entry per detected pair eliminated the ambiguity. Signed integer click count as the script-convention value matched cockpit reality 1:1 (no synthetic units, no fractional state to keep in sync).
- **Live verification before designing the second phase.** The DIG12 investigation that surfaced the master/slave chain only happened *because* the wheel rework had shipped and the user could click a real cockpit control while watching DCSControlPanel. The displayArgs design was directly informed by reading the actual `slave_animation` Lua spec, not by guessing what fields might exist.
- **`extractSlaveAnimation` via lupa, not regex.** User explicitly redirected mid-implementation: "Remember we want to use lupa whenever possible, not regex." The Lua sandbox already has the element table with `slave_animation` on it as a `_LuaTable`; recursively walking `entry.slave` is ~15 lines and exact. No source-text knowledge needed. Repo precedent in `extractUtils.installCmdAccessLogger` already established the pattern.
- **Side-channel `<ref>#extra:<arg>` payload keys for the WheelCard debug row.** PollWorker emits one synthetic key per non-master arg, and `_onValuesUpdated` routes them through `card.updateExtraArg(arg, value)`. The main payload still routes by ref (no impact on existing card types). Compact and contained.
- **Phase 5 byte-identity check.** After regenerating all 6 modules, `git status` showed only Mi-8MT and Mi-24P JSON files changed. That's the right invariant for a feature that only touches Mi-8/Mi-24 helper output — quick check, high signal.
- **Plan-then-execute for the displayArgs phase.** Asked clarifying questions up front (scalar vs list, primary widget driven by which arg, what to show on the debug row). The user pivoted from "displayArg (int)" to "displayArgs (list)" mid-discussion based on reading the DIG12 cockpit shape. That decision was much cheaper before any code was written.

## What didn't (or needed a second try)

- **Initial mental model conflated two different phenomena.** I started by lumping "F-16C compound rotaries" with "Mi-8 wheels" because both look like multi-element clickable elements. They are not — F-16 compound rotaries are split into siblings during generation (an existing well-tested mechanism); Mi-8 wheels are single logical controls whose pulse arg differs from their display arg. A clarifying question early would have caught this faster than tracing through code paths.
- **Almost reflexively reached for regex** to parse `clickabledata.lua` for the displayArg spec. The user caught this with a one-line redirect. Lesson reinforced for next time: when extending an extractor, default to instrumenting the Lua sandbox before reaching for source-text parsing.
- **`displayArgs` field name initially singular (`displayArg`).** Got refined to plural list during planning when the master/slave chain reality of DIG12 was confirmed. Cheap to fix at design time, would have been annoying in code if locked in.

## Instruction update candidates

Consider adding to `AGENTS.md` under "Things to NOT do":

> **Do not text-parse Lua source to extract data that is already available on the runtime objects.** The `lupa` sandbox already executes `clickabledata.lua` and gives you the resulting tables — walk those directly via `lupa.lua_type()` and field access. Source-text parsing is a last resort for data that genuinely isn't reachable through any runtime structure.

And under "Pattern matching on mixed-era code":

> **When extending an extractor, install the new capture inside the Lua sandbox** (either as a wrapped helper, a metatable hook, or a post-walk of the resulting tables). This matches the established pattern in `installCmdAccessLogger` and keeps the extractor pipeline uniform.

## Snippets worth promoting

- `extractSlaveAnimation` in `tools/extractUtils.py` — clean example of recursively walking a `_LuaTable` chain (`.slave` field) into a flat Python list. Could be `.agent/snippets/lupa-recursive-table-walk.lua` or `.py` if a similar pattern comes up again.

## Followups

- The DCSAutoMate Mi-8 script can now switch from arg-direct frequency setting to `pushSeqCmd(dt, 'setControl', control='Mi-8MT/JADRO_1A.PTR_ADDSECPLT_LVR_DIG12', value=+1)` style. That conversion is the next session's work.
- Validator (`tools/validateControlMapping.py`) currently exits cleanly for Mi-8 wheels. If a future "value changed after sending" check breaks because dispatcher reads displayArg now, the validator should be updated to accept either pulse arg movement OR displayArg movement as evidence of activity.
