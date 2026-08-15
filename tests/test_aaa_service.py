from services.aaa_service import AAAService
from services.service_orchestrator import ServiceState


def test_aaa_supports_local_only_and_blocks_unconfirmed_external_identity():
    service = AAAService()
    local = service.generate({"protocol": "local_only"})
    assert local.state == ServiceState.GENERATED.value
    preview = service.generate({"protocol": "radius", "servers": ["radius.internal"], "shared_secret_refs": ["secret://aaa/shared"], "external_integration": True})
    assert preview.state == ServiceState.PREVIEW_ONLY.value
