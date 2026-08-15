"""Chaos tests for bootstrap permission and production-boundary failures."""
from __future__ import annotations

from bootstrap.bootstrap_orchestrator import BootstrapOrchestrator
from bootstrap.vendor_workflows.common import BootstrapRequest, BootstrapStatus


def test_preview_only_bootstrap_is_not_production_deployable():
    orchestrator = BootstrapOrchestrator(preview_only_vendors=("cisco",))
    request = BootstrapRequest(device_id="BOOT-001", vendor="cisco", platform="ios-xe", endpoint_reference="oob://boot", credential_reference="secret://cred", console_available=True)
    artifact = orchestrator.build(request)
    assert artifact.status == BootstrapStatus.PREVIEW_ONLY.value
    assert artifact.production_deployable is False
    assert artifact.remote_destructive_allowed is False


def test_remote_destructive_bootstrap_is_blocked_by_policy():
    orchestrator = BootstrapOrchestrator()
    request = BootstrapRequest(device_id="BOOT-002", vendor="aruba", platform="aoscx", endpoint_reference="oob://boot", credential_reference="secret://cred", console_available=True, remote_destructive=True)
    artifact = orchestrator.build(request)
    assert artifact.status == BootstrapStatus.BLOCKED_REMOTE_DESTRUCTIVE.value
    assert artifact.production_deployable is False
    assert any("blocked" in text.lower() or "destructive" in text.lower() for text in artifact.assumptions + artifact.required_human_inputs)
