# Sibling control validation failures — root causes and structural limits

## What siblings are

Sibling controls (`_EXT`, `_ITER`, `_AXIS`) are synthesised entries added to the control mapping by `emitSiblingControls()` in `generateControlMapping.py`. They correspond to commands defined in `command_defs.lua` that are NOT referenced by `clickabledata.lua` — i.e. commands that are only reachable via keyboard binding, DCS BIOS, or joystick input.

- **`_ITER`** (increment): keyboard-style commands that step a multi-position switch by ±1 click. sendProtocol `S:` (SetCommand). Used by DCS BIOS rotary protocol.
- **`_AXIS`** (joystick axis): analog joystick commands with argLim `[-1.0, 1.0]` mapping to the full cockpit range. sendProtocol `C:` (PerformClickableAction, absolute). argLim may be inverted vs readback (`readbackArgLim`).
- **`_EXT`** (external): catch-all for the remaining non-clickable commands. Treated as discrete `positionMap` entries. sendProtocol `C:` (absolute).

## Zero-delta TUMB no-op — the fundamental `_EXT` failure mode

Many cockpit switches use the `default_3_position_tumb` (and `springloaded_3_pos_tumb`, `springloaded_2_pos_tumb2`) class in clickabledata.lua. These switches operate on **delta semantics**: DCS adds the sent value to the current arg rather than setting it absolutely.

The `_EXT` sibling computes the value to send as:
```
value = argLim[0] + step * posIndex
```

For any switch where `argLim[0] + step * posIndex = 0.0`, sending that value is a **no-op** — DCS interprets 0.0 as "no movement."

### Known failures from FA-18C validation run 11

| Control | argLim | step | Problem position | Computed delta |
|---|---|---|---|---|
| `EXT_LIGHTS.Strobe_EXT` | [-1.0, 1.0] | 1.0 | pos 1 (middle) | -1.0 + 1.0*1 = **0.0** |
| `CMDS.Dispenser_EXT` | [0.0, 1.0] | 0.1 | pos 0 (start) | 0.0 + 0.1*0 = **0.0** |

`Strobe_EXT` positions 0 (delta −1.0) and 2 (delta +1.0) pass. Only the zero-delta position fails.

`Dispenser_EXT` is additionally affected by a second, independent issue (see below).

### Why this can't be fixed

The zero-delta is structural. The `_EXT` positionMap encodes absolute-looking values but the underlying command uses delta semantics. To correctly set the switch to position 1, the correct value to send depends on the **current state** of the switch — you'd need to know where you're coming from and compute `target_pos - current_pos` steps. That's exactly what `_ITER` does — and `_ITER` siblings already exist for most of these switches.

There is no way to set a TUMB-class switch to an absolute position via a single `C:` command when any target position evaluates to 0.0.

## BIOS input commands — the `_EXT` commandId failure mode

Some commands in `command_defs.lua` appear in an `-- input commands` section (added by DCS BIOS). These commands have commandIds that DCS **silently ignores** unless DCS BIOS is loaded and intercepts the socket traffic.

`CMDS.Dispenser_EXT` uses commandId 3004 (`cmds_commands.Dispenser_EXT`) — a BIOS input command. The base clickable `Dispenser` uses commandId 3001. Without BIOS, every call to commandId 3004 is a silent no-op regardless of value.

### Detection method

In `command_defs.lua`, scan for the comment `-- input commands`. Any commandId in that section below the comment is BIOS-only. Example:

```lua
-- input commands (from DCS BIOS)
["Dispenser_EXT"] = {device_commands.Button_3004, ...},
```

The generator currently does NOT skip these. Post-elimination this is moot. If siblings were ever reinstated, `emitSiblingControls` should skip commands sourced from BIOS input sections.

## Spring-loaded switch `_EXT` failures

Spring-loaded switches (`springloaded_2_pos_tumb2`, `springloaded_3_pos_tumb`) physically return to center when released. Their `_EXT` siblings have a `positionMap` derived by reverse-lookup from the base switch's positionMap — but the simulation still spring-loads back to center after any non-center command, so the validator sees the arg at center instead of the commanded position.

`HookBypass_EXT` and `ModeSw_EXT` fail for this reason (same as the base non-sibling `HookBypass`).

## Scale of the sibling problem (FA-18C hornet)

| Metric | Value |
|---|---|
| Total controls in mapping | ~756 |
| Sibling controls (`inferred: true`) | 212 |
| `_EXT` siblings | 110 |
| `_ITER` siblings | 56 |
| `_AXIS` siblings | 46 |
| Sibling share | ~28% |
| Generator lines dedicated to siblings | ~186 (lines 942–1128 in emitSiblingControls) |
| Validator lines dedicated to siblings | ~92 (testInferredCycleDiscrete + readbackArgLim branch + routing) |
| Generator tests dedicated to siblings | 13 of 19 |
| Sibling controls referenced at runtime | **0** |

## Why siblings were built

The original motivation was the AH-64D SAI cage knob: `SAI.CageKnobRotate_ITER` is the only DCS BIOS protocol that reliably rotates the SAI without desync. The `_ITER` suffix was needed to distinguish it from the base absolute command. Rather than hand-adding it, the decision was made to synthesize all siblings automatically.

This was the right call at the time — but the validation work revealed that the synthesis is more expensive to maintain than the runtime value it provides, and that many of the synthesised controls have unfixable structural failures.

## The two valid uses that survive elimination

1. **SAI cage knob**: The startup script uses `SAI.CageKnobRotate` (base command, Option B — explicit pull-in staging). This is unaffected by sibling removal. `SAI.CageKnobRotate_ITER` was an alternative; removing it has no effect on shipped scripts.

2. **DCSControlPanel step slider**: The `_defaultStep()` method looked up `siblingOf` to inherit a step size for rendering. Post-elimination this lookup is removed; controls provide their own `step` field or fall back to the existing defaults.

## Decision

See `.agent/decisions/eliminate-sibling-controls.md`.
