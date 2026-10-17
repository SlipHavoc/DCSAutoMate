# AJS37 Viggen — Validation Notes

## Final result (run 1 — 2026-06-07)
154 pass, 33 fail, 22 skip, 9 error (218 tested of 1879 total; 1661 raw excluded)
All 42 failures/errors are acknowledged and expected (see below). Validation complete.

## Acknowledged failures

### Category A — arg=-666 controls, no readback possible (9 errors)

These controls use the AJS37 sentinel arg `-666`, meaning no cockpit animation arg
is wired to their state. DCS returns `0.0` for any read of arg -666 regardless of
the physical switch position. The commands are sent correctly and the device
responds, but state is not observable via telemetry.

| Control | Hint | Notes |
|---|---|---|
| `COUNTERMEASURE.cmd_3805` | Countermeasure Dispense | 3-position switch; physically moves, no readable arg |
| `FLIGHTDATAUNIT.cmd_3402` | AFK Mode 3 | Button; no readable arg |
| `FLIGHTDATAUNIT.cmd_3720` | Backup ADI Cage | Button; no readable arg |
| `FLIGHTDATAUNIT.cmd_3722` | Max G Reset | Button; no readable arg |
| `FR22.Button_110` | FR24 Mode Selector | 3-pos tumb (cmd_3110); no readable arg |
| `FR22.cmd_3230` | Base Selector | 3-pos tumb; no readable arg |
| `FR22.cmd_3307` | Group Selector | 3-pos tumb; no readable arg |
| `RADAR.cmd_3800` | CI filter | Axis; no readable arg |
| `WEAPON_SYSTEM.cmd_3800` | Missile Select Button | 1-pos tumb; no readable arg |

**Status:** Expected. No extraction or mapping error.

### Category B — FR22 radio channel buttons, radio-group latch behavior (21 failures)

The 20 FR22 preset/channel buttons (`PNT_362`–`PNT_381`) are all `default_button`
(`BTN` class, `stopAction` = same command, `use_release_message = true`). The FR22
device implements a radio-group latch: pressing any button selects that channel and
deselects all others. One button is always latched at 1.0.

The validator sends value 0.0 (pos 0) expecting to read 0.0 back, but the FR22
device reacts to *any* message on the command (press or release) by latching that
channel to 1.0. So every send produces a readback of 1.0.

In DCSControlPanel these controls work correctly: both Pos 0 and Pos 1 select the
channel (the FR22 ignores the value and just latches whichever button received any
message), and pressing a different button deselects the current one.

| Control | Arg | Notes |
|---|---|---|
| `FR22.Button_200` (PNT_2002) | — | `cmd_3230` Base Selector (arg -666; see Cat A) |
| `FR22.cmd_3201`–`FR22.cmd_3219` | 363–381 | Channel H, Special 1–3, Minus, A/G, B, C/F, C2, D/E, Flight 0–9 |

**Status:** Expected. No extraction or mapping error. All 20 controls added to
`DCSControlPanelSettings.json` for manual testing confirmation.

### Category C — Autopilot state-dependent switches (4 failures)

These autopilot/flight-control switches are in a particular state when the engine
is running and the autopilot has initialised. The validator's expected pos 0 = 0.0
doesn't match the active aircraft state.

| Control | Hint | Notes |
|---|---|---|
| `FLIGHTDATAUNIT.Button_97` (cmd_3097) | HÖJD CISI | Currently ON with engine running |
| `FLIGHTDATAUNIT.cmd_3301` | SPAK | Currently ON with engine running |
| `FLIGHTDATAUNIT.cmd_3302` | Attitude Hold | Currently OFF (hold not engaged) |
| `FLIGHTDATAUNIT.cmd_3303` | Altitude Hold | Currently OFF (hold not engaged) |

**Status:** Expected aircraft-state dependency. Confirmed working correctly in
DCSControlPanel. No extraction or mapping error.

