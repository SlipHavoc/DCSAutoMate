# DCS Native Control Types — Research Findings

**Date:** 2025-04-14
**Aircraft tested:** F/A-18C Hornet
**Scope:** This document records findings from live in-cockpit testing via the DCSAutoMate TCP protocol (port 7780). All findings are verified on the F-18C only. Other modules likely follow the same patterns (they use the same factory functions in `clickable_defs.lua`), but this has NOT been verified yet — there may be module-specific gotchas.

---

## 1. How DCS Control Definitions Work

Each clickable cockpit control in DCS is defined across three Lua files:

### 1.1 devices.lua — Device IDs

Maps symbolic device names to numeric IDs. Each physical system (electrical, engines, lights, UFC, etc.) gets its own device ID.

```lua
devices["ELEC_INTERFACE"]    = 3
devices["CPT_MECHANICS"]     = 7
devices["CPT_LIGHTS"]        = 9
devices["ENGINES_INTERFACE"] = 12
devices["UFC"]               = 25
devices["RADAR_ALTIMETER"]   = 30
devices["AMPCD"]             = 37
devices["INS"]               = 44
```

### 1.2 command_defs.lua — Command IDs

Each device gets its own command table. A `counter()` function auto-increments IDs starting from `start_command` (3000). The counter resets for each device, so command IDs are per-device:

```lua
start_command = 3000
local count = 0
local function counter()
    count = count + 1
    return count
end

count = start_command
engines_commands = {
    APU_ControlSw    = counter();  -- 3001
    EngineCrankLSw   = counter();  -- 3002
    EngineCrankRSw   = counter();  -- 3003
    ...
}
```

**Key takeaway:** To determine a command's numeric ID, count its position in the table. First entry = 3001, second = 3002, etc.

### 1.3 clickabledata.lua — Control Instances

Each cockpit control is created by calling a factory function from `clickable_defs.lua`. The entry in `clickabledata.lua` specifies the factory function, description, device, command(s), and argument number:

```lua
-- Battery switch: 3-position toggle, device 3, command 3001, arg 404
elements["pnt_404"] = default_3_position_tumb(
    _("Battery Switch, ON/OFF/ORIDE"),
    devices.ELEC_INTERFACE, elec_commands.BattSw, 404
)

-- Engine crank: springloaded, device 12, TWO commands (3002 LEFT, 3003 RIGHT), arg 377
elements["pnt_377"] = springloaded_3_pos_tumb2(
    _("Engine Crank Switch, LEFT/OFF/RIGHT"),
    devices.ENGINES_INTERFACE,
    engines_commands.EngineCrankLSw, engines_commands.EngineCrankRSw, 377
)
```

### 1.4 clickable_defs.lua — Factory Functions

The factory function determines:
- **Class** (BTN, TUMB, LEV, MOVABLE_LEV) — the interaction model
- **Element count** — how many sub-controls (most switches have 2: one for each direction)
- **arg_value** — native value sent when activated (the press/step value)
- **arg_lim** — min/max range the argument can reach
- **stop_action / use_release_message** — what happens on release (springloaded behavior)
- **updatable** — whether DCS keeps the arg synced with internal state
- **gain / relative** — for axes/rotaries

These are the properties that determine what values DCSAutoMate must send to control each type.

---

## 2. Control Type Taxonomy and Value Ranges

### 2.1 Summary Table

| Control Type | Factory Function(s) | Values to Send | Example |
|---|---|---|---|
| **Button** (momentary) | `default_button`, `short_way_button`, `push_button_tumb` | 1 = press, 0 = release | UFC buttons, FCS Reset |
| **2-Position Switch** | `default_2_position_tumb`, `default_cover` | 0 or 1 (absolute positions) | Various ON/OFF switches |
| **3-Position Switch** | `default_3_position_tumb` | -1, 0, or 1 (absolute) | Battery SW, Flap SW |
| **Multiposition Switch** | `multiposition_switch`, `multiposition_switch_cl` | 0.0, 0.1, 0.2… up to `delta × (count-1)` | INS knob (8 pos, 0.0–0.7) |
| **Axis / Potentiometer** | `default_axis`, `default_axis_limited` | 0.0–1.0 continuous | CONSOLES Dimmer |
| **Springloaded 2-pos** | `springloaded_2_pos_tumb` | 1 = press, 0 = release (single command) | Various |
| **Springloaded 3-pos** | `springloaded_3_pos_tumb`, `_tumb2` | Two commands; see §3 | Engine Crank, Canopy |
| **AMPCD Switch** | Paired `AMPCD_switch_positive` + `_negative` | Two commands: 1/-1 press, 0 release | AMPCD Night/Day |
| **Rotary Encoder** | `default_button_axis_extended` | Use `SetCommand` (S:) with relative steps | RADALT Height |
| **Hybrid Button+Axis** | `default_button_tumb`, `default_button_axis` | Two commands, one per function | Various |

