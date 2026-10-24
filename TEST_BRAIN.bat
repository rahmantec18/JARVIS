@echo off
title J.A.R.V.I.S. Brain Terminal (Step 2 Checkpoint)
color 0b
cd /d "%~dp0"
".\.venv\Scripts\python.exe" backend\brain_cli.py
pause
