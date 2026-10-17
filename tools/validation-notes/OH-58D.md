# OH-58D — Validation Notes

Module: `OH-58D`
Tested: 2026-05-25, cold start (engine off), hot start (engine running), active pause.
Default delay: 0.08s — 332 controls tested (skipped: 4 SCAS).

## Summary

- Pass: 332 | Fail: 0 | Skip: 3744 | Error: 0

All tested controls pass. SCAS controls require engine-running — see below.

## Recommended `--skip` list

```bash
python tools/validation-scripts/validateControlMapping.py --module OH-58D \
  --json-output tools/validation-scripts/validation_OH58D.json \
  --skip "SCAS.HLP_SCASHEADING_ENG_DIS,SCAS.HLP_SCASHEADING_LEFT_RIGHT,SCAS.HLP_SCAS_PITCHROLL_SWITCH,SCAS.HLP_SCAS_YAW_SWITCH" \
  2>&1 | tee tools/validation-scripts/validation_OH58D.log
```

## Known skip reasons

### SCAS engage switches — skip (engine off)

`SCAS.HLP_SCAS_PITCHROLL_SWITCH`, `SCAS.HLP_SCAS_YAW_SWITCH`

**Failure message:** `pos 1: expected 1.0000, got 0.0000`

These toggle switches are locked-out when the engine is not running. They pass
correctly when tested with the engine running. Not a mapping error.

### SCAS heading hold switches — skip (engine off)

`SCAS.HLP_SCASHEADING_ENG_DIS`, `SCAS.HLP_SCASHEADING_LEFT_RIGHT`

Same engine-off lockout as above. Tested and confirmed working with engine running.

## Module name mismatch — expected warning

DCS reports the loaded module as `OH58D` (no hyphen); the control mapping file and
all scripts are named `OH-58D` (with hyphen). The validator warns about this but
continues correctly. No action required.

## HLP_DESIG_BUTTON — fix applied in mapper

`MMS.HLP_DESIG_BUTTON` was originally mapped as `positions=3` by the generic
`twoCommandSpringloaded` handler, which assumed two *different* commands.

**Root cause:** `clickabledata.lua` line 196 uses `springloaded_3_pos_tumb` with
the *same* command (`device_commands.Button_26` = 3026) for both the dec and inc
sub-controls:

```lua
elements["HLP_DESIG_BUTTON"] = springloaded_3_pos_tumb(
    _("Nav/Target Designate Switch"),
    devices.MMS, device_commands.Button_26, device_commands.Button_26,
    arg_int.CoPilot_Cyclic_DESIG_Button) -- 43 arg number
```

The positive direction (+1) is defined in Lua but the MMS device ignores it.
Only the negative direction (Target Designate hat down, arg → −1) works
physically. The fix adds a module-local `springloaded3PosTumb` function in
`map_OH58D.py` that detects the same-command case and produces `positions=2`
with positionMap `[{dec entry}, None]`. The inc direction entry is omitted.

**After initial fix:** `"positions": 2`, positionMap had the −1 entry (position 0)
and a null center (position 1). Passed validation.

**Follow-up fix (DCSControlPanel display):** The positionMap `[{-1.0}, null]` format
has a reverse-translation bug: a trailing `null` with no right anchor is extrapolated
to the same value (−1.0) as position 0, so `bestIndex` is always 0 regardless of the
actual arg. The control was replaced with a standard simpleDiscrete encoding:
`argLim: [-1.0, 0.0]`, `step: 1.0`, `positions: 2` — no `positionMap`. Now:
- Position 0 (sends −1.0) = active/pressed (arg → −1).
- Position 1 (sends  0.0) = center/release (arg → 0, spring-back).
DCSControlPanel's Current display correctly tracks the switch state between 0 and 1.
