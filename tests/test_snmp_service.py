from services.service_orchestrator import ServiceState
from services.snmp_service import SNMPService


def test_snmp_requires_version_managers_and_secret_references():
    service = SNMPService()
    assert service.generate({}).state == ServiceState.BLOCKED_MISSING_HUMAN_DATA.value
    v3 = service.generate({"version": "v3", "managers": ["nms.local"], "auth_secret_refs": ["secret://snmp/auth"]})
    assert v3.state == ServiceState.GENERATED.value
    try:
        service.generate({"version": "v2c", "managers": ["nms.local"], "community_secret_refs": ["public" ]})
    except ValueError:
        return
    raise AssertionError("SNMP community must be a secret:// reference")
