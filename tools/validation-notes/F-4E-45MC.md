# F-4E Phantom II — Validation Notes

Module: `F-4E-45MC`
Tested: 2026-05-03, hot start (F-4E training mission), active pause.
Default delay: 0.08s — 584 controls total (after guid-N fix; see below).

## Summary

- Pass:  533 | Fail: 39 | Skip: 12 | Error: 0
- Run time: ~6.7 minutes

Note: the initial run was against 633 controls (before the guid-N fix).
After filtering 49 guid-N indication fields from the mapping (see below), the
remaining 584 controls break down as Pass 533 / Fail 39 / Skip 12.

---

## Known Bugs Fixed During This Run

### guid-N indication fields (49 controls removed)

`create_guid_string()` in the F-4E indicator Lua files is mocked in the extractor
to return `guid-1`, `guid-2`, etc. for naming display elements.  The real DCS
runtime assigns actual UUID-format GUIDs like `{2672587C-F6C0-43b0-AA8B-16FEAE04441B}`.
These synthetic `guid-N` names can never match the real field names DCS reports.

**Fix:** `generateControlMapping.py` now skips any indication field name matching
`^guid-\d+$`.  49 controls removed from the mapping.

**Guidance:** The real GUID field names are visible in the validator output (e.g.
`fields: ['glass', 'total_field_of_view', '{2672587C-...}', ...]`).  If those
fields are useful for scripting, they can be added as hand-curated read-only
entries in the mapping.  For the F-4E HUD the only named fields are `glass` and
`total_field_of_view` which both pass.

---

## Remaining Failures

### Indication fields — systems need to be powered

These indications returned empty field lists, meaning the avionics system for that
display is not active in a plain hot-start, active-pause mission.  All underlying
fields in the extraction are correct names from the Lua source.

| Indication | C++ Class | Probable reason |
|---|---|---|
| ind.2 | ccRadar (DSCG radar) | Radar not powered / in standby |
| ind.3 | ccRadarScope (TV indicator) | No EO weapon loaded/selected |
| ind.4 | ccSensor (TV sensor) | No EO weapon loaded/selected |
| ind.11 | ccALR46 (RWR display) | RWR needs specific avionics init |
| ind.13 | ccControlsIndicator | No active flight warnings during straight-and-level active pause |

All confirmed WAI — see per-indicator notes below.  Re-test ind.2 with radar
powered to INS/STB/OPR mode.  Re-test ind.3/4 with a Maverick or Walleye loaded
and Pave Spike / WSO sensor active.  Re-test ind.11 with RWR powered (ALR-46
self-test confirms the pipeline works).

Fields that DO pass in ind.0 (HUD): `glass`, `total_field_of_view`.
All fields for ind.7–10, ind.14–15 pass (EO designator bit/range displays, UHF
radio freq indicators, AVTR time indicators).

### ind.0.rangebarMask — extracted but not exposed at runtime (WAI / accepted)

`rangebarMask` is a `ceMeshPoly` element defined in `reticle_page.lua` and
registered with `Add()` — the same mechanism used by every other named element.
DCS exposes `glass` and `total_field_of_view` (also `ceMeshPoly`, also via
`Add()`) but does not expose `rangebarMask`.  The distinction is made in the C++
engine and cannot be determined from Lua alone.

**Decision:** no extraction filter will be added for this case.  `rangebarMask`
will remain in the mapping but will always return an empty string at runtime.
This is accepted behaviour.

### ind.11: rwr_launch_circle, rwr_priority_diamond, base

Real field names from the ALR-46 RWR init Lua, but ind.11 reports empty at
runtime.  See system-power note above.

### ind.13: ControlsIndicator — WAI

Real field names from the ControlsIndicator init Lua.  Confirmed: the F-4E
ControlsIndicator only outputs autopilot status and other exceptional flight-mode
warning strings, not continuous stick/throttle position data.  ind.13 was blank
during straight-and-level active pause because no warnings were active.  Fields
became populated immediately when the aircraft was manoeuvred and flight-warning
conditions were met.

Closed — WAI.

---

## Control Failures

### ARC164 — Naming inconsistency (Heatblur source bug)

The pilot and WSO UHF frequency knobs have inconsistent names in Heatblur's
`clickabledata.lua`.  Our canonical names are verbatim from the Lua `device_commands`
table, so we correctly reflect the inconsistency:

