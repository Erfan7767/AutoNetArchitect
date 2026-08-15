"""Run Traffic Analysis Engine tests without pytest."""
from __future__ import annotations
import importlib.util
from pathlib import Path
import traceback
TEST_FILES = tuple(sorted({path.name for path in Path("/home/ubuntu/AutoNetArchitect/tests").glob("test_traffic*.py")} | {"test_traffic_orchestrator.py", "test_traffic_model.py", "test_traffic_estimator.py", "test_traffic_collector.py", "test_traffic_classifier.py", "test_bandwidth_calculator.py", "test_oversubscription_analyzer.py", "test_bottleneck_detector.py", "test_capacity_planner.py", "test_growth_projector.py", "test_upgrade_recommender.py", "test_baseline_manager.py", "test_anomaly_detector.py", "test_application_profiler.py", "test_flow_analyzer.py", "test_qos_utilization_analyzer.py", "test_wan_utilization_analyzer.py", "test_traffic_reporter.py", "test_traffic_scope_boundary.py"}))
def load_module(path: Path):
    """Load one test module."""
    spec = importlib.util.spec_from_file_location(f"traffic_tests_{path.stem}", path)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module); return module
def main() -> int:
    """Execute all traffic tests."""
    root = Path("/home/ubuntu/AutoNetArchitect/tests"); total = 0; failures = []
    for filename in TEST_FILES:
        module = load_module(root / filename)
        for name in sorted(item for item in dir(module) if item.startswith("test_")):
            candidate = getattr(module, name)
            if not callable(candidate):
                continue
            total += 1
            try:
                candidate(); print(f"PASS {filename}::{name}")
            except Exception:
                failures.append(f"{filename}::{name}"); print(f"FAIL {filename}::{name}"); traceback.print_exc()
    print(f"Executed {total} tests; failures={len(failures)}")
    for failure in failures: print(f"- {failure}")
    return 1 if failures else 0
if __name__ == "__main__":
    raise SystemExit(main())
