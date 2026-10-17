# UH-1H Validation Notes

## Final result (run 3 — 2026-05-12)
390 pass, 6 fail, 72 skip, 0 error (468 tested of 2371 total; 1903 raw excluded)
All 6 failures are acknowledged and expected (see below). Validation complete.

## Run history
| Run | Pass | Fail | Skip | Notes |
|-----|------|------|------|-------|
| 1 | 387 | 9 | 72 | Initial extraction |
| 2 | 390 | 6 | 72 | Fixed IFF.CODE-PTR and WIPERS-PTR (IFF_multiposition_spring_switch) |
| 3 | 390 | 6 | 72 | Fixed 5 springloaded 3-pos switches (detectSpringloadedSwitch); same pass count because GOV-RPM-2 remains copilot-seat-only |

## Acknowledged failures

### Seat-specific controls (copilot seat required) — 3 failures

The UH-1H is an old module that does NOT use the `crewAccess` field to tag controls by seat.
Instead, DCS activates copilot controls only when the player is in the copilot seat.
Validation always runs from the pilot seat, so copilot-only controls return 0 or don't respond.

| Control | Arg | Notes |
|---|---|---|
| `CONTROL_SYSTEM.FORCE-TRIM-2-PTR` | 193 | Copilot stick force trim button. FORCE-TRIM-1-PTR (pilot) passes fine. |
| `EXT_CARGO_EQUIPMENT.CARGO-RELEASE-2-PTR` | 198 | Copilot cargo release button. CARGO-RELEASE-1-PTR (pilot) passes fine. |
| `ENGINE_INTERFACE.THROTTLE-2-PTR` | 250 | Copilot throttle axis. Both throttles share arg 250; copilot side non-functional from pilot seat. |
| `ENGINE_INTERFACE.GOV-RPM-2-PTR` | 210 | `default_springloaded_3pos_switch` — copilot governor RPM rocker. Confirmed working correctly in DCSControlPanel from copilot seat. |

**Status:** Expected. No extraction error.

### State-dependent controls (engine off) — 1 failure

| Control | Arg | Notes |
|---|---|---|
| `ENGINE_INTERFACE.THROTTLE-1-PTR` | 250 | `default_axis_limited`, argLim `[-1.0, 0.4]`. The 0.4 upper limit (above idle stop) is only reachable with the engine running. From cold/idle state, DCS clamps at 0.0. Validation at 75%/100% fails. |

**Status:** Expected. No extraction error.

### Weapons selector pos 2 unreachable — 1 failure

| Control | Arg | Notes |
|---|---|---|
| `WEAPON_SYS.762-SWITCH-PTR` | 256 | `default_3_position_tumb` with `inversed_=true`. Positions 0 (2.75) and 1 (40mm) pass. Position 2 (7.62, value 1.0) fails — requires miniguns loaded. |

**Status:** Expected, weapons-dependent. No extraction error.

## Fixed during validation

| Control | Issue | Fix |
|---|---|---|
| `IFF.CODE-PTR` | Mapped as simple discrete; wrong type for spring-return delta knob | Added `detectIFFMultipositionSpring()` + `IFF_multiposition_spring_switch` helper tag → `type=relative` |
| `CPT_MECH.WIPERS-PTR` | Same pattern as CODE-PTR | Same fix |
| `ENGINE_INTERFACE.GOV-RPM-1-PTR` | argLim `[-1, 0]`, positions 2 — only lower half captured | Added `detectSpringloadedSwitch()` + `default_springloaded_3pos_switch` helper tag → argLim `[-1, 1]`, positions 3 |
| `ENGINE_INTERFACE.CHIP-DET-PTR` | Same | Same fix |
| `SYS_CONTROLLER.BRIGHT-DIM-SWITCH-PTR` | Same | Same fix |
| `SYS_CONTROLLER.RESET-TEST-SWITCH-PTR` | Same | Same fix |
