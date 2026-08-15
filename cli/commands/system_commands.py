"""System command adapters."""
from __future__ import annotations

import platform
import sys

import click

from .common import get_cli_context, require_command, run_action


def register(parent: click.Group) -> None:
    """Register system commands."""
    @parent.group("system")
    def system() -> None:
        """Inspect system health and local persistence services."""

    @system.command("info")
    @click.pass_context
    def info(click_context: click.Context) -> None:
        """Show local runtime information."""
        cli_context = require_command(click_context, "system")
        cli_context.output.emit({"python": sys.version, "platform": platform.platform(), "root": str(cli_context.settings.root), "version": "0.1.0"}, status="loaded", message="System information")

    @system.command("health")
    @click.pass_context
    def health(click_context: click.Context) -> None:
        """Check local persistence and audit integrity."""
        cli_context = require_command(click_context, "system")
        audit_ok = cli_context.audit_trail.verify_integrity()
        cli_context.output.emit({"audit_integrity": audit_ok, "project_root_exists": cli_context.persistence.root.exists(), "session_store_exists": cli_context.session_manager.path.exists()}, status="healthy" if audit_ok else "error", message="System health checked")

    @system.group("dependencies")
    def dependencies() -> None:
        """Inspect optional dependency availability."""

    @dependencies.command("check")
    @click.pass_context
    def dependencies_check(click_context: click.Context) -> None:
        """Check dependency availability without installing packages."""
        cli_context = require_command(click_context, "system")
        dependencies_data = {}
        for name in ("click", "rich", "typer", "yaml"):
            try:
                __import__(name)
                dependencies_data[name] = "available"
            except ImportError:
                dependencies_data[name] = "unavailable"
        cli_context.output.emit({"dependencies": dependencies_data, "installation_performed": False}, status="checked", message="Dependencies checked")

    @dependencies.command("install")
    @click.option("--optional", is_flag=True)
    @click.pass_context
    def dependencies_install(click_context: click.Context, optional: bool) -> None:
        """Delegate dependency installation to an external governed service."""
        run_action(click_context, "system.dependencies.install", {"optional": optional}, permission="system")

    @system.group("db")
    def db() -> None:
        """Inspect or migrate local database state."""

    for name, action in (("migrate", "system.db.migrate"), ("status", "system.db.status"), ("backup", "system.db.backup")):
        @db.command(name)
        @click.option("--path", "output_path", default=None)
        @click.pass_context
        def command(click_context: click.Context, output_path: str | None, _action: str = action) -> None:
            """Delegate database operation."""
            run_action(click_context, _action, {"path": output_path}, permission="system")

    @system.command("cache")
    @click.option("--clear", is_flag=True)
    @click.pass_context
    def cache(click_context: click.Context, clear: bool) -> None:
        """Request cache inspection or clearing through system boundary."""
        run_action(click_context, "system.cache.clear" if clear else "system.cache.status", {"clear": clear}, permission="system", destructive=clear)

    @system.command("update-check")
    @click.pass_context
    def update_check(click_context: click.Context) -> None:
        """Check for available updates through a registered service."""
        run_action(click_context, "system.update_check", {}, permission="system")
