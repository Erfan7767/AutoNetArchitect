"""Tests for the CLI root application."""
from __future__ import annotations

from click.testing import CliRunner

from cli.app import cli


def test_cli_help_and_version_are_available():
    runner = CliRunner()
    help_result = runner.invoke(cli, ["--help"])
    version_result = runner.invoke(cli, ["--version"])
    assert help_result.exit_code == 0
    assert "project" in help_result.output
    assert "deploy" in help_result.output
    assert version_result.exit_code == 0
    assert "0.1.0" in version_result.output


def test_cli_global_output_format_and_quiet_options_are_available():
    runner = CliRunner()
    result = runner.invoke(cli, ["--output-format", "json", "--quiet", "project", "list"])
    assert result.exit_code == 0
    assert result.output == ""


def test_cli_command_groups_are_registered():
    expected = {"project", "questionnaire", "design", "equipment", "config", "validate", "deploy", "ops", "troubleshoot", "incident", "change", "compliance", "report", "diagram", "export", "lab", "admin", "audit", "system"}
    assert expected.issubset(set(cli.commands))
