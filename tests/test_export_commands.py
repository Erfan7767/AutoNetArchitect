"""Tests for export CLI commands."""
from __future__ import annotations

from click.testing import CliRunner

from cli.app import cli


def test_export_help_lists_project_and_config():
    result = CliRunner().invoke(cli, ["export", "--help"])
    assert result.exit_code == 0
    assert "project" in result.output
    assert "config" in result.output


def test_export_project_requires_path():
    result = CliRunner().invoke(cli, ["export", "project"])
    assert result.exit_code == 2
    assert "--path" in result.output
