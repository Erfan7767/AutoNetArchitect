"""Engineer decision workbench as a thin view over existing services."""
from __future__ import annotations

from typing import Any, Iterable

from pydantic import BaseModel, ConfigDict, Field

from designers.base_designer import BaseDesigner

from .alternative_viewer import AlternativeView, AlternativeViewer
from .evidence_viewer import EvidenceItemView, EvidenceViewer
from .risk_viewer import RiskItemView, RiskViewer
from .signoff_panel import SignoffPanel, SignoffPanelView
from .unresolved_viewer import UnresolvedItemView, UnresolvedViewer


class DecisionWorkbenchView(BaseModel):
    """Complete decision review surface for one engineer session."""

    model_config = ConfigDict(extra="forbid")

    decision_id: str
    decision_status: str
    chosen_recommendation: str | None = None
    rationale: str = ""
    confidence: float = 0.0
    confidence_rationale: str = ""
    alternatives: tuple[AlternativeView, ...] = ()
    evidence_chain: tuple[EvidenceItemView, ...] = ()
    risks: tuple[RiskItemView, ...] = ()
    unresolved_items: tuple[UnresolvedItemView, ...] = ()
    assumptions: tuple[str, ...] = ()
    affected_artifacts: tuple[str, ...] = ()
    required_approvals: tuple[str, ...] = ()
    scope_boundaries: tuple[str, ...] = ()
    evidence_ids: tuple[str, ...] = ()
    production_claim_allowed: bool = False
    source_references: dict[str, str] = Field(default_factory=dict)


class DecisionWorkbench(BaseDesigner):
    """Compose source outputs for review without recomputing business decisions."""

    def __init__(self, *, alternative_viewer: AlternativeViewer | None = None, evidence_viewer: EvidenceViewer | None = None, risk_viewer: RiskViewer | None = None, unresolved_viewer: UnresolvedViewer | None = None, signoff_panel: SignoffPanel | None = None) -> None:
        """Initialize workbench with presentation adapters."""
        super().__init__("DecisionWorkbench")
        self.alternative_viewer = alternative_viewer or AlternativeViewer()
        self.evidence_viewer = evidence_viewer or EvidenceViewer()
        self.risk_viewer = risk_viewer or RiskViewer()
        self.unresolved_viewer = unresolved_viewer or UnresolvedViewer()
        self.signoff_panel = signoff_panel or SignoffPanel()
        self.record_decision("workbench_policy", "source_artifact_composition", "workbench displays existing service outputs and does not make, rank, approve, or override decisions")

    def build(self, *, decision_id: str, decision_result: Any, decision_context: Any | None = None, final_review_pack: Any | None = None, signoff_evaluation: Any | None = None, evidence_records: Iterable[Any] = (), risks: Iterable[Any] = (), human_mandatory: Iterable[Any] = (), assumptions: Iterable[Any] = (), insufficient_evidence: Iterable[Any] = (), scope_issues: Iterable[Any] = (), affected_artifacts: Iterable[str] = ()) -> DecisionWorkbenchView:
        """Build the engineer-facing workbench view from source objects."""
        result_data = self._data(decision_result)
        explanation = result_data.get("explanation") or {}
        chosen = result_data.get("chosen")
        chosen_name = explanation.get("chosen_option") or self._name(chosen)
        context_data = self._data(decision_context)
        pack_data = self._data(final_review_pack)
        evidence_ids = tuple(dict.fromkeys(str(value) for value in tuple(explanation.get("evidence_basis", ())) + tuple(context_data.get("evidence", ())) + tuple(pack_data.get("evidence_ids", ()))))
        evidence_views = self.evidence_viewer.build(evidence_records, evidence_ids)
        alternative_views = self.alternative_viewer.build(chosen_name=chosen_name, ranked=result_data.get("ranked", ()), explanation=explanation)
        unresolved_views = self.unresolved_viewer.build(human_mandatory=human_mandatory, assumptions=assumptions, insufficient_evidence=insufficient_evidence, scope_issues=scope_issues)
        signoff_view = self.signoff_panel.build(signoff_evaluation)
        readiness = pack_data.get("readiness_assessment") or {}
        pack_scope = pack_data.get("scope_assessment") or {}
        scope_boundaries = tuple(str(value) for value in pack_scope.get("boundaries", pack_scope.get("issues", ())))
        artifact_ids = tuple(dict.fromkeys(str(value) for value in tuple(affected_artifacts) + tuple(pack_data.get("evidence_ids", ())) + self._artifact_keys(pack_data)))
        required_approvals = signoff_view.pending_checkpoints if signoff_view is not None else ()
        return DecisionWorkbenchView(decision_id=decision_id, decision_status=str(result_data.get("status", explanation.get("status", "unknown"))), chosen_recommendation=chosen_name, rationale=str(explanation.get("rationale", "")), confidence=float(result_data.get("confidence", explanation.get("confidence", 0.0)) or 0.0), confidence_rationale=str(explanation.get("confidence_rationale", "")), alternatives=alternative_views, evidence_chain=evidence_views, risks=self.risk_viewer.build(risks=risks, blockers=(pack_data.get("blockers") or ()), readiness=readiness or None), unresolved_items=unresolved_views, assumptions=tuple(str(value) for value in tuple(context_data.get("missing_information", ())) + tuple(self._assumption_names(assumptions))), affected_artifacts=artifact_ids, required_approvals=tuple(required_approvals), scope_boundaries=scope_boundaries, evidence_ids=evidence_ids, production_claim_allowed=bool(readiness.get("production_ready", False)), source_references=dict(pack_data.get("sot_basis", {})))

    @staticmethod
    def _data(value: Any) -> dict[str, Any]:
        """Read a Pydantic or dataclass-like source object."""
        if value is None:
            return {}
        if isinstance(value, dict):
            return value
        if hasattr(value, "model_dump"):
            return dict(value.model_dump())
        if hasattr(value, "__dict__"):
            return dict(value.__dict__)
        return {}

    @staticmethod
    def _name(value: Any) -> str | None:
        """Read a chosen alternative name without selecting one."""
        if value is None:
            return None
        if isinstance(value, dict):
            return value.get("name")
        return getattr(value, "name", str(value))

    @staticmethod
    def _assumption_names(items: Iterable[Any]) -> tuple[str, ...]:
        """Render source assumption keys or descriptions."""
        values: list[str] = []
        for item in items:
            if isinstance(item, dict):
                values.append(str(item.get("key", item.get("description", item))))
            else:
                values.append(str(getattr(item, "key", getattr(item, "description", item))))
        return tuple(values)

    @staticmethod
    def _artifact_keys(pack: dict[str, Any]) -> tuple[str, ...]:
        """Expose names of populated review-pack sections as affected surfaces."""
        return tuple(key for key in ("requirements", "design_summary", "equipment_bom", "config_artifacts") if pack.get(key))
