from types import SimpleNamespace
from decision_engine.optimization_engine import DecisionResult
from governance import SignoffEvaluation
from review_console.decision_workbench import DecisionWorkbench

def _result():
    ranked = [SimpleNamespace(alternative_name="option-a", total_score=9.0, rejection_reasons=[], constraint_results=[]), SimpleNamespace(alternative_name="option-b", total_score=6.0, rejection_reasons=["soft cost penalty"], constraint_results=[])]
    return DecisionResult(status="decided", chosen=SimpleNamespace(name="option-a"), ranked=ranked, explanation={"chosen_option": "option-a", "rejected_options": [{"option": "option-b", "score": 6.0, "rejection_reasons": ["soft cost penalty"]}], "evidence_basis": ["ev-1"], "confidence": 0.86, "confidence_rationale": "evidence-backed", "rationale": "highest admissible weighted utility"}, confidence=0.86)

def test_workbench_presents_decision_alternatives_evidence_and_approvals():
    view = DecisionWorkbench().build(decision_id="decision-1", decision_result=_result(), decision_context={"evidence": ["ev-2"], "missing_information": ["floor dimensions"]}, final_review_pack={"scope_assessment": {"boundaries": ["site survey required"]}, "readiness_assessment": {"production_ready": False}, "sot_basis": {"DESIGN": "sot://design/1"}, "design_summary": {"status": "review"}}, signoff_evaluation=SignoffEvaluation(workflow="design", allowed=False, state="blocked_pending_signoff", pending_checkpoints=("approval:design_authority",)), insufficient_evidence=({"item_id": "ev-gap", "description": "survey evidence missing"},))
    assert view.chosen_recommendation == "option-a" and len(view.alternatives) == 2 and view.evidence_ids == ("ev-1", "ev-2") and view.required_approvals == ("approval:design_authority",) and view.unresolved_items
