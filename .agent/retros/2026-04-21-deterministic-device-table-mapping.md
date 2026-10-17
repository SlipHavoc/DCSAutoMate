# Retro: Deterministic device→command-table mapping + Mi-24P unification

**Date:** 2026-04-21
**Branch:** `canonical-alias-naming` (2 commits added this session)
**Outcome:** Shipped. All 4 aircraft live-validated with zero regressions; strictly better on 3 of 4.

## Goal

Replace the brittle `inferDeviceTableMapByEvidence` + `nameScore` heuristic
pipeline (which was failing silently — e.g. AH-64D KU_CPG getting mapped to
the wrong command table, producing 123 wrongly-named canonicals) with a
deterministic signal captured during extraction. Then close out the
long-running canonical-alias-naming refactor by unifying the last
module-specific generator (`tools/generate_Mi24P.py`) into the shared
generator.

## What worked

- **Lupa `__index` metatable on every `*_commands` global** captured the
  exact table alias used at each `clickabledata.lua` call site. No regex,
  no source parsing, no guessing. Signal is deterministic and complete for
  every device referenced in clickabledata.
- **One shared extractor helper (`tools/extractUtils.py`)** — wiring all 4
  per-module extractors to emit `deviceTableMap` was ~3 lines per extractor.
- **Reverting `nameScore` to the original single-string LCP form** (Phase 4)
  was safe once the deterministic mapping carried the weight — confirmed by
  regenerating all 4 canonicals byte-identical to installed.
- **"Simplify first, then unify"** for the Mi-24P generator unification:
  instead of porting Mi-24P-specific quirks into the shared generator, I
  diffed Mi-24P-dedicated output vs shared output and found the shared
  generator was actually *doing more* than needed (inventing positionMaps
  for same-cmd ±v switches that work fine as plain discretes). The fix was
  to remove case (b) of `isPositionMapElement` and the `isRelative` short-
  circuit in `classifyType`. Net deletion of code.
- **Live validation at each step** kept confidence high: Mi-24P 1002/30/162
  unchanged, FA-18C +2/−2, AV-8B +2/0, AH-64D +4/−4.
- **`remapAliasKeys.py`** — tiny, reusable utility that rewrites alias-file
  keys by `(deviceId, commandId)` fingerprint. Made the 123-rename AH-64D
  install trivial and will be the standard tool for future canonical
  renames.

## What didn't (or needed a second try)

- **AH-64D 0/91 deterministic coverage bug.** First full extraction run
  produced an empty `deviceTableMap`. Root cause: `VR_config.lua` re-executes
  `dofile('command_defs.lua')` *after* the metatables were installed, and
  because the `*_commands` globals already existed, the reassignment bypassed
  `__newindex` (Lua writes to existing raw keys don't invoke `__newindex`).
  Plain-table reassignment clobbered the proxies.
  - **Fix:** wrap `dofile` itself to re-sweep `_G` for unwrapped
    `*_commands` tables after each invocation and re-install proxies. Ugly
    but correct. Captured in the commit message and `extractUtils.py`.
- **Git Bash MINGW64 heredoc tab-completion** corrupted multi-line Lua
  embedded in `python << 'PY'` blocks. Switched to writing probe scripts to
  files and running them. Already noted in previous retros but re-surfaced
  here.
- **One value-diff during Mi-24P shared-vs-dedicated verification**
  (`CPT_MECH.Command_CPT_MECH_PILOT_MODE_WIPER`) initially looked like a
  regression — turned out it was a canonical-collision last-write-wins
  interaction where the OFF and RESET sub-elements legitimately share the
  same canonical. Confirmed dedicated generator produced the same output;
  not a regression.

## Instruction update candidates

None this session. Current `AGENTS.md` + `.agent/decisions/` machinery
worked well: I consulted `canonical-alias-naming.md` and the session plan
memory, live-validated at each step, wrote no unnecessary code.

One observation worth watching for future sessions: **when an extraction
pipeline relies on Lua metatables, always check whether the target script
re-`dofile`s its dependencies** — that was the AH-64D trap and I'd hit it
again without the wrapping-`dofile`-to-re-sweep pattern now baked into
`extractUtils.py`.
