from __future__ import annotations
from collections import defaultdict

from pool_aggregation.utils.rounding import weighted_average, median_round, py_round


def build_overall_map(weekly_map: dict) -> dict:
    """Build overallOccupancyMap from an already-computed weeklyOccupancyMap."""
    # Collect utilizationRate values per (day, hour) across all weeks.
    slot_rates: dict[tuple[str, str], list[int]] = defaultdict(list)

    for week in weekly_map.values():
        for day, day_data in week["days"].items():
            for hour_key, hour_data in day_data["hours"].items():
                slot_rates[(day, hour_key)].append(hour_data["utilizationRate"])

    if not slot_rates:
        return {}

    # Build per-(day, hour) stats.
    days_map: dict[str, dict[str, dict]] = defaultdict(dict)
    for (day, hour_key), rates in slot_rates.items():
        float_rates = [float(r) for r in rates]
        days_map[day][hour_key] = {
            "averageUtilizationRate": py_round(sum(float_rates) / len(float_rates)),
            "weightedAverageUtilizationRate": weighted_average(float_rates),
            "medianUtilizationRate": median_round(float_rates),
        }

    result: dict[str, dict] = {}
    for day, hours in days_map.items():
        result[day] = hours

    return {"days": result}
