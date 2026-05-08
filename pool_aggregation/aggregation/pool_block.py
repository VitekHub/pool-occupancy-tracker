from __future__ import annotations

from pool_aggregation.models.records import OccupancyRecord
from pool_aggregation.utils.timezones import hour_start, to_iso8601


def build_data_range(records: list[OccupancyRecord]) -> dict | None:
    if not records:
        return None
    first = min(records, key=lambda r: (r.date_str.split(".")[::-1], r.time_str))
    last = max(records, key=lambda r: (r.date_str.split(".")[::-1], r.time_str))
    return {
        "firstRecordAt": to_iso8601(hour_start(first.date_str, first.hour)),
        "lastRecordAt": to_iso8601(hour_start(last.date_str, last.hour)),
    }