### 2.2 How Values Are Determined

**The native value range for any control is fully determined by the factory function's parameters.** You do not need to guess or experiment — the Lua definition tells you everything:

1. **arg_value** in the factory function = the increment/press value. For `default_3_position_tumb`, this is `{-1, 1}` by default (one element steps down, the other up).
2. **arg_lim** = the bounds. For `default_3_position_tumb`, this is `{{-1, 1}, {-1, 1}}` — the arg ranges from -1 to 1.
3. For `multiposition_switch`, **count** and **delta** are explicit parameters: `multiposition_switch(..., 8, 0.1)` = 8 positions at 0.1 step intervals, giving values 0.0, 0.1, 0.2, …, 0.7.
4. For axes (`default_axis_limited`), **arg_lim** defaults to `{0, 1}` — a continuous range.

**Critical caveat:** `performClickableAction` (our C: protocol command) sets the arg to an **absolute position**, NOT an increment. So even though `arg_value` in the factory function defines an increment for mouse-click stepping, we send the target value directly.

> **See also:** `.agent/research/clickabledata-helper-and-action-override-patterns.md` covers two patterns where the *calling site* in `clickabledata.lua` matters as much as the factory function — helper composition (e.g. `animated_guard_switch` wrapping a continuous range to make a 2-position cover) and post-construction `.action = {a, b}` overrides on multi-position rotaries.  Both required generator changes during the Ka-50 conversion.

---

## 3. Multi-Command Controls (The Springloaded Problem)

### 3.1 Single-Command vs Multi-Command

Most switches use a **single command ID** with **two TUMB elements** (one for each direction). The two elements share the same command — they just send opposite arg_value increments. With `performClickableAction`, we bypass the element system and set the arg directly, so one command is sufficient.

**Example: Battery Switch** (`default_3_position_tumb`)
```lua
action    = {command, command}    -- SAME command for both elements
arg_value = {-1, 1}              -- element 0 steps down, element 1 steps up
arg_lim   = {{-1, 1}, {-1, 1}}   -- arg range: -1 to 1
```
To control: `C:3:3001:-1` (ORIDE), `C:3:3001:0` (OFF), `C:3:3001:1` (ON) — single command, any value.

### 3.2 Springloaded 3-Position Switches (Two Commands)

`springloaded_3_pos_tumb` and `springloaded_3_pos_tumb2` are fundamentally different. They create **two BTN elements with SEPARATE commands** — one for the negative direction and one for the positive direction:

```lua
function springloaded_3_pos_tumb(hint_, device_, command1_, command2_, arg_, ...)
    -- command1 = negative direction button (e.g., LEFT, CLOSE)
    -- command2 = positive direction button (e.g., RIGHT, OPEN)
    return {
        class     = {BTN, BTN},
        action    = {command1_, command2_},            -- TWO DIFFERENT commands
        stop_action = {command1_, command2_},           -- release sends same command
        arg_value = {val1, val3},                       -- default: {-1, 1}
        arg_lim   = {{val1, val2}, {val2, val3}},       -- default: {{-1, 0}, {0, 1}}
        use_release_message = {true, true},             -- both send release
    }
end
```

**The key discovery:** The value you send via `performClickableAction` must match the element's `arg_value`, NOT simply "1 for press, 0 for release":

| Direction | Command | Press Value | Release Value |
|---|---|---|---|
| Negative (LEFT/CLOSE) | cmd1 | **-1** (matching `val1`) | 0 |
| Positive (RIGHT/OPEN) | cmd2 | **1** (matching `val3`) | 0 |

Sending value 1 to the negative-direction button does **nothing** — the arg stays at 0. This was confirmed by live testing:

```
# ENGINE CRANK SWITCH (springloaded_3_pos_tumb2)
# cmd1 = 3002 (EngineCrankLSw), cmd2 = 3003 (EngineCrankRSw), arg 377

# LEFT: must use value -1 (matching arg_value = -1)
C:12:3002:-1   → arg 377 = -1  ✓ switch moves LEFT
C:12:3002:0    → arg 377 = 0   ✓ springs back to center

C:12:3002:1    → arg 377 = 0   ✗ DOES NOT WORK (val 1 doesn't match arg_value -1)

# RIGHT: value 1 works (matching arg_value = 1)
C:12:3003:1    → arg 377 = 1   ✓ switch moves RIGHT
C:12:3003:0    → arg 377 = 0   ✓ springs back to center
```

