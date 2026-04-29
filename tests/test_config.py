from pathlib import Path
from pool_aggregation.config import load_pool_config
from pool_aggregation.models.pool import iter_pool_types

FIXTURE = Path(__file__).parent / "fixtures" / "config_snippet.json"


def test_load_returns_list():
    cfg = load_pool_config(FIXTURE)
    assert isinstance(cfg, list)
    assert len(cfg) == 2


def test_iter_pool_types_order():
    cfg = load_pool_config(FIXTURE)
    result = list(iter_pool_types(cfg))
    assert result[0] == ("Pool Alpha", "insidePool", cfg[0]["insidePool"])
    assert result[1] == ("Pool Alpha", "outsidePool", cfg[0]["outsidePool"])
    assert result[2] == ("Pool Beta", "outsidePool", cfg[1]["outsidePool"])


def test_iter_pool_types_count():
    cfg = load_pool_config(FIXTURE)
    assert len(list(iter_pool_types(cfg))) == 3


def test_iter_pool_types_yields_raw_dict():
    cfg = load_pool_config(FIXTURE)
    for pool_name, pool_type_key, raw in iter_pool_types(cfg):
        assert isinstance(pool_name, str)
        assert pool_type_key in ("insidePool", "outsidePool")
        assert isinstance(raw, dict)
        assert "csvFile" in raw
