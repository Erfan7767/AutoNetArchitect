"""Performance test for large deterministic project persistence."""
from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
import time

from persistence.project_persistence import ProjectPersistence


def _large_project() -> dict[str, object]:
    """Build a fixed-size enterprise project without random data."""
    devices = [{"device_id": f"SITE-{site:03d}-DEV-{device:03d}", "vendor": "cisco", "platform": "ios-xe", "role": "access"} for site in range(1, 21) for device in range(1, 26)]
    sites = [{"site_id": f"SITE-{site:03d}", "site_type": "branch", "rooms": [f"MDF-{site:03d}"]} for site in range(1, 21)]
    return {"project_id": "LargeDeterministicProject", "scenario": "performance", "sites": sites, "devices": devices, "requirements": {"segments": ["staff", "guest", "management"], "growth_percent": 30}, "governance": {"supervised_mode": True}}


def test_large_project_save_load_completes_with_integrity():
    with TemporaryDirectory() as tmp:
        store = ProjectPersistence(Path(tmp) / "projects")
        payload = _large_project()
        started = time.perf_counter()
        saved = store.save("LargeDeterministicProject", payload)
        loaded, loaded_result = store.load("LargeDeterministicProject")
        elapsed = time.perf_counter() - started
        assert elapsed < 10.0
        assert len(loaded["devices"]) == 500
        assert len(loaded["sites"]) == 20
        assert saved.checksum == loaded_result.checksum
