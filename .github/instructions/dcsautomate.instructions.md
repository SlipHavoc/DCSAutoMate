# Specific instructions for the DCSAutoMate project

Consider adding more steps to this file as we learn:

- When working with DCS cockpit control values, always refer to `.agent/research/dcs-native-control-types.md` before making assumptions about value ranges or command behavior. performClickableAction sets absolute positions, not relative steps.

- For any control type investigation, start by reading the factory function definition in `clickable_defs.lua`. The function signature + default values tell you everything about what values the control expects.

- Continuous control values in scripts are proportional (0.0 = minimum, 1.0 = maximum of the control's native range). The translation layer in DCSDirectManager scales these to actual argLim values. This matches the semantic intent of the old int16() convention.

- When migrating other aircraft scripts from DCS BIOS to native format, refer to `.agent/research/script-migration-patterns.md`. The key transformations are: remove int16() (divide raw ints by 65535), replace SCREAMING_SNAKE_CASE names with camelCase from nameMap, convert special-case controls (relative types need native delta values, not DCS BIOS-scaled strings), and update dynamic name construction patterns for camelCase.

- At the **start** of each session, read `todos/<branch-name>.md` (if it exists) to understand current status and next steps. At the **end** of each session that produces non-trivial changes, update the status table in that file (if it doesn't exist, ask the user if they want you to create it) to reflect what was completed. Keep `.agent/` notes current per AGENTS.md.

- When extracting data from DCS Lua files, always prefer executing the Lua via **lupa** (the Python-Lua bridge) over regex parsing. DCS Lua files are written by human programmers and are not guaranteed to be regular — regex is fragile against formatting variations, comments, conditional logic, and multi-file `dofile()` chains. Lupa handles actual Lua control flow, picks up transitive file includes automatically, and is consistent with the existing extraction approach in `tools/extract_*.py`. Mock any missing C++ host functions as needed rather than falling back to regex.

- After a DCS update, run `python tools/checkDcsUpdate.py`, review the reported changes, and commit `config/nativeExtractions`, `config/controlMappings` and `config/dcsVersionChecked.json`.

- Auto Select only sets vars on the script it picks (Cold / Hot / Air Start).  For a var that only exists on other scripts (e.g. AH-64D `seat`), read the value at run time in a live script instead.

- Lua tables in DCS clickable definitions can have `nil` holes (`relative = {nil, true}`, `arg = {nil, 10}`).  Keep per-sub-control lists index-aligned: map `None` to a neutral value, never filter it out.  See `.agent/research/lupa-native-extraction.md`.

- After changing an extractor, regenerate with `python tools/checkDcsUpdate.py` and read the mapping diff entry by entry; the tests don't cover what real DCS Lua produces.
