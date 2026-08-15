from __future__ import annotations

from typing import Any

from .common import EnterpriseDomainBase


class EnterpriseServicesProfile(EnterpriseDomainBase):
    """Shared services expected in a corporate network design."""

    def design(self, requirements: dict[str, Any]) -> dict[str, Any]:
        guard = self.guard_domain(requirements)
        if not guard["applicable"]:
            return self.envelope(requirements, {"status": guard["status"]})
        services = {
            "baseline_services": ["dns", "dhcp", "ntp", "identity", "logging", "monitoring", "configuration_backup"],
            "optional_services": ["voip_uc", "nac", "ipam", "load_balancing", "gslb", "wireless_controller"],
            "availability_expectation": "redundant_for_business_critical_services",
            "ownership_metadata_required": True,
            "source_of_truth_required": True,
        }
        self.record_decision("enterprise_services_baseline", services["baseline_services"], "Shared network services support consistent branch, campus, and remote access operations.")
        return self.envelope(requirements, services)
