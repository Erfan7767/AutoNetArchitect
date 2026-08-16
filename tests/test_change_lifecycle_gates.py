"""Lifecycle gate tests for the engineer-supervised local change flow."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from change_management import (
    Approval,
    ChangeOrchestrator,
    ConfigChange,
    DeviceRef,
    MaintenanceWindow,
    VerificationResult,
)


def _request(orchestrator: ChangeOrchestrator) -> str:
    """Create a scoped request with a documented target and rollback intent."""
    request = orchestrator.create_request(
        "Add documented VLAN",
        "Introduce one approved VLAN on a known edge device.",
        "engineer@example.test",
        affected_devices=[DeviceRef("edge-1")],
        config_changes=[
            ConfigChange(
                "edge-1",
                "edge-1",
                "vlan",
                commands_to_apply=("set vlan",),
                commands_to_rollback=("remove vlan",),
            )
        ],
    )
    return request.change_id


def test_risk_assessment_cannot_skip_classification_and_preserves_gate_reason() -> None:
    """An unresolved classification gate stops downstream risk preparation."""
    orchestrator = ChangeOrchestrator()
    change_id = _request(orchestrator)
    orchestrator.submit(change_id)

    with pytest.raises(ValueError, match=r"impact assessment requires status in \['risk_assessed'\], current=submitted"):
        orchestrator.assess_impact(change_id, user_counts={"edge-1": 10})

    lifecycle = orchestrator.lifecycle(change_id)
    assert lifecycle.current_status == "submitted"
    assert lifecycle.next_steps == ("classify",)
    assert lifecycle.production_execution_allowed is False


def test_missing_approval_halts_scheduling_and_names_the_unmet_gate() -> None:
    """A complete plan cannot enter a maintenance window without recorded approval."""
    orchestrator = ChangeOrchestrator()
    change_id = _request(orchestrator)
    orchestrator.submit(change_id)
    orchestrator.classify(change_id, production_environment=True)
    orchestrator.assess_risk(
        change_id,
        lab_tested=True,
        during_maintenance_window=True,
        dependencies="none",
        reversibility="fully_reversible",
        experience="standard",
    )
    orchestrator.assess_impact(change_id, user_counts={"edge-1": 10})
    orchestrator.build_plans(change_id, validator=lambda _device, _commands: True, backup_evidence_ids=["backup-1"])
    window_start = datetime.now(timezone.utc) + timedelta(hours=1)
    window = MaintenanceWindow(window_start, window_start + timedelta(hours=2), "UTC", "approved window", True)

    with pytest.raises(ValueError, match=r"scheduling requires status in \['approved'\], current=plan_complete"):
        orchestrator.schedule(change_id, window)

    lifecycle = orchestrator.lifecycle(change_id)
    assert lifecycle.current_status == "plan_complete"
    assert lifecycle.next_steps == ("request_approvals",)
    assert lifecycle.production_execution_allowed is False


def test_failed_verification_requires_human_follow_up_and_blocks_automatic_completion() -> None:
    """A failed observation remains explicit and never authorizes autonomous remediation."""
    orchestrator = ChangeOrchestrator()
    change_id = _request(orchestrator)
    orchestrator.submit(change_id)
    orchestrator.classify(change_id, production_environment=True)
    orchestrator.assess_risk(change_id, lab_tested=True, during_maintenance_window=True, dependencies="none", reversibility="fully_reversible", experience="standard")
    orchestrator.assess_impact(change_id, user_counts={"edge-1": 10})
    orchestrator.build_plans(change_id, validator=lambda _device, _commands: True, backup_evidence_ids=["backup-1"])
    requirements, _ = orchestrator.request_approvals(change_id)
    for role in requirements.required_roles:
        orchestrator.record_approval(change_id, Approval(role, "reviewer@example.test", "approved", "recorded approval"), requirements.required_roles)
    window_start = datetime.now(timezone.utc) + timedelta(hours=1)
    window = MaintenanceWindow(window_start, window_start + timedelta(hours=2), "UTC", "approved window", True)
    orchestrator.schedule_manager.add_window(window)
    orchestrator.schedule(change_id, window)
    orchestrator.start_execution(change_id, actor="executor@example.test")
    orchestrator.update_step(change_id, 1, "completed", executed_by="executor@example.test", matches_expected=True)

    result = orchestrator.verify(
        change_id,
        [VerificationResult("verification-1", "connectivity_verification", "approved external check", "reachable", "unreachable", "failed", evidence_ids=("evidence-1",))],
    )

    lifecycle = orchestrator.lifecycle(change_id)
    assert result.overall_status == "failed"
    assert result.rollback_consideration_required is True
    assert lifecycle.current_status == "failed"
    assert lifecycle.next_steps == ()
    assert lifecycle.production_execution_allowed is False
