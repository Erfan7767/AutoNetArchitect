"""Tests for operations CLI commands."""
from __future__ import annotations

from click.testing import CliRunner

from cli.app import cli


def test_ops_help_lists_read_only_and_maintenance_paths():
    result = CliRunner().invoke(cli, ["ops", "--help"])
    assert result.exit_code == 0
    assert "monitor" in result.output
    assert "drift" in result.output
    assert "maintenance" in result.output


def test_ops_maintenance_schedule_requires_window():
    result = CliRunner().invoke(cli, ["ops", "maintenance", "schedule"])
    assert result.exit_code == 2
    assert "--window" in result.output
