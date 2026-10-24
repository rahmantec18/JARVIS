import os
import time
import base64
import subprocess
from pathlib import Path
from typing import Dict, Any

SCREENSHOTS_DIR = Path(__file__).parent.parent.parent / "screenshots"
SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)


def capture_screenshot(include_base64: bool = False) -> Dict[str, Any]:
    """Capture the current primary screen and save to disk."""
    timestamp_str = time.strftime("%Y%m%d_%H%M%S")
    out_file = SCREENSHOTS_DIR / f"screenshot_{timestamp_str}.png"
    out_path_str = str(out_file.resolve())

    # Method 1: Try Pillow ImageGrab
    try:
        from PIL import ImageGrab
        img = ImageGrab.grab()
        img.save(out_path_str, "PNG")
        if out_file.is_file() and out_file.stat().st_size > 0:
            return _format_success(out_file, include_base64)
    except Exception:
        pass

    # Method 2: Robust PowerShell .NET Graphics fallback
    ps_cmd = (
        "Add-Type -AssemblyName System.Windows.Forms,System.Drawing; "
        "$b = [System.Windows.Forms.Screen]::PrimaryScreen.Bounds; "
        "$bmp = New-Object System.Drawing.Bitmap($b.Width, $b.Height); "
        "$g = [System.Drawing.Graphics]::FromImage($bmp); "
        f"$g.CopyFromScreen($b.Location, [System.Drawing.Point]::Empty, $b.Size); "
        f"$bmp.Save('{out_path_str}', [System.Drawing.Imaging.ImageFormat]::Png); "
        "$g.Dispose(); $bmp.Dispose()"
    )
    try:
        subprocess.run(
            ["powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", ps_cmd],
            capture_output=True,
            timeout=8
        )
        if out_file.is_file() and out_file.stat().st_size > 0:
            return _format_success(out_file, include_base64)
    except Exception as e:
        return {"success": False, "error": f"Failed to capture screenshot: {str(e)}"}

    return {
        "success": False,
        "error": "Screen capture could not access the active graphical display session."
    }


def _format_success(file_path: Path, include_base64: bool) -> Dict[str, Any]:
    size_kb = round(file_path.stat().st_size / 1024, 1)
    b64_str = ""
    if include_base64:
        try:
            with open(file_path, "rb") as f:
                b64_str = base64.b64encode(f.read()).decode("utf-8")
        except Exception:
            pass

    return {
        "success": True,
        "file_path": str(file_path),
        "file_name": file_path.name,
        "size_kb": size_kb,
        "base64": b64_str if include_base64 else None,
        "message": f"Screenshot saved to '{file_path.name}' ({size_kb} KB)."
    }
