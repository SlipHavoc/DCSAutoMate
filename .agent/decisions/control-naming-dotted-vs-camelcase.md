# Decision: Dotted device.command naming vs hint-derived camelCase

**Date:** 2026-04-19
**Context:** Choosing the control naming scheme for `generateControlMapping.py` output.

## Options considered

### Option A: Dotted `DEVICE_NAME.CommandName` (rejected)

Uses verbatim DCS names: `ENGINES_INTERFACE.APU_ControlSw`, `MDI_LEFT.MDI_PB_1`.

Pros:
- Simple, literal — names come directly from DCS native files.
- Easy to reverse-lookup in the original Lua sources.
- Embeds the device name, which helps identify what/where the control is.

Cons:
- **Inconsistent across modules.** FA-18C has 36 named per-subsystem command tables with descriptive names. Ka-50_3 has a single `device_commands` table with only `Button_1`–`Button_50` — no semantic names at all. This means dotted naming would be great for some modules and useless for others.
- **Inconsistent within modules.** DCS Lua naming conventions vary: SCREAMING_SNAKE, PascalCase, abbreviations — sometimes within the same file.
- **PositionMap controls** (springloaded switches with multiple commands on one arg) still need custom names, breaking the direct-from-source principle.
- **Names are longer, harder to type, and visually noisy** compared to camelCase.

### Option B: Hint-derived camelCase (chosen)

Derives names from command table names via `cmdNameToCamelCase()`, with hint text as fallback: `apuControlSw`, `mdiPb1`.

Pros:
- Consistent camelCase convention across all modules regardless of DCS Lua style.
- Works for modules with and without named command tables (hint fallback).
- Shorter, easier to type, matches project-wide coding conventions.

Cons:
- One level of indirection from the original Lua names.
- Abbreviation handling can be imperfect (e.g. `engineCrankLSw` from `EngineCrankLSw`).

## Outcome

Chose Option B. The dotted experiment was implemented as a side-by-side `_dotted.json` output, reviewed, and removed. The cross-module inconsistency problem (FA-18C vs Ka-50_3) was the deciding factor — a naming scheme that only works well for some modules isn't worth the trade-offs.

PositionMap controls (14 in FA-18C) are flagged for human review in the generator's console output, since their auto-generated names are most likely to need manual adjustment.

## Future consideration

A renaming utility app could help with batch name adjustments — filter by device, add/remove prefixes, etc. Added to the project todo list.
