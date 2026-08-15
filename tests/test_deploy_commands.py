"""Tests for deployment CLI commands."""
from __future__ import annotations

from click.testing import CliRunner

from cli.app import cli


def test_deploy_help_lists_safe_and_real_paths():
    result = CliRunner().invoke(cli, ["deploy", "--help"])
    assert result.exit_code == 0
    assert "dry-run" in result.output
    assert "execute" in result.output
    assert "rollback" in result.output


def test_deploy_execute_requires_device_change_and_backup():
    result = CliRunner().invoke(cli, ["deploy", "execute"])
    assert result.exit_code == 2
    assert "Missing option" in result.output
