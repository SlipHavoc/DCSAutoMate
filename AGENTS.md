# Agent Instructions

Instructions for coding agents (Claude Code, Codex, Cursor, GitHub Copilot, ...) working in this repository.  GitHub Copilot reads the first two files below automatically; other agents should read them at the start of every session.

- [.github/copilot-instructions.md](.github/copilot-instructions.md): how to work here (tests first, red/green TDD, the code quality bar, git discipline, retrospectives).
- [.github/instructions/dcsautomate.instructions.md](.github/instructions/dcsautomate.instructions.md): DCSAutoMate specifics (control values, Lua extraction with lupa, what to run after a DCS update).

Knowledge from earlier sessions:

- [.agent/research/](.agent/research/): investigations of DCS internals, extraction and validation techniques, and what didn't work.
- [.agent/decisions/](.agent/decisions/): design decisions and the reasons for them.
- [.agent/retros/](.agent/retros/): session retrospectives.
- [.agent/snippets/](.agent/snippets/): small reusable code examples.
- [todos/](todos/): plans and status of past and current work.

Task-specific agents in [.github/agents/](.github/agents/):

- `module-control-extractor`: extract a module's cockpit controls from its DCS Lua files and generate its control mapping (adding support for a new aircraft starts here).
- `dcsbios-migrator`: convert an old DCS BIOS-format script to the native control names.

Also see [ARCHITECTURE.md](ARCHITECTURE.md), [DEVELOPMENT.md](DEVELOPMENT.md), and [tools/extraction-guides/](tools/extraction-guides/).
