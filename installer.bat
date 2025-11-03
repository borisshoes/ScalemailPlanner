@echo off
setlocal

REM Run from this script's directory
cd /d "%~dp0"

REM Detect Python (prefer Windows launcher)
where py >nul 2>&1
if %errorlevel%==0 (
  set "PY=py"
) else (
  where python >nul 2>&1
  if %errorlevel%==0 (
    set "PY=python"
  ) else (
    echo Python was not detected on this system.
    echo Please install Python 3 and be sure to check "Add Python to PATH".
    echo Download: https://www.python.org/downloads/windows/
    pause
    exit /b 1
  )
)

echo Installing requirements...
"%PY%" -m pip install --upgrade --user pip
if %errorlevel% neq 0 (
  echo Failed to upgrade pip.
  pause
  exit /b 1
)

"%PY%" -m pip install -r requirements.txt --user
if %errorlevel% neq 0 (
  echo Failed to install requirements. See messages above.
  pause
  exit /b 1
)

echo Launching app...
"%PY%" "%~dp0scales.py"
if %errorlevel% neq 0 (
  echo The app exited with an error. See messages above.
  pause
  exit /b 1
)

endlocal