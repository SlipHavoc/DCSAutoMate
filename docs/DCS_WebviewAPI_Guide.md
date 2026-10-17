# DCS Webview-API Guide

## WARNING ##

This document was assembled by reverse-engineering the F-4E module files and the DCS core DXGUI bindings. It has not been validated by running live code. Corrections are welcome.

## Overview

The **Webview-API** is a DCS-native system that lets any module (or potentially any mod/utility) embed a full HTML/CSS/JavaScript UI inside DCS World. It was pioneered by Heatblur Simulations for their **HBUI** (Heatblur Browser UI) system in the F-4E Phantom, and then formally integrated by Eagle Dynamics as a first-class API available to all 3rd parties (announced in DCS 2.9.23.18431).

**HBUI** is the layer Heatblur built on top of the core Webview-API. The core API itself is simpler.

The rendering engine is **Chromium Embedded Framework (CEF)** — a full modern browser embedded in the game. Standard HTML5, CSS3, and JavaScript all work, including third-party libraries (jQuery, Pixi.js, Select2, etc.).

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│  DCS Game Engine                                             │
│                                                              │
│  ┌──────────────────┐     ┌─────────────────────────────┐   │
│  │  Lua device code │────▶│  WebViewWidget (DXGUI)      │   │
│  │  (your script)   │     │  (embedded CEF browser)     │   │
│  │                  │◀────│                             │   │
│  └──────────────────┘     └──────────────┬──────────────┘   │
│   edQueryCallback /               window.edQuery()           │
│   edQuerySuccess()                (injected by ED)           │
│                                          │                   │
└──────────────────────────────────────────┼──────────────────┘
                                           │
                              ┌────────────▼────────────┐
                              │  Your HTML/JS page       │
                              │  (local file:// or URL)  │
                              └─────────────────────────┘
```

**Key points:**
- Lua calls global JS functions on the page to push state updates (no explicit "send" API — just call a `window.MyFunction(data)` you've defined in your JS).
- JS calls Lua via `window.edQuery()`, which ED injects into every page.
- The Lua side receives these via `edQueryCallback` and replies via `edQuerySuccess` / `edQueryFailure`.

---

## File Locations

| File | Description |
|------|-------------|
| `c:\Games\DCS World\dxgui\bind\WebViewWidget.lua` | The Lua binding — the full public API surface |
| `c:\Games\DCS World\Scripts\UI\CEFTest.lua` | ED's minimal usage example |
| `c:\Games\DCS World\Scripts\UI\webViewBackground.dlg` | Example `.dlg` file with a transparent window skin for webview |
| `c:\Games\DCS World\Mods\aircraft\F-4E\UI\` | All F-4E HBUI apps (the richest examples available) |

---

## Lua-Side API

### Requiring the module

```lua
local WebViewWidget = require('WebViewWidget')
local Window = require('Window')  -- or use DialogLoader with a .dlg file
```

### Creating and showing a webview

```lua
local win = Window.new('myWindow')
win:setSize(800, 600)
win:setVisible(true)

local webview = WebViewWidget.new()
webview:setSize(800, 600)
win:insertWidget(webview)
```

### Navigating to a page

Wait for the browser to be ready first:

```lua
webview:browserCreated(function()
    webview:cefLoadUrl('file:///C:/path/to/your/UI/index.html')
    -- Or a real URL (subject to any whitelist in effect):
    -- webview:cefLoadUrl('https://example.com')
end)
```

**Note:** `cefCallback` appears in the older `CEFTest.lua` example and may be an alias for `browserCreated`.

### Receiving messages from JavaScript (JS → Lua)

```lua
webview:edQueryCallback(function(query_id, request, persistent)
    -- 'request' is whatever string was passed to window.edQuery({ request: "..." }) in JS
    -- 'persistent' is true if the JS called it with persistent: true
    -- 'query_id' must be echoed back in your reply

    -- Parse the request however you like. Heatblur uses pipe-delimited strings:
    local parts = {}
    for part in request:gmatch('[^|]+') do
        parts[#parts + 1] = part
    end
    local category = parts[1]
    local action = parts[2]
    local value = parts[3]

    -- Send a success response back to the JS onSuccess callback:
    webview:edQuerySuccess(query_id, 'response string here')

    -- Or send a failure:
    -- webview:edQueryFailure(query_id, error_code, 'error message')
end)

-- Optionally handle cancellation (e.g. if the page navigates away mid-query):
webview:edQueryCancelCallback(function(query_id)
    -- query_id was cancelled by the browser
end)
```

### Sending data to JavaScript (Lua → JS)

There is no explicit "push" or "send" method. Instead:
1. Define global functions in your JS: `window.UpdateDisplay = function(state) { ... }`
2. From Lua, build a JSON-serialized state table and call those globals

Heatblur does this from C++ device code, but in a pure-Lua context you would need to use `executeScript` or a similar mechanism if ED exposes one, OR structure your app so JS polls via `edQuery` with `persistent: true`.

---

## JavaScript-Side API

ED injects `window.edQuery` into every page loaded by `WebViewWidget`.

### Sending a message to Lua

```js
window.edQuery({
    request: "category|action|value",  // your string format — anything you agree on
    persistent: false,                  // true = Lua can reply multiple times (streaming)
    onSuccess: function(response) {
        // 'response' is whatever string Lua passed to edQuerySuccess()
        console.log("Lua replied:", response);
    },
    onFailure: function(error_code, error_message) {
        console.error("Lua error:", error_code, error_message);
    }
});
```

### Receiving data from Lua

Define global functions that Lua (or C++ device code) can call:

```js
// Lua/C++ will call this directly when state changes
window.UpdateDisplay = function(stateObject) {
    document.getElementById('myValue').textContent = stateObject.someField;
};

// Heatblur's JesterWheel pattern for replacing menu structure:
window.replaceMenus = function(newMenu, menuLocation) { ... };
```

### Graceful fallback for browser-outside-DCS development

```js
function hb_send_proxy(action, ...args) {
    if (typeof window.edQuery === 'function') {
        window.edQuery({
            request: [action, ...args].join('|'),
            persistent: false,
            onSuccess: function(response) {},
            onFailure: function(error_code, error_message) {}
        });
    } else {
        // Running in a regular browser — log instead
        console.log('edQuery:', action, ...args);
    }
}
```

---

## F-4E HBUI Examples

These are the best available reference implementations. All live under `c:\Games\DCS World\Mods\aircraft\F-4E\UI\`.

### BombingTable — Interactive form → sends data to Jester

The richest example of the pattern: a jQuery/Select2 form where selecting a delivery mode dynamically shows/hides rows, calculations run in JS, and a "Send to Jester" button packages the form values and sends them to the Jester AI via `edQuery`.

**Key files:**
- `BombingTable/index.html` — Full form HTML with `<select>`, `<input>`, section visibility classes
- `BombingTable/js/main.js` — All JS logic: `computeMode()`, `transferTableToJester()`, `window.Set*Result()` receivers
- `BombingTable/js/interface.js` — `hb_send_proxy()` helper wrapping `edQuery`

**Request format:** `"DIRECT|bomb_type|alt|speed|dist|tgt_alt|dive_angle"`
**Lua→JS for results:** `window.SetCcrpResult(release_range_ft)`, `window.SetLabsResult(pull_up_timer_s)`, etc.

### JesterWheel — Radial menu (Pixi.js)

Animated radial/pie menu for selecting Jester AI commands. Uses Pixi.js for WebGL rendering.

**Key files:**
- `JesterWheel/index.html`
- `JesterWheel/js/main.js` — Segment click handlers, menu navigation
- `JesterWheel/js/interface.js` — `hb_send_proxy(category, action, value)`
- `JesterWheel/js/renderer.js` — Pixi.js rendering

**Request format:** `"select|action_name|action_value"`, `"misc|outer_menu_open"`, etc.
**Lua→JS:** `window.replaceMenus(newMenu, menuLocation)` — lets Lua update the available options dynamically

### EFB (Electronic Flight Bag) — Live data dashboard

Tabbed display of engine, fuel, and electrical system data. A static `interface.js` defines the state shape, and Lua pushes state updates by calling `window.UpdateDisplay(state)`.

**Key files:**
- `EFB/index.html` — Tab navigation using an iframe for each sub-tab
- `EFB/main.js` — `loadTab()`, `UpdateDisplay()`
- `EFB/interface.js` — Full state schema definition
- `EFB/engines/`, `EFB/fuel/`, `EFB/electrics/` — Sub-page HTML+JS

**Lua→JS:** `window.UpdateDisplay(stateObject)` called each sim frame

### GreasePencil — Drawing overlay

In-cockpit drawing tool using Pixi.js. Simpler `edQuery` usage — single-string action names.

### VirtualBrowser — Embedded web browser

`VirtualBrowser/index.html` — literally an in-game web browser. Uses the domain whitelist (`hbui_whitelist.txt`) to control which URLs are accessible. This is Heatblur's own feature built on top of `cefLoadUrl`.

---

## Potential DCSAutoMate Applications

- **In-game script selector UI** — replace the current DXGUI overlay with a richer HTML form
- **Real-time status overlay** — push simulation state (waypoints, fuel, gear, weapons) as live-updating HTML dashboard
- **Interactive checklists** — checkboxes that tick off as DCSAutoMate completes steps
- **Configuration forms** — dropdowns, sliders, inputs for script parameters before a sequence runs

---

## Key Differences: Webview-API vs Classic DXGUI

| | Classic DXGUI | Webview-API |
|---|---|---|
| UI defined in | `.dlg` files (Lua tables) | HTML/CSS/JS files |
| Widgets | Predefined set (Button, Static, Grid…) | Any HTML element |
| Styling | Skin tables, textures | CSS |
| State updates | `widget:setText()`, etc. | Call JS global functions |
| User input → Lua | Callbacks (`onChange`, `addMouseDownCallback`) | `window.edQuery()` |
| Rendering | DCS native GPU | Chromium Embedded Framework |
| Dev workflow | Edit `.dlg`, reload DCS | Edit HTML/JS, reload page |

---

## References

- **CEFTest.lua** (ED's minimal example): `c:\Games\DCS World\Scripts\UI\CEFTest.lua`
- **WebViewWidget binding**: `c:\Games\DCS World\dxgui\bind\WebViewWidget.lua`
- **Changelog announcement**: DCS 2.9.23.18431 — search "HBUI" / "Webview-API"
- **F-4E HBUI source**: `c:\Games\DCS World\Mods\aircraft\F-4E\UI\`
