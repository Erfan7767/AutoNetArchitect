"""Run Incident Response Engine tests without pytest."""

from __future__ import annotations

import importlib.util
from pathlib import Path
import traceback

TEST_FILES = tuple(sorted({path.name for path in Path("/home/ubuntu/AutoNetArchitect/tests").glob("test_incident*.py")} | {"test_severity_classifier.py", "test_impact_assessor.py", "test_containment_planner.py", "test_eradication_planner.py", "test_recovery_planner.py", "test_escalation_engine.py", "test_communication_manager.py", "test_timeline_recorder.py", "test_war_room_coordinator.py", "test_sla_tracker.py", "test_post_incident_reviewer.py", "test_runbook_executor.py", "test_auto_detection_rules.py"}))


def load_module(path: Path):
    """Load one incident test module."""
    name = f"incident_tests_{path.stem}"
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main() -> int:
    """Execute test functions and return a shell status."""
    root = Path("/home/ubuntu/AutoNetArchitect/tests")
    total = 0
    failures: list[str] = []
    for filename in TEST_FILES:
        module = load_module(root / filename)
        for name in sorted(item for item in dir(module) if item.startswith("test_")):
            candidate = getattr(module, name)
            if not callable(candidate):
                continue
            total += 1
            try:
                candidate()
                print(f"PASS {filename}::{name}")
            except Exception:
                failures.append(f"{filename}::{name}")
                print(f"FAIL {filename}::{name}")
                traceback.print_exc()
    print(f"Executed {total} tests; failures={len(failures)}")
    for failure in failures:
        print(f"- {failure}")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
