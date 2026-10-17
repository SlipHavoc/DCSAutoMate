# DCSAutoMate Network Port Architecture

## Export channel (DCSAutoMateExportSettings.lua)
Runs in DCS's export/simulation loop. Has access to cockpit data.

- **UDP 6121** (`dcsAutoMateUdpPort` / `udpPort`): One-way multicast telemetry broadcast from DCS to the app. Sends flight data once/sec. Used for auto-select (module identification).
- **TCP 7780** (`dcsDirectPort` / `tcpPort`): Bidirectional command/control. DCSDirectManager connects to DCSAutoMateExport.lua's TCP server. Sends cockpit commands, receives aircraft state.

## UI overlay channel (DCSAutoMateHookSettings.lua)
Runs in DCS's GUI/overlay layer. Has access to the DCS UI framework (dxgui, DialogLoader).

- **UDP 7786** (`uiRemoteControlPort`): In-game hook overlay → desktop app. Sends UI commands (module/script selection, start/stop).
- **UDP 7779** (`uiRemoteControlReplyPort`): Desktop app → in-game hook overlay. Sends replies (module lists, script lists, status updates).

## Why two Lua files?
Export and Hook run in separate DCS environments and can't share state. Each has its own settings file and ports.

## Config flow
Python config (`DCSAutoMateConfig.json`) stores all four ports. When Settings are saved, `writeHookSettingsFile()` writes both Lua settings files to Saved Games.
