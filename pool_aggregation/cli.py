from __future__ import annotations
from pathlib import Path

from pool_aggregation.aggregation.bucketing import available_week_ids
from pool_aggregation.aggregation.current import build_current_occupancy
from pool_aggregation.aggregation.pool_block import build_data_range
from pool_aggregation.aggregation.overall import build_overall_map
from pool_aggregation.aggregation.weekly import build_weekly_map
from pool_aggregation.config import load_pool_config
from pool_aggregation.io.csv_reader import read_records
from pool_aggregation.io.json_writer import write_json
from pool_aggregation.models.pool import iter_pools
from pool_aggregation.utils.timezones import now_prague, to_iso8601

_DATA_DIR = Path(__file__).parent.parent / "data"


def _build_payload(generated_at: str) -> dict:
    return {
        "schemaVersion": 1,
        "generatedAt": generated_at,
        "timezone": "Europe/Prague",
        "dataRange": None,
    }

def build_and_write_payload(path: Path, payload: dict) -> None:
    write_json(path, payload)
    print(f"Wrote {path.relative_to(path.parents[1]) if len(path.parents) > 1 else path.name}")

def process_pool(pool_name: str, pool_cfg: dict, data_dir: Path, output_dir: Path, generated_at: str, now) -> None:
    csv_file = pool_cfg.get("data", {}).get("occupancy", {}).get("raw", "")
    if not csv_file:
        print(f"Skipping {pool_name}: no occupancy data configured")
        return

    csv_path = data_dir / csv_file
    records = read_records(csv_path)

    data_range = build_data_range(records)
    weekly_map = build_weekly_map(records, pool_cfg)
    available_weeks = available_week_ids(records, weekly_map.keys())
    overall_map = build_overall_map(weekly_map)
    current_occ = build_current_occupancy(records, pool_cfg, overall_map, now)

    # overall
    overall_file = pool_cfg.get("data", {}).get("occupancy", {}).get("overall", "")
    if not overall_file:
        print(f"Skipping {pool_name}: no occupancy overall file defined")
    else:
        overall_payload = _build_payload(generated_at)
        overall_payload.update({
            "poolName": pool_name,
            "dataRange": data_range,
            "currentOccupancy": current_occ,
            "overallOccupancyMap": overall_map,
        })
        overall_path = output_dir / overall_file
        build_and_write_payload(overall_path, overall_payload)

    # weekly
    weekly_file = pool_cfg.get("data", {}).get("occupancy", {}).get("weekly", "")
    if not weekly_file:
        print(f"Skipping {pool_name}: no occupancy weekly file defined")
    else:
        weekly_payload = _build_payload(generated_at)
        weekly_payload.update({
            "poolName": pool_name,
            "dataRange": data_range,
            "availableWeekIds": available_weeks,
            "weeklyOccupancyMap": weekly_map,
        })
        weekly_path = output_dir / weekly_file
        build_and_write_payload(weekly_path, weekly_payload)

def main(clock=None, data_dir: Path = _DATA_DIR, output_dir: Path = _DATA_DIR) -> int:
    now = now_prague(clock)
    generated_at = to_iso8601(now)
    cfg = load_pool_config(data_dir / "pool_occupancy_config.json")

    for pool_name, pool_cfg in iter_pools(cfg):
        process_pool(pool_name, pool_cfg, data_dir, output_dir, generated_at, now)

    return 0
