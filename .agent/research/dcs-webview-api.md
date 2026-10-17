# DCS Webview-API Research

**Date discovered:** 2026-06-02
**Full docs:** `docs/DCS_WebviewAPI_Guide.md`

## Summary

DCS has a first-class HTML/JS UI embedding system based on Chromium Embedded Framework (CEF), available to all 3rd parties since DCS 2.9.23.18431. Pioneered by Heatblur for the F-4E (they call their layer "HBUI").

## Key Facts

- `require('WebViewWidget')` in Lua — it's a DXGUI widget, insert it into any Window
- `webview:browserCreated(cb)` → then `webview:cefLoadUrl('file:///...')` to load local HTML
- JS→Lua: `window.edQuery({ request: "string", onSuccess: fn, onFailure: fn })` — ED injects this
- Lua→JS: no push API — call JS globals (`window.YourFunction(data)`) from Lua/C++
- Lua receives edQuery calls via `webview:edQueryCallback(function(query_id, request, persistent) ... end)`
- Reply with `webview:edQuerySuccess(query_id, response)` or `edQueryFailure(query_id, code, msg)`
- Domain whitelisting is Heatblur's own feature on top, not part of the core API
- Local `file://` URLs work freely; no whitelist needed for local files

## Best Reference Implementations

All under `c:\Games\DCS World\Mods\aircraft\F-4E\UI\`:
- `BombingTable/` — best example: HTML form with dynamic rows, jQuery/Select2, sends data to Jester
- `JesterWheel/` — radial menu with Pixi.js WebGL rendering, Lua updates menu structure live
- `EFB/` — live telemetry dashboard, Lua pushes state each frame via `window.UpdateDisplay(state)`

## Relevance to DCSAutoMate

Could replace or augment the current DXGUI overlay with a richer HTML UI. Enables:
- Interactive script selection and configuration forms
- Live status dashboards (waypoints, sequence progress, warnings)
- Richer checklists with per-step tick-off

## Gotchas / Unknowns

- No known Lua-side "execute JS string" method — the Lua→JS direction appears to only work via C++ device callbacks calling named JS globals. May need to verify if there's a scripting hook for pure-Lua use that can push to JS.
- The `cefCallback` method seen in the older `CEFTest.lua` may be an alias for or predecessor of `browserCreated` — unclear if both still work.
- `persistent: true` in edQuery may enable streaming (Lua replies multiple times to one query) — untested.
