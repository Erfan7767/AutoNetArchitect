from services.dhcp_service import DHCPService
from services.service_orchestrator import ServiceState


def test_dhcp_requires_explicit_complete_scopes():
    service = DHCPService()
    assert service.generate({}).state == ServiceState.BLOCKED_MISSING_HUMAN_DATA.value
    artifact = service.generate({"scopes": [{"name": "users", "network": "192.0.2.0/24", "range_start": "192.0.2.50", "range_end": "192.0.2.200", "gateway": "192.0.2.1"}]})
    assert artifact.state == ServiceState.GENERATED.value
    assert artifact.config["scopes"][0]["name"] == "users"
