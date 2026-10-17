# Release 2.0.0

Publish DCSAutoMate 2.0.0 to the public repo (SlipHavoc/DCSAutoMate) as a GitHub Release, without the private development history.  Feature freeze: 2.0 = `master` as of 2026-10-14 plus release prep only.

Each public release is one snapshot commit plus a `vX.Y.Z` tag, made by `tools/publishRelease.py` from an allow-list of tracked files.  The private repo keeps the full history and gets the same tag.

## Decisions

- Public repo contents: app source, `tools/` (including validation results and the DCS BIOS migration tools), `tests/`, and the development knowledge so forks can carry on with an AI agent: `.agent/`, `todos/`, `.github/` agent instructions and custom agents, and a root `AGENTS.md` pointing to them.  Not published: `archive/`, `keyboard tests/`, the M-2000C WIP and `test.py` scripts, `tests/manual_*`, and root clutter (`DCS BIOS bugs.txt`, PySide6 summaries, `baseline.json`, the `.code-workspace`).  The zip stays minimal.
- DCSMonitor is retired (moved to `archive/`); DCSControlPanel replaces it.
- Single-file exes stay unless Defender/VirusTotal flag them.
- No personal information may be published.  Every release scans the public files, the zip and the files inside both exes, against generic rules plus an untracked private-terms file (`config/privateTerms.txt`).
- Version in one place (`utils/version.py`), shown in window titles.
- The existing public HEAD is tagged `v1.0.0` before 2.0 replaces it.
- README gets screenshots of the desktop app and the in-game overlay.

## Status

| Step | Status |
|---|---|
| Branch `release-2.0` | Done |
| Remove personal info from tracked files | Done (tests use a neutral user; A-4E-C extraction writes %USERPROFILE%) |
| Retire DCSMonitor | Done (archive/DCSMonitor) |
| Version number in titles and zip name | Done |
| Antivirus check (Defender, VirusTotal) | Defender: no threats.  VirusTotal: 3/~70 (DCSAutoMate) and 4/~70 (DCSControlPanel) generic/ML detections (Bkav, CrowdStrike, SecureAge, Arctic Wolf); accepted as PyInstaller false positives, single-file exes kept |
| Screenshots | Done (docs/screenshots; reviewed, no personal info or PNG text metadata) |
| README / LICENSE / DEVELOPMENT.md for 2.0 | Done; user to review wording and the release date |
| Publish filter + personal-info scanner (pure, tested) | Done |
| GitHub CLI installed, `gh auth login`, public clone | Done (`..\DCSAutoMate-Public`); public history scanned clean (14 commits, 7 exe/zip versions) |
| Tag public v1.0.0 | Already existed: tag and "DCSAutoMate 1.0.0" Release with the v1 zip |
| Publish script | Dry run OK against the real public clone (250 files, scan clean, 1510 tests pass in the public copy); --publish untested |
| Hide Test scripts (CH-47F, F-16C, F-4E, F-86F) | Done |
| Public repo settings | Pending, at publish time (Wiki and Projects off; description still mentions DCS BIOS) |
| Clean-folder and in-game test of the zip | Done on a second PC (two Saved Games folders detected, install, Auto Select, FA-18C Cold Start).  Found: hook logging defaulted on before install; fixed |
| Publish 2.0.0 | Pending |
| Merge to `master`, tag private `v2.0.0`, retro | Pending |
