# Delta-only commands (unresolved known-fail category)

## Context

Some DCS cockpit commands are "delta-only": sending the command with
argValue `v` increments the arg by `v` rather than setting the arg to `v`
directly.  These controls must be mapped as `positionMap` rather than plain
`discrete`, because a plain discrete mapping sends the command with the
desired absolute target value (e.g. 0.0, 0.5, 1.0) and the validator expects
the arg to become that value — but a delta command will instead add that
value to the current arg.

## Detection signal

The extraction sub-controls form a single-action `+v/-v` pair:

- `action`   = `[X, X]` (same)
- `argValue` = `[+a, -a]` (opposing signs)

This pattern is **necessary** but **not sufficient** — the same pattern
also appears on ordinary 2-position toggle switches whose commands accept
absolute values fine.

### Reliable secondary signal: symmetric `argLim`

- `argLim` = `[-1, 1]` (or any range straddling 0) → delta-only
- `argLim` = `[0, 1]` → ordinary toggle (command accepts absolute values)

This is how the generator currently distinguishes them (see
`isPositionMapElement` in `tools/generateControlMapping.py`).  It correctly
handles `WEAP-BOMBS-BLOCKS-OP-PTR` (Mi-24P bombs/blocks, argLim=[-1,1]).

## Known unresolved cases (Mi-24P)

These 4 controls appear structurally identical to ordinary toggle switches
in the extraction but are actually delta-only in the simulator.  No signal
in the extraction data distinguishes them:

| Control | Element | Action | argValue | argLim |
|---|---|---|---|---|
| `parkingBrakeHandleArg736` | `STICK-BRAKE-FIX-PTR` | 3027 | [+1, -1] | [0, 1] |
| `pedalDamperArg290` | `PEDAL-DAMPER-COVER-PTR` | 3007 | [+1, -1] | [0, 1] |
| `mainArg217` | `HYDRO-MAIN-SECOND-PTR` | 3001 | [+1, -1] | [0, 1] |
| `mainArg219` | `LANDING-GEAR-MAIN-BACKUP-PTR` | 3003 | [+1, -1] | [0, 1] |

Compare to ordinary toggles that have exactly the same shape but work fine
as discretes (e.g. `CB-RIGHT-FIRE-2-AUTO-PTR` action=3083).

### Also unresolved: `setIArg971` (`ASO2V-SETS-PTR`)

A 4-position selector with `action=[3006]*4`, `argValue=[-0.1, 0.1, 0.2, 0.3]`,
`argLim` varying per sub-control (`[0,0.3]`, `[0,0.3]`, `[0,0.2]`, `[0,0.3]`).
The first sub-control has a negative argValue but no clean symmetric-argLim
signal.  Needs closer look.

## Options for resolution (future work)

1. **Runtime probe tool** — a small script that, for each suspected delta
   control, reads current arg, sends the command with value 0, checks if
   arg changed.  If no change on 0 and change on +/- → delta-only.
2. **Manual override list** — `config/controlOverrides/<module>.json` listing
   element names or arg numbers that should be forced to `positionMap`.
3. **Source inspection** — grep the module's Lua clickables source for the
   command handler logic (e.g. `performClickableAction(3027, ...)` or
   similar) to see whether it treats argValue as absolute or delta.

The user explicitly flagged these as "don't leave behind" and wants to
return to them after the increment-no-effect and range-mismatch categories
are addressed.
