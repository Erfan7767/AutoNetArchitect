from governance import SignoffEvaluation
from review_control.mandatory_checkpoints import CheckpointRecord, MandatoryCheckpointStatus
from review_control.readiness_gate import ReadinessGate

def test_readiness_gate_blocks_without_proof():
    result = ReadinessGate().assess(stage="design", proof_status="not_verifiable_with_current_inputs", field_feasibility_status="feasible", production_requested=True, approval_present=True)
    assert not result.production_ready and result.readiness_status == "blocked_no_go"

def test_readiness_gate_allows_verified_governed_design():
    record = CheckpointRecord(checkpoint_id="design.final_review", workflow_stage="design", status=MandatoryCheckpointStatus.APPROVED, reviewer_id="owner", reviewer_role="design_authority", decision_reference="approval://design/2", rationale="approved", evidence_ids=("design-1",))
    governance = SignoffEvaluation(workflow="design", allowed=True, state="approved")
    result = ReadinessGate().assess(stage="design", checkpoint_records=(record,), proof_status="verified", field_feasibility_status="feasible", governance_evaluation=governance, evidence_ids=("proof-1",), production_requested=True, approval_present=True)
    assert result.production_ready and result.readiness_status == "production_ready"