Same pattern confirmed for Canopy Control Switch (`springloaded_3_pos_tumb`):
- CLOSE: `C:7:3002:-1` (press), `C:7:3002:0` (release) — works
- OPEN: `C:7:3001:1` (press), `C:7:3001:0` (release) — works
- CLOSE with val 1: `C:7:3002:1` → nothing happens

### 3.3 How to Identify Multi-Command Controls

You can tell from the `clickabledata.lua` entry:

```lua
-- Single command: ONE command reference
elements["pnt_404"] = default_3_position_tumb(_("Battery Switch..."),
    devices.ELEC_INTERFACE, elec_commands.BattSw, 404)
--                          ^^ single command

-- Two commands: TWO command references
elements["pnt_377"] = springloaded_3_pos_tumb2(_("Engine Crank Switch..."),
    devices.ENGINES_INTERFACE,
    engines_commands.EngineCrankLSw, engines_commands.EngineCrankRSw, 377)
--  ^^ cmd1 = negative direction    ^^ cmd2 = positive direction
```

The factory function signature tells you: `springloaded_3_pos_tumb(hint, device, cmd1, cmd2, arg, ...)` takes TWO commands, while `default_3_position_tumb(hint, device, command, arg, ...)` takes ONE.

### 3.4 AMPCD Switches — A Different Pattern

`AMPCD_switch_positive` and `AMPCD_switch_negative` look like springloaded controls but work differently. They're defined as **two separate clickabledata entries** sharing the same arg, each with its own command:

```lua
elements["pnt_177_2"] = AMPCD_switch_positive(_("AMPCD Night/Day, DAY"),
    devices.AMPCD, AMPCD_commands.AMPCD_nite_day_DAY, 177)
elements["pnt_177_1"] = AMPCD_switch_negative(_("AMPCD Night/Day, NGT"),
    devices.AMPCD, AMPCD_commands.AMPCD_nite_day_NGT, 177)
```

Under the hood, `AMPCD_switch_positive` wraps `short_way_button` (single BTN, arg_value = 1, arg_lim = {0,1}) and `AMPCD_switch_negative` is the same but with arg_value = -1 and arg_lim = {-1,0}. Each is a standalone element with its own command — not a multi-element control.

However, for DCSAutoMate's purposes this is NOT relevant as a special case. We tested sending `-1`, `0`, `1` on **either** command and it works on both:

```
C:37:3002:-1   → arg 177 = -1   ✓ held to NIGHT
C:37:3002:0    → arg 177 = 0    ✓ springs back to center
C:37:3002:1    → arg 177 = 1    ✓ held to DAY
```

This works because DCS applies the value to the shared arg regardless of which command fires. The separate positive/negative definitions only matter for mouse-click interaction (which direction the element moves when clicked). From our TCP protocol perspective, either command works for any value.

---

## 4. Continuous vs Discrete Controls

### 4.1 How to Tell from the Lua Definition

**Discrete (stepped) controls** use `multiposition_switch` or `multiposition_switch_cl`, which take explicit `count` and `delta` parameters:

```lua
-- INS Switch: 8 positions, 0.1 step
local INS_sw = multiposition_switch_cl(
    _("INS Switch, OFF/CV/GND/NAV/IFA/GYRO/GB/TEST"),
    devices.INS, INS_commands.INS_SwitchChange, 443,
    8,    -- count: 8 positions
    0.1,  -- delta: step size
    false, 0, 1.5, true
)
-- Valid values: 0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7
```

The `count` and `delta` parameters tell you:
- **Number of positions** = `count` (8)
- **Step size** = `delta` (0.1)
- **Minimum** = `min` parameter (default 0)
- **Maximum** = `min + delta × (count - 1)` = 0 + 0.1 × 7 = 0.7
- **Valid values** = {0.0, 0.1, 0.2, … 0.7}

In the cockpit, the INS knob can only be clicked (not freely rotated), so it jumps from one discrete position to the next. However, if you send a non-step-boundary value via `performClickableAction` (e.g., 0.15), DCS does NOT snap to the nearest valid position — the knob actually moves to the in-between position, which is not normally reachable through the mouse UI. In our testing, sending 0.15 placed the knob visually halfway between positions 0.1 and 0.2. Whether other multiposition switches behave the same way has not been verified.

Note that the click-only (vs freely rotatable) behavior is implied by the control being a `multiposition_switch` rather than an axis — multiposition switches have discrete `count` and `delta` parameters, while axes are continuous. There doesn't appear to be a separate "click-only" flag in the Lua definitions; the distinction is inherent in the factory function choice.

**Continuous controls** use `default_axis` or `default_axis_limited`:

```lua
-- CONSOLES Dimmer: continuous 0.0–1.0
elements["pnt_413"] = default_axis_limited(
    _("CONSOLES Lights Dimmer Control"),
    devices.CPT_LIGHTS, cptlights_commands.Consoles, 413,
    0,     -- default value
    0.15   -- gain (mouse sensitivity, not relevant for TCP)
)
-- arg_lim defaults to {0, 1} — any float from 0.0 to 1.0 is valid
```

