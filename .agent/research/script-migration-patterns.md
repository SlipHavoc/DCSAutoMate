# Script Migration Patterns: DCS BIOS → Native

**Date:** 2026-04-18 (updated 2026-04-23)
**Context:** Distilled from the four one-time migration scripts (FA-18C, AH-64D, AV8BNA, Mi-24P) before deleting them. These patterns apply to any remaining module scripts that still use DCS BIOS conventions.

## Bulk alias → canonical rewrite (retired tool)

`tools/rewriteScriptToCanonical.py` was a one-shot used when the alias layer was retired.  The alias files (`config/controlAliases/`) have since been deleted.  Pattern preserved here for reference:

1. Load the then-existing `config/controlAliases/<module>.json`; each entry had a canonical `name` and optional `aliases[]`.
2. Build a dict `{aliasOrCanonical → canonical}` then sort keys by length DESCENDING to avoid prefix collisions (e.g. `HUD_BRT` vs `HUD_BRT_KNB`).
3. For each alias `A` with canonical `C`, replace occurrences of `A` inside quoted string literals only, using regex `(['"/])A(['"])` so bare Python identifiers are untouched.
4. Driven per-script by cross-referencing the script's `moduleName` variable against the matching alias filename.
5. Idempotent — run twice, second pass does 0 substitutions.

Caveats: script strings that reference identifiers NOT present in the alias file (e.g. `ICP_HUD_BRT_KNB` in the F-16C script) will be silently skipped.  Grep the rewritten files for suspiciously SCREAMING_SNAKE literals to catch these.

## Universal Steps (all modules)

### 1. Remove int16() function definition
Every BIOS-era script defined this helper:
```python
# Returns 0-65535 scaled by multiple (0-1), eg for 50% call int16(0.5)
def int16(mult = 1):
	int16 = 65535
	return int(mult * int16)
```
Delete it entirely. It has no equivalent in the native format.

### 2. Replace int16() calls with proportional floats
- `int16()` → `1.0` (full range)
- `int16(X)` → `X` (X is already the proportion, e.g. `int16(0.5)` → `0.5`)
- `-int16()` → `-1.0`
- `int16(0)` → `0`

Regex: `re.sub(r'\bint16\(\)', '1.0', src)` then `re.sub(r'\bint16\(([0-9.]+)\)', r'\1', src)`

### 3. Convert raw int16 values to native floats
When a raw integer appears as a value (not wrapped in int16()), divide by 65535:
- `11141` → `0.17` (11141 / 65535 ≈ 0.17)

### 4. Convert BIOS relative string values to native floats
DCS BIOS used string-format relative commands like `'+3200'` or `'-'+str(int16())`. Convert to native proportional floats:
- `'+3200'` → `0.0488` (3200 / 65535 ≈ 0.0488)
- `'+3000'` → `0.0458` (3000 / 65535 ≈ 0.0458)
- `'-'+str(int16())` → `-1.0` (full negative range)
- `'-100'` → small negative native delta (module-specific; FA-18C SAI_SET used -0.002)

**Key formula:** `nativeValue = biosIntValue / 65535`

### 5. Bulk-replace SCREAMING_SNAKE control names → camelCase
Uses a nameMap JSON (generated during control mapping creation). Sort by length (longest first) to avoid partial matches:
```python
sortedNames = sorted(nameMap.items(), key=lambda x: len(x[0]), reverse=True)
for oldName, newName in sortedNames:
	content = content.replace(f"'{oldName}'", f"'{newName}'")
```

### 6. Update scriptCockpitState path references
These embed control names in path format: `'FA-18C_hornet/BATTERY_SW'` → `'FA-18C_hornet/batterySw'`

### 7. Verification checks
After migration, scan for:
- Any remaining `int16` references in non-comment lines
- Any remaining `'SCREAMING_SNAKE'` quoted strings that look like control names (uppercase + underscore, 4+ chars)

## Module-Specific Lessons

