import subprocess
import sys
from typing import Dict, Any


def show_notification(title: str, message: str) -> Dict[str, Any]:
    """Display a native desktop notification on Windows."""
    clean_title = title.replace('"', '`"').replace("'", "`'")
    clean_msg = message.replace('"', '`"').replace("'", "`'")

    # PowerShell script to trigger Windows notification
    ps_cmd = (
        f"[void] [System.Reflection.Assembly]::LoadWithPartialName('System.Windows.Forms'); "
        f"$notify = New-Object System.Windows.Forms.NotifyIcon; "
        f"$notify.Icon = [System.Drawing.SystemIcons]::Information; "
        f"$notify.Visible = $true; "
        f"$notify.ShowBalloonTip(5000, '{clean_title}', '{clean_msg}', [System.Windows.Forms.ToolTipIcon]::Info); "
        f"Start-Sleep -Milliseconds 100; "
        f"$notify.Dispose()"
    )

    try:
        if sys.platform == "win32":
            subprocess.Popen(
                ["powershell", "-NoProfile", "-WindowStyle", "Hidden", "-Command", ps_cmd],
                shell=False
            )
        return {
            "success": True,
            "title": title,
            "message": message,
            "status": "Notification sent to desktop"
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to display notification: {str(e)}"
        }
