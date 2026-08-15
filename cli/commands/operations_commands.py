"""Operations command adapters."""
from __future__ import annotations

import click

from .common import run_action


def register(parent: click.Group) -> None:
    """Register operations commands."""
    @parent.group("ops")
    def ops() -> None:
        """Monitor health, drift, backups, maintenance, and capacity."""

    for name, action in (("monitor", "operations.monitor"), ("health", "operations.health"), ("drift", "operations.drift"), ("backup", "operations.backup"), ("backup-status", "operations.backup_status"), ("capacity", "operations.capacity"), ("interfaces", "operations.interfaces")):
        @ops.command(name)
        @click.option("--project", "project_name", default=None)
        @click.option("--device", default=None)
        @click.option("--link", default=None)
        @click.option("--live", is_flag=True)
        @click.option("--errors-only", is_flag=True)
        @click.pass_context
        def command(click_context: click.Context, project_name: str | None, device: str | None, link: str | None, live: bool, errors_only: bool, _action: str = action) -> None:
            """Delegate an operational read action."""
            run_action(click_context, _action, {"project": project_name, "device": device, "link": link, "live": live, "errors_only": errors_only}, permission="operations.read")

    @ops.group("maintenance")
    def maintenance() -> None:
        """Manage governed maintenance windows."""

    @maintenance.command("schedule")
    @click.option("--window", required=True)
    @click.option("--project", "project_name", default=None)
    @click.pass_context
    def schedule(click_context: click.Context, window: str, project_name: str | None) -> None:
        """Schedule a maintenance window."""
        run_action(click_context, "operations.maintenance.schedule", {"window": window, "project": project_name}, permission="operations.write")

    @maintenance.command("list")
    @click.option("--project", "project_name", default=None)
    @click.pass_context
    def list_windows(click_context: click.Context, project_name: str | None) -> None:
        """List maintenance windows."""
        run_action(click_context, "operations.maintenance.list", {"project": project_name}, permission="operations.read")
