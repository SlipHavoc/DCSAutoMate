@echo off
setlocal
echo Building DCSControlPanel executable...
echo Using virtual environment for consistent dependencies
echo.

REM Change to project root directory
cd /d "%~dp0.."

if exist "DCSControlPanel.exe" (
    echo DCSControlPanel.exe already exists in the root folder.
    choice /c yn /m "Do you want to proceed with the build"
    if errorlevel 2 goto :cancelBuild
)

REM Use a temp work directory to avoid file-lock issues in synced folders (Dropbox/AV indexing)
set "pyiWorkpath=%TEMP%\DCSControlPanel-PyInstaller-Work"

REM Clean previous build
if exist "dist\DCSControlPanel.exe" (
    echo Removing previous build...
    del "dist\DCSControlPanel.exe"
)

REM Best-effort cleanup of prior build artifacts (with retries for transient WinError 32 locks)
call :cleanupDirWithRetry "%pyiWorkpath%" 5 2

REM Build using virtual environment's PyInstaller
echo Building executable...
.venv\Scripts\python.exe -m PyInstaller --workpath "%pyiWorkpath%" DCSControlPanel.spec

REM Wait for PyInstaller to finish writing the EXE (can lag behind stdout)
set "buildWaitSeconds=120"
set "buildWaitCount=0"
:waitForExe
if exist "dist\DCSControlPanel.exe" goto :exeReady
set /a buildWaitCount=%buildWaitCount%+1
if %buildWaitCount% GEQ %buildWaitSeconds% goto :exeNotReady
timeout /t 1 /nobreak >nul
goto :waitForExe

:exeReady

if exist "dist\DCSControlPanel.exe" (
    echo.
    echo ✓ Build successful!
    echo Executable created: dist\DCSControlPanel.exe
    echo File size:
    dir "dist\DCSControlPanel.exe" | findstr "DCSControlPanel.exe"
    echo.
    echo Copying to root folder...
    copy "dist\DCSControlPanel.exe" "DCSControlPanel.exe"
    echo.
) else (
:exeNotReady
    echo.
    echo ✗ Build failed!
    echo Check the output above for errors.
)

echo.
if defined DCSAUTOMATE_NO_PAUSE goto :eof
pause

goto :eof

:cancelBuild
echo Build cancelled.
goto :eof

:cleanupDirWithRetry
set "cleanupPath=%~1"
set "cleanupMaxTries=%~2"
set "cleanupDelaySeconds=%~3"

if "%cleanupMaxTries%"=="" set "cleanupMaxTries=5"
if "%cleanupDelaySeconds%"=="" set "cleanupDelaySeconds=2"

if not exist "%cleanupPath%" exit /b 0

for /l %%i in (1,1,%cleanupMaxTries%) do (
    rmdir /s /q "%cleanupPath%" >nul 2>&1
    if not exist "%cleanupPath%" exit /b 0
    echo Temp build folder is locked; retrying cleanup ^(%%i/%cleanupMaxTries%^)...
    timeout /t %cleanupDelaySeconds% /nobreak >nul
)

echo WARNING: Could not delete "%cleanupPath%". Continuing without cleanup.
exit /b 0
