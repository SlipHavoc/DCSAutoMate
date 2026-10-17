# DCS Native Control Extraction — A-4E-C Skyhawk

Module-specific extraction notes for the A-4E-C Skyhawk. Read [tools/extraction-guides/general.md](tools/extraction-guides/general.md) first for universal patterns.

## File Locations

- **Scripts directory:** [A-4E-C/Cockpit/Scripts/](A-4E-C/Cockpit/Scripts/)
- **clickabledata.lua:** [A-4E-C/Cockpit/Scripts/clickabledata.lua](A-4E-C/Cockpit/Scripts/clickabledata.lua)
- **clickable_defs.lua:** [A-4E-C/Cockpit/Scripts/clickable_defs.lua](A-4E-C/Cockpit/Scripts/clickable_defs.lua)
- **devices.lua:** [A-4E-C/Cockpit/Scripts/devices.lua](A-4E-C/Cockpit/Scripts/devices.lua)
- **command_defs.lua:** [A-4E-C/Cockpit/Scripts/command_defs.lua](A-4E-C/Cockpit/Scripts/command_defs.lua)
- **device_init.lua:** [A-4E-C/Cockpit/Scripts/device_init.lua](A-4E-C/Cockpit/Scripts/device_init.lua)

## Devices

48 devices total. Derived from [A-4E-C/Cockpit/Scripts/devices.lua](A-4E-C/Cockpit/Scripts/devices.lua).
A-4E-C quirk: devices.COMPASS is not defined in [A-4E-C/Cockpit/Scripts/devices.lua](A-4E-C/Cockpit/Scripts/devices.lua) but is referenced in [A-4E-C/Cockpit/Scripts/clickabledata.lua](A-4E-C/Cockpit/Scripts/clickabledata.lua). These elements have `device = nil` and are gracefully handled on extraction.

## Command Tables

2 tables total. Extracted from [A-4E-C/Cockpit/Scripts/command_defs.lua](A-4E-C/Cockpit/Scripts/command_defs.lua):

| Table | Count | Notes |
|-------|-------|-------|
| `device_commands` | 212 | Auto-incremented starting from 3000 |
| `Keys` | 134 | Hardcoded global key/EFM command integers |

## Elements

147 clickable elements extracted from [A-4E-C/Cockpit/Scripts/clickabledata.lua](A-4E-C/Cockpit/Scripts/clickabledata.lua).

### Quirks and Workarounds Applied:
- **use_release_message / relative / other attributes:** In A-4E-C, some element attributes such as `use_release_message` or `relative` are set directly as boolean values (e.g. `use_release_message = true`) rather than 1-indexed tables. The extractor uses a new robust `luaValueToList` helper to map both scales safely to Python lists.
- **sounds.lua loading:** Executed inside [A-4E-C/Cockpit/Scripts/clickabledata.lua](A-4E-C/Cockpit/Scripts/clickabledata.lua) via `dofile()`. Uses global definitions for toggle and knob clicks.

## Indicators

5 indicators registered via [A-4E-C/Cockpit/Scripts/device_init.lua](A-4E-C/Cockpit/Scripts/device_init.lua):

| Index | Indication ID | C++ Class | Init File | Device |
|-------|--------------|-----------|-----------|--------|
| 1 | 0 | `ccIndicator` | `HUD/Indicator/init.lua` | `nil` |
| 2 | 1 | `ccIndicator` | `HUD/Indicator/init_debug.lua` | `nil` |
| 3 | 2 | `ccIndicator` | `RADAR/Indicator/init.lua` | `nil` |
| 4 | 3 | `ccControlsIndicatorBase` | `ControlsIndicator/ControlsIndicator.lua` | `nil` |
| 5 | 4 | `ccIndicator` | `AN_ARC51/indicator/frequency_labels_init.lua` | `nil` |

There are 28 text indication fields extracted from the indicators.

## Gauges and Lamps

170 gauges and lamps extracted from [A-4E-C/Cockpit/Scripts/mainpanel_init.lua](A-4E-C/Cockpit/Scripts/mainpanel_init.lua).
