# Retro: raw commands from keybindings and listened commands, all 22 modules

**Goal:** Fix the raw-command regression (June 10 heuristic dropped real controls like UH-1H `ENGINE_INTERFACE.Button_18`) by deriving raw commands deterministically from DCS's own data, then roll it out to every module.  Along the way: C-130J GUID-named indicators, restore lost `sort_keys` / `incrementalTumb`, fix the CH-47F and AJS37 mappers broken by DCS updates.

## What worked

- **Vertical slice first.**  UH-1H end to end (extract → map → user test in DCS), then F-4E and FA-18C, then CH-47F, then batch the remaining 18.  Each earlier module surfaced one new Lua quirk (`external_profile`, `listen_command`, iCommand globals) before the batch, so the batch itself was uneventful.
- **Separating my changes from DCS drift** by running the committed extractor (`git show HEAD:extract_X.py`).  It settled every "is this change mine?" question in one run (F-4E, CH-47F, AH-64D, F-16C, Mi-24P, AJS37).
- **Anchored one-shot edit script** for 18 near-identical extractors: fail on any anchor that isn't unique, preserve CRLF, verify the diff is insertions only.  Zero manual fix-ups.
- **Filtering the mapping diff to clickable controls.**  Thousands of raw/indicator changes hid the 14 AJS37 IFF changes that actually mattered.
- **Checking the scripts' controls** after every regeneration (`checkScriptControls.py`) caught nothing new, which is the point: it made "no script broke" a checked fact.
- **Reading the Lua factory** for new helpers (`button_and_axis_cyclic`, `multiposition_switch`) before mapping them.  Both matched an existing archetype.

## What didn't

- **A red-phase test hung and ate memory.**  The `external_profile` isolation test reproduced the real OH-58D bug (`join(t, t)` through a shared global), so without the fix it looped forever instead of failing.  The user noticed before I did.  Fix: run lupa tests under `timeout`.
- **`sort_keys` and `incrementalTumb` were silently lost** from the working copy (probably a stale editor buffer saved over the files).  Found only because output ordering changed.  `mappingRegression.py` now guards against that.
- **Text reports broke on names with spaces** (F-16C indicator fields like `ind.4.ALT TRK`), producing a garbage summary.  Compare the JSON directly instead of parsing printed lines.
- **grep `$` anchors on CRLF files** matched nothing in Git Bash, which briefly looked like the extractors had diverged.  Check `file <name>` for line endings first.
- **Decoding mapper output as UTF-8** crashed a reader thread (the mappers print cp1252 text on Windows).  Harmless, but noisy; pass `errors='replace'`.

## Instruction update candidates

- Add to "Use red/green TDD": "When a test exercises code that can loop (Lua sandboxes, parsers, retry logic), run the red phase under a hard timeout (e.g. `timeout 60 python -m pytest ...`) so a hang counts as a failure instead of consuming the machine."
- Add to "Additional instructions": "When a DCS update may have changed a module, run the committed extractor (`git show HEAD:<extractor>`) and compare its output with yours before attributing any extraction change to your own edit."
- Add to `dcsautomate.instructions.md`: "After regenerating a mapping, run `python tools/diffCockpitControls.py <mappingName>` and `python tools/checkScriptControls.py <scriptModule> <mappingName>`.  Raw and read-only churn is expected; any clickable change or unresolved script control needs a look."
