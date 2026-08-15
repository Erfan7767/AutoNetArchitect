"""Root pytest configuration and deterministic test fixtures for AutoNetArchitect."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

import pytest

PROJECT_ROOT: Path = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


@pytest.fixture(scope="session")
def project_root() -> Path:
    """Return the repository root used by the pytest session."""
    return PROJECT_ROOT


@pytest.fixture(scope="session")
def test_data_dir(project_root: Path) -> Path:
    """Return the deterministic test fixture directory."""
    return project_root / "tests" / "fixtures"


@pytest.fixture(scope="function")
def tmp_project_dir(tmp_path: Path) -> Path:
    """Create an isolated temporary project directory for one test."""
    project_dir = tmp_path / "test_project"
    project_dir.mkdir()
    return project_dir


@pytest.fixture(scope="session")
def sample_requirements() -> dict[str, Any]:
    """Return synthetic requirements data for fixture-only tests.

    The values are deliberately limited to tests and must never be interpreted as
    human-supplied production requirements or as evidence about a real site.
    """
    return {
        "organization": {
            "name": "Test Corp",
            "type": "enterprise",
            "size": "medium",
        },
        "sites": [
            {
                "name": "HQ",
                "type": "headquarters",
                "users": 500,
                "floors": 5,
            },
        ],
        "network": {
            "greenfield": True,
            "internet_required": True,
            "wireless_required": True,
            "voice_required": True,
        },
    }
