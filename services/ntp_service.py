"""Local NTP service configuration designer."""
from __future__ import annotations

from typing import Any

from .service_common import external_preview, missing, secret_references
from .service_orchestrator import ServiceBase, ServiceDefinition, ServiceConfigArtifact


class NTPService(ServiceBase):
    """Generate a local infrastructure NTP configuration without inventing servers."""

    definition = ServiceDefinition("ntp", scope="local_infrastructure_support", description="Time synchronization baseline for infrastructure devices.", health_checks=("clock_source_reachable", "offset_within_policy"))

    def generate(self, request: dict[str, Any]) -> ServiceConfigArtifact:
        """Generate NTP peers and policy from human/design inputs."""
        blocked = missing(request, ("servers",))
        if blocked:
            return self.blocked("NTP upstreams are not inferable", blocked)
        refs = secret_references(request, ("authentication_secret_refs",))
        preview = external_preview(self, request, "ntp.external_integration")
        if preview is not None:
            return preview
        servers = request["servers"]
        if not isinstance(servers, list) or not all(isinstance(server, str) and server for server in servers):
            raise ValueError("NTP servers must be a non-empty list of explicit names or addresses")
        config = {"servers": servers, "authentication": {"secret_references": list(refs)}, "iburst": bool(request.get("iburst", True)), "stratum_policy": request.get("stratum_policy", "human_supplied")}
        return self._artifact("generated", config, decision_ids=request.get("decision_ids", ()), assumption_ids=request.get("assumption_ids", ()))
