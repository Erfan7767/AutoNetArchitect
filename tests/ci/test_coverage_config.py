"""CI contract tests for the repository coverage configuration."""

from __future__ import annotations

import configparser
from pathlib import Path
from typing import Final

from coverage import Coverage

ROOT: Final[Path] = Path(__file__).resolve().parents[2]
CONFIG: Final[Path] = ROOT / "coverage_config" / ".coveragerc"


def test_coverage_config_declares_scope_and_threshold() -> None:
    """Require the declared source scope, omission boundaries, and threshold."""
    coverage = Coverage(config_file=str(CONFIG))
    config = coverage.config
    assert config.source == ["autonetarchitect"]
    assert config.branch is True
    assert config.fail_under == 70.0
    assert config.skip_covered is False
    parser = configparser.ConfigParser()
    parser.read(CONFIG, encoding="utf-8")
    omit = tuple(parser["run"]["omit"].splitlines())
    assert "*/tests/*" in omit
    assert "*/migrations/*" in omit
    assert "*/__init__.py" in omit
    assert "*/__main__.py" in omit
    assert "*/cli/completions/*" in omit
    assert "*/ui/pages/*" in omit


def test_coverage_outputs_are_declared() -> None:
    """Require HTML title/directory and XML output paths used by local and CI reports."""
    coverage = Coverage(config_file=str(CONFIG))
    config = coverage.config
    assert config.html_dir == "htmlcov"
    assert config.html_title == "AutoNetArchitect Coverage Report"
    assert config.xml_output == "coverage.xml"
    assert "pragma: no cover" in config.exclude_list
    assert "if TYPE_CHECKING" in config.exclude_list
