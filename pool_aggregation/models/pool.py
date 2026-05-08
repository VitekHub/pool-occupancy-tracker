from __future__ import annotations
from typing import Iterator


def iter_pools(cfg: list[dict]) -> Iterator[tuple[str, dict]]:
    """Yield (pool_name, pool_cfg) for every pool in the config.
    
    Each pool entry contains all configuration including data file paths
    directly on the pool object (not nested under insidePool/outsidePool).
    """
    for pool in cfg:
        pool_name = pool["name"]
        yield pool_name, pool
