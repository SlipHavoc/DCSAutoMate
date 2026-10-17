# Control Mapping Validation Guide

This doc explains how to use [tools/validateControlMapping.py](validateControlMapping.py)
to verify that a module's control mapping JSON actually works against a live
DCS instance, and describes the testing process we've developed.

## What it does

The validator iterates every control in `config/controlMappings/<Module>.json`,
sends commands to DCS via the TCP export protocol, reads back the resulting arg
values, and reports pass/fail/skip/error for each control. It handles the four
control types (`discrete`, `continuous`, `relative`, read-only `arg`/`indication`),
auto-opens guards and covers before testing, and restores each control to its
initial position after testing.

## Prerequisites

1. **DCS running** with a mission loaded. A hot-start aircraft is strongly
   preferred — cold-start aircraft have many controls that won't respond
   (no power, no hydraulics, etc.).  If a test has been run already, it's recommended to respawn a fresh aircraft for a new test.
2. **Active pause enabled** — the simulation runs so controls animate, but the
   aircraft stays in place so you don't fly into the ground mid-test.
3. **DCSAutoMateExport.lua active**, installed in your DCS `Saved Games/Scripts/`
   folder (or equivalent export hook setup). This exposes the TCP server on
   port 7780.
4. **Python venv activated** with the project's requirements installed.

## Basic usage

```bash
# Activate the venv (Git Bash on Windows).
source .venv/Scripts/activate

# Validate an entire module.
python tools/validateControlMapping.py --module AH-64D_BLK_II
python tools/validateControlMapping.py --module FA-18C_hornet
python tools/validateControlMapping.py --module AV8BNA

# Test specific controls only.
python tools/validateControlMapping.py --module AV8BNA --only handleNozzleStoStop,switchFreqMode

# Skip problem controls.
python tools/validateControlMapping.py --module AV8BNA --skip switchAfc,handleFuelShutOff

# Increase delay for slow-animating modules.
python tools/validateControlMapping.py --module AV8BNA --delay 0.15

# Save machine-readable results.
python tools/validateControlMapping.py --module AV8BNA --json-output results.json

# Print every control's result (not just failures).
python tools/validateControlMapping.py --module AV8BNA --verbose
```

## CLI reference

| Flag | Default | Description |
|------|---------|-------------|
| `--module` | *(required)* | Module name, matches the JSON file basename in `config/controlMappings/` |
| `--delay` | `0.08` | Seconds to wait after each command before reading back the arg |
| `--skip` | `''` | Comma-separated control names to skip |
| `--only` | `''` | Comma-separated control names to test exclusively |
| `--verbose` | off | Print per-control pass/skip status, not just failures |
| `--json-output` | *(none)* | Write full results to a JSON file |
| `--no-open-guards` | off | Don't auto-open guards/covers before testing |
| `--host` | `127.0.0.1` | DCS host |
| `--port` | `7780` | DCS TCP port |

Press Ctrl+C to interrupt — the validator will finish the current control,
restore it, close opened guards, and report partial results.

Exit code: `0` if all tests passed, `1` if any failed.

## How each control type is tested

### `discrete`
Steps through every position from 0 to `positions - 1`, computing the expected
native arg value as `argLim[0] + step * position`. After each step, waits for
the arg to stabilize, then compares. Restores the initial position at the end.

### `discrete` with `positionMap` (multi-device controls)
For each non-null entry in the positionMap, sends the command and verifies the
arg changed (doesn't check against a specific value — just that the control
responded). Sends `0.0` to release after each press.

### `continuous`
Sets the control to 5 proportional points (`0.0`, `0.25`, `0.5`, `0.75`, `1.0`)
of `argLim[0]` → `argLim[1]`. Verifies the readback matches within tolerance.
On failure, reports the actual min/max range achieved so you can see whether
the mapping's `argLim` is wrong.

### `relative`
Sends `+0.1`, verifies the arg changed, then sends `-0.1` to restore. Respects
the `sendProtocol` field (`C` for performClickableAction, `S` for SetCommand) —
this was the source of many early failures on the FA-18C and AV8BNA.

### Read-only `arg`
Reads the arg. If `argLim` is defined, verifies the value falls within bounds.

### Read-only `indication`
Queries the indication by ID, checks that `fieldName` is present in the parsed
field dictionary. Failures often indicate state-dependent fields that only
appear in specific cockpit modes — see the per-module validation notes.

## Animation timing: `waitForStable()`

Many animated controls (rotaries, multi-position switches, covers) take longer
than a fixed delay to settle. Instead of bumping `--delay` for the whole run,
the validator uses `waitForStable()`:

