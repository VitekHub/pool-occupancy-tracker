from __future__ import annotations
from pathlib import Path

from pool_aggregation.io.capacity_reader import load_hourly_capacity

_DATA_DIR = Path(__file__).parent.parent.parent / "data"


def resolve_max_capacity(pool_type_cfg: dict, date_str: str, hour: int) -> int:
    """Return the resolved maximumCapacity for (date_str, hour).

    Looks up the hourlyMaxCapacity CSV when configured; falls back to the
    pool's static maximumCapacity when the CSV is absent or the row is missing.
    """
    fallback: int = pool_type_cfg.get("maximumCapacity", 0)
    hourly_file = pool_type_cfg.get("hourlyMaxCapacity")
    if not hourly_file:
        return fallback

    lookup = load_hourly_capacity(_DATA_DIR / hourly_file)
    hour_key = f"{hour:02d}:00"
    value = lookup.get((date_str, hour_key))
    return value if value is not None else fallback
