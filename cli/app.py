"""Click application root and command-group registration."""
from __future__ import annotations

from pathlib import Path
from typing import Any

import click

from .context import CLIContext, CLISettings
from .commands import (
    admin_commands,
    audit_commands,
    change_commands,
    compliance_commands,
    config_commands,
    deploy_commands,
    design_commands,
    diagram_commands,
    equipment_commands,
    export_commands,
    incident_commands,
    lab_commands,
    operations_commands,
    project_commands,
    questionnaire_commands,
    report_commands,
    system_commands,
    troubleshoot_commands,
    validate_commands,
)


VERSION = "0.1.0"


@click.group(context_settings={"help_option_names": ["-h", "--help"]})
@click.option("--project", "project_name", "-p", default=None, help="Current project identifier.")
@click.option("--output-format", "output_format", "-o", type=click.Choice(["json", "yaml", "table", "text"]), default="text", show_default=True, help="Output format.")
@click.option("--verbose", "verbose", "-v", count=True, help="Increase diagnostic verbosity.")
@click.option("--debug", is_flag=True, help="Show stack traces for unexpected errors.")
@click.option("--quiet", "quiet", "-q", is_flag=True, help="Emit errors only.")
@click.option("--no-color", is_flag=True, help="Disable ANSI color output.")
@click.option("--config", "config_path", type=click.Path(dir_okay=False, path_type=Path), default=None, help="Configuration file override.")
@click.version_option(VERSION, prog_name="autonet")
@click.pass_context
def cli(click_context: click.Context, project_name: str | None, output_format: str, verbose: int, debug: bool, quiet: bool, no_color: bool, config_path: Path | None) -> None:
    """AutoNetArchitect professional network design and operations CLI."""
    if click_context.obj is None:
        settings = CLISettings(project=project_name, output_format=output_format, verbose=verbose, debug=debug, quiet=quiet, no_color=no_color, config_path=str(config_path) if config_path else None)
        click_context.obj = CLIContext(settings)


for _register in (
    project_commands.register,
    questionnaire_commands.register,
    design_commands.register,
    equipment_commands.register,
    config_commands.register,
    validate_commands.register,
    deploy_commands.register,
    operations_commands.register,
    troubleshoot_commands.register,
    incident_commands.register,
    change_commands.register,
    compliance_commands.register,
    report_commands.register,
    diagram_commands.register,
    export_commands.register,
    lab_commands.register,
    admin_commands.register,
    audit_commands.register,
    system_commands.register,
):
    _register(cli)
