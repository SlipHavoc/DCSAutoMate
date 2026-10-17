# Architecture

DCSAutoMate is a Python scripting engine that automates cockpit procedures in DCS World.  It sends commands directly to DCS via a custom Lua export script (TCP) and keyboard simulation (PyDirectInput), bypassing the "Pure Scripts" integrity check that broke the game's built-in autostart scripts.

DCS BIOS is no longer required.  Historical versions used DCS BIOS as the command channel; that dependency has been replaced by `DCSAutoMateExport.lua` and `DCSDirectManager`.  Archived BIOS code lives in `archive/`.

## Main Modules

| Module | Responsibility |
|---|---|
| `DCSAutoMate.py` | PySide6 desktop GUI: module/script selection, start/stop/pause, config, output log.  Also manages an in-game overlay (Lua/CEF) toggled by hotkey. |
| `engine/DCSSeqExecute.py` | Executes command sequences — sends control commands via `DCSDirectManager`, keyboard input, TTS speech, cockpit-state waits, and timers.  Runs in the main thread with `processEvents` calls to keep the UI responsive. |
| `engine/ScriptManager.py` | Discovers and dynamically imports aircraft scripts from `DCSAutoMateScripts/` via `importlib`. |
| `engine/SequenceHelper.py` | Helpers passed to script functions: Lua-based coordinate conversion (lupa), MGRS truncation, route-tool utilities. |
| `network/DCSDirectManager.py` | TCP client to `DCSAutoMateExport.lua` (default `127.0.0.1:7780`).  Sends C/S/Q/W/X/T/E/I commands, looks control names up in canonical mappings, and performs value translation (discrete/continuous/relative). |
| `network/DCSAutoMateExportManager.py` | Threaded UDP multicast receiver (port 6121, group 239.255.61.21).  Parses key=value export data (altitude, position, loadout). |
| `network/BaseMulticastReceiver.py` | Abstract base class for UDP multicast receivers: non-blocking socket, threading, clean shutdown. |
| `network/UdpWireLogger.py` | Optional UDP packet logging for debugging. |
| `utils/SettingsManager.py` | Loads/saves config (`DCSAutoMateConfig.json`) and last-used selections (`DCSAutoMateSettings.json`).  Detects DCS paths. |
| `utils/TTSManager.py` | Windows SAPI text-to-speech with selectable voices, rate, and volume. |
| `utils/DcsScriptsInstaller.py` | Copies Lua export scripts and the overlay hook into the DCS Saved Games folder. |
| `DCSAutoMateScripts/*.py` | Aircraft-specific scripts (~23 aircraft).  Pure functions returning lists of command dicts. |

## Command Sequence Format

Every script function returns a `list` of `dict`s.  Each dict has:
- `time` (float) — seconds to wait after the previous command (typically 0.3 for MP safety)
- `cmd` (string) — a canonical control name (`<deviceName>.<cmdName>`, `arg.<N>`, or `ind.<id>.<field>`) or a `script*` command (`scriptKeyboard`, `scriptSpeech`, `scriptCockpitState`, `scriptTimerStart`, `scriptTimerEnd`, `scriptPause`, `scriptText`).
- `arg` — parameter for the command
- `msg` (string, optional) — display message

## Native Extraction Pipeline

The cockpit control metadata for each module is produced by a two-step pipeline that reads DCS's own Lua files:

