@echo off
setlocal
cd /d "%~dp0"
if exist "venv\Scripts\pythonw.exe" (
  start "" "venv\Scripts\pythonw.exe" -m ate.ui.launch
) else if exist "venv\Scripts\python.exe" (
  start "" "venv\Scripts\python.exe" -m ate.ui.launch
) else (
  echo venv not found. Run install.py or START.bat first.
  pause
  exit /b 1
)
endlocal
