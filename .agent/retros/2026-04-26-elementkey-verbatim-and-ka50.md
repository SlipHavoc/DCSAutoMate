# Retro: Ka-50 cold-start conversion + elementKey-verbatim refactor

**Date:** 2026-04-26
**Branch:** eliminate-dcs-bios

## Goal

(1) Migrate `DCSAutoMateScripts/Ka-50 Blackshark II.py` from DCS BIOS SCREAMING_SNAKE control names to the new canonical mapping, including all extractor work needed to land a clean Ka-50 control mapping.  (2) During that work, eliminate the dash-to-underscore substitution in canonical command names so canonical names preserve the clickabledata element key verbatim — restoring grep-based traceability between native extraction, control mapping, BIOS name map, and DCSAutoMate scripts.

## What worked

- **Two patterns, one fix per pattern, both keyed off the calling site, not the returned element.**  The Ka-50 surfaced two clickabledata patterns the structural classifier could not resolve from the element shape alone: (a) `animated_guard_switch` helpers wrapping a continuous range to make a 2-position cover, which would otherwise emit a 101-position pseudo-discrete; (b) post-construction `.action = {a, b}` overrides on multi-position rotaries.  Both required the *generator* to know something about how the element was *built*, not just what it returned.  Resolved (a) with a Lua `_G.__newindex` hook that wraps named helper functions to tag their return tables with `_helper = '<name>'`, then a `detectBinaryToggle()` branch in the generator keyed off that tag.  See [.agent/research/clickabledata-helper-and-action-override-patterns.md](.agent/research/clickabledata-helper-and-action-override-patterns.md).
- **Snapshot-then-regenerate-then-diff.**  Before changing the substitution, snapshotted all four affected control mappings to `$TEMP/oldMappings/`, regenerated, then built a `{oldCanonical → newCanonical}` delta from the snapshots by joining on `(deviceId, commandId, arg)` for cmd-backed controls and on `(firstPositionMapDevId, firstPositionMapCmdId, arg)` for positionMap-only controls.  Fed the delta to `tools/applyNameMap.py` to rewrite the affected scripts.  Result: 79 names → 194 occurrences in Ka-50 BSII, 159 names → 283 occurrences in Mi-8MTV2, both verified (`717 passed / 32 skipped`, `py_compile` clean, all script refs resolve in their regenerated mappings).
- **Cross-module impact analysis up-front saved a regen pass.**  For FA-18C, AV8BNA, AH-64D the substitution branch in `makeCanonicalName()` (gated on `tableName == 'device_commands'`) was confirmed to never fire — none of those modules have any device mapped to `device_commands` in their `deviceTableMap`.  AH-64D *does* have ~20 dashed elementKeys (`pnt_492-2` etc.), but they live on devices using per-system command tables (`tedac_commands`, `eufd_commands`).  Skipped regenerating those three mappings; verified zero diff would be produced.
- **Ka-50 BIOS name map gained positionMap-aware indexing.**  Ka-50 has 11 multi-position discretes whose top-level `deviceId`/`commandId` are `null` and whose per-position `(dev, cmd, value)` triples live inside `positionMap[]`.  The Mi-8 builder only indexed top-level fields and would have missed all 11.  `tools/buildBiosNameMap_Ka50.py::buildIndexes()` now indexes every `positionMap[]` entry's `(dev, cmd, arg)` (with a dedupe pass).  Should be backported to other builders if any new module needs one.
- **Helper-tagger fits cleanly under the existing `installCmdAccessLogger` hook.**  The `_G.__newindex` interposition reads any pre-existing `__newindex` and chains to it instead of replacing it.  No risk of breaking unrelated extraction tooling.

## What didn't

- **Bash heredocs (`python << 'EOF'`) with tabs trigger interactive completion** (`Display all 46 possibilities? (y or n)`) that hangs the terminal.  Hit this twice this session even after writing the lesson into user memory; the trigger is the leading tab in Python code, which bash interprets as a tab-completion request.  **Fix:** always write a temp `tools/_<thing>.py` script file, run it, delete it.  Reinforced the existing memory note.
- **`/tmp/oldMappings/` ↔ Windows-Python path mismatch.**  Bash's `/tmp/` and Windows Python's `os.environ['TEMP']` resolve to the same physical directory under MSYS, but Windows Python doesn't translate the literal string `/tmp/oldMappings/Ka-50.json` into a path it can open.  **Fix:** `os.path.join(os.environ.get('TEMP', '/tmp'), 'oldMappings', '<file>')` — works under both shells.
- **Initial Mi-24P regeneration emitted two `Canonical collision` warnings** that did not appear pre-refactor.  Re-ran cleanly later; could not reproduce.  Likely a transient verbosity artifact from a different generator run.  Mi-24P final mapping has 704 controls, no collisions.  Worth keeping the dedup checks suspicious for future surprises but not investigating further now.
- **No automated way to validate canonical-mapping changes against a live cockpit short of `validateControlMapping.py` against a running DCS.**  Static `pytest` and `py_compile` tell you the script *parses*, not that the renames preserve behavior.  Live-test in DCS is the only ground truth.  User confirmed Ka-50 cold-start and Mi-8MTV2 cold-start both work post-rename.

## Instruction update candidates

- **User memory `tooling.md`** already has the heredoc note — confirmed the rule on a third occurrence this session.  No change needed.
- **`.agent/research/dcs-native-control-types.md`** updated with a forward-pointer to the new helper-and-action-override notes.
- **`.agent/research/module-conversion-pipeline.md`** gained a Ka-50 entry under module-specific quirks and was added to the conversion-targets list.
- **`.agent/research/clickabledata-helper-and-action-override-patterns.md`** new — covers both patterns surfaced by Ka-50, with a generic recipe for tagging additional helpers in the future.

## Future work

- BIOS name maps for FA-18C / AV8BNA / AH-64D / Mi-24P were not regenerated this branch (mappings did not change for those modules).  If any of those modules' canonicals are regenerated for unrelated reasons, regenerate the BIOS name map alongside.
- BSIII (`Ka-50_3` install dir, also `Module:new("Ka-50", 0x1800, { "Ka-50", "Ka-50_3" })` in BIOS) was not converted.  Same BIOS module so the BIOS name map reuses cleanly, but the native extraction would need its own pass — different cockpit, different clickabledata.
- The post-construction `.action = {a, b}` override pattern (Pattern B in the helper-and-action-override doc) was identified during Ka-50 work but only partially handled.  Specific module(s) that exhibit it should be re-extracted if the generator changes its handling.
