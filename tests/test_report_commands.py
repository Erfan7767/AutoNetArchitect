"""Tests for report CLI commands."""
from __future__ import annotations

from click.testing import CliRunner

from cli.app import cli


def test_report_help_lists_generate_and_inventory():
    result = CliRunner().invoke(cli, ["report", "--help"])
    assert result.exit_code == 0
    assert "generate" in result.output
    assert "list" in result.output
    assert "all" in result.output


def test_report_generate_requires_type():
    result = CliRunner().invoke(cli, ["report", "generate", "run"])
    assert result.exit_code == 2
    assert "--type" in result.output
