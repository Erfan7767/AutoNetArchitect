"""Local syslog service configuration designer."""
from __future__ import annotations

from typing import Any

from .service_common import as_list, external_preview, missing, secret_references
from .service_orchestrator import ServiceBase, ServiceDefinition, ServiceConfigArtifact


class SyslogService(ServiceBase):
    """Generate local logging transport and retention intent."""

    definition = ServiceDefinition("syslog", dependencies=("ntp",), scope="local_infrastructure_support", description="Central logging transport baseline.", health_checks=("collector_listening", "transport_authenticated", "retention_available"))

    def generate(self, request: dict[str, Any]) -> ServiceConfigArtifact:
        """Generate explicit syslog destinations and transport policy."""
        blocked = missing(request, ("collectors",))
        if blocked:
            return self.blocked("syslog collectors are not inferable", blocked)
        collectors = as_list(request["collectors"])
        if not collectors:
            return self.blocked("at least one syslog collector is required", ("collectors",))
        refs = secret_references(request, ("tls_secret_refs",))
        preview = external_preview(self, request, "syslog.external_collector")
        if preview is not None:
            return preview
        config = {"collectors": collectors, "transport": request.get("transport", "human_supplied"), "tls": bool(request.get("tls", False)), "tls_secret_references": list(refs), "facility": request.get("facility", "local7"), "retention_days": request.get("retention_days", "human_supplied")}
        return self._artifact("generated", config, decision_ids=request.get("decision_ids", ()), assumption_ids=request.get("assumption_ids", ()), external_integrations=("syslog.external_collector",) if request.get("external_integration") else ())
