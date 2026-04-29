from __future__ import annotations
from pathlib import Path

from pool_aggregation.aggregation.bucketing import available_week_ids
from pool_aggregation.aggregation.current import build_current_occupancy
from pool_aggregation.aggregation.pool_block import build_data_range, build_pool_block
from pool_aggregation.aggregation.overall import build_overall_map
from pool_aggregation.aggregation.weekly import build_weekly_map
from pool_aggregation.config import load_pool_config
from pool_aggregation.io.csv_reader import read_records
from pool_aggregation.io.json_writer import write_json
from pool_aggregation.models.pool import iter_pool_types
from pool_aggregation.utils.timezones import now_prague, to_iso8601

_DATA_DIR = Path(__file__).parent.parent / "data"
_OUTPUT_DIR = _DATA_DIR / "aggregation"


def _stub_payload(generated_at: str) -> dict:
    return {
        "schemaVersion": 1,
        "generatedAt": generated_at,
        "timezone": "Europe/Prague",
        "pool": {},
        "dataRange": None,
        "currentOccupancy": None,
        "availableWeekIds": [],
        "weeklyOccupancyMap": {},
        "overallOccupancyMap": {},
    }


def main(clock=None, data_dir: Path = _DATA_DIR, output_dir: Path = _OUTPUT_DIR) -> int:
    now = now_prague(clock)
    generated_at = to_iso8601(now)
    cfg = load_pool_config(data_dir / "pool_occupancy_config.json")
    for pool_name, pool_type_key, pool_type_cfg in iter_pool_types(cfg):
        csv_file = pool_type_cfg.get("csvFile", "")
        csv_path = data_dir / csv_file
        records = read_records(csv_path)
        payload = _stub_payload(generated_at)
        payload["pool"] = build_pool_block(pool_name, pool_type_key, pool_type_cfg)
        payload["dataRange"] = build_data_range(records)
        payload["availableWeekIds"] = available_week_ids(records, clock=lambda: now)
        payload["weeklyOccupancyMap"] = build_weekly_map(records, pool_type_cfg)
        payload["overallOccupancyMap"] = build_overall_map(payload["weeklyOccupancyMap"])
        payload["currentOccupancy"] = build_current_occupancy(
            records, pool_type_cfg, payload["overallOccupancyMap"], now
        )
        out_path = output_dir / f"{csv_file}.json"
        write_json(out_path, payload)
        print(f"Wrote {out_path.name}")
    return 0
