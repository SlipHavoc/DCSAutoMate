# Mi-24P Hind — Validation Notes

Module: `Mi-24P`
Tested: 2026-04-20, hot start, active pause (baseline); re-validated
2026-04-20 after canonical-alias-naming refactor; unchanged by 2026-04-21
deterministic-device-table-mapping Phase 5 (positionMap-collapse changes
did not affect any Mi-24P controls).
Re-validated 2026-05-02 after `eliminate-dcs-bios` branch sibling-control
elimination (424 inferred `_ITER`/`_EXT`/`_AXIS` siblings removed and JSON
regenerated). Default delay: 0.08s — 1194 controls total.

## Summary

- **Post-sibling-elimination (current)**: Pass 1006 | Fail 16 | Skip 172 | Error 0
  (1 of the 16 failures is a false positive — `ASO_2V.ASO_2V_Set_I_II_III` passes
  when re-run alone; the full-run failure was due to the switch already being in
  position 1 at start. True distinct failure count: **15**)
- **Post-refactor (prior)**: Pass 1002 | Fail 30 | Skip 162 | Error 0
- **Pre-refactor baseline** (captured in repo-root `baseline.json`, camelCase names):
  Pass 995 | Fail 42 | Skip 163
- Net change from sibling elimination: +4 pass / **−14 fail** / +10 skip (strictly better).
  The 14 fewer failures are the former "relative knob no-effect" controls
  (throttle iter clicks, counter wheels, Jadro-1I freq selectors, KM-2
  compass knob, nav-computer trims) — these were inferred `_ITER` siblings
  that no longer exist in the JSON.
- Still flaky: `I9K113.Command_NABL` fails intermittently; passes on retry.

## Relative knobs — resolved by sibling elimination (14 controls, previously failing)

These were all inferred `_ITER` sibling controls generated from `TUMB` elements
that the validation script's increment test couldn't move detectably at 80ms delay.
After the `eliminate-dcs-bios` branch removed all `_ITER` synthesis, these controls
no longer exist in the JSON and are no longer tested:

- `controlLeftThrottleClick`, `controlRightThrottleClick` — throttle iter clicks
- `counterAdjustment1`..`5` — bombing computer counter wheels
- `km2SetMagneticDeclination` — KM-2 compass declination knob
- `freq100hz`, `freq1khz`, `freq10khz`, `freq100khz`, `freq1mhz` — Jadro-1I
  frequency selectors
- `mechClockLeftLeverArg58`, `mechClockLeftLeverArg688` — mech clock left lever

