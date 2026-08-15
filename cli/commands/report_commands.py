"""Report and documentation command adapters."""
from __future__ import annotations

import click

from .common import run_action


def register(parent: click.Group) -> None:
    """Register report commands."""
    @parent.group("report")
    def report() -> None:
        """Generate, list, inspect, and export reports."""

    @report.command("generate")
    @click.option("--type", "report_type", required=True)
    @click.option("--project", "project_name", default=None)
    @click.option("--format", "report_format", default=None)
    @click.option("--framework", default=None)
    @click.option("--path", "output_path", default=None)
    @click.pass_context
    def generate_run(click_context: click.Context, report_type: str, project_name: str | None, report_format: str | None, framework: str | None, output_path: str | None) -> None:
        """Generate a selected report type."""
        run_action(click_context, "report.generate", {"type": report_type, "project": project_name, "format": report_format, "framework": framework, "path": output_path}, permission="report.read")

    for name, action in (("list", "report.list"), ("show", "report.show"), ("all", "report.all")):
        @report.command(name)
        @click.option("--project", "project_name", default=None)
        @click.option("--report-id", default=None)
        @click.option("--path", "output_path", default=None)
        @click.pass_context
        def command(click_context: click.Context, project_name: str | None, report_id: str | None, output_path: str | None, _action: str = action) -> None:
            """Delegate report listing or inspection."""
            run_action(click_context, _action, {"project": project_name, "report_id": report_id, "path": output_path}, permission="report.read")
