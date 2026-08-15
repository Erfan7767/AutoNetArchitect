"""Tests for questionnaire CLI commands."""
from __future__ import annotations

from click.testing import CliRunner

from cli.app import cli


def test_questionnaire_group_help_lists_major_actions():
    result = CliRunner().invoke(cli, ["questionnaire", "--help"])
    assert result.exit_code == 0
    assert "start" in result.output
    assert "validate" in result.output
    assert "import" in result.output


def test_questionnaire_start_requires_project_or_returns_structured_block():
    result = CliRunner().invoke(cli, ["questionnaire", "start", "--project", "UnknownProject"])
    assert result.exit_code in {0, 3, 4, 5}
