from services.service_orchestrator import ServiceState
from services.siem_service import SIEMService


def test_siem_requires_event_classes_and_forwarding_collectors():
    service = SIEMService()
    assert service.generate({}).state == ServiceState.BLOCKED_MISSING_HUMAN_DATA.value
    assert service.generate({"event_classes": ["authentication"], "forwarding": True}).state == ServiceState.BLOCKED_MISSING_HUMAN_DATA.value
    artifact = service.generate({"event_classes": ["authentication", "configuration"], "forwarding": True, "collectors": ["siem.local"], "transport_secret_refs": ["secret://siem/transport"]})
    assert artifact.state == ServiceState.GENERATED.value
