@echo off
title J.A.R.V.I.S. Personal AI Ecosystem
color 0b

echo ========================================================
echo       J.A.R.V.I.S. PERSONAL AI ECOSYSTEM (WINDOWS)
echo ========================================================
echo [i] Initializing J.A.R.V.I.S. Subsystems...

cd /d "%~dp0"

powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0start_jarvis.ps1"

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [!] Standard PowerShell launcher exited with code %ERRORLEVEL%.
    echo [i] Attempting direct Python unified launcher...
    ".\.venv\Scripts\python.exe" run_jarvis.py
)

pause
