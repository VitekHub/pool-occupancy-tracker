"""End-to-end: CSV fixtures -> CLI -> JSON on disk."""
from __future__ import annotations
import json
import shutil
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import pytest

from pool_aggregation.cli import main
from pool_aggregation.io.capacity_reader import clear_cache

PRAGUE = ZoneInfo("Europe/Prague")
# Pinned to Monday 15 July 2024 14:30 Prague — same week as sample data.
_PINNED = datetime(2024, 7, 15, 14, 30, 0, tzinfo=PRAGUE)
_FIXTURES = Path(__file__).parent / "fixtures"


@pytest.fixture()
def data_dir(tmp_path):
    """Temp data dir with fixture files wired to the config's expected CSV names."""
    (tmp_path / "pool_occupancy_config.json").write_text(
        (_FIXTURES / "config_snippet.json").read_text(encoding="utf-8"),
        encoding="utf-8",
    )
    for name in ["alpha_inside.csv", "alpha_outside.csv", "beta_outside.csv"]:
        shutil.copy(_FIXTURES / "sample_occupancy.csv", tmp_path / name)
    return tmp_path


@pytest.fixture()
def output_dir(tmp_path):
    out = tmp_path / "out"
    out.mkdir()
    return out


@pytest.fixture(autouse=True)
def _clear_capacity_cache():
    clear_cache()
    yield
    clear_cache()


def _run(data_dir, output_dir):
    return main(clock=lambda: _PINNED, data_dir=data_dir, output_dir=output_dir)


# --- exit code ---

def test_cli_exits_zero(data_dir, output_dir):
    assert _run(data_dir, output_dir) == 0


# --- output files created ---

def test_produces_six_json_files(data_dir, output_dir):
    _run(data_dir, output_dir)
    # Check both overall and weekly subdirectories
    overall_dir = output_dir / "overall"
    weekly_dir = output_dir / "weekly"
    overall_files = {f.name for f in overall_dir.iterdir()} if overall_dir.exists() else set()
    weekly_files = {f.name for f in weekly_dir.iterdir()} if weekly_dir.exists() else set()
    assert overall_files == {"alpha_inside_occupancy.json", "alpha_outside_occupancy.json", "beta_outside_occupancy.json"}
    assert weekly_files == {"alpha_inside_occupancy.json", "alpha_outside_occupancy.json", "beta_outside_occupancy.json"}

# --- snapshot: alpha inside pool ---
def test_alpha_inside_overall_snapshot(data_dir, output_dir):
    _run(data_dir, output_dir)
    produced = json.loads((output_dir / "overall/alpha_inside_occupancy.json").read_text(encoding="utf-8"))
    expected = json.loads((_FIXTURES / "expected_alpha_inside_overall_occupancy.json").read_text(encoding="utf-8"))
    assert produced == expected

def test_alpha_inside_weekly_snapshot(data_dir, output_dir):
    _run(data_dir, output_dir)
    produced = json.loads((output_dir / "weekly/alpha_inside_occupancy.json").read_text(encoding="utf-8"))
    expected = json.loads((_FIXTURES / "expected_alpha_inside_weekly_occupancy.json").read_text(encoding="utf-8"))
    assert produced == expected

# --- structural checks for overall files ---
@pytest.mark.parametrize("fname", [
    "alpha_inside_occupancy.json",
    "alpha_outside_occupancy.json",
    "beta_outside_occupancy.json",
])
def test_overall_top_level_keys_present(data_dir, output_dir, fname):
    _run(data_dir, output_dir)
    data = json.loads((output_dir / "overall" / fname).read_text(encoding="utf-8"))
    for key in (
        "schemaVersion", "generatedAt", "timezone", "pool",
        "dataRange", "currentOccupancy", "overallOccupancyMap",
    ):
        assert key in data, f"missing key '{key}' in {fname}"


# --- structural checks for weekly files ---

@pytest.mark.parametrize("fname", [
    "alpha_inside_occupancy.json",
    "alpha_outside_occupancy.json",
    "beta_outside_occupancy.json",
])
def test_weekly_top_level_keys_present(data_dir, output_dir, fname):
    _run(data_dir, output_dir)
    data = json.loads((output_dir / "weekly" / fname).read_text(encoding="utf-8"))
    for key in (
        "schemaVersion", "generatedAt", "timezone", "pool",
        "dataRange", "availableWeekIds", "weeklyOccupancyMap",
    ):
        assert key in data, f"missing key '{key}' in {fname}"


@pytest.mark.parametrize("fname", [
    "alpha_inside_occupancy.json",
    "alpha_outside_occupancy.json",
    "beta_outside_occupancy.json",
])
def test_generated_at_matches_pinned_clock(data_dir, output_dir, fname):
    _run(data_dir, output_dir)
    overall_data = json.loads((output_dir / "overall" / fname).read_text(encoding="utf-8"))
    weekly_data = json.loads((output_dir / "weekly" / fname).read_text(encoding="utf-8"))
    assert overall_data["generatedAt"] == "2024-07-15T14:30:00+02:00"
    assert weekly_data["generatedAt"] == "2024-07-15T14:30:00+02:00"


@pytest.mark.parametrize("fname", [
    "alpha_inside_occupancy.json",
    "alpha_outside_occupancy.json",
    "beta_outside_occupancy.json",
])
def test_current_occupancy_populated(data_dir, output_dir, fname):
    _run(data_dir, output_dir)
    data = json.loads((output_dir / "overall" / fname).read_text(encoding="utf-8"))
    assert data["currentOccupancy"] is not None


def test_pool_block_only_has_name_and_pooltype(data_dir, output_dir):
    _run(data_dir, output_dir)
    data = json.loads((output_dir / "overall" / "alpha_inside_occupancy.json").read_text(encoding="utf-8"))
    assert set(data["pool"].keys()) == {"name", "poolType"}


def test_outside_pool_lanes_in_current_not_pool(data_dir, output_dir):
    _run(data_dir, output_dir)
    data = json.loads((output_dir / "overall" / "alpha_outside_occupancy.json").read_text(encoding="utf-8"))
    # pool block should only have name and poolType
    assert "totalLanes" not in data["pool"]
    # currentOccupancy should have totalLanes
    assert data["currentOccupancy"]["totalLanes"] is None
    assert data["currentOccupancy"]["openLanes"] is None


def test_inside_pool_lanes_not_null(data_dir, output_dir):
    _run(data_dir, output_dir)
    data = json.loads((output_dir / "overall" / "alpha_inside_occupancy.json").read_text(encoding="utf-8"))
    assert data["currentOccupancy"]["totalLanes"] == 4
    assert data["currentOccupancy"]["openLanes"] is not None


def test_available_week_ids_ascending(data_dir, output_dir):
    _run(data_dir, output_dir)
    data = json.loads((output_dir / "weekly" / "alpha_inside_occupancy.json").read_text(encoding="utf-8"))
    ids = data["availableWeekIds"]
    assert ids == sorted(ids)
    assert "2024-07-15" in ids
