from supervised_mode.workflow_annotations import WorkflowAnnotation, WorkflowAnnotationRegistry, supervised_workflow
from supervised_mode.workflow_mode import WorkflowStage

def test_workflow_annotation_is_discoverable():
    annotation = WorkflowAnnotation(workflow_name="design_preview", workflow_stage=WorkflowStage.DESIGN, checkpoint_ids=("design.intent_review",), mutating=False)
    @supervised_workflow(annotation)
    def run():
        return "ok"
    registry = WorkflowAnnotationRegistry()
    assert registry.discover(run) == annotation and run() == "ok"
