"""Troubleshooting command adapters."""
from __future__ import annotations

import click

from .common import run_action


def register(parent: click.Group) -> None:
    """Register troubleshooting commands."""
    @parent.group("troubleshoot")
    def troubleshoot() -> None:
        """Start and inspect read-only troubleshooting sessions."""

    @troubleshoot.command("start")
    @click.option("--symptom", required=True)
    @click.option("--project", "project_name", default=None)
    @click.option("--severity", default=None)
    @click.pass_context
    def start(click_context: click.Context, symptom: str, project_name: str | None, severity: str | None) -> None:
        """Start a diagnostic session."""
        run_action(click_context, "troubleshoot.start", {"symptom": symptom, "project": project_name, "severity": severity}, permission="operations.read")

    for name, action in (("connectivity", "troubleshoot.connectivity"), ("path", "troubleshoot.path"), ("device", "troubleshoot.device"), ("interface", "troubleshoot.interface"), ("routing", "troubleshoot.routing"), ("parse-output", "troubleshoot.parse_output"), ("sessions", "troubleshoot.sessions"), ("known-issues", "troubleshoot.known_issues")):
        @troubleshoot.command(name)
        @click.option("--project", "project_name", default=None)
        @click.option("--source", default=None)
        @click.option("--destination", default=None)
        @click.option("--device", default=None)
        @click.option("--interface", default=None)
        @click.option("--vendor", default=None)
        @click.option("--platform", default=None)
        @click.option("--command", default=None)
        def command(project_name: str | None, source: str | None, destination: str | None, device: str | None, interface: str | None, vendor: str | None, platform: str | None, command: str | None, _action: str = action) -> None:
            """Delegate read-only troubleshooting action."""
            click_context = click.get_current_context()
            run_action(click_context, _action, {"project": project_name, "source": source, "destination": destination, "device": device, "interface": interface, "vendor": vendor, "platform": platform, "command": command}, permission="operations.read")

    @troubleshoot.group("session")
    def session() -> None:
        """Inspect one diagnostic session."""

    @session.command("show")
    @click.option("--session-id", required=True)
    @click.option("--project", "project_name", default=None)
    @click.pass_context
    def session_show(click_context: click.Context, session_id: str, project_name: str | None) -> None:
        """Show a diagnostic session."""
        run_action(click_context, "troubleshoot.session.show", {"session_id": session_id, "project": project_name}, permission="operations.read")
