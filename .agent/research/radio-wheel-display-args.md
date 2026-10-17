# Radio-wheel master/slave display-arg coupling (Mi-8 / Mi-24)

**Date:** 2026-04-26
**Context:** Mi-8 / Mi-24 radio frequency selectors, R-863 channel selectors, JADRO 1A/1I HF radios.
**Commits:** `0abfd5a` (wheel as relative click-count), `841e508` (displayArgs).

## TL;DR

The DCS Lua helpers `radio_wheel_1` and `radio_wheel_double` (defined in
`Mi-8MTV2/Cockpit/Scripts/clickabledata.lua` and `Mi-24P/Cockpit/Scripts/clickable_defs.lua`)
build a clickable element whose **command-pulse arg** (the click counter) is
*different from* the **cockpit-display arg(s)**. Multi-digit displays
chain a **master → slave** spec where the master holds the ones digit and
the slave holds the tens digit, with `master_lim` defining the digit-carry
threshold.

This is unique to the Russian helo modules — F-16C / FA-18C / AH-64D / AV8B / Ka-50_3
do not use this helper or any inlined equivalent.

## The Lua spec shape

`radio_wheel_1(hint, device, command, arg, argValues, argLim, slave, ...)`
returns an element where `slave_animation = {{slave = slave}, {slave = slave}}`
(once per sub-element — wheels always have 2 sub-elements: increment
TUMB and decrement TUMB sharing the same `arg` and `command`).

The `slave` table itself is `{<masterArg>, <range>, <step>, slave = {<slaveArg>, ..., master_lim = {...}}}`
— recursive. The `slave` field on the outer spec carries the chain.

Concrete example — Mi-8 JADRO 1A DIG12 (1 MHz selector, 16 positions 2-17 MHz):
```
elements["PTR-ADDSECPLT-LVR-DIG12"] = radio_wheel_1(
    _("Jadro 1A, Frequency Selector, 1MHz"),
    devices.JADRO_1A,
    device_commands.Button_3,
    745,                                   -- pulse arg (click counter)
    {-0.1, 0.1},
    {0.0, 1.0},
    {751, {0.0, 1.0}, 1.0,                 -- master display arg = ones digit
        slave = {750, {0.0, 1.0}, 1.0,    -- slave display arg = tens digit
            master_lim = {0.9, 1.0},
        },
    }
)
```

Live verification (2026-04-26): clicking + on this control advances arg
751 in 0.1 increments through 16 positions; when 751 wraps from 1.0 → 0.0,
arg 750 advances by 0.1 (digit-carry).

`radio_wheel_double` is the same pattern but for 4 sub-elements (two
2-button wheels sharing one element); each wheel has its own `slave_animation`
spec — sub-elements 1-2 share `slave1`, sub-elements 3-4 share `slave2`.

## Why this matters

The pulse arg is **a click counter**, not a position. Reading it back via
`get_argument_value` returns the cumulative click count (which itself is
in `argLim` cycle terms, not human-meaningful), not the visible cockpit
state. Scripts that need "is the radio set to 9.5 MHz?" must read the
display arg(s), not the pulse arg.

We previously didn't surface display args anywhere — they were only
visible if you read `clickabledata.lua` directly. After 0abfd5a we modeled
wheels as `type: 'relative', wheel: True` (signed click counts on send),
but readback was still hitting the pulse arg, which is useless.

## Capturing it via lupa (no regex)

Critical: do not text-parse `clickabledata.lua`. The `slave_animation`
field is on the returned element table — walk it via `lupa`:

```python
def extractSlaveAnimation(element, numSubElements):
    out = []
    sa = element.slave_animation
    if sa is None or lupa.lua_type(sa) != 'table':
        return [[] for _ in range(numSubElements)]
    for i in range(1, numSubElements + 1):
        entry = sa[i]
        chain = []
        if entry is not None and lupa.lua_type(entry) == 'table':
            spec = entry.slave
            while spec is not None and lupa.lua_type(spec) == 'table':
                argEntry = spec[1]
                if argEntry is None:
                    break
                chain.append(int(argEntry))
                spec = spec.slave    # follow the chain recursively
        out.append(chain)
    return out
```

Lives in [tools/extractUtils.py](../../tools/extractUtils.py). Both
`extract_Mi8MTV2.py` and `extract_Mi24P.py` call it from
`extractElements()` and emit `slaveAnimation` only when at least one
sub-element has a non-empty chain.

## Schema flow

- **Native extraction** (`config/nativeExtractions/Mi-8MTV2.json`,
  `Mi-24P.json`): per-element `slaveAnimation: [[<chain1>], [<chain2>], ...]`
  aligned with sub-element index.
- **Control mapping** (`config/controlMappings/Mi-8MT.json`, `Mi-24P.json`):
  per wheel control `displayArgs: [<master>, <slave>, ...]` (flat list,
  master first). Only emitted when chain ≠ `[arg]`.
- **Dispatcher** (`network/DCSDirectManager.getControlState`): when wheel
  control has `displayArgs`, default arg-read uses `displayArgs[0]`.
  Send path is unchanged (still pulses the cmd arg by ±incrementValue /
  decrementValue).
- **DCSControlPanel WheelCard**: debug row shows pulse + every
  displayArg, each labeled with its arg id, all live-polled via a
  `<ref>#extra:<arg>` synthetic-key side channel from PollWorker.

## Population census (Mi-8MT + Mi-24P)

Mi-8MT (8 wheel controls):
- `R_863.PTR_APP_LVR_SEL1..4` — channel digit selectors, displayArgs `[157]` / `[158]` / `[159]` / `[160]`.
- `JADRO_1A.PTR_ADDSECPLT_LVR_DIG12` — 1MHz, displayArgs `[751, 750]` (master/slave digit-carry).
- `JADRO_1A.PTR_ADDSECPLT_LVR_DIG3` — 100kHz, displayArgs `[752]`.
- `JADRO_1A.PTR_ADDSECPLT_LVR_DIG4` — 10kHz, displayArgs `[753]`.
- `JADRO_1A.PTR_ADDSECPLT_LVR_DIG6_arg748` — 1kHz (radio_wheel_double), displayArgs `[754]`.

Mi-24P (5 wheel controls): JADRO 1I frequency selectors, including one
master/slave pair `[434, 435]` mirroring DIG12.

## Things that mislead

- "displayArg singular" — the chain can be longer than 1 (currently
  observed: 1 or 2). Always model as a list. `displayArgs[0]` is the
  master / most-significant.
- "displayArgs vs `_arg{N}` siblings on `radio_wheel_double`" — these are
  orthogonal concepts. The double-wheel produces *two* `_arg{N}` siblings
  (one per direction-pair). Each sibling gets its own displayArgs sub-list
  via `slaveAnimation[incIdx]` indexed by sub-element. Don't conflate
  multi-element compound controls (already split into siblings) with the
  display-arg-separate-from-pulse-arg phenomenon (only Mi-8 / Mi-24).
- "F-16C compound rotaries" — they don't need displayArgs. Their
  multi-element compound controls are already split into siblings during
  generation (see decisions/canonical-alias-naming.md).
