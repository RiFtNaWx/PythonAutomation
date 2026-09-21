@echo off
setlocal
cd /d "%~dp0"

echo Stopping ATE worker (8766) and UI (5174)...
for /f "tokens=5" %%P in ('netstat -ano ^| findstr ":8766" ^| findstr "LISTENING"') do (
  echo Killing PID %%P on 8766
  taskkill /F /PID %%P >nul 2>&1
)
for /f "tokens=5" %%P in ('netstat -ano ^| findstr ":5174" ^| findstr "LISTENING"') do (
  echo Killing PID %%P on 5174
  taskkill /F /PID %%P >nul 2>&1
)

timeout /t 1 /nobreak >nul 2>&1
if errorlevel 1 ping -n 2 127.0.0.1 >nul

if not exist "venv\Scripts\pythonw.exe" if not exist "venv\Scripts\python.exe" (
  echo venv not found — run install.py first.
  pause
  exit /b 1
)

if exist "venv\Scripts\pythonw.exe" (
  start "" "venv\Scripts\pythonw.exe" -m ate.ui.launch
) else (
  start "" "venv\Scripts\python.exe" -m ate.ui.launch
)
echo ATE restarted. Ctrl+F5 if the console was already open.
endlocal
