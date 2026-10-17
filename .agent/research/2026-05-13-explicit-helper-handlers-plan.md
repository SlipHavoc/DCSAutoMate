# Plan: Explicit helper-handler architecture for control mapping generation

**Date:** 2026-05-13
**Updated:** 2026-05-14
**Branch:** `map-scripts-arch` (off `eliminate-dcs-bios`)
**Precipitating bug:** A 3-position springloaded switch in UH-1H was mapped as 2-position. Validation passed because validation only tests the positions present in the mapping. The bug was found only because an unrelated cockpit issue prompted manual inspection. **All controls built by the same helper function had the same wrong mapping.**

**Goal:** Catch this class of bug systematically by requiring every clickabledata helper function used in a module to have an explicit handler in the mapping generator. No silent fallback path may produce a complete mapping.

---

## TL;DR

Replace the current monolithic `generateControlMapping.py` (structural inference + a few helper-tag special cases + default fallback) with:

1. **Per-module `tools/map_<module>.py` scripts** — each contains a `HELPER_MAP = { helperName: archetypeFn, ... }` dict that explicitly maps every helper function used in that module's clickabledata to an archetype function.
2. **Shared `tools/mapUtils.py`** — contains all archetype functions and the structural fallback dispatch runner.
3. **Exhaustive helper tagging** — every element in every `nativeExtractions/<module>.json` gets a `helper` field (the name of the Lua factory function that created it).
4. **Per-helper coverage in `validateControlMapping.py`** — validation reports which helpers have >=1 passing test vs. zero.
5. **Retire `generateControlMapping.py`** — once all `map_<module>.py` scripts exist, the old file is deleted.

---

## Background facts (verified during research)

- Per module, ~15-25 distinct factory functions are defined in `clickable_defs.lua` (or inline at the top of `clickabledata.lua` for older modules like UH-1H).
- **Same helper name across modules does NOT imply same behavior.** Examples:
  - FA-18C `default_2_position_tumb(hint, dev, cmd, arg, animation_speed)` vs UH-1H `default_2_position_tumb(hint, dev, cmd, arg)` — different parameter count.
  - `multiposition_switch` parameter order differs between FA-18C and F-16C.
- Per-module Python files (`map_*.py`) handle module-specific behavior naturally — no global registry needed.
- A small fraction of controls (~5-10%) are **raw inline table literals** in `clickabledata.lua` rather than helper calls. These have no helper name. They fall through to the structural fallback path in `mapUtils.py`.
- Helper tagging infrastructure already exists: `tools/extractUtils.py::installHelperTagger`, the `_helper` field on extracted elements, and `HELPER_NAMES_TO_TAG`. Currently selective (6 helpers); this plan makes it exhaustive (all helpers).

---

## Architecture

### Archetype functions (~14, in `tools/mapUtils.py`)

Each archetype takes a normalized element dict and returns a canonical mapping entry. This is where ALL mapping logic lives:

1. **momentaryButton** — type=momentary
2. **twoPositionTumb** — 2-position discrete
3. **threePositionTumb** — 3-position discrete
4. **springloadedTumb** — springloaded discrete (single or dual command; positions derived from class count + stop_action presence + argValue count, NOT from argLim shape)
5. **multipositionDiscrete** — N-position discrete from delta
6. **continuousAxis** — type=continuous
7. **cover** — 2-position with cover metadata
8. **compoundMultiClass** — multi-entry compound control
9. **relative** — type=relative, sendProtocol=C
10. **iter** — ITER protocol
11. **wheelEncoder** — type=relative, wheel=True
12. **dualCommandRotary** — discrete with inc-side command
13. **rotaryWithMomentary** — positionMap with springloaded momentary
14. **pdpCircuitBreaker** — positionMap with sendValue/readbackValue

### Per-module `HELPER_MAP` dict (in `tools/map_<module>.py`)

