@echo off
title J.A.R.V.I.S. Shutdown Protocol
color 0c

echo ========================================================
echo       J.A.R.V.I.S. SUBSYSTEM SHUTDOWN PROTOCOL
echo ========================================================

cd /d "%~dp0"
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0stop_jarvis.ps1"

echo.
echo [✓] All J.A.R.V.I.S. subsystem processes terminated.
timeout /t 3
