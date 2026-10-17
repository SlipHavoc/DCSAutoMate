# Non-Clickable Controls (HOTAS, Stick, etc.)

## Summary

Some cockpit controls exist as valid DCS devices/commands but have no entry in
`clickabledata.lua` because they have no on-screen mouse interaction area.
These are typically HOTAS stick and throttle controls (buttons, switches, axes).

## What We Know

- DCS BIOS defines these using **the same `performClickableAction(command, value)`
  mechanism** as every other control. They work identically over the wire.
- They have a valid `device_id`, `command`, and `arg_number` — DCS treats them
  the same as any panel switch.
- They do NOT appear in the `elements` table from `clickabledata.lua`, so
  `extractControlsLupa.py` will not find them. This means no native metadata
  (argLim, argValue, controlClass) is available from that source.

## FA-18C Examples (device 13 = HOTAS)

| BIOS Name            | Command | Arg | Type             |
|----------------------|---------|-----|------------------|
| STICK_GUN_TRIGGER2   | 3002    | 479 | definePushButton |
| THROTTLE_CAGE_BTN    | 3031    | 487 | definePushButton |
| THROTTLE_DISP_SW     | 3032    | 488 | defineRockerSwitch |
| THROTTLE_SPEED_BRK   | 3035    | 489 | define3PosTumb   |
| THROTTLE_ATC_SW      | 3037    | 491 | definePushButton |
| THROTTLE_FOV_SEL_SW  | 3034    | 492 | definePushButton |
| THROTTLE_RADAR_ELEV  | 3026    | 493 | definePotentiometer |

## Implications for Future Modules

If building a module from scratch (no DCS BIOS reference):

- **Names**: We'd invent our own control names, since there's no BIOS name and
  no clickabledata hint text to derive one from.
- **Command IDs**: Can be found in `command_defs.lua` for the module.
- **Arg numbers**: NOT in clickabledata. Would need to be found in other module
  Lua files (e.g. `mainpanel_init.lua` sometimes maps arg numbers to
  animations), or discovered through in-game testing using
  `dev0:get_argument_value(n)` sweeps.
- **Value ranges**: The DCS BIOS definitions encode these (e.g. `define3PosTumb`
  implies limits `{-1, 1}` with step 1; `definePotentiometer` has explicit
  limits like `{-1, 1}`). Without BIOS, you'd need to determine ranges by
  inspecting mainpanel animation definitions or in-game testing.

## Current Handling

In `generateBiosMapping.py`, these 7 controls are "unmatched" — they have valid
BIOS entries with correct device/command/arg but no `native` sub-object. The
translation layer uses the BIOS-provided step/limits data for value conversion.
