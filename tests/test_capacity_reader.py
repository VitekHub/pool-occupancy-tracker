from pathlib import Path
import pytest
from pool_aggregation.io.capacity_reader import load_hourly_capacity, clear_cache

FIXTURE = Path(__file__).parent / "fixtures" / "sample_hourly_capacity.csv"


@pytest.fixture(autouse=True)
def reset_cache():
    clear_cache()
    yield
    clear_cache()


def test_parses_hhmmss_format():
    lookup = load_hourly_capacity(FIXTURE)
    assert lookup[("15.07.2024", "06:00")] == 90


def test_parses_hhmm_format():
    lookup = load_hourly_capacity(FIXTURE)
    assert lookup[("16.07.2024", "09:00")] == 45


def test_multiple_rows():
    lookup = load_hourly_capacity(FIXTURE)
    assert lookup[("15.07.2024", "07:00")] == 112
    assert lookup[("15.07.2024", "14:00")] == 135


def test_missing_file_returns_empty(tmp_path):
    lookup = load_hourly_capacity(tmp_path / "nonexistent.csv")
    assert lookup == {}


def test_result_is_cached():
    first = load_hourly_capacity(FIXTURE)
    second = load_hourly_capacity(FIXTURE)
    assert first is second
