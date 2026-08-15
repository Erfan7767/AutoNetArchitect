"""Validation command adapters."""
from __future__ import annotations

import click

from .common import run_action


def register(parent: click.Group) -> None:
    """Register validation commands."""
    @parent.group("validate")
    def validate() -> None:
        """Run design, configuration, security, compliance, and readiness validation."""

    for name, action in (("all", "validate.all"), ("design", "validate.design"), ("config", "validate.config"), ("syntax", "validate.syntax"), ("security", "validate.security"), ("compliance", "validate.compliance"), ("readiness", "validate.readiness"), ("pre-deploy", "validate.pre_deploy")):
        @validate.command(name)
        @click.option("--project", "project_name", default=None)
        @click.option("--device", default=None)
        @click.option("--framework", default=None)
        @click.pass_context
        def command(click_context: click.Context, project_name: str | None, device: str | None, framework: str | None, _action: str = action) -> None:
            """Delegate one validation action."""
            run_action(click_context, _action, {"project": project_name, "device": device, "framework": framework}, permission="validate")