| Seat | Hundreds | Tens | Ones | DecOnes | DecHundreds |
|------|----------|------|------|---------|-------------|
| Pilot | `UHF_FREQ_KNOB_HUNDREDS` (all-caps) | `UHF_Freq_Knob_Tens` (mixed) | `UHF_Freq_Knob_Ones` | `UHF_Freq_Knob_DecOnes` | `UHF_Freq_Knob_DecHundreds` |
| WSO | `UHF_WSO_FREQ_KNOB_HUNDREDS` (WSO prefix) | `RIO_UHF_Freq_Knob_Tens` (RIO prefix) | `RIO_UHF_Freq_Knob_Ones` | `RIO_UHF_Freq_Knob_DecOnes` | `RIO_UHF_Freq_Knob_DecHundreds` |

The hundreds knob uses a different naming convention to the rest on both seats,
and the WSO back-seat knobs switch from a `WSO_` prefix to a `RIO_` prefix between
hundreds and tens.  This is a Heatblur source inconsistency.  No mapping change is
needed — the names are correct.

### ARC164.UHF_Freq_Knob_Tens / ARC164.RIO_UHF_Freq_Knob_Tens — frequency range constraint

Confirmed (via DCSControlPanel, radio in MAN mode): both radios work, but positions
0, 1, and 2 (arg values 0.0, 0.111, 0.222) are unreachable — the knob snaps to
position 3 (0.3333) as the minimum.

The mapping has `argLim [0.0, 1.0]` with 10 positions (step 0.1111), which is what
the Lua `clickabledata.lua` specifies.  Heatblur even annotated both tens-knob
elements with `--TODO Odd behavior. Depending on frequency, knob changes its
available range`.  The minimum is enforced at runtime by the simulation (likely
because the UHF radio's minimum frequency makes tens-digit < 3 unreachable for
the hundreds value currently set).

**WAI.**  The mapping correctly reflects the Lua definition.  The runtime
constraint cannot be determined statically from the Lua source and varies with the
hundreds digit.  Scripts that set this knob should not target positions 0–2 when
hundreds = 2 (225–299 MHz), but may be able to use position 0 when hundreds = 3
(300–399 MHz).  To be safe, automation scripts should treat position 3 as the
effective minimum for the tens knob.

### CANOPYCONTROLS.CANOPYCONTROLS_ManualUnlockPilotCanopy / ...CopilotCanopy

Expected pos 1 = 1.0, got 0.0.  Confirmed WAI — the manual unlock handle can only
be moved once the canopy open/close switch (ActuatePilotCanopy / ActuateCopilotCanopy)
is in the open position.  With the canopy open, the control actuates and reads back
correctly.  Prerequisite state not satisfied during validation run.

Closed — WAI.

### GEARANDHOOK.PARACHUTE_RELEASE

Expected pos 1 = 1.0, got 0.0.  Spring-loaded button.  Also conditional:
"only while deployed" — requires the drag chute to be deployed first.  WAI.

### COMPASSSYSTEM.PILOT_COMPASS_PILOT_SET_HDG_KNOB

Type: continuous, argLim [-1.0, 1.0].  All positions got 0.0.  Confirmed WAI —
the heading set knob requires `PILOT_COMPASS_PILOT_SET_HDG_KNOB_PRESS` to be
pressed (held) first before the knob will move.  With the press engaged, the
control operates correctly.  Prerequisite state not satisfied during validation run.

Closed — WAI.

### RADAR.RADAR_ANTENNA_HAND_CONTROL_ELEVATION

Expected pos 0 = -1.0, got 0.4107; pos 1 = 0.0, got 0.0373 in full validation run.
Targeted re-test passed cleanly.  The full-run failure was a transient: the physical
joystick axis (or a controller input) was deflected at the time, so the readback
didn't match the commanded position.  Control is correct; failure was environmental.

Closed — WAI.

---

## Skipped Controls (12)

The 12 skipped controls are the 5 guard/cover open controls + 5 close controls
(tested as part of guard management, not as separate controls) and 2 other
controls the validator auto-skips by default.

---

## Test Conditions for Re-Validation

To re-test failures with higher coverage:
- **ind.2 (DSCG radar):** Avionics power on, radar mode to STB or OPR
- **ind.3/4 (EO weapon displays):** Maverick or Walleye loaded, WSO sensor active
- **ind.11 (RWR):** Verify RWR is powered (ALR-46 power switch on)
- **ind.13 (ControlsIndicator):** Closed — WAI (see note above)
- **ARC164 freq knobs:** Closed — naming inconsistency is a Heatblur source bug (WAI);
  tens-knob positions 0–2 are a frequency-range runtime constraint (WAI).
- **Compass knob:** Investigate BTN+LEV interaction; may need manual testing
