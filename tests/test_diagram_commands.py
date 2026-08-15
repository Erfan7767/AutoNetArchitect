"""Tests for diagram CLI commands."""
from __future__ import annotations

from click.testing import CliRunner

from cli.app import cli


def test_diagram_help_lists_generation_paths():
    result = CliRunner().invoke(cli, ["diagram", "--help"])
    assert result.exit_code == 0
    assert "generate" in result.output
    assert "all" in result.output


def test_diagram_generate_requires_type():
    result = CliRunner().invoke(cli, ["diagram", "generate"])
    assert result.exit_code == 2
    assert "--type" in result.output