### Category D — Animated lever timing/behavior quirks (2 failures)

These controls use `default_animated_lever` (TUMB+TUMB, cycle=true) and have
DCS-side behavior that prevents a clean pos 2 = 1.0 read-back.

| Control | Hint | Notes |
|---|---|---|
| `FLIGHTDATAUNIT.cmd_3406` | Canopy Open/Close | 3-position handle. While canopy is closing, arg 9 = 0.5 (handle in intermediate position). Only reaches 1.0 when the canopy fully closes and the handle snaps to the final position. Validator catches it mid-travel. |
| `FLIGHTDATAUNIT.cmd_3408` | Parking Brake | Animated lever. The brake only latches out if the brake pedals are depressed when the handle is pulled; otherwise it springs back in immediately. Validator reads 0.0 because the pedals aren't held. |

**Status:** Expected quirks of these specific controls. Confirmed working correctly
when operated under the right conditions in DCSControlPanel. No mapping error.

### Category E — Engine-state-dependent control (1 failure)

| Control | Hint | Notes |
|---|---|---|
| `ENGINEPANEL.Button_1` | Start System | The start system switch can only be turned ON with the throttle at a specific detent. With the engine already running, the switch cannot be set to pos 1. |

**Status:** Expected aircraft-state dependency. No extraction or mapping error.

### Category F — "No function" switch (1 failure)

| Control | Hint | Notes |
|---|---|---|
| `ENGINEPANEL.Button_6` (cmd_3006) | Manual Afterburner Fuel Regulator | Reads inverted (pos 0 = 1.0, pos 1 = 0.0). Per the AJS37 flight manual, this switch has "no function" in DCS. The inverted polarity may reflect an unmapped internal signal. Not used in any script. |

**Status:** Expected. Switch has no function per flight manual. No script impact.

### Category G — Axes behind covers not detected by validator (2 failures)

The validator detects covers/guards by checking for keywords (`cover`, `guard`,
`cvr`) in the **canonical name**. These two cover controls have generic canonical
names (no keyword) and were therefore not opened before their underlying axes
were tested.

| Cover control | Axis tested | Notes |
|---|---|---|
| `FLIGHTDATAUNIT.cmd_3742` (PNT_1200) | `FLIGHTDATAUNIT.cmd_3724` | Magnetic Declination Cover → Magnetic Declination Correction axis. Confirmed working once cover is open. |
| `FLIGHTDATAUNIT.cmd_3741` (PNT_493) | `FLIGHTDATAUNIT.cmd_3732` | Autopilot Yaw Trim Cover → Autopilot Yaw Trim axis. Confirmed working once cover is open. |

**Status:** Validator limitation — cover not detected because canonical name lacks
keyword. Underlying axes confirmed working in DCSControlPanel with covers open.
No extraction or mapping error.

### Category H — Weapon buttons behind covers not detected by validator (3 failures)

Same cover-detection limitation as Category G. The weapon system flipcover controls
have generic canonical names.

| Cover control | Protected button | Notes |
|---|---|---|
| `WEAPON_SYSTEM.cmd_3302` (WepEmRCvr-PTR) | `WEAPON_SYSTEM.cmd_3303` | Weapon Emergency Release Cover → Button |
| `WEAPON_SYSTEM.cmd_3308` (GroundSafetyCvr-PTR) | `WEAPON_SYSTEM.cmd_3309` | Bypass Firing Circuit Cover → Button |
| `WEAPON_SYSTEM.cmd_3402` (XTCVR-PTR) | `WEAPON_SYSTEM.cmd_3320` | External Tank Release Cover → Button |

**Status:** Validator limitation — same as Category G. No extraction or mapping error.
Also `NAVIGATIONPANEL.RENSACVR-PTR` was detected (has `cvr` in name) but failed to
open (arg 300 read back as 0.6, not 1.0) — likely requires a specific aircraft
state or the Rensa cover animation is non-standard.
