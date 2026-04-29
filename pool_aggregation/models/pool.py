from __future__ import annotations
from dataclasses import dataclass
from typing import Iterator


POOL_TYPE_KEYS = ("insidePool", "outsidePool")


@dataclass
class PoolTypeConfig:
    pool_name: str
    pool_type: str  # "insidePool" or "outsidePool"
    raw: dict


@dataclass
class PoolConfig:
    name: str
    pool_types: list[PoolTypeConfig]


def iter_pool_types(cfg: list[dict]) -> Iterator[tuple[str, str, dict]]:
    """Yield (pool_name, pool_type_key, pool_type_raw_dict) for every pool-type."""
    for pool in cfg:
        pool_name = pool["name"]
        for key in POOL_TYPE_KEYS:
            if key in pool:
                yield pool_name, key, pool[key]
