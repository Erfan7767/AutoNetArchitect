"""Lab validation command adapters."""
from __future__ import annotations

import click

from .common import run_action


def register(parent: click.Group) -> None:
    """Register lab commands."""
    @parent.group("lab")
    def lab() -> None:
        """Validate designs in lab environments without replacing production control."""

    for name, action in (("deploy", "lab.deploy"), ("push-config", "lab.push_config"), ("verify", "lab.verify"), ("compare", "lab.compare")):
        @lab.command(name)
        @click.option("--project", "project_name", default=None)
        @click.option("--lab", "lab_name", required=True)
        @click.option("--golden", default=None)
        @click.pass_context
        def command(click_context: click.Context, project_name: str | None, lab_name: str, golden: str | None, _action: str = action) -> None:
            """Delegate a non-production lab validation action."""
            run_action(click_context, _action, {"project": project_name, "lab": lab_name, "golden": golden, "production_change_control_replaced": False}, permission="lab.preview")
