from __future__ import annotations
from typing import TypedDict


class PoolBlock(TypedDict):
    name: str
    poolType: str  # "inside" | "outside"


class DataRange(TypedDict):
    firstRecordAt: str
    lastRecordAt: str
