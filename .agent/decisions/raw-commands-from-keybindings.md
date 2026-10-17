# ADR: Raw commands come from keybindings and listened commands

**Date:** 2026-09-26
**Branch:** `map-scripts-arch`
**Status:** Accepted
**Supersedes in part:** `reintroduce-raw-controls.md` (which commands become raw; the raw type itself is unchanged)

## Context

`reintroduce-raw-controls.md` emitted a raw entry for every command-table entry with no clickable element.  Command tables are shared (one `device_commands` table used by many devices), so the generator had to guess which device each command belonged to.  The June 10 heuristic (bce61f5) tied each shared command to a single device, which silently dropped real controls such as UH-1H `ENGINE_INTERFACE.Button_18` (starter) and produced pairs no device actually handles.

## Decision

A `(deviceId, commandId)` pair becomes a raw control only if DCS itself says a device handles it:

1. **Keybindings.**  Every `Input/<profile>/{keyboard,joystick,mouse}/default.lua` binding with a numeric `cockpit_device_id`.  Bindings for the same pair are merged into one entry with a `bindings` list (name, values, sources).  One command can have many bindings told apart by value (UH-1H `ELEC_INTERFACE.Button_18` covers 61 circuit breakers).
2. **Listened commands.**  Pairs registered with `dev:listen_command()` by scripted devices (`creators[]` entries naming a `.lua` script), limited to `commandId >= 3000` (device command range) and not already covered by a binding.  This catches commands that are scriptable but not bindable, e.g. F-4E `PROXY` 20000–20099 and AJS37 navigation extras.

Pairs that are clickable elements or already mapped controls are skipped.  The names still come from the command tables (`<deviceName>.<cmdName>`), falling back to `cmd_<id>`.  The legacy heuristic is only used when an extraction has no `keybindings` key.

## Why

- **Deterministic.**  No guessing which device owns a shared command; the binding or `listen_command` call names the device.
- **Covers "anything you can bind to a key".**  That's the tool's stated scope.
- **Accepts a few extras.**  A listened command may do nothing useful on its own.  The user prefers a few extra use-at-your-own-risk raw commands over any heuristic that might drop a real control.

## Consequences

- Raw counts drop in most modules (e.g. C-101CC 610 → 194) and rise in some (AH-64D, Mi-8MT, OH-58D).  No control used by any module script was lost.
- Older modules that bind almost everything through simulator `iCommand`s (A-10C, Ka-50) get few raw entries, because those commands have no `cockpit_device_id`.
- The `bindings` list gives script authors the native values to send, which the old ADR could only point to as "go read the Input files".
