from datetime import datetime, timedelta, timezone

from change_management import Approval, ChangeOrchestrator, ConfigChange, DeviceRef, MaintenanceWindow, VerificationResult


def test_change_orchestrator_runs_governed_lifecycle_to_close():
    orchestrator = ChangeOrchestrator()
    request = orchestrator.create_request("Add VLAN", "Add one documented VLAN", "alice", affected_devices=[DeviceRef("edge-1")], config_changes=[ConfigChange("edge-1", "edge-1", "vlan", commands_to_apply=("set vlan",), commands_to_rollback=("remove vlan",))])
    orchestrator.submit(request.change_id)
    orchestrator.classify(request.change_id, production_environment=True)
    orchestrator.assess_risk(request.change_id, lab_tested=True, during_maintenance_window=True, dependencies="none", reversibility="fully_reversible", experience="standard")
    orchestrator.assess_impact(request.change_id, user_counts={"edge-1": 10})
    orchestrator.build_plans(request.change_id, validator=lambda device, commands: True, backup_evidence_ids=["backup-1"])
    requirements, evaluation = orchestrator.request_approvals(request.change_id)
    approval = None
    for role in requirements.required_roles:
        approval = orchestrator.record_approval(request.change_id, Approval(role, "bob", "approved", "approved"), requirements.required_roles)
    assert approval is not None
    assert approval.state == "approved"
    start = datetime.now(timezone.utc) + timedelta(hours=1)
    window = MaintenanceWindow(start, start + timedelta(hours=2), "UTC", "maintenance", True)
    orchestrator.schedule_manager.add_window(window)
    orchestrator.schedule(request.change_id, window)
    orchestrator.start_execution(request.change_id, actor="alice")
    orchestrator.update_step(request.change_id, 1, "completed", executed_by="alice", matches_expected=True)
    orchestrator.verify(request.change_id, [VerificationResult("v-1", "command_verification", "show vlan", "present", "present", "passed")])
    closed = orchestrator.close(request.change_id, "successful", lessons_learned="none")
    assert closed.closure_code == "successful"
    assert orchestrator.lifecycle(request.change_id).production_execution_allowed is False
