# Session Retrospective — Native Extraction Script (FA-18C)

**Date:** 2026-04-18
**Branch:** eliminate-dcs-bios

## Goal

Begin Phase 1 of the DCS BIOS elimination: create a per-module native extraction script for the FA-18C that extracts all control data (devices, commands, elements, indicators, text fields) directly from DCS's native Lua files, with no BIOS dependency.

## What Worked

- **Lupa for clickabledata.lua** — the existing extractControlsLupa.py pattern (mock DCS globals, execute clickabledata.lua, read populated tables) transferred cleanly to the new per-module script. 285 elements, 71 devices, 36 command tables extracted with zero issues.

- **Lupa for device_init.lua** — executing device_init.lua to populate indicators[] worked well once the right mocks were in place. This correctly handles conditional branches (helmet_option, bakeIndicators/bakeHUD), function-based indicator insertion (maintenance_setup_HMS), and runtime config — things that regex couldn't reliably capture.

- **Regex for text fields** — page files use rendering APIs that would need extensive mocking, but the text field naming patterns (addStrPoly, .name assignments) are simple enough for regex. The hybrid approach (lupa for execution, regex for static text patterns) is a good balance.

- **pcall in dofile** — wrapping dofile's execution in pcall to catch runtime errors from font/material files that depend on missing rendering globals. This lets device_init.lua run to completion even when secondary dofile chains fail.

## What Didn't Work

- **Regex-only indicator parsing** — the first implementation used regex to parse `indicators[#indicators + 1] = {...}` patterns from device_init.lua. This only captured 6 entries (the bake indicators, which are single-line). The 8 static indicators are multi-line with varying whitespace and tab patterns that didn't match. Helmet indicators are added via function calls (`add_inds(maintenance_setup_HMS())`), which regex fundamentally can't handle. Switching to lupa execution solved all of this.

- **dofile without pcall** — the initial dofile mock only caught loadfile failures (file not found). But device_init.lua → materials.lua → fonts.lua → references `symbol` global (set by symbols_locale.lua which doesn't exist outside DCS). This caused a runtime error that aborted device_init.lua execution entirely. Adding pcall fixed it.

## Instruction Update Candidates

1. **Add to AGENTS.md or project instructions:** "For DCS Lua extraction, prefer lupa execution over regex parsing. Use pcall-wrapped dofile to tolerate missing/broken dependency files. Regex is appropriate only for static text patterns in indicator page files."

2. **Consider adding to dcsautomate.instructions.md:** "Per-module extraction scripts live in `tools/extract_<module>.py` and output to `config/nativeExtractions/<module>.json`. Extraction guides are in `tools/extraction-guides/`."
