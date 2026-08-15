"""Contract tests for the repository pull request template."""

from __future__ import annotations

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
TEMPLATE = PROJECT_ROOT / ".github" / "PULL_REQUEST_TEMPLATE.md"


def _template_text() -> str:
    """Return the pull request template text."""
    return TEMPLATE.read_text(encoding="utf-8")


def test_pr_template_declares_change_scope_and_type() -> None:
    """Ensure contributors can describe the change and affected phase/module."""
    text = _template_text()
    for heading in ("## Description", "## Type of Change", "## Phase/Module Affected"):
        assert heading in text
    for change_type in ("Bug fix", "New feature", "Breaking change", "Documentation update", "Test addition"):
        assert f"- [ ] {change_type}" in text


def test_pr_template_declares_project_safety_and_provenance_checks() -> None:
    """Ensure the PR form preserves V1 safety, governance, and evidence boundaries."""
    text = _template_text()
    for marker in (
        "local-single-user V1 scope",
        "HumanSuppliedMandatory",
        "review, approval, backup, verification, rollback, audit, and no-go",
        "DecisionRecords",
        "assumptions",
        "Source of Truth",
        "Secrets and raw secret values",
        "pass",
        "TODO",
        "placeholder",
    ):
        assert marker in text


def test_pr_template_declares_required_quality_commands() -> None:
    """Ensure required developer and release validation commands are visible."""
    text = _template_text()
    for command in ("make test", "make lint", "make typecheck", "make security", "make check-all", "compileall", "run_release_tests.py"):
        assert command in text
    assert "CI required checks" in text
    assert "Release manifests, checksums, and archives" in text


def test_pr_template_declares_testing_and_release_evidence_sections() -> None:
    """Ensure testing evidence, screenshots, and bounded release impact are requested."""
    text = _template_text()
    for heading in ("## Testing / التحقق", "## Screenshots (if applicable)", "## Release impact / أثر الإصدار"):
        assert heading in text
    for marker in ("mocked", "lab-only", "read-only discovery", "real evidence", "production readiness"):
        assert marker in text
