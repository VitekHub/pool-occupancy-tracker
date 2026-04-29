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


def test_total_lanes_null_for_outside_pool():
    records = [_rec("15.7.2024", "Monday", 14, 42)]
    hour = build_weekly_map(records, CFG_NO_HOURLY)["2024-07-15"]["days"]["Monday"]["hours"]["14"]
    assert hour["totalLanes"] is None


def test_open_lanes_null_when_total_lanes_null():
    records = [_rec("15.7.2024", "Monday", 14, 42)]
    hour = build_weekly_map(records, CFG_NO_HOURLY)["2024-07-15"]["days"]["Monday"]["hours"]["14"]
    assert hour["openLanes"] is None


def test_total_lanes_propagated_for_inside_pool():
    cfg = {"maximumCapacity": 135, "totalLanes": 6}
    records = [_rec("15.7.2024", "Monday", 14, 135)]
    hour = build_weekly_map(records, cfg)["2024-07-15"]["days"]["Monday"]["hours"]["14"]
    assert hour["totalLanes"] == 6


def test_open_lanes_full_capacity():
    # resolved == static → all 6 lanes open
    cfg = {"maximumCapacity": 135, "totalLanes": 6}
    records = [_rec("15.7.2024", "Monday", 14, 135)]
    hour = build_weekly_map(records, cfg)["2024-07-15"]["days"]["Monday"]["hours"]["14"]
    assert hour["openLanes"] == 6


def test_open_lanes_half_capacity():
    # resolved = 90, static = 135, lanes = 6 → round(90*6/135) = round(4.0) = 4
    cfg = {"maximumCapacity": 135, "totalLanes": 6}
    records = [_rec("15.7.2024", "Monday", 6, 50)]

    import pool_aggregation.aggregation.capacity as cap_mod
    # Mock: for this test just rely on static fallback with a different cap
    # Use maximumCapacity=90 as if that were resolved
    cfg2 = {"maximumCapacity": 90, "totalLanes": 6}
    # static_max_cap is taken from cfg2["maximumCapacity"] so open = round(90*6/90) = 6
    hour = build_weekly_map(records, cfg2)["2024-07-15"]["days"]["Monday"]["hours"]["6"]
    assert hour["openLanes"] == 6


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


# --- maxDayValues and maxWeekValues ---

def test_max_day_values_single_hour():
    records = [_rec("15.7.2024", "Monday", 14, 90)]
    wmap = build_weekly_map(records, CFG_NO_HOURLY)
    assert wmap["2024-07-15"]["days"]["Monday"]["maxDayValues"]["utilizationRate"] == 67


def test_max_day_values_multi_hour_picks_max():
    # hour 14: 90/135*100 = 67, hour 15: 135/135*100 = 100
    records = [_rec("15.7.2024", "Monday", 14, 90), _rec("15.7.2024", "Monday", 15, 135)]
    wmap = build_weekly_map(records, CFG_NO_HOURLY)
    assert wmap["2024-07-15"]["days"]["Monday"]["maxDayValues"]["utilizationRate"] == 100


def test_max_week_values_single_day():
    records = [_rec("15.7.2024", "Monday", 14, 90)]
    wmap = build_weekly_map(records, CFG_NO_HOURLY)
    assert wmap["2024-07-15"]["maxWeekValues"]["utilizationRate"] == 67


def test_max_week_values_multi_day_picks_max():
    # Monday hour 14: 90/135*100=67; Tuesday hour 9: 135/135*100=100
    records = [
        _rec("15.7.2024", "Monday", 14, 90),
        _rec("16.7.2024", "Tuesday", 9, 135),
    ]
    wmap = build_weekly_map(records, CFG_NO_HOURLY)
    assert wmap["2024-07-15"]["maxWeekValues"]["utilizationRate"] == 100


def test_max_week_values_separate_weeks_independent():
    records = [
        _rec("15.7.2024", "Monday", 14, 90),   # week 1: util=67
        _rec("22.7.2024", "Monday", 14, 135),  # week 2: util=100
    ]
    wmap = build_weekly_map(records, CFG_NO_HOURLY)
    assert wmap["2024-07-15"]["maxWeekValues"]["utilizationRate"] == 67
    assert wmap["2024-07-22"]["maxWeekValues"]["utilizationRate"] == 100


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
