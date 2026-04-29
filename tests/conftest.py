import pytest
from pool_aggregation.models.records import OccupancyRecord


@pytest.fixture
def sample_records():
    return [
        OccupancyRecord(date_str="15.7.2024", day="Monday", time_str="14:15", occupancy=42, hour=14),
        OccupancyRecord(date_str="15.7.2024", day="Monday", time_str="15:00", occupancy=55, hour=15),
        OccupancyRecord(date_str="16.7.2024", day="Tuesday", time_str="09:00", occupancy=10, hour=9),
    ]


@pytest.fixture
def inside_pool_cfg():
    return {
        "weekdaysOpeningHours": "6-22",
        "weekendOpeningHours": "8-21",
        "maximumCapacity": 135,
        "totalLanes": 6,
        "todayClosed": False,
        "temporarilyClosed": "28.6.2025 - 19.10.2025",
    }


@pytest.fixture
def outside_pool_cfg():
    return {
        "weekdaysOpeningHours": "9-21",
        "weekendOpeningHours": "9-20",
        "maximumCapacity": 2000,
        "todayClosed": False,
        "temporarilyClosed": None,
    }
