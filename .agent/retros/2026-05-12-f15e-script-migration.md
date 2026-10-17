# Retrospective: F-15E Script Migration (BIOS → Canonical)

**Date:** 2026-05-12
**Branch:** eliminate-dcs-bios

---

## Goal

Migrate `DCSAutoMateScripts/F-15E_dcsbios.py` to `F-15E.py` using canonical native control names from the validated `config/controlMappings/F-15ESE.json`. Covers Cold Start, Hot Start, Air Start, Shutdown, Load Route, and Load Scratchpad.

---

## What Worked

- **Mapping script approach:** Writing `tools/temp_build_f15e_map.py` to cross-reference DCS BIOS source files against the controlMapping JSON gave a complete and accurate BIOS→canonical table before touching the script. This is the right workflow for modules with large numbers of controls.
- **MFD button pattern:** The F-15E uses numbered button suffixes (`Button_01` through `Button_20`) with zero-padding. Deriving this from the controlMapping JSON (rather than guessing) avoided errors.
- **UFC key map:** Building a complete inline `ufcKeyMap` dict in `pressUfcButton()` (rather than string-constructing canonical names) made the rewrite clean and auditable.
- **positionMap control (`fuelqty_totalizer`):** Passing position index directly works correctly — the DCSDirectManager translates index → positionMap value internally. No special handling needed in the script.
- **Relative control (`FLINST.cmd_3385` BINGO fuel):** `3200 / 65535 ≈ 0.04884` is the correct native delta. The existing loop of 40 × delta is preserved as-is.
- **`int16()` removal was mechanical:** Once the value semantics were clear (1.0 for full deflection, proportion for partial), all substitutions were straightforward.

---

## What Didn't Work / Complications

- **`F_FUEL_TOTAL` / `fuelqty_totalizer` missing from mapping script:** The temp mapping script only looked up controls by `{deviceId, commandId}` pairs. `fuelqty_totalizer` is a `positionMap` type — it has multiple `{deviceId, commandId, value}` entries, one per position. The simple lookup missed it. Had to find it manually by grepping the controlMapping JSON for the arg value. **Lesson:** When building a BIOS-to-canonical mapping script for future modules, also scan positionMap entries.
- **`R_MIC_SW` device ID mismatch:** DCS BIOS used device ID 17 for this control but the native extraction uses device 13 for the same arg (1427). The temp mapping script returned `None`. Resolved by looking up the arg number directly in the controlMapping. The FIXME comment on this control is preserved since it was already in the original script.
- **`ARC_210_RADIO` and `F_BH_ARMSAFE_OVER`:** These had no match in the controlMapping. They appear to be DCS BIOS synthetic controls with no native equivalent. Left as FIXME comments (though they don't appear in the main script body — only referenced in the commented-out `Test` function scaffolding).
- **Session compaction mid-task:** The full mapping work was done in a prior session that hit the token limit. The summary captured the complete BIOS→canonical table accurately enough to write the migrated file from scratch in the next session without re-running any tools.

---

## Instruction Update Candidates

1. **positionMap lookup in mapping scripts:** When writing a temp BIOS→canonical mapping script, include a second pass that scans `positionMap` entries for matching `{deviceId, commandId}` pairs — not just the top-level `deviceId`/`commandId` fields.

2. **Confirmed pattern — position indices pass through unchanged:** For the fifth time across multiple modules, BIOS position indices (0, 1, 2...) and canonical positionMap indices resolved to the same cockpit-visible states. No value adjustment needed when migrating discrete position values.
