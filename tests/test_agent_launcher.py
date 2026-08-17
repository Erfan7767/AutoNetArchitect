"""Tests for the installable, secret-free local-agent health entry point."""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone

from click.testing import CliRunner

from site_agent.enrollment import EnrollmentReceipt
from site_agent.launcher import cli, health_from_manifest
from site_agent.scope import AuthorizedScope


def manifest_payload(expires_at: datetime) -> dict[str, object]:
    """Return a valid local manifest without device credentials or private key material."""

    scope = AuthorizedScope(
        site_id="site-jeddah-1",
        approved_networks=("10.30.0.0/24",),
        approved_targets=("10.30.0.10",),
        allowed_protocols=("snmp",),
        approval_reference="human-scope-100",
        operator_acknowledged=True,
    )
    receipt = EnrollmentReceipt(
        enrollment_id="enrollment-100-abcdef",
        agent_id="agent-jeddah-1",
        site_id=scope.site_id,
        scope_hash=scope.evidence_hash(),
        agent_fingerprint="agent-fingerprint-100",
        control_plane_fingerprint="control-plane-fingerprint-100",
        enrolled_at=datetime(2026, 8, 17, tzinfo=timezone.utc),
        expires_at=expires_at,
    )
    return {"agent_id": receipt.agent_id, "receipt": receipt.model_dump(mode="json"), "scope": scope.model_dump(mode="json")}


def test_health_command_emits_a_secret_free_active_record(tmp_path) -> None:
    """The installable entry point reports scope-bound health without starting discovery."""

    manifest_path = tmp_path / "agent-health.json"
    manifest_path.write_text(json.dumps(manifest_payload(datetime.now(timezone.utc) + timedelta(hours=1))), encoding="utf-8")

    result = CliRunner().invoke(cli, ["health", "--manifest", str(manifest_path)])

    assert result.exit_code == 0
    output = json.loads(result.output)
    assert output["healthy"] is True
    assert "fingerprint" not in result.output
    assert "credential" not in result.output


def test_health_model_fails_closed_when_receipt_is_expired() -> None:
    """Expired enrollment produces a clear unhealthy record before collection could start."""

    from site_agent.launcher import LocalAgentHealthManifest

    manifest = LocalAgentHealthManifest.model_validate(manifest_payload(datetime(2026, 8, 16, tzinfo=timezone.utc)))
    record = health_from_manifest(manifest, now=datetime(2026, 8, 17, tzinfo=timezone.utc))

    assert not record.healthy
    assert "expired" in record.detail