**2 relative knobs still present and failing** (these were not inferred siblings —
they are standalone canonical controls with large enough argLim to be tested but
the increment doesn't register at 80ms):

- `BAROALT_P.CMD_ADJUST_PRESSURE` — pilot barometric setting knob
- `MAP_DISPLAY.VertAdj` — navigation computer vertical trim knob (operator-side)

These work when scripts send multiple increments in sequence (proven by operational
Mi-24P scripts). Not mapping errors.

## Position-map miscalibrations (3 controls)

- `ASP_17V.Azimuth_Delta` — ASP sight azimuth delta knob. Expected [0.0, 1.0]
  but actual arg range clusters around 0.43–0.55. The knob rotates but the arg
  only moves through a narrow band; may be a RAZBAM-style internal clamp,
  or the argLim reported by the Lua doesn't match the physical arg behavior.
- `ASP_17V.Elevation_Delta` — ASP sight elevation delta knob. Same pattern —
  arg stays in a compressed sub-range [0.04, 0.81].
- `ASP_17V.Reflector_Move` — ASP-17V sight reflector movement. Arg clamped
  to range [0.50, 0.70] vs expected [0.0, 1.0].

Note: `PKV.Reflector_Move` also fails (all positions return 0.0) — see
*Multi-command rotary* below.

Decision: cockpit research needed. Not blocking.

## Spring-loaded / momentary switches (4 controls)

- `TIMER.CMD_Timer_Left_Rot`, `TIMER.CMD_Timer_Right_Rot` — mech clock timer
  rotate. Values return to 0 immediately after the test — these are momentary
  winding actions, not settable positions.
- `CLOCK_P.CLOCK-RIGHT-PTR_arg60`, `CLOCK_O.CLOCK-RIGHT-OP-PTR_arg694` — mech
  clock right lever. Negative-half of the argLim (wind backwards) doesn't
  register; only the positive half responds. May be a one-way ratchet-style
  control.

Decision: expected behavior for momentary controls. Not mapping errors.

## Delta-only buttons treated as toggles (5 controls)

These all show `pos 1: expected 1.0000, got 0.0000` or similar.  They are
buttons whose cmd is delta-only (sends a relative impulse) but whose Lua
`argLim=[0.0, 1.0]` hides the fact from the extractor — the extractor can't
distinguish them from ordinary 2-position toggles:

- `CPT_MECH.Command_CPT_MECH_Gear_Pilot` — gear lever detent (pos 1: expected 1.0, got 0.0)
- `CPT_MECH.Command_CPT_MECH_ParkingBrake` — parking brake handle (arg stuck at 0.0)
- `HYDRO_SYS_INTERFACE.Hydro_Damper_P` — pedal damper (pos 1: expected 1.0, got 0.0)

Note: `bombsArg700`, `mainArg217`, `mainArg219` no longer appear in failures —
possibly removed as inferred siblings or now passing.

These are known-fail pending a runtime probe or manual override, as
documented in the `isPositionMapElement` docstring in
`tools/generateControlMapping.py` (case (b) was removed because the
symmetric-argLim-around-0 heuristic that used to catch some of these
caused more harm than good on other modules — see ADR
`.agent/decisions/canonical-alias-naming.md`).

## Multi-command rotary not tested (1 control)

- `PKV.Reflector_Move` — PKI/PKV reflector movement. All positions return
  0.0000. The control is likely a 2-position toggle (cmd 3006 Lock/Unlock)
  whose arg doesn't reflect position state; the physical reflector arm may
  not have a readable arg in the expected range. See also
  `ASP_17V.Reflector_Move` in *Position-map miscalibrations* above.

## Other known quirks (1 control)

- `RADAR_ALTIMETER.ROTARY` — RV-5 radar altimeter test/adjust. Positions
  mis-reported; actual range [0.0, 0.75] vs expected [0.0, 1.0]. Needs
  cockpit investigation.

Note: `ASO_2V.ASO_2V_Set_I_II_III` showed `pos 0: expected 0.0000, got 0.1000`
in the full run because the switch was already in position 1 when testing began.
Re-running the control alone passes cleanly (4 positions OK). Not a mapping bug.

Note: `wheelBrakesHandle` (wheel brake lever reading 0.7 at rest) no longer
appears in failures — may now be passing or removed as a sibling.

## Indication fields — state-dependent (172 skips, 58 pass, 0 fail)

172 indication fields skipped because the field is declared in the
extraction but not currently emitted by `list_indication()`. Mostly
ASP-17V sight-page elements, PrPNK nav-display fields, and SAU autopilot
holder graphics that only appear in specific cockpit modes. 58 fields that
were visible at validation time passed. These are not mapping errors — just
state-dependent visibility, same pattern as FA-18C IFEI and AV8BNA ODU/UVHF
fields. Skip count increased from 162 → 172 compared to prior run, consistent
with 10 additional indication controls added during regeneration.

## Notes on canonical naming for Mi-24P

The canonical-alias refactor caught **16 genuine cmd→name resolution bugs**
that the old heuristic generator was silently papering over:
- `CLOCK_O.cmd_3002` → `CLOCK_O.Button_2`
- `CLOCK_O.cmd_3003` → `CLOCK_O.Button_3`
- `PKV.cmd_3001` → `PKV.Reflector_Move`
- `PKV.cmd_3004` → `PKV.Brightness`
- `PKV.cmd_3006` → `PKV.Lock_Unlock`
- `VMS.cmd_3001/2/3` → `VMS.CMD_RI_Mi24_Off/Check/Repeat`
- plus CLOCK_P and PKP72M_INTERFACE renames.

These were all caused by the old heuristic getting the wrong device→table
binding and falling through to `cmd_<id>` fallback. After the deterministic
mapping (via lupa `__index` metatables) was added in Phase 5, all 16
canonicals resolve to their real Lua names.
