"""Performance test for guarded configuration generation."""
from __future__ import annotations

import time

from config_generators.cisco.ios_xe_generator import IOSXEGenerator


def test_guarded_config_generation_speed_for_repeated_devices():
    generator = IOSXEGenerator()
    started = time.perf_counter()
    results = []
    for index in range(100):
        result = generator.generate({"device": {"device_id": f"PERF-{index:03d}", "platform": "ios_xe", "os_version": "17.9"}, "features": [], "decision_ids": [f"DEC-{index:03d}"]}, production=False)
        results.append(result)
    elapsed = time.perf_counter() - started
    assert elapsed < 10.0
    assert len(results) == 100
    assert all(item.artifact.status == "generated_empty_config" for item in results)
    assert all(item.artifact.secret_references == () for item in results)
