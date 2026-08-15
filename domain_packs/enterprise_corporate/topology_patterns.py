from __future__ import annotations

from typing import Any

from .common import EnterpriseDomainBase


class EnterpriseTopologyPatterns(EnterpriseDomainBase):
    """HQ and branch topology patterns for corporate networks."""

    def design(self, requirements: dict[str, Any]) -> dict[str, Any]:
        guard = self.guard_domain(requirements)
        if not guard["applicable"]:
            return self.envelope(requirements, {"status": guard["status"]})
        patterns = {
            "hq": {
                "default": "redundant_campus_or_enterprise_core",
                "alternatives": ["collapsed_core_for_small_hq", "spine_leaf_for_data_center_adjacent_hq"],
                "failure_domains": ["device", "power_feed", "uplink", "building"],
            },
            "branch": {
                "default": "routed_access_with_dual_wan_when_critical",
                "alternatives": ["single_router_small_branch", "sdwan_edge_branch"],
                "failure_domains": ["edge_device", "carrier", "last_mile"],
            },
        }
        self.record_decision("enterprise_topology_pattern", patterns["hq"]["default"], "HQ and branch patterns are selected by scale and criticality.")
        return self.envelope(requirements, patterns)
