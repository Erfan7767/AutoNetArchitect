"""Tests for change-management CLI commands."""
from __future__ import annotations

from click.testing import CliRunner

from cli.app import cli


def test_change_help_lists_governed_lifecycle():
    result = CliRunner().invoke(cli, ["change", "--help"])
    assert result.exit_code == 0
    assert "create" in result.output
    assert "approve" in result.output
    assert "rollback" in result.output
    assert "freeze" in result.output


def test_change_create_requires_title_and_type():
    result = CliRunner().invoke(cli, ["change", "create"])
    assert result.exit_code == 2
    assert "--title" in result.output
