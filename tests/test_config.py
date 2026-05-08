from pathlib import Path
from pool_aggregation.config import load_pool_config
from pool_aggregation.models.pool import iter_pools

FIXTURE = Path(__file__).parent / "fixtures" / "config_snippet.json"


def test_load_returns_list():
    cfg = load_pool_config(FIXTURE)
    assert isinstance(cfg, list)
    assert len(cfg) == 3


def test_iter_pools_order():
    cfg = load_pool_config(FIXTURE)
    result = list(iter_pools(cfg))
    assert result[0] == ("Pool Alpha (Inside)", cfg[0])
    assert result[1] == ("Pool Alpha (Outside)", cfg[1])
    assert result[2] == ("Pool Beta", cfg[2])


def test_iter_pools_count():
    cfg = load_pool_config(FIXTURE)
    assert len(list(iter_pools(cfg))) == 3


def test_iter_pools_yields_pool_cfg():
    cfg = load_pool_config(FIXTURE)
    for pool_name, pool_cfg in iter_pools(cfg):
        assert isinstance(pool_name, str)
        assert isinstance(pool_cfg, dict)
        assert "data" in pool_cfg
        assert "occupancy" in pool_cfg["data"]
        assert "raw" in pool_cfg["data"]["occupancy"]
