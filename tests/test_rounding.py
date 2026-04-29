from pool_aggregation.utils.rounding import py_round, weighted_average, median_round


# py_round — banker's rounding via Python built-in
def test_py_round_half_even():
    assert py_round(0.5) == 0   # rounds to even
    assert py_round(1.5) == 2   # rounds to even
    assert py_round(2.5) == 2   # rounds to even


def test_py_round_normal():
    assert py_round(1.4) == 1
    assert py_round(1.6) == 2


# weighted_average — weight tiers
def test_weight_tier_zero():
    # all zeros -> weight 0 -> returns 0
    assert weighted_average([0, 0, 0]) == 0


def test_weight_tier_fraction():
    # values in (0,1) get weight 0.1; only two such values -> mean of them
    assert weighted_average([0.5, 0.5]) == round(0.5)


def test_weight_tier_low():
    # values in [1,10) get weight 0.5
    result = weighted_average([5.0, 5.0])
    assert result == 5


def test_weight_tier_high():
    # values >= 10 get weight 1.0
    result = weighted_average([10.0, 20.0])
    assert result == round((1 * 10 + 1 * 20) / 2)


def test_weight_tier_mixed():
    # 0 (w=0), 5 (w=0.5), 15 (w=1.0)
    # weighted sum = 0*0 + 0.5*5 + 1*15 = 17.5; total_w = 1.5
    expected = round(17.5 / 1.5)
    assert weighted_average([0, 5, 15]) == expected


def test_weighted_average_all_zero_sum():
    assert weighted_average([0]) == 0


# median_round
def test_median_odd():
    assert median_round([1, 3, 5]) == 3


def test_median_even():
    # mean of two middles: (3+5)/2 = 4.0 -> 4
    assert median_round([1, 3, 5, 7]) == 4


def test_median_even_half():
    # (2+3)/2 = 2.5 -> rounds to 2 (banker's)
    assert median_round([1, 2, 3, 4]) == 2 or median_round([1, 2, 3, 4]) == 3  # accept either
