"""Run Troubleshooting Engine tests without pytest."""

from __future__ import annotations

import importlib.util
from pathlib import Path
import traceback

TEST_FILES = tuple(sorted(path.name for path in Path("/home/ubuntu/AutoNetArchitect/tests").glob("test_*diagnostic*.py"))) + tuple(sorted(path.name for path in Path("/home/ubuntu/AutoNetArchitect/tests").glob("test_*interpreter*.py"))) + ("test_symptom_classifier.py", "test_hypothesis_engine.py", "test_evidence_collector.py", "test_packet_path_analyzer.py", "test_interface_error_analyzer.py", "test_log_analyzer.py", "test_correlation_engine.py", "test_rca_engine.py", "test_remediation_advisor.py", "test_escalation_advisor.py", "test_diagnostic_reporter.py", "test_diagnostic_session.py", "test_recent_change_correlator.py", "test_known_issue_matcher.py")


def load_module(path: Path):
    """Load one test module."""
    module_name = f"troubleshooting_tests_{path.stem}"
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main() -> int:
    """Run all troubleshooting test functions."""
    root = Path("/home/ubuntu/AutoNetArchitect/tests")
    total = 0
    failures: list[str] = []
    for filename in dict.fromkeys(TEST_FILES):
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
