# DCSAutoMate Development Setup

This document explains how to set up a development environment for DCSAutoMate.

## For Users (Simple)

Just download and run the executable: `DCSAutoMate.exe`.

No Python installation required!

## For Developers (Source Code)

### Prerequisites
- Python 3.13.5 (or compatible version)
- Git

### Quick Setup

1. **Clone the repository**
   ```bash
   git clone <your-repo-url>
   cd DCSAutoMate
   ```

2. **Create virtual environment**
   ```bash
   python -m venv .venv
   ```

3. **Activate virtual environment**
   ```bash
   # Windows PowerShell/Command Prompt
   .venv\Scripts\activate

   # Windows Git Bash
   source .venv/Scripts/activate

   # Linux/Mac
   source .venv/bin/activate
   ```

4. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

5. **Run the application**
   ```bash
   # Main application (PySide6-based modern interface)
   python DCSAutoMate.py
   ```

### Building Executables

To create a distributable zip:

```bash
tools\Build_DCSAutoMate.bat
tools\Build_DCSControlPanel.bat
"tools\Make Zip Distribution.bat"
```

The build scripts create `dist\DCSAutoMate.exe` and `dist\DCSControlPanel.exe` (and copy them to the repo root).  The zip script packages both exes with the files they need next to them (`config/controlMappings/`, `config/simCommands.json`, `DCSAutoMateScripts/`, `Scripts/`, `docs/controlReference.html`, README and LICENSE) into `DCSAutoMate-<version>.zip` (the version comes from `utils/version.py`); user settings aren't included.  The exes look for these files in their own folder, so unzip everything into one folder.

### Project Structure

- `DCSAutoMate.py` — Main application (PySide6 GUI)
- `DCSControlPanel.py` — Utility for watching and driving individual cockpit controls, with a Snapshot Tool for finding what changed
- `engine/` — Script execution engine (`DCSSeqExecute.py`, `ScriptManager.py`, `SequenceHelper.py`)
- `network/` — Network managers (`DCSDirectManager.py` TCP client, `DCSAutoMateExportManager.py` UDP receiver, `BaseMulticastReceiver.py`, `UdpWireLogger.py`)
- `utils/` — Config, TTS, and installer helpers (`SettingsManager.py`, `TTSManager.py`, `DcsScriptsInstaller.py`)
- `DCSAutoMateScripts/` — Aircraft-specific automation scripts
- `Scripts/` — DCS-side Lua scripts installed into Saved Games (`DCSAutoMateExport.lua`, overlay hook)
- `config/` — Runtime config plus `controlMappings/` and `nativeExtractions/` per-module data
- `tools/` — Native extraction pipeline (`extract_<module>.py`, `extractUtils.py`, `generateControlMapping.py`), live validator (`validateControlMapping.py`), and build scripts
- `tests/` — pytest suite
- `archive/` — Retired code kept for reference (tkinter/curses GUIs, DCSMonitor, `DCSBIOSExportManager.py`, migration utilities)
- `.venv/` — Virtual environment (not in git)
- `requirements.txt` — Python dependencies
- `DCSAutoMate.spec` — PyInstaller configuration

### Virtual Environment Benefits

- **Isolation**: Dependencies don't conflict with other projects
- **Reproducibility**: Exact same versions as used in development
- **Clean System**: System Python stays unmodified
- **Easy Distribution**: Contributors get identical environments

### Development Workflow

1. Make changes to source files
2. Test with: `python DCSAutoMate.py`
3. Build executables: `tools\Build_DCSAutoMate.bat` and `tools\Build_DCSControlPanel.bat`
4. Test the executables (unzip `DCSAutoMate-<version>.zip` into an empty folder and run them from there)
5. Commit changes (executable not included in git)

### After a DCS Update

Run `python tools/checkDcsUpdate.py`.  It re-extracts every module from the DCS install, regenerates every control mapping, checks every script's controls, and reports what changed compared with git HEAD (only clickable controls are listed for the mappings; raw and read-only changes are expected).  Review the changes with `git diff`, then commit `config/nativeExtractions`, `config/controlMappings` and `config/dcsVersionChecked.json`.

### Publishing a Release

Development happens in a private repo; each release is published to the public repo ([SlipHavoc/DCSAutoMate](https://github.com/SlipHavoc/DCSAutoMate)) as a single commit, so the development history stays private.

One-time setup:
1. Install the GitHub CLI (`winget install GitHub.cli`) and sign in with `gh auth login`.
2. Clone the public repo next to this one: `gh repo clone SlipHavoc/DCSAutoMate "..\DCSAutoMate-Public"`.
3. Create `config/privateTerms.txt` with one private term (e.g. your real name) per line.  Git ignores it, so the list itself is never published.

For each release:
1. Set `APP_VERSION` in `utils/version.py`, update the README heading to match, and add a `## <date> - Version <version>` section to the README's release notes.  Commit.
2. Dry run: `.venv\Scripts\python.exe tools\publishRelease.py`.  It runs the tests, builds both exes and the zip, copies the public files (an allow-list in `publicFiles()`, as committed at HEAD) into the public clone, scans everything for personal information (the private terms, this PC's user name in paths, and email addresses other than the published one, including inside the exes), and runs the tests in the public copy.  Review the file changes and release notes it prints.
3. Publish: `.venv\Scripts\python.exe tools\publishRelease.py --publish`.  After you type the version to confirm, it commits and tags the public repo, pushes, creates the GitHub Release with the zip attached, and tags this repo.

When run from source, DCSAutoMate shows a reminder at startup if the installed DCS version is newer than the one in `config/dcsVersionChecked.json`.

### Dependencies Explained

- **PySide6**: Modern Qt-based GUI framework
- **psutil**: System and process utilities
- **PyDirectInput**: Windows input simulation
- **PyGetWindow**: Window management
- **pywin32**: Windows API access
- **PyInstaller**: Executable packaging

### Troubleshooting

- If activation fails due to execution policy, use: `.venv\Scripts\python.exe` directly
- If builds fail, ensure all dependencies are installed in the virtual environment
- For missing modules, check that virtual environment is activated before installing

## License

MIT License - See LICENSE file for details.
