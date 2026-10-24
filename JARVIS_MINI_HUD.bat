@echo off
title J.A.R.V.I.S. Floating Companion HUD
cd /d "%~dp0"
start "" ".\.venv\Scripts\pythonw.exe" desktop_companion.py
exit
