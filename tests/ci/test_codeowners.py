"""Contract tests for repository CODEOWNERS policy."""

from __future__ import annotations

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
CODEOWNERS = PROJECT_ROOT / ".github" / "CODEOWNERS"


def _rules() -> dict[str, str]:
    """Return non-comment CODEOWNERS rules keyed by path pattern."""
    rules: dict[str, str] = {}
    for line in CODEOWNERS.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        fields = stripped.split()
        assert len(fields) >= 2, f"invalid CODEOWNERS rule: {line}"
        rules[fields[0]] = " ".join(fields[1:])
    return rules


def test_codeowners_declares_global_core_ownership() -> None:
    """Ensure every unmatched path has the core team as its default owner."""
    rules = _rules()
    assert rules.get("*") == "@autonet-core-team"


def test_codeowners_declares_foundation_design_and_config_owners() -> None:
    """Ensure foundational, design, and configuration paths have specialized owners."""
    rules = _rules()
    expected = {
        "/constants.py": "@autonet-core-team",
        "/exceptions.py": "@autonet-core-team",
        "/infrastructure/": "@autonet-core-team",
        "/designers/": "@autonet-design-team",
        "/config_generators/": "@autonet-config-team",
        "/config_validators/": "@autonet-config-team",
    }
    for path, owner in expected.items():
        assert rules.get(path) == owner


def test_codeowners_declares_security_and_operations_owners() -> None:
    """Ensure security-sensitive and production-operation paths have dedicated owners."""
    rules = _rules()
    expected = {
        "/secrets/": "@autonet-security-team",
        "/auth/": "@autonet-security-team",
        "/pki/": "@autonet-security-team",
        "/log_redaction/": "@autonet-security-team",
        "/audit/": "@autonet-security-team",
        "/deployment/": "@autonet-ops-team",
        "/operations/": "@autonet-ops-team",
        "/firmware/": "@autonet-ops-team",
    }
    for path, owner in expected.items():
        assert rules.get(path) == owner


def test_codeowners_declares_ci_cd_and_release_owners() -> None:
    """Ensure CI/CD, packaging, and container files have DevOps ownership."""
    rules = _rules()
    expected = {
        "/.github/": "@autonet-devops-team",
        "/Dockerfile*": "@autonet-devops-team",
        "/docker-compose*": "@autonet-devops-team",
        "/Makefile": "@autonet-devops-team",
        "/tox.ini": "@autonet-devops-team",
        "/noxfile.py": "@autonet-devops-team",
        "/pyproject.toml": "@autonet-devops-team",
        "/requirements*.txt": "@autonet-devops-team",
    }
    for path, owner in expected.items():
        assert rules.get(path) == owner


def test_codeowners_paths_match_repository_layout() -> None:
    """Ensure concrete CODEOWNERS paths refer to files or directories in this repository."""
    rules = _rules()
    concrete_paths = [pattern for pattern in rules if pattern.startswith("/") and not any(char in pattern for char in "*?")]
    missing = [pattern for pattern in concrete_paths if not (PROJECT_ROOT / pattern.lstrip("/")).exists()]
    assert missing == [], f"CODEOWNERS paths missing from repository: {missing}"
