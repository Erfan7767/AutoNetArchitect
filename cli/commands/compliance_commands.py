"""Technical compliance command adapters."""
from __future__ import annotations

import click

from .common import run_action


def register(parent: click.Group) -> None:
    """Register compliance commands."""
    @parent.group("compliance")
    def compliance() -> None:
        """Run evidence-bounded technical compliance assessments."""

    @compliance.command("assess")
    @click.option("--project", "project_name", default=None)
    @click.option("--framework", required=True)
    @click.pass_context
    def assess(click_context: click.Context, project_name: str | None, framework: str) -> None:
        """Assess technical controls within an explicit scope."""
        run_action(click_context, "compliance.assess", {"project": project_name, "framework": framework, "technical_only": True}, permission="compliance.read")

    @compliance.command("scope")
    @click.option("--project", "project_name", default=None)
    @click.pass_context
    def scope(click_context: click.Context, project_name: str | None) -> None:
        """Show assessment scope and disclaimers."""
        run_action(click_context, "compliance.scope", {"project": project_name}, permission="compliance.read")
