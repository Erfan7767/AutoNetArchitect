"""Chaos test for a mid-deployment connection disconnect."""
from __future__ import annotations

from tests.chaos.chaos_helpers import run_failing_deploy


def test_mid_deploy_disconnect_is_bounded_and_non_successful():
    def disconnect(_context, _payload):
        raise ConnectionError("simulated transport disconnect")

    result = run_failing_deploy(disconnect)
    assert result.success is False
    assert result.status == "blocked"
    assert any("failed" in reason.lower() for reason in result.reasons)
    assert all("retry" not in reason.lower() for reason in result.reasons)
