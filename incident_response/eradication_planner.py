"""Root-cause eradication planning with change governance boundaries."""

from __future__ import annotations

from datetime import timedelta
from typing import Sequence

from designers.base_designer import Assumption, DecisionRecord

from ._common import make_assumption, make_decision
from .incident_models import EradicationPlan, IncidentCategory, IncidentPlanStep


class EradicationPlanner:
    """Prepare governed eradication proposals after diagnosis."""

    def __init__(self) -> None:
        """Initialize decision and assumption registries."""
        self.decisions: list[DecisionRecord] = []
        self.assumptions: list[Assumption] = []

    def plan(self, *, incident_id: str, category: IncidentCategory, root_cause: str, root_cause_confidence: float, change_request_reference: str | None = None, vendor_case_reference: str | None = None, firmware_reference: str | None = None, evidence_ids: Sequence[str] = ()) -> EradicationPlan:
        """Return a non-executing eradication plan."""
        if not root_cause:
            self.assumptions.append(make_assumption(f"{incident_id}:root_cause", "not_supplied", "eradication cannot select a fix without a root-cause statement", True))
        if root_cause_confidence < 0.3:
            remediation_type = "investigation_required"
            action = "collect additional evidence before selecting an eradication action"
            risk = "low"
            self.assumptions.append(make_assumption(f"{incident_id}:eradication_confidence", root_cause_confidence, "low RCA confidence blocks a specific eradication fix", True))
        elif category == IncidentCategory.CONFIGURATION_ERROR:
            remediation_type = "configuration_change"
            action = "prepare a corrective configuration change through Change Management"
            risk = "high"
        elif category == IncidentCategory.HARDWARE_FAILURE:
            remediation_type = "hardware_replacement"
            action = "coordinate field replacement and validate redundancy before physical work"
            risk = "high"
        elif category == IncidentCategory.SOFTWARE_BUG:
            remediation_type = "vendor_engagement_and_upgrade_plan"
            action = "validate vendor advisory, workaround, and supported fix version"
            risk = "high"
        elif category == IncidentCategory.SECURITY_INCIDENT:
            remediation_type = "security_remediation_and_hardening"
            action = "coordinate security remediation and evidence preservation"
            risk = "critical"
        elif category == IncidentCategory.CAPACITY_EXCEEDED:
            remediation_type = "capacity_upgrade"
            action = "prepare a capacity change based on measured demand and approved design"
            risk = "medium"
        elif category == IncidentCategory.ENVIRONMENTAL:
            remediation_type = "environmental_correction"
            action = "coordinate power, cooling, or facility correction with field owners"
            risk = "high"
        else:
            remediation_type = "governed_corrective_change"
            action = "prepare a governed corrective change after evidence review"
            risk = "medium"
        if category == IncidentCategory.CONFIGURATION_ERROR and not change_request_reference:
            self.assumptions.append(make_assumption(f"{incident_id}:change_request", "not_supplied", "configuration eradication cannot be considered approved without a change reference", True))
        if category == IncidentCategory.SOFTWARE_BUG and not vendor_case_reference:
            self.assumptions.append(make_assumption(f"{incident_id}:vendor_case", "not_supplied", "software bug eradication requires vendor engagement evidence", True))
        if category == IncidentCategory.SOFTWARE_BUG and not firmware_reference:
            self.assumptions.append(make_assumption(f"{incident_id}:firmware_reference", "not_supplied", "firmware path is not fabricated when exact support evidence is absent", True))
        step = IncidentPlanStep(step_id=f"{incident_id}:eradication:1", action=action, commands=[], risk=risk, requires_approval=True, estimated_time=timedelta(minutes=30), verification="verify root cause no longer manifests and preserve post-change evidence", reversible=category in {IncidentCategory.CONFIGURATION_ERROR, IncidentCategory.SOFTWARE_BUG}, backup_required=True, evidence_preservation_required=category == IncidentCategory.SECURITY_INCIDENT)
        decision = make_decision("EradicationPlanner", f"{incident_id}:eradication", remediation_type, "map category and RCA confidence to a governed plan without execution", ["governed_plan", "automatic_remediation"], {"governed_plan": "selected", "automatic_remediation": "rejected in V1"})
        self.decisions.append(decision)
        return EradicationPlan(plan_id=f"{incident_id}:eradication-plan", root_cause=root_cause or "unknown", remediation_type=remediation_type, steps=[step], change_request_reference=change_request_reference, vendor_case_reference=vendor_case_reference, firmware_reference=firmware_reference, execution_allowed=False, assumptions=[item.key for item in self.assumptions])
