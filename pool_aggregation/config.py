import json
from pathlib import Path

_DEFAULT_PATH = Path(__file__).parent.parent / "data" / "pool_occupancy_config.json"


def load_pool_config(path: Path | str | None = None) -> list[dict]:
    resolved = Path(path) if path is not None else _DEFAULT_PATH
    with resolved.open(encoding="utf-8") as f:
        return json.load(f)
