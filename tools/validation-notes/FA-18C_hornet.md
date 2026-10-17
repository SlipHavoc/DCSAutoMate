# FA-18C Hornet — Validation Notes

Module: `FA-18C_hornet`
Tested: 2026-04-19, hot start, active pause.
Default delay: 0.08s — 491 controls total.

## Summary (80ms delay, with auto-retry at 320ms and 1.28s)

- Initial run: Pass 467 | Fail 20 | Skip 4 | Error 0
- After sendProtocol fix: Pass 472 | Fail 15 | Skip 4 | Error 0
- Run time: ~2.7 minutes (with guard auto-opening)

## Guard/cover auto-opening

5 guards/covers detected and opened:
- `emerg*Cover` controls for emergency jettison, parking brake, etc.
All verified open before testing, closed after.

## IFEI indication fields — state-dependent (7 failures)

Indication 5 (IFEI) returns 36 fields at runtime, but 7 fields defined in the
Lua source are not present in the current display mode:
- `txtCodes` — transponder codes, likely only shown in specific radio/IFF mode.
- `txtFuelL`, `txtFuelR` — left/right fuel, may require specific fuel display page.
- `txtSp` — possibly specific power or a sub-mode field.
- `txtT` — possibly temperature or time sub-field.
- `txtTimeSetMode` — time set mode indicator, likely only shown during clock setting.
- `txtZ` — possibly zulu time, shown in alternate time display mode.

These fields exist in the IFEI Lua definition but DCS only includes them in
`list_indication()` when the corresponding display mode is active. Not mapping
errors — just state-dependent visibility.

## UFC indication fields — all pass

All 15 UFC fields (indication 6) pass: comm displays, option cueings, option
displays, and scratchpad fields all found and readable.

## Relative controls — FIXED (were 5 failures, now 0)

All 5 FA-18C relative controls were failing because the validation tool (and
the runtime `sendControl()`) used `S:` (SetCommand) by default for relative
controls. FA-18C relative controls actually need `C:` (performClickableAction)
because their Lua device handlers process deltas through the clickable action
pathway, not the SetCommand pathway.

Fix: Added `"sendProtocol": "C"` to all 5 controls in the mapping JSON:
- `aau52ClkCmdZeroSetting` — altimeter barometric setting knob (dev 26, cmd 3001)
- `comm1Ch` — COMM 1 channel knob (dev 25, cmd 3033)
- `comm2Ch` — COMM 2 channel knob (dev 25, cmd 3034)
- `id2163aSetMinAlt` — radar altimeter min alt knob (dev 30, cmd 3002)
- `saiRotate` — SAI cage/adjust knob (dev 32, cmd 3003)

All 5 now pass validation. This is the opposite of the AH-64D SAI ITER pattern
where `S:` is needed with a separate ITER command ID (3004). The distinction:
- FA-18C: `relative=true` in Lua element + base command → needs `C:`
- AH-64D SAI: ITER command (3004) via device handler → needs `S:`

Also updated the validation tool `testRelative()` to respect `sendProtocol`.

## Radar switch mapping issue (1 failure)

- `radarRadarSwitchChange` — positions are consistently offset by ~0.08. Expected
  [0.0, 0.1, 0.2, 0.3] but got [0.08, 0.0, 0.12, 0.2]. This suggests either the
  position step/argLim in the mapping is wrong, or the switch has a non-linear
  position mapping. Needs investigation against clickabledata.lua.

**Additional note**: The 4th position (0.3 = EMERG) involves a pull-up action
(`radarRadarSwitchPull`, dev 42, cmd 3002) that locks the switch. Once in EMERG,
the switch cannot be released programmatically — requires manual mouse interaction
(scroll down + left click). The mapping may need to be limited to 3 positions
(OFF/STBY/OPR) for safe scripting, with EMERG handled separately.

## Physical/safety-blocked controls (4 failures)

- `canopyJettLever` — one-shot jettison lever, won't move in normal operation.
  DCS prevents this to avoid accidental canopy loss.
- `seatEjectionControlHandle` — ejection handle safety. Same as canopy jettison —
  one-shot irreversible action.
- `gearHandle` — landing gear. Stuck at 0.0 (down position). Likely locked by
  weight-on-wheels safety. Should pass in air start missions.
- `emergParkHandleSelectPark` — parking brake positionMap control. This is a
  multi-step rotate+pull sequence (documented in `.agent/research/multi-step-control-sequences.md`).
  The individual positions can't be tested independently because the sequence
  requires rotate → release → pull in order.

## HookBypass toggle behavior (1 failure)

- `cptLightsHookBypass` — defined in clickabledata.lua as `springloaded_2_pos_tumb2`,
  identical in structure to `cptLightsLtTestSw`. However, the DCS device handler for
  `HookBypass` implements **toggle semantics**: sending value `1.0` toggles state,
  sending `0.0` is a no-op. `LtTestSw` uses **absolute set semantics** where the
  value directly selects the position. This difference is entirely in compiled DCS
  device code (not visible in Lua). Result: pos 0 send is ignored and pos 1 appears
  inverted in validation. Not a mapping error — a DCS-internal toggle control.
  Safe to leave as a known failure; runtime scripts should use toggle-style sends.

## Wing fold (2 failures)

- `controlWingFoldPull` — reports full range but at wrong percentages (0% and
  100% only, no intermediate). This is a two-stage control: must select fold
  direction first, then pull to actuate.
- `controlWingFoldSelect` — expected [-1, 0] but got [1, 1]. May be locked or
  require specific ground conditions (ground power, hydraulics).

## emergParkHandleOnOff (1 failure)

- `emergParkHandleOnOff` — parking brake handle rotate. Known multi-step control
  (rotate+pull sequence). Maps to a relative-style control but the parking brake
  mechanism requires a specific interaction sequence.

## Skipped controls (4)

4 controls were skipped (missing commandId or other required fields). These are
likely gauge-only entries or placeholder definitions.
