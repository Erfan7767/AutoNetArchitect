"""Mutual-authentication enrollment records for the local read-only agent.

The module stores only identity and certificate/public-key fingerprints. Signature
verification is injected so production callers can use their approved OS-backed
certificate or hardware-key provider without placing private keys in this project.
"""

from __future__ import annotations

import secrets
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from hashlib import sha256
from typing import Protocol

from pydantic import BaseModel, ConfigDict, Field

from .trust import Ed25519PinnedSignatureVerifier, PinnedTrustStore


def _utc_now() -> datetime:
    """Return a timezone-aware UTC timestamp."""

    return datetime.now(timezone.utc)


def _canonical_payload(values: dict[str, str]) -> bytes:
    """Produce a deterministic, secret-free payload for an external verifier."""

    return "\n".join(f"{key}={values[key]}" for key in sorted(values)).encode("utf-8")


class SignatureVerifier(Protocol):
    """Verify a detached proof using a known public-key or certificate fingerprint."""

    def verify(self, fingerprint: str, payload: bytes, proof: str) -> bool:
        """Return true only when the proof is valid for the supplied identity."""


class EnrollmentRequest(BaseModel):
    """Control-plane signed request to begin enrollment of one local agent identity."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    agent_id: str = Field(min_length=3, max_length=160)
    site_id: str = Field(min_length=1, max_length=160)
    scope_hash: str = Field(min_length=32, max_length=160)
    control_plane_fingerprint: str = Field(min_length=16, max_length=256)
    agent_fingerprint: str = Field(min_length=16, max_length=256)
    control_plane_proof: str = Field(min_length=16, max_length=4096)

    def signed_payload(self) -> bytes:
        """Return the exact request fields authenticated by the control plane."""

        return _canonical_payload({
            "agent_fingerprint": self.agent_fingerprint,
            "agent_id": self.agent_id,
            "scope_hash": self.scope_hash,
            "site_id": self.site_id,
        })


class EnrollmentChallenge(BaseModel):
    """One-time server challenge that the intended local agent must prove."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    challenge_id: str = Field(min_length=16, max_length=256)
    nonce: str = Field(min_length=16, max_length=256)
    agent_id: str
    site_id: str
    scope_hash: str
    expires_at: datetime

    def agent_payload(self) -> bytes:
        """Return the challenge payload that must be signed by the local agent."""

        return _canonical_payload({
            "agent_id": self.agent_id,
            "challenge_id": self.challenge_id,
            "nonce": self.nonce,
            "scope_hash": self.scope_hash,
            "site_id": self.site_id,
        })


