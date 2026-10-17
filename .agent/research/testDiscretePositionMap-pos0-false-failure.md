# testDiscretePositionMap — Position 0 False Failure

**Date:** 2026-04-30
**Branch:** eliminate-dcs-bios

## Problem

`testDiscretePositionMap` commanded each mapped position in order and checked whether the cockpit arg changed. The logic was:

```python
if valuesMatch(preNative, postNative):
    failures.append(f'pos {i}: arg unchanged at {postNative:.4f}')
```

This produces a **false failure for position 0** if the cockpit starts up with the control already at its position-0 state (e.g. arg = 0.0, which is the default for most discrete controls). Commanding position 0 correctly does nothing — the arg was already right — but the old logic flagged it as a failure because the arg didn't change.

## Fix

Only fail if the arg didn't change AND wasn't already at the commanded value before the send:

```python
elif valuesMatch(preNative, postNative) and not valuesMatch(preNative, value):
    failures.append(f'pos {i}: arg unchanged at {postNative:.4f}')
```

(`value` here is the native float being commanded for position `i`.)

## Scope

This affects any positionMap control whose position 0 maps to the cockpit's startup-state arg value — which is the majority of discrete controls. The fix eliminates spurious pos-0 failures without masking real ones (if the arg genuinely didn't move to a non-zero position that's still a failure).
