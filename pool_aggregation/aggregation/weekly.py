from __future__ import annotations
from collections import defaultdict
from pathlib import Path

from pool_aggregation.aggregation.bucketing import bucket_records, day_name_from_date_str, week_id
from pool_aggregation.aggregation.capacity import resolve_max_capacity
from pool_aggregation.io.capacity_reader import load_hourly_capacity
from pool_aggregation.models.records import OccupancyRecord
from pool_aggregation.utils.rounding import py_round
from pool_aggregation.utils.timezones import hour_start, to_iso8601

_DATA_DIR = Path(__file__).parent.parent.parent / "data"

_DAY_ORDER = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]


def compute_open_lanes(
    resolved_max_cap: int,
    total_lanes: int | None,
    static_max_cap: int,
) -> int | None:
    """round((resolved_max_cap * total_lanes) / static_max_cap); null when not applicable."""
    if total_lanes is None or static_max_cap == 0:
        return None
    return py_round(resolved_max_cap * total_lanes / static_max_cap)


def _capacity_date_hours(pool_cfg: dict) -> set[tuple[str, int]]:
    """Return all (date_str, hour) pairs present in the forecast capacity CSV."""
    filename = pool_cfg.get("data", {}).get("capacity", {}).get("forecast")
    if not filename:
        return set()
    pairs: set[tuple[str, int]] = set()
    for date_str, hour_key in load_hourly_capacity(_DATA_DIR / filename):
        try:
            hour = int(hour_key.split(":")[0])
        except (ValueError, AttributeError):
            continue
        pairs.add((date_str, hour))
    return pairs


def build_weekly_map(
    records: list[OccupancyRecord],
    pool_type_cfg: dict,
) -> dict:
    """Return weeklyOccupancyMap with hour buckets including totalLanes/openLanes.

    Hours with real occupancy data include all occupancy fields. Hours that
    only appear in capacity CSV files (future slots) have null occupancy fields.
    """
    buckets = bucket_records(records)

    static_max_cap: int = pool_type_cfg.get("maximumCapacity", 0)
    total_lanes: int | None = pool_type_cfg.get("totalLanes")

    # week -> day -> hour -> bucket dict
    weekly: dict[str, dict[str, dict[str, dict]]] = defaultdict(
        lambda: defaultdict(dict)
    )

    # --- slots with real occupancy data ---
    occupied_slots: set[tuple[str, str, int]] = set()
    for (wid, day, hour), recs in buckets.items():
        occupancies = [r.occupancy for r in recs]
        avg_occ = py_round(sum(occupancies) / len(occupancies))
        min_occ = min(occupancies)
        max_occ = max(occupancies)

        # Use first record's date for capacity resolution (all share weekId/day/hour).
        date_str = recs[0].date_str
        max_cap = resolve_max_capacity(pool_type_cfg, date_str, hour)

        util = py_round(avg_occ / max_cap * 100) if max_cap else 0
        open_lanes = compute_open_lanes(max_cap, total_lanes, static_max_cap)

        weekly[wid][day][str(hour)] = {
            "day": day,
            "hour": hour,
            "date": to_iso8601(hour_start(date_str, hour)),
            "minOccupancy": min_occ,
            "maxOccupancy": max_occ,
            "averageOccupancy": avg_occ,
            "maximumCapacity": max_cap,
            "totalLanes": total_lanes,
            "openLanes": open_lanes,
            "utilizationRate": util,
            "remainingCapacity": py_round(max_cap - avg_occ),
        }
        occupied_slots.add((wid, day, hour))

    # --- future capacity-only slots (no occupancy records yet) ---
    for date_str, hour in sorted(_capacity_date_hours(pool_type_cfg), key=lambda x: (x[0], x[1])):
        day = day_name_from_date_str(date_str)
        wid = week_id(date_str)
        if (wid, day, hour) in occupied_slots:
            continue
        max_cap = resolve_max_capacity(pool_type_cfg, date_str, hour)
        open_lanes = compute_open_lanes(max_cap, total_lanes, static_max_cap)
        weekly[wid][day][str(hour)] = {
            "day": day,
            "hour": hour,
            "date": to_iso8601(hour_start(date_str, hour)),
            "minOccupancy": None,
            "maxOccupancy": None,
            "averageOccupancy": None,
            "maximumCapacity": max_cap,
            "totalLanes": total_lanes,
            "openLanes": open_lanes,
            "utilizationRate": None,
            "remainingCapacity": None,
        }

    result = {}
    for wid, days in weekly.items():
        built_days = {}
        week_max_util: int | None = None
        for day in [d for d in _DAY_ORDER if d in days]:
            hours = days[day]
            util_values = [h["utilizationRate"] for h in hours.values() if h["utilizationRate"] is not None]
            day_max_util: int | None = max(util_values) if util_values else None
            if day_max_util is not None:
                week_max_util = max(week_max_util, day_max_util) if week_max_util is not None else day_max_util
            built_days[day] = {
                "maxDayValues": {"utilizationRate": day_max_util},
                "hours": hours,
            }
        result[wid] = {
            "maxWeekValues": {"utilizationRate": week_max_util},
            "days": built_days,
        }
    return result
