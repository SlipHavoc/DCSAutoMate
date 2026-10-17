# Decision: Unified Control Mapping Format (Clean Break from DCS BIOS)

**Date:** 2026-04-15
**Status:** Planned (implementation not yet started)
**Scope:** Control mapping JSON format, DCSDirectManager, FA-18C script, value conventions

---

## Context

DCSAutoMate originally depended on DCS BIOS for all cockpit communication. Phase 1–5 of the `eliminate-dcs-bios` branch replaced the transport layer (UDP multicast → direct TCP), but the data formats, naming conventions, type system, and value conventions still mirror DCS BIOS's architecture:

- **biosMappings JSON** uses DCS BIOS's separate `commands` and `stateReads` dicts, even though a physical control is one object with both send and read capabilities.
- **14+ biosType values** (`definePushButton`, `defineToggleSwitch`, `defineTumb`, `define3PosTumb`, `defineMultipositionSwitch`, `defineRotary`, `definePotentiometer`, `defineToggleSwitchToggleOnly`, `defineVariableStepTumb`, `defineFixedStepTumb`, `defineMultipositionSwitchWithCycle`, `defineEjectionHandleSwitch`, `defineSetCommandTumb`, `defineToggleSwitchManualRange`) when there are only 3 fundamentally different behaviors.
- **int16 value convention** (0–65535 for continuous controls) requiring runtime translation to/from native floats.
- **SCREAMING_SNAKE_CASE control names** inherited from DCS BIOS, including typos (`COCKKPIT_LIGHT_MODE_SW`).
- **nativeControls JSON** as a build artifact that gets embedded as a `native` sub-dict inside the BIOS-structured biosMappings — the BIOS format is the container, native data is the passenger.

This architectural coupling means DCS BIOS continues to influence design decisions even though it's no longer the transport layer. Since DCSAutoMate 2.0 hasn't shipped yet, now is the time for a clean break.

## Decision

Replace the entire biosMappings format with a **unified control mapping** format:

### 1. Single flat `controls` dict (no commands/stateReads split)

A control's capabilities are determined by field presence:
- Has `type` + `deviceId` + `commandId` → commandable
- Has `arg` → readable by argument query
- Has `indicationId` + `fieldName` → readable by indication query
- A control can have any combination of these

### 2. Three control types (not 14)

| Type | Behavior | Script value | Runtime translation |
|---|---|---|---|
| `continuous` | Potentiometers, axes, dimmers | Native float (e.g., `0.5`) | Clamp to `argLim` |
| `discrete` | All switches and buttons (2-pos, 3-pos, N-pos, push) | Position index (0, 1, 2…) | `argLim[0] + step × index` |
| `relative` | Rotary encoders | Increment float | Passthrough via `S:` command |

Push buttons are 2-position discrete controls (step=1.0, positions=2, argLim=[0,1]).

### 3. Native float values in scripts (no int16)

Scripts send `0.5` directly, not `int16(0.5)` = `32768`. The `int16()` helper is removed.

### 4. camelCase naming

Control names derived from DCS Lua `hint` text, converted to camelCase. BIOS naming typos fixed.

### 5. Module name from DCS

`moduleName` = whatever `LoGetSelfData().Name` returns (e.g., `FA-18C_hornet`). Same value DCS BIOS happened to use, but the source of truth is DCS itself.

## Alternatives Considered

### Keep biosMappings with BIOS naming (rejected)
- Pro: Zero script changes, backward compatible
- Con: Perpetuates BIOS architectural influence, carries dead weight (14 types, int16, commands/stateReads split), makes future modules harder (would need to invent fake BIOS names for modules BIOS never supported)

### Keep int16 convention, change everything else (rejected)
- Pro: Less script churn (only name changes, not value changes)
- Con: int16 is a BIOS artifact with no benefit — it adds a runtime translation step and makes scripts harder to read. If `0.5` means 50% brightness, the script should say `0.5`, not `32768`.

### Derive names from hint text algorithmically (chosen, with manual review)
- Pro: Names come from the authoritative source (DCS itself)
- Con: Hint text sometimes includes mouse button instructions like "(RMB)UP/(LMB)DOWN" that need to be stripped. Manual review catch needed.

## Consequences

- **All non-FA-18C aircraft scripts break** until individually converted (accepted — they'll be done in Phase 7)
- **DCSDirectManager method names change**: `sendBiosCommand()` → `sendControl()`, `_lookupCommand()`/`_lookupStateRead()` → `_lookupControl()`, etc.
- **Test fixtures need updating** for the new JSON format
- **Migration tool needed** to convert existing biosMappings → controlMappings (one-time use per aircraft)
- **Future modules** can be generated directly from `extractControlsLupa.py` output without ever touching DCS BIOS

## Related Files

- `todos/replace-dcs-bios.md` — Phase 6 describes the full implementation plan
- `.agent/research/dcs-native-control-types.md` — Research confirming the 3 fundamental control behaviors
- `config/biosMappings/FA-18C_hornet_bios_mapping.json` — Current format being replaced
- `config/nativeControls/FA-18C_hornet_native.json` — Build artifact (kept)
