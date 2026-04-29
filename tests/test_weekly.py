from pool_aggregation.aggregation.weekly import build_weekly_map
from pool_aggregation.io.capacity_reader import clear_cache
from pool_aggregation.models.records import OccupancyRecord
import pytest


@pytest.fixture(autouse=True)
def reset_cap_cache():
    clear_cache()
    yield
    clear_cache()


def _rec(date_str, day, hour, occupancy):
    return OccupancyRecord(date_str=date_str, day=day,
                           time_str=f"{hour:02d}:00", occupancy=occupancy, hour=hour)


CFG_NO_HOURLY = {"maximumCapacity": 135}


# --- basic structure ---

def test_week_key_present():
    records = [_rec("15.7.2024", "Monday", 14, 42)]
    wmap = build_weekly_map(records, CFG_NO_HOURLY)
    assert "2024-07-15" in wmap


def test_day_key_present():
    records = [_rec("15.7.2024", "Monday", 14, 42)]
    wmap = build_weekly_map(records, CFG_NO_HOURLY)
    assert "Monday" in wmap["2024-07-15"]["days"]


def test_hour_key_is_string():
    records = [_rec("15.7.2024", "Monday", 14, 42)]
    wmap = build_weekly_map(records, CFG_NO_HOURLY)
    hours = wmap["2024-07-15"]["days"]["Monday"]["hours"]
    assert "14" in hours


def test_empty_records_returns_empty_map():
    assert build_weekly_map([], CFG_NO_HOURLY) == {}


# --- field values ---

def test_single_record_avg_equals_occupancy():
    records = [_rec("15.7.2024", "Monday", 14, 42)]
    hour = build_weekly_map(records, CFG_NO_HOURLY)["2024-07-15"]["days"]["Monday"]["hours"]["14"]
    assert hour["averageOccupancy"] == 42


def test_average_rounding():
    # (42 + 43) / 2 = 42.5 → banker's round → 42
    records = [_rec("15.7.2024", "Monday", 14, 42), _rec("15.7.2024", "Monday", 14, 43)]
    hour = build_weekly_map(records, CFG_NO_HOURLY)["2024-07-15"]["days"]["Monday"]["hours"]["14"]
    assert hour["averageOccupancy"] == 42


def test_average_rounding_up():
    # (43 + 44) / 2 = 43.5 → banker's round → 44
    records = [_rec("15.7.2024", "Monday", 14, 43), _rec("15.7.2024", "Monday", 14, 44)]
    hour = build_weekly_map(records, CFG_NO_HOURLY)["2024-07-15"]["days"]["Monday"]["hours"]["14"]
    assert hour["averageOccupancy"] == 44


def test_min_max_occupancy():
    records = [
        _rec("15.7.2024", "Monday", 14, 10),
        _rec("15.7.2024", "Monday", 14, 50),
        _rec("15.7.2024", "Monday", 14, 30),
    ]
    hour = build_weekly_map(records, CFG_NO_HOURLY)["2024-07-15"]["days"]["Monday"]["hours"]["14"]
    assert hour["minOccupancy"] == 10
    assert hour["maxOccupancy"] == 50


def test_utilization_rate():
    # avg=90, cap=135 → round(90/135*100) = round(66.66) = 67
    records = [_rec("15.7.2024", "Monday", 14, 90)]
    hour = build_weekly_map(records, CFG_NO_HOURLY)["2024-07-15"]["days"]["Monday"]["hours"]["14"]
    assert hour["utilizationRate"] == 67


def test_remaining_capacity():
    records = [_rec("15.7.2024", "Monday", 14, 90)]
    hour = build_weekly_map(records, CFG_NO_HOURLY)["2024-07-15"]["days"]["Monday"]["hours"]["14"]
    assert hour["remainingCapacity"] == 135 - 90


def test_maximum_capacity_from_config():
    records = [_rec("15.7.2024", "Monday", 14, 42)]
    hour = build_weekly_map(records, CFG_NO_HOURLY)["2024-07-15"]["days"]["Monday"]["hours"]["14"]
    assert hour["maximumCapacity"] == 135


def test_date_field_iso8601():
    records = [_rec("15.7.2024", "Monday", 14, 42)]
    hour = build_weekly_map(records, CFG_NO_HOURLY)["2024-07-15"]["days"]["Monday"]["hours"]["14"]
    assert hour["date"].startswith("2024-07-15T14:")
    assert "+02:00" in hour["date"]


def test_day_and_hour_fields():
    records = [_rec("15.7.2024", "Monday", 14, 42)]
    hour = build_weekly_map(records, CFG_NO_HOURLY)["2024-07-15"]["days"]["Monday"]["hours"]["14"]
    assert hour["day"] == "Monday"
    assert hour["hour"] == 14


def test_total_lanes_and_open_lanes_are_null():
    records = [_rec("15.7.2024", "Monday", 14, 42)]
    hour = build_weekly_map(records, CFG_NO_HOURLY)["2024-07-15"]["days"]["Monday"]["hours"]["14"]
    assert hour["totalLanes"] is None
    assert hour["openLanes"] is None


# --- only emit hours/days/weeks with data ---

def test_only_populated_hours_emitted():
    records = [_rec("15.7.2024", "Monday", 14, 42), _rec("15.7.2024", "Monday", 15, 10)]
    hours = build_weekly_map(records, CFG_NO_HOURLY)["2024-07-15"]["days"]["Monday"]["hours"]
    assert set(hours.keys()) == {"14", "15"}


def test_separate_weeks_separate_entries():
    records = [_rec("15.7.2024", "Monday", 14, 42), _rec("22.7.2024", "Monday", 14, 30)]
    wmap = build_weekly_map(records, CFG_NO_HOURLY)
    assert "2024-07-15" in wmap
    assert "2024-07-22" in wmap


# --- capacity resolution via hourly CSV ---

def test_hourly_capacity_resolution(monkeypatch, tmp_path):
    csv_path = tmp_path / "cap.csv"
    csv_path.write_text("Date,Day,Hour,Maximum Occupancy\n15.7.2024,Monday,14:00:00,90\n")

    import pool_aggregation.aggregation.capacity as cap_mod
    monkeypatch.setattr(cap_mod, "_DATA_DIR", tmp_path)

    cfg = {"maximumCapacity": 135, "hourlyMaxCapacity": "cap.csv"}
    records = [_rec("15.7.2024", "Monday", 14, 45)]
    hour = build_weekly_map(records, cfg)["2024-07-15"]["days"]["Monday"]["hours"]["14"]
    assert hour["maximumCapacity"] == 90
    assert hour["remainingCapacity"] == 90 - 45
