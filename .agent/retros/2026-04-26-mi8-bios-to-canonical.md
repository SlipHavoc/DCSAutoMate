# Retro: Mi-8MTV2 BIOS → canonical script migration

**Date:** 2026-04-26
**Branch:** eliminate-dcs-bios
**Commits:** 388837b, e46fa02, 49eb231

## Goal

Convert `DCSAutoMateScripts/Mi-8MTV2.py` from DCS BIOS SCREAMING_SNAKE control names to the new canonical mapping. Then document the work and commit.

## What worked

- **Regex-parse the BIOS Lua + join on (dev, cmd, arg) triple.** The DCS BIOS Mi-8MT.lua source is single-line `Mi_8MT:defineXXX("NAME", dev, cmd, arg, ...)` rows — no need for lupa, simple regex was enough. Joining against `config/controlMappings/Mi-8MT.json` on the `(deviceId, commandId, arg)` triple gave 95.6 % automatic coverage (410 of 429 BIOS defines), with `(dev, cmd)` pair-match recovering 9 more. The 19 remaining unmappable entries turned out to be entirely unused by the script.
- **Reuse `tools/applyNameMap.py` for the actual rename.** Longest-first word-boundary regex replacement is idempotent and safe to re-run.
- **Live-test in DCS before committing.** User verified cold/hot/shutdown sequences identically to the pre-migration script. Confirmed once again that BIOS position indices and canonical position indices resolve to the same cockpit state — five modules in a row now (FA-18C, AH-64D, AV8BNA, Mi-24P, Mi-8MTV2). The pre-inserted "verify position N" TODO comments cost some time to insert and zero changes to resolve. Worth keeping the audit, probably not worth keeping the inline TODOs.

## What didn't

- **bash heredoc with `python << 'EOF'` got mangled by tab-completion** eating leading whitespace, breaking Python indentation. Switched to writing a temp script file (`tools/_insertMi8Todos.py`), running it, then deleting it. **Lesson worth recording in user memory:** avoid heredocs for non-trivial Python in interactive bash; use a temp script file instead.
- **Wrong native-extraction file name.** Tried to read `config/nativeExtractions/Mi-8MT.json` — the file is actually `Mi-8MTV2.json`. The mapping file is `Mi-8MT.json` because that is the DCS-reported module name, but the extraction file uses the install-directory name. Now documented in the new extraction guide and in the pipeline doc's mismatch table.

## Instruction update candidates

Nothing for `AGENTS.md` itself — the pipeline doc and extraction guides are the right home for these notes and they were updated.

One candidate for **user memory** (`/memories/`): a short note that interactive bash heredocs (`python << 'EOF'`) are unreliable in this environment and a temp script file is preferable. Will add unless the user objects.
