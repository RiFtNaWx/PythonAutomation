@echo off
setlocal EnableExtensions
cd /d "%~dp0"
REM DUT pin-1: Continue only if orientation is correct.
REM Zip (no .git) is operator-only. Git clone keeps engineer writes.
if not exist ".git" set "ATE_APP_ONLY=1"

set "PY="
py -3 -c "import sys" >nul 2>&1 && set "PY=py -3"
if not defined PY python -c "import sys" >nul 2>&1 && set "PY=python"
if not defined PY (
  echo Install Python 3.11+ from https://www.python.org/downloads/
  echo Tick "Add python.exe to PATH" then run START.bat again.
  pause
  exit /b 1
)

if not exist "venv\Scripts\python.exe" (
  echo First run: creating venv and installing packages. Takes 2 to 5 minutes.
  %PY% -m venv venv
  if errorlevel 1 (
    echo venv failed
    pause
    exit /b 1
  )
  "venv\Scripts\python.exe" -m pip install --upgrade pip
  "venv\Scripts\python.exe" -m pip install -r requirements-console.txt
  if errorlevel 1 (
    echo pip install failed
    pause
    exit /b 1
  )
)

if not exist "ate\config\cloud_db.txt" (
  copy /Y "ate\config\cloud_db.example.txt" "ate\config\cloud_db.txt" >nul
)

"venv\Scripts\python.exe" -m ate.core.sync_cloud_db
"venv\Scripts\python.exe" -m ate.core.require_cloud_db
REM Missing #Test_Database must not block. Setup -> Choose folder.

:launch
call "%~dp0run_ate_app.bat"
exit /b 0