```python
from mapUtils import momentaryButton, twoPositionTumb, springloadedTumb, runMapping

HELPER_MAP = {
    'default_button':                momentaryButton,
    'default_2_position_tumb':       twoPositionTumb,
    'default_springloaded_3pos_switch': lambda e: springloadedTumb(e, positions=3),
    # ... one entry per helper function used in this module's clickabledata.lua
}

if __name__ == '__main__':
    runMapping('UH-1H', HELPER_MAP)
```

- Every helper used in the module MUST have an entry. Missing = `runMapping` fails loudly.
- Same helper name in different module = different lambda / different archetype call — no conflict.

### Dispatch runner (`mapUtils.runMapping`)

```python
def runMapping(moduleName, helperMap):
    for each element in extraction:
        helper = element.get('helper')
        if helper:
            if helper not in helperMap:
                unhandledHelpers.add(helper)
                continue
            result = helperMap[helper](element)
        else:
            result = structuralFallback(element)  # structural inference for inline tables
        emit(result)
    if unhandledHelpers:
        print error listing each unhandled helper name + element keys
        exit(1)
```

**Key rule:** An unregistered helper = hard failure. No silent fallback for tagged controls.

The structural fallback path is the existing `generateControlMapping.py` dispatch chain, ported to `mapUtils.py`. It handles inline-table controls (those without a `_helper` tag).

---

## Implementation phases

### Phase 1 — Make helper tagging exhaustive

**Files:** `tools/extractUtils.py`, `tools/extract_AH64D.py`, `tools/extract_AV8BNA.py`, `tools/extract_F16C.py`, `tools/extract_F4E.py`, `tools/extract_FA18C.py`, `tools/extract_Mi24P.py`, `tools/extract_Mi8MTV2.py`

Changes to `extractUtils.py`:
1. Remove `HELPER_NAMES_TO_TAG` allowlist.
2. Replace `_INSTALL_HELPER_TAGGER_LUA` with a new static Lua snippet that wraps **all** global function assignments via `__newindex`. Guard: only inject `_helper = fnName` if `type(result) == 'table' and result.arg ~= nil` (the hallmark of a DCS clickable element).
3. Remove `helperNames` parameter from `installHelperTagger` — exhaustive with no configuration.
4. Chains correctly on top of `installCmdAccessLogger`'s existing `__newindex` hook.

Changes to 7 extractors (add `installHelperTagger` call):
- `extract_AH64D.py`, `extract_AV8BNA.py`, `extract_F16C.py`, `extract_F4E.py`, `extract_FA18C.py`, `extract_Mi24P.py`, `extract_Mi8MTV2.py`
- Import `installHelperTagger` and call it after `installCmdAccessLogger`, before loading `clickabledata.lua`.

Acceptance: every module's extraction has a `helper` field on >=95% of elements. The remaining <=5% are inline-table controls.

### Phase 2a — Create `tools/mapUtils.py`

Port all logic from `generateControlMapping.py` into two categories:

**Archetype functions (14 total)** — take an element dict, return a mapping entry. One function per archetype. Each should be clean and independently testable.

**Structural fallback** — port the existing structural detection chain from `generateControlMapping.py:processElements()`. This handles inline-table controls (no `helper` field).

**`runMapping(moduleName, helperMap)`** — the dispatch runner described above.

Also port: `makeCanonicalName`, `buildCommandReverse`, `buildDeviceTableMap`, `buildPositionMap`, `processIndicators`, `processGaugesAndLamps`, `processRawCommands`, `preserveExistingSendProtocol`, `annotateIndicatorArgLim`.

### Phase 2b — Update `tools/validateControlMapping.py` for per-helper coverage

Changes:
1. After loading the control mapping, build a dict of `helper -> [controls]` (from the `helper` field on each mapping entry).
2. After the test run, report: for each helper, count of controls tested, count that passed.
3. Warn prominently (or exit non-zero with `--strict-coverage`) if any helper has zero passing tests.

Note: `helper` field must be stored in `controlMappings/<module>.json` entries too (additive, backward-compatible).

### Phase 3 — Create per-module `map_*.py` scripts (iterative)

Order: UH-1H first (smallest module, freshest bug), then FA-18C, then the rest incrementally.

