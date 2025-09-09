from datetime import datetime, time, timedelta
import pytz
from typing import Optional, Union

# Config
MOSCOW_TZ = pytz.timezone("Europe/Moscow")
# Sleep windows in Moscow local time: (start, end). End is exclusive.
SLEEP_WINDOWS = [
    # (time(22, 0), time(8, 0)),    # crosses midnight
    (time(12, 0), time(13, 0)),   # lunch
    (time(17, 30), time(18, 15)), # break
]

def _now_moscow(at_unix: Optional[Union[int, float]] = None) -> datetime:
    """Return timezone-aware Moscow datetime for now or a supplied Unix timestamp."""
    if at_unix is None:
        return datetime.now(MOSCOW_TZ)
    return datetime.fromtimestamp(at_unix, tz=pytz.UTC).astimezone(MOSCOW_TZ)

def _seconds_since_midnight(t: time) -> int:
    return t.hour * 3600 + t.minute * 60 + t.second

def _in_window(now_s: int, start_t: time, end_t: time) -> bool:
    start_s = _seconds_since_midnight(start_t)
    end_s = _seconds_since_midnight(end_t)
    if start_s < end_s:
        return start_s <= now_s < end_s
    # crosses midnight
    return now_s >= start_s or now_s < end_s

def _seconds_until_window_end(now_dt: datetime, start_t: time, end_t: time) -> int:
    """
    If now is inside the window, return seconds until the window ends.
    If not inside, return -1.
    """
    now_s = now_dt.hour * 3600 + now_dt.minute * 60 + now_dt.second
    start_s = _seconds_since_midnight(start_t)
    end_s = _seconds_since_midnight(end_t)

    if start_s < end_s:
        # simple same-day window
        if start_s <= now_s < end_s:
            end_dt = now_dt.replace(hour=end_t.hour, minute=end_t.minute, second=end_t.second, microsecond=0)
            return int((end_dt - now_dt).total_seconds())
        return -1
    else:
        # crosses midnight
        if now_s >= start_s:
            # window ends tomorrow at end_t
            end_dt = (now_dt + timedelta(days=1)).replace(hour=end_t.hour, minute=end_t.minute, second=end_t.second, microsecond=0)
            return int((end_dt - now_dt).total_seconds())
        elif now_s < end_s:
            # we're after midnight, before end_t today
            end_dt = now_dt.replace(hour=end_t.hour, minute=end_t.minute, second=end_t.second, microsecond=0)
            return int((end_dt - now_dt).total_seconds())
        return -1

def bot_can_answer(at_unix: Optional[Union[int, float]] = None) -> bool:
    """
    Returns True if bot is allowed to answer (outside all sleep windows),
    False if it should be silent. Evaluated in Moscow time.
    """
    now_dt = _now_moscow(at_unix)
    now_s = now_dt.hour * 3600 + now_dt.minute * 60 + now_dt.second
    return not any(_in_window(now_s, s, e) for s, e in SLEEP_WINDOWS)

def seconds_until_can_answer(at_unix: Optional[Union[int, float]] = None) -> int:
    """
    Returns how many seconds to wait until answering is allowed, in Moscow time.
    - If already allowed: returns 0.
    - If within one or more sleep windows: returns the soonest window end in seconds.
    """
    now_dt = _now_moscow(at_unix)
    waits = []
    for s, e in SLEEP_WINDOWS:
        w = _seconds_until_window_end(now_dt, s, e)
        if w >= 0:
            waits.append(w)
    return 0 if not waits else min(waits)