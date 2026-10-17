# DCS Export Hook Chaining and LuaExportActivityNextEvent

**Date:** 2026-04-16
**Source:** Debugging UDP telemetry failure during Lua script merge

## The Problem

DCS loads Lua export scripts sequentially. If two scripts both define `LuaExportActivityNextEvent` as bare globals, the second definition silently overwrites the first. There's no warning or error — the first script's periodic callback simply never fires.

## DCS Export Hook Chaining Pattern

```lua
local PrevLuaExportActivityNextEvent = LuaExportActivityNextEvent
function LuaExportActivityNextEvent(t)
    -- Your logic here...

    -- Chain to previous handler.
    if PrevLuaExportActivityNextEvent then
        PrevLuaExportActivityNextEvent(t)
    end

    return t + 0.05  -- Next callback time.
end
```

The `local Prev*` capture must happen **before** the new function definition on the very next line. This works because Lua evaluates the right-hand side of the local assignment before creating the new global.

## Critical Constraint: Single Return Value

`LuaExportActivityNextEvent` returns a single timestamp — the next time DCS should call this hook. If two subsystems need different frequencies (e.g., TCP subscriptions at 20 Hz and UDP telemetry at 1 Hz), they **cannot** use separate chained hooks with different return values. Only the outermost return value is used by DCS.

**Solution:** Use the fastest frequency as the return value, and manage slower intervals with internal timers:

```lua
function LuaExportActivityNextEvent(t)
    processSubscriptions(t)  -- 20 Hz (runs every call)

    -- UDP telemetry at ~1 Hz using internal timer.
    if t - lastTelemetrySendTime >= 1.0 then
        sendTelemetry()
        lastTelemetrySendTime = t
    end

    if PrevLuaExportActivityNextEvent then
        PrevLuaExportActivityNextEvent(t)
    end
    return t + 0.05  -- 20 Hz base rate.
end
```

## All Four DCS Export Hooks

| Hook | Purpose | When called |
|---|---|---|
| `LuaExportStart()` | Initialize (open sockets, files) | Mission load |
| `LuaExportStop()` | Cleanup (close sockets) | Mission end |
| `LuaExportBeforeNextFrame()` | Per-frame processing | Every DCS frame |
| `LuaExportActivityNextEvent(t)` | Periodic processing | At time `t` (self-scheduled) |

All four should use the Prev* chaining pattern. `LuaExportBeforeNextFrame` and `LuaExportStop` don't return values. `LuaExportStart` doesn't either.

## DCS's Global `log` Object

DCS provides a global `log` object (used as `log.write('DCSAutoMate', log.INFO, msg)`). Do NOT shadow it with a local function named `log()`. Use a different name like `logToFile()` for custom file logging.
