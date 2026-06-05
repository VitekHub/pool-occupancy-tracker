from __future__ import annotations
from collections import defaultdict
from collections.abc import Iterable
from datetime import date, datetime, timedelta

from pool_aggregation.models.records import OccupancyRecord
from pool_aggregation.utils.timezones import PRAGUE

_DAY_NAMES = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]


def day_name_from_date_str(date_str: str) -> str:
    """Return the English weekday name for a date_str in d.M.yyyy format."""
    return _DAY_NAMES[_parse_date(date_str).weekday()]


def _parse_date(date_str: str) -> date:
    """Parse d.M.yyyy into a date object."""
    day, month, year = date_str.split(".")
    return date(int(year), int(month), int(day))


def week_id(date_str: str) -> str:
    """Return the ISO Monday of the week containing date_str as yyyy-MM-dd."""
    d = _parse_date(date_str)
    monday = d - timedelta(days=d.weekday())
    return monday.isoformat()


def bucket_records(
    records: list[OccupancyRecord],
) -> dict[tuple[str, str, int], list[OccupancyRecord]]:
    """Group records by (weekId, day, hour)."""
    buckets: dict[tuple[str, str, int], list[OccupancyRecord]] = defaultdict(list)
    for r in records:
        buckets[(week_id(r.date_str), r.day, r.hour)].append(r)
    return dict(buckets)


def available_week_ids(
    records: list[OccupancyRecord],
    extra_week_ids: Iterable[str] = (),
) -> list[str]:
    """Ascending Monday ISO dates for weeks that have records or capacity data.

    If both sources are empty, returns only the current Prague week.
    """
    from_records = {week_id(r.date_str) for r in records}
    merged = from_records | set(extra_week_ids)
    if not merged:
        today = datetime.now(tz=PRAGUE).date()
        current_monday = today - timedelta(days=today.weekday())
        return [current_monday.isoformat()]

    return sorted(merged)
