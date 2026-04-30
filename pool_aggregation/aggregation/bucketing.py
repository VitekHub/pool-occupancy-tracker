from __future__ import annotations
from collections import defaultdict
from datetime import date, datetime, timedelta

from pool_aggregation.models.records import OccupancyRecord
from pool_aggregation.utils.timezones import PRAGUE


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


def available_week_ids(records: list[OccupancyRecord]) -> list[str]:
    """Ascending Monday ISO dates for weeks that actually have records.

    If records is empty, returns only the current Prague week.
    """
    if not records:
        today = datetime.now(tz=PRAGUE).date()
        current_monday = today - timedelta(days=today.weekday())
        return [current_monday.isoformat()]

    return sorted({week_id(r.date_str) for r in records})
