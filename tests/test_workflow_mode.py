from supervised_mode.workflow_mode import WorkflowMode, WorkflowModeManager, WorkflowStage

def test_workflow_mode_defaults_to_supervised_high_assurance():
    state = WorkflowModeManager().create(human_owner_id="eng-1")
    assert state.mode == WorkflowMode.SUPERVISED and state.high_assurance is True and state.autonomy_permitted is False

def test_workflow_stage_taxonomy_covers_required_lifecycle():
    expected = {"questionnaire", "requirements", "design", "equipment", "config_generation", "deployment_preparation", "deployment_execution", "operations", "compliance", "reports"}
    assert {stage.value for stage in WorkflowStage} == expected
