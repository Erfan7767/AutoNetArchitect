"""Tests for compliance CLI commands."""
from __future__ import annotations

from click.testing import CliRunner

from cli.app import cli


def test_compliance_help_is_technical_and_scoped():
    result = CliRunner().invoke(cli, ["compliance", "--help"])
    assert result.exit_code == 0
    assert "technical" in result.output.lower()
    assert "assess" in result.output
    assert "scope" in result.output


def test_compliance_assess_requires_framework():
    result = CliRunner().invoke(cli, ["compliance", "assess"])
    assert result.exit_code == 2
    assert "--framework" in result.output
