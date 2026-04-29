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

def test_produces_three_json_files(data_dir, output_dir):
    _run(data_dir, output_dir)
    files = {f.name for f in output_dir.iterdir()}
    assert files == {
        "alpha_inside.csv.json",
        "alpha_outside.csv.json",
        "beta_outside.csv.json",
    }


# --- snapshot: alpha inside pool ---

def test_alpha_inside_snapshot(data_dir, output_dir):
    _run(data_dir, output_dir)
    produced = json.loads((output_dir / "alpha_inside.csv.json").read_text(encoding="utf-8"))
    expected = json.loads((_FIXTURES / "expected_alpha_inside.csv.json").read_text(encoding="utf-8"))
    assert produced == expected


# --- structural checks shared across all outputs ---

@pytest.mark.parametrize("fname", [
    "alpha_inside.csv.json",
    "alpha_outside.csv.json",
    "beta_outside.csv.json",
])
def test_top_level_keys_present(data_dir, output_dir, fname):
    _run(data_dir, output_dir)
    data = json.loads((output_dir / fname).read_text(encoding="utf-8"))
    for key in (
        "schemaVersion", "generatedAt", "timezone", "pool",
        "dataRange", "currentOccupancy", "availableWeekIds",
        "weeklyOccupancyMap", "overallOccupancyMap",
    ):
        assert key in data, f"missing key '{key}' in {fname}"


@pytest.mark.parametrize("fname", [
    "alpha_inside.csv.json",
    "alpha_outside.csv.json",
    "beta_outside.csv.json",
])
def test_generated_at_matches_pinned_clock(data_dir, output_dir, fname):
    _run(data_dir, output_dir)
    data = json.loads((output_dir / fname).read_text(encoding="utf-8"))
    assert data["generatedAt"] == "2024-07-15T14:30:00+02:00"


@pytest.mark.parametrize("fname", [
    "alpha_inside.csv.json",
    "alpha_outside.csv.json",
    "beta_outside.csv.json",
])
def test_current_occupancy_populated(data_dir, output_dir, fname):
    _run(data_dir, output_dir)
    data = json.loads((output_dir / fname).read_text(encoding="utf-8"))
    assert data["currentOccupancy"] is not None


def test_outside_pool_lanes_null(data_dir, output_dir):
    _run(data_dir, output_dir)
    data = json.loads((output_dir / "alpha_outside.csv.json").read_text(encoding="utf-8"))
    assert data["currentOccupancy"]["totalLanes"] is None
    assert data["currentOccupancy"]["openLanes"] is None


def test_inside_pool_lanes_not_null(data_dir, output_dir):
    _run(data_dir, output_dir)
    data = json.loads((output_dir / "alpha_inside.csv.json").read_text(encoding="utf-8"))
    assert data["currentOccupancy"]["totalLanes"] == 4
    assert data["currentOccupancy"]["openLanes"] is not None


def test_available_week_ids_ascending(data_dir, output_dir):
    _run(data_dir, output_dir)
    data = json.loads((output_dir / "alpha_inside.csv.json").read_text(encoding="utf-8"))
    ids = data["availableWeekIds"]
    assert ids == sorted(ids)
    assert "2024-07-15" in ids
