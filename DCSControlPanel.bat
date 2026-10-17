@echo off
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
	echo.
	echo Python virtual environment not found.
	echo.
	echo DCSControlPanel can set it up now by running:
	echo 	py -m venv .venv
	echo 	.venv\Scripts\python.exe -m pip install --upgrade pip
	echo 	.venv\Scripts\python.exe -m pip install -r requirements.txt
	echo.
	choice /m "Create venv and install requirements now"
	if errorlevel 2 (
		echo.
		echo Setup cancelled.
		echo.
		pause
		exit /b 1
	)

	echo.
	echo Creating virtual environment...
	py -m venv .venv
	if errorlevel 1 goto :setupFailed

	echo.
	echo Upgrading pip...
	.venv\Scripts\python.exe -m pip install --upgrade pip
	if errorlevel 1 goto :setupFailed

	if not exist "requirements.txt" (
		echo.
		echo ERROR: requirements.txt not found.
		goto :setupFailed
	)

	echo.
	echo Installing requirements...
	.venv\Scripts\python.exe -m pip install -r requirements.txt
	if errorlevel 1 goto :setupFailed

	if not exist ".venv\Scripts\python.exe" goto :setupFailed
)

.venv\Scripts\python.exe DCSControlPanel.py
pause

goto :eof

:setupFailed
echo.
echo ERROR: Failed to set up the Python environment.
echo.
echo You can try manually running (from the repo root):
echo 	py -m venv .venv
echo 	.venv\Scripts\python.exe -m pip install --upgrade pip
echo 	.venv\Scripts\python.exe -m pip install -r requirements.txt
echo.
pause
exit /b 1
