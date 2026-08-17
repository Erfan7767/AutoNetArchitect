"""Installable command-line health entry point for the bounded local site agent."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import click
from pydantic import BaseModel, ConfigDict, ValidationError

from .enrollment import EnrollmentReceipt
from .models import AgentHealth
from .scope import AuthorizedScope


class LocalAgentHealthManifest(BaseModel):
    """Secret-free local manifest needed only to attest enrollment and scope health."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    agent_id: str
    receipt: EnrollmentReceipt
    scope: AuthorizedScope


def read_health_manifest(path: Path) -> LocalAgentHealthManifest:
    """Load a local health manifest while rejecting malformed or extra configuration."""

    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except OSError as error:
        raise click.ClickException(f"Cannot read agent health manifest: {error}") from error
    except json.JSONDecodeError as error:
        raise click.ClickException(f"Agent health manifest is not valid JSON: {error.msg}") from error
    try:
        return LocalAgentHealthManifest.model_validate(payload)
    except ValidationError as error:
        raise click.ClickException(f"Agent health manifest failed validation: {error}") from error


def health_from_manifest(manifest: LocalAgentHealthManifest, now: datetime | None = None) -> AgentHealth:
    """Create a secret-free health record without opening a network or device session."""

    current = now or datetime.now(timezone.utc)
    healthy = manifest.receipt.valid_for(manifest.agent_id, manifest.scope.site_id, manifest.scope.evidence_hash(), current)
    return AgentHealth(
        agent_id=manifest.agent_id,
        site_id=manifest.scope.site_id,
        observed_at=current,
        healthy=healthy,
        detail="Active mutual enrollment matches the acknowledged read-only scope." if healthy else "Enrollment is inactive, expired, or does not match the acknowledged local scope.",
    )


@click.group()
def cli() -> None:
    """Expose only local health attestation; collection remains adapter- and scope-bound."""


@cli.command("health")
@click.option("--manifest", "manifest_path", type=click.Path(exists=True, dir_okay=False, path_type=Path), required=True, help="Secret-free local enrollment and scope manifest.")
def health_command(manifest_path: Path) -> None:
    """Emit one secret-free JSON health record and fail closed if enrollment is unhealthy."""

    record = health_from_manifest(read_health_manifest(manifest_path))
    click.echo(record.model_dump_json())
    if not record.healthy:
        raise click.ClickException("Local agent enrollment health is not active for the acknowledged scope.")


def main() -> None:
    """Start the installable local-agent health command."""

    cli()
