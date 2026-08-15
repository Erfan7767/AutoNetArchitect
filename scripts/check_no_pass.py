"""Reject executable Python pass statements outside test files."""

from __future__ import annotations

import ast
import sys
from pathlib import Path
from typing import Final

PROJECT_ROOT: Final[Path] = Path.cwd()


def is_excluded(path: Path) -> bool:
    """Return whether a path belongs to a test tree excluded by policy."""
    try:
        relative = path.resolve().relative_to(PROJECT_ROOT.resolve())
    except ValueError:
        relative = path
    return "tests" in relative.parts


def files_with_pass_statements(paths: list[str]) -> list[str]:
    """Return Python paths containing AST Pass nodes outside tests."""
    findings: list[str] = []
    for raw_path in paths:
        path = Path(raw_path)
        if path.suffix != ".py" or is_excluded(path):
            continue
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        except (OSError, SyntaxError) as error:
            findings.append(f"{path}: cannot parse ({error})")
            continue
        if any(isinstance(node, ast.Pass) for node in ast.walk(tree)):
            findings.append(str(path))
    return findings


def main(argv: list[str] | None = None) -> int:
    """Check supplied paths and return non-zero only for executable pass statements."""
    paths = argv if argv is not None else sys.argv[1:]
    findings = files_with_pass_statements(paths)
    for finding in findings:
        print(f"FORBIDDEN_PASS_STATEMENT {finding}")
    return 1 if findings else 0


if __name__ == "__main__":
    raise SystemExit(main())
