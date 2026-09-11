@echo off
setlocal EnableExtensions
cd /d "%~dp0"
set "ATE_APP_ONLY=1"

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

"venv\Scripts\python.exe" -m ate.core.require_cloud_db
if errorlevel 2 goto need_cloud
if errorlevel 1 goto need_cloud
goto launch

:need_cloud
echo.
echo Central database folder is not on this PC yet.
echo 1. Open the SharePoint link Jian Hong sends (or ate\config\sharepoint.url).
echo 2. Sync that library with OneDrive.
echo 3. Paste the local folder path (the #Test_Database tree) into ate\config\cloud_db.txt
echo    One line. Not a https:// URL.
echo.
if exist "ate\config\sharepoint.url" (
  for /f "usebackq eol=# tokens=* delims=" %%U in ("ate\config\sharepoint.url") do (
    if not "%%U"=="" start "" "%%U"
  )
)
notepad "ate\config\cloud_db.txt"
echo Save cloud_db.txt then run START.bat again.
pause
exit /b 2

:launch
call "%~dp0run_ate_app.bat"
echo.
echo Console: http://127.0.0.1:5174
echo Everyone uses the same SharePoint-synced #Test_Database. Results land there; OneDrive uploads.
echo Pick a person (not All). Setup -^> Create folders + open. Then DEMO (no instruments).
echo DUT pin-1: Continue only if orientation is correct. Wrong = Abort, rotate, Continue.
pause
