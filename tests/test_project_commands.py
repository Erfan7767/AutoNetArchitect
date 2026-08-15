"""Tests for project CLI commands."""
from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory

from cli.context import CLIContext, CLISettings


def test_project_create_list_show():
    with TemporaryDirectory() as tmp:
        context = CLIContext(CLISettings(root=Path(tmp)))
        context.principal = context.auth_manager.rbac and context.principal
        context.principal = type(context.principal)("admin", ("admin",))
        created = context.dispatch("project.create", {"name": "HQ", "sector": "banking"}, permission="project.write")
        assert created.success is True
        listed = context.dispatch("project.list", {}, permission="project.read")
        assert "HQ" in listed.data["projects"]
        shown = context.dispatch("project.show", {"project": "HQ"}, permission="project.read")
        assert shown.success is True


def test_project_command_group_is_registered():
    from click.testing import CliRunner
    from cli.app import cli
    result = CliRunner().invoke(cli, ["project", "--help"])
    assert result.exit_code == 0
    assert "create" in result.output
