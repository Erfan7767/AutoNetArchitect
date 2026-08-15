"""Tests for troubleshooting CLI commands."""
from __future__ import annotations

from click.testing import CliRunner

from cli.app import cli


def test_troubleshoot_help_lists_diagnostic_paths():
    result = CliRunner().invoke(cli, ["troubleshoot", "--help"])
    assert result.exit_code == 0
    assert "connectivity" in result.output
    assert "device" in result.output
    assert "session" in result.output


def test_troubleshoot_start_requires_symptom():
    result = CliRunner().invoke(cli, ["troubleshoot", "start"])
    assert result.exit_code == 2
    assert "--symptom" in result.output
