# Retro: Mi-24P radar altimeter knob and Lua nil holes in extraction

**Goal:** The user noticed that DCSControlPanel shows the Mi-24P `RADAR_ALTIMETER.ROTARY` as continuous 0–1, while in the cockpit it turns endlessly like the F/A-18 radar altimeter knob, and asked to check it in a running cold Mi-24P.

## What worked

- **Probing the live arg with `tools/live-testing/diagControl.py`** settled it in one run: `C:12:3001:<v>` adds `v` to arg 30 and wraps mod 1.0 (+0.05 from 0.953 → 0.003; +1.0 → no change).  It is a relative knob, the same as the F/A-18 `ID2163A_SetMinAlt`.
- **Reading the extraction JSON before the generator.**  The element had no `relative` key at all, which pointed straight at `luaTableToList` rather than at `classifyType`.
- **Grepping all installed modules for `{nil,` tables** showed the scope (stop_action on F-15E/F-4E/C-130J, gain on UH-1H) before choosing between a Mi-24P-only fix and a fix for every extractor.
- **Moving the function first, unchanged, into `extractUtils`** so that the red phase was a genuine assertion failure, not an import error.
- **One parametrized test over all 22 `extract_*.extractElements`** with a synthetic `elements` table caught each copy of the post-processing at once.
- **Auditing real extractions by wrapping each module's `luaTableToList`** listed exactly which fields have holes in DCS 2.9.30, so only those fields' `None` handling was changed.

## What didn't

- **The first fix shifted data instead of dropping it.**  Keeping holes as `None` while the extractors still filtered `None` out of `arg` moved the F-15E mirror's arg 10 from the LEV onto the BTN.  Reviewing the regenerated mapping diff caught it, not the tests.  Any list indexed per sub-control must map `None` to a neutral value, never filter it.
- **Test methods named `testFoo` were not collected**: `pytest.ini` sets `python_functions = test_*`.  The repo uses `test_camelCase`.
- **`python tools/checkDcsUpdate.py --help` runs the whole update** (no argparse).  Harmless here because the DCS version hadn't changed, but it writes the extraction and mapping files.
- **`validateControlMapping.py` opens and re-closes guards by default**, which touches the user's cockpit.  Use `--no-open-guards` when checking a single non-guarded control in someone's live session.

## Instruction update candidates

- Add to `dcsautomate.instructions.md`: "Lua tables in DCS clickable definitions can have `nil` holes (`relative = {nil, true}`, `arg = {nil, 10}`).  Keep per-sub-control lists index-aligned: map `None` to a neutral value, never filter it out.  See `.agent/research/lupa-native-extraction.md`."
- Add to `dcsautomate.instructions.md`: "After changing an extractor, regenerate with `python tools/checkDcsUpdate.py` and read the mapping diff entry by entry; the tests don't cover what real DCS Lua produces."
