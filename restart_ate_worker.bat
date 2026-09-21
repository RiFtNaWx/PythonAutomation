@echo off
setlocal
cd /d "%~dp0"

echo Stopping worker on port 8766 (supervisor stays)...
for /f "tokens=5" %%P in ('netstat -ano ^| findstr ":8766" ^| findstr "LISTENING"') do (
  echo Killing PID %%P
  taskkill /F /PID %%P >nul 2>&1
)

ping -n 6 127.0.0.1 >nul

if exist "venv\Scripts\python.exe" (
  "venv\Scripts\python.exe" -c "import urllib.request; urllib.request.urlopen(urllib.request.Request('http://127.0.0.1:8766', data=b'{\"jsonrpc\":\"2.0\",\"id\":1,\"method\":\"ping\",\"params\":{}}', headers={'Content-Type':'application/json'}, method='POST'), timeout=2)" >nul 2>&1
  if not errorlevel 1 (
    echo Worker back on http://127.0.0.1:8766 - supervisor respawn
    endlocal
    exit /b 0
  )
  "venv\Scripts\python.exe" -m ate.ui.launch --worker-only
) else (
  echo venv\Scripts\python.exe not found
  pause
  exit /b 1
)

echo Worker restarted on http://127.0.0.1:8766
endlocal
