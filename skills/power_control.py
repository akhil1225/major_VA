# skills/power_control.py
"""
Basic Windows power controls for OrbitOS.
Use with care: these commands actually affect the system.
"""

import os
import subprocess
import sys

def _is_windows() -> bool:
    return os.name == "nt"

def shutdown_system() -> str:
    if not _is_windows():
        return "Shutdown is only supported on Windows in this prototype."
    try:
        # /s = shutdown, /t 5 = after 5 seconds
        subprocess.Popen(["shutdown", "/s", "/t", "5"])
        return "Shutting down the system in 5 seconds."
    except Exception as e:
        return f"Failed to shutdown system: {e}"

def restart_system() -> str:
    if not _is_windows():
        return "Restart is only supported on Windows in this prototype."
    try:
        # /r = restart, /t 5 = after 5 seconds
        subprocess.Popen(["shutdown", "/r", "/t", "5"])
        return "Restarting the system in 5 seconds."
    except Exception as e:
        return f"Failed to restart system: {e}"

def sleep_system() -> str:
    if not _is_windows():
        return "Sleep is only supported on Windows in this prototype."
    try:
        # Put system to sleep
        # This uses rundll32 call: documented for Windows sleep.
        subprocess.Popen(
            ["rundll32.exe", "powrprof.dll,SetSuspendState", "0,1,0"],
            shell=False,
        )
        return "Putting the system to sleep."
    except Exception as e:
        return f"Failed to put system to sleep: {e}"
