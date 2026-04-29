from __future__ import annotations
from typing import TypedDict


class PoolBlock(TypedDict):
    name: str
    poolType: str  # "inside" | "outside"
    maximumCapacity: int
    totalLanes: int | None
    weekdaysOpeningHours: str
    weekendOpeningHours: str
    todayClosed: bool
    temporarilyClosed: str | None


class DataRange(TypedDict):
    firstRecordAt: str
    lastRecordAt: str
