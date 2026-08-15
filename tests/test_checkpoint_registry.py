from supervised_mode.checkpoint_registry import CheckpointRegistry
from supervised_mode.workflow_mode import WorkflowStage

def test_checkpoint_registry_has_all_stages_and_required_fields():
    registry = CheckpointRegistry()
    assert {stage.value for stage in registry.stages()} == {stage.value for stage in WorkflowStage}
    for definition in registry.all():
        assert definition.workflow_stage and definition.trigger_condition and definition.required_human_role and definition.decision_type and definition.allowed_actions is not None and definition.block_conditions is not None

def test_checkpoint_registry_supports_stage_query():
    assert registry_for_design()

def registry_for_design():
    return CheckpointRegistry().for_stage(WorkflowStage.DESIGN)
