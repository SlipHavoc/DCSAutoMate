# AV8BNA (Harrier) — Validation Notes

Module: `AV8BNA` (RAZBAM AV-8B Night Attack, third-party, 2017-era)
Tested: 2026-04-19, hot start, active pause.
Default delay: 0.08s — 277 controls total.

## Summary

- Pass rate: ~256/277 (92.4%) after animation timing fix
- Run time: ~3 minutes

## Known Failures — Module Quirks

### handleNozzleStoStop (STO Stop Lever)
- Mapping: deviceId 13 (VREST), commandId 3488, arg 488, argLim [0.35, 1.0], step 0.05, positions 14
- Issue: 12 of 14 positions work correctly. Two positions consistently fail:
  - **0.80** → reads back as 1.0
  - **0.95** → reads back as 0.75
- Cause: In the physical cockpit, the STO Stop lever's first click from fully-back
  jumps several notches forward to the 75° mark, then each subsequent click moves
  one notch (5°) at a time. RAZBAM likely never wired up the intermediate positions.
  The Lua defines 14 evenly-spaced positions via `multiposition_switch_limited`, but
  the internal flight model snaps 0.80 and 0.95 to nearby valid stops.
- Evidence:
  - Failures are direction-independent and timing-independent (fully reproducible)
  - DCS-BIOS uses identical approach (`defineTumb`) with no special handling or known issues
  - Floating-point analysis: 0.95 has precision mismatch (`0.35 + 0.05*12 = 0.9500000000000001`), but 0.80 is exact — so FP alone doesn't explain both failures
  - Step-increment probing confirmed C: protocol treats values as absolute, not relative
- Decision: Leave mapping at 14 positions as-is. These are RAZBAM module quirks, not mapping errors.

### switchAfc (AFC Switch)
- Issue: Spring-loaded switch. Moving OFF→ON sticks, then springs back to center.
- Decision: Expected behavior for spring-loaded controls. Not a mapping error.

### mirrors (args 1125, 1126)
- Issue: Rendering toggles for cockpit mirror visibility, not physical controls. No response to any value via protocol.
- Decision: Not actionable — these are visual rendering commands, not clickable cockpit controls.

### handleFuelShutOff (Fuel Shutoff Handle)
- Issue: Requires unlock command before it can be moved. FIXME already exists in AV8BNA.py line 527.
- Decision: Needs multi-step control sequence support. Tracked separately.

### handleGearBattLift (Emergency Gear / Battery Lift Handle)
- Issue: Moves freely on fresh mission start (at 0.0). After emergency gear activation (rotate knob 90° and pull), it sticks. One-shot behavior.
- Decision: Not a mapping issue — reflects real cockpit behavior.

## Indication Fields — State-Dependent

These indication fields are valid but only populated in specific cockpit modes:

- **ODU `_Slc` fields** (oduOption1Slc through oduOption5Slc): Only the currently
  selected option shows its marker.
- **UFC fields** (ufcNumericOutput, ufcRightAlphaPosition): Only appear during
  data entry mode.
- **UVHF fields** (uvhfFreqRight, uvhfFreqScolon, uvhfLeftPosition): Appear in
  different radio operational modes.

## sendProtocol Fixes Applied

Five relative controls needed explicit `"sendProtocol": "C"` to use
`performClickableAction` instead of the default `SetCommand`:
- bingoSet
- knobAltimeter
- knobChanFreq
- knobComm1Chnl
- knobComm2Chnl
