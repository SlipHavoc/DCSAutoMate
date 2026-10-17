# Keybinding and listened-command extraction

Notes from wiring `extractKeybindings()` and `extractListenedCommands()` (in `tools/extraction-scripts/extractUtils.py`) into all 22 extractors.  See `.agent/decisions/raw-commands-from-keybindings.md` for why.

## Where the Input files live

| Layout | Modules | `inputDir` from `scriptsDir` |
|---|---|---|
| `Input/<profile>/<kind>/default.lua` | most (`Cockpit/Scripts`) | `'..', '..', 'Input'` |
| same, scripts in `Cockpit/` | AV8BNA, F-4E, F-15E, OH-58D | `'..', 'Input'` |
| `Input/<kind>/default.lua` (no profile folder) | AJS37, A-4E-C | `'..', '..', 'Input'` (auto-detected as a single profile) |
| one profile per variant | C-101CC, C-101EB | `'..', '..', 'Input', 'C-101CC'` |

`<kind>` is `keyboard`, `joystick` or `mouse`.  Hardware presets (`Some Stick.lua`) are not `default.lua` and are ignored, as DCS does.

## Lua environment gotchas

- **Use Lua 5.1 (`lupa.lua51`).**  lupa 2.7's default runtime is 5.5.  Ka-50 names contain `\%`, which 5.1 reads as `%` and 5.4+ rejects as an invalid escape.
- **`external_profile(path)` must give the loaded file its own globals** (`setfenv(chunk, setmetatable({}, {__index = getfenv(2)}))`), inheriting the caller's `folder`.  OH-58D seat profiles set a global `inputs` in both files; with shared globals the loaded file replaces the caller's table and `join(inputs.keyCommands, core.keyCommands)` appends a table to itself.  `ipairs` then never ends and memory grows until the process is killed.
- **Missing DCS `Config/Input` profiles** (`common_keyboard_binding.lua` etc.) return an empty `{keyCommands, axisCommands, forceFeedback}`.  They only hold simulator `iCommand` bindings, which have no `cockpit_device_id` anyway.
- **Stubs every binding file may call:** `_`, `join`, `external_profile`, `ignore_features`, `defaultDeviceAssignmentFor`, `MultiEngineDefaultDeviceAssignmentForThrust` (returns three nils), `defaultFFB`.
- **Bindings that use an undefined `iCommand...` global** have a nil command and are dropped (e.g. FA-18C `iCommandSeatArmHandle`).  Stray top-level entries (UH-1H Cargo View) are ignored, as DCS does.

## Listened commands

- Found by running each `creators[]` entry whose second field is a `.lua` script in a sandbox where `GetSelf():listen_command(id)` records the id, then calling `post_initialize()`.  Everything else (`GetDevice`, `get_param_handle`, `get_base_data`, ...) returns an inert "magic" value that absorbs indexing, calls and arithmetic.
- Device-script warnings (usually missing shared DCS files such as `Radio.lua`, `Macro_handler.lua`, `wsTypes.lua`) are expected.  Commands registered before the error are kept.  Most modules register none; F-4E, A-4E-C and AJS37 do.

## Keybinding counts are not a quality signal

A-10C (22), A-10C_2 (67) and Ka-50 (112/124) look low but are complete: their Input files bind ~900 simulator `iCommand`s handled by C++ avionics, and only a few dozen entries carry a `cockpit_device_id`.  To check, compare `grep -c cockpit_device_id` against the extracted count.

## Verification workflow that worked (18 modules, one pass)

1. **Wire the extractors mechanically.**  Every extractor has the same anchors (`from extractUtils import (`, `\tstats = {`, `\t\t'stats': stats,`, the last `print` in `main()`).  A one-shot script that inserts at each anchor and **fails if an anchor isn't found exactly once** is safer than hand edits.  The extractors are CRLF: read with `newline=''`, normalise to `\n`, edit, convert back; confirm the diff shows only insertions.
2. **Re-extract and diff each JSON against `git show HEAD:<path>`**, ignoring the new `keybindings` / `listenedCommands` keys.
3. **Separate DCS drift from your change:** run `git show HEAD:<extractor> > tmp.py` and run that.  If the committed extractor produces the same non-keybinding changes, it's a DCS update.
4. **Regenerate mappings and diff cockpit controls only** (`python tools/diffCockpitControls.py <mappingName> ...`).  Raw and read-only churn is expected and large (F-16C indicators: −2165/+2937); clickable changes are what matter.
5. **Flag removed controls that a script uses.**  A regex over the script's non-comment lines for `pushSeqCmd(<dt>, '<name>'` and `control='<module>/<name>'` catches literal names; then run `python tools/checkScriptControls.py <scriptModule> <mappingName>` for the app's own check.  Names built at run time (F-16C `'ICP_BTN_' + btn`) are invisible to both.
6. **`tools/mappingRegression.py`**, then the full pytest suite.

## New helpers seen after DCS updates

A mapper exits when an extraction contains a helper not in its `HELPER_MAP`; that's how a DCS update shows up.  Both cases so far matched an existing helper's shape:

- CH-47F `button_and_axis_cyclic` (BTN+BTN+relative LEV, SFD knobs) → `buttonOrAxis`, like `button_and_axis_limited`.
- AJS37 `multiposition_switch` (TUMB+TUMB, transponder code wheels) → `simpleDiscrete`, like `multiposition_switch_limited` minus `cycle = false`.

Compare `controlClass`, `action`, `argValue`, `argLim`, `relative`, `cycle` with the nearest registered helper and read the Lua factory before choosing.

## DCS naming quirks that are correct

- CH-47F `SFD1.SFD2_KNOB_*` / `SFD2.SFD1_KNOB_*`: DCS's `clickabledata.lua` attaches `SFD1_*` elements to `devices.SFD2`.  Canonical names copy the Lua verbatim.
- A shared command id can exist on two devices with different meanings (AJS37 `ENGINEPANEL.cmd_3925` data cartridge vs `IFF.cmd_3925` transponder wheel).  The device prefix is what separates them.
