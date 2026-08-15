from services.dns_service import DNSService
from services.service_orchestrator import ServiceState


def test_dns_requires_mode_specific_inputs():
    service = DNSService()
    assert service.generate({"mode": "resolver"}).state == ServiceState.BLOCKED_MISSING_HUMAN_DATA.value
    resolver = service.generate({"mode": "resolver", "upstreams": ["192.0.2.53"]})
    assert resolver.state == ServiceState.GENERATED.value
    authoritative = service.generate({"mode": "authoritative", "zones": [{"name": "example.internal"}]})
    assert authoritative.state == ServiceState.GENERATED.value
