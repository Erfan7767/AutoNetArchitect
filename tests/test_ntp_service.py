from services.ntp_service import NTPService
from services.service_orchestrator import ServiceState


def test_ntp_requires_explicit_servers_and_generates_config():
    service = NTPService()
    assert service.generate({}).state == ServiceState.BLOCKED_MISSING_HUMAN_DATA.value
    artifact = service.generate({"servers": ["ntp.internal"], "authentication_secret_refs": ["secret://ntp/key"], "decision_ids": ["d1"]})
    assert artifact.state == ServiceState.GENERATED.value
    assert artifact.config["servers"] == ["ntp.internal"]
    assert artifact.config["authentication"]["secret_references"] == ["secret://ntp/key"]
