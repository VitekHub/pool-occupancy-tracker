from __future__ import annotations
import math
from statistics import median


def py_round(x: float) -> int:
    """Round to nearest int using standard 'round half up' logic.
    But rounds to 2 decimal places if x < 0.5.
    """
    if x <= 0:
        return 0
    elif x < 0.5:
        return math.floor(x * 100 + 0.5) / 100
    else:
        return math.floor(x + 0.5)


def _weight(r: float) -> float:
    if r == 0:
        return 0.0
    if r < 1:
        return 0.1
    if r < 10:
        return 0.5
    return 1.0


def weighted_average(values: list[float]) -> int:
    """Weighted average with four weight tiers; returns 0 when sum of weights is 0."""
    total_w = sum(_weight(r) for r in values)
    if total_w == 0:
        return 0
    return py_round(sum(_weight(r) * r for r in values) / total_w)


def median_round(values: list[float]) -> int:
    """Median of values, rounded (even-length: mean of two middles then round)."""
    return py_round(median(values))
