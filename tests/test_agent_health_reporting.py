"""Tests for signing and transporting secret-free site-agent health reports."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from site_agent.enrollment import EnrollmentReceipt
from site_agent.health_reporting import ControlPlaneHealthReporter
from site_agent.models import AgentHealth


class CapturingTransport:
    """Capture a report payload and return a configured response status."""

    def __init__(self, response_status: int) -> None:
        """Set the response returned to the health reporter."""

        self.response_status = response_status
        self.payloads: list[dict[str, str | bool]] = []

    def post_health(self, payload: dict[str, str | bool]) -> int:
        """Capture one payload without making a network connection in the test."""

        self.payloads.append(payload)
        return self.response_status


def receipt() -> EnrollmentReceipt:
    """Create an active secret-free enrollment receipt."""

    return EnrollmentReceipt(
        enrollment_id="enrollment-health-report-001",
        agent_id="agent-health-001",
        site_id="site-health-001",
        scope_hash="a" * 64,
        agent_fingerprint="b" * 64,
        control_plane_fingerprint="c" * 64,
        enrolled_at=datetime.now(timezone.utc),
        expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
    )


def health() -> AgentHealth:
    """Create one matching read-only agent health record."""

    return AgentHealth(agent_id="agent-health-001", site_id="site-health-001", healthy=True, detail="Mutual enrollment remains active for the acknowledged scope.")


def test_health_reporter_signs_and_transports_a_secret_free_report() -> None:
    """A successful status acknowledges only the signed health report, never a device action."""

    transport = CapturingTransport(202)
    reporter = ControlPlaneHealthReporter(receipt(), Ed25519PrivateKey.generate(), transport)

    assert reporter.report(health())
    payload = transport.payloads[0]
    assert payload["mode"] == "read_only"
    assert payload["signature"]
    assert "credential" not in str(payload).lower()
    assert "private" not in str(payload).lower()


def test_health_reporter_returns_false_for_control_plane_rejection() -> None:
    """A rejected report does not retry, discover, or alter any device state."""

    transport = CapturingTransport(403)
    reporter = ControlPlaneHealthReporter(receipt(), Ed25519PrivateKey.generate(), transport)

    assert not reporter.report(health())
    assert len(transport.payloads) == 1
