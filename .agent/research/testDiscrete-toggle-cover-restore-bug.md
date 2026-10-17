# testDiscrete — Toggle Cover Restore Bug

**Date:** 2026-04-30
**Branch:** eliminate-dcs-bios

## Problem

`validateControlMapping.py::testDiscrete` sweeps a discrete control through every position, then tries to restore it to its initial value by sending `performClickableAction(sock, deviceId, commandId, initialNative)`.

For controls using the `animated_guard_switch` type (most toggle covers in the Ka-50_3), **sending any value toggles the cover regardless of the value sent**. So if the sweep happened to leave the cover at `initialNative`, the unconditional restore send would flip it *away* from that state — producing a false failure on the next test that uses that cover.

## Fix

Read the current arg value first; only send the restore command if the arg is not already at `initialNative`:

```python
currentNative = queryArg(sock, arg)
if currentNative is None or not valuesMatch(currentNative, initialNative):
    performClickableAction(sock, deviceId, commandId, initialNative)
    waitForStable(sock, arg, delay)
```

## Affected modules

Any module with `animated_guard_switch` covers. Confirmed on Ka-50_3 (18 failures → 8 after the fix). The remaining 8 failures are unrelated edge-cases (not cover double-flip).

## Key insight

The guard is essential for *any* toggle-type control (not just covers): if the control is already at the target state, a send will take it *away* from that state.
