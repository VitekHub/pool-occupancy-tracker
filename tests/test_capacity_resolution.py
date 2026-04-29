from pathlib import Path
import pytest
from pool_aggregation.io.capacity_reader import clear_cache
from pool_aggregation.aggregation.capacity import resolve_max_capacity

FIXTURE_DIR = Path(__file__).parent / "fixtures"


@pytest.fixture(autouse=True)
def reset_cache():
    clear_cache()
    yield
    clear_cache()


def _cfg(max_cap, hourly_file=None):
    cfg = {"maximumCapacity": max_cap}
    if hourly_file:
        cfg["hourlyMaxCapacity"] = hourly_file
    return cfg


def test_no_hourly_file_returns_static(monkeypatch):
    cfg = _cfg(135)
    assert resolve_max_capacity(cfg, "15.07.2024", 14) == 135


def test_hit_returns_csv_value(monkeypatch, tmp_path):
    csv_path = tmp_path / "cap.csv"
    csv_path.write_text("Date,Day,Hour,Maximum Occupancy\n15.07.2024,Monday,14:00:00,90\n")

    # Patch _DATA_DIR inside the module
    import pool_aggregation.aggregation.capacity as cap_mod
    monkeypatch.setattr(cap_mod, "_DATA_DIR", tmp_path)

    cfg = _cfg(135, "cap.csv")
    assert resolve_max_capacity(cfg, "15.07.2024", 14) == 90


def test_miss_falls_back_to_static(monkeypatch, tmp_path):
    csv_path = tmp_path / "cap.csv"
    csv_path.write_text("Date,Day,Hour,Maximum Occupancy\n15.07.2024,Monday,06:00:00,45\n")

    import pool_aggregation.aggregation.capacity as cap_mod
    monkeypatch.setattr(cap_mod, "_DATA_DIR", tmp_path)

    cfg = _cfg(135, "cap.csv")
    # hour 14 not in CSV → fallback
    assert resolve_max_capacity(cfg, "15.07.2024", 14) == 135


def test_missing_csv_falls_back_to_static(monkeypatch, tmp_path):
    import pool_aggregation.aggregation.capacity as cap_mod
    monkeypatch.setattr(cap_mod, "_DATA_DIR", tmp_path)

    cfg = _cfg(200, "no_such_file.csv")
    assert resolve_max_capacity(cfg, "15.07.2024", 14) == 200


def test_hhmm_hour_key_matches(monkeypatch, tmp_path):
    csv_path = tmp_path / "cap.csv"
    csv_path.write_text("Date,Day,Hour,Maximum Occupancy\n16.07.2024,Tuesday,09:00,45\n")

    import pool_aggregation.aggregation.capacity as cap_mod
    monkeypatch.setattr(cap_mod, "_DATA_DIR", tmp_path)

    cfg = _cfg(135, "cap.csv")
    assert resolve_max_capacity(cfg, "16.07.2024", 9) == 45
