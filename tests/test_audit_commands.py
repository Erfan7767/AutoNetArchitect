"""Tests for audit CLI commands."""
from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory

from cli.context import CLIContext, CLISettings


def test_audit_show_and_search_are_read_only():
    with TemporaryDirectory() as tmp:
        context = CLIContext(CLISettings(root=Path(tmp)))
        context.audit_trail.record("cli.command", "admin", {"action": "deploy", "token": "raw"}, outcome="success")
        shown = context.audit_trail.query(event_type="cli.command")
        assert len(shown) == 1
        assert shown[0].details["token"] == "<REDACTED>"


def test_audit_group_help_lists_export_and_search():
    from click.testing import CliRunner
    from cli.app import cli
    result = CliRunner().invoke(cli, ["audit", "--help"])
    assert result.exit_code == 0
    assert "export" in result.output
    assert "search" in result.output
