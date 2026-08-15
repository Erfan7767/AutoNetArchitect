"""Tests for validation CLI commands."""
from __future__ import annotations

from click.testing import CliRunner

from cli.app import cli


def test_validate_help_lists_all_major_checks():
    result = CliRunner().invoke(cli, ["validate", "--help"])
    assert result.exit_code == 0
    for name in ("all", "design", "config", "security", "compliance", "readiness", "pre-deploy"):
        assert name in result.output


def test_validate_compliance_help_has_framework_option():
    result = CliRunner().invoke(cli, ["validate", "compliance", "--help"])
    assert result.exit_code == 0
    assert "--framework" in result.output
