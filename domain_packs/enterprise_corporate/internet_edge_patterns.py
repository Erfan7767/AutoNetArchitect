from __future__ import annotations

from typing import Any

from .common import EnterpriseDomainBase


class EnterpriseInternetEdgePatterns(EnterpriseDomainBase):
    """Internet edge baseline for enterprise ingress, egress, and remote access."""

    def design(self, requirements: dict[str, Any]) -> dict[str, Any]:
        guard = self.guard_domain(requirements)
        if not guard["applicable"]:
            return self.envelope(requirements, {"status": guard["status"]})
        edge = {
            "default": "dual_firewall_or_firewall_cluster",
            "transit": "separate_inside_dmz_outside_zones",
            "wan": "dual_isp_when_business_critical",
            "routing": "controlled_default_and_prefix_policy",
            "nat": "documented_ordered_rules_with_logging",
            "remote_access": "vpn_or_zero_trust_gateway_with_mfa",
            "ddos": "provider_or_edge_service_required_when_exposure_demands_it",
        }
        self.record_decision("enterprise_internet_edge", edge["default"], "Internet edge uses explicit trust zones and resilient termination for critical enterprises.")
        return self.envelope(requirements, edge)
