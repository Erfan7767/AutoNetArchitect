from services.service_orchestrator import HealthState, ServiceOrchestrator, ServiceState


def test_service_orchestrator_orders_dependencies_and_generates_artifacts():
    orchestrator = ServiceOrchestrator()
    order = orchestrator.deployment_order()
    assert order.index("ntp") < order.index("dns") < order.index("dhcp")
    assert order.index("syslog") < order.index("siem")
    artifacts = orchestrator.generate_all({"dns": {"mode": "resolver", "upstreams": ["192.0.2.53"]}})
    by_name = {artifact.service: artifact for artifact in artifacts}
    assert by_name["ntp"].state == ServiceState.BLOCKED_MISSING_HUMAN_DATA.value
    assert by_name["dns"].state == ServiceState.BLOCKED_DEPENDENCY.value


def test_service_orchestrator_health_is_unknown_without_runtime_observation():
    results = ServiceOrchestrator().health_all()
    assert results
    assert all(result.state == HealthState.UNKNOWN.value and result.healthy is None for result in results)
