"""NMS service configuration designer."""
from __future__ import annotations

from typing import Any

from .service_common import as_list, external_preview, missing
from .service_orchestrator import ServiceBase, ServiceDefinition, ServiceConfigArtifact


class NMSService(ServiceBase):
    """Generate local monitoring inventory and polling intent without inventing an NMS."""

    definition = ServiceDefinition("nms", dependencies=("snmp", "syslog"), scope="local_infrastructure_support", description="Infrastructure inventory and monitoring baseline.", health_checks=("inventory_loaded", "poll_schedule_active", "alert_sink_available"))

    def generate(self, request: dict[str, Any]) -> ServiceConfigArtifact:
        """Generate explicit targets and polling policy."""
        blocked = missing(request, ("targets",))
        if blocked:
            return self.blocked("NMS targets are human-supplied", blocked)
        targets = as_list(request["targets"])
        if not targets:
            return self.blocked("NMS requires at least one explicit target", ("targets",))
        preview = external_preview(self, request, "nms.external_platform")
        if preview is not None:
            return preview
        config = {"targets": targets, "poll_interval_seconds": request.get("poll_interval_seconds", "human_supplied"), "metrics": as_list(request.get("metrics")), "alert_rules": as_list(request.get("alert_rules")), "local_inventory": bool(request.get("local_inventory", True))}
        return self._artifact("generated", config, decision_ids=request.get("decision_ids", ()), assumption_ids=request.get("assumption_ids", ()), external_integrations=("nms.external_platform",) if request.get("external_integration") else ())
