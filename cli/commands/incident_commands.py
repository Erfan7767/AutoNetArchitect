"""Incident response command adapters."""
from __future__ import annotations

import click

from .common import run_action


def register(parent: click.Group) -> None:
    """Register incident response commands."""
    @parent.group("incident")
    def incident() -> None:
        """Create, coordinate, and report network incidents."""

    @incident.command("create")
    @click.option("--title", required=True)
    @click.option("--severity", required=True)
    @click.option("--project", "project_name", default=None)
    @click.pass_context
    def create(click_context: click.Context, title: str, severity: str, project_name: str | None) -> None:
        """Create an incident."""
        run_action(click_context, "incident.create", {"title": title, "severity": severity, "project": project_name}, permission="incident.write")

    for name, action in (("list", "incident.list"), ("show", "incident.show"), ("timeline", "incident.timeline"), ("report", "incident.report"), ("metrics", "incident.metrics")):
        @incident.command(name)
        @click.option("--project", "project_name", default=None)
        @click.option("--incident-id", default=None)
        @click.option("--status", default="all")
        @click.option("--severity", default=None)
        @click.option("--format", "report_format", default=None)
        @click.option("--period", default=None)
        @click.pass_context
        def command(click_context: click.Context, project_name: str | None, incident_id: str | None, status: str, severity: str | None, report_format: str | None, period: str | None, _action: str = action) -> None:
            """Delegate an incident read or report action."""
            run_action(click_context, _action, {"project": project_name, "incident_id": incident_id, "status": status, "severity": severity, "format": report_format, "period": period}, permission="incident.read")

    @incident.command("update")
    @click.option("--incident-id", required=True)
    @click.option("--status", required=True)
    @click.option("--note", required=True)
    @click.pass_context
    def update(click_context: click.Context, incident_id: str, status: str, note: str) -> None:
        """Update an incident status with an audit-safe note."""
        run_action(click_context, "incident.update", {"incident_id": incident_id, "status": status, "note": note}, permission="incident.write")

    @incident.command("escalate")
    @click.option("--incident-id", required=True)
    @click.option("--level", type=int, required=True)
    @click.pass_context
    def escalate(click_context: click.Context, incident_id: str, level: int) -> None:
        """Escalate an incident."""
        run_action(click_context, "incident.escalate", {"incident_id": incident_id, "level": level}, permission="incident.write")

    @incident.command("resolve")
    @click.option("--incident-id", required=True)
    @click.option("--resolution", required=True)
    @click.option("--root-cause", default=None)
    @click.pass_context
    def resolve(click_context: click.Context, incident_id: str, resolution: str, root_cause: str | None) -> None:
        """Resolve an incident."""
        run_action(click_context, "incident.resolve", {"incident_id": incident_id, "resolution": resolution, "root_cause": root_cause}, permission="incident.write")

    @incident.command("close")
    @click.option("--incident-id", required=True)
    @click.pass_context
    def close(click_context: click.Context, incident_id: str) -> None:
        """Close an incident."""
        run_action(click_context, "incident.close", {"incident_id": incident_id}, permission="incident.write")
