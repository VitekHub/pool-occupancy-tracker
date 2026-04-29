from __future__ import annotations
from collections import defaultdict

from pool_aggregation.aggregation.bucketing import bucket_records, week_id
from pool_aggregation.aggregation.capacity import resolve_max_capacity
from pool_aggregation.models.records import OccupancyRecord
from pool_aggregation.utils.rounding import py_round
from pool_aggregation.utils.timezones import hour_start, to_iso8601


def build_weekly_map(
    records: list[OccupancyRecord],
    pool_type_cfg: dict,
) -> dict:
    """Return weeklyOccupancyMap with hour buckets (totalLanes/openLanes null)."""
    buckets = bucket_records(records)

    # week -> day -> hour -> bucket dict
    weekly: dict[str, dict[str, dict[str, dict]]] = defaultdict(
        lambda: defaultdict(dict)
    )

    for (wid, day, hour), recs in buckets.items():
        occupancies = [r.occupancy for r in recs]
        avg_occ = py_round(sum(occupancies) / len(occupancies))
        min_occ = min(occupancies)
        max_occ = max(occupancies)

        # Use any record's date_str for capacity resolution; all share the same
        # (weekId, day, hour) so use the first record's date.
        date_str = recs[0].date_str
        max_cap = resolve_max_capacity(pool_type_cfg, date_str, hour)

        util = py_round(avg_occ / max_cap * 100) if max_cap else 0

        weekly[wid][day][str(hour)] = {
            "day": day,
            "hour": hour,
            "date": to_iso8601(hour_start(date_str, hour)),
            "minOccupancy": min_occ,
            "maxOccupancy": max_occ,
            "averageOccupancy": avg_occ,
            "maximumCapacity": max_cap,
            "totalLanes": None,
            "openLanes": None,
            "utilizationRate": util,
            "remainingCapacity": max_cap - avg_occ,
        }

    # Convert nested defaultdicts to plain dicts
    return {
        wid: {
            "maxWeekValues": {"utilizationRate": 0},
            "days": {
                day: {
                    "maxDayValues": {"utilizationRate": 0},
                    "hours": hours,
                }
                for day, hours in days.items()
            },
        }
        for wid, days in weekly.items()
    }
