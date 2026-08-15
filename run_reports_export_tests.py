"""Run Reports, Export, and As-Built tests without pytest."""
from __future__ import annotations
import importlib.util
from pathlib import Path
import traceback
TEST_FILES = ("test_pdf_generator.py", "test_excel_generator.py", "test_word_generator.py", "test_diagram_generator.py", "test_as_built_generator.py", "test_handover_pack_generator.py", "test_project_exporter.py", "test_config_exporter.py")
def load_module(path: Path):
    """Load one test module."""
    spec = importlib.util.spec_from_file_location(f"reports_tests_{path.stem}", path)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module); return module
def main() -> int:
    """Execute all report/export tests."""
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
