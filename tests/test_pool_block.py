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
        "weekdaysOpeningHours": "6-22",
        "weekendOpeningHours": "8-22",
        "maximumCapacity": 267,
        "todayClosed": False,
        "temporarilyClosed": None,
    }
    block = build_pool_block("Aquapark Kohoutovice", "outsidePool", cfg)
    assert block["name"] == "Bazény a posilovna"


def test_total_lanes_inside(inside_pool_cfg):
    block = build_pool_block("Kraví Hora", "insidePool", inside_pool_cfg)
    assert block["totalLanes"] == 6


def test_total_lanes_outside_is_none(outside_pool_cfg):
    block = build_pool_block("Dobrák", "outsidePool", outside_pool_cfg)
    assert block["totalLanes"] is None


def test_maximum_capacity(inside_pool_cfg):
    block = build_pool_block("Kraví Hora", "insidePool", inside_pool_cfg)
    assert block["maximumCapacity"] == 135


def test_temporarily_closed_string(inside_pool_cfg):
    block = build_pool_block("Kraví Hora", "insidePool", inside_pool_cfg)
    assert block["temporarilyClosed"] == "28.6.2025 - 19.10.2025"


def test_temporarily_closed_none(outside_pool_cfg):
    block = build_pool_block("Dobrák", "outsidePool", outside_pool_cfg)
    assert block["temporarilyClosed"] is None


def test_today_closed_false(outside_pool_cfg):
    block = build_pool_block("Dobrák", "outsidePool", outside_pool_cfg)
    assert block["todayClosed"] is False


def test_opening_hours(inside_pool_cfg):
    block = build_pool_block("Kraví Hora", "insidePool", inside_pool_cfg)
    assert block["weekdaysOpeningHours"] == "6-22"
    assert block["weekendOpeningHours"] == "8-21"
