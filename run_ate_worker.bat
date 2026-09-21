@echo off
setlocal
cd /d "%~dp0"
if not exist "venv\Scripts\python.exe" (
  echo venv not found
  pause
  exit /b 1
)
"venv\Scripts\python.exe" -m ate.ui.launch --worker-only
echo Worker started on http://127.0.0.1:8766
endlocal
