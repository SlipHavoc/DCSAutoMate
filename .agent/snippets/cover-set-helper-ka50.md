# coverSet() — Absolute-Set Helper for Toggle Covers

Some Ka-50_3 cockpit covers are `animated_guard_switch` type: **any command value toggles the cover** rather than setting it to a specific state. To make startup scripts idempotent (safe to run from any initial cockpit state), use this helper instead of bare `pushSeqCmd`.

## Pattern

```python
def coverSet(name, targetValue):
    fullName = f'Ka-50_3/{name}'
    pushSeqCmd(0, 'scriptLoopUntilStart', control=fullName, condition='=', value=targetValue, maxIterations=1)
    pushSeqCmd(dt, name, 1) # Toggle (value ignored by toggle covers).
    pushSeqCmd(0, 'scriptLoopUntilEnd')
```

`scriptLoopUntilStart` / `scriptLoopUntilEnd` wrap a block that only executes if the condition is NOT yet met. So the toggle is only sent if the cover is currently NOT at `targetValue`. The `maxIterations=1` prevents an infinite loop if the cover doesn't move (fails silently rather than hanging).

## Usage

```python
# Open cover, flip switch, close cover:
coverSet('ELEC_INTERFACE.ENERG-COVER-AKK1-PTR', 1)  # open
pushSeqCmd(dt, 'ELEC_INTERFACE.ENERG-AKK1-PTR', 1)  # switch on
coverSet('ELEC_INTERFACE.ENERG-COVER-AKK1-PTR', 0)  # close

# EKRAN cover — leave open after flipping switch:
coverSet('CPT_MECH.P-CONTR-VMG-HYDRO-COVER-PTR', 1)  # open (leave open)
pushSeqCmd(dt, 'CPT_MECH.P-CONTR-VMG-HYDRO-PTR', 0)  # switch
```

## Notes

- The module prefix in `fullName` must match the `moduleName` used by `scriptLoopUntilStart` — for Ka-50_3 that is `'Ka-50_3'`.
- For Ka-50 (original), change the prefix to `'Ka-50'`.
- **Do not** use raw `pushSeqCmd(dt, coverName, 1)` for these covers in startup scripts. Because the toggle fires on every command regardless of value, a bare call is state-dependent and will misbehave if the cockpit isn't in the expected initial state.
- The same pattern applies to any other module that uses `animated_guard_switch`-style covers.
