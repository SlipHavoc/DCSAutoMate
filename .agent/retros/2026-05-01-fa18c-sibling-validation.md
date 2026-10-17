# Retro: FA-18C validation run 11 + sibling control analysis + removal decision

**Date:** 2026-05-01
**Branch:** `eliminate-dcs-bios`
**Outcome:** Savepoint commit. Decision made to remove sibling control synthesis in the next session.

## Goal

Push the FA-18C validation pass rate as high as possible, diagnose remaining failures, and determine whether the sibling control system (`_EXT`/`_ITER`/`_AXIS`) is worth maintaining going forward.

## What shipped this session

- **`generateControlMapping.py`**: `_ITER` siblings now inherit `argLim` from their base (previously always `[-1.0, 1.0]`), `positionMap` derivation for `_EXT` siblings of spring-loaded switches, `incValueMap` injection from DCS input profile files via new `parseInputFiles.py`.
- **`validateControlMapping.py`**: `testInferredCycleDiscrete()` for `_EXT` discrete siblings (change-detection sweep), `readbackArgLim` branch in `testContinuous()` for `_AXIS` inverted-range controls, improved `testRelative()` (boundary-direction detection, `incValue`-aware step), guard deferral (covers tested after main loop).
- **`DCSDirectManager.py`**: `_reverseTranslateValue()` interpolates across `None` positionMap entries so spring-loaded center positions resolve correctly.
- **`parseInputFiles.py`**: new tool — executes DCS keyboard/joystick `default.lua` files via lupa to extract per-command step values.
- Two new generator tests: `test_extSiblingInheritsPositionMapFromBase`, `test_extSiblingPositionMapValueOnlyFallback`.
- `FA-18C_hornet.json` regenerated; stale `FA-18C.json` deleted.
- **Validation run 11**: 644 pass / 20 fail / 40 skip (up from ~600 pass earlier in the branch).

## What the 20 failures turned out to be

Three distinct categories, none fixable by the validator or generator:

**1. Spring-loaded switches (2 controls)**: `HookBypass`, `HookBypass_EXT` — these are `springloaded_2_pos_tumb2` in clickabledata.lua. They only send a toggle signal; the arg position cannot be set absolutely. The validator correctly detects this as a failure because the arg doesn't land where commanded.

**2. Physical/safety locks on ground (9 controls)**: `CanopyJettLever`, `SeatEjectionControlHandle`, `GearHandle`, `EmergParkHandleOnOff_EXT`, `WingFoldSelect`, `WingFoldSelect_ITER`, `WingFoldPull`, `RADAR.RADAR_SwitchChange` pos 3 (pull-to-EMERG), `ModeSw_EXT` pos 1 — these controls require a mechanical interlock or a weight-on-wheels condition to move past a protected position. They would pass in-flight or with the appropriate interlock state.

**3. IFEI page-dependent indicators (7 fields)**: `txt_Codes`, `txt_FUEL_L`, `txt_FUEL_R`, `txt_SP`, `txt_T`, `txt_Z`, `txt_TimeSetMode` — these fields only appear in `list_indication(5)` when the IFEI is on the FUEL or TIME page. During the validation run the IFEI was on a different page, so the fields were absent.

**4. `_EXT` sibling structural failures (2 controls)**: `CMDS.Dispenser_EXT` and `EXT_LIGHTS.Strobe_EXT` — the underlying TUMB-class switches have argLim ranges that produce a zero delta at one position index (`argLim[0] + step * posIndex = 0`). Sending delta 0.0 to a TUMB control is a no-op in DCS. `Dispenser_EXT` additionally references a BIOS input commandId (3004) that silently does nothing without BIOS loaded.

## The removal decision

**Decision: remove all sibling control synthesis (`_EXT`/`_ITER`/`_AXIS`) in the next session.** See `.agent/decisions/eliminate-sibling-controls.md`.

## What didn't go smoothly

- **`CMDS.Dispenser_EXT` root cause took multiple passes to diagnose.** The failure message ("arg stuck at 0.1000 for all positions") looked like the normal zero-delta TUMB problem, but the secondary cause (commandId 3004 is a BIOS input command, not a native clickable) was equally real. Lesson: for `_EXT` sibling failures, always check both the zero-delta condition AND the commandId source section in command_defs.lua.
- **`EXT_LIGHTS.Strobe_EXT` position 1**: `argLim = [-1.0, 1.0]`, `step = 1.0`, so `translateToNative(pos=1) = -1.0 + 1.0*1 = 0.0`. Zero-delta. Positions 0 (delta −1.0) and 2 (delta +1.0) worked fine.
- **`parseInputFiles.py` lupa approach** is functional but depends on DCS Lua globals being loaded in a specific order. Modules without an Input directory degrade gracefully via the optional `--input-dir` flag.

## Instruction update candidates

> **`_EXT` sibling failure diagnosis**: When an `_EXT` sibling shows "arg stuck at X for all positions", check two independent causes: (1) does `argLim[0] + step * posIndex = 0` for any position (zero-delta TUMB no-op), and (2) is the commandId in the `-- input commands` section of command_defs.lua (a BIOS-only input command that DCS ignores natively)?
