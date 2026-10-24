import subprocess
import time
from typing import Dict, Any

BLOCKED_PATTERNS = [
    "format c:",
    "rmdir /s /q c:\\",
    "remove-item -recurse -force c:\\",
    "del /f /s /q c:\\windows",
    "bcdedit",
    ":(){ :|:& };:"
]


def execute_powershell(command: str, timeout: int = 20) -> Dict[str, Any]:
    """Execute a PowerShell command on the Windows host and capture output."""
    clean_cmd = command.strip()
    if not clean_cmd:
        return {"success": False, "error": "Command string cannot be empty."}

    # Safety check against catastrophic system wipes
    lower = clean_cmd.lower()
    for pattern in BLOCKED_PATTERNS:
        if pattern in lower:
            return {
                "success": False,
                "error": f"Security refusal: Command contains prohibited system destruction signature '{pattern}'."
            }

    start_time = time.time()
    try:
        proc = subprocess.run(
            ["powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", clean_cmd],
            capture_output=True,
            text=True,
            timeout=timeout,
            shell=False
        )
        duration = round(time.time() - start_time, 2)
        stdout = proc.stdout.strip()
        stderr = proc.stderr.strip()
        success = proc.returncode == 0

        return {
            "success": success,
            "command": clean_cmd,
            "stdout": stdout,
            "stderr": stderr,
            "returncode": proc.returncode,
            "duration_sec": duration,
            "output": stdout if stdout else (stderr if stderr else "Command completed with no console output.")
        }
    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "command": clean_cmd,
            "error": f"Command execution timed out after {timeout} seconds."
        }
    except Exception as e:
        return {
            "success": False,
            "command": clean_cmd,
            "error": f"Command execution error: {str(e)}"
        }
