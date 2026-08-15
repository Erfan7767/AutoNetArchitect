"""Tests for design CLI commands."""
from __future__ import annotations

from click.testing import CliRunner

from cli.app import cli


def test_design_group_help_lists_review_actions():
    result = CliRunner().invoke(cli, ["design", "--help"])
    assert result.exit_code == 0
    assert "generate" in result.output
    assert "override" in result.output
    assert "compare" in result.output


def test_design_generate_without_project_is_blocked_cleanly():
    result = CliRunner().invoke(cli, ["design", "generate"])
    assert result.exit_code in {3, 4, 5}
    assert "Traceback" not in result.output
