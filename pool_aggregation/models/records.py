from __future__ import annotations
from dataclasses import dataclass


@dataclass(frozen=True)
class OccupancyRecord:
    date_str: str   # d.M.yyyy
    day: str        # English weekday name
    time_str: str   # HH:mm
    occupancy: int
    hour: int       # 0-23
