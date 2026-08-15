"""Deployment command adapters."""
from __future__ import annotations

import click

from .common import run_action


def register(parent: click.Group) -> None:
    """Register deployment commands."""
    @parent.group("deploy")
    def deploy() -> None:
        """Plan, preview, execute, verify, and roll back deployments."""

    @deploy.command("plan")
    @click.option("--project", "project_name", default=None)
    @click.option("--device", default="all")
    @click.pass_context
    def plan(click_context: click.Context, project_name: str | None, device: str) -> None:
        """Prepare a deployment package."""
        run_action(click_context, "deployment.prepare", {"project": project_name, "device": device, "deployment_artifact_id": f"deployment:{device}"}, permission="deploy.preview")

    @deploy.command("dry-run")
    @click.option("--project", "project_name", default=None)
    @click.option("--device", default="all")
    @click.pass_context
    def dry_run(click_context: click.Context, project_name: str | None, device: str) -> None:
        """Execute a logical dry-run through the deployment boundary."""
        run_action(click_context, "deployment.execute", {"project": project_name, "device": device, "execution_result_id": f"dry-run:{device}", "real_execution": False}, permission="deploy.preview")

    @deploy.command("execute")
    @click.option("--project", "project_name", default=None)
    @click.option("--device", required=True)
    @click.option("--change-id", required=True)
    @click.option("--backup-reference", required=True)
    @click.option("--approval-reference", default=None)
    @click.option("--destructive-operation-approval", is_flag=True)
    @click.option("--yes", is_flag=True)
    @click.pass_context
    def execute(click_context: click.Context, project_name: str | None, device: str, change_id: str, backup_reference: str, approval_reference: str | None, destructive_operation_approval: bool, yes: bool) -> None:
        """Execute a production deployment after mandatory confirmation and gates."""
        run_action(click_context, "deployment.execute", {"project": project_name, "device": device, "change_id": change_id, "backup_reference": backup_reference, "approval_reference": approval_reference, "destructive_operation_approval": destructive_operation_approval, "execution_result_id": f"execution:{device}", "real_execution": True}, permission="deploy.execute", destructive=True, confirmation=f"Deploy to production device {device}? Type confirmation through governance.", yes=yes)

    for name, action in (("status", "deployment.status"), ("verify", "deployment.verify"), ("history", "deployment.history"), ("backup", "deployment.backup"), ("backup-all", "deployment.backup_all")):
        @deploy.command(name)
        @click.option("--project", "project_name", default=None)
        @click.option("--device", default=None)
        @click.pass_context
        def command(click_context: click.Context, project_name: str | None, device: str | None, _action: str = action) -> None:
            """Delegate deployment status, verification, history, or backup action."""
            run_action(click_context, _action, {"project": project_name, "device": device}, permission="deploy.preview")

    @deploy.command("rollback")
    @click.option("--project", "project_name", default=None)
    @click.option("--device", required=True)
    @click.option("--change-id", required=True)
    @click.option("--yes", is_flag=True)
    @click.pass_context
    def rollback(click_context: click.Context, project_name: str | None, device: str, change_id: str, yes: bool) -> None:
        """Request a governed rollback."""
        run_action(click_context, "deployment.rollback", {"project": project_name, "device": device, "change_id": change_id}, permission="rollback.execute", destructive=True, confirmation=f"Rollback device {device}?", yes=yes)