Per module:
1. Re-run `extract_<module>.py` after Phase 1. Verify `helper` coverage.
2. List all distinct `helper` values in the extraction JSON.
3. Read the module's `clickable_defs.lua` (or top of `clickabledata.lua` for inline-helper modules) to understand each helper.
4. Create `tools/map_<module>.py` with `HELPER_MAP`.
5. Run `python tools/map_<module>.py` -> new `config/controlMappings/<module>.json`.
6. Diff against old mapping. Every difference should be a bug being fixed.
7. Run live validation. Confirm coverage report shows >=1 passing test per helper.

### Phase 4 — Retire `generateControlMapping.py`

Once all 15 modules have `map_<module>.py` scripts and pass validation, delete `generateControlMapping.py`.

---

## Pilot: UH-1H end-to-end verification

The original bug is the acceptance test:
- `default_springloaded_3pos_switch` must map to `springloadedTumb(positions=3)`.
- The old mapping had this as 2-position (a bug). The new mapping will have 3 positions.
- Diff should show ONLY the springloaded switch controls changing.
- Live validation: `default_springloaded_3pos_switch` controls should get >=1 passing test.

---

## Files to create / modify

| File | Action | Purpose |
|---|---|---|
| `tools/extractUtils.py` | Modify | Exhaustive helper tagging (Phase 1) |
| `tools/extract_AH64D.py` etc. (x7) | Modify | Add `installHelperTagger(lua)` call |
| `tools/extract_*.py` (all 14) | Re-run | Regenerate extractions with full tagging |
| `tools/mapUtils.py` | Create | Archetype functions + structural fallback + `runMapping` |
| `tools/map_Uh1H.py` | Create | UH-1H pilot: `HELPER_MAP` + entry point |
| `tools/map_FA18C.py` etc. | Create (x14) | Per-module mapping scripts |
| `tools/validateControlMapping.py` | Modify | Per-helper coverage report |
| `config/nativeExtractions/*.json` (all) | Regenerate | `helper` on every element |
| `config/controlMappings/*.json` (all) | Regenerate | Output of new per-module scripts |
| `tools/generateControlMapping.py` | Delete (Phase 4) | Retired once all modules migrated |

---

## Known risks / things the implementer should watch for

1. **Helper-name overload.** Same name in different modules = potentially different behavior. Always read the helper source in that module's `clickable_defs.lua`. Do NOT assume same name = same archetype.

2. **Inline-table controls.** The structural fallback in `mapUtils.py` handles these. They do not need a `HELPER_MAP` entry.

3. **Helpers wrapping helpers.** The outermost wrapper's name wins as `_helper` (because `__newindex` fires when the outermost function is DEFINED as a global). This is the correct behavior.

4. **UH-1H has no separate `clickable_defs.lua`.** Helpers are inline at the top of `clickabledata.lua`. The exhaustive `__newindex` hook handles this: it fires for every new global function assignment, regardless of which file defines it.

5. **Don't relax tests.** A previously-passing control that now fails = the new mapping may be wrong. Investigate before changing the mapping.

6. **Additive schema change.** Adding `helper` to `controlMappings/<module>.json` entries is backward-compatible: `DCSAutoMate.py` ignores unknown fields.

7. **`STRUCTURAL_FALLBACK` (= `None` in `HELPER_MAP`) is exclusively for anonymous inline table elements** — controls written as raw table literals in `clickabledata.lua` with no factory function, which therefore have no `helper` tag. Every named helper, no matter how simple its output, must have an explicit archetype entry in `HELPER_MAP`. Using `STRUCTURAL_FALLBACK` for a named helper is an error: it hides the helper from any future per-helper coverage checks and allows silent regressions if the helper's shape ever changes. Confirmed during FA-18C Phase 3: `default_movable_axis` was initially mapped to `STRUCTURAL_FALLBACK` on the mistaken belief that `continuousAxis` couldn't handle `MOVABLE_LEV` elements; it was corrected to `continuousAxis` once verified that `continuousAxis` hardcodes `'LEV'` to `classifyType` and never reads the element's class.
