import platform
import time
from typing import Dict, Any
import psutil


def get_system_status() -> Dict[str, Any]:
    """Retrieve real system telemetry including CPU, RAM, Disk, and Battery."""
    cpu_percent = psutil.cpu_percent(interval=0.1)
    cpu_count = psutil.cpu_count(logical=True)
    
    memory = psutil.virtual_memory()
    disk = psutil.disk_usage('/')
    
    battery_info = None
    try:
        battery = psutil.sensors_battery()
        if battery:
            battery_info = {
                "percent": battery.percent,
                "power_plugged": battery.power_plugged,
                "secsleft": battery.secsleft if battery.secsleft != psutil.POWER_TIME_UNLIMITED else "Unlimited"
            }
    except Exception:
        battery_info = None

    boot_time = psutil.boot_time()
    uptime_seconds = int(time.time() - boot_time)
    hours, remainder = divmod(uptime_seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    uptime_formatted = f"{hours}h {minutes}m {seconds}s"

    return {
        "os": f"{platform.system()} {platform.release()} ({platform.version()})",
        "hostname": platform.node(),
        "cpu": {
            "percent": cpu_percent,
            "logical_cores": cpu_count
        },
        "memory": {
            "total_gb": round(memory.total / (1024 ** 3), 2),
            "used_gb": round(memory.used / (1024 ** 3), 2),
            "free_gb": round(memory.available / (1024 ** 3), 2),
            "percent": memory.percent
        },
        "disk": {
            "total_gb": round(disk.total / (1024 ** 3), 2),
            "used_gb": round(disk.used / (1024 ** 3), 2),
            "free_gb": round(disk.free / (1024 ** 3), 2),
            "percent": disk.percent
        },
        "battery": battery_info,
        "uptime": uptime_formatted
    }
