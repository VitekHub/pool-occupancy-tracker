from pool_aggregation.aggregation.pool_block import build_data_range
from pool_aggregation.models.records import OccupancyRecord


def test_empty_csv_returns_none():
    assert build_data_range([]) is None


def test_data_range_keys(sample_records):
    dr = build_data_range(sample_records)
    assert "firstRecordAt" in dr
    assert "lastRecordAt" in dr


def test_first_record_is_earliest(sample_records):
    dr = build_data_range(sample_records)
    # 15.7.2024 14:xx < 16.7.2024 09:xx
    assert "2024-07-15T14:" in dr["firstRecordAt"]


def test_last_record_is_latest(sample_records):
    dr = build_data_range(sample_records)
    assert "2024-07-16T09:" in dr["lastRecordAt"]


def test_single_record_first_equals_last():
    records = [OccupancyRecord(date_str="1.1.2024", day="Monday", time_str="10:00", occupancy=5, hour=10)]
    dr = build_data_range(records)
    assert dr["firstRecordAt"] == dr["lastRecordAt"]


def test_timestamps_are_iso8601_with_offset(sample_records):
    dr = build_data_range(sample_records)
    # Summer → +02:00
    assert "+02:00" in dr["firstRecordAt"]
    assert "+02:00" in dr["lastRecordAt"]