class EnrollmentReceipt(BaseModel):
    """Secret-free receipt proving enrollment for one bounded read-only scope."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    enrollment_id: str = Field(min_length=16, max_length=256)
    agent_id: str
    site_id: str
    scope_hash: str
    agent_fingerprint: str
    control_plane_fingerprint: str
    mode: str = "read_only"
    enrolled_at: datetime
    expires_at: datetime
    active: bool = True

    def valid_for(self, agent_id: str, site_id: str, scope_hash: str, now: datetime | None = None) -> bool:
        """Return whether this active receipt binds the exact local identity and scope."""

        current = now or _utc_now()
        return self.active and self.mode == "read_only" and current < self.expires_at and self.agent_id == agent_id and self.site_id == site_id and self.scope_hash == scope_hash


@dataclass(frozen=True)
class EnrollmentDecision:
    """Non-sensitive enrollment result that never includes proof or key material."""

    accepted: bool
    reason: str
    challenge: EnrollmentChallenge | None = None
    receipt: EnrollmentReceipt | None = None


@dataclass(frozen=True)
class _PendingEnrollment:
    """In-memory correlation data retained only until a challenge is completed."""

    request: EnrollmentRequest
    challenge: EnrollmentChallenge


class MutualEnrollmentAuthority:
    """Issue bounded enrollment receipts after control plane and local agent prove identity."""

    def __init__(self, trusted_control_plane_fingerprint: str, verifier: SignatureVerifier, challenge_ttl: timedelta = timedelta(minutes=5), receipt_ttl: timedelta = timedelta(hours=24)) -> None:
        """Create a verifier using an explicitly pinned control-plane fingerprint."""

        if challenge_ttl <= timedelta(0) or receipt_ttl <= timedelta(0):
            raise ValueError("Enrollment lifetimes must be positive.")
        self._trusted_control_plane_fingerprint = trusted_control_plane_fingerprint
        self._verifier = verifier
        self._challenge_ttl = challenge_ttl
        self._receipt_ttl = receipt_ttl
        self._pending: dict[str, _PendingEnrollment] = {}

    def begin(self, request: EnrollmentRequest, now: datetime | None = None) -> EnrollmentDecision:
        """Validate the signed control-plane request and return a one-time agent challenge."""

        current = now or _utc_now()
        if request.control_plane_fingerprint != self._trusted_control_plane_fingerprint:
            return EnrollmentDecision(False, "Control-plane identity fingerprint is not pinned for this agent.")
        if not self._verifier.verify(request.control_plane_fingerprint, request.signed_payload(), request.control_plane_proof):
            return EnrollmentDecision(False, "Control-plane enrollment proof did not verify.")
        challenge = EnrollmentChallenge(
            challenge_id=secrets.token_urlsafe(24),
            nonce=secrets.token_urlsafe(24),
            agent_id=request.agent_id,
            site_id=request.site_id,
            scope_hash=request.scope_hash,
            expires_at=current + self._challenge_ttl,
        )
        self._pending[challenge.challenge_id] = _PendingEnrollment(request=request, challenge=challenge)
        return EnrollmentDecision(True, "Control-plane identity verified; local agent proof is required.", challenge=challenge)

    def complete(self, challenge_id: str, agent_proof: str, now: datetime | None = None) -> EnrollmentDecision:
        """Verify the local agent proof and issue one active, read-only receipt."""

        current = now or _utc_now()
        pending = self._pending.pop(challenge_id, None)
        if pending is None:
            return EnrollmentDecision(False, "Enrollment challenge is unknown, already used, or expired.")
        if current >= pending.challenge.expires_at:
            return EnrollmentDecision(False, "Enrollment challenge expired before local agent proof was received.")
        if not self._verifier.verify(pending.request.agent_fingerprint, pending.challenge.agent_payload(), agent_proof):
            return EnrollmentDecision(False, "Local agent enrollment proof did not verify.")
        receipt_payload = _canonical_payload({
            "agent_id": pending.request.agent_id,
            "agent_fingerprint": pending.request.agent_fingerprint,
            "scope_hash": pending.request.scope_hash,
            "site_id": pending.request.site_id,
        })
        receipt = EnrollmentReceipt(
            enrollment_id=sha256(receipt_payload + str(current.timestamp()).encode("utf-8")).hexdigest(),
            agent_id=pending.request.agent_id,
            site_id=pending.request.site_id,
            scope_hash=pending.request.scope_hash,
            agent_fingerprint=pending.request.agent_fingerprint,
            control_plane_fingerprint=pending.request.control_plane_fingerprint,
            enrolled_at=current,
            expires_at=current + self._receipt_ttl,
        )
        return EnrollmentDecision(True, "Mutual identity proof verified; read-only enrollment is active.", receipt=receipt)


class PinnedMutualEnrollmentAuthority:
    """Concrete enrollment authority bound to provisioned Ed25519 public-key trust material."""

    def __init__(self, trust_store: PinnedTrustStore, challenge_ttl: timedelta = timedelta(minutes=5), receipt_ttl: timedelta = timedelta(hours=24)) -> None:
        """Create an authority that accepts only the pinned control plane and provisioned agent keys."""

        trust_store.validate()
        self._trust_store = trust_store
        self._authority = MutualEnrollmentAuthority(
            trusted_control_plane_fingerprint=trust_store.control_plane.fingerprint,
            verifier=Ed25519PinnedSignatureVerifier(trust_store),
            challenge_ttl=challenge_ttl,
            receipt_ttl=receipt_ttl,
        )

    def begin(self, request: EnrollmentRequest, now: datetime | None = None) -> EnrollmentDecision:
        """Begin only if the request identities match the administrator-provisioned trust binding."""

        agent = self._trust_store.agent_for(request.agent_id)
        if agent is None or request.agent_fingerprint != agent.fingerprint:
            return EnrollmentDecision(False, "Agent identity is not provisioned with the supplied pinned public-key fingerprint.")
        return self._authority.begin(request, now)

    def complete(self, challenge_id: str, agent_proof: str, now: datetime | None = None) -> EnrollmentDecision:
        """Complete the concrete Ed25519 local-agent proof flow."""

        return self._authority.complete(challenge_id, agent_proof, now)
