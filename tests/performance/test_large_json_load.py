"""Performance test for large JSON fixture load and structural validation."""
from __future__ import annotations

import json
from pathlib import Path
from tempfile import TemporaryDirectory
import time

from tests.performance.test_large_project import _large_project


def test_large_json_load_is_bounded_and_structurally_complete():
    payload = _large_project()
    encoded = json.dumps(payload, sort_keys=True, ensure_ascii=False)
    with TemporaryDirectory() as tmp:
        target = Path(tmp) / "large.json"
        target.write_text(encoded, encoding="utf-8")
        started = time.perf_counter()
        loaded = json.loads(target.read_text(encoding="utf-8"))
        elapsed = time.perf_counter() - started
        assert elapsed < 5.0
        assert loaded["project_id"] == "LargeDeterministicProject"
        assert len(loaded["devices"]) == 500
        assert len(loaded["sites"]) == 20
