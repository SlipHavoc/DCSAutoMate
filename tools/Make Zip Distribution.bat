@echo off
setlocal
rem
rem Makes DCSAutoMate-<version>.zip: the two exes and the files they need next to them.  Build both exes first
rem (tools\Build_DCSAutoMate.bat and tools\Build_DCSControlPanel.bat).
rem User-specific config (settings, saved choices) isn't included; the programs create it on first run.
rem

set "repoRoot=%~dp0.."
set "stageDir=%repoRoot%\build\zipStage"

pushd "%repoRoot%" >nul 2>&1

set "appVersion="
for /f "usebackq delims=" %%V in (`.venv\Scripts\python.exe -c "from utils.version import APP_VERSION; print(APP_VERSION)"`) do set "appVersion=%%V"
if not defined appVersion (
	echo ERROR: Could not read APP_VERSION from utils\version.py.
	goto :failed
)
set "zipName=DCSAutoMate-%appVersion%.zip"
set "zipFile=%repoRoot%\%zipName%"

for %%F in (DCSAutoMate.exe DCSControlPanel.exe) do (
	if not exist "dist\%%F" (
		echo ERROR: dist\%%F not found.  Build it first.
		goto :failed
	)
)

echo Staging files...
if exist "%stageDir%" rmdir /s /q "%stageDir%"
mkdir "%stageDir%\config" "%stageDir%\docs"

copy /y dist\DCSAutoMate.exe "%stageDir%" >nul || goto :failed
copy /y dist\DCSControlPanel.exe "%stageDir%" >nul || goto :failed
copy /y README.md "%stageDir%" >nul || goto :failed
copy /y LICENSE "%stageDir%" >nul || goto :failed
copy /y config\simCommands.json "%stageDir%\config" >nul || goto :failed
copy /y docs\controlReference.html "%stageDir%\docs" >nul || goto :failed

rem Robocopy exit codes below 8 mean success.
robocopy config\controlMappings "%stageDir%\config\controlMappings" *.json /njh /njs /nfl /ndl >nul
if errorlevel 8 goto :failed
robocopy DCSAutoMateScripts "%stageDir%\DCSAutoMateScripts" *.py /xf test.py "M-2000C*" /njh /njs /nfl /ndl >nul
if errorlevel 8 goto :failed
robocopy Scripts\DCSAutoMate "%stageDir%\Scripts\DCSAutoMate" /njh /njs /nfl /ndl >nul
if errorlevel 8 goto :failed
robocopy Scripts\Hooks "%stageDir%\Scripts\Hooks" /njh /njs /nfl /ndl >nul
if errorlevel 8 goto :failed

echo Creating %zipName%...
del /q "%zipFile%" >nul 2>&1
7z a -tzip "%zipFile%" "%stageDir%\*" -mx9 >nul || goto :failed
del /q "%zipFile%.tmp*" >nul 2>&1
echo Done: %zipFile%
popd >nul 2>&1
goto :done

:failed
echo Zip not created.
popd >nul 2>&1

:done
rem Keep the window open after we're done.  Pass any argument to skip.
if "%~1"=="" (
	pause
)
