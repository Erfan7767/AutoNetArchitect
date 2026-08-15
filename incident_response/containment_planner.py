"""Human-approved containment planning for incidents."""

from __future__ import annotations

from datetime import timedelta
from typing import Any, Mapping, Sequence

from designers.base_designer import Assumption, DecisionRecord

from ._common import make_assumption, make_decision
from .incident_models import ContainmentPlan, IncidentCategory, IncidentSeverity, IncidentPlanStep


class ContainmentPlanner:
    """Suggest reversible, evidence-preserving containment; never execute it."""

    STRATEGIES: dict[IncidentCategory, tuple[tuple[str, str, str, bool], ...]] = {
        IncidentCategory.NETWORK_OUTAGE: (("isolate failed segment", "medium", "confirm alternate path and preserve pre-change state", True), ("route traffic through an explicitly validated alternate path", "high", "verify reachability and blast radius before approval", True)),
        IncidentCategory.SECURITY_INCIDENT: (("isolate the explicitly identified compromised device or VLAN", "high", "preserve logs and forensic evidence before isolation", True), ("block explicitly identified suspicious traffic through governed security change", "high", "security owner must approve and preserve evidence", True)),
        IncidentCategory.HARDWARE_FAILURE: (("fail over to the explicitly identified redundant device or link", "medium", "verify redundancy state and avoid simultaneous pair changes", True), ("isolate the failed hardware from the operational path", "medium", "field and hardware evidence must be retained", True)),
        IncidentCategory.CONFIGURATION_ERROR: (("prepare rollback of the explicitly related change", "high", "backup and rollback artifact must be verified", True), ("apply a temporary documented workaround through change governance", "medium", "workaround must have an explicit expiry and verification", True)),
        IncidentCategory.NETWORK_DEGRADATION: (("advertise or select an explicitly validated alternate path", "high", "route safety and loop checks must pass", True),),
        IncidentCategory.EXTERNAL_DEPENDENCY: (("activate an explicitly documented alternate dependency", "medium", "provider or business owner must confirm availability", True),),
    }

    def __init__(self) -> None:
        """Initialize decision and assumption registries."""
        self.decisions: list[DecisionRecord] = []
        self.assumptions: list[Assumption] = []

    def plan(self, *, incident_id: str, category: IncidentCategory, severity: IncidentSeverity, affected_devices: Sequence[str] = (), affected_services: Sequence[str] = (), related_change_ids: Sequence[str] = (), preserve_evidence: bool = True, backup_reference: str | None = None, explicit_alternate_path: str | None = None) -> ContainmentPlan:
        """Create a non-executing containment plan."""
        if not incident_id:
            raise ValueError("incident_id is required")
        if not preserve_evidence:
            raise ValueError("containment cannot disable evidence preservation")
        templates = list(self.STRATEGIES.get(category, (("hold service state and collect additional evidence", "low", "no safe category-specific action is inferred", True),)))
        if explicit_alternate_path:
            self.assumptions.append(make_assumption(f"{incident_id}:alternate_path", explicit_alternate_path, "alternate path was supplied by a human or validated dependency map", True))
        if not backup_reference and category == IncidentCategory.CONFIGURATION_ERROR:
            self.assumptions.append(make_assumption(f"{incident_id}:backup", "missing", "rollback-related containment remains blocked until backup evidence exists", True))
        steps: list[IncidentPlanStep] = []
        for index, (action, risk, verification, reversible) in enumerate(templates, start=1):
            if severity == IncidentSeverity.P1_CRITICAL and index == 1:
                risk = "high"
            steps.append(IncidentPlanStep(step_id=f"{incident_id}:containment:{index}", action=action, commands=[], risk=risk, requires_approval=True, estimated_time=timedelta(minutes=15 if risk == "low" else 30), verification=verification, reversible=reversible, backup_required=category == IncidentCategory.CONFIGURATION_ERROR, evidence_preservation_required=True))
        strategy = "preserve_evidence_and_limit_blast_radius"
        decision = make_decision("ContainmentPlanner", f"{incident_id}:containment", strategy, "all containment actions remain advisory and require explicit human approval", ["preserve_evidence_and_limit_blast_radius", "automatic_containment"], {"preserve_evidence_and_limit_blast_radius": "selected by V1 safety policy", "automatic_containment": "rejected"})
        self.decisions.append(decision)
        return ContainmentPlan(plan_id=f"{incident_id}:containment-plan", strategy=strategy, steps=steps, preserves_evidence=True, wider_outage_risk="requires human impact review", execution_allowed=False, approval_reference=None, assumptions=[item.key for item in self.assumptions])