1. Wait the base `--delay` (default 80ms).
2. Read the arg.
3. Poll every 50ms for up to 3 seconds, returning as soon as consecutive reads
   match within tolerance (`0.02`).

This makes the validator robust to slow-animating controls (like the Hornet's
8-position `switchFreqMode` or the Harrier's 7-position `switchOpMode`) without
slowing the whole run for the 95% of controls that settle instantly.

## Guard/cover handling

Before testing, the validator finds all controls whose name contains `cover`
or `guard` (case-insensitive) and opens them by setting their arg to `argLim[1]`.
This makes guarded buttons accessible during testing. After the run completes
(or is interrupted), it closes them again.

Use `--no-open-guards` to disable this if a module has false-positive matches
or if you want to test the guards themselves without interference.

## Testing process we've followed

This is the workflow we've settled on after validating the AH-64D, FA-18C,
and AV8BNA:

### 1. Set up a clean test aircraft
- Create a hot-start mission (cold-start cockpits have too many power-off
  controls to be useful baselines).
- Enable active pause right after mission load.
- Confirm the export hook is running: `python tools/testDCSConnection.py` or
  `telnet 127.0.0.1 7780` and type `I\n` — should echo back `I:<Module>`.

### 2. Run a baseline validation
```bash
python tools/validateControlMapping.py --module <Module> --json-output baseline.json
```
Expect some failures on the first run — that's the point. Note the counts and
look at the failure details.

### 3. Categorize failures
Every failure falls into one of these buckets:

- **Mapping errors** — wrong `deviceId`, `commandId`, `arg`, `argLim`, `step`,
  or `positions`. Fix the JSON.
- **Wrong `sendProtocol`** — relative controls that need `C` but default to
  `S`, or vice versa. Common on third-party modules. Add `"sendProtocol": "C"`.
- **State-dependent indications** — indication fields that only appear in
  specific cockpit modes (e.g., Hornet IFEI `txtTimeSetMode` only during clock
  set, Harrier UFC `ufc_numeric_output` only during data entry). Not errors;
  document in the module's validation notes.
- **Spring-loaded switches** — controls that snap back after release. Validator
  reports failure because readback doesn't match the set value. Document; not
  fixable in the mapping.
- **Module quirks** — positions the module developer never wired up (e.g., the
  Harrier STO Stop lever's positions 0.80 and 0.95). Document in validation
  notes.
- **One-shot / conditional controls** — controls that only work after some
  prerequisite action (e.g., Harrier `handleFuelShutOff` needs unlock first,
  `handleGearBattLift` only moves before emergency gear activation). Document;
  may need multi-step sequence support later.

### 4. Fix mapping errors and re-run
For each real mapping error, edit the JSON and re-run with `--only` for just
that control to verify the fix. Then run the full suite again to confirm
nothing regressed.

### 5. Document the rest
Create or update `tools/validation-notes/<Module>.md` with:
- Pass/fail counts and run time.
- Each known-failure category with the specific controls affected.
- Any `sendProtocol` or protocol fixes applied.
- State-dependent indication fields.
- Module quirks worth remembering for future sessions.

See [tools/validation-notes/FA-18C_hornet.md](validation-notes/FA-18C_hornet.md),
[tools/validation-notes/AH-64D_BLK_II.md](validation-notes/AH-64D_BLK_II.md),
and [tools/validation-notes/AV8BNA.md](validation-notes/AV8BNA.md) for examples.

### 6. Commit
Commit the JSON fixes, validation notes, and any validator improvements
together with a message describing what was validated and what was fixed.
Run `pytest` before committing to confirm the 689-test baseline still holds.

## Protocol reference (for debugging)

The TCP export protocol runs on port 7780 and uses newline-terminated commands:

| Send | Purpose | Response |
|------|---------|----------|
| `I\n` | Query module name | `I:<ModuleName>\n` |
| `Q:0:<arg>\n` | Query arg value | `R:0:<arg>:<value>\n` |
| `C:<dev>:<cmd>:<val>\n` | performClickableAction | `OK\n` |
| `S:<dev>:<cmd>:<val>\n` | SetCommand | `OK\n` |
| `T:<id>\n` | Query indication text | `D:<id>:<json-string>\n` |

The distinction between `C:` and `S:` matters for relative controls. Most
first-party ED relative controls use `S:` via a separate ITER command ID; many
third-party modules (FA-18C, AV8BNA) route relative deltas through `C:` on the
same command ID as the discrete position. When in doubt, check the module's
Lua `clickable_defs.lua` or `devices/*.lua` to see how the handler is wired.
