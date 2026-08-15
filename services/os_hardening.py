"""Operating-system hardening baseline service."""
from __future__ import annotations

from typing import Any

from .service_common import as_list, missing
from .service_orchestrator import ServiceBase, ServiceDefinition, ServiceConfigArtifact


class OSHardeningService(ServiceBase):
    """Generate platform-neutral hardening intent without claiming compliance certification."""

    definition = ServiceDefinition("os_hardening", dependencies=("ntp", "aaa", "syslog"), scope="local_infrastructure_support", description="Platform-neutral baseline controls for infrastructure hosts and appliances.", health_checks=("unsupported_services_reviewed", "admin_access_restricted", "logging_enabled", "time_sync_enabled"))

    DEFAULT_CONTROLS = ("disable_unused_services", "restrict_management_sources", "enforce_unique_admin_identity", "use_ssh_or_equivalent_secure_transport", "enable_time_sync", "enable_audited_logging", "apply_vendor_supported_patches")

    def generate(self, request: dict[str, Any]) -> ServiceConfigArtifact:
        """Generate hardening controls and explicit exception register."""
        blocked = missing(request, ("platform",))
        if blocked:
            return self.blocked("OS platform/version is human-supplied", blocked)
        controls = as_list(request.get("controls")) or list(self.DEFAULT_CONTROLS)
        exceptions = as_list(request.get("exception_register", request.get("exceptions")))
        if any(not isinstance(item, dict) or "control" not in item or "reason" not in item for item in exceptions):
            return self.blocked("hardening exceptions require control and reason", ("exception_register.control", "exception_register.reason"))
        config = {"platform": request["platform"], "os_version": request.get("os_version", "human_supplied"), "controls": controls, "exceptions": exceptions, "exception_register": exceptions, "baseline_source": request.get("baseline_source", "project_baseline"), "compliance_claim": "not_claimed"}
        return self._artifact("generated", config, decision_ids=request.get("decision_ids", ()), assumption_ids=request.get("assumption_ids", ()))
