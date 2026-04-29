from pool_aggregation.config import load_pool_config
from pool_aggregation.models.pool import iter_pool_types


def main() -> int:
    cfg = load_pool_config()
    for pool_name, pool_type_key, _pool_type_cfg in iter_pool_types(cfg):
        print(f"{pool_name} / {pool_type_key}")
    return 0
