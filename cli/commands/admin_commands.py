"""Administrative command adapters."""
from __future__ import annotations

import getpass
from typing import Any

import click

from cli.auth_handler import AuthHandler
from .common import get_cli_context, require_command, run_action


def register(parent: click.Group) -> None:
    """Register administrative commands."""
    @parent.group("admin")
    def admin() -> None:
        """Manage local authentication, roles, settings, and system backup."""

    @admin.command("login")
    @click.option("--username", default="admin")
    @click.option("--ttl", type=int, default=3600)
    @click.pass_context
    def login(click_context: click.Context, username: str, ttl: int) -> None:
        """Authenticate a local user."""
        cli_context = get_cli_context(click_context)
        try:
            result = AuthHandler(cli_context).login(username, ttl_seconds=ttl)
        except Exception as exc:
            raise click.ClickException(str(exc))
        cli_context.output.emit(result.to_dict(), status=result.status, message=result.message)

    @admin.command("logout")
    @click.pass_context
    def logout(click_context: click.Context) -> None:
        """Revoke the current local session."""
        cli_context = get_cli_context(click_context)
        result = AuthHandler(cli_context).logout()
        cli_context.output.emit(result.to_dict(), status=result.status, message=result.message)

    @admin.command("whoami")
    @click.pass_context
    def whoami(click_context: click.Context) -> None:
        """Show current principal metadata."""
        cli_context = get_cli_context(click_context)
        result = AuthHandler(cli_context).whoami()
        cli_context.output.emit(result.to_dict(), status=result.status, message=result.message)

    @admin.group("user")
    def user() -> None:
        """Manage local users."""

    @user.command("create")
    @click.option("--username", required=True)
    @click.option("--role", "roles", multiple=True, required=True)
    @click.option("--password", default=None, help="Password input; prefer prompt when omitted.")
    @click.pass_context
    def user_create(click_context: click.Context, username: str, roles: tuple[str, ...], password: str | None) -> None:
        """Create a local user without printing credential values."""
        cli_context = require_command(click_context, "admin")
        secret = password or getpass.getpass("Password: ")
        record = cli_context.auth_manager.create_user(username, secret, tuple(roles))
        cli_context.output.emit({"username": record.username, "roles": list(record.roles), "active": record.active}, status="created", message="User created")

    @user.command("list")
    @click.pass_context
    def user_list(click_context: click.Context) -> None:
        """List users without password hashes."""
        cli_context = require_command(click_context, "admin")
        users = [{"username": item.username, "roles": list(item.roles), "active": item.active, "last_login_at": item.last_login_at} for item in cli_context.auth_manager.list_users()]
        cli_context.output.emit({"users": users}, status="listed", message="Users listed")

    for name, action in (("show", "admin.user.show"), ("modify", "admin.user.modify"), ("delete", "admin.user.delete")):
        @user.command(name)
        @click.option("--username", required=True)
        @click.option("--role", default=None)
        @click.option("--confirm", "confirmed", is_flag=True)
        @click.pass_context
        def user_action(click_context: click.Context, username: str, role: str | None, confirmed: bool, _action: str = action) -> None:
            """Delegate user administration through the auth service boundary."""
            if _action == "admin.user.delete" and not confirmed:
                raise click.UsageError("--confirm is required for user delete")
            run_action(click_context, _action, {"username": username, "role": role, "confirmed": confirmed}, permission="admin", destructive=_action == "admin.user.delete")

    @admin.group("roles")
    def roles() -> None:
        """Inspect configured roles and permissions."""

    @roles.command("list")
    @click.pass_context
    def roles_list(click_context: click.Context) -> None:
        """List configured roles and permissions."""
        cli_context = require_command(click_context, "admin")
        roles_data = [{"name": role.name, "permissions": sorted(role.permissions), "description": role.description} for role in cli_context.rbac.roles()]
        cli_context.output.emit({"roles": roles_data}, status="listed", message="Roles listed")

    @admin.group("settings")
    def settings() -> None:
        """Inspect or update local CLI settings."""

    @settings.command("show")
    @click.pass_context
    def settings_show(click_context: click.Context) -> None:
        """Show local settings without secrets."""
        cli_context = require_command(click_context, "admin")
        cli_context.output.emit({"output_format": cli_context.settings.output_format, "verbose": cli_context.settings.verbose, "debug": cli_context.settings.debug, "root": str(cli_context.settings.root)}, status="loaded", message="Settings loaded")

    @settings.command("set")
    @click.option("--key", required=True)
    @click.option("--value", required=True)
    @click.pass_context
    def settings_set(click_context: click.Context, key: str, value: str) -> None:
        """Delegate a settings update to the local settings service."""
        run_action(click_context, "admin.settings.set", {"key": key, "value": value}, permission="admin")

    @admin.group("secrets")
    def secrets() -> None:
        """Manage secret metadata and rotation requests."""

    @secrets.command("rotate")
    @click.option("--type", "secret_type", default="all")
    @click.pass_context
    def secrets_rotate(click_context: click.Context, secret_type: str) -> None:
        """Request governed secret rotation without showing values."""
        run_action(click_context, "admin.secrets.rotate", {"type": secret_type}, permission="admin", destructive=True)

    @admin.command("backup-system")
    @click.option("--path", "output_path", required=True)
    @click.pass_context
    def backup_system(click_context: click.Context, output_path: str) -> None:
        """Create a local system backup through a registered service."""
        run_action(click_context, "admin.backup_system", {"path": output_path}, permission="admin")

    @admin.command("restore-system")
    @click.option("--path", "input_path", required=True, type=click.Path(exists=True, dir_okay=False))
    @click.option("--confirm", "confirmed", is_flag=True)
    @click.pass_context
    def restore_system(click_context: click.Context, input_path: str, confirmed: bool) -> None:
        """Restore a local system backup after explicit confirmation."""
        if not confirmed:
            raise click.UsageError("--confirm is required for system restore")
        run_action(click_context, "admin.restore_system", {"path": input_path}, permission="admin", destructive=True)
