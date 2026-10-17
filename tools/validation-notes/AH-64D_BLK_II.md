# AH-64D Block II — Validation Notes

Module: `AH-64D_BLK_II`
Tested: 2026-04-19, hot start, active pause.
Default delay: 0.05s — 626 controls total.

## Summary at default delay (80ms, with auto-retry at 320ms and 1.28s)

- Pass: 614 | Fail: 12 | Skip: 0 | Error: 0
- Run time: ~4.8 minutes (with guard auto-opening)

## Animation delay controls (auto-resolved by retry logic)

The AH-64D module animates many controls over varying durations:
- ~49 controls need >50ms but ≤80ms (resolved by default 80ms delay).
- ~11 controls need >80ms but ≤320ms (resolved by 1st retry at 4× delay).
  Examples: mode knobs, anti-collision lights, rotor brake, stick folding.
- ~8 controls need >320ms but ≤1.28s (resolved by 2nd retry at 16× delay).
  Examples: spSelectSw, mik, cpg/pltDoorLock.

All animation-related failures are automatically resolved by the retry logic.

## Guarded spring-loaded buttons (pass with guard auto-opening)

These are momentary-action buttons behind guards/covers. With guard auto-opening
enabled (default), the covers are opened before testing and all 8 pass:
- `apuStartBtn` — fires APU start then springs back.
- `pltApuFireBtn`, `cpgApuFireBtn` — fire suppression; momentary.
- `pltEng1FireBtn`, `cpgEng1FireBtn` — fire suppression; momentary.
- `pltEng2FireBtn`, `cpgEng2FireBtn` — fire suppression; momentary.
- `cmwsJettSw` — jettison; momentary.

Note: these controls do actuate when tested — APU start fires, fire bottles
discharge, etc. No aircraft damage observed in active-pause hot start.

## Safety-blocked controls

- `pltM4Trigger`, `cpgM4Trigger` — weapon trigger won't move because
  `pltM4Safety` / `cpgM4Safety` is in the safe position. The trigger arg stays
  at 0.0 for both half-press and full-press. Not a mapping error — the trigger
  works, it's just blocked by the safety. Unlike guards/covers, safety switches
  are not auto-opened because flipping them has system-wide effects (arming
  weapons, etc.).

## Power levers — physical lockouts

All four power levers (pltLPowerLever, pltRPowerLever, cpgLPowerLever,
cpgRPowerLever) have DCS-enforced travel limits:
- Low end locked at 0.2500 (idle cutoff requires guard manipulation).
- High end locked at 0.9000 (emergency power requires lockout lever).
- Middle positions (25%, 50%, 75%) pass fine.

These should be tested by verifying the lever moved and reporting actual min/max,
rather than asserting it reached the full argLim range.

## Relative controls

- `cageKnobRotate` — increment had no effect at any delay. This is the SAI
  (Standby Attitude Indicator) cage knob. It requires the ITER command (3004)
  via SetCommand (`S:`) rather than the base command (3002). The mapping already
  uses commandId 3004, and the AH-64D script uses it successfully (sending
  -0.75 fifteen times to uncage/center). The validation script's relative test
  sends a small increment and checks for arg change — the 0.03-per-notch
  movement may be too small to detect, or the test's increment value may not
  match the expected ITER step size. See `.agent/research/dcs-native-control-types.md`
  §11 for the full investigation.

## TEDAC manual tracker (4 controls)

- `tedacRhgManTrkUp/Down/Left/Right` — these are rate-based controls. Sending
  position 1.0 moves the tracker in that direction, but the arg represents the
  tracker position, not the input. Got values like ±0.12 rather than ±1.0.
  The mapping may need a different control type or special handling.

## Read-only indication fields

- `parkingBrakeLbl` (indication 17, field `parking_brake_lbl`) — returned empty.
  The parking brake in the Apache is a pull lever, not a labeled indicator. This
  field may only populate when the brake is engaged, or the indication ID may be
  wrong. Needs cockpit research.
- `txtChanName0` through `txtChanName3` (indication 17, fields
  `txt_chan_name0`..`3`) — returned empty. These likely populate only on specific
  EUFD/radio pages. Not a mapping error, just state-dependent.
