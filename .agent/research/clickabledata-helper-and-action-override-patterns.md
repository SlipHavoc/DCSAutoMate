# clickabledata.lua — helper composition and `.action` override patterns

**Date:** 2026-04-26
**First encountered on:** Ka-50 Blackshark II (BSII)
**See also:** `.agent/research/dcs-native-control-types.md` (taxonomy of factory functions)

Two patterns in DCS `clickabledata.lua` cannot be resolved by inspecting the *returned element* alone — the generator needs information from the *calling site* (which helper built the element, or whether `.action` was overwritten).  Both patterns surfaced during the Ka-50 conversion and required generator changes; they almost certainly recur in other legacy modules.

---

## Pattern A — Helper-composed elements (e.g. `animated_guard_switch`)

Some clickabledata helpers compose a more abstract element (a continuous range, an axis, etc.) into something that semantically *is* a different control type.  The most common case is a **cover/guard**:

```lua
function animated_guard_switch(hint, dev, cmd, arg, ...)
    -- builds an element whose argLim spans many small steps
    -- so the cover animates smoothly when clicked
end
```

The returned element looks structurally like a continuous range — there is no `class_type.TUMB`, no obvious 2-position shape — so a structural classifier emits it as a 101-position pseudo-discrete (the default fallback for argLim with many steps).  But semantically it is a 2-position cover.

### Fix: helper tagging

`tools/extractUtils.py` defines `HELPER_NAMES_TO_TAG = ('animated_guard_switch',)` and `installHelperTagger(lua, ...)` which wraps each named global helper so every element it returns receives a `_helper = '<helperName>'` field.  The extractor copies that field into the JSON output as `helper`.

`tools/generateControlMapping.py::detectBinaryToggle` reads `elem.get('helper') == 'animated_guard_switch'` and emits a clean 2-position discrete (positions 0 and 1) regardless of the underlying argLim shape.

To extend this pattern to a new helper:

1. Add the helper name to `HELPER_NAMES_TO_TAG` in `extractUtils.py`.
2. Re-run `tools/extract_<module>.py` so the helper field appears in the native extraction JSON.
3. Add a detector + emit branch in `generateControlMapping.py` keyed off `elem.get('helper') == '<helperName>'`.

The helper tag survives across re-extractions (it is part of the JSON schema) and is queryable from the mapping generator without re-parsing Lua.

### Modules currently affected
- **Ka-50 BSII:** 22 elements have `helper='animated_guard_switch'` (all covers/guards on the cockpit).

---

## Pattern B — `.action` override on multi-position rotaries

A handful of clickabledata elements call a standard helper (`multiposition_switch` or `default_3_position_tumb`) and **then overwrite `.action = {cmdA, cmdB}` post-construction** so each direction maps to its own device command.  The post-override structural shape is:

- 2 sub-controls of class `TUMB`
- Same `arg` index on both
- **Different** action command IDs
- Symmetric `argValue = {-step, +step}`
- `argLim` spans more than one step (multi-position rotary)

### Why DCS does this

The override exists purely for **keybinding ergonomics** — DCS lets keybinds target a single `(deviceId, commandId, value)` triple, so giving each cockpit-arrow clickspot its own command lets them be bound to separate keys.

### Critical semantic: device handlers are absolute-set, not relative-step

The DCS clickabledata TUMB handler universally computes `clamp(currentArg + argValue, argLim[0], argLim[1])` and dispatches that **new absolute position** to the device command.  The device handler is "set state = value", not "step by sign(value)".  This is independent of whether `.action` was overridden — both commands have identical absolute-set semantics; they differ only in the keybind they collect.

Verification: the Ka-50 keyboard input file (`Mods/aircraft/Ka-50/Input/ka-50/keyboard/default.lua`) binds the same single command (e.g. `Button_26`) to absolute `value_down = 0, 0.1, 0.2, …, 0.6` for every position of `PVI_SWITCH_PTR`.  One command alone can drive the rotary across its entire range.

### Wrong fixes we considered

1. **Emit as a 3-entry positionMap** (the previous default for 2-action rotaries).  Wrong because positionMaps assume springloaded behavior — the rotary then only had {dec, neutral, inc} reachable, not all N positions.
2. **Emit as a "wheel" with separate inc/dec command IDs.**  Live-tested on the Ka-50 PVI knob: sending `+0.1` repeatedly is "set to 0.1" repeatedly, so the knob got stuck at position 1.  Confirmed device commands are absolute-set, not step.

### Correct fix — single-command N-position discrete

`tools/generateControlMapping.py::detectDualCommandRotary` matches the structural shape above and returns `(incIdx, decIdx)`.  The emit branch builds a normal multi-position discrete using `actions[incIdx]` (the positive-argValue command) and `step = abs(argValues[incIdx])`, with `positions = round((argLim[1] - argLim[0]) / step) + 1`.

Detection is purely structural — no helper-tag lookup needed — so it covers both the `multiposition_switch` and `default_3_position_tumb` override variants.

### Discriminator vs. legitimate 2-command springloaded switches

A 2-command springloaded switch has the same "2 TUMB / same arg / different actions / symmetric argValue" shape, but its `argLim` spans **exactly ±|argValue|** (one step in each direction from neutral).  The override-pattern rotaries span many steps.  So the test:

```python
range_ = argLim[1] - argLim[0]
if range_ > abs(argValue) + epsilon:  # multi-step → override pattern
```

is the discriminator.  Springloaded switches continue through the existing positionMap path.

### Modules currently affected
- **Ka-50 BSII:** 5 controls — `PVI.PVI_SWITCH_PTR` (7-pos), `WEAP_INTERFACE.PVR_MODE_PTR` (5-pos), `UV_26.UV26_BOARD_PTR` (3-pos), `NAV_INTERFACE.GYRO_MAG_MAN_HEADING_PTR` (3-pos), `FIRE_EXTING_INTERFACE.FIREEXT_PTR` (3-pos).

Other legacy modules (Mi-8, Mi-24P, Ka-50_3) likely have similar overrides — re-run validation after their next regeneration to confirm.

---

## Architectural principle: keep mappings 1:1 with native Lua

When considering a fix, prefer the option that keeps `config/nativeExtractions/<module>.json` and `config/controlMappings/<module>.json` faithful to what the DCS module's Lua actually exposes — even if that means more work in startup scripts.

- Do **not** invent synthetic command IDs at the mapping layer.
- Do **not** add synthetic UI affordances at the DCSControlPanel layer (e.g. fake `+`/`−` step buttons that pretend a discrete is a wheel).
- Do **not** call `iCommand*` engine-layer abstractions.  They are not reachable via `performClickableAction(deviceId, commandId, value)` — only the device-button command IDs are.

Synthetic per-control conveniences (relative knob stepping, multi-press macros, debounced presses, etc.) belong in `DCSAutoMateScripts/*.py` startup scripts on an as-needed basis.  The Python scripting engine there is fully expressive and does not require any cross-module mapping changes.
