"""Nox sessions for AutoNetArchitect quality and release verification."""

from __future__ import annotations

from pathlib import Path
from typing import Final

import nox


PYTHON_VERSIONS: Final[list[str]] = ["3.11", "3.12"]
DEV_REQUIREMENTS: Final[str] = "requirements-dev.txt"
PROJECT_ROOT: Final[Path] = Path(__file__).resolve().parent


@nox.session(python=PYTHON_VERSIONS, reuse_venv=True)
def tests(session: nox.Session) -> None:
    """Run unit, integration, end-to-end, and controlled chaos tests."""
    session.install("-r", DEV_REQUIREMENTS)
    session.run(
        "pytest",
        "tests/unit",
        "tests/integration",
        "tests/e2e",
        "tests/chaos",
        "-v",
        "--tb=short",
        env={"PYTHONPATH": str(PROJECT_ROOT), "AUTONET_RUNTIME_MODE": "test"},
    )


@nox.session(reuse_venv=True)
def lint(session: nox.Session) -> None:
    """Run Ruff lint and format checks."""
    session.install("-r", DEV_REQUIREMENTS)
    session.run("ruff", "check", ".", "--config", "pyproject.toml")
    session.run("ruff", "format", "--check", ".", "--config", "pyproject.toml")


@nox.session(reuse_venv=True)
def typecheck(session: nox.Session) -> None:
    """Run mypy against the installable compatibility namespace."""
    session.install("-r", DEV_REQUIREMENTS)
    session.run("mypy", "autonetarchitect/", "--config-file", "mypy.ini")


@nox.session(reuse_venv=True)
def security(session: nox.Session) -> None:
    """Run static security and dependency vulnerability checks."""
    session.install("-r", DEV_REQUIREMENTS)
    session.run("bandit", "-r", "autonetarchitect/", "-f", "json", "-o", "bandit-report.json", "-ll")
    session.run("pip-audit", "--requirement", "requirements.txt")


@nox.session(reuse_venv=True)
def docs(session: nox.Session) -> None:
    """Build the strict MkDocs documentation site."""
    session.install("-r", DEV_REQUIREMENTS)
    session.run("mkdocs", "build", "--strict", "--config-file", "docs/mkdocs.yml")


@nox.session(reuse_venv=True)
def build(session: nox.Session) -> None:
    """Build and validate the source distribution and wheel."""
    session.install("-r", DEV_REQUIREMENTS)
    session.run("python", "-m", "build")
    session.run("twine", "check", *sorted(str(path) for path in Path("dist").glob("*")))
