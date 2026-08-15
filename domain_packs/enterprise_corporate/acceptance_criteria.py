from __future__ import annotations

from typing import Any

from .common import EnterpriseDomainBase


class EnterpriseAcceptanceCriteria(EnterpriseDomainBase):
    """Sector-specific acceptance gates for an enterprise network design."""

    def design(self, requirements: dict[str, Any]) -> dict[str, Any]:
        guard = self.guard_domain(requirements)
        if not guard["applicable"]:
            return self.envelope(requirements, {"status": guard["status"]})
        criteria = [
            {"id": "ENT-SEG-001", "criterion": "staff, guest, voice, IoT, management, and quarantine boundaries are explicit", "evidence": "segmentation_verification_report"},
            {"id": "ENT-WAN-001", "criterion": "HQ and critical branches have documented WAN primary and backup behavior", "evidence": "wan_and_failover_design"},
            {"id": "ENT-CAMPUS-001", "criterion": "campus access/distribution/core roles and failure domains are documented", "evidence": "campus_topology_artifact"},
            {"id": "ENT-EDGE-001", "criterion": "internet edge zones, NAT order, remote access, and logging are validated", "evidence": "edge_security_and_nat_artifacts"},
            {"id": "ENT-SVC-001", "criterion": "DNS, DHCP, NTP, identity, monitoring, and logging ownership is assigned", "evidence": "services_profile_and_ownership"},
            {"id": "ENT-OPS-001", "criterion": "management access, backup, telemetry, and rollback evidence exist", "evidence": "operations_and_deployment_records"},
            {"id": "ENT-PHYS-001", "criterion": "field feasibility and power/cooling/rack assumptions are resolved before production", "evidence": "field_and_physical_feasibility"},
            {"id": "ENT-PROOF-001", "criterion": "formal verification status is explicit and production gates consume it", "evidence": "verification_report"},
        ]
        self.record_decision("enterprise_acceptance_criteria", [x["id"] for x in criteria], "Acceptance requires evidence across design, field, operational, security, and verification layers.")
        return self.envelope(requirements, {"criteria": criteria, "minimum_status": "all_applicable_criteria_verified", "production_claim_requires": ["formal_proof_status", "field_feasibility_pass", "evidence_complete"]})
