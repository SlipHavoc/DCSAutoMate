# Validation Notes — A-4E-C Skyhawk

Notes from running [tools/validation-scripts/validateControlMapping.py](tools/validation-scripts/validateControlMapping.py) against a running DCS instance with the A-4E-C module active.

## Summary

- **Total tested:** 355
- **Pass:** 339
- **Fail:** 2
- **Skip:** 14
- **Error:** 0
- **Total in mapping:** 515

Exceptional results for a free community mod! 339 out of 341 active cockpit controls behave exactly as predicted by our archetype generators.

---

## Known Failures and Discrepancies

### 1. `devNone.COMPASS_set_heading`
- **Symptom:** Command is sent but cockpit display arg remains at `0.0`.
- **Reason:** Expected and known/acknowledged. The `COMPASS` device is not implemented in [A-4E-C/Cockpit/Scripts/devices.lua](A-4E-C/Cockpit/Scripts/devices.lua) but is referenced as draft in clickabledata. It resolves to a `None` device and does not have backend logic.

### 2. `TACAN.PNT_903` (TACAN Volume)
- **Symptom:** Expected arg range `[-1.0, 1.0]`, but the physical cockpit model limits reads of the arg to a bottom range of `[-0.5, 1.0]`.
- **Reason:** Minor discrepancy between the `clickabledata.lua` definition (`{-1.0, 1.0}`) and the 3D model’s actual limits (`[-0.5, 1.0]`). The control is still perfectly functional, it just doesn't animate mathematically beyond `-0.5`.

---

## Acknowledged Skips

- `AVIONICS.PNT_25` (Alternate Ejection Handle): Explicitly bypassed via `--skip` to prevent ejecting the pilot from the cockpit mid-validation.
- Pure encoders (arg=-1) (13 controls): These lack absolute physical state args in the cockpit and cannot be tested via absolute readback.
