from __future__ import annotations
from datetime import datetime

from pool_aggregation.aggregation.capacity import resolve_max_capacity
from pool_aggregation.aggregation.weekly import compute_open_lanes
from pool_aggregation.models.records import OccupancyRecord
from pool_aggregation.utils.rounding import py_round
from pool_aggregation.utils.timezones import PRAGUE, hour_start, to_iso8601


def build_current_occupancy(
    records: list[OccupancyRecord],
    pool_type_cfg: dict,
    overall_map: dict,
    now: datetime,
) -> dict | None:
    """Return currentOccupancy block or None if no records for today."""
    d = now.astimezone(PRAGUE)
    today_str = f"{d.day:02d}.{d.month:02d}.{d.year}"
    today_records = [r for r in records if r.date_str == today_str]
    if not today_records:
        return None

    latest = max(today_records, key=lambda r: r.time_str)
    current_hour = now.astimezone(PRAGUE).hour

    static_max_cap: int = pool_type_cfg.get("maximumCapacity", 0)
    total_lanes: int | None = pool_type_cfg.get("totalLanes")
    max_cap = resolve_max_capacity(pool_type_cfg, today_str, current_hour)
    open_lanes = compute_open_lanes(max_cap, total_lanes, static_max_cap)

    current_util = py_round(latest.occupancy / max_cap * 100) if max_cap else 0

    today_weekday = now.astimezone(PRAGUE).strftime("%A")
    hour_key = str(current_hour)
    avg_util = (
        overall_map.get("days", {})
        .get(today_weekday, {})
        .get("hours", {})
        .get(hour_key, {})
        .get("averageUtilizationRate", 0)
    )

    timestamp = to_iso8601(hour_start(today_str, latest.hour).replace(
        minute=int(latest.time_str.split(":")[1]),
        second=0,
        microsecond=0,
    ))

    return {
        "occupancy": latest.occupancy,
        "time": latest.time_str,
        "timestamp": timestamp,
        "currentUtilizationRate": current_util,
        "averageUtilizationRate": avg_util,
        "maximumCapacity": max_cap,
        "totalLanes": total_lanes,
        "openLanes": open_lanes,
    }
