import pool_aggregation
from pool_aggregation import cli


def test_main_returns_zero():
    assert cli.main() == 0
