"""End-to-end local boundary test for enrollment, durable receipt, and signed health output."""

from __future__ import annotations

import base64
from datetime import datetime, timezone

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from site_agent.enrollment import EnrollmentRequest, PinnedMutualEnrollmentAuthority
from site_agent.health_reporting import ControlPlaneHealthReporter
from site_agent.models import AgentHealth, ManagementProtocol
from site_agent.scope import AuthorizedScope
from site_agent.trust import PinnedTrustStore, TrustedAgentPublicKey, TrustedPublicKey, public_key_fingerprint
from windows_app.workspace import WindowsWorkspace


def pem(key: Ed25519PrivateKey) -> str:
    """Return public key PEM for the pinned trust store fixture."""

    return key.public_key().public_bytes(serialization.Encoding.PEM, serialization.PublicFormat.SubjectPublicKeyInfo).decode("utf-8")


def detached_signature(key: Ed25519PrivateKey, payload: bytes) -> str:
    """Return an Ed25519 base64 proof for a canonical payload."""

    return base64.b64encode(key.sign(payload)).decode("ascii")


class CapturingTransport:
    """Capture one signed health payload as the local agent boundary output."""

    def __init__(self) -> None:
        """Initialize an empty accepted transport capture."""

        self.payload: dict[str, str | bool] | None = None

    def post_health(self, payload: dict[str, str | bool]) -> int:
        """Capture and acknowledge the report; no discovery or device operation occurs."""

        self.payload = payload
        return 202


def test_pinned_enrollment_receipt_persists_and_binds_a_signed_read_only_health_report(tmp_path) -> None:
    """Exercise the complete local enrollment boundary without storing a private key or opening a device session."""

    control_plane_key = Ed25519PrivateKey.generate()
    agent_key = Ed25519PrivateKey.generate()
    control_plane_pem = pem(control_plane_key)
    agent_pem = pem(agent_key)
    control_plane_fingerprint = public_key_fingerprint(control_plane_pem)
    agent_fingerprint = public_key_fingerprint(agent_pem)
    scope = AuthorizedScope(
        site_id="site-madinah-1",
        approved_networks=("10.50.0.0/24",),
        approved_targets=("10.50.0.10",),
        allowed_protocols=(ManagementProtocol.SNMP,),
        approval_reference="human-scope-madinah-01",
        operator_acknowledged=True,
    )
    trust = PinnedTrustStore(
        control_plane=TrustedPublicKey(fingerprint=control_plane_fingerprint, public_key_pem=control_plane_pem),
        agents=(TrustedAgentPublicKey(agent_id="agent-madinah-1", fingerprint=agent_fingerprint, public_key_pem=agent_pem),),
    )
    unsigned = EnrollmentRequest(
        agent_id="agent-madinah-1",
        site_id=scope.site_id,
        scope_hash=scope.evidence_hash(),
        control_plane_fingerprint=control_plane_fingerprint,
        agent_fingerprint=agent_fingerprint,
        control_plane_proof="temporary-proof-value",
    )
    request = unsigned.model_copy(update={"control_plane_proof": detached_signature(control_plane_key, unsigned.signed_payload())})
    now = datetime(2026, 8, 17, tzinfo=timezone.utc)
    authority = PinnedMutualEnrollmentAuthority(trust)
    challenge = authority.begin(request, now).challenge
    assert challenge is not None
    receipt = authority.complete(challenge.challenge_id, detached_signature(agent_key, challenge.agent_payload()), now).receipt
    assert receipt is not None

    workspace = WindowsWorkspace(tmp_path / "agent-workspace")
    workspace.save_enrollment_receipt(receipt)
    persisted = workspace.load_enrollment_receipt()
    assert persisted == receipt

    transport = CapturingTransport()
    reporter = ControlPlaneHealthReporter(persisted, agent_key, transport)
    health = AgentHealth(agent_id=receipt.agent_id, site_id=receipt.site_id, healthy=True, detail="Mutual enrollment is active for the exact acknowledged read-only scope.")
    assert reporter.report(health)
    assert transport.payload is not None
    assert transport.payload["enrollmentId"] == receipt.enrollment_id
    assert transport.payload["mode"] == "read_only"
    assert "private" not in str(transport.payload).lower()
    assert "credential" not in str(transport.payload).lower()