### FA-18C (most complex migration)
- **RADALT_HEIGHT**: Multi-line relative block with `int(int16() * 3 + 8194)` math. Replaced with two simple lines using native relative values (-3.125 for full-off, 0.28 for 28% of one turn).
- **IFEI brightness**: Minimum value was `1000` (BIOS int), became `0.0` (native float).
- **SAI_SET**: Relative values `'-100'`/`'+100'` became `-0.002`/`0.002` (small native deltas).
- **SAI_CAGE**: String `'1'` became integer `1`.
- **pressMfdButton**: Dynamic name construction changed: `'LEFT_DDI_PB'` + `f'_{pbNum}'` → `'leftDdiPb'` + `f'{pbNum}'` (no underscore separator in camelCase).
- **pressUfcButton**: `'UFC_' + cmd` → `'ufc' + cmd.title()` (camelCase concatenation).

### AH-64D
- **Power lever loop**: Had `int(powerLeverIncrement)` wrapping a float value (because int16 returned ints). After migration, the `int()` wrapper needed removal since native values are already floats.
- **scriptCockpitState path**: `'AH-64D/PLT_APU_L'` → `'AH-64D_BLK_II/pltApuL'` (note: module name also changed).

### AV8BNA
- **RWR_VOL raw value**: `11141` → `0.17` (÷65535). This was a case where the script used a pre-computed int16 value directly rather than calling int16().
- **BINGO_SET relative**: `'+3200'` → `0.0488` (÷65535). DCS BIOS string-format relative step.

### Mi-24P
- **Throttle string-concat**: `'-'+str(int16())` was a pattern for "full negative relative". Became `-1.0`.
- **Throttle string relative**: `'+3000'` → `0.0458` (÷65535). Same pattern as AV8BNA BINGO_SET.

### F-15E (2026-05-12)
- **BINGO fuel relative**: `3200` raw int → `0.04884` (÷65535). Control is `FLINST.cmd_3385`, type `relative`. The script loops 40× to set BINGO to ~4000 lbs.
- **`fuelqty_totalizer` (positionMap)**: BIOS used `cmd=3381` with position index. The temp mapping script missed it because positionMap entries store `{deviceId, commandId, value}` per position rather than a top-level `commandId`. Had to look it up by arg number manually. **Always scan positionMap entries when building a BIOS→canonical mapping script.**
- **Device ID mismatch (`R_MIC_SW`)**: DCS BIOS used device 17, canonical uses device 13 for the same arg (1427). Temp mapping script returned `None` for this control. Resolved by searching the controlMapping by arg number directly.
- **MFD button naming**: F-15E uses `Button_01`…`Button_20` (zero-padded, numbered 01–20). Pattern: `device + f'.Button_{int(N):02d}'`. No underscore gap between device prefix and button number.
- **UFC key naming**: F-15E UFC has letter-prefixed keys (`UFC_KEY_A1`, `UFC_KEY_N2`, etc.) and double-underscore keys (`UFC_KEY__7`, `UFC_KEY__0`). Built an explicit `ufcKeyMap` dict in `pressUfcButton()` rather than constructing names dynamically.
- **Dynamic MFD prefixes**: Front seat — `MPD_FLEFT`, `MPD_FRIGHT`, `MPCD_FCENTER`. Rear seat — `MPCD_RLEFT`, `MPD_RLEFT`, `MPD_RRIGHT`, `MPCD_RRIGHT`.

## Key Insight

The int16 convention mapped 0–65535 integers to the 0.0–1.0 native float range. Every conversion follows the same formula: **divide by 65535**. The only tricky cases are:
1. Multi-step relative commands (like RADALT_HEIGHT) where the BIOS value encoded multiple turns
2. Dynamic name construction in code (string concatenation patterns change with camelCase)
3. Controls where the script stored a pre-computed int16 value as a raw integer literal

## Note on positionMap Controls in Mapping Scripts

When writing a BIOS→canonical mapping script (e.g. `tools/temp_build_<module>_map.py`), a lookup by `{deviceId, commandId}` at the top level of the controlMapping will **miss** controls of type `positionMap`. These controls store `{deviceId, commandId, value}` in each position entry rather than at the top level. To find them: iterate all controls and scan the `positionMap` array for matching `{deviceId, commandId}` pairs.
