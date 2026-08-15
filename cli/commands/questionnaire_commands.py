"""Questionnaire command adapters."""
from __future__ import annotations

import click

from .common import add_action_command, run_action


def register(parent: click.Group) -> None:
    """Register questionnaire commands."""
    @parent.group("questionnaire")
    def questionnaire() -> None:
        """Collect, validate, import, and export requirements inputs."""

    @questionnaire.command("start")
    @click.option("--project", "project_name", default=None)
    @click.option("--interactive", is_flag=True)
    @click.pass_context
    def start(click_context: click.Context, project_name: str | None, interactive: bool) -> None:
        """Start a questionnaire workflow."""
        run_action(click_context, "questionnaire.start", {"project": project_name, "interactive": interactive}, permission="questionnaire.write")

    for name, action in (("resume", "questionnaire.resume"), ("status", "questionnaire.status"), ("show", "questionnaire.show"), ("validate", "questionnaire.validate"), ("export", "questionnaire.export")):
        @questionnaire.command(name)
        @click.option("--project", "project_name", default=None)
        @click.option("--section", default=None)
        @click.pass_context
        def command(click_context: click.Context, project_name: str | None, section: str | None, _action: str = action) -> None:
            """Delegate a questionnaire read or export action."""
            run_action(click_context, _action, {"project": project_name, "section": section}, permission="questionnaire.read")

    @questionnaire.command("import")
    @click.option("--file", "input_file", required=True, type=click.Path(exists=True, dir_okay=False))
    @click.option("--project", "project_name", default=None)
    @click.pass_context
    def import_answers(click_context: click.Context, input_file: str, project_name: str | None) -> None:
        """Import questionnaire answers from JSON or YAML through a service adapter."""
        run_action(click_context, "questionnaire.import", {"file": input_file, "project": project_name}, permission="questionnaire.write")

    @questionnaire.command("reset")
    @click.option("--project", "project_name", default=None)
    @click.option("--confirm", "confirmed", is_flag=True)
    @click.pass_context
    def reset(click_context: click.Context, project_name: str | None, confirmed: bool) -> None:
        """Reset questionnaire values only after explicit confirmation."""
        if not confirmed:
            raise click.UsageError("--confirm is required for questionnaire reset")
        run_action(click_context, "questionnaire.reset", {"project": project_name}, permission="questionnaire.write", destructive=True)
