"""Run Compliance layer tests without pytest."""
from __future__ import annotations
import importlib.util
from pathlib import Path
import traceback
TEST_FILES = ("test_compliance_engine.py", "test_scope_definitions.py", "test_hipaa_checker.py", "test_pci_checker.py", "test_iso27001_checker.py", "test_nca_checker.py", "test_cis_benchmark_checker.py")
def load_module(path: Path):
    """Load one test module."""
    spec = importlib.util.spec_from_file_location(f"compliance_tests_{path.stem}", path)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module); return module
def main() -> int:
    """Execute all compliance tests."""
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
