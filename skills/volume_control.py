import subprocess
import re



def _run_ps(script: str) -> str:
    result = subprocess.run(
        [
            "powershell",
            "-NoProfile",
            "-Command",
            script
        ],
        capture_output=True,
        text=True
    )
    return result.stdout.strip()


def get_volume() -> int:
    output = _run_ps(
        "(Get-AudioDevice -PlaybackVolume).Volume"
    )
    try:
        return int(float(output))
    except Exception:
        return 0


def set_volume(percent: int) -> str:
    percent = max(0, min(100, percent))
    _run_ps(f"Set-AudioDevice -PlaybackVolume {percent}")
    return f"Volume set to {percent} percent."


def increase_volume(step: int = 10) -> str:
    current = get_volume()
    return set_volume(current + step)


def decrease_volume(step: int = 10) -> str:
    current = get_volume()
    return set_volume(current - step)


def mute() -> str:
    _run_ps("Set-AudioDevice -PlaybackMute $true")
    return "Volume muted."


def unmute() -> str:
    _run_ps("Set-AudioDevice -PlaybackMute $false")
    return "Volume unmuted."

