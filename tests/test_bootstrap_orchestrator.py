from bootstrap import BootstrapOrchestrator, BootstrapRequest, BootstrapStatus


def _request(vendor="cisco"):
    return BootstrapRequest("edge-1", vendor, "ios_xe", endpoint_reference="human://oob/edge-1", credential_reference="secret://bootstrap/edge-1", console_available=True, validated_command_evidence_ids=("cmd-e1",), evidence_ids=("asset-e1",))


def test_bootstrap_orchestrator_selects_supported_workflow_without_production_authority():
    orchestrator = BootstrapOrchestrator()
    artifact = orchestrator.build(_request())
    assert artifact.status == BootstrapStatus.READY_FOR_REVIEW.value
    assert artifact.production_deployable is False
    assert artifact.remote_destructive_allowed is False
    assert artifact.vendor == "cisco"
    assert "secret://bootstrap/edge-1" in artifact.secret_references


def test_bootstrap_orchestrator_blocks_unknown_and_preview_vendors_and_remote_destructive():
    orchestrator = BootstrapOrchestrator(preview_only_vendors=("unknown-preview",))
    unknown = orchestrator.build(_request("not-supported"))
    assert unknown.status == BootstrapStatus.BLOCKED_UNSUPPORTED_VENDOR.value
    preview = orchestrator.build(_request("unknown-preview"))
    assert preview.status == BootstrapStatus.PREVIEW_ONLY.value
    blocked = orchestrator.build(BootstrapRequest("edge-1", "cisco", "ios_xe", endpoint_reference="human://oob/edge-1", console_available=True, remote_destructive=True))
    assert blocked.status == BootstrapStatus.BLOCKED_REMOTE_DESTRUCTIVE.value
