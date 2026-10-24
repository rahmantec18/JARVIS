import subprocess
from typing import Dict, Any


def get_clipboard() -> Dict[str, Any]:
    """Retrieve current text content from the Windows clipboard."""
    try:
        proc = subprocess.run(
            ["powershell.exe", "-NoProfile", "-Command", "Get-Clipboard"],
            capture_output=True,
            text=True,
            timeout=5
        )
        content = proc.stdout.rstrip("\r\n")
        return {
            "success": True,
            "content": content,
            "length": len(content),
            "message": f"Retrieved {len(content)} characters from clipboard." if content else "Clipboard is currently empty."
        }
    except Exception as e:
        return {"success": False, "error": f"Failed to read clipboard: {str(e)}"}


def set_clipboard(text: str) -> Dict[str, Any]:
    """Copy text string onto the Windows clipboard."""
    try:
        proc = subprocess.Popen(
            ["powershell.exe", "-NoProfile", "-Command", "Set-Clipboard -Value $input"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        proc.communicate(input=text, timeout=5)
        return {
            "success": True,
            "length": len(text),
            "message": f"Successfully copied {len(text)} characters to clipboard."
        }
    except Exception as e:
        return {"success": False, "error": f"Failed to set clipboard: {str(e)}"}
