from __future__ import annotations
import json
from pathlib import Path


def write_json(path: Path | str, payload: dict) -> None:
    """Write payload as deterministic, pretty-printed UTF-8 JSON."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False, sort_keys=False)
        f.write("\n")
