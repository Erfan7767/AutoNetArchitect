from review_control.no_go_policy import BlockerClass, NoGoBlocker
from review_console.risk_viewer import RiskViewer

def test_risk_viewer_surfaces_formal_blockers():
    blocker = NoGoBlocker(blocker_id="B-1", blocker_class=BlockerClass.EVIDENCE, blocking_reason="evidence insufficient", affected_stage="design", required_resolution="collect evidence")
    risks = RiskViewer().build(blockers=(blocker,))
    assert risks[0].risk_id == "B-1" and risks[0].severity == "blocking" and risks[0].resolved is False
