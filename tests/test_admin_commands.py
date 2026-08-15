"""Tests for administrative CLI commands."""
from __future__ import annotations

from click.testing import CliRunner

from cli.app import cli


def test_admin_help_lists_auth_and_user_groups():
    result = CliRunner().invoke(cli, ["admin", "--help"])
    assert result.exit_code == 0
    assert "login" in result.output
    assert "user" in result.output
    assert "roles" in result.output


def test_admin_user_create_requires_credentials_options():
    result = CliRunner().invoke(cli, ["admin", "user", "create", "--help"])
    assert result.exit_code == 0
    assert "--username" in result.output
    assert "--role" in result.output
