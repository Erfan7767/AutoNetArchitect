"""SIEM integration service configuration designer."""
from __future__ import annotations

from typing import Any

from .service_common import as_list, external_preview, missing, secret_references
from .service_orchestrator import ServiceBase, ServiceDefinition, ServiceConfigArtifact


class SIEMService(ServiceBase):
    """Generate SIEM forwarding intent without claiming an enterprise SIEM exists."""

    definition = ServiceDefinition("siem", dependencies=("syslog", "aaa"), scope="local_infrastructure_support", description="Security event forwarding baseline.", health_checks=("event_queue_available", "collector_reachable", "delivery_acknowledged"))

    def generate(self, request: dict[str, Any]) -> ServiceConfigArtifact:
        """Generate explicit event classes and collector configuration."""
        blocked = missing(request, ("event_classes",))
        if blocked:
            return self.blocked("SIEM event classes are human-supplied", blocked)
        event_classes = as_list(request["event_classes"])
        refs = secret_references(request, ("transport_secret_refs",))
        preview = external_preview(self, request, "siem.external_platform")
        if preview is not None:
            return preview
        collectors = as_list(request.get("collectors"))
        forwarding_enabled = bool(request.get("forwarding_enabled", request.get("forwarding", False)))
        if forwarding_enabled and not collectors:
            return self.blocked("SIEM collectors are required when forwarding is enabled", ("collectors",))
        config = {"event_classes": event_classes, "collectors": collectors, "forwarding_enabled": forwarding_enabled, "transport": request.get("transport", "human_supplied"), "transport_secret_references": list(refs), "local_queue_retention": request.get("local_queue_retention", "human_supplied")}
        return self._artifact("generated", config, decision_ids=request.get("decision_ids", ()), assumption_ids=request.get("assumption_ids", ()), external_integrations=("siem.external_platform",) if request.get("external_integration") else ())
