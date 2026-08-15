"""Local DNS service configuration designer."""
from __future__ import annotations

from typing import Any

from .service_common import as_list, external_preview, missing, secret_references
from .service_orchestrator import ServiceBase, ServiceDefinition, ServiceConfigArtifact


class DNSService(ServiceBase):
    """Generate local DNS service intent without assuming enterprise resolvers."""

    definition = ServiceDefinition("dns", dependencies=("ntp",), scope="local_infrastructure_support", description="Resolver and optional local zone baseline.", health_checks=("resolver_listening", "zones_loaded", "upstream_reachable"))

    def generate(self, request: dict[str, Any]) -> ServiceConfigArtifact:
        """Generate explicit resolver and zone configuration."""
        blocked = missing(request, ("mode",))
        if blocked:
            return self.blocked("DNS mode is a human/design input", blocked)
        preview = external_preview(self, request, "dns.external_integration")
        if preview is not None:
            return preview
        mode = str(request["mode"]).lower()
        if mode not in {"resolver", "authoritative", "combined"}:
            raise ValueError("DNS mode must be resolver, authoritative, or combined")
        zones = as_list(request.get("zones"))
        upstreams = as_list(request.get("upstreams"))
        refs = secret_references(request, ("tsig_secret_refs",))
        if mode in {"resolver", "combined"} and not upstreams:
            return self.blocked("resolver upstreams are not inferable", ("upstreams",))
        if mode in {"authoritative", "combined"} and not zones:
            return self.blocked("authoritative zones are not inferable", ("zones",))
        config = {"mode": mode, "zones": zones, "upstreams": upstreams, "listen_addresses": as_list(request.get("listen_addresses")), "tsig_secret_references": list(refs), "dnssec": request.get("dnssec", "human_supplied")}
        return self._artifact("generated", config, decision_ids=request.get("decision_ids", ()), assumption_ids=request.get("assumption_ids", ()))
