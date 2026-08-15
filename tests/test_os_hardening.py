from services.os_hardening import OSHardeningService
from services.service_orchestrator import ServiceState


def test_os_hardening_requires_platform_and_records_exceptions():
    service = OSHardeningService()
    assert service.generate({}).state == ServiceState.BLOCKED_MISSING_HUMAN_DATA.value
    artifact = service.generate({"platform": "network_os", "exception_register": [{"control": "disable_telnet", "reason": "legacy management dependency"}]})
    assert artifact.state == ServiceState.GENERATED.value
    assert artifact.config["controls"]
    assert artifact.config["exception_register"][0]["control"] == "disable_telnet"
