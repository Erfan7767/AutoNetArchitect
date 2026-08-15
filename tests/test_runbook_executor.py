from incident_response.runbook_executor import RunbookExecutor
from incident_response.incident_models import IncidentCategory

def test_runbook_executor_loads_and_tracks_human_step():
    executor = RunbookExecutor("/home/ubuntu/AutoNetArchitect/data/incident_runbooks")
    runbook = executor.load("link_failure", IncidentCategory.NETWORK_OUTAGE)
    executor.start(runbook.runbook_id, incident_commander="alice")
    updated = executor.record_step(runbook.runbook_id, runbook.steps[0].step_id, executed_by="alice", status="completed", result="interface state confirmed")
    assert updated.steps[0].status == "completed"

def test_runbook_executor_rejects_unknown_runbook():
    try:
        RunbookExecutor("/home/ubuntu/AutoNetArchitect/data/incident_runbooks").load("missing", IncidentCategory.NETWORK_OUTAGE)
    except FileNotFoundError:
        return
    raise AssertionError("missing runbook must be rejected")
