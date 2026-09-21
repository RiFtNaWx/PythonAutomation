@echo off
title UPDATE GOLDENS -- import + safety gateway
cd /d "%~dp0"
if not exist "venv\Scripts\python.exe" (
    echo Missing venv\Scripts\python.exe -- run python install.py first.
    pause
    exit /b 1
)
echo Import from Downloads / author trees if newer, then verify.
venv\Scripts\python.exe -m ate.core.golden_gateway --import --verify
if errorlevel 1 (
    echo.
    echo GATEWAY blocked. Fix the named file only. Do not edit runner.py.
    pause
    exit /b 1
)
echo.
echo Next: double-click push.bat to open the GitHub PR.
echo Gateway runs again before the push. Mixed goldens + runner.py is blocked.
pause
