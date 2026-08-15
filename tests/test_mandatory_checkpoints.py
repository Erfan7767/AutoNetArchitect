from review_control.mandatory_checkpoints import CheckpointControlType, MandatoryCheckpointRegistry

def test_mandatory_registry_contains_required_checkpoints():
    ids = {item.checkpoint_id for item in MandatoryCheckpointRegistry().all()}
    assert {"requirements.completeness_review", "scope.unsupported_review", "evidence.sufficiency_review", "design.final_review", "equipment.bom_review", "config.pre_generation_review", "deployment.pre_go_no_go", "deployment.post_acceptance"} <= ids

def test_checkpoint_controls_include_review_approval_and_no_go():
    types = {item.control_type for item in MandatoryCheckpointRegistry().all()}
    assert {CheckpointControlType.REVIEW_ONLY, CheckpointControlType.APPROVAL_REQUIRED, CheckpointControlType.NO_GO_UNTIL_RESOLVED} <= types
