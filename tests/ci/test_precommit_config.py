"""CI contract tests for the repository pre-commit configuration."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Final

import yaml

ROOT: Final[Path] = Path(__file__).resolve().parents[2]
CONFIG_PATH: Final[Path] = ROOT / ".pre-commit-config.yaml"


def repositories() -> list[dict[str, Any]]:
    """Load configured pre-commit repositories."""
    data = yaml.safe_load(CONFIG_PATH.read_text(encoding="utf-8"))
    return list(data["repos"])


def hook_ids(repository: dict[str, Any]) -> set[str]:
    """Return hook identifiers from one repository entry."""
    return {str(hook["id"]) for hook in repository.get("hooks", [])}


def test_precommit_contains_required_repository_hooks() -> None:
    """Require the supplied validation categories in the maintained configuration."""
    repos = repositories()
    by_repo = {str(repo["repo"]): repo for repo in repos}
    assert "https://github.com/pre-commit/pre-commit-hooks" in by_repo
    assert by_repo["https://github.com/pre-commit/pre-commit-hooks"]["rev"] == "v6.0.0"
    assert "https://github.com/astral-sh/ruff-pre-commit" in by_repo
    assert by_repo["https://github.com/astral-sh/ruff-pre-commit"]["rev"] == "v0.16.3"
    assert "https://github.com/python-jsonschema/check-jsonschema" in by_repo
    assert by_repo["https://github.com/python-jsonschema/check-jsonschema"]["rev"] == "0.38.0"
    required_standard = {
        "trailing-whitespace",
        "end-of-file-fixer",
        "check-yaml",
        "check-json",
        "check-toml",
        "check-added-large-files",
        "check-merge-conflict",
        "detect-private-key",
        "no-commit-to-branch",
        "check-ast",
        "debug-statements",
    }
    assert required_standard.issubset(hook_ids(by_repo["https://github.com/pre-commit/pre-commit-hooks"]))
    assert {"ruff-check", "ruff-format"}.issubset(hook_ids(by_repo["https://github.com/astral-sh/ruff-pre-commit"]))
    assert "check-github-workflows" in hook_ids(by_repo["https://github.com/python-jsonschema/check-jsonschema"])


def test_local_hooks_preserve_mypy_bandit_and_warning_boundaries() -> None:
    """Require local checks to use repository policy and keep marker reporting non-blocking."""
    local = next(repo for repo in repositories() if repo["repo"] == "local")
    hooks = {str(hook["id"]): hook for hook in local["hooks"]}
    assert {"mypy", "bandit", "check-no-pass", "check-no-todo"}.issubset(hooks)
    assert hooks["mypy"]["pass_filenames"] is False
    assert hooks["bandit"]["pass_filenames"] is False
    assert hooks["check-no-pass"]["entry"].endswith("scripts/check_no_pass.py")
    assert hooks["check-no-todo"]["entry"].endswith("scripts/check_todo.py")
    assert hooks["check-no-todo"]["verbose"] is True
    content = CONFIG_PATH.read_text(encoding="utf-8")
    assert "-----BEGIN" not in content
    assert "ghp_" not in content
    assert "sk-" not in content
