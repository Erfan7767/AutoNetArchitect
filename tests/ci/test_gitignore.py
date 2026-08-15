"""Contract tests for repository Git ignore boundaries."""

from __future__ import annotations

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
GITIGNORE = PROJECT_ROOT / ".gitignore"


def _gitignore_text() -> str:
    """Return the repository Git ignore policy."""
    return GITIGNORE.read_text(encoding="utf-8")


def test_gitignore_covers_python_tooling_and_build_outputs() -> None:
    """Ensure generated Python, test, coverage, and package outputs are ignored."""
    text = _gitignore_text()
    for pattern in ("__pycache__/", "*.pyc", "*.pyo", "build/", "dist/", "*.egg-info/", ".tox/", ".nox/", "htmlcov/", "coverage.xml"):
        assert pattern in text


def test_gitignore_covers_local_secrets_and_operational_data() -> None:
    """Ensure vaults, keys, databases, projects, caches, and backups are ignored."""
    text = _gitignore_text()
    for pattern in ("data/vault.enc", "*.vault", "*.key", "*.pem", "*.p12", "*.pfx", "*.db", "projects/", "cache/", "backups/"):
        assert pattern in text


def test_gitignore_keeps_safe_environment_templates_visible() -> None:
    """Ensure safe environment examples remain reviewable despite .env exclusion."""
    text = _gitignore_text()
    assert ".env\n" in text
    assert "!.env.example" in text
    assert "!.env.test" in text


def test_gitignore_covers_editor_frontend_and_log_outputs() -> None:
    """Ensure IDE, optional frontend, and local log outputs are ignored."""
    text = _gitignore_text()
    for pattern in (".idea/", ".vscode/", "node_modules/", "*.log"):
        assert pattern in text


def test_gitignore_does_not_ignore_release_evidence_files() -> None:
    """Ensure release manifests and checksums are not hidden by broad patterns."""
    text = _gitignore_text()
    assert "RELEASE_MANIFEST.txt" not in text
    assert "SHA256SUMS" not in text
