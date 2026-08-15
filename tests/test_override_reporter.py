from expert_override.override_manager import OverrideManager
from expert_override.override_models import OverrideRequest, OverrideScope, OverrideTargetType, OverrideType
from expert_override.override_reporter import OverrideReporter

def _request(override_id, machine_id):
    return OverrideRequest(override_id=override_id, target_id="decision-1", target_type=OverrideTargetType.DESIGN_DECISION, override_type=OverrideType.FORCE_ACCEPT, scope=OverrideScope(project_id="p-1", workflow="design", target_ids=("decision-1",), scope_statement="bounded"), actor_id="eng", actor_role="engineer", reason="human engineering rationale", impact="downstream review", machine_decision_id=machine_id)

def test_override_reporter_distinguishes_origins():
    manager = OverrideManager()
    first = manager.apply(_request("ov-o", "machine-1"))
    second = manager.apply(_request("ov-h", None).model_copy(update={"override_type": OverrideType.FORCE_REJECT}))
    report = OverrideReporter().generate(project_id="p-1", applications=[first, second])
    markdown = OverrideReporter().to_markdown(report)
    assert len(report.human_overridden_decisions) == 1 and len(report.human_originated_decisions) == 1 and "Human-overridden" in markdown
