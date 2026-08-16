"""Dynamic package initializer coverage for AutoNetArchitect source trees."""

from __future__ import annotations

from pathlib import Path
from typing import Final

ROOT: Final[Path] = Path(__file__).resolve().parents[2]
NON_PACKAGE_PARTS: Final[frozenset[str]] = frozenset({".git", ".tox", ".nox", ".venv", "build", "dist", "__pycache__", "tests", "scripts", "node_modules"})


def _is_source_python_file(path: Path) -> bool:
    """Return whether a Python file belongs to an importable source tree."""
    relative_parts = path.relative_to(ROOT).parts
    if path.parent == ROOT:
        return False
    return not any(part in NON_PACKAGE_PARTS for part in relative_parts)


def find_package_directories() -> tuple[Path, ...]:
    """Find directories containing Python files that should be explicit packages."""
    candidates = {path.parent for path in ROOT.rglob("*.py") if path.is_file() and _is_source_python_file(path)}
    return tuple(sorted(candidates))


def find_missing_initializers() -> tuple[str, ...]:
    """Return repository-relative source directories missing __init__.py."""
    missing = [
        directory.relative_to(ROOT).as_posix() for directory in find_package_directories() if not (directory / "__init__.py").is_file()
    ]
    return tuple(sorted(missing))


def test_all_packages_have_init() -> None:
    """Every source package directory with Python files must have __init__.py."""
    missing = find_missing_initializers()
    assert missing == (), f"missing package initializers: {missing}"
