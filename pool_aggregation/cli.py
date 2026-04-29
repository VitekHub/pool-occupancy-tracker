from __future__ import annotations
from pathlib import Path

from pool_aggregation.config import load_pool_config
from pool_aggregation.io.csv_reader import read_records
from pool_aggregation.io.json_writer import write_json
from pool_aggregation.models.pool import iter_pool_types

_DATA_DIR = Path(__file__).parent.parent / "data"
_OUTPUT_DIR = _DATA_DIR / "aggregation"


def _stub_payload() -> dict:
    return {
        "schemaVersion": 1,
        "generatedAt": None,
        "timezone": "Europe/Prague",
        "pool": {},
        "dataRange": None,
        "currentOccupancy": None,
        "availableWeekIds": [],
        "weeklyOccupancyMap": {},
        "overallOccupancyMap": {},
    }


def main() -> int:
    cfg = load_pool_config()
    for pool_name, pool_type_key, pool_type_cfg in iter_pool_types(cfg):
        csv_file = pool_type_cfg.get("csvFile", "")
        csv_path = _DATA_DIR / csv_file
        read_records(csv_path)  # parse (unused in stub but validates the path)

        payload = _stub_payload()
        out_path = _OUTPUT_DIR / f"{csv_file}.json"
        write_json(out_path, payload)
        print(f"Wrote {out_path.name}")
    return 0
