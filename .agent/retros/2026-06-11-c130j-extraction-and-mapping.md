# Retrospective — C-130J-30 Super Hercules Extraction & Mapping

**Date:** 2026-06-11

---

## Goal

Successfully complete Phase 1 through 5 of the C-130J-30 cockpit control extraction and mapping pipeline, live-validate the layout in-game, and refine our mappings to match real cockpit behavior.

---

## What Worked

- **Lupa Execution and Devices Map:** Mocking global tables and standard setup in `extract_C130J.py` successfully extracted 765 native controls, 97 devices, and 49 indicator pages without regex.
- **Direct Axis/Discrete Mapping:** The customized archetypes cleanly divided 1308 generated configurations.
- **Selective Helper Adaptation:** Grouping exceptions into tailored mapping intercepts (`customVisor`, `customFirePull`, `customMultiswitch`, `customHudBtn`) in `map_C130J.py` rather than altering general archetypes.
- **Direct Range Elevation:** Re-configuring Oxygen and Squelch regulators to use `argLim = [-2.0, 2.0]` with `step = 4.0` bypassed the need for `indicatorArgLim` workarounds, resulting in clean, simple 2-position discrete controls.

---

## What Didn't

- **Momentary HUD Pressed States:** Using raw helper bounds (`argLim = [0, 1.0]` with `argValue = [0.25]`) originally caused momentary HUD buttons (`hud_btn`) to be mapped as 5-position discrete controls, allowing deep pseudo-press positions. Creating `customHudBtn` clamped the functional command range to `[0.0, 0.25]` with a single step, aligning it with the real physical button action.
- **Workaround Dependency:** Over-relying on `indicatorArgLim` for controls that internally command beyond the logical range of `[-1.0, 1.0]`. Direct elevation of command boundaries is cleaner when the native draw argument matches the commanded input range.

---

## Instruction Update Candidates

We should add a reminder to the module-control-extractor instructions or extraction guides:
- When a native helper has a step fractional to the limits (e.g. `arg_value = 0.25` inside `[0, 1.0]`), verify if it represents visual spring travel or a multi-step selector. If the former, clamp the `argLim` to `step` value to represent a clean 2-position toggle/button.
