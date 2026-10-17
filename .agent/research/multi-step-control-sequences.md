# Multi-Step Control Sequences (positionMap / Spring-Loaded)

## Pattern: Spring-Loaded Rotate + Pull

Some DCS controls combine multiple input types on a single cockpit element. The parking brake handle on the FA-18C is a canonical example:

### FA-18C Emergency/Parking Brake Handle

**clickabledata.lua definition** (pnt_240):
- Index 0: `BTN` (LMB) — `EmergParkHandleSelectPark` — rotate toward PARK, **spring-loaded** (has stop_action)
- Index 1: `TUMB` (RMB) — `EmergParkHandleSelectEmerg` — rotate toward EMERG, **latched** (no stop_action)
- Index 2: `LEV` (MW) — `EmergParkHandleOnOff` — pull/push, **relative**

**Control mapping** splits this into two controls:
- `emergParkHandleSelectPark` — discrete, 3-position positionMap:
  - Position 0: EmergParkHandleSelectEmerg (rotate to horizontal)
  - Position 1: null (release — center/off)
  - Position 2: EmergParkHandleSelectPark (rotate to vertical/park)
- `emergParkHandleOnOff` — relative

### Correct sequences:

**Set brake OFF (stow handle):**
```python
pushSeqCmd(dt, 'emergParkHandleSelectPark', 2)  # Rotate to PARK
pushSeqCmd(dt, 'emergParkHandleOnOff', 1)        # Push in (stow)
pushSeqCmd(dt, 'emergParkHandleSelectPark', 0)   # Rotate to horizontal
```

**Set brake ON (pull handle out in PARK position):**
```python
pushSeqCmd(dt, 'emergParkHandleSelectPark', 2)  # Rotate to PARK
pushSeqCmd(dt, 'emergParkHandleSelectPark', 1)  # Release rotation
pushSeqCmd(dt, 'emergParkHandleOnOff', 0)        # Pull out
```

### Key insight
Position 1 in the positionMap is null (release/center), not "select park." Position 2 is "select park." Always verify positionMap indices against the actual element definition, not assumptions about the physical control.

### Reference
DCS's own autostart sequence in `Macro_sequencies.lua` uses the same rotate → release → pull pattern.
