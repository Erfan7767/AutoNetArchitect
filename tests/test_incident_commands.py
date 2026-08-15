"""Tests for incident response CLI commands."""
from __future__ import annotations

from click.testing import CliRunner

from cli.app import cli


def test_incident_help_lists_lifecycle_actions():
    result = CliRunner().invoke(cli, ["incident", "--help"])
    assert result.exit_code == 0
    assert "create" in result.output
    assert "resolve" in result.output
    assert "timeline" in result.output


def test_incident_create_requires_title_and_severity():
    result = CliRunner().invoke(cli, ["incident", "create"])
    assert result.exit_code == 2
    assert "--title" in result.output