There is no `count` parameter — the control accepts any value in the range. Verified by testing:

```
C:9:3001:0.0   → arg 413 = 0.0    ✓ full dim
C:9:3001:0.25  → arg 413 = 0.25   ✓
C:9:3001:0.5   → arg 413 = 0.5    ✓
C:9:3001:0.75  → arg 413 = 0.75   ✓
C:9:3001:1.0   → arg 413 = 1.0    ✓ full bright
```

### 4.2 Summary: Identifying Control Continuity

| Factory Function | Continuous? | How to Read Values |
|---|---|---|
| `multiposition_switch` / `_cl` | **No** — discrete steps | `count` positions, `delta` step size |
| `default_axis` / `default_axis_limited` | **Yes** — any float in range | `arg_lim` gives min/max (default 0.0–1.0) |
| `default_3_position_tumb` | **No** — 3 fixed positions | Always -1, 0, 1 (unless overridden) |
| `default_2_position_tumb` | **No** — 2 positions | Always 0, 1 |
| `default_button` / `short_way_button` | **No** — 2 states | 0 (released), 1 (pressed) |

---

## 5. Command Protocol Behavior

DCSAutoMate communicates with DCS via the export Lua script on TCP port 7780. Two command types are relevant for controlling cockpit switches:

### 5.1 performClickableAction (`C:device:command:value`)

Sets the control argument to an **absolute position**. This is the primary method for all switch and potentiometer controls.

- **Switches**: Value = the exact position (-1, 0, 1 for three-position; 0.0–0.7 for multiposition)
- **Potentiometers/axes**: Value = exact float in the arg_lim range (typically 0.0–1.0)
- **Buttons**: Value = 1 (press) or 0 (release)
- **Springloaded buttons**: Value = arg_value to press (may be -1 or 1 depending on direction), 0 to release

**No clamping**: If you send a value outside the control's arg_lim range, the arg accepts it (no error), but the visual representation clamps to its valid range. The internal arg value may be out of range until a valid value is sent.

**Verified behavior:**
- Sending 2.0 to a 3-position switch → arg reads back as 2.0 but the switch visual is at position 1
- Sending -0.1 to the INS switch (min 0.0) → arg reads back as -0.1 but knob visual stays at 0.0 position

### 5.2 SetCommand (`S:device:command:value`)

Sends a **relative step** to the device. Works for rotary encoders but NOT for potentiometers or axes.

**Works:**
```
S:30:3002:3000     → RADALT height knob rotates clockwise (small step)
S:30:3002:-3000    → RADALT height knob rotates counter-clockwise
S:30:3002:65535    → rotate to maximum
S:30:3002:-65535   → rotate to minimum
```

**Does NOT work:**
```
S:9:3001:3000      → CONSOLES dimmer does NOT respond (use C: instead)
```

The value for SetCommand represents the step magnitude. The scale varies by control — 3000 is a small step for RADALT, while 65535 is the maximum the knob can travel.

### 5.3 Query (`Q:0:arg`)

Reads the current argument value. Note: the `0` is a historical artifact (device 0 = "self" in DCS). The arg number alone determines what is read.

```
Q:0:377   → returns current position of engine crank switch (-1, 0, or 1)
Q:0:413   → returns current value of CONSOLES dimmer (0.0–1.0)
```

---

## 6. Confirmed Test Results

All tests run on 2025-04-14 via `tools/testControlTypes.py`.

### 6.1 Observation Tests (Manual Control, Read Values)

| Control | Factory Function | Arg | Observed Values |
|---|---|---|---|
| BATTERY_SW | `default_3_position_tumb` | 404 | -1 (ORIDE), 0 (OFF), 1 (ON) |
| FLAP_SW | `default_3_position_tumb` | 234 | -1 (FULL), 0 (HALF), 1 (AUTO) |
| INS_SW | `multiposition_switch_cl` | 443 | 0.0 (OFF), 0.1 (CV), …, 0.7 (TEST) |
| ENGINE_CRANK | `springloaded_3_pos_tumb2` | 377 | -1 (LEFT), 0 (OFF), 1 (RIGHT) — springs back |
| CANOPY | `springloaded_3_pos_tumb` | 453 | -1 (CLOSE), 0 (HOLD), 1 (OPEN) — springs back |
| CANOPY position | (animation arg) | 181 | 0.0 (closed) to 1.0 (open) — moves gradually |
| CONSOLES_DIMMER | `default_axis_limited` | 413 | 0.0–1.0 continuous |
| RADALT_HEIGHT | `default_button_axis_extended` | 291 | 0.0–1.0 continuous (rotary part) |
| AMPCD_NIGHT_DAY | `AMPCD_switch_positive/negative` | 177 | -1 (NGT), 0 (center), 1 (DAY) — springs back |
| AMPCD_GAIN | `AMPCD_switch_positive/negative` | 180 | -1 (down), 0 (center), 1 (up) — springs back |

