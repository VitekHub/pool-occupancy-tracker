from pathlib import Path
from pool_aggregation.io.csv_reader import read_records
from pool_aggregation.models.records import OccupancyRecord

FIXTURE = Path(__file__).parent / "fixtures" / "sample_occupancy.csv"


def test_reads_valid_rows():
    records = read_records(FIXTURE)
    assert len(records) == 3


def test_first_record_fields():
    records = read_records(FIXTURE)
    r = records[0]
    assert r.date_str == "15.7.2024"
    assert r.day == "Monday"
    assert r.time_str == "14:15"
    assert r.occupancy == 42
    assert r.hour == 14


def test_missing_file_returns_empty():
    records = read_records("/nonexistent/path.csv")
    assert records == []


def test_bad_row_skipped():
    records = read_records(FIXTURE)
    # "bad-line-missing-fields" should be silently skipped
    assert all(isinstance(r, OccupancyRecord) for r in records)
