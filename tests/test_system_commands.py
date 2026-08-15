"""Tests for system CLI commands."""
from __future__ import annotations

from click.testing import CliRunner

from cli.app import cli


def test_system_help_lists_health_and_dependency_paths():
    result = CliRunner().invoke(cli, ["system", "--help"])
    assert result.exit_code == 0
    assert "info" in result.output
    assert "health" in result.output
    assert "dependencies" in result.output
    assert "db" in result.output


def test_system_dependencies_check_is_available():
    result = CliRunner().invoke(cli, ["system", "dependencies", "check"])
    assert result.exit_code in {0, 3}
