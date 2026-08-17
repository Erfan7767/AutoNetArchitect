"""Signed, secret-free health reporting from an enrolled site agent to the control plane."""

from __future__ import annotations

import base64
import json
from dataclasses import dataclass
from datetime import datetime
from typing import Protocol

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from .enrollment import EnrollmentReceipt
from .models import AgentHealth


def _canonical_health_payload(receipt: EnrollmentReceipt, health: AgentHealth) -> bytes:
    """Return the deterministic payload authenticated by the local agent private key."""

    values = {
        "agent_id": health.agent_id,
        "detail": health.detail,
        "enrollment_id": receipt.enrollment_id,
        "healthy": health.healthy,
        "mode": health.mode,
        "observed_at": health.observed_at.isoformat(),
        "scope_hash": receipt.scope_hash,
        "site_id": health.site_id,
    }
    return "\n".join(f"{key}={values[key]}" for key in sorted(values)).encode("utf-8")


@dataclass(frozen=True)
class SignedHealthReport:
    """Signed health payload with no credential, private-key, or device data field."""

    enrollment_id: str
    agent_id: str
    site_id: str
    scope_hash: str
    healthy: bool
    mode: str
    detail: str
    observed_at: datetime
    signature: str

    def payload(self) -> dict[str, str | bool]:
        """Return a transport-ready JSON dictionary excluding any local private-key material."""

        return {
            "enrollmentId": self.enrollment_id,
            "agentId": self.agent_id,
            "siteId": self.site_id,
            "scopeHash": self.scope_hash,
            "healthy": self.healthy,
            "mode": self.mode,
            "detail": self.detail,
            "observedAt": self.observed_at.isoformat(),
            "signature": self.signature,
        }


class HealthReportTransport(Protocol):
    """Post one signed report to the configured control-plane endpoint."""

    def post_health(self, payload: dict[str, str | bool]) -> int:
        """Return the HTTP-like status for a submitted signed health report."""


class ControlPlaneHealthReporter:
    """Sign and send current agent health; transport failures cannot trigger device work."""

    def __init__(self, receipt: EnrollmentReceipt, signing_key: Ed25519PrivateKey, transport: HealthReportTransport) -> None:
        """Bind one enrolled agent receipt to its locally held signing key and transport."""

        self._receipt = receipt
        self._signing_key = signing_key
        self._transport = transport

    def build(self, health: AgentHealth) -> SignedHealthReport:
        """Build an identity-bound report only when the health record matches the enrollment receipt."""

        if health.agent_id != self._receipt.agent_id or health.site_id != self._receipt.site_id:
            raise ValueError("Agent health identity must match the enrollment receipt.")
        payload = _canonical_health_payload(self._receipt, health)
        signature = base64.b64encode(self._signing_key.sign(payload)).decode("ascii")
        return SignedHealthReport(
            enrollment_id=self._receipt.enrollment_id,
            agent_id=health.agent_id,
            site_id=health.site_id,
            scope_hash=self._receipt.scope_hash,
            healthy=health.healthy,
            mode=health.mode,
            detail=health.detail,
            observed_at=health.observed_at,
            signature=signature,
        )

    def report(self, health: AgentHealth) -> bool:
        """Send a signed health report and return true only for a successful accepted response."""

        response_status = self._transport.post_health(self.build(health).payload())
        return 200 <= response_status < 300


class JsonHttpHealthTransport:
    """Minimal injectable HTTP transport; callers configure endpoint and TLS externally."""

    def __init__(self, endpoint: str, post_json: callable) -> None:
        """Store an HTTPS endpoint and injected network primitive for explicit caller control."""

        if not endpoint.startswith("https://"):
            raise ValueError("Health reporting endpoint must use HTTPS.")
        self._endpoint = endpoint
        self._post_json = post_json

    def post_health(self, payload: dict[str, str | bool]) -> int:
        """Post exactly one JSON record; no automatic retry or side-effect beyond health reporting."""

        return int(self._post_json(self._endpoint, json.dumps(payload, separators=(",", ":")).encode("utf-8")))
