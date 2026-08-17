"""Concrete Ed25519 trust-store tests for the local-agent enrollment boundary."""

from __future__ import annotations

import base64
from datetime import datetime, timezone

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from site_agent.enrollment import EnrollmentRequest, PinnedMutualEnrollmentAuthority
from site_agent.scope import AuthorizedScope
from site_agent.trust import PinnedTrustStore, TrustedAgentPublicKey, TrustedPublicKey, public_key_fingerprint


def public_pem(private_key: Ed25519PrivateKey) -> str:
    """Serialize the public component only for a pinning test fixture."""

    return private_key.public_key().public_bytes(serialization.Encoding.PEM, serialization.PublicFormat.SubjectPublicKeyInfo).decode("utf-8")


def signed(private_key: Ed25519PrivateKey, payload: bytes) -> str:
    """Return a base64 detached Ed25519 signature for one exact canonical payload."""

    return base64.b64encode(private_key.sign(payload)).decode("ascii")


def scope() -> AuthorizedScope:
    """Build one approved read-only scope used in the enrollment proof."""

    return AuthorizedScope(
        site_id="site-dammam-1",
        approved_networks=("10.40.0.0/24",),
        approved_targets=("10.40.0.10",),
        allowed_protocols=("netconf",),
        approval_reference="human-scope-dammam-100",
        operator_acknowledged=True,
    )


def test_pinned_ed25519_authority_requires_the_provisioned_control_plane_and_agent_keys() -> None:
    """Issue an enrollment receipt only when both detached proofs use pre-provisioned public keys."""

    control_plane_private = Ed25519PrivateKey.generate()
    agent_private = Ed25519PrivateKey.generate()
    control_plane_pem = public_pem(control_plane_private)
    agent_pem = public_pem(agent_private)
    control_plane_fingerprint = public_key_fingerprint(control_plane_pem)
    agent_fingerprint = public_key_fingerprint(agent_pem)
    trust_store = PinnedTrustStore(
        control_plane=TrustedPublicKey(fingerprint=control_plane_fingerprint, public_key_pem=control_plane_pem),
        agents=(TrustedAgentPublicKey(agent_id="agent-dammam-1", fingerprint=agent_fingerprint, public_key_pem=agent_pem),),
    )
    authority = PinnedMutualEnrollmentAuthority(trust_store)
    approved_scope = scope()
    unsigned_request = EnrollmentRequest(
        agent_id="agent-dammam-1",
        site_id=approved_scope.site_id,
        scope_hash=approved_scope.evidence_hash(),
        control_plane_fingerprint=control_plane_fingerprint,
        agent_fingerprint=agent_fingerprint,
        control_plane_proof="temporary-proof-value",
    )
    request = unsigned_request.model_copy(update={"control_plane_proof": signed(control_plane_private, unsigned_request.signed_payload())})

    begun = authority.begin(request, datetime(2026, 8, 17, tzinfo=timezone.utc))

    assert begun.accepted and begun.challenge is not None
    completed = authority.complete(begun.challenge.challenge_id, signed(agent_private, begun.challenge.agent_payload()), datetime(2026, 8, 17, tzinfo=timezone.utc))
    assert completed.accepted and completed.receipt is not None
    assert completed.receipt.valid_for("agent-dammam-1", approved_scope.site_id, approved_scope.evidence_hash(), datetime(2026, 8, 17, tzinfo=timezone.utc))


def test_pinned_ed25519_authority_rejects_an_unprovisioned_agent_fingerprint() -> None:
    """Fail closed before challenge issuance when the declared agent key is not provisioned."""

    control_plane_private = Ed25519PrivateKey.generate()
    provisioned_agent_private = Ed25519PrivateKey.generate()
    unprovisioned_agent_private = Ed25519PrivateKey.generate()
    control_plane_pem = public_pem(control_plane_private)
    provisioned_agent_pem = public_pem(provisioned_agent_private)
    trust_store = PinnedTrustStore(
        control_plane=TrustedPublicKey(fingerprint=public_key_fingerprint(control_plane_pem), public_key_pem=control_plane_pem),
        agents=(TrustedAgentPublicKey(agent_id="agent-dammam-1", fingerprint=public_key_fingerprint(provisioned_agent_pem), public_key_pem=provisioned_agent_pem),),
    )
    approved_scope = scope()
    unsigned_request = EnrollmentRequest(
        agent_id="agent-dammam-1",
        site_id=approved_scope.site_id,
        scope_hash=approved_scope.evidence_hash(),
        control_plane_fingerprint=trust_store.control_plane.fingerprint,
        agent_fingerprint=public_key_fingerprint(public_pem(unprovisioned_agent_private)),
        control_plane_proof="temporary-proof-value",
    )
    request = unsigned_request.model_copy(update={"control_plane_proof": signed(control_plane_private, unsigned_request.signed_payload())})

    decision = PinnedMutualEnrollmentAuthority(trust_store).begin(request, datetime(2026, 8, 17, tzinfo=timezone.utc))

    assert not decision.accepted
    assert "not provisioned" in decision.reason
