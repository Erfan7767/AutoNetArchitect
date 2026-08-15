from __future__ import annotations

from typing import Any

from .common import EnterpriseDomainBase


class EnterpriseCorporatePack(EnterpriseDomainBase):
    """Entry point that prevents accidental application outside the target sector."""

    def design(self, requirements: dict[str, Any]) -> dict[str, Any]:
        guard = self.guard_domain(requirements)
        if not guard["applicable"]:
            return self.envelope(requirements, {"status": guard["status"]})
        self.record_decision(
            "enterprise_domain_activation",
            "enterprise_corporate",
            "Apply the pack only to corporate enterprise organizations with explicit sector selection.",
            alternatives=["banking_pack", "healthcare_pack", "university_pack"],
            rejection_reasons={
                "other_sectors": "Those sectors require their own domain-specific assumptions and controls.",
            },
        )
        return self.envelope(
            requirements,
            {
                "status": "active",
                "in_scope": [
                    "hq_network",
                    "branch_networks",
                    "campus_networks",
                    "enterprise_segmentation",
                    "branch_wan",
                    "remote_access_baseline",
                    "internet_edge",
                    "shared_network_services",
                ],
                "out_of_scope": [
                    "sector_specific_regulation_not_supplied",
                    "application_architecture",
                    "cloud_internal_network_design",
                    "facility_engineering",
                ],
                "sector_exclusivity": True,
            },
        )
