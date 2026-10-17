# Telemetry check, Skip Wait, and blocked sim commands

**Goal:** Started as questions about running automation inside DCS, axis injection, and an autopilot.  Live testing showed that servers blocking player export break telemetry waits and sim commands.  That led to three features on `telemetry-check-skip-wait` (branched from `auto-select`):
- a start-of-script warning and pause when a `LoGet*` function the script waits on doesn't answer;
- a Skip Wait button, in the desktop app and the in-game window, for cockpit-state waits, Loop Until, and timers;
- a warning plus a step-by-step "do it yourself" pause for sim commands on blocking servers.

**What worked:**
- Probing DCS directly over the Export TCP protocol (`G:`, `L:`, `BULKQ`) answered every question in a few calls, including frame-locked injection rates.
- Diffing `BULKQ:scan` before and after an action found the cockpit args for stick and throttle without looking anything up.
- Tacview's "Export rights granted" line in dcs.log showed the host is exempt from its own export restrictions, which explained the confusing first MP test.
- Red/green TDD with a 3 s safety stop in the Skip Wait tests: a broken skip fails instead of hanging the suite.
- Moving uncommitted work onto a new base with `git stash push -- <my files>`, `checkout -B`, `stash pop`.  Only the Hook conflicted, and the user's unrelated uncommitted scripts stayed put.

**What didn't:**
- Branched from `master` as asked, then found `auto-select` had reworked the in-game layout, and that rework was what was installed in DCS.  Had to rebase onto `auto-select` mid-task.  Compare the installed Saved Games files with the branches before choosing a base for Hook/dlg work.
- The first MP test ran on a server the user was hosting, and the host is exempt, so nothing looked restricted.
- Two live runs failed because the mission was paused or not entered: the Export TCP port refuses connections, or accepts and never answers.  Probe once with a raw socket before a full run.
- PowerShell `>` wrote a temp file as UTF-16 and made a diff look binary.  Use Python or `git show ... | Set-Content -Encoding utf8`.
- The edit tool treats blocks that differ only in indentation as the same text, so the two hide-all blocks in the Hook needed an exact-tab Python replace.
- Appending a PowerShell here-string with `Add-Content` writes LF into CRLF files.  Normalize afterwards.
- The test suite's "Windows fatal exception 0xe0000002" comes from `test_ttsManager` (SAPI COM) and is pre-existing.  It looked like a new failure at first.

**Instruction update candidates:**
- "Before changing `Scripts/Hooks` or `.dlg` files, compare the installed copies in Saved Games/DCS/Scripts with the candidate base branch.  The installed Hook may come from an unmerged branch."
- "To test multiplayer export restrictions, join a dedicated server as a client.  The hosting player is exempt from its own server's export settings."
- "If DCS's Export TCP port refuses connections, or accepts and never answers, the mission isn't running or is paused.  Ask the user before retrying."
