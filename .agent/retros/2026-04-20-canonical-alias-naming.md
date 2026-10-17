# Session Retrospective — Canonical Control Names + Alias Files

**Date:** 2026-04-20
**Branch:** `canonical-alias-naming` (off `eliminate-dcs-bios`)

## Goal

Replace the brittle name-synthesis pipeline (camelCase conversion, suffix
stripping, dedup, per-module `CONTROL_NAME_OVERRIDES`) with canonical
DCS-Lua-verbatim keys (`<deviceName>.<cmdName>`) plus per-module alias JSON
files that scripts can continue addressing by short human-friendly names.
Migrate all four supported modules and validate each against a running DCS.

## What Worked

- **Canonical-name choice was the right cut.**  Round-tripping to the Lua source
  turned out to be the primary win — grepping `command_defs.lua` for a short
  command name now actually finds things.  The old camelCase pipeline had
  disguised that correspondence.

- **Pilot-on-one-module, then generalize.**  Mi-24P was done end-to-end (generator
  → migrator → resolver → live validation) *before* touching FA-18C / AV-8B /
  AH-64D.  This meant the schema was stable before it had to handle three more
  modules' quirks, and the shared generator inherited a proven design.

- **Live validator as the regression gate.**  Having `validateControlMapping.py`
  produce JSON output meant regression analysis was a script, not a spot-check.
  For three of the four modules we had no saved baseline but could still prove
  zero regressions by matching `(deviceId, commandId)` + `arg` tuples from the
  `.old.json.bak` through the alias file forward to the new canonical and
  confirming every new failure was already failing under the old mapping.

- **Red/green gate per module.**  Each swap was: regenerate → migrate → pytest
  (689/32) → live validate → compare → proceed.  No module went live without the
  previous one fully green.

- **Last-write-wins for canonical collisions.**  The alternative (forcing
  canonicals to be unique by appending a tag) would have reintroduced the
  round-tripping problem.  In practice collisions only occurred on intentional
  aliasing like the Mi-24P CPT_MECH wiper switches.

- **Shared generator collapsed 3 per-module scripts into 1.**  `generate_FA18C.py`,
  `generate_AV8BNA.py`, and `generate_AH64D.py` produced byte-identical output
  to the shared generator post-canonicalization and were deleted.  This was
  possible only because we stopped synthesizing names.

## What Didn't Work

- **Mi-24P generator did not unify into the shared one (yet).**  The shared
  generator produces 103 `cmd_<id>` fallbacks and uses `positionMap` form where
  the Mi-24P-specific generator produces named commands and `argLim`/`step`
  form.  This is a follow-up task — logged in
  `todos/canonical-alias-naming.md`.

- **`_unmatched` counts were not uniformly informative.**  Mi-24P had 482
  unmatched old controls (mostly retired `_ext`/`_iter`/`_axis` siblings the
  old suffix-stripping pipeline was collapsing); FA-18C had 2 (actually-retired
  controls); AV-8B and AH-64D had 0.  Distinguishing "expected retirement" from
  "genuine loss" required case-by-case analysis.  A future extraction could
  flag retired siblings in the extraction JSON itself.

- **Windows `create_file` append behavior cost time early on.**  On VS Code for
  Windows, calling `create_file` on an existing (or recently-deleted) path
  appends rather than overwrites.  Workaround: truncate via terminal
  (`: > path`) then use `replace_string_in_file` with `oldString=""`.  Cost ~3
  confused cycles before diagnosing.

## Instruction Update Candidates

Proposed addition to `AGENTS.md` under a new "Tooling gotchas" section:

> **`create_file` append behavior on Windows.**  On Windows / VS Code,
> `create_file` can behave as append rather than overwrite when the path has
> recently existed.  To force a clean write, truncate the file first
> (`: > path/to/file` in bash, or `Out-File -Force` in PowerShell) and then
> write content via `replace_string_in_file` with `oldString=""`.  Do not
> assume `rm` followed by `create_file` gives you a fresh file.

Proposed addition to the "Do not" list:

> - **Do not synthesize identifiers through case conversion, suffix stripping,
>   or deduplication when the source already provides stable names.**  Prefer
>   verbatim source keys + a separate alias file.  The cost of a clever
>   transform compounds every time a new module or edge case surfaces.
