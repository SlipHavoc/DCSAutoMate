# Retro: AJS37 Native Migration

**Date:** 2026-06-07
**Branch:** map-scripts-arch

## Goal

Migrate the AJS37 Viggen from DCS BIOS format to the native canonical-names
format: extract native controls from the Lua files, generate and validate a
controlMapping, then rewrite `AJS37_dcsbios.py` to `AJS37.py`.

## What worked

- Extraction, mapping, and script rewrite all went smoothly in a single session.
- The `simpleDiscrete` + `continuousAxis` archetype coverage was complete — no
  new archetypes needed.
- The script was small and straightforward (20 control names, no dynamic
  construction, no imports to remove).
- Validation categorization was clean; all 42 failures were explainable.
- `'TOGGLE'` on the parking brake was the only value question, and the correct
  native value (`0` = released) was confirmed immediately by the user.

## What didn't work

- **Zero elements on first extraction run.** AJS37's `clickabledata.lua` resets
  `elements = {}` twice. The second reset bypasses the `installCmdAccessLogger`
  proxy's `__newindex` tracker, so `uninstallCmdAccessLogger` was restoring the
  first (empty) table. Fix: call `extractElements(lua)` *before*
  `uninstallCmdAccessLogger(lua)`.
- **0/41 device→table mappings.** AJS37 uses hardcoded numeric command IDs
  throughout `clickabledata.lua` (e.g. `3406`, `3718`) rather than symbolic
  names from `device_commands`. The access logger never sees `device_commands`
  table accesses, so `deriveDeviceTableMap` produces nothing. The resulting
  canonical names use the `cmd_NNNN` fallback pattern for most controls. This
  is expected and not a bug — the mapping and validation both work correctly.

## Instruction update candidates

- Add to AGENTS.md or the extraction guide: **"If elements count is 0 after
  extraction, check whether `clickabledata.lua` resets `elements = {}` more
  than once. If so, call `extractElements(lua)` before
  `uninstallCmdAccessLogger(lua)` in the extractor."**
- The cover-detection limitation in the validator (only checks canonical name,
  not description) is now documented in the AJS37 validation notes. If this
  affects multiple modules it may be worth a general note in the validator docs.
