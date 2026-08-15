from services.service_orchestrator import ServiceState
from services.syslog_service import SyslogService


def test_syslog_requires_collectors_and_does_not_assume_external_collector():
    service = SyslogService()
    assert service.generate({}).state == ServiceState.BLOCKED_MISSING_HUMAN_DATA.value
    preview = service.generate({"collectors": ["log.local"], "external_integration": True})
    assert preview.state == ServiceState.PREVIEW_ONLY.value
    generated = service.generate({"collectors": ["log.local"], "tls": True, "tls_secret_refs": ["secret://syslog/tls"]})
    assert generated.state == ServiceState.GENERATED.value
