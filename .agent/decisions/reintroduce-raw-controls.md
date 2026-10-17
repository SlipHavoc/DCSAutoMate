# ADR: Reintroduce unbound commands as `type: "raw"` controls

**Date:** 2026-05-03
**Branch:** `eliminate-dcs-bios`
**Status:** Accepted
**Supersedes in part:** `eliminate-sibling-controls.md`

## Context

`eliminate-sibling-controls.md` documented the decision to remove synthesis of `_EXT`/`_ITER`/`_AXIS` sibling controls from the generator.  That decision was sound for its stated goals (eliminating broken `_EXT` zero-delta failures, removing dead BIOS commandId entries, shrinking JSON size).

However, the same removal also silently discarded all **AI crew command tables** — specifically:

- **F-4E**: `JESTER_WHEEL` device (ID 78), ~190 commands for Jester and the Crew Chief.  Three were actively used in `DCSAutoMateScripts/F-4E.py` but had no physical clickable element, so they were never emitted by `processElements()`.
- **AH-64D**: `george_commands` table (device 87, PrestonAI), 9 George AI commands.  Only `StickFolding` (cmd 3007) has a physical element; the other 8 were silently dropped.
- **Mi-24P**: helperai device 30, 21 Petrovich commands.  None have physical elements; all were silently dropped.
- **F-14**: similar Jester command table (not yet extracted).

The F-4E scripts were working around this via old-style `'PLT_JESTER_COMMAND_...'` names passed through a legacy path.  After the canonical migration, those names became unresolvable, leaving three `# FIXME` markers in the script.

## Why `type: "raw"` rather than structured types

The core difference between AI crew commands and physical clickable commands is **the absence of a cockpit arg**.  For physical switches we know:
- The arg to read back from DCS.
- The argLim (expected native value range).
- The step or scale factor.

For AI crew commands none of that applies.  The Lua tables simply map a name to a command ID.  The runtime sends a value and DCS routes it to the AI crew module, which decides what to do.  There is no way to statically infer what value to send or what arg to read to confirm the action.

Attempting to infer type/argLim/step for these commands would be guessing.  Instead:

- `processRawCommands()` in `generateControlMapping.py` emits a minimal entry: `{description, type, deviceId, commandId}` — nothing more.
- `DCSDirectManager.sendControl()` short-circuits for `type: "raw"`: the caller-supplied value is sent directly to DCS with no translation.
- `validateControlMapping.py` excludes `type: "raw"` controls entirely (no known values to send, no known arg to read back).
- Script authors supply the correct DCS value themselves.  For AI crew "press" commands this is typically `1`.  For axis or incremental commands the author must experiment.

## Why the sibling commands come along for the ride

`processRawCommands()` emits an entry for every `(deviceId, commandId)` pair in any `commandTable` that has no physical element binding.  This naturally catches:

- Pure AI crew tables (all commands unbound).
- `_ITER`, `_AXIS`, `_EXT` siblings — command IDs that exist in the command tables but never appear in `clickabledata.lua`.

The old objection to siblings was that their structural properties (zero-delta values, stale BIOS commandIds) caused *validation failures* and *generator complexity*.  Both objections are now moot:

- `type: "raw"` entries have no `argLim`/`step`/`positions`; there is nothing to validate structurally.
- The generator emits them in ~30 lines with no per-type logic.
- The validator skips them entirely — no false failures.

Script authors who want to use a `_ITER` or `_AXIS` variant can do so by passing the appropriate value.  Authors who don't want them can ignore them.  The cost of including them is near zero.

## Decision

1. Add `processRawCommands()` to `tools/generateControlMapping.py`.  It emits `type: "raw"` for every command-table entry with no physical element binding.
2. Add raw bypass to `DCSDirectManager.sendControl()`.
3. Exclude `type: "raw"` from `validateControlMapping.py`.
4. Regenerate all modules.
5. Resolve the three `# FIXME` lines in `DCSAutoMateScripts/F-4E.py` using canonical `JESTER_WHEEL.*` names.

## Finding correct values

The `type: "raw"` entries deliberately carry no value guidance.  For script authors who need to find what value to send:

- **AI crew commands**: typically `1` (pulse/press).  Check the Heatblur/other developer documentation or community resources.
- **`_ITER` commands**: DCS usually expects a delta value (e.g. `+1` or `-1`).
- **`_AXIS` commands**: DCS usually expects a float in `[-1.0, 1.0]`.
- **Reference material**: the module's `Input/<variant>/keyboard/default.lua` and `Input/<variant>/joystick/default.lua` files map key/axis actions to `{device, action, value}` triples.  The `value` field is the native DCS value for that action — a direct guide for `type: "raw"` callers.

## Revisit condition

If raw controls accumulate so many entries that JSON files become unwieldy, consider a `--no-raw` flag to `generateControlMapping.py` that suppresses them.  This keeps the default behaviour discoverable without forcing authors to hand-trim the files.
