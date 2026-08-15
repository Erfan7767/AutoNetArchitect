"""Safe remediation advice for troubleshooting findings."""

from __future__ import annotations

from typing import Any

from designers.base_designer import Assumption, DecisionRecord

from .models import RemediationPlan, RemediationStep, RootCauseAnalysis


class RemediationAdvisor:
    """Turn RCA into governed advice rather than automatic change execution."""

    def __init__(self) -> None:
        """Initialize decision and assumption registries."""
        self.decisions: list[DecisionRecord] = []
        self.assumptions: list[Assumption] = []

    def advise(self, diagnostic_id: str, rca: RootCauseAnalysis, *, change_management_reference: str | None = None) -> RemediationPlan:
        """Create ordered, non-executing remediation steps from an RCA."""
        root = rca.root_cause
        if rca.root_cause_classification.value == "unknown" or rca.root_cause_confidence < 0.3:
            self.assumptions.append(Assumption(f"remediation:{diagnostic_id}", "investigation_required", "root cause confidence is too low for a specific fix", True))
            step = RemediationStep(step_id=f"{diagnostic_id}:investigate", description="collect the missing evidence and repeat bounded diagnosis", commands=[], risk_level="low", requires_change_request=False, requires_maintenance_window=False, estimated_fix_time="unknown", verification_after_fix=["do not change production state while cause remains inconclusive"], remediation_type="immediate_fix", safety_warnings=["diagnosis remains inconclusive"], read_only_preview=True)
            plan = RemediationPlan(plan_id=f"{diagnostic_id}:remediation", root_cause=root, steps=[step], plan_type="investigation", execution_allowed=False, safety_warnings=["no production remediation is recommended below 0.3 RCA confidence"], change_management_reference=change_management_reference, assumptions=[item.key for item in self.assumptions])
        else:
            classification = rca.root_cause_classification.value
            if classification == "hardware_failure":
                remediation_type, description = "hardware_replacement", "validate hardware, optics, power, and field evidence before replacement"
            elif classification == "software_bug":
                remediation_type, description = "vendor_engagement", "open a vendor support case and validate fixed-version scope"
            elif classification == "security_incident":
                remediation_type, description = "planned_fix", "coordinate with security governance before containment or policy change"
            elif classification == "design_flaw":
                remediation_type, description = "design_change", "review the design and create a governed change before implementation"
            else:
                remediation_type, description = "planned_fix", "prepare a validated configuration or operational change through change management"
            warnings = ["backup and rollback evidence must be verified before production execution", "post-change verification must be defined", "no command is executed by the troubleshooting engine"]
            step = RemediationStep(step_id=f"{diagnostic_id}:planned-fix", description=description, commands=[], risk_level="high" if rca.root_cause_confidence >= 0.8 else "medium", requires_change_request=True, requires_maintenance_window=True, estimated_fix_time="requires human estimate", verification_after_fix=["validate expected state after the change"], remediation_type=remediation_type, safety_warnings=warnings, read_only_preview=True)
            plan = RemediationPlan(plan_id=f"{diagnostic_id}:remediation", root_cause=root, steps=[step], plan_type=remediation_type, execution_allowed=False, safety_warnings=warnings, change_management_reference=change_management_reference, assumptions=[item.key for item in self.assumptions])
        self.decisions.append(DecisionRecord("RemediationAdvisor", f"remediation:{diagnostic_id}", plan.plan_type, "recommend governed remediation without automatic execution", ["advisory_only", "automatic_execution"], {"advisory_only": "selected by V1 safety policy", "automatic_execution": "rejected"}))
        return plan
