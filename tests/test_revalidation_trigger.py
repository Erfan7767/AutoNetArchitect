from expert_override.override_manager import OverrideManager
from expert_override.override_models import OverrideRequest, OverrideScope, OverrideTargetType, OverrideType, RevalidationStatus

def test_revalidation_engine_creates_triggers_for_dependents():
    request = OverrideRequest(override_id="ov-r", target_id="design-1", target_type=OverrideTargetType.DESIGN_DECISION, override_type=OverrideType.MODIFY_VALUE, scope=OverrideScope(project_id="p-1", workflow="design", target_ids=("design-1",), scope_statement="one design"), actor_id="eng", actor_role="engineer", reason="field evidence", impact="downstream config changes", proposed_value="choice-b", machine_decision_id="machine-1")
    application = OverrideManager().apply(request, dependency_graph={"design-1": ("equipment-1", "config-1")})
    assert application.revalidation_status == RevalidationStatus.SCHEDULED and set(application.revalidation_trigger_ids) >= {"reval:ov-r:0", "reval:ov-r:1", "reval:ov-r:2"}
