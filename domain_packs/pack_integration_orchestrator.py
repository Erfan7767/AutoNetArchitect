from __future__ import annotations

from typing import Any

from .cross_pack_governance import CrossPackGovernance
from .domain_pack_context import DomainPackContext
from .domain_pack_selector import DomainPackSelector
from .pack_activation_guard import PackActivationGuard
from .pack_boundary_reporter import PackBoundaryReporter


class PackIntegrationOrchestrator:
    """Tie sector selection into requirements, design, review, and deployment paths."""

    def __init__(self) -> None:
        self.selector = DomainPackSelector()
        self.guard = PackActivationGuard()
        self.governance = CrossPackGovernance()
        self.reporter = PackBoundaryReporter()

    def integrate(self, requirements: dict[str, Any]) -> dict[str, Any]:
        workflow_id = str(requirements.get("workflow_id", "unidentified_workflow"))
        selection = self.selector.select(requirements)
        inference = selection["inference"]
        selected = selection.get("selected_pack")
        active = list(requirements.get("active_packs", [selected] if selected else []))
        context = DomainPackContext(
            workflow_id=workflow_id,
            requested_sector=requirements.get("sector"),
            inferred_sector=inference.get("sector"),
            inference_confidence=float(inference.get("confidence", 0.0)),
            review_required=bool(selection.get("review_required", True)),
            selected_pack=selected,
            active_packs=active,
            source_of_truth=requirements.get("source_of_truth", "requirements_document"),
            general_rules=requirements.get("general_rules", {}),
            sector_rules=requirements.get("sector_rules", {}),
            governance_rules=requirements.get("governance_rules", {}),
            compliance_rules=requirements.get("compliance_rules", {}),
            evidence_ids=list(requirements.get("evidence_ids", [])),
        )
        governance_context = context.trace()
        governance_context["review_completed"] = bool(requirements.get("review_completed", False))
        governance = self.governance.govern(governance_context)
        guard_context = dict(governance_context)
        activation = self.guard.check(guard_context)
        report = self.reporter.report(guard_context, activation)
        return {
            "workflow_id": workflow_id,
            "selection": selection,
            "context": context.trace(),
            "governance": governance,
            "activation": activation,
            "boundary_report": report,
            "paths": {"requirements": "sector_profile_and_general_rules", "design": "selected_pack_with_compatibility_policy", "review": "human_review_and_evidence_gate", "deployment": "activation_guard_required"},
            "status": "ready_for_governed_review" if activation["status"] == "blocked" else "integrated_pending_deployment_gate",
        }
