"""Equipment and BOM command adapters."""
from __future__ import annotations

import click

from .common import run_action


def register(parent: click.Group) -> None:
    """Register equipment commands."""
    @parent.group("equipment")
    def equipment() -> None:
        """Select equipment, inspect capabilities, and produce BOM outputs."""

    @equipment.command("select")
    @click.option("--project", "project_name", default=None)
    @click.pass_context
    def select(click_context: click.Context, project_name: str | None) -> None:
        """Select equipment through the equipment service boundary."""
        run_action(click_context, "equipment.select", {"project": project_name}, permission="equipment.write")

    for name, action in (("show", "equipment.show"), ("bom", "equipment.bom"), ("compare", "equipment.compare")):
        @equipment.command(name)
        @click.option("--project", "project_name", default=None)
        @click.option("--format", "bom_format", default=None)
        @click.option("--model1", default=None)
        @click.option("--model2", default=None)
        @click.pass_context
        def command(click_context: click.Context, project_name: str | None, bom_format: str | None, model1: str | None, model2: str | None, _action: str = action) -> None:
            """Delegate equipment inspection or BOM action."""
            run_action(click_context, _action, {"project": project_name, "format": bom_format, "model1": model1, "model2": model2}, permission="equipment.read")

    @equipment.group("catalog")
    def catalog() -> None:
        """Search the equipment catalog."""

    @catalog.command("search")
    @click.option("--query", required=True)
    @click.option("--vendor", default=None)
    @click.pass_context
    def catalog_search(click_context: click.Context, query: str, vendor: str | None) -> None:
        """Search equipment catalog records."""
        run_action(click_context, "equipment.catalog.search", {"query": query, "vendor": vendor}, permission="equipment.read")

    @catalog.command("show")
    @click.option("--model", required=True)
    @click.pass_context
    def catalog_show(click_context: click.Context, model: str) -> None:
        """Show one catalog model."""
        run_action(click_context, "equipment.catalog.show", {"model": model}, permission="equipment.read")

    @equipment.command("capabilities")
    @click.option("--model", required=True)
    @click.option("--feature", default=None)
    @click.pass_context
    def capabilities(click_context: click.Context, model: str, feature: str | None) -> None:
        """Inspect capability evidence for a model."""
        run_action(click_context, "equipment.capabilities", {"model": model, "feature": feature}, permission="equipment.read")

    @equipment.command("override")
    @click.option("--project", "project_name", default=None)
    @click.option("--device-id", required=True)
    @click.option("--model", required=True)
    @click.option("--reason", required=True)
    @click.pass_context
    def override(click_context: click.Context, project_name: str | None, device_id: str, model: str, reason: str) -> None:
        """Record a human equipment override through the override service."""
        run_action(click_context, "equipment.override", {"project": project_name, "device_id": device_id, "model": model, "reason": reason}, permission="equipment.write")
