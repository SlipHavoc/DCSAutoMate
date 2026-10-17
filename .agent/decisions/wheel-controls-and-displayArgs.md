# Decision: model wheels as `type: relative, wheel: True` with optional `displayArgs`

**Date:** 2026-04-26
**Commits:** `0abfd5a`, `841e508`
**Status:** Shipped, live-validated in Mi-8 and Mi-24.

## Context

The DCS `radio_wheel_1` / `radio_wheel_double` helpers (Mi-8 / Mi-24 only)
produce clickable elements with two semantic peculiarities:

1. **Two TUMB sub-elements share one (arg, command).** They differ only
   by argValue sign: clicking one sends `+0.1`, the other sends `-0.1`.
   The cockpit interpretation is "rotate one notch CW" / "one notch CCW";
   there is no provision to seek to an absolute position.
2. **The pulse arg is a click counter, not a visible position.** The
   actual cockpit display lives on a separate "master" arg, optionally
   coupled via `slave_animation` to one or more "slave" args for digit
   carrying on multi-digit displays (e.g. JADRO DIG12: master=ones,
   slave=tens).

See `.agent/research/radio-wheel-display-args.md` for the full Lua spec
shape.

## Decision

### Modeling

- Wheel controls emit as `type: 'relative', wheel: True`.
- Script-convention value is a **signed integer click count**: positive →
  CW (increment) clicks, negative → CCW (decrement). 0 = no-op.
- `incrementValue` / `decrementValue` carry the per-click argValue (signed).
- `argLim` is preserved on the control (for documentation / cycle range).
- New optional field: `displayArgs: [int, ...]` — a flat list of cockpit
  display args, master first, slaves in chain order. Only emitted when
  chain is non-empty AND not equal to `[arg]` (the pulse arg).

### Send path (`DCSDirectManager._sendWheelCommand`)

Unchanged from `0abfd5a`: pulse the `commandId` `abs(value)` times in the
direction implied by sign. This matches cockpit reality — the cockpit
state machine is responsible for translating clicks into display-arg
movement, including digit carry.

### Read path (`DCSDirectManager.getControlState`)

When `wheel: True` and `displayArgs` is present, default arg-query reads
`displayArgs[0]` (the master). Falls back to `arg` (pulse arg) otherwise.
This gives scripts the visible cockpit position by default. Scripts that
explicitly want the pulse arg or a slave arg use `arg.<N>` direct addressing.

### UI (DCSControlPanel WheelCard)

Debug row shows pulse + every displayArg, each labeled with its arg id
(e.g. `arg.745=0.4 · arg.751=0.3 · arg.750=0.0`), all live-polled. The
"Current:" label is driven by `displayArgs[0]` when present (via the
default getControlState path). Side-channel queries route through
`PollWorker` → synthetic `<ref>#extra:<arg>` payload keys → `card.updateExtraArg`.

## Alternatives considered

- **`displayArg` (singular int) instead of a list.** Rejected because
  master/slave chains exist (DIG12, Mi-24 1I). Introducing a separate
  `slaveDisplayArg` field would split a single conceptual chain across
  two parallel structures — annoying for the dispatcher and the UI to
  walk. List is uniform.
- **Capture display args by re-parsing `clickabledata.lua` text via
  regex.** Rejected per repo policy ("use lupa whenever possible, not
  regex"). The `slave_animation` field is on the returned element table,
  walkable via lupa with no source-text knowledge. Implementation lives
  in `extractUtils.extractSlaveAnimation` and recursively follows the
  `.slave` chain.
- **Drop the pulse arg from controlMappings entirely once we have
  displayArgs.** Rejected — the validator and DCSControlPanel both want
  to show the pulse counter for debugging, and scripts may legitimately
  want to read it via `arg.<N>` direct addressing.
- **Treat each displayArg as a separate sibling control (like `_AXIS` /
  `_ITER`).** Rejected because slave args are not independently
  controllable — they are a passive readout coupled to the master via the
  cockpit's digit-carry machinery. Exposing them as siblings would imply
  writability that doesn't exist.

## Invariants

- `displayArgs` only appears on wheel controls (`wheel: True`).
- When present, `displayArgs[0] != arg` (otherwise it would be redundant
  and is not emitted). Slaves may equal `arg`? No — never observed; would
  indicate a malformed slave_animation entry if it happened.
- Generator output: only Mi-8MT.json and Mi-24P.json contain
  `displayArgs` entries. F-16C / FA-18C / AH-64D / AV8B regenerate
  byte-identical.
