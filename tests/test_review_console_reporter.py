from types import SimpleNamespace
from decision_engine.optimization_engine import DecisionResult
from governance import SignoffEvaluation
from review_console.decision_workbench import DecisionWorkbench
from review_console.review_console_reporter import ReviewConsoleReporter
from review_console.review_session import ReviewSession

def test_console_reporter_generates_bilingual_review_artifact():
    result = DecisionResult(status="no_decision", chosen=None, ranked=[], explanation={"status": "no_decision", "chosen_option": None, "evidence_basis": [], "confidence": 0.1, "confidence_rationale": "inputs missing", "rationale": "no safe decision"}, confidence=0.1)
    workbench = DecisionWorkbench().build(decision_id="d-1", decision_result=result, decision_context={"missing_information": ["mandatory input"]}, final_review_pack={"readiness_assessment": {"production_ready": False}}, signoff_evaluation=SignoffEvaluation(workflow="design", allowed=False, state="blocked_pending_signoff"))
    session = ReviewSession(session_id="s-1", project_id="p-1", workflow="design", reviewer_id="eng", reviewer_role="engineer")
    report = ReviewConsoleReporter().generate(workbench=workbench, session=session)
    assert report.human_action_required and "Engineer Review Console Report" in ReviewConsoleReporter().to_markdown(report)
