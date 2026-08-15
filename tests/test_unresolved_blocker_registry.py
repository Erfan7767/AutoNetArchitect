from review_control.no_go_policy import BlockerClass, NoGoBlocker
from review_control.unresolved_blocker_registry import BlockerRegistry

def test_blocker_registry_open_and_resolve_requires_evidence():
    registry = BlockerRegistry()
    registry.open(NoGoBlocker(blocker_id="B-2", blocker_class=BlockerClass.DESIGN, blocking_reason="field feasibility pending", affected_stage="design", required_resolution="complete survey"))
    assert registry.active()
    resolved = registry.resolve("B-2", resolution_reference="survey://site-1", evidence_ids=("survey-1",))
    assert resolved.resolved and not registry.active()
