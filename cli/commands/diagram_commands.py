"""Network diagram command adapters."""
from __future__ import annotations

import click

from .common import run_action


def register(parent: click.Group) -> None:
    """Register diagram commands."""
    @parent.group("diagram")
    def diagram() -> None:
        """Generate and inspect network diagrams."""

    @diagram.command("generate")
    @click.option("--type", "diagram_type", required=True)
    @click.option("--project", "project_name", default=None)
    @click.option("--format", "diagram_format", default=None)
    @click.option("--rack-id", default=None)
    @click.pass_context
    def generate(click_context: click.Context, diagram_type: str, project_name: str | None, diagram_format: str | None, rack_id: str | None) -> None:
        """Generate a selected diagram type."""
        run_action(click_context, "diagram.generate", {"type": diagram_type, "project": project_name, "format": diagram_format, "rack_id": rack_id}, permission="diagram.read")

    @diagram.command("all")
    @click.option("--project", "project_name", default=None)
    @click.option("--format", "diagram_format", default="drawio")
    @click.option("--path", "output_path", default=None)
    @click.pass_context
    def all_diagrams(click_context: click.Context, project_name: str | None, diagram_format: str, output_path: str | None) -> None:
        """Generate the registered diagram set."""
        run_action(click_context, "diagram.all", {"project": project_name, "format": diagram_format, "path": output_path}, permission="diagram.read")

    @diagram.command("list")
    @click.option("--project", "project_name", default=None)
    @click.pass_context
    def list_diagrams(click_context: click.Context, project_name: str | None) -> None:
        """List diagram artifacts."""
        run_action(click_context, "diagram.list", {"project": project_name}, permission="diagram.read")