1. **Per-module extractor** — `tools/extract_<module>.py` uses [lupa](https://pypi.org/project/lupa/) to execute the module's `command_defs.lua`, `clickabledata.lua`, and `device_init.lua` inside a mock DCS environment provided by `tools/extractUtils.py`.  A `__index` metatable on every `*_commands` global captures the exact device→command-table mapping used at each `clickabledata.lua` call site.  Output: `config/nativeExtractions/<module>.json`.
2. **Shared generator** — `tools/generateControlMapping.py` (module-agnostic) reads the extraction JSON and overwrites `config/controlMappings/<module>.json` in place.  Control keys are canonical verbatim Lua names in the form `<deviceName>.<cmdName>`.  These canonical names are the public script API; there is no alias indirection.  Before writing, the generator reads the existing file (when one exists) so explicit `sendProtocol` overrides are preserved across regenerations.  The generator also performs **sibling synthesis** (see *Naming Policy* below): for every `*_ITER`/`*_AXIS`/`*_EXT` entry in `command_defs.lua` that no clickable element references, it emits a control entry with `inferred: true` (and `siblingOf` when a clickable cousin exists) so scripts can drive these commands without anything being hidden.
3. **Live validator** — `tools/validateControlMapping.py` smoke-tests every control in a module's mapping against a running DCS instance (hot start, active pause).  Produces the per-module notes in `tools/validation-notes/`.

DCS native Lua files are the sole source of truth.  DCS BIOS is not consulted at runtime or at generation time.

## Data Flow

```
DCS World
├── DCSAutoMateExport.lua
│   ├── TCP server (7780) ──────────────► DCSDirectManager (commands + queries)
│   └── UDP multicast (6121) ───────────► DCSAutoMateExportManager (periodic state)
└── In-game overlay ◄──UDP send/reply──► DCSAutoMate GUI (7786/7779)
                                              │
                              ScriptManager loads script
                              DCSSeqExecute runs commands
                              ├── Control commands → DCSDirectManager (TCP)
                              ├── Keyboard (PyDirectInput)
                              └── TTS (Windows SAPI)
```

## Constraints and Conventions

- **Threading model**: Network managers each run in daemon threads.  Script execution runs in the main thread and calls `processEvents` to keep the GUI alive.  Shared data is protected by locks.
- **camelCase everywhere**: Variables, functions, class names.  No snake_case or kebab-case.
- **Tabs for indentation** in all files.
- **Scripts are pure functions**: They receive a `SequenceHelper` and return data.  They do not import the engine or GUI.
- **Canonical naming**: Control mapping keys are verbatim DCS Lua names (`<deviceName>.<cmdName>`).  No case conversion, suffix stripping, or dedup synthesis.  Scripts reference controls by these canonical names directly; see *Naming Policy* below.
- **DCS does not require DCS BIOS**.  The `Install/Update DCS Scripts` menu item installs `DCSAutoMateExport.lua` and the overlay hook into the Saved Games folder; that is the only DCS-side setup needed.

## Naming Policy

Scripts reference controls by their **canonical name**, which is the verbatim DCS Lua identifier: `<deviceName>.<cmdName>` for commandable controls (e.g. `FUEL_INTERFACE.FuelQtySelSw`, `UFC.SYM_Knob`), `arg.<N>` for raw cockpit args, and `ind.<id>.<field>` for indicator fields.  These names are stable, unambiguous, and identical for every user running the same DCS version, which makes scripts portable without any accompanying per-user config.

The human-readable text for logs and UIs comes from the `description` field of each control mapping entry, not from the name.  Script authors who want a shorter local label can define a module-level constant in their own script (`FUEL_QTY_SEL = 'FUEL_INTERFACE.FuelQtySelSw'`) — there is no shared alias mechanism.

### Inferred sibling controls

DCS modules typically declare three `command_defs.lua` entries per rotary or analog control: a clickable base (`FuelQtySelSw`) plus convention-named siblings (`FuelQtySelSw_ITER` for relative steps, `FuelQtySelSw_AXIS` for continuous-axis input, sometimes `_EXT` for cockpit-external triggers).  `clickabledata.lua` references only the base, so a strict clickable-only extraction would silently hide the siblings — yet the data is right there in the native Lua, and scripts may legitimately want to drive a stepper from a hat switch.

The generator therefore emits a control entry for every `_ITER`/`_AXIS`/`_EXT` command found in `command_defs.lua` that has no clickable counterpart.  Synthesized entries carry:

- `inferred: true` — flag that the entry's `type`/`argLim` are conventional guesses, not extracted from clickable metadata.
- `siblingOf: "<deviceName>.<baseName>"` — present when a clickable base exists; absent for orphan siblings.
- Suffix-driven defaults: `_ITER` → `type='relative'`, `argLim=[-1.0, 1.0]`, `sendProtocol='C'`, inherits `arg` from base.  `_AXIS` → `type='continuous'`, inherits `arg`/`argLim` from base.  `_EXT` → inherits from base if present, otherwise discrete two-position momentary.

Scripts should prefer non-inferred entries when both exist (the clickable form has been validated against real cockpit behavior).  Inferred entries are still safe to use; the `inferred` flag exists so callers and validators know the metadata is conventional rather than observed.

See `.agent/decisions/canonical-alias-naming.md` (and its 2026-04-23 update) for the history of why the earlier alias layer was retired.

## Things That Would Surprise a Newcomer

1. **Script execution blocks the main thread.**  `DCSSeqExecute` uses a loop with `time.sleep` and `processEvents`, not a worker thread or async.  This is intentional — it keeps the execution model simple and avoids race conditions with the UI.
2. **The in-game overlay is a separate Lua/CEF interface** inside DCS, communicating with the Python app over UDP (ports 7786/7779).  It is not a PySide6 window.
3. **`scriptCockpitState` is a blocking wait.**  It pauses the sequence until a cockpit control reaches a target value (with comparison operators), which makes scripts react to dynamic in-game events rather than relying on hardcoded timers.  Queries go through `DCSDirectManager` over TCP.
4. **Keyboard commands require the DCS window to be focused.**  `PyDirectInput` sends input to the foreground window, so the app uses `PyGetWindow` to find and activate DCS before sending keys.
5. **Canonical names are the public script API.**  Control mappings are keyed by verbatim Lua identifiers (`<deviceName>.<cmdName>`, `arg.<N>`, `ind.<id>.<field>`) that grep directly into DCS's `command_defs.lua` and `clickabledata.lua`.  Scripts use these names directly; there is no runtime alias resolution layer.  See *Naming Policy* above.
6. **Per-module extractors share `tools/extractUtils.py`** for the Lua mock environment, `dofile` re-sweep, and deterministic device→command-table mapping.  The AH-64D extraction trap is the motivating example: `VR_config.lua` re-`dofile`s `command_defs.lua` after metatables are installed, and the re-sweep is what keeps the proxies in place.
7. **The `archive/` folder** contains historical versions of the app (tkinter, curses, console), the retired `DCSBIOSExportManager.py`, and the retired Tkinter DCSMonitor (`archive/DCSMonitor/`), which DCSControlPanel replaced.
8. **`DCSControlPanel.py`** is a second PySide6 app alongside `DCSAutoMate`.  It reuses `DCSDirectManager` but focuses on *driving* controls interactively: each monitored control renders as a card with type-appropriate input (buttons for discrete, slider for continuous, ±/step for relative, read-only label otherwise).  Monitored refs persist to `config/DCSControlPanelControls.json`; polling runs on a worker thread.
9. **Two workspaces coexist**: The DCSAutoMate Python project, and the DCS game's module folders (FA-18C, F-16C, AH-64D, Ka-50_3, etc.) opened as separate roots.  The module folders are reference material for extraction, not part of the build.
