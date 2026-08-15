"""Design command adapters."""
from __future__ import annotations

import click

from .common import run_action


def register(parent: click.Group) -> None:
    """Register design commands."""
    @parent.group("design")
    def design() -> None:
        """Generate, inspect, validate, and compare network designs."""

    @design.command("generate")
    @click.option("--project", "project_name", default=None)
    @click.option("--phase", default="all")
    @click.option("--evidence-id", "evidence_ids", multiple=True)
    @click.option("--approval-reference", default=None)
    @click.pass_context
    def generate(click_context: click.Context, project_name: str | None, phase: str, evidence_ids: tuple[str, ...], approval_reference: str | None) -> None:
        """Generate a design through the design orchestrator."""
        run_action(click_context, "design.generate", {"project": project_name, "phase": phase, "evidence_ids": evidence_ids, "approval_reference": approval_reference, "artifact_id": f"design:{project_name or 'current'}"}, permission="design.write")

    for name, action in (("status", "design.status"), ("show", "design.show"), ("decisions", "design.decisions"), ("assumptions", "design.assumptions"), ("unresolved", "design.unresolved"), ("validate", "design.validate"), ("export", "design.export")):
        @design.command(name)
        @click.option("--project", "project_name", default=None)
        @click.option("--section", default=None)
        @click.option("--area", default=None)
        @click.pass_context
        def command(click_context: click.Context, project_name: str | None, section: str | None, area: str | None, _action: str = action) -> None:
            """Delegate a design inspection or validation action."""
            run_action(click_context, _action, {"project": project_name, "section": section, "area": area}, permission="design.read")

    @design.command("override")
    @click.option("--project", "project_name", default=None)
    @click.option("--decision-id", required=True)
    @click.option("--value", required=True)
    @click.option("--reason", required=True)
    @click.pass_context
    def override(click_context: click.Context, project_name: str | None, decision_id: str, value: str, reason: str) -> None:
        """Submit an expert override through the registered override service."""
        run_action(click_context, "design.override", {"project": project_name, "decision_id": decision_id, "value": value, "reason": reason}, permission="design.write")

    @design.command("compare")
    @click.option("--project1", required=True)
    @click.option("--project2", required=True)
    @click.pass_context
    def compare(click_context: click.Context, project1: str, project2: str) -> None:
        """Compare two projects through the registered review service."""
        run_action(click_context, "design.compare", {"project1": project1, "project2": project2}, permission="design.read")
