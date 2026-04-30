from pool_aggregation.aggregation.pool_block import build_pool_block


def test_inside_pool_type(inside_pool_cfg):
    block = build_pool_block("Kraví Hora", "insidePool", inside_pool_cfg)
    assert block["poolType"] == "inside"


def test_outside_pool_type(outside_pool_cfg):
    block = build_pool_block("Koupaliště Dobrák", "outsidePool", outside_pool_cfg)
    assert block["poolType"] == "outside"


def test_inside_pool_name(inside_pool_cfg):
    block = build_pool_block("Kraví Hora", "insidePool", inside_pool_cfg)
    assert block["name"] == "Kraví Hora"


def test_custom_name_overrides_pool_name():
    cfg = {
        "customName": "Bazény a posilovna",
    }
    block = build_pool_block("Aquapark Kohoutovice", "outsidePool", cfg)
    assert block["name"] == "Bazény a posilovna"


def test_only_name_and_pooltype_fields():
    """PoolBlock should only have name and poolType."""
    cfg = {
        "customName": "Test Pool",
        "weekdaysOpeningHours": "6-22",
        "weekendOpeningHours": "8-22",
        "maximumCapacity": 267,
        "totalLanes": 8,
        "todayClosed": False,
        "temporarilyClosed": "1.1.2025 - 31.12.2025",
    }
    block = build_pool_block("Original Name", "insidePool", cfg)
    assert set(block.keys()) == {"name", "poolType"}
