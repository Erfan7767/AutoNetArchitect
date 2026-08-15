"""SNMP monitoring service configuration designer."""
from __future__ import annotations

from typing import Any

from .service_common import as_list, missing, secret_references
from .service_orchestrator import ServiceBase, ServiceDefinition, ServiceConfigArtifact


class SNMPService(ServiceBase):
    """Generate SNMP monitoring intent without inventing managers or communities."""

    definition = ServiceDefinition("snmp", dependencies=("ntp",), scope="local_infrastructure_support", description="Infrastructure monitoring telemetry baseline.", health_checks=("agent_enabled", "manager_reachable", "poll_response"))

    def generate(self, request: dict[str, Any]) -> ServiceConfigArtifact:
        """Generate explicit SNMP version and manager configuration."""
        blocked = missing(request, ("version", "managers"))
        if blocked:
            return self.blocked("SNMP version and managers are human-supplied", blocked)
        version = str(request["version"]).lower()
        if version not in {"v2c", "v3"}:
            raise ValueError("SNMP version must be v2c or v3")
        managers = as_list(request["managers"])
        if not managers:
            return self.blocked("SNMP manager endpoints are required", ("managers",))
        refs = secret_references(request, ("community_secret_refs", "auth_secret_refs", "privacy_secret_refs"))
        if version == "v2c" and not request.get("community_secret_refs"):
            return self.blocked("SNMP v2c community must remain a secret reference", ("community_secret_refs",))
        if version == "v3" and not request.get("auth_secret_refs"):
            return self.blocked("SNMPv3 authentication secret must remain a secret reference", ("auth_secret_refs",))
        config = {"version": version, "managers": managers, "secret_references": list(refs), "views": as_list(request.get("views")), "traps": as_list(request.get("traps")), "source_interface": request.get("source_interface", "human_supplied")}
        return self._artifact("generated", config, decision_ids=request.get("decision_ids", ()), assumption_ids=request.get("assumption_ids", ()))
