"""Contract tests for implementation completeness markers in source files."""

from __future__ import annotations

import ast
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
EXCLUDED_PARTS = frozenset({".git", ".tox", ".nox", ".venv", "build", "dist", "tests", "scripts"})


def _source_files() -> tuple[Path, ...]:
    """Return application Python files outside excluded tooling and test trees."""
    files = [
        path
        for path in PROJECT_ROOT.rglob("*.py")
        if path.is_file() and not any(part in EXCLUDED_PARTS for part in path.relative_to(PROJECT_ROOT).parts)
    ]
    return tuple(sorted(files))


def _has_executable_ellipsis(tree: ast.AST) -> bool:
    """Return whether an AST contains standalone executable ellipsis syntax."""
    for node in ast.walk(tree):
        if isinstance(node, ast.Expr) and isinstance(node.value, ast.Constant) and node.value.value is Ellipsis:
            return True
        if isinstance(node, ast.Return) and isinstance(node.value, ast.Constant) and node.value.value is Ellipsis:
            return True
    return False


def test_source_has_no_executable_placeholder_constructs() -> None:
    """Reject pass, executable ellipsis, or NotImplementedError in application source."""
    findings: list[str] = []
    for path in _source_files():
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        if any(isinstance(node, ast.Pass) for node in ast.walk(tree)):
            findings.append(f"pass:{path.relative_to(PROJECT_ROOT)}")
        if _has_executable_ellipsis(tree):
            findings.append(f"ellipsis:{path.relative_to(PROJECT_ROOT)}")
        if any(
            isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "NotImplementedError"
            for node in ast.walk(tree)
        ):
            findings.append(f"NotImplementedError:{path.relative_to(PROJECT_ROOT)}")
    assert findings == [], f"incomplete source constructs detected: {findings}"
