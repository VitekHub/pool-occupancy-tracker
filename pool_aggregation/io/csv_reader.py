from __future__ import annotations
import csv
import logging
from pathlib import Path

from pool_aggregation.models.records import OccupancyRecord

logger = logging.getLogger(__name__)


def read_records(path: Path | str) -> list[OccupancyRecord]:
    """Parse a pool occupancy CSV and return valid records; skip bad rows."""
    records: list[OccupancyRecord] = []
    path = Path(path)
    if not path.exists():
        return records
    with path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for lineno, row in enumerate(reader, start=2):
            try:
                norm = {k.lower(): v for k, v in row.items()}
                time_str = norm["time"].strip()
                records.append(OccupancyRecord(
                    date_str=norm["date"].strip(),
                    day=norm["day"].strip(),
                    time_str=time_str,
                    occupancy=int(norm["occupancy"]),
                    hour=int(time_str.split(":")[0]),
                ))
            except (KeyError, ValueError, AttributeError) as exc:
                logger.warning("Skipping row %d in %s: %s", lineno, path.name, exc)
    return records
