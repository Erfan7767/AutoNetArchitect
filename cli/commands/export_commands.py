"""Export command adapters."""
from __future__ import annotations

import click

from .common import run_action


def register(parent: click.Group) -> None:
    """Register export commands."""
    @parent.group("export")
    def export() -> None:
        """Export projects and configuration artifacts safely."""

    @export.command("project")
    @click.option("--project", "project_name", default=None)
    @click.option("--path", "output_path", required=True)
    @click.option("--redact", is_flag=True, default=True, help="Keep secret redaction enabled.")
    @click.pass_context
    def export_project(click_context: click.Context, project_name: str | None, output_path: str, redact: bool) -> None:
        """Export a project with redaction enabled by default."""
        run_action(click_context, "export.project", {"project": project_name, "path": output_path, "redact": redact}, permission="export.read")

    @export.command("config")
    @click.option("--project", "project_name", default=None)
    @click.option("--device", default="all")
    @click.option("--path", "output_path", required=True)
    @click.option("--redact", is_flag=True, default=True, help="Keep secret redaction enabled.")
    @click.pass_context
    def export_config(click_context: click.Context, project_name: str | None, device: str, output_path: str, redact: bool) -> None:
        """Export configuration artifacts without secret values."""
        run_action(click_context, "export.config", {"project": project_name, "device": device, "path": output_path, "redact": redact}, permission="export.read")
