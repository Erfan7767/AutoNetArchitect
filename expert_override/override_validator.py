"""Validation policy for expert override requests."""
from __future__ import annotations

from pydantic import BaseModel, ConfigDict

from designers.base_designer import BaseDesigner

from .override_models import OverrideRequest, OverrideTargetType, OverrideType
from .override_scope import OverrideScopeValidator


class OverrideValidationResult(BaseModel):
    """Explainable override validation result."""

    model_config = ConfigDict(extra="forbid")

    allowed: bool
    reasons: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()
    requires_revalidation: bool
    scope_project_id: str


class OverrideValidator(BaseDesigner):
    """Validate expert interventions before they can be applied."""

    def __init__(self, *, scope_validator: OverrideScopeValidator | None = None) -> None:
        """Initialize validator with scope checks."""
        super().__init__("OverrideValidator")
        self.scope_validator = scope_validator or OverrideScopeValidator()
        self.record_decision("override_validation_default", "deny_invalid_intervention", "override requests require reason, impact, explicit scope, and target-appropriate authorization")

    def validate(self, request: OverrideRequest) -> OverrideValidationResult:
        """Validate a request and classify downstream revalidation necessity."""
        reasons: list[str] = []
        warnings: list[str] = []
        scope = self.scope_validator.evaluate(request)
        reasons.extend(scope.reasons)
        warnings.extend(scope.warnings)
        if not request.reason.strip():
            reasons.append("reason is mandatory")
        if not request.impact.strip():
            reasons.append("impact is mandatory")
        value_change = request.override_type in {OverrideType.MODIFY_VALUE, OverrideType.REPLACE_RECOMMENDATION}
        if value_change and request.proposed_value is None:
            reasons.append("proposed_value is required for value or recommendation changes")
        if request.override_type == OverrideType.DEFER_DECISION and request.proposed_value is not None:
            warnings.append("deferred decisions retain proposed_value only as an unaccepted human proposal")
        elevated_target = request.target_type in {OverrideTargetType.CONFIG_ARTIFACT, OverrideTargetType.DEPLOYMENT_GATE, OverrideTargetType.OPERATIONAL_POLICY}
        elevated_type = request.override_type in {OverrideType.FORCE_ACCEPT, OverrideType.MODIFY_VALUE, OverrideType.WIDEN_SCOPE_WITH_WARNING, OverrideType.REPLACE_RECOMMENDATION}
        if elevated_target and elevated_type and not request.approval_reference.startswith("approval://"):
            reasons.append("elevated target override requires an approval:// reference")
        if request.override_type == OverrideType.WIDEN_SCOPE_WITH_WARNING and not request.warning.strip():
            reasons.append("scope widening requires an explicit warning")
        requires_revalidation = request.requires_revalidation or request.override_type in {OverrideType.MODIFY_VALUE, OverrideType.NARROW_SCOPE, OverrideType.WIDEN_SCOPE_WITH_WARNING, OverrideType.REPLACE_RECOMMENDATION}
        allowed = not reasons
        self.record_decision(f"validate:{request.override_id}", allowed, "override validation is completed before any artifact patch or downstream use")
        return OverrideValidationResult(allowed=allowed, reasons=tuple(dict.fromkeys(reasons)), warnings=tuple(dict.fromkeys(warnings)), requires_revalidation=requires_revalidation, scope_project_id=scope.project_id)
