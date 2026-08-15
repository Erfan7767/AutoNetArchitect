"""Final human review pack builder."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Iterable

from governance import SignoffEvaluation
from pydantic import BaseModel, ConfigDict, Field

from designers.base_designer import BaseDesigner
from expert_override import OverrideApplication

from .no_go_policy import NoGoBlocker, NoGoEvaluation, NoGoOutcome
from .readiness_gate import ReadinessAssessment


class FinalReviewPack(BaseModel):
    """Complete, traceable package for final human approval."""

    model_config = ConfigDict(extra="forbid")

    pack_id: str
    project_id: str
    generated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    requirements: dict[str, Any] = Field(default_factory=dict)
    scope_assessment: dict[str, Any] = Field(default_factory=dict)
    evidence_summary: dict[str, Any] = Field(default_factory=dict)
    design_summary: dict[str, Any] = Field(default_factory=dict)
    equipment_bom: dict[str, Any] = Field(default_factory=dict)
    config_artifacts: dict[str, Any] = Field(default_factory=dict)
    readiness_assessment: dict[str, Any] = Field(default_factory=dict)
    governance_signoff: dict[str, Any] = Field(default_factory=dict)
    no_go_evaluation: dict[str, Any] = Field(default_factory=dict)
    blockers: tuple[dict[str, Any], ...] = ()
    overrides: tuple[dict[str, Any], ...] = ()
    missing_items: tuple[str, ...] = ()
    final_approval_allowed: bool = False
    sot_basis: dict[str, str] = Field(default_factory=dict)
    evidence_ids: tuple[str, ...] = ()
    disclaimer_en: str = "Final approval remains the responsibility of the accountable human engineer and authorized organization."
    disclaimer_ar: str = "يبقى الاعتماد النهائي مسؤولية المهندس البشري المسؤول والجهة المخولة تنظيمياً."


class FinalReviewPackBuilder(BaseDesigner):
    """Build a final review pack without inventing absent artifacts."""

    def __init__(self) -> None:
        """Initialize pack builder."""
        super().__init__("FinalReviewPackBuilder")
        self.record_decision("final_review_pack_policy", "missing_items_explicit", "the final pack exposes missing inputs and unresolved controls instead of filling them with assumptions")

    def build(self, *, project_id: str, requirements: dict[str, Any] | None = None, scope_assessment: dict[str, Any] | None = None, evidence_summary: dict[str, Any] | None = None, design_summary: dict[str, Any] | None = None, equipment_bom: dict[str, Any] | None = None, config_artifacts: dict[str, Any] | None = None, readiness_assessment: ReadinessAssessment | None = None, governance_signoff: SignoffEvaluation | None = None, no_go_evaluation: NoGoEvaluation | None = None, blockers: Iterable[NoGoBlocker] = (), overrides: Iterable[OverrideApplication] = (), sot_basis: dict[str, str] | None = None, evidence_ids: Iterable[str] = (), pack_id: str | None = None) -> FinalReviewPack:
        """Create a pack that remains incomplete when required sections are absent."""
        missing: list[str] = []
        sections = {"requirements": requirements, "scope_assessment": scope_assessment, "evidence_summary": evidence_summary, "design_summary": design_summary, "equipment_bom": equipment_bom, "config_artifacts": config_artifacts}
        for name, value in sections.items():
            if not value:
                missing.append(name)
        if readiness_assessment is None:
            missing.append("readiness_assessment")
        if governance_signoff is None:
            missing.append("governance_signoff")
        if no_go_evaluation is None:
            missing.append("no_go_evaluation")
        blocker_items = tuple(blockers)
        override_items = tuple(overrides)
        if any(not item.resolved for item in blocker_items):
            missing.append("unresolved_blockers")
        if readiness_assessment is not None and not readiness_assessment.production_ready:
            missing.append("production_readiness")
        if governance_signoff is not None and not governance_signoff.allowed:
            missing.append("governance_signoff_completion")
        if no_go_evaluation is not None and no_go_evaluation.outcome != NoGoOutcome.GO:
            missing.append("go_outcome")
        pack = FinalReviewPack(pack_id=pack_id or f"FRP-{project_id}-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}", project_id=project_id, requirements=requirements or {}, scope_assessment=scope_assessment or {}, evidence_summary=evidence_summary or {}, design_summary=design_summary or {}, equipment_bom=equipment_bom or {}, config_artifacts=config_artifacts or {}, readiness_assessment=readiness_assessment.model_dump(mode="json") if readiness_assessment else {}, governance_signoff=governance_signoff.model_dump(mode="json") if governance_signoff else {}, no_go_evaluation=no_go_evaluation.model_dump(mode="json") if no_go_evaluation else {}, blockers=tuple(item.model_dump(mode="json") for item in blocker_items), overrides=tuple(item.model_dump(mode="json") for item in override_items), missing_items=tuple(dict.fromkeys(missing)), final_approval_allowed=not missing, sot_basis=sot_basis or {"status": "not supplied"}, evidence_ids=tuple(dict.fromkeys(str(item) for item in evidence_ids)))
        self.record_decision(f"review_pack:{pack.pack_id}", "approval_ready" if pack.final_approval_allowed else "incomplete", "final review pack status is derived from supplied artifacts and formal controls")
        return pack
