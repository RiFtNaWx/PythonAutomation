@echo off
setlocal EnableExtensions
cd /d "%~dp0"
REM Build the operator zip (Desktop + dist\ATE_Console_Try_YYYY-MM-DD.zip).
if not exist "venv\Scripts\python.exe" (
  echo Run START.bat once first so venv exists.
  pause
  exit /b 1
)
"venv\Scripts\python.exe" pack_ate_console.py --check
if errorlevel 1 (
  echo pack check failed
  pause
  exit /b 1
)
"venv\Scripts\python.exe" pack_ate_console.py
if errorlevel 1 (
  echo pack failed
  pause
  exit /b 1
)
echo.
echo Zip is on Desktop, dist\, and D:\ATE_Console\ when D: exists
echo Give operators the zip. Vibe-coders keep using git clone.
exit /b 0
