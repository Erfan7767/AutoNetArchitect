"""Local DHCP service configuration designer."""
from __future__ import annotations

from typing import Any

from .service_common import as_list, missing
from .service_orchestrator import ServiceBase, ServiceDefinition, ServiceConfigArtifact


class DHCPService(ServiceBase):
    """Generate local DHCP scopes without inventing address pools."""

    definition = ServiceDefinition("dhcp", dependencies=("dns",), scope="local_infrastructure_support", description="Address allocation baseline for known network scopes.", health_checks=("service_listening", "scope_available", "lease_store_writable"))

    def generate(self, request: dict[str, Any]) -> ServiceConfigArtifact:
        """Generate explicit DHCP scopes."""
        blocked = missing(request, ("scopes",))
        if blocked:
            return self.blocked("DHCP scopes are human-supplied network data", blocked)
        scopes = as_list(request["scopes"])
        if not scopes or not all(isinstance(scope, dict) for scope in scopes):
            raise ValueError("DHCP scopes must be a non-empty list of objects")
        for index, scope in enumerate(scopes):
            required = [field for field in ("name", "network", "range_start", "range_end", "gateway") if field not in scope]
            if required:
                return self.blocked(f"DHCP scope {index} is incomplete", tuple(f"scopes[{index}].{field}" for field in required))
        config = {"scopes": scopes, "default_dns_servers": as_list(request.get("default_dns_servers")), "lease_seconds": request.get("lease_seconds", "human_supplied"), "reservations": as_list(request.get("reservations"))}
        return self._artifact("generated", config, decision_ids=request.get("decision_ids", ()), assumption_ids=request.get("assumption_ids", ()))
