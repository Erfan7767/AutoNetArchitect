from __future__ import annotations

from typing import Any

from .common import BankingDomainBase


class BankingEquipmentPreferences(BankingDomainBase):
    """Strict equipment selection preferences without asserting vendor compliance."""

    def design(self, requirements: dict[str, Any]) -> dict[str, Any]:
        guard = self.guard_domain(requirements)
        if not guard["applicable"]:
            return self.envelope(requirements, {"status": guard["status"]})
        preferences = {
            "selection_principles": [
                "documented_security_lifecycle",
                "long_term_support_and_security_fix_process",
                "redundant_control_plane_or_pairing",
                "hardware_rooted_or_cryptographic_identity_when_supported",
                "centralized_audit_and_telemetry",
                "role_based_administration",
                "validated_interoperability_for_atm_and_payment_paths",
            ],
            "evidence_required": ["vendor_support_statement", "capability_evidence", "lifecycle_dates", "security_advisory_process", "lab_validation"],
            "selection_status_without_evidence": "blocked",
            "vendor_neutral": True,
        }
        self.record_decision("banking_equipment_preferences", preferences["selection_status_without_evidence"], "No banking equipment recommendation is production-eligible without capability, lifecycle, and validation evidence.")
        return self.envelope(requirements, preferences)
