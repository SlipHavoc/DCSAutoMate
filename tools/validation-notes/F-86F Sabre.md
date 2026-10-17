# Validation Notes — F-86F Sabre

Module: `F-86F Sabre`
Validation run: 2026-05-17, hot start, active pause.
Results: 245 pass, 3 fail, 19 skip, 0 error — 267 total.

---

## Category A — APX-6 IFF Mode dial stop interlock (EXPECTED — no fix needed)

**Control:** `AN_APX6_IFF.F86_CockpitDeviceCommand_APX6_Mode` — pos 4 (EMERGENCY)

The IFF master mode selector is a 5-position multiposition switch. The EMERGENCY position
(pos 4, arg value 0.4) has a mechanical dial-stop button that must be physically depressed
to allow the selector to rotate past the STDBY stop into EMERGENCY. The validator cannot
press the dial-stop button, so the selector stalls at pos 3 (STDBY, arg 0.3) and pos 4
never reads 0.4.

`AN_APX6_IFF.F86_CockpitDeviceCommand_APX6_DialStopBtn` is the companion momentary button
that releases the stop; testing the mode selector across all 5 positions requires the button
to be held during the move to pos 4.

**Acknowledged as expected — mechanical interlock, not a mapping error.**

---

## Category B — Oxygen regulator emergency lever snapping behavior (EXPECTED — no fix needed)

**Control:** `OXYGEN_INTERFACE.F86_CockpitDeviceCommand_EmergencySw`

Failure: 25% of range (expected −0.5000) got 0.0000; 75% of range (expected 0.5000) got 1.0000.

The oxygen regulator emergency lever (`Emergency_Test` element in `clickabledata.lua`) is
defined with `arg_lim = {-1, 1}`, making the mapping a continuous control with argLim
`[-1.0, 1.0]` — which is correct per the Lua source.

However, the device-side Lua implementation snaps the lever to exactly three physical
positions: forward (1.0), center (0.0), and aft (−1.0). The element definition uses two
`class_type.LEV` scroll actions (one per direction, both with `class_vr = class_type.TUMB`),
which in VR behave as a tumbable lever rather than a smooth axis. When the validator sends an
intermediate value such as 0.25 of the range (−0.5), DCS snaps it to the nearest valid
position (0.0). Likewise, 0.75 of the range (0.5) snaps to 1.0.

The continuous mapping with argLim `[-1.0, 1.0]` is structurally correct and matches the
Lua arg limits. The snapping to {−1.0, 0.0, 1.0} is device-side behavior, not a mapping
error. In practice the control should be driven only to −1.0, 0.0, or 1.0.

**Acknowledged as expected — device snaps to discrete positions, continuous argLim is correct.**

---

## Category C — Generator switch cover interlock (EXPECTED — no fix needed)

**Control:** `ELEC_INTERFACE.F86_CockpitDeviceCommand_GeneratorSwCover` — pos 0 (closed)

Failure: pos 0 expected 0.0000 (closed/down), got 1.0000 (open/up).

The generator switch cover is mechanically interlocked with the generator switch
(`ELEC_INTERFACE.F86_CockpitDeviceCommand_GeneratorSw`). The cover can only be closed
(pos 0) when the generator switch is in its pos 2 state. Because the validator tests the
cover in isolation without first moving the generator switch to the required position, the
cover cannot reach its closed state and returns 1.0 throughout.

`GeneratorSw` itself passes validation; `GeneratorSwCover` passes for pos 1 (open).

**Acknowledged as expected — mechanical interlock, not a mapping error.**