### 6.2 Command Tests (Programmatic Control)

| Control | Type | Protocol | Device | Cmd(s) | Arg | Values Sent | Result |
|---|---|---|---|---|---|---|---|
| INS_SW | multiposition | C: | 44 | 3001 | 443 | 0.0–0.7 | ✓ All 8 positions work |
| CONSOLES_DIMMER | axis | C: | 9 | 3001 | 413 | 0.0–1.0 | ✓ Continuous range works |
| FLAP_SW | 3-pos | C: | 2 | 3007 | 234 | -1, 0, 1 | ✓ All 3 positions work |
| BATTERY_SW | 3-pos | C: | 3 | 3001 | 404 | -1, 0, 1 | ✓ All 3 positions work |
| FCS_RESET | button | C: | 2 | 3003 | 349 | 1, 0 | ✓ Press/release works |
| UFC_1 | button | C: | 25 | 3019 | 111 | 1, 0 | ✓ Press/release works |
| ENGINE_CRANK LEFT | springloaded btn | C: | 12 | 3002 | 377 | -1, 0 | ✓ Press with -1, release with 0 |
| ENGINE_CRANK RIGHT | springloaded btn | C: | 12 | 3003 | 377 | 1, 0 | ✓ Press with 1, release with 0 |
| CANOPY OPEN | springloaded btn | C: | 7 | 3001 | 453 | 1, 0 | ✓ Press with 1, release with 0 |
| CANOPY CLOSE | springloaded btn | C: | 7 | 3002 | 453 | -1, 0 | ✓ Press with -1, release with 0 |
| AMPCD_NIGHT_DAY | AMPCD switch | C: | 37 | 3002 | 177 | -1, 0, 1 | ✓ Single command, all values work |
| RADALT_HEIGHT | rotary encoder | S: | 30 | 3002 | 291 | ±3000, ±65535 | ✓ Relative steps work |

---

## 7. What extractControlsFromDCS.py Captures

The parser already extracts most of what's needed:

| Needed Info | Parser Field | Status |
|---|---|---|
| Device ID | `deviceId` | ✓ Captured |
| Primary command ID | `commandId` | ✓ Captured |
| Secondary command ID | `commandId2` | ✓ Captured (for dual-command controls) |
| Arg number | `arg` | ✓ Captured |
| Control type | `type` | ✓ Mapped from factory function name |
| Value range | `argValue`, `argLim` | ✓ Captured |
| Position count (discrete) | `positions` | ✓ Captured for multiposition switches |
| Step size (discrete) | `step` | ✓ Captured for multiposition switches |
| Description | `description` | ✓ Captured from hint text |

### 7.1 Known Gaps

1. **Springloaded press-value rule**: The parser captures `argValue` (e.g., `[-1, 1]`) and both command IDs, but does NOT explicitly flag that for springloaded controls, the press value sent must match the element's `arg_value`. It would be helpful to add a field like `pressValues: { cmd1: -1, cmd2: 1 }` so DCSAutoMate scripts know what value to send per command without having to know the underlying rule. **Planned enhancement — not yet implemented.**

2. **Continuous vs discrete distinction**: The parser captures `positions` and `step` for multiposition switches but doesn't have a simple boolean like `discrete: true/false`. This could be inferred from the control type but would be more convenient as an explicit field.

3. **SetCommand compatibility**: No field indicates whether a control responds to SetCommand (S:) vs only performClickableAction (C:). From testing, only rotary-encoder-style controls (like `default_button_axis_extended`) respond to S:. This would need to be flagged per control to avoid trial-and-error.

---

## 8. Control Reference Design (Future)

### 8.1 Purpose

Create a lightweight HTML page (similar to DCS BIOS `control-reference.html` but much simpler) that shows only what DCSAutoMate script authors need. No memory addresses, bit masks, or state array offsets.

### 8.2 Needed Fields

For each control, display:

| Field | Source | Example |
|---|---|---|
| **Name** | `description` from parser | "Battery Switch, ON/OFF/ORIDE" |
| **Type** | `type` from parser | threePositionSwitch |
| **Device** | `deviceId` + `deviceName` | 3 (ELEC_INTERFACE) |
| **Command(s)** | `commandId` (+ `commandId2` if present) | 3001 (or 3002/3003 for springloaded) |
| **Arg** | `arg` | 404 |
| **Value Range** | Derived from type + argLim | -1, 0, 1 |
| **Positions** | `positions` + labels if available | 3: ORIDE / OFF / ON |
| **Step** | `step` (for multiposition only) | 0.1 |
| **Protocol** | inferred from type | C: (absolute) |
| **Usage Example** | auto-generated | `C:3:3001:1` → ON |

