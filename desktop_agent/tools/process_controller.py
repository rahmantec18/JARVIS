from typing import Dict, Any, List, Optional
import psutil


def list_processes(filter_name: Optional[str] = None, limit: int = 25) -> Dict[str, Any]:
    """List running processes filtered by name or sorted by memory usage."""
    procs: List[Dict[str, Any]] = []
    clean_filter = (filter_name or "").lower().strip()

    try:
        for p in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
            try:
                info = p.info
                name = info['name'] or ""
                if clean_filter and clean_filter not in name.lower():
                    continue
                procs.append({
                    "pid": info['pid'],
                    "name": name,
                    "cpu_percent": info['cpu_percent'] or 0.0,
                    "memory_percent": round(info['memory_percent'] or 0.0, 1)
                })
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue

        # Sort by memory descending
        procs.sort(key=lambda x: x["memory_percent"], reverse=True)
        return {
            "success": True,
            "count": len(procs),
            "processes": procs[:limit]
        }
    except Exception as e:
        return {"success": False, "error": f"Failed to list processes: {str(e)}"}


def kill_process(target: str) -> Dict[str, Any]:
    """Terminate a process by PID or process name (e.g. 'notepad.exe')."""
    clean_target = str(target).strip()
    if not clean_target:
        return {"success": False, "error": "Target PID or process name required."}

    # Protected core processes
    protected = ["explorer.exe", "system", "csrss.exe", "smss.exe", "lsass.exe", "services.exe", "winlogon.exe"]
    if clean_target.lower() in protected:
        return {"success": False, "error": f"Refusing to kill critical Windows system process '{clean_target}'."}

    killed_count = 0
    try:
        # Check if target is a PID
        if clean_target.isdigit():
            pid = int(clean_target)
            p = psutil.Process(pid)
            p_name = p.name()
            if p_name.lower() in protected:
                return {"success": False, "error": f"Refusing to kill critical Windows process {p_name}."}
            p.terminate()
            return {"success": True, "message": f"Successfully terminated process {p_name} (PID: {pid})."}

        # Target by name
        for p in psutil.process_iter(['pid', 'name']):
            try:
                if p.info['name'] and p.info['name'].lower() == clean_target.lower():
                    p.terminate()
                    killed_count += 1
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue

        if killed_count > 0:
            return {"success": True, "message": f"Terminated {killed_count} instance(s) of '{clean_target}'."}
        else:
            return {"success": False, "error": f"No active process matching '{clean_target}' was found."}

    except psutil.NoSuchProcess:
        return {"success": False, "error": f"Process {clean_target} is no longer running."}
    except psutil.AccessDenied:
        return {"success": False, "error": f"Access denied: Administrator privileges required to terminate {clean_target}."}
    except Exception as e:
        return {"success": False, "error": f"Error terminating process: {str(e)}"}
