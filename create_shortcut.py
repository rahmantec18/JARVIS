import os
from pathlib import Path

desktop = Path(os.environ.get("USERPROFILE", "C:\\Users\\abdur")) / "Desktop"
if not desktop.exists():
    desktop = Path(os.environ.get("USERPROFILE", "C:\\Users\\abdur")) / "OneDrive" / "Desktop"

bat_launcher = desktop / "JARVIS.bat"
repo_dir = Path(r"C:\Users\abdur\OneDrive\Documents\JARVIS")
start_bat = repo_dir / "START_JARVIS.bat"

content = f"""@echo off
title J.A.R.V.I.S.
cd /d "{repo_dir}"
call "{start_bat}"
"""

bat_launcher.write_text(content, encoding="utf-8")
print(f"Created desktop shortcut: {bat_launcher} (exists: {bat_launcher.exists()})")

hud_launcher = desktop / "JARVIS_HUD.bat"
hud_bat = repo_dir / "JARVIS_MINI_HUD.bat"
hud_content = f"""@echo off
title J.A.R.V.I.S. Floating HUD
cd /d "{repo_dir}"
call "{hud_bat}"
"""
hud_launcher.write_text(hud_content, encoding="utf-8")
print(f"Created desktop HUD shortcut: {hud_launcher} (exists: {hud_launcher.exists()})")
