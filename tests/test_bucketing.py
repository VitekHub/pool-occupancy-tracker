from pool_aggregation.aggregation.bucketing import (
    week_id,
    bucket_records,
    available_week_ids,
)
from pool_aggregation.models.records import OccupancyRecord


def _rec(date_str, day, hour, occupancy=10):
    return OccupancyRecord(date_str=date_str, day=day, time_str=f"{hour:02d}:00",
                           occupancy=occupancy, hour=hour)


# --- week_id ---

def test_week_id_monday():
    assert week_id("15.7.2024") == "2024-07-15"  # Monday


def test_week_id_sunday_belongs_to_previous_monday():
    # Sunday 14 Jul 2024 should map to Mon 8 Jul 2024
    assert week_id("14.7.2024") == "2024-07-08"


def test_week_id_saturday():
    assert week_id("13.7.2024") == "2024-07-08"  # Sat -> Mon 8 Jul


def test_week_id_dst_spring_forward():
    # 31 Mar 2024 (Sunday, last day before DST spring-forward) -> Mon 25 Mar
    assert week_id("31.3.2024") == "2024-03-25"


def test_week_id_dst_fall_back():
    # 27 Oct 2024 (Sunday, DST fall-back night) -> Mon 21 Oct
    assert week_id("27.10.2024") == "2024-10-21"


# --- bucket_records ---

def test_bucket_groups_same_week_day_hour():
    records = [
        _rec("15.7.2024", "Monday", 14),
        _rec("22.7.2024", "Monday", 14),  # different week
        _rec("15.7.2024", "Monday", 14),  # same week/day/hour as first
    ]
    buckets = bucket_records(records)
    assert len(buckets[("2024-07-15", "Monday", 14)]) == 2
    assert len(buckets[("2024-07-22", "Monday", 14)]) == 1


def test_bucket_different_hours_separate():
    records = [_rec("15.7.2024", "Monday", 14), _rec("15.7.2024", "Monday", 15)]
    buckets = bucket_records(records)
    assert ("2024-07-15", "Monday", 14) in buckets
    assert ("2024-07-15", "Monday", 15) in buckets


def test_bucket_empty():
    assert bucket_records([]) == {}


# --- available_week_ids ---

def test_available_week_ids_no_records_returns_current_week():
    result = available_week_ids([])
    # Should contain exactly one entry that is a valid ISO Monday
    assert len(result) == 1
    from datetime import date
    monday = date.fromisoformat(result[0])
    assert monday.weekday() == 0


def test_available_week_ids_ascending():
    records = [_rec("15.7.2024", "Monday", 14), _rec("22.7.2024", "Monday", 14)]
    result = available_week_ids(records)
    assert result == sorted(result)


def test_available_week_ids_only_actual_weeks():
    # data in week of Jul 1 and Jul 22 only — middle week must NOT be present
    records = [_rec("1.7.2024", "Monday", 10), _rec("22.7.2024", "Monday", 10)]
    result = available_week_ids(records)
    assert result == ["2024-07-01", "2024-07-22"]
    assert "2024-07-08" not in result


def test_available_week_ids_deduplicates():
    # multiple records in the same week collapse to one entry
    records = [
        _rec("15.7.2024", "Monday", 10),
        _rec("16.7.2024", "Tuesday", 11),
        _rec("17.7.2024", "Wednesday", 12),
    ]
    result = available_week_ids(records)
    assert result == ["2024-07-15"]


def test_available_week_ids_first_entry_is_earliest_data_monday():
    records = [_rec("22.7.2024", "Monday", 10), _rec("15.7.2024", "Monday", 10)]
    result = available_week_ids(records)
    assert result[0] == "2024-07-15"
