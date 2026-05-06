from __future__ import annotations
import csv
from pathlib import Path

_cache: dict[str, dict[tuple[str, str], int]] = {}


def load_hourly_capacity(path: Path) -> dict[tuple[str, str], int]:
    """Return {(date_str, 'HH:00'): max_occupancy} from a capacity CSV.

    Accepts both 'HH:00:00' and 'HH:00' in the Hour column.
    Result is cached by resolved path string.
    """
    key = str(path.resolve())
    if key in _cache:
        return _cache[key]

    lookup: dict[tuple[str, str], int] = {}
    if path.exists():
        try:
            with path.open(newline="", encoding="utf-8") as f:
                for row in csv.DictReader(f):
                    date = row.get("Date", "").strip()
                    raw_hour = row.get("Hour", "").strip()
                    hour_key = raw_hour[:5] if len(raw_hour) >= 5 else raw_hour
                    try:
                        lookup[(date, hour_key)] = int(row.get("Maximum Occupancy", "").strip())
                    except (ValueError, AttributeError):
                        continue
        except Exception as e:
            print(f"Warning: could not read capacity file {path}: {e}")

    _cache[key] = lookup
    return lookup


def clear_cache() -> None:
    _cache.clear()
