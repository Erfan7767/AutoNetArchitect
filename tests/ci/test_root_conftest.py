"""Contract tests for the root pytest fixture configuration."""

from __future__ import annotations

from pathlib import Path
from typing import Any


def test_project_root_fixture(project_root: Path) -> None:
    """Ensure the project_root fixture resolves the repository root."""
    assert project_root.is_dir()
    assert (project_root / "pyproject.toml").is_file()
    assert (project_root / "tests").is_dir()


def test_test_data_dir_fixture(test_data_dir: Path) -> None:
    """Ensure the test data fixture points at the repository fixture tree."""
    assert test_data_dir.is_dir()
    assert (test_data_dir / "golden_projects").is_dir()
    assert (test_data_dir / "expected_outputs").is_dir()


def test_tmp_project_dir_fixture_is_isolated(tmp_project_dir: Path) -> None:
    """Ensure each temporary project directory is created and writable."""
    assert tmp_project_dir.name == "test_project"
    assert tmp_project_dir.is_dir()
    marker = tmp_project_dir / "fixture-marker.txt"
    marker.write_text("fixture-only", encoding="utf-8")
    assert marker.read_text(encoding="utf-8") == "fixture-only"


def test_sample_requirements_fixture_is_explicit_test_data(sample_requirements: dict[str, Any]) -> None:
    """Ensure the synthetic requirements fixture has the requested deterministic shape."""
    assert sample_requirements["organization"] == {"name": "Test Corp", "type": "enterprise", "size": "medium"}
    sites = sample_requirements["sites"]
    assert isinstance(sites, list)
    assert sites == [{"name": "HQ", "type": "headquarters", "users": 500, "floors": 5}]
    network = sample_requirements["network"]
    assert network == {"greenfield": True, "internet_required": True, "wireless_required": True, "voice_required": True}
