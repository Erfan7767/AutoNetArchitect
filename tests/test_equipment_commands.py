"""Tests for equipment CLI commands."""
from __future__ import annotations

from click.testing import CliRunner

from cli.app import cli


def test_equipment_help_lists_catalog_and_capability_commands():
    result = CliRunner().invoke(cli, ["equipment", "--help"])
    assert result.exit_code == 0
    assert "catalog" in result.output
    assert "capabilities" in result.output


def test_equipment_catalog_search_has_required_query_option():
    result = CliRunner().invoke(cli, ["equipment", "catalog", "search", "--help"])
    assert result.exit_code == 0
    assert "--query" in result.output
