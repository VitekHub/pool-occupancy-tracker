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
        cfg["data"] = {"capacity": {"raw": hourly_file}}
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


def test_raw_has_data_uses_raw(monkeypatch, tmp_path):
    """Test that raw data is used when both raw and forecast have data for the same date."""
    raw_path = tmp_path / "raw.csv"
    forecast_path = tmp_path / "forecast.csv"
    raw_path.write_text("Date,Day,Hour,Maximum Occupancy\n15.07.2024,Monday,14:00:00,90\n")
    forecast_path.write_text("Date,Day,Hour,Maximum Occupancy\n15.07.2024,Monday,14:00:00,80\n")

    import pool_aggregation.aggregation.capacity as cap_mod
    monkeypatch.setattr(cap_mod, "_DATA_DIR", tmp_path)

    cfg = {"maximumCapacity": 135, "data": {"capacity": {"raw": "raw.csv", "forecast": "forecast.csv"}}}
    # Should use raw value (90) not forecast value (80)
    assert resolve_max_capacity(cfg, "15.07.2024", 14) == 90


def test_raw_missing_forecast_has_data_uses_forecast(monkeypatch, tmp_path):
    """Test that forecast data is used when raw is missing data but forecast has it."""
    raw_path = tmp_path / "raw.csv"
    forecast_path = tmp_path / "forecast.csv"
    raw_path.write_text("Date,Day,Hour,Maximum Occupancy\n15.07.2024,Monday,13:00:00,90\n")
    forecast_path.write_text("Date,Day,Hour,Maximum Occupancy\n15.07.2024,Monday,14:00:00,80\n")

    import pool_aggregation.aggregation.capacity as cap_mod
    monkeypatch.setattr(cap_mod, "_DATA_DIR", tmp_path)

    cfg = {"maximumCapacity": 135, "data": {"capacity": {"raw": "raw.csv", "forecast": "forecast.csv"}}}
    # Should use forecast value (80) since raw doesn't have hour 14
    assert resolve_max_capacity(cfg, "15.07.2024", 14) == 80


def test_both_missing_falls_back_to_static(monkeypatch, tmp_path):
    """Test that static capacity is used when both raw and forecast are missing data."""
    raw_path = tmp_path / "raw.csv"
    forecast_path = tmp_path / "forecast.csv"
    raw_path.write_text("Date,Day,Hour,Maximum Occupancy\n15.07.2024,Monday,13:00:00,90\n")
    forecast_path.write_text("Date,Day,Hour,Maximum Occupancy\n15.07.2024,Monday,13:00:00,80\n")

    import pool_aggregation.aggregation.capacity as cap_mod
    monkeypatch.setattr(cap_mod, "_DATA_DIR", tmp_path)

    cfg = {"maximumCapacity": 200, "data": {"capacity": {"raw": "raw.csv", "forecast": "forecast.csv"}}}
    # Should use static value (200) since neither raw nor forecast has hour 14
    assert resolve_max_capacity(cfg, "15.07.2024", 14) == 200


def test_forecast_only_file_missing_uses_static(monkeypatch, tmp_path):
    """Test that static capacity is used when forecast file doesn't exist."""
    raw_path = tmp_path / "raw.csv"
    raw_path.write_text("Date,Day,Hour,Maximum Occupancy\n15.07.2024,Monday,13:00:00,90\n")

    import pool_aggregation.aggregation.capacity as cap_mod
    monkeypatch.setattr(cap_mod, "_DATA_DIR", tmp_path)

    cfg = {"maximumCapacity": 200, "data": {"capacity": {"raw": "raw.csv", "forecast": "missing.csv"}}}
    # Should use static value (200) since forecast file doesn't exist and raw doesn't have hour 14
    assert resolve_max_capacity(cfg, "15.07.2024", 14) == 200


def test_no_raw_file_uses_forecast(monkeypatch, tmp_path):
    """Test that forecast data is used when no raw file is configured."""
    forecast_path = tmp_path / "forecast.csv"
    forecast_path.write_text("Date,Day,Hour,Maximum Occupancy\n15.07.2024,Monday,14:00:00,80\n")

    import pool_aggregation.aggregation.capacity as cap_mod
    monkeypatch.setattr(cap_mod, "_DATA_DIR", tmp_path)

    cfg = {"maximumCapacity": 135, "data": {"capacity": {"forecast": "forecast.csv"}}}
    # Should use forecast value (80) since no raw file is configured
    assert resolve_max_capacity(cfg, "15.07.2024", 14) == 80


def test_no_capacity_files_uses_static(monkeypatch, tmp_path):
    """Test that static capacity is used when no capacity files are configured."""
    import pool_aggregation.aggregation.capacity as cap_mod
    monkeypatch.setattr(cap_mod, "_DATA_DIR", tmp_path)

    cfg = {"maximumCapacity": 300, "data": {"capacity": {}}}
    # Should use static value (300) since no capacity files are configured
    assert resolve_max_capacity(cfg, "15.07.2024", 14) == 300
