from __future__ import annotations
from pathlib import Path

from pool_aggregation.io.capacity_reader import load_hourly_capacity

_DATA_DIR = Path(__file__).parent.parent.parent / "data"


def resolve_max_capacity(pool_cfg: dict, date_str: str, hour: int) -> int:
    """Return the resolved maximumCapacity for (date_str, hour).

    Looks up the data.capacity.raw first, then the data.capacity.forecast;
    finally falls back to the pool's static maximumCapacity.
    """
    fallback: int = pool_cfg.get("maximumCapacity", 0)

    def lookup_in(file_key: str) -> int | None:
        filename = pool_cfg.get("data", {}).get("capacity", {}).get(file_key)
        if not filename:
            return None
        lookup = load_hourly_capacity(_DATA_DIR / filename)
        return lookup.get((date_str, f"{hour:02d}:00"))

    for file_key in ("raw", "forecast"):
        val = lookup_in(file_key)
        if val is not None:
            return val

    return fallback
