from services.pki_service import PKIService
from services.service_orchestrator import ServiceState


def test_pki_service_requires_explicit_certificate_profile():
    service = PKIService()
    assert service.generate({}).state == ServiceState.BLOCKED_MISSING_HUMAN_DATA.value
    preview = service.generate({"certificate_profile": {"common_name": "edge", "validity_days": 365, "key_algorithm": "RSA-2048"}, "external_integration": True})
    assert preview.state == ServiceState.PREVIEW_ONLY.value
    artifact = service.generate({"certificate_profile": {"common_name": "edge", "validity_days": 365, "key_algorithm": "RSA-2048"}, "ca_key_secret_refs": ["secret://pki/ca-key"]})
    assert artifact.state == ServiceState.GENERATED.value
