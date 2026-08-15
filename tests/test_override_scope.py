from expert_override.override_models import OverrideRequest, OverrideScope, OverrideTargetType, OverrideType
from expert_override.override_scope import OverrideScopeValidator

def _base(kind):
    return OverrideRequest(override_id="ov-s", target_id="decision-1", target_type=OverrideTargetType.DESIGN_DECISION, override_type=kind, scope=OverrideScope(project_id="p-1", workflow="design", target_ids=("decision-1",), scope_statement="bounded decision"), actor_id="eng", actor_role="engineer", reason="reason", impact="impact", warning="scope changed" if kind == OverrideType.WIDEN_SCOPE_WITH_WARNING else "")

def test_scope_validator_rejects_target_outside_declared_scope():
    request = _base(OverrideType.FORCE_ACCEPT).model_copy(update={"target_id": "decision-2"})
    assert not OverrideScopeValidator().evaluate(request).allowed

def test_scope_validator_requires_warning_for_scope_widening():
    request = _base(OverrideType.WIDEN_SCOPE_WITH_WARNING).model_copy(update={"warning": ""})
    assert not OverrideScopeValidator().evaluate(request).allowed
