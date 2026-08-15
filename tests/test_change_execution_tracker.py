from change_management import ChangeExecutionTracker, ChangeRequest, ImplementationPlan, ImplementationStep


def test_change_execution_tracker_updates_steps_and_moves_to_verification():
    request = ChangeRequest("CHG-12", "Execution", "Detailed", "alice", status="scheduled", implementation_plan=ImplementationPlan(steps=(ImplementationStep(1, "step", "edge-1", commands=("show",)),)))
    tracker = ChangeExecutionTracker()
    tracker.start(request, actor="alice")
    summary = tracker.update_step(request, 1, "completed", executed_by="alice", actual_output="password=secret-value", matches_expected=True)
    assert request.status == "verification"
    assert summary.completed_steps == 1
    assert "secret-value" not in request.execution_log[0].actual_output


def test_change_execution_tracker_records_failed_step():
    request = ChangeRequest("CHG-13", "Execution", "Detailed", "alice", status="scheduled", implementation_plan=ImplementationPlan(steps=(ImplementationStep(1, "step", "edge-1"),)))
    tracker = ChangeExecutionTracker()
    tracker.start(request, actor="alice")
    tracker.update_step(request, 1, "failed", executed_by="alice", actual_output="failure")
    assert request.status == "failed"
