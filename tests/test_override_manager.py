from expert_override.override_manager import OverrideManager
from expert_override.override_models import DecisionOrigin, OverrideRequest, OverrideScope, OverrideTargetType, OverrideType, RevalidationStatus

def _request(**kwargs):
    values = {"override_id": "ov-m", "target_id": "decision-1", "target_type": OverrideTargetType.DESIGN_DECISION, "override_type": OverrideType.FORCE_ACCEPT, "scope": OverrideScope(project_id="p-1", workflow="design", target_ids=("decision-1",), scope_statement="bounded decision"), "actor_id": "eng-1", "actor_role": "engineer", "reason": "validated field constraint", "impact": "recheck downstream design", "original_value": False, "machine_decision_id": "machine-1", "evidence_ids": ("ev-1",)}
    values.update(kwargs)
    return OverrideRequest(**values)

def test_override_manager_preserves_machine_provenance_and_schedules_revalidation():
    result = OverrideManager().apply(_request(), dependency_graph={"decision-1": ("config-1",)})
    assert result.status == "applied" and result.origin == DecisionOrigin.HUMAN_OVERRIDDEN and result.resulting_value is True and result.revalidation_status == RevalidationStatus.SCHEDULED
    assert result.provenance_chain == ("machine-1", "ov-m")

def test_override_manager_records_human_originated_decision():
    result = OverrideManager().apply(_request(override_id="ov-human", machine_decision_id=None, override_type=OverrideType.FORCE_REJECT))
    assert result.origin == DecisionOrigin.HUMAN_ORIGINATED and result.resulting_value is False
