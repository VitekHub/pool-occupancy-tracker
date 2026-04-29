import pytest
from pool_aggregation.aggregation.weekly import compute_open_lanes


# --- null propagation ---

def test_null_when_total_lanes_none():
    assert compute_open_lanes(135, None, 135) is None


def test_null_when_static_max_cap_zero():
    assert compute_open_lanes(135, 6, 0) is None


def test_null_when_both_zero_and_none():
    assert compute_open_lanes(0, None, 0) is None


# --- rounding ---

def test_full_capacity_all_lanes_open():
    # 135 * 6 / 135 = 6.0 → 6
    assert compute_open_lanes(135, 6, 135) == 6


def test_half_resolved():
    # 90 * 6 / 135 = 4.0 → 4
    assert compute_open_lanes(90, 6, 135) == 4


def test_round_half_even():
    # 45 * 6 / 135 = 2.0 → 2
    assert compute_open_lanes(45, 6, 135) == 2


def test_fractional_rounds():
    # 100 * 6 / 135 = 4.444... → 4
    assert compute_open_lanes(100, 6, 135) == 4


def test_rounds_up():
    # 113 * 6 / 135 = 5.022... → 5
    assert compute_open_lanes(113, 6, 135) == 5


def test_zero_resolved_cap():
    # 0 * 6 / 135 = 0
    assert compute_open_lanes(0, 6, 135) == 0


def test_single_lane_pool():
    # 50 * 1 / 100 = 0.5 → banker's round → 0
    assert compute_open_lanes(50, 1, 100) == 0


def test_single_lane_full():
    assert compute_open_lanes(100, 1, 100) == 1
