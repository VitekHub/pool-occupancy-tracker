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


def available_week_ids(
    records: list[OccupancyRecord],
    clock: object = None,
) -> list[str]:
    """Ascending Monday ISO dates from earliest observed week through current Prague week.

    Weeks with no data are included. The current week is always present even if
    the CSV is empty.
    """
    now: datetime = clock() if callable(clock) else datetime.now(tz=PRAGUE)
    today = now.date()
    current_monday = today - timedelta(days=today.weekday())

    if not records:
        return [current_monday.isoformat()]

    earliest_monday_str = min(week_id(r.date_str) for r in records)
    earliest_monday = date.fromisoformat(earliest_monday_str)

    weeks: list[str] = []
    cursor = earliest_monday
    while cursor <= current_monday:
        weeks.append(cursor.isoformat())
        cursor += timedelta(weeks=1)
    return weeks
