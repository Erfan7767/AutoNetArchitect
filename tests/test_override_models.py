from datetime import datetime, timezone
from expert_override.override_models import DecisionOrigin, OverrideRequest, OverrideScope, OverrideTargetType, OverrideType, RevalidationStatus

def _request(override_type=OverrideType.FORCE_ACCEPT, target_type=OverrideTargetType.DESIGN_DECISION, **kwargs):
    values = {"override_id": "ov-1", "target_id": "decision-1", "target_type": target_type, "override_type": override_type, "scope": OverrideScope(project_id="p-1", workflow="design", target_ids=("decision-1",), scope_statement="one design decision"), "actor_id": "eng-1", "actor_role": "engineer_in_charge", "reason": "field constraint requires a different decision", "impact": "downstream design artifacts require review", "original_value": "machine-choice", "evidence_ids": ("ev-1",), "machine_decision_id": "machine-1"}
    values.update(kwargs)
    return OverrideRequest(**values)

def test_override_model_preserves_decision_fields():
    request = _request()
    assert request.machine_decision_id == "machine-1" and request.decided_at.tzinfo is not None
    assert request.target_type == OverrideTargetType.DESIGN_DECISION

def test_override_origin_enum_is_explicit():
    assert DecisionOrigin.HUMAN_OVERRIDDEN.value == "human_overridden" and RevalidationStatus.SCHEDULED.value == "scheduled"
