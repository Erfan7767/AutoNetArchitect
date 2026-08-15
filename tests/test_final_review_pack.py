from governance import SignoffEvaluation
from review_control.final_review_pack import FinalReviewPackBuilder
from review_control.mandatory_checkpoints import CheckpointRecord, MandatoryCheckpointStatus
from review_control.no_go_policy import NoGoEvaluation, NoGoOutcome
from review_control.readiness_gate import ReadinessAssessment

def test_final_review_pack_marks_missing_sections():
    pack = FinalReviewPackBuilder().build(project_id="p-1")
    assert not pack.final_approval_allowed and "requirements" in pack.missing_items

def test_final_review_pack_allows_complete_explicit_inputs():
    no_go = NoGoEvaluation(stage="design", outcome=NoGoOutcome.GO, production_release_allowed=True)
    readiness = ReadinessAssessment(stage="design", production_ready=True, readiness_status="production_ready", no_go_evaluation=no_go, proof_status="verified", evidence_ids=("ev-1",))
    governance = SignoffEvaluation(workflow="design", allowed=True, state="approved")
    pack = FinalReviewPackBuilder().build(project_id="p-1", requirements={"status": "complete"}, scope_assessment={"status": "supported"}, evidence_summary={"status": "sufficient"}, design_summary={"status": "approved"}, equipment_bom={"status": "reviewed"}, config_artifacts={"status": "reviewed"}, readiness_assessment=readiness, governance_signoff=governance, no_go_evaluation=no_go, sot_basis={"DESIGN": "sot://design/p-1"}, evidence_ids=("ev-1",))
    assert pack.final_approval_allowed and pack.sot_basis["DESIGN"] == "sot://design/p-1"
