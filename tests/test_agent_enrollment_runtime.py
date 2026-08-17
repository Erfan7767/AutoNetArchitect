"""Tests for mutual enrollment and the bounded local read-only agent runtime."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from site_agent.enrollment import EnrollmentRequest, MutualEnrollmentAuthority
from site_agent.models import DiscoveryResult, DiscoveryState, DiscoveryTarget, ManagementProtocol
from site_agent.runtime import EnrolledReadOnlyAgent
from site_agent.scope import AuthorizedScope


class DeterministicVerifier:
    """Test-only verifier that makes the signed payload expectation inspectable."""

    def verify(self, fingerprint: str, payload: bytes, proof: str) -> bool:
        """Accept only a proof encoding the fingerprint and exact canonical payload."""

        return proof == f"proof:{fingerprint}:{payload.decode('utf-8')}"


def proof_for(fingerprint: str, payload: bytes) -> str:
    """Create the deterministic test proof for one payload."""

    return f"proof:{fingerprint}:{payload.decode('utf-8')}"


def scope() -> AuthorizedScope:
    """Create an acknowledged, strictly bounded local discovery scope."""

    return AuthorizedScope(
        site_id="site-riyadh-1",
        approved_networks=("10.24.0.0/24",),
        approved_targets=("10.24.0.10",),
        allowed_protocols=(ManagementProtocol.HTTPS_API,),
        approval_reference="human-scope-review-001",
        operator_acknowledged=True,
    )


def request_for(authorized_scope: AuthorizedScope, control_plane_fingerprint: str = "control-plane-fingerprint-001") -> EnrollmentRequest:
    """Build a control-plane signed enrollment request for the exact local scope."""

    unsigned = EnrollmentRequest(
        agent_id="agent-riyadh-1",
        site_id=authorized_scope.site_id,
        scope_hash=authorized_scope.evidence_hash(),
        control_plane_fingerprint=control_plane_fingerprint,
        agent_fingerprint="agent-fingerprint-001",
        control_plane_proof="temporary-proof-value",
    )
    return unsigned.model_copy(update={"control_plane_proof": proof_for(control_plane_fingerprint, unsigned.signed_payload())})


def enrolled_receipt(authorized_scope: AuthorizedScope, now: datetime):
    """Perform both proof steps and return the issued bounded receipt."""

    authority = MutualEnrollmentAuthority("control-plane-fingerprint-001", DeterministicVerifier())
    began = authority.begin(request_for(authorized_scope), now)
    assert began.challenge is not None
    completed = authority.complete(began.challenge.challenge_id, proof_for("agent-fingerprint-001", began.challenge.agent_payload()), now)
    assert completed.receipt is not None
    return completed.receipt


def test_enrollment_requires_a_pinned_control_plane_and_local_agent_proof() -> None:
    """Reject unpinned control identities and issue no receipt before both proof steps pass."""

    now = datetime(2026, 8, 17, tzinfo=timezone.utc)
    authorized_scope = scope()
    authority = MutualEnrollmentAuthority("control-plane-fingerprint-001", DeterministicVerifier())

    untrusted = authority.begin(request_for(authorized_scope, "different-control-plane-fingerprint"), now)
    assert not untrusted.accepted
    assert untrusted.receipt is None

    began = authority.begin(request_for(authorized_scope), now)
    assert began.accepted and began.challenge is not None
    rejected = authority.complete(began.challenge.challenge_id, "invalid-agent-proof", now)
    assert not rejected.accepted
    assert rejected.receipt is None


def test_enrolled_runtime_reports_health_and_collects_only_authorized_targets() -> None:
    """Run a collector only while receipt and local scope are both active and exact."""

    now = datetime(2026, 8, 17, tzinfo=timezone.utc)
    authorized_scope = scope()
    receipt = enrolled_receipt(authorized_scope, now)
    calls: list[DiscoveryTarget] = []

    def collector(target: DiscoveryTarget) -> DiscoveryResult:
        calls.append(target)
        return DiscoveryResult(target=target, state=DiscoveryState.DISCOVERED, message="Read-only evidence recorded.")

    runtime = EnrolledReadOnlyAgent(receipt, authorized_scope, collector, now=lambda: now)
    target = DiscoveryTarget(address="10.24.0.10", protocol=ManagementProtocol.HTTPS_API, credential_reference="credential-reference-01")

    assert runtime.health().healthy
    assert runtime.discover(target).state is DiscoveryState.DISCOVERED
    assert calls == [target]

    denied = runtime.discover(DiscoveryTarget(address="10.24.0.11", protocol=ManagementProtocol.HTTPS_API, credential_reference="credential-reference-01"))
    assert denied.state is DiscoveryState.UNAUTHORIZED
    assert calls == [target]


def test_expired_or_scope_mismatched_receipt_blocks_any_local_collection() -> None:
    """Prevent collection after enrollment expiry or when scope differs from the receipt."""

    now = datetime(2026, 8, 17, tzinfo=timezone.utc)
    authorized_scope = scope()
    receipt = enrolled_receipt(authorized_scope, now)
    calls: list[DiscoveryTarget] = []

    def collector(target: DiscoveryTarget) -> DiscoveryResult:
        calls.append(target)
        return DiscoveryResult(target=target, state=DiscoveryState.DISCOVERED, message="Unexpected collection.")

    with pytest.raises(ValueError, match="active read-only enrollment receipt"):
        EnrolledReadOnlyAgent(receipt, authorized_scope, collector, now=lambda: now + timedelta(days=2))
    assert calls == []

    different_scope = authorized_scope.model_copy(update={"approval_reference": "different-human-approval"})
    with pytest.raises(ValueError, match="matching the local acknowledged scope"):
        EnrolledReadOnlyAgent(receipt, different_scope, collector, now=lambda: now)
