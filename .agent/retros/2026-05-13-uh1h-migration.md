# Retro: UH-1H Full Migration (Phases 1–6)

**Date:** 2026-05-13
**Branch:** eliminate-dcs-bios

---

## Goal

Migrate the UH-1H module through the full conversion pipeline:
- Phase 1–3: Extract native controls from DCS Lua files, write extraction guide
- Phase 4–5: Generate and live-validate the controlMapping
- Phase 6: Rewrite `UH-1H_dcsbios.py` → `UH-1H.py` using canonical names

---

## What Worked

- **Lupa extraction** went cleanly. The UH-1H Lua structure is straightforward: two command tables, 57 devices, 217 elements, 10 indicators.
- **`deriveDeviceTableMap`** matched 30/57 devices deterministically — the remaining 27 are passive/instrument devices with no clickable elements, so no impact on correctness.
- **`installHelperTagger`** correctly tagged all helper functions of interest. Adding `default_springloaded_switch` and `default_springloaded_3pos_switch` to `HELPER_NAMES_TO_TAG` was straightforward.
- **`detectIFFMultipositionSpring`** (from prior sessions) correctly handled `IFF.CODE-PTR` and `CPT_MECH.WIPERS-PTR`.
- **BIOS→canonical name mapping script** resolved all 33 BIOS names on first pass. No mismatches, no manual lookups needed.
- **Script migration** was mechanical and clean. `IFF_CODE: 'DEC'/'INC'` → `±1.0` worked correctly.

---

## What Didn't Work / Required Iteration

### `detectSpringloadedSwitch` — generator fix for 3-position springloaded switches

**Problem:** Five controls (`GOV-RPM-1/2`, `CHIP-DET`, `BRIGHT-DIM`, `RESET-TEST`) were mapped as `argLim=[-1, 0], positions=2` instead of `argLim=[-1, 1], positions=3`. The simple discrete path was picking only the first sub-control's argLim and ignoring the complementary second half.

**Root cause:** `default_springloaded_3pos_switch` and `default_springloaded_switch` produce two sub-controls with the **same commandId** and complementary argLims (`[-1,0]` and `[0,1]`). The generator's `isPositionMapElement` check requires ≥2 different commandIds — same-commandId pairs fell through to the simple-discrete path, which uses only the first index's argLim.

**Fix:** Added `detectSpringloadedSwitch()` with helper-tag guard + structural validation. Merges the two complementary half-ranges into the correct full argLim. Added `default_springloaded_switch` and `default_springloaded_3pos_switch` to `HELPER_NAMES_TO_TAG` in `extractUtils.py`. This fix also correctly detected `MAIN-GEN-SWITCHER-PTR`, `TEST-M-1-PTR`, and two others as positions=3.

**Side effect check:** A-10C also uses `default_springloaded_switch` — but A-10C's variants use *different* commandIds per sub-control, so they hit the `positionMap` path (not the springloaded path). Confirmed zero A-10C mapping changes after re-extraction and re-generation.

### `VHFCOMM_PWR` — unusual BIOS definition

`VHFCOMM_PWR` maps to `VHF_ARC_134.MHZ-SELECTOR-PTR_arg5` (a 2-position discrete with argLim `[0.85, 1.0]`). The DCS BIOS definition is `defineTumb` with argLim `{0.85, 1.0}` — it's a frequency+power combo knob where position index maps to the correct argLim value. The position index in the script (0 = OFF, 1 = ON) maps to argLim positions correctly because DCSDirectManager translates position indices to native float values.

### Continuous throttle values

The original script sent `46810` (raw BIOS integer) for the idle stop. The native argLim is `[-1.0, 0.4]`. The conversion: `46810 / 65535 ≈ 0.7143` (proportional fraction) which DCSDirectManager maps to the native range as `lerp(-1.0, 0.4, 0.7143) ≈ 0.0` — the correct idle stop value. The throttle ramp loop also converts correctly.

### Radar altimeter relative steps

`RADAR_ALT_LO` / `RADAR_ALT_HI` use `type=relative` with `sendProtocol=C`. The original script sent `'+3200'` / `'-50000'` as BIOS relative string format. The native equivalent is just the float value: `round(3200/65535, 4)` / `round(-50000/65535, 4)`. These are passed directly as the ±delta.

---

## Validation Notes

390 pass, 6 fail, 72 skip. All 6 failures acknowledged:

| Control | Reason |
|---------|--------|
| `CONTROL_SYSTEM.FORCE-TRIM-2-PTR` | Copilot seat only |
| `EXT_CARGO_EQUIPMENT.CARGO-RELEASE-2-PTR` | Copilot seat only |
| `ENGINE_INTERFACE.THROTTLE-2-PTR` | Copilot seat only |
| `ENGINE_INTERFACE.GOV-RPM-2-PTR` | Copilot seat only (works correctly in copilot seat) |
| `ENGINE_INTERFACE.THROTTLE-1-PTR` | Upper range only reachable with engine running |
| `WEAPON_SYS.762-SWITCH-PTR` | Position 2 requires miniguns loaded |

UH-1H has no `crewAccess` tagging in its Lua files — the validator always runs from the pilot seat, so copilot-side controls silently return 0.

---

## Instruction Update Candidates

1. **`detectSpringloadedSwitch` pattern is now handled.** The `default_springloaded_switch` / `default_springloaded_3pos_switch` helpers with same commandId + complementary argLims now correctly emit `positions=3, argLim=[-1,1]`. No future manual intervention needed for modules using these helpers.

2. **A-10C uses `default_springloaded_switch` with different commandIds** — its controls correctly hit the `positionMap` path, not the new `springloaded-switch` path. If a future module uses this helper with different commandIds, `detectSpringloadedSwitch` will correctly decline (same-commandId check) and fall through to positionMap.

3. **IFF.CODE-PTR `'DEC'`/`'INC'` in BIOS → `±1.0` in native.** These are relative controls (`type=relative, sendProtocol=C`). The BIOS special strings `'DEC'`/`'INC'` become literal float values `−1.0`/`+1.0` passed to `pushSeqCmd`. Validated working.
