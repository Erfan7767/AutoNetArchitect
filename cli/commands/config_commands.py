"""Configuration command adapters."""
from __future__ import annotations

import click

from .common import run_action


def register(parent: click.Group) -> None:
    """Register configuration commands."""
    @parent.group("config")
    def config() -> None:
        """Generate, inspect, validate, diff, and export configurations."""

    @config.command("generate")
    @click.option("--project", "project_name", default=None)
    @click.option("--device", default="all")
    @click.option("--artifact-id", default=None)
    @click.pass_context
    def generate(click_context: click.Context, project_name: str | None, device: str, artifact_id: str | None) -> None:
        """Generate configuration artifacts through the config service boundary."""
        run_action(click_context, "config.generate", {"project": project_name, "device": device, "artifact_id": artifact_id or f"config:{device}"}, permission="config.generate")

    for name, action in (("show", "config.show"), ("validate", "config.validate"), ("diff", "config.diff"), ("export", "config.export"), ("search", "config.search")):
        @config.command(name)
        @click.option("--project", "project_name", default=None)
        @click.option("--device", default=None)
        @click.option("--section", default=None)
        @click.option("--against", default=None)
        @click.option("--path", "output_path", default=None)
        @click.option("--pattern", default=None)
        @click.pass_context
        def command(click_context: click.Context, project_name: str | None, device: str | None, section: str | None, against: str | None, output_path: str | None, pattern: str | None, _action: str = action) -> None:
            """Delegate configuration action."""
            permission = "config.generate" if _action == "config.validate" else "config.read"
            run_action(click_context, _action, {"project": project_name, "device": device, "section": section, "against": against, "path": output_path, "pattern": pattern}, permission=permission)
