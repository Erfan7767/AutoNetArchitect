"""AAA service configuration designer."""
from __future__ import annotations

from typing import Any

from .service_common import as_list, external_preview, missing, secret_references
from .service_orchestrator import ServiceBase, ServiceDefinition, ServiceConfigArtifact


class AAAService(ServiceBase):
    """Generate AAA intent without inventing identity servers or credentials."""

    definition = ServiceDefinition("aaa", dependencies=("dns", "ntp"), scope="local_infrastructure_support", description="Administrative authentication and authorization transport baseline.", health_checks=("aaa_server_reachable", "authentication_test", "local_fallback_available"))

    def generate(self, request: dict[str, Any]) -> ServiceConfigArtifact:
        """Generate explicit AAA method and server configuration."""
        blocked = missing(request, ("protocol",))
        if blocked:
            return self.blocked("AAA protocol is human-supplied", blocked)
        protocol = str(request["protocol"]).lower()
        if protocol not in {"radius", "tacacs+", "local_only"}:
            raise ValueError("AAA protocol must be radius, tacacs+, or local_only")
        servers = as_list(request.get("servers"))
        refs = secret_references(request, ("shared_secret_refs",))
        if protocol != "local_only" and not servers:
            return self.blocked("AAA server endpoints are required", ("servers",))
        preview = external_preview(self, request, "aaa.external_identity")
        if preview is not None:
            return preview
        config = {"protocol": protocol, "servers": servers, "shared_secret_references": list(refs), "authentication_order": as_list(request.get("authentication_order")) or ["remote", "local"], "authorization": request.get("authorization", "human_supplied"), "accounting": request.get("accounting", "human_supplied"), "local_fallback": bool(request.get("local_fallback", True))}
        return self._artifact("generated", config, decision_ids=request.get("decision_ids", ()), assumption_ids=request.get("assumption_ids", ()), required_human_inputs=("authorization",) if request.get("authorization") == "human_supplied" else ())
