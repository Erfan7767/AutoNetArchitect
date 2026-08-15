"""Tests for configuration CLI commands."""
from __future__ import annotations

from click.testing import CliRunner

from cli.app import cli


def test_config_help_lists_generation_and_validation():
    result = CliRunner().invoke(cli, ["config", "--help"])
    assert result.exit_code == 0
    assert "generate" in result.output
    assert "validate" in result.output


def test_config_generate_help_has_device_option():
    result = CliRunner().invoke(cli, ["config", "generate", "--help"])
    assert result.exit_code == 0
    assert "--device" in result.output
