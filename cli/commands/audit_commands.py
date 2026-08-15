"""Audit trail command adapters."""
from __future__ import annotations

import csv
import json
from pathlib import Path

import click

from log_redaction.redacting_filter import RedactingFilter
from .common import get_cli_context, require_command, run_action


def register(parent: click.Group) -> None:
    """Register audit commands."""
    @parent.group("audit")
    def audit() -> None:
        """Inspect and export the append-only audit trail."""

    @audit.command("show")
    @click.option("--project", "project_name", default=None)
    @click.option("--user", "username", default=None)
    @click.option("--action", "event_type", default=None)
    @click.option("--limit", type=int, default=100)
    @click.pass_context
    def show(click_context: click.Context, project_name: str | None, username: str | None, event_type: str | None, limit: int) -> None:
        """Show filtered audit entries."""
        cli_context = require_command(click_context, "audit.read")
        entries = cli_context.audit_trail.query(event_type=event_type, actor=username)
        selected = [RedactingFilter.sanitize_value(item.to_dict()) for item in entries[-limit:]]
        cli_context.output.emit({"entries": selected, "read_only": True, "project": project_name}, status="loaded", message="Audit entries loaded")

    @audit.command("search")
    @click.option("--query", required=True)
    @click.option("--project", "project_name", default=None)
    @click.pass_context
    def search(click_context: click.Context, query: str, project_name: str | None) -> None:
        """Search audit entry metadata."""
        cli_context = require_command(click_context, "audit.read")
        entries = []
        for item in cli_context.audit_trail.entries():
            serialized = json.dumps(RedactingFilter.sanitize_value(item.to_dict()), ensure_ascii=False)
            if query.lower() in serialized.lower():
                entries.append(item.to_dict())
        cli_context.output.emit({"entries": entries, "project": project_name, "read_only": True}, status="loaded", message="Audit search completed")

    @audit.command("export")
    @click.option("--project", "project_name", default=None)
    @click.option("--format", "export_format", type=click.Choice(["json", "csv"]), default="json")
    @click.option("--path", "output_path", required=True, type=click.Path(dir_okay=False))
    @click.pass_context
    def export(click_context: click.Context, project_name: str | None, export_format: str, output_path: str) -> None:
        """Export audit entries without raw secrets."""
        cli_context = require_command(click_context, "audit.read")
        entries = [RedactingFilter.sanitize_value(item.to_dict()) for item in cli_context.audit_trail.entries()]
        target = Path(output_path)
        target.parent.mkdir(parents=True, exist_ok=True)
        if export_format == "json":
            target.write_text(json.dumps({"entries": entries, "project": project_name}, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        else:
            keys = sorted({key for item in entries for key in item})
            with target.open("w", encoding="utf-8", newline="") as handle:
                writer = csv.DictWriter(handle, fieldnames=keys)
                writer.writeheader()
                writer.writerows(entries)
        cli_context.output.emit({"path": str(target), "entry_count": len(entries), "redacted": True}, status="exported", message="Audit export written")

    @audit.command("report")
    @click.option("--project", "project_name", default=None)
    @click.option("--period", default="monthly")
    @click.pass_context
    def report(click_context: click.Context, project_name: str | None, period: str) -> None:
        """Produce an audit summary through the audit reporter boundary."""
        run_action(click_context, "audit.report", {"project": project_name, "period": period}, permission="audit.read")
