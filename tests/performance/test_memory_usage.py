"""Memory-bound performance test for project persistence."""
from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
import tracemalloc

from persistence.project_persistence import ProjectPersistence
from tests.performance.test_large_project import _large_project


def test_large_project_peak_memory_stays_bounded():
    with TemporaryDirectory() as tmp:
        store = ProjectPersistence(Path(tmp) / "projects")
        payload = _large_project()
        tracemalloc.start()
        store.save("MemoryProject", payload | {"project_id": "MemoryProject"})
        loaded, _result = store.load("MemoryProject")
        _current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        assert len(loaded["devices"]) == 500
        assert peak < 128 * 1024 * 1024
