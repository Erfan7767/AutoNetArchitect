"""Scope validation for expert interventions."""
from __future__ import annotations

from pydantic import BaseModel, ConfigDict

from designers.base_designer import BaseDesigner

from .override_models import OverrideRequest, OverrideType


class ScopeEvaluation(BaseModel):
    """Explainable scope validation result."""

    model_config = ConfigDict(extra="forbid")

    allowed: bool
    target_id: str
    project_id: str
    reasons: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()
    normalized_target_ids: tuple[str, ...] = ()


class OverrideScopeValidator(BaseDesigner):
    """Validate intervention scope without assuming authority outside the request."""

    def __init__(self) -> None:
        """Initialize scope validator."""
        super().__init__("OverrideScopeValidator")
        self.record_decision("override_scope_default", "deny_ambiguous_scope", "expert intervention must name a project and explicit target scope")

    def evaluate(self, request: OverrideRequest) -> ScopeEvaluation:
        """Validate target scope and add an explicit warning for scope widening."""
        reasons: list[str] = []
        warnings: list[str] = []
        scope = request.scope
        if request.target_id not in set(scope.target_ids) and scope.target_ids:
            reasons.append("target_id is outside the declared target_ids scope")
        if not scope.scope_statement.strip():
            reasons.append("scope statement is mandatory")
        if request.override_type == OverrideType.WIDEN_SCOPE_WITH_WARNING:
            warnings.append("scope widening requires downstream review of every newly affected artifact")
            if not request.warning.strip():
                reasons.append("widen_scope_with_warning requires an explicit warning")
        if request.override_type == OverrideType.NARROW_SCOPE and not scope.target_ids and not scope.device_ids and not scope.site_ids:
            reasons.append("narrow_scope requires at least one bounded target, device, or site")
        allowed = not reasons
        self.record_decision(f"scope:{request.override_id}", allowed, "override scope is checked against explicit request boundaries")
        return ScopeEvaluation(allowed=allowed, target_id=request.target_id, project_id=scope.project_id, reasons=tuple(dict.fromkeys(reasons)), warnings=tuple(dict.fromkeys(warnings)), normalized_target_ids=tuple(dict.fromkeys((request.target_id,) + scope.target_ids)))
