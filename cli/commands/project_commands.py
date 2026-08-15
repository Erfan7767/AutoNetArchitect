"""Project lifecycle command adapters."""
from __future__ import annotations

from typing import Any

import click

from .common import get_cli_context, payload_from_kwargs, run_action


def register(parent: click.Group) -> None:
    """Register project commands."""
    @parent.group("project")
    def project() -> None:
        """Create, inspect, open, archive, and export projects."""

    @project.command("create")
    @click.option("--name", required=True)
    @click.option("--sector", default=None)
    @click.option("--description", default="")
    @click.pass_context
    def create(click_context: click.Context, name: str, sector: str | None, description: str) -> None:
        """Create a local project."""
        run_action(click_context, "project.create", {"name": name, "sector": sector, "description": description}, permission="project.write")

    @project.command("list")
    @click.option("--status", type=click.Choice(["active", "archived", "all"]), default="all", show_default=True)
    @click.pass_context
    def list_projects(click_context: click.Context, status: str) -> None:
        """List local projects."""
        run_action(click_context, "project.list", {"status": status}, permission="project.read")

    @project.command("show")
    @click.option("--project", "project_name", default=None)
    @click.pass_context
    def show(click_context: click.Context, project_name: str | None) -> None:
        """Show one project payload."""
        run_action(click_context, "project.show", {"project": project_name}, permission="project.read")

    @project.command("open")
    @click.option("--name", required=True)
    @click.pass_context
    def open_project(click_context: click.Context, name: str) -> None:
        """Open one local project."""
        run_action(click_context, "project.open", {"name": name}, permission="project.read")

    @project.command("close")
    @click.pass_context
    def close_project(click_context: click.Context) -> None:
        """Clear the current project selection for this invocation."""
        cli_context = get_cli_context(click_context)
        cli_context.current_project = None
        cli_context.output.emit({"project": None}, status="closed", message="Project selection cleared")

    @project.command("status")
    @click.option("--project", "project_name", default=None)
    @click.pass_context
    def status(click_context: click.Context, project_name: str | None) -> None:
        """Show project status."""
        run_action(click_context, "project.status", {"project": project_name}, permission="project.read")

    @project.command("archive")
    @click.option("--name", required=True)
    @click.pass_context
    def archive(click_context: click.Context, name: str) -> None:
        """Mark a project archived through the persistence boundary."""
        run_action(click_context, "project.archive", {"name": name}, permission="project.write")

    @project.command("delete")
    @click.option("--name", required=True)
    @click.option("--confirm", "confirmed", is_flag=True)
    @click.pass_context
    def delete(click_context: click.Context, name: str, confirmed: bool) -> None:
        """Delete a project after mandatory confirmation."""
        if not confirmed:
            raise click.UsageError("--confirm is required for project delete")
        run_action(click_context, "project.delete", {"name": name}, permission="project.write", destructive=True)

    @project.command("export")
    @click.option("--project", "project_name", default=None)
    @click.option("--path", "output_path", required=True, type=click.Path(dir_okay=False))
    @click.pass_context
    def export_project(click_context: click.Context, project_name: str | None, output_path: str) -> None:
        """Export a project through the registered export service."""
        run_action(click_context, "project.export", {"project": project_name, "path": output_path}, permission="project.read")

    @project.command("import")
    @click.option("--path", "input_path", required=True, type=click.Path(exists=True, dir_okay=False))
    @click.option("--name", default=None)
    @click.pass_context
    def import_project(click_context: click.Context, input_path: str, name: str | None) -> None:
        """Import a project through the registered export service."""
        run_action(click_context, "project.import", {"path": input_path, "name": name}, permission="project.write")

    @project.command("clone")
    @click.option("--source", required=True)
    @click.option("--target", required=True)
    @click.pass_context
    def clone(click_context: click.Context, source: str, target: str) -> None:
        """Clone a project through the registered persistence service."""
        run_action(click_context, "project.clone", {"source": source, "target": target}, permission="project.write")