### 8.3 Layout

- Searchable/filterable by name, device, or type
- Grouped by device (like BIOS groups by system category)
- Each control is a compact card or table row
- Expandable details for multi-command controls showing both commands with press/release values
- Input format: JSON output of `extractControlsFromDCS.py`
- Single self-contained HTML file (inline CSS/JS, no build step)

### 8.4 What's NOT Needed (vs DCS BIOS reference)

- Memory addresses, masks, shift values — we don't read from a state array
- Input interface descriptions (set_state, variable_step, fixed_step) — we only use C: and S:
- Output type/encoding — we read args directly as floats
- Max value 65535 normalization — we use native DCS values

---

## 9. Open Questions

1. **Do these patterns hold across all DCS modules?** The factory functions in `clickable_defs.lua` appear to be shared across modules, but module-specific overrides or custom functions may exist. Needs verification on at least 2-3 other aircraft before assuming universality.

2. **RADALT rotary behavior**: The RADALT knob (arg 291) responds to both `C:` (absolute positioning) and `S:` (relative steps). However, the C: behavior for this specific control (`default_button_axis_extended`) has `relative = true` and `gain = 0.1`, which may mean C: acts as a relative step rather than an absolute set. The S: behavior is confirmed to work well with relative steps. Further testing needed to nail down exact C: semantics for relative-mode axes.

3. **Out-of-range value persistence**: When we send an out-of-range value via C:, the arg accepts it but the visual clamps. Does this cause any downstream issues (e.g., the device logic using the unclamped value)? In testing, sending a valid value afterward restores normal behavior, so this seems safe but worth keeping in mind.

---

## 10. Addendum: Mapping to Unified Control Types (2026-04-15)

The analysis in this document confirms that all DCS factory functions reduce to **3 fundamental control behaviors**, which became the basis for the Phase 6 unified control mapping (see `.agent/decisions/unified-control-mapping.md`):

