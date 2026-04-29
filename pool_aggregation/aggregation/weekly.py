from __future__ import annotations
from collections import defaultdict

from pool_aggregation.aggregation.bucketing import bucket_records, week_id
from pool_aggregation.aggregation.capacity import resolve_max_capacity
from pool_aggregation.models.records import OccupancyRecord
from pool_aggregation.utils.rounding import py_round
from pool_aggregation.utils.timezones import hour_start, to_iso8601


def compute_open_lanes(
    resolved_max_cap: int,
    total_lanes: int | None,
    static_max_cap: int,
) -> int | None:
    """round((resolved_max_cap * total_lanes) / static_max_cap); null when not applicable."""
    if total_lanes is None or static_max_cap == 0:
        return None
    return py_round(resolved_max_cap * total_lanes / static_max_cap)


def build_weekly_map(
    records: list[OccupancyRecord],
    pool_type_cfg: dict,
) -> dict:
    """Return weeklyOccupancyMap with hour buckets including totalLanes/openLanes."""
    buckets = bucket_records(records)

    static_max_cap: int = pool_type_cfg.get("maximumCapacity", 0)
    total_lanes: int | None = pool_type_cfg.get("totalLanes")

    # week -> day -> hour -> bucket dict
    weekly: dict[str, dict[str, dict[str, dict]]] = defaultdict(
        lambda: defaultdict(dict)
    )

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
            "remainingCapacity": max_cap - avg_occ,
        }

    result = {}
    for wid, days in weekly.items():
        built_days = {}
        week_max_util = 0
        for day, hours in days.items():
            day_max_util = max(h["utilizationRate"] for h in hours.values())
            week_max_util = max(week_max_util, day_max_util)
            built_days[day] = {
                "maxDayValues": {"utilizationRate": day_max_util},
                "hours": hours,
            }
        result[wid] = {
            "maxWeekValues": {"utilizationRate": week_max_util},
            "days": built_days,
        }
    return result
