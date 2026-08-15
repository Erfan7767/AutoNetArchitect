"""Chaos test for partial device responses."""
from __future__ import annotations

from tests.chaos.chaos_helpers import run_failing_deploy


def test_partial_device_response_does_not_advance_stage():
    def partial_response(_context, _payload):
        return {"state": "partial", "reasons": ["device returned incomplete response"]}

    result = run_failing_deploy(partial_response)
    assert result.success is False
    assert result.status == "blocked"
    assert any("artifact" in reason.lower() or "service" in reason.lower() for reason in result.reasons)
