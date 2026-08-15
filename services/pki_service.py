"""PKI service configuration designer over the existing PKI layer."""
from __future__ import annotations

from typing import Any

from .service_common import external_preview, missing, secret_references
from .service_orchestrator import ServiceBase, ServiceDefinition, ServiceConfigArtifact


class PKIService(ServiceBase):
    """Generate PKI service intent; certificate issuance remains explicit and auditable."""

    definition = ServiceDefinition("pki", dependencies=("ntp", "dns"), scope="local_infrastructure_support", description="Certificate service baseline using the existing PKIManager and SecretManager contracts.", health_checks=("certificate_store_available", "inventory_readable", "renewal_queue_checked"))

    def generate(self, request: dict[str, Any]) -> ServiceConfigArtifact:
        """Generate certificate profile and renewal policy without assuming a CA integration."""
        blocked = missing(request, ("certificate_profile",))
        if blocked:
            return self.blocked("PKI certificate profile is human-supplied", blocked)
        preview = external_preview(self, request, "pki.external_ca")
        if preview is not None:
            return preview
        refs = secret_references(request, ("ca_key_secret_refs",))
        profile = request["certificate_profile"]
        if not isinstance(profile, dict):
            raise ValueError("certificate_profile must be an object")
        required = tuple(field for field in ("common_name", "validity_days", "key_algorithm") if field not in profile)
        if required:
            return self.blocked("PKI certificate profile is incomplete", tuple(f"certificate_profile.{field}" for field in required))
        config = {"certificate_profile": profile, "ca_key_secret_references": list(refs), "renewal_window_days": request.get("renewal_window_days", 30), "revocation_policy": request.get("revocation_policy", "human_supplied"), "issuance_mode": request.get("issuance_mode", "existing_pki_manager")}
        return self._artifact("generated", config, decision_ids=request.get("decision_ids", ()), assumption_ids=request.get("assumption_ids", ()))
