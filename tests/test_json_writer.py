import json
from pathlib import Path
from pool_aggregation.io.json_writer import write_json


def test_roundtrip(tmp_path):
    payload = {"z": 1, "a": 2, "m": [3, 4]}
    out = tmp_path / "out.json"
    write_json(out, payload)
    loaded = json.loads(out.read_text(encoding="utf-8"))
    assert loaded == payload


def test_deterministic_key_order(tmp_path):
    payload = {"z": 1, "a": 2, "m": 3}
    out = tmp_path / "out.json"
    write_json(out, payload)
    text = out.read_text(encoding="utf-8")
    keys = [line.strip().split(":")[0].strip('"') for line in text.splitlines() if ":" in line]
    assert keys == list(payload.keys())


def test_utf8_non_ascii(tmp_path):
    payload = {"name": "Kraví Hora"}
    out = tmp_path / "out.json"
    write_json(out, payload)
    text = out.read_text(encoding="utf-8")
    assert "Kraví Hora" in text


def test_creates_parent_dirs(tmp_path):
    out = tmp_path / "nested" / "deep" / "out.json"
    write_json(out, {"x": 1})
    assert out.exists()
