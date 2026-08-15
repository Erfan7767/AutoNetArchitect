"""Contract tests for the repository Makefile developer command surface."""

from __future__ import annotations

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
MAKEFILE = PROJECT_ROOT / "Makefile"


def _makefile_text() -> str:
    """Return the current Makefile text."""
    return MAKEFILE.read_text(encoding="utf-8")


def test_makefile_declares_requested_command_surface() -> None:
    """Ensure the Makefile exposes the requested developer workflow targets."""
    text = _makefile_text()
    required_targets = {
        "help",
        "install",
        "install-dev",
        "lint",
        "format",
        "typecheck",
        "test",
        "test-unit",
        "test-integration",
        "test-e2e",
        "security",
        "coverage",
        "docs",
        "clean",
        "docker",
        "docker-dev",
        "run-api",
        "run-ui",
        "run-cli",
        "test-all",
        "test-parallel",
        "db-migrate",
        "check-all",
    }
    for target in required_targets:
        assert f"{target}:" in text


def test_makefile_preserves_project_specific_validation_boundaries() -> None:
    """Ensure local commands use the repository's declared validation boundaries."""
    text = _makefile_text()
    assert "tests/unit/ tests/ci/" in text
    assert "--cov-config=coverage_config/.coveragerc" in text
    assert "scripts/run_security_scan.sh" in text
    assert "tests/integration/" in text
    assert "tests/e2e/" in text
    assert "tests/chaos/" in text
    assert "mkdocs build --strict --config-file docs/mkdocs.yml" in text


def test_makefile_uses_actual_v1_entry_points() -> None:
    """Ensure API, UI, and CLI targets point to the implemented V1 entry points."""
    text = _makefile_text()
    assert "$(PYTHON) -m api.server" in text
    assert "streamlit run ui/app.py" in text
    assert "$(PYTHON) -m autonetarchitect --help" in text
    assert "system db migrate" in text


def test_check_all_keeps_mandatory_local_gates() -> None:
    """Ensure check-all includes lint, typing, tests, and security scanning."""
    text = _makefile_text()
    assert "check-all: lint typecheck test-unit security" in text


def test_parallel_testing_declares_its_optional_tooling() -> None:
    """Ensure the parallel target's xdist dependency is declared in both manifests."""
    requirements = (PROJECT_ROOT / "requirements-dev.txt").read_text(encoding="utf-8")
    pyproject = (PROJECT_ROOT / "pyproject.toml").read_text(encoding="utf-8")
    assert "pytest-xdist>=3.6,<4" in requirements
    assert '"pytest-xdist>=3.6,<4"' in pyproject
