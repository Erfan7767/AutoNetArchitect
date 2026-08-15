"""Contract tests for repository Dependabot configuration."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEPENDABOT = PROJECT_ROOT / ".github" / "dependabot.yml"


def _config() -> dict[str, Any]:
    """Load the Dependabot configuration as a mapping."""
    value = yaml.safe_load(DEPENDABOT.read_text(encoding="utf-8"))
    assert isinstance(value, dict)
    return value


def _updates() -> dict[str, dict[str, Any]]:
    """Return update entries keyed by package ecosystem."""
    entries = _config()["updates"]
    assert isinstance(entries, list)
    return {str(entry["package-ecosystem"]): entry for entry in entries}


def test_dependabot_declares_required_ecosystems_and_weekly_schedule() -> None:
    """Ensure pip, GitHub Actions, and Docker receive weekly update proposals."""
    updates = _updates()
    assert set(updates) == {"pip", "github-actions", "docker"}
    for entry in updates.values():
        assert entry["directory"] == "/"
        assert entry["schedule"]["interval"] == "weekly"
        assert entry["open-pull-requests-limit"] == 10


def test_dependabot_assigns_specialized_reviewers_and_labels() -> None:
    """Ensure dependency update classes route to the correct review teams."""
    updates = _updates()
    assert updates["pip"]["reviewers"] == ["autonet-core-team"]
    assert updates["pip"]["labels"] == ["dependencies", "python"]
    assert updates["github-actions"]["reviewers"] == ["autonet-devops-team"]
    assert updates["github-actions"]["labels"] == ["ci/cd", "github-actions"]
    assert updates["docker"]["reviewers"] == ["autonet-devops-team"]
    assert updates["docker"]["labels"] == ["docker"]


def test_dependabot_blocks_unreviewed_pip_major_updates() -> None:
    """Ensure pip major updates remain explicit review work rather than auto-flowing."""
    pip_update = _updates()["pip"]
    assert pip_update["versioning-strategy"] == "increase"
    assert pip_update["ignore"] == [{"dependency-name": "*", "update-types": ["version-update:semver-major"]}]


def test_dependabot_preserves_dependency_grouping() -> None:
    """Ensure production and development Python updates remain separately grouped."""
    groups = _updates()["pip"]["groups"]
    assert groups["runtime-dependencies"]["dependency-type"] == "production"
    assert groups["development-dependencies"]["dependency-type"] == "development"
    assert _updates()["github-actions"]["groups"]["github-actions"]["patterns"] == ["*"]
