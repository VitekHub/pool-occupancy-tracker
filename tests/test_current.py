from datetime import datetime
from zoneinfo import ZoneInfo

import pytest

from pool_aggregation.aggregation.current import build_current_occupancy
from pool_aggregation.models.records import OccupancyRecord

PRAGUE = ZoneInfo("Europe/Prague")

# Monday 15 July 2024, 14:30 Prague time
_NOW = datetime(2024, 7, 15, 14, 30, 0, tzinfo=PRAGUE)

_INSIDE_CFG = {
    "maximumCapacity": 100,
    "totalLanes": 4,
}

_OUTSIDE_CFG = {
    "maximumCapacity": 2000,
}

_RECORDS_TODAY = [
    OccupancyRecord(date_str="15.07.2024", day="Monday", time_str="13:00", occupancy=50, hour=13),
    OccupancyRecord(date_str="15.07.2024", day="Monday", time_str="14:15", occupancy=80, hour=14),
]

_RECORDS_OTHER_DAY = [
    OccupancyRecord(date_str="16.7.2024", day="Tuesday", time_str="10:00", occupancy=30, hour=10),
]


def _overall(avg_util: int, day: str = "Monday", hour: str = "14") -> dict:
    return {
        "days": {
            day: {
                "hours": {
                    hour: {"averageUtilizationRate": avg_util},
                }
            }
        }
    }


# --- null when no records today ---

def test_null_when_no_records_today():
    result = build_current_occupancy(_RECORDS_OTHER_DAY, _INSIDE_CFG, {}, _NOW)
    assert result is None


def test_null_when_empty_records():
    result = build_current_occupancy([], _INSIDE_CFG, {}, _NOW)
    assert result is None


# --- populated today ---

def test_returns_dict_when_records_today():
    result = build_current_occupancy(_RECORDS_TODAY, _INSIDE_CFG, {}, _NOW)
    assert result is not None


def test_picks_latest_record():
    result = build_current_occupancy(_RECORDS_TODAY, _INSIDE_CFG, {}, _NOW)
    assert result["occupancy"] == 80
    assert result["time"] == "14:15"


def test_timestamp_is_iso8601():
    result = build_current_occupancy(_RECORDS_TODAY, _INSIDE_CFG, {}, _NOW)
    # Should contain timezone offset
    assert "+" in result["timestamp"] or result["timestamp"].endswith("Z")


def test_current_utilization_rate():
    # occupancy=80, maximumCapacity=100 → 80%
    result = build_current_occupancy(_RECORDS_TODAY, _INSIDE_CFG, {}, _NOW)
    assert result["currentUtilizationRate"] == 80


def test_maximum_capacity_from_config():
    result = build_current_occupancy(_RECORDS_TODAY, _INSIDE_CFG, {}, _NOW)
    assert result["maximumCapacity"] == 100


# --- averageUtilizationRate from overallOccupancyMap ---

def test_average_util_rate_from_overall():
    overall = _overall(avg_util=55, day="Monday", hour="14")
    result = build_current_occupancy(_RECORDS_TODAY, _INSIDE_CFG, overall, _NOW)
    assert result["averageUtilizationRate"] == 55


def test_average_util_rate_fallback_zero_when_no_history():
    result = build_current_occupancy(_RECORDS_TODAY, _INSIDE_CFG, {}, _NOW)
    assert result["averageUtilizationRate"] == 0


def test_average_util_rate_fallback_zero_wrong_slot():
    # overall has data for a different hour
    overall = _overall(avg_util=40, day="Monday", hour="9")
    result = build_current_occupancy(_RECORDS_TODAY, _INSIDE_CFG, overall, _NOW)
    assert result["averageUtilizationRate"] == 0


# --- totalLanes and openLanes ---

def test_total_lanes_inside_pool():
    result = build_current_occupancy(_RECORDS_TODAY, _INSIDE_CFG, {}, _NOW)
    assert result["totalLanes"] == 4


def test_open_lanes_inside_pool():
    # resolved cap == static cap (no hourlyMaxCapacity), so openLanes == totalLanes
    result = build_current_occupancy(_RECORDS_TODAY, _INSIDE_CFG, {}, _NOW)
    assert result["openLanes"] == 4


def test_total_lanes_outside_pool_is_null():
    result = build_current_occupancy(_RECORDS_TODAY, _OUTSIDE_CFG, {}, _NOW)
    assert result["totalLanes"] is None


def test_open_lanes_outside_pool_is_null():
    result = build_current_occupancy(_RECORDS_TODAY, _OUTSIDE_CFG, {}, _NOW)
    assert result["openLanes"] is None


# --- zero maximumCapacity guard ---

def test_zero_max_cap_util_is_zero():
    cfg = {"maximumCapacity": 0}
    result = build_current_occupancy(_RECORDS_TODAY, cfg, {}, _NOW)
    assert result["currentUtilizationRate"] == 0
