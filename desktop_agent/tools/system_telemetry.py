import platform
import time
from typing import Dict, Any, List
import psutil


def get_desktop_system_info() -> Dict[str, Any]:
    """Gather real hardware telemetry and active process overview."""
    cpu_percent = psutil.cpu_percent(interval=0.1)
    cpu_cores = psutil.cpu_count(logical=True)
    memory = psutil.virtual_memory()
    disk = psutil.disk_usage('/')

    battery_info = None
    try:
        b = psutil.sensors_battery()
        if b:
            battery_info = {
                "percent": b.percent,
                "charging": b.power_plugged,
            }
    except Exception:
        pass

    # Top 5 processes by memory usage
    top_processes: List[Dict[str, Any]] = []
    try:
        for p in sorted(psutil.process_iter(['name', 'cpu_percent', 'memory_percent']), key=lambda x: x.info['memory_percent'] or 0, reverse=True)[:5]:
            top_processes.append({
                "name": p.info['name'],
                "cpu": p.info['cpu_percent'] or 0.0,
                "memory": round(p.info['memory_percent'] or 0.0, 1)
            })
    except Exception:
        pass

    return {
        "os": f"{platform.system()} {platform.release()}",
        "architecture": platform.machine(),
        "hostname": platform.node(),
        "cpu_percent": cpu_percent,
        "cpu_cores": cpu_cores,
        "memory_percent": memory.percent,
        "memory_used_gb": round(memory.used / (1024 ** 3), 2),
        "memory_total_gb": round(memory.total / (1024 ** 3), 2),
        "disk_percent": disk.percent,
        "disk_free_gb": round(disk.free / (1024 ** 3), 2),
        "battery": battery_info,
        "top_processes": top_processes,
        "timestamp": time.time()
    }
