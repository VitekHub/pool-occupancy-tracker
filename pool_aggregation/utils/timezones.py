from __future__ import annotations
from datetime import datetime, timezone
from typing import Callable
from zoneinfo import ZoneInfo

PRAGUE = ZoneInfo("Europe/Prague")


def now_prague(clock: Callable[[], datetime] | None = None) -> datetime:
    """Return the current datetime in Europe/Prague. Inject clock for tests."""
    if clock is not None:
        return clock()
    return datetime.now(tz=PRAGUE)


def hour_start(date_str: str, hour: int) -> datetime:
    """Return a tz-aware datetime for the start of *hour* on *date_str* (d.M.yyyy)."""
    day, month, year = date_str.split(".")
    naive = datetime(int(year), int(month), int(day), hour, 0, 0)
    return naive.replace(tzinfo=PRAGUE)


def to_iso8601(dt: datetime) -> str:
    """Format a tz-aware datetime as ISO8601 with the Prague UTC offset."""
    return dt.isoformat()
