import psutil
import platform
import socket
import shutil
import time
from datetime import datetime



def get_cpu_usage() -> float:
    return psutil.cpu_percent(interval=0.5)



def get_memory_usage() -> dict:
    mem = psutil.virtual_memory()
    return {
        "total_gb": round(mem.total / (1024 ** 3), 2),
        "used_gb": round(mem.used / (1024 ** 3), 2),
        "percent": mem.percent
    }



def get_disk_usage(path: str = "/") -> dict:
    usage = shutil.disk_usage(path)
    total = usage.total / (1024 ** 3)
    used = usage.used / (1024 ** 3)
    percent = (used / total) * 100

    return {
        "total_gb": round(total, 2),
        "used_gb": round(used, 2),
        "percent": round(percent, 2)
    }



def get_battery_status() -> dict:
    battery = psutil.sensors_battery()
    if not battery:
        return {"available": False}

    return {
        "available": True,
        "percent": battery.percent,
        "plugged_in": battery.power_plugged
    }



def is_connected_to_internet(timeout: float = 1.0) -> bool:
    try:
        socket.create_connection(("8.8.8.8", 53), timeout=timeout)
        return True
    except OSError:
        return False



def get_system_uptime_minutes() -> int:
    uptime_seconds = time.time() - psutil.boot_time()
    return int(uptime_seconds / 60)


def get_os_info() -> dict:
    return {
        "system": platform.system(),
        "release": platform.release(),
        "version": platform.version(),
        "machine": platform.machine(),
        "processor": platform.processor()
    }



def get_current_time() -> str:
    return datetime.now().strftime("%I:%M %p").lstrip("0")


def get_current_date() -> str:
    return datetime.now().strftime("%A, %d %B %Y")
