from __future__ import annotations

from pool_aggregation.models.output import PoolBlock
from pool_aggregation.models.records import OccupancyRecord
from pool_aggregation.utils.timezones import hour_start, to_iso8601


_POOL_TYPE_MAP = {
    "insidePool": "inside",
    "outsidePool": "outside",
}


def build_pool_block(pool_name: str, pool_type_key: str, cfg: dict) -> PoolBlock:
    pool_type = _POOL_TYPE_MAP[pool_type_key]
    display_name = cfg.get("customName") or pool_name

    return PoolBlock(
        name=display_name,
        poolType=pool_type,
        maximumCapacity=cfg["maximumCapacity"],
        totalLanes=cfg.get("totalLanes"),
        weekdaysOpeningHours=cfg["weekdaysOpeningHours"],
        weekendOpeningHours=cfg["weekendOpeningHours"],
        todayClosed=cfg.get("todayClosed", False),
        temporarilyClosed=cfg.get("temporarilyClosed") or None,
    )


def build_data_range(records: list[OccupancyRecord]) -> dict | None:
    if not records:
        return None
    first = min(records, key=lambda r: (r.date_str.split(".")[::-1], r.time_str))
    last = max(records, key=lambda r: (r.date_str.split(".")[::-1], r.time_str))
    return {
        "firstRecordAt": to_iso8601(hour_start(first.date_str, first.hour)),
        "lastRecordAt": to_iso8601(hour_start(last.date_str, last.hour)),
    }
