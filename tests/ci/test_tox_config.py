"""CI contract tests for the repository tox configuration."""

from __future__ import annotations

import configparser
from pathlib import Path
from typing import Final

ROOT: Final[Path] = Path(__file__).resolve().parents[2]
TOX_CONFIG: Final[Path] = ROOT / "tox.ini"


def tox_parser() -> configparser.ConfigParser:
    """Read tox.ini using the compatible INI parser."""
    parser = configparser.ConfigParser()
    parser.read(TOX_CONFIG, encoding="utf-8")
    return parser


def test_tox_declares_required_environment_matrix() -> None:
    """Require the Python matrix and all requested quality/test environments."""
    parser = tox_parser()
    env_list = {item.strip() for item in parser["tox"]["env_list"].split(",")}
    required = {"py311", "py312", "integration", "e2e", "lint", "typecheck", "security"}
    assert required.issubset(env_list)
    assert parser["tox"]["skip_missing_interpreters"].lower() == "true"
    assert parser["tox"]["skipsdist"].lower() == "false"
    assert parser["testenv:py311"]["base_python"] == "python3.11"
    assert parser["testenv:py312"]["base_python"] == "python3.12"


def test_tox_commands_match_repository_quality_policy() -> None:
    """Require coverage, strict typing, lint, and mandatory security command boundaries."""
    parser = tox_parser()
    test_command = parser["testenv"]["commands"]
    assert "--cov-config=coverage_config/.coveragerc" in test_command
    assert "--cov-report=term-missing" in test_command
    assert "ruff check . --config pyproject.toml" in parser["testenv:lint"]["commands"]
    assert "ruff format --check . --config pyproject.toml" in parser["testenv:lint"]["commands"]
    assert "mypy autonetarchitect/ --config-file mypy.ini" in parser["testenv:typecheck"]["commands"]
    assert "bash scripts/run_security_scan.sh" in parser["testenv:security"]["commands"]
    assert "safety check" not in parser["testenv:security"]["commands"]
    assert "python scripts/check_docs_links.py" in parser["testenv:docs"]["commands"]
