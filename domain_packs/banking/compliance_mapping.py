from __future__ import annotations

from typing import Any

from .common import BankingDomainBase


class BankingComplianceMapping(BankingDomainBase):
    """Maps supplied banking obligations to network technical controls without certification claims."""

    def design(self, requirements: dict[str, Any]) -> dict[str, Any]:
        guard = self.guard_domain(requirements)
        if not guard["applicable"]:
            return self.envelope(requirements, {"status": guard["status"]})
        obligations = requirements.get("compliance_obligations", [])
        mapping = {
            "access_control": ["mfa", "pam_or_jump_host", "least_privilege", "dual_control"],
            "network_segmentation": ["zone_matrix", "explicit_flows", "formal_verification", "change_approval"],
            "auditability": ["central_logging", "trusted_time", "tamper_evident_storage", "review_evidence"],
            "resilience": ["dual_path", "dr_connectivity", "tested_failover", "approved_runbook"],
            "change_management": ["decision_record", "rollback", "independent_review", "deployment_gate"],
            "third_party_risk": ["circuit_inventory", "provider_assurance", "remote_access_review"],
        }
        self.record_decision("banking_compliance_mapping", mapping, "Technical controls are mapped to supplied obligations; the pack does not certify compliance.")
        status = "requires_authoritative_obligations" if not obligations else "mapped_pending_evidence"
        if not obligations:
            self.record_assumption("compliance_obligations", [], "Exact jurisdictional and regulatory obligations must be supplied by the organization or authoritative knowledge source.")
        return self.envelope(requirements, {"status": status, "obligations": obligations, "control_mapping": mapping, "certification": "not_provided"})