| Unified Type | DCS Factory Functions | Rationale |
|---|---|---|
| **discrete** | `default_button`, `short_way_button`, `push_button_tumb`, `default_2_position_tumb`, `default_3_position_tumb`, `default_cover`, `multiposition_switch`, `multiposition_switch_cl`, `springloaded_2_pos_tumb`, `springloaded_3_pos_tumb`, `springloaded_3_pos_tumb2`, `AMPCD_switch_positive/negative` | All have finite positions with known values. Push buttons are 2-position discrete (step=1, argLim=[0,1]). Springloaded controls are discrete with auto-release behavior (handled by the script's press/release timing, not the mapping format). |
| **continuous** | `default_axis`, `default_axis_limited` | Accept any float in argLim range. No step/positions concept. |
| **relative** | `default_button_axis_extended` | Rotary encoders. Use `S:` protocol with relative steps. |

Key insight: the distinction between "button", "2-position switch", "3-position switch", and "multiposition switch" is just a matter of how many positions and what the step size is. They all work the same way from the protocol perspective — script sends a position index, runtime translates to `argLim[0] + step × index`.

---

## 11. EXT / ITER / AXIS Command Variants (2026-04-19)

**Aircraft tested:** AH-64D Apache
**Scope:** Findings from debugging the SAI (Standby Attitude Indicator) cage knob, which uses `default_button_axis` — a hybrid BTN + LEV control.

### 11.1 The Three Command Variants

Many controls in `command_defs.lua` define up to three alternate command IDs in addition to the "base" command. These are NOT present in `clickabledata.lua` — they exist only in `command_defs.lua`:

| Suffix | Purpose | Typical consumer |
|---|---|---|
| `_EXT` | External input (hardware panels, DCS BIOS) | External hardware via SetCommand |
| `_ITER` | Iterative/discrete stepping | Keyboard bindings |
| `_AXIS` | Continuous axis input | Joystick axes, sliders |

**Base commands** (no suffix) are used by `clickabledata.lua` for mouse interaction in the 3D cockpit. The suffixed variants are registered as input commands available in the DCS input binding UI (Settings → Controls).

### 11.2 When Base Commands Don't Behave Like You Expect

**The base command may not handle state-machine side-effects that the keyboard/external variants handle for free.** This was discovered with the AH-64D SAI cage knob:

- `sai_commands.CageKnobRotate` (3002) — the base command used by `clickabledata.lua` for mouse-wheel interaction
- `sai_commands.CageKnobRotate_ITER` (3004) — the keyboard/iterative variant

DCS BIOS independently discovered the same issue ([PR #550](https://github.com/DCS-Skunkworks/dcs-bios/pull/550), March 2024): command 3002 was unsuitable for programmatic control, and they switched to 3004.

**Our testing (live-validated 2026-04-25):**
- `C:13:3002:<value>` via performClickableAction → causes device state desync (arg moves but internal state machine is bypassed; mouse interaction is broken afterward)
- `C:13:3004:<value>` via performClickableAction → uncages the SAI but does NOT rotate the knob (wrong protocol for `_ITER`)
- `S:13:3002:<value>` via SetCommand, sent in isolation → knob jumps to bottom immediately, desynced
- **`S:13:3004:<value>` via SetCommand → works correctly.** Knob moves incrementally, no desync, mouse interaction works normally afterward. Auto-pulls the cage knob in (sets `CageKnobPull` arg 620 from 1 → 0) once rotation crosses into the lock zone — this is a state-machine side-effect the keyboard handler performs that the base mouse path does not.
- **`S:13:3002:<value>` via SetCommand, with explicit pull-in staging → also works.** If the script first sends a rotate value ≤ 0.792 (so the knob is in the pull-in zone), then explicitly sends `CageKnobPull = 0`, then sends the final rotate value, the base command can be used directly with no desync. The trade-off: the script has to orchestrate the pull-in cycle manually, since the base path won't auto-pull. Example:

  ```python
  pushSeqCmd(dt, 'SAI.CageKnobRotate', 0.792)  # rotate into pull-in zone
  pushSeqCmd(dt, 'SAI.CageKnobPull', 0)        # manually pull cage knob in
  pushSeqCmd(dt, 'SAI.CageKnobRotate', 0.432)  # rotate to centered position
  ```

**Bottom line:** prefer the `_ITER` sibling for these hybrid controls — it goes through the keyboard input handler in the C++ device code and gets state-machine side-effects (auto-pull, auto-release, etc.) for free. Use the base command only if the script is willing to take responsibility for orchestrating those side-effects itself.

### 11.3 Protocol + Command Combination Matters

The working combination for the SAI was **SetCommand (S:) with the ITER command (3004)**. Neither the base command with S:, nor the ITER command with C:, worked correctly. Both the command ID and the protocol must be correct.

| Protocol | Base cmd (3002) | ITER cmd (3004) |
|---|---|---|
| `C:` (performClickableAction) | Desync | Uncages only, no rotation |
| `S:` (SetCommand) | Jumps to bottom, desync | **Works correctly** |

### 11.4 Value Scaling Is Opaque

The value sent via SetCommand to an ITER command is scaled by the C++ device code. This scaling is NOT exposed in any Lua file:

- `S:13:3004:-1` moves arg 619 by **0.04** per step
- `S:13:3004:-0.75` moves arg 619 by **0.03** per step (matches one mouse-wheel notch)
- The mouse-wheel path uses base command 3002 with `gain = 0.2`, producing 0.03 per notch

The relationship between the ITER value and the actual arg movement is empirical. The `gain` attribute in `clickable_defs.lua` applies only to the base command's mouse-interaction path, not to the ITER variant.

### 11.5 Identifying Controls That Need ITER/EXT Treatment

**Red flags that a control may need a non-base command:**

1. **`default_button_axis` or `default_button_axis_extended`** — hybrid controls combining a button (push/pull) with a lever (rotation). The lever part has complex internal state that may not be properly updated by the base command via external protocols.
2. **Controls with EXT/ITER/AXIS variants in `command_defs.lua`** — if the DCS developers created alternate input paths, the base command may have assumptions about being called from the cockpit mouse interaction path only.
3. **Controls where `performClickableAction` moves the arg but causes behavioral desync** — the arg value changes, but subsequent mouse interaction is broken (stuck until fast-scrolling forces a re-sync). This is the telltale desync symptom.

**Recommendation:** When extracting controls for a new module, cross-reference `clickabledata.lua` with `command_defs.lua` to identify controls that have EXT/ITER/AXIS variants. Flag these for manual testing. Don't assume the base command will work.

### 11.6 The `sendProtocol` Override

To support controls where the `relative` type (which defaults to SetCommand/S:) needs to use performClickableAction/C: (or vice versa), `DCSDirectManager.sendControl()` supports a per-control `"sendProtocol"` field in the control mapping:

```json
{
    "type": "relative",
    "sendProtocol": "C",
    ...
}
```

- `"sendProtocol": "C"` — force performClickableAction regardless of type
- `"sendProtocol": "S"` — force SetCommand regardless of type
- (omitted) — use default behavior based on type (relative → S:, everything else → C:)

**In practice, no shipped mapping currently needs this override.** The SAI `_ITER` sibling is `relative` type, and the default `S:` is exactly what `_ITER` siblings need. The mechanism exists for future edge cases. Note: as of 2026-04-25 the generator deliberately does NOT emit `sendProtocol` on inferred `_ITER` siblings — they fall through to the default — and `preserveExistingSendProtocol` skips inferred entries so a mistaken default cannot be locked in across regenerations.

### 11.7 SAI Cage Knob — Canonical Sibling Configuration

Since the sibling-synthesis work (commit `09772d1`, 2026-04-25), `_ITER` / `_AXIS` / `_EXT` siblings discovered in `command_defs.lua` are emitted automatically as `inferred: true` entries in `<module>.json`, named `<Device>.<Command>_ITER` etc. No hand-curation is required. The AH-64D SAI cage knob ships as:

```json
"SAI.CageKnobRotate_ITER": {
    "type": "relative",
    "deviceId": 13,
    "commandId": 3004,
    "arg": 619,
    "argLim": [-1.0, 1.0],
    "inferred": true,
    "siblingOf": "SAI.CageKnobRotate"
}
```

**Option A — `_ITER` sibling** (cold start, uncage and center from caged position arg 619 = 0.90):
```python
for i in range(15):
    pushSeqCmd(dt, 'SAI.CageKnobRotate_ITER', -0.75)
```

Each step of -0.75 moves arg 619 by 0.03, matching one mouse-wheel notch. 15 steps moves from 0.90 to 0.45 (centered). Auto-pulls `CageKnobPull` (arg 620) from 1 → 0 once rotation enters the lock zone.

**Option B — base command, uncage to center** (live-validated 2026-04-25):
```python
# Standby Attitude Indicator - Uncage and center.
pushSeqCmd(dt, 'SAI.CageKnobRotate', 0.5)  # Rotate knob to center position.
pushSeqCmd(dt, 'SAI.CageKnobPull', 0)      # Push knob in.
```

This is the cleanest absolute-positioning sequence — rotate first to a value inside the pull-in zone (anything ≤ 0.792 works; 0.5 is centered), then push the knob in. No desync, mouse interaction works normally afterward.

**Option C — base command, re-cage** (live-validated 2026-04-25; useful for shutdown scripts):
```python
# Standby Attitude Indicator - Cage.
pushSeqCmd(dt, 'SAI.CageKnobPull', 1)      # Pull knob to cage, and hold.
pushSeqCmd(dt, 'SAI.CageKnobRotate', 0.9)  # Rotate knob to max position (past cage point).
pushSeqCmd(dt, 'SAI.CageKnobPull', 0)      # Push knob in; stays pulled out because rotated past the caged point.
```

This faithfully reproduces what the cockpit state machine does on a manual cage: pull, rotate past the lock detent, release. Leaves the SAI in the caged state with no desync.

**Picking between them:** the `_ITER` path is best when you want incremental stepping that mirrors mouse-wheel behavior. The base-command sequences (Options B and C) are best when you want absolute positioning and are willing to orchestrate the `CageKnobPull` transitions explicitly — they're also the only way to *re-cage* the knob, since `_ITER` only handles the auto-pull-in side of the state machine.

---

## 12. wca_knob — LEV Axis + Springloaded BTN Helper (2026-05-12)

**Source:** F-15E extraction work. First seen on `INTLT.wac_bklt_knob` (warning/caution area backlight knob).

### What it is

A `wca_knob` is a combined clickable element with two sub-controls:
1. A **LEV axis** — continuous brightness knob (e.g. arg range 0.0–0.75)
2. One or more **springloaded BTN commands** — pressing the knob momentarily drives the arg to a higher value (e.g. 1.0 = RESET), then DCS uses `use_release_message` to spring back to the held position automatically.

This pattern is NOT the same as a multiposition switch or a btn-pulse-counter. The BTN portion is a true momentary action with a fixed release value.

### How the generator handles it

The `wca_knob` helper tag (set by `installHelperTagger` in `extractUtils.py`) causes `generateControlMapping.py` to emit **two controls per element**:
- `<name>` — `type: continuous`, `sendProtocol: S`, `argLim: [levMin, levMax]`
- `<name>_reset` (or equivalent BTN cmd name) — `type: discrete`, `argLim: [btnMin, btnMax]`, `step: btnMax - btnMin`, `positions: 2`

### Script usage (F-15E example)

```python
# Set WCA backlight to 50%
pushSeqCmd(dt, 'INTLT.wac_bklt_knob', 0.5)
# Trigger RESET (springs back automatically — no release command needed)
pushSeqCmd(dt, 'INTLT.wac_bklt_knob_reset', 1)
```

### Validated

Live-validated 2026-05-12 on F-15E in DCS: both the continuous axis and the reset BTN pass `validateControlMapping.py`.
