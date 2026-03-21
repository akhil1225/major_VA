import threading
import time
from typing import Callable, Optional

_alarm_thread: Optional[threading.Thread] = None
_alarm_active = False
_alarm_time = None


def set_alarm(hour: int, minute: int, callback: Callable[[], None]) -> str:
    global _alarm_thread, _alarm_active, _alarm_time

    cancel_alarm()

    now = time.localtime()
    target = time.struct_time((
        now.tm_year, now.tm_mon, now.tm_mday,
        hour, minute, 0,
        now.tm_wday, now.tm_yday, now.tm_isdst
    ))

    target_ts = time.mktime(target)
    now_ts = time.time()

    if target_ts <= now_ts:
        target_ts += 24 * 60 * 60  # next day

    delay = target_ts - now_ts
    _alarm_active = True
    _alarm_time = (hour, minute)

    def runner():
        global _alarm_active
        time.sleep(delay)
        if _alarm_active:
            callback()
            _alarm_active = False

    _alarm_thread = threading.Thread(target=runner, daemon=True)
    _alarm_thread.start()

    return f"Alarm set for {hour:02d}:{minute:02d}."


def cancel_alarm() -> str:
    global _alarm_active, _alarm_thread, _alarm_time
    _alarm_active = False
    _alarm_thread = None
    _alarm_time = None
    return "Alarm cancelled."


def get_alarm_status() -> str:
    if not _alarm_active or not _alarm_time:
        return "No alarm is currently set."
    h, m = _alarm_time
    return f"Alarm is set for {h:02d}:{m:02d}."
