"""AST-based circular import detection for AutoNetArchitect source packages."""

from __future__ import annotations

import ast
from pathlib import Path
from typing import Final

ROOT: Final[Path] = Path(__file__).resolve().parents[2]
NON_SOURCE_PARTS: Final[frozenset[str]] = frozenset({".git", ".tox", ".nox", ".venv", "build", "dist", "__pycache__", "tests", "scripts"})


def _is_source_path(path: Path) -> bool:
    """Return whether a Python path belongs to an importable source package."""
    relative_parts = path.relative_to(ROOT).parts
    return not any(part in NON_SOURCE_PARTS for part in relative_parts)


def discover_package_roots() -> tuple[str, ...]:
    """Discover top-level source packages with explicit initializers."""
    roots = [
        directory.name
        for directory in ROOT.iterdir()
        if directory.is_dir() and _is_source_path(directory / "__init__.py") and (directory / "__init__.py").is_file()
    ]
    return tuple(sorted(roots))


def module_name_for(path: Path) -> str:
    """Convert a repository-relative Python path to its import module name."""
    relative = path.relative_to(ROOT).with_suffix("")
    parts = list(relative.parts)
    if parts[-1] == "__init__":
        parts.pop()
    return ".".join(parts)


def discover_source_files(package_roots: tuple[str, ...]) -> tuple[Path, ...]:
    """Return all Python source files below discovered package roots."""
    files = [path for package in package_roots for path in (ROOT / package).rglob("*.py") if path.is_file() and _is_source_path(path)]
    return tuple(sorted(files))


def discover_module_names(files: tuple[Path, ...]) -> set[str]:
    """Return all module and package names represented by source files."""
    return {module_name_for(path) for path in files}


def _relative_target(source_path: Path, node: ast.ImportFrom) -> str:
    """Resolve an AST relative import to its absolute candidate module name."""
    source_module = module_name_for(source_path)
    if source_path.name == "__init__.py":
        package_parts = source_module.split(".") if source_module else []
    else:
        package_parts = source_module.rsplit(".", 1)[0].split(".") if "." in source_module else []
    if node.level > 1:
        package_parts = package_parts[: -(node.level - 1)] if node.level - 1 <= len(package_parts) else []
    base = ".".join(package_parts)
    return ".".join(part for part in (base, node.module or "") if part)


def _resolve_known_module(candidate: str, known_modules: set[str]) -> str | None:
    """Resolve a candidate import to its longest known internal module prefix."""
    if not candidate:
        return None
    parts = candidate.split(".")
    for end in range(len(parts), 0, -1):
        prefix = ".".join(parts[:end])
        if prefix in known_modules:
            return prefix
    return None


def internal_imports(path: Path, known_modules: set[str]) -> set[str]:
    """Extract resolved internal imports from one Python source file."""
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    imports: set[str] = set()
    for node in tree.body:
        candidates: list[str] = []
        if isinstance(node, ast.Import):
            candidates.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            target = _relative_target(path, node) if node.level else (node.module or "")
            candidates.append(target)
            candidates.extend(f"{target}.{alias.name}" for alias in node.names if alias.name != "*")
        for candidate in candidates:
            resolved = _resolve_known_module(candidate, known_modules)
            if resolved is not None:
                imports.add(resolved)
    return imports


def build_graph() -> dict[str, set[str]]:
    """Build a module-level internal import graph from AST nodes."""
    package_roots = discover_package_roots()
    files = discover_source_files(package_roots)
    known_modules = discover_module_names(files)
    graph = {module_name: set() for module_name in known_modules}
    for path in files:
        source_module = module_name_for(path)
        graph[source_module].update(dependency for dependency in internal_imports(path, known_modules) if dependency != source_module)
    return graph


def find_cycles(graph: dict[str, set[str]]) -> list[list[str]]:
    """Return deterministic import cycles found by depth-first traversal."""
    cycles: list[list[str]] = []
    visiting: list[str] = []
    visited: set[str] = set()

    def visit(node: str) -> None:
        if node in visiting:
            start = visiting.index(node)
            cycles.append(visiting[start:] + [node])
            return
        if node in visited:
            return
        visiting.append(node)
        for dependency in sorted(graph.get(node, set())):
            visit(dependency)
        visiting.pop()
        visited.add(node)

    for node in sorted(graph):
        visit(node)
    return cycles


def test_no_circular_imports() -> None:
    """Verify that the complete discovered source import graph has no cycles."""
    cycles = find_cycles(build_graph())
    assert cycles == [], f"circular imports detected: {cycles}"
