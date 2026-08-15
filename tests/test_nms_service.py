from services.nms_service import NMSService
from services.service_orchestrator import ServiceState


def test_nms_requires_targets_and_external_nms_is_preview_only():
    service = NMSService()
    assert service.generate({}).state == ServiceState.BLOCKED_MISSING_HUMAN_DATA.value
    preview = service.generate({"targets": ["switch-1"], "external_integration": True})
    assert preview.state == ServiceState.PREVIEW_ONLY.value
    artifact = service.generate({"targets": ["switch-1"], "poll_interval_seconds": 60, "metrics": ["interface_errors"]})
    assert artifact.state == ServiceState.GENERATED.value
