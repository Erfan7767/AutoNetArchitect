"""Change-management command adapters."""
from __future__ import annotations

import click

from .common import run_action


def register(parent: click.Group) -> None:
    """Register change commands."""
    @parent.group("change")
    def change() -> None:
        """Plan, approve, schedule, execute, and close governed changes."""

    @change.command("create")
    @click.option("--title", required=True)
    @click.option("--type", "change_type", required=True)
    @click.option("--project", "project_name", default=None)
    @click.pass_context
    def create(click_context: click.Context, title: str, change_type: str, project_name: str | None) -> None:
        """Create a change request."""
        run_action(click_context, "change.create", {"title": title, "type": change_type, "project": project_name}, permission="change.write")

    @change.command("create-from-template")
    @click.option("--template", required=True)
    @click.option("--project", "project_name", default=None)
    @click.pass_context
    def create_template(click_context: click.Context, template: str, project_name: str | None) -> None:
        """Create a change from a registered template."""
        run_action(click_context, "change.create_from_template", {"template": template, "project": project_name}, permission="change.write")

    for name, action in (("list", "change.list"), ("show", "change.show"), ("plan", "change.plan"), ("risk-assess", "change.risk_assess"), ("impact", "change.impact"), ("verify", "change.verify"), ("catalog", "change.catalog.list"), ("calendar", "change.calendar")):
        @change.command(name)
        @click.option("--project", "project_name", default=None)
        @click.option("--change-id", default=None)
        @click.option("--status", default="all")
        @click.option("--period", default=None)
        @click.option("--month", default=None)
        @click.pass_context
        def command(click_context: click.Context, project_name: str | None, change_id: str | None, status: str, period: str | None, month: str | None, _action: str = action) -> None:
            """Delegate a change inspection action."""
            run_action(click_context, _action, {"project": project_name, "change_id": change_id, "status": status, "period": period, "month": month}, permission="change.read")

    for name, action in (("approve", "change.approve"), ("reject", "change.reject"), ("schedule", "change.schedule"), ("execute", "change.execute"), ("rollback", "change.rollback"), ("close", "change.close")):
        @change.command(name)
        @click.option("--change-id", required=True)
        @click.option("--condition", default=None)
        @click.option("--reason", default=None)
        @click.option("--window", default=None)
        @click.option("--result", default=None)
        @click.option("--yes", is_flag=True)
        @click.pass_context
        def mutating(click_context: click.Context, change_id: str, condition: str | None, reason: str | None, window: str | None, result: str | None, yes: bool, _action: str = action) -> None:
            """Delegate a governed change mutation."""
            destructive = _action in {"change.execute", "change.rollback"}
            run_action(click_context, _action, {"change_id": change_id, "condition": condition, "reason": reason, "window": window, "result": result}, permission="change.execute" if destructive else "change.write", destructive=destructive, confirmation=f"Confirm {_action} for {change_id}?" if destructive else None, yes=yes)

    @change.group("freeze")
    def freeze() -> None:
        """Manage change freezes."""

    @freeze.command("list")
    @click.pass_context
    def freeze_list(click_context: click.Context) -> None:
        """List change freeze windows."""
        run_action(click_context, "change.freeze.list", {}, permission="change.read")

    @freeze.command("add")
    @click.option("--start", required=True)
    @click.option("--end", required=True)
    @click.option("--type", "freeze_type", required=True)
    @click.option("--reason", required=True)
    @click.pass_context
    def freeze_add(click_context: click.Context, start: str, end: str, freeze_type: str, reason: str) -> None:
        """Add a change freeze window."""
        run_action(click_context, "change.freeze.add", {"start": start, "end": end, "type": freeze_type, "reason": reason}, permission="change.write")

    @change.command("metrics")
    @click.option("--period", default="monthly")
    @click.pass_context
    def metrics(click_context: click.Context, period: str) -> None:
        """Show change metrics."""
        run_action(click_context, "change.metrics", {"period": period}, permission="change.read")
