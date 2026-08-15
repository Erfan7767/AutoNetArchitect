"""Shared thin adapters used by CLI command groups."""
from __future__ import annotations

from typing import Any, Iterable, Mapping

import click

from cli.confirmation_handler import ConfirmationHandler, ConfirmationPolicy
from cli.context import CLIContext, CLIResult
from cli.error_handler import ErrorHandler


def get_cli_context(click_context: click.Context) -> CLIContext:
    """Return the initialized application context."""
    if not isinstance(click_context.obj, CLIContext):
        raise click.ClickException("CLI context is not initialized")
    return click_context.obj


def require_command(click_context: click.Context, permission: str) -> CLIContext:
    """Enforce one permission and convert failures to stable CLI exits."""
    cli_context = get_cli_context(click_context)
    try:
        cli_context.require(permission)
    except Exception as exc:
        error = ErrorHandler().classify(exc, debug=cli_context.settings.debug)
        click.echo(ErrorHandler().render(exc, debug=cli_context.settings.debug), err=True)
        raise click.exceptions.Exit(error.exit_code)
    return cli_context


def run_action(click_context: click.Context, action: str, payload: Mapping[str, Any] | None = None, *, permission: str | None = None, destructive: bool = False, confirmation: str | None = None, yes: bool = False) -> CLIResult:
    """Authorize and delegate one command action, then render its result."""
    cli_context = get_cli_context(click_context)
    if confirmation is not None:
        accepted = ConfirmationHandler().confirm(ConfirmationPolicy(confirmation, mandatory=destructive), yes=yes)
        if not accepted:
            result = CLIResult(False, "cancelled", "Operation cancelled by user", {"action": action}, 5)
            cli_context.output.emit(result.to_dict(), status=result.status, message=result.message)
            raise click.exceptions.Exit(result.exit_code)
    try:
        result = cli_context.dispatch(action, dict(payload or {}), permission=permission, destructive=destructive)
    except Exception as exc:
        error = ErrorHandler().classify(exc, debug=cli_context.settings.debug)
        click.echo(ErrorHandler().render(exc, debug=cli_context.settings.debug), err=True)
        raise click.exceptions.Exit(error.exit_code)
    cli_context.output.emit(result.data if cli_context.settings.output_format == "table" else result.to_dict(), status=result.status, message=result.message)
    if result.exit_code:
        raise click.exceptions.Exit(result.exit_code)
    return result


def add_standard_options(command: click.Command, *, include_project: bool = True, include_format: bool = False) -> click.Command:
    """Apply common options to dynamically created commands."""
    if include_format:
        command = click.option("--format", "output_format", type=click.Choice(["json", "yaml", "table", "text"]), default=None, help="Override output format for this command.")(command)
    if include_project:
        command = click.option("--project", "project_name", default=None, help="Project identifier.")(command)
    return command


def payload_from_kwargs(kwargs: Mapping[str, Any]) -> dict[str, Any]:
    """Normalize Click keyword arguments and omit unset values."""
    return {str(key): value for key, value in kwargs.items() if value is not None}


def add_action_command(group: click.Group, name: str, action: str, *, help_text: str, permission: str | None = None, options: Iterable[tuple[str, dict[str, Any]]] = (), include_project: bool = True, destructive: bool = False) -> None:
    """Register a simple command that delegates to one action name."""
    def decorator(function):
        wrapped = click.command(name=name, help=help_text)(function)
        wrapped = click.pass_context(wrapped)
        for option_name, option_kwargs in reversed(tuple(options)):
            wrapped = click.option(option_name, **option_kwargs)(wrapped)
        if include_project:
            wrapped = click.option("--project", "project_name", default=None, help="Project identifier.")(wrapped)
        group.add_command(wrapped)
        return wrapped

    @decorator
    def command(click_context: click.Context, **kwargs: Any) -> None:
        payload = payload_from_kwargs(kwargs)
        run_action(click_context, action, payload, permission=permission, destructive=destructive)
