from __future__ import annotations

from typing import Any

from .common import EnterpriseDomainBase


class EnterpriseBranchPatterns(EnterpriseDomainBase):
    """Branch patterns selected by size, criticality, and WAN availability."""

    def design(self, requirements: dict[str, Any]) -> dict[str, Any]:
        guard = self.guard_domain(requirements)
        if not guard["applicable"]:
            return self.envelope(requirements, {"status": guard["status"]})
        patterns = {
            "small": {"edge": "single_integrated_edge", "wan": "single_or_backup_internet", "local_services": "minimal"},
            "medium": {"edge": "redundant_edge_or_sdwan_pair", "wan": "dual_transport_preferred", "local_services": "local_dhcp_dns_cache_optional"},
            "large": {"edge": "dual_edge_devices", "wan": "dual_provider_or_mpls_plus_internet", "local_services": "survivability_and_local_breakout"},
        }
        size = requirements.get("branch_size", "medium")
        if size not in patterns:
            self.record_assumption("branch_size", size, "Branch size must be validated against endpoint and service counts.")
            size = "medium"
        self.record_decision("enterprise_branch_pattern", size, "Branch pattern is selected from explicit branch scale.")
        return self.envelope(requirements, {"selected": size, "patterns": patterns})
