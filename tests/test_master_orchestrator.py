"""Tests for master orchestration contracts."""
from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory

from audit.audit_trail import AuditTrail
from orchestrators import MasterOrchestrator, Preconditions, PreconditionError, StageOrderError, WorkflowStage
from source_of_truth.sot_manager import SoTManager, SoTType


def _master(tmp: str) -> tuple[MasterOrchestrator, AuditTrail]:
    audit = AuditTrail(Path(tmp) / "audit.jsonl")
    sot = SoTManager(Path(tmp) / "sot.json")
    return MasterOrchestrator(sot_manager=sot, audit_trail=audit), audit


def test_master_enforces_exact_stage_order() -> None:
    with TemporaryDirectory() as tmp:
        master, _ = _master(tmp)
        context = master.create_context(project_id="p1", actor="engineer", completed_through=WorkflowStage.REQUIREMENTS)
        blocked = master.execute_stage(
            context,
            target_stage=WorkflowStage.EQUIPMENT,
            preconditions=Preconditions(),
            handler=lambda _context, _data: {"artifact_ids": ("a1",)},
            input_data={},
        )
        assert blocked.success is False
        assert "stage order violation" in blocked.reasons[0]
        assert context.current_stage == WorkflowStage.REQUIREMENTS.value


def test_master_requires_approved_attached_sot() -> None:
    with TemporaryDirectory() as tmp:
        master, _ = _master(tmp)
        context = master.create_context(project_id="p2", actor="engineer", completed_through=WorkflowStage.REQUIREMENTS)
        record = master.sot_manager.register(
            sot_type=SoTType.DESIGN,
            payload={"artifact_ids": ["d1"]},
            source="test",
            authority="engineer",
            evidence_ids=("e1",),
            approved=False,
        )
        context.attach_sot(record)
        reasons = master.validate_preconditions(
            context,
            target_stage=WorkflowStage.DESIGN,
            preconditions=Preconditions(required_sot_types=(SoTType.DESIGN.value,)),
        )
        assert reasons
        assert "approved" in " ".join(reasons)
        master.sot_manager.approve(record.record_id, authority="engineer")
        assert master.validate_preconditions(
            context,
            target_stage=WorkflowStage.DESIGN,
            preconditions=Preconditions(required_sot_types=(SoTType.DESIGN.value,)),
        ) == ()


def test_master_audits_success_and_blocked_outcomes() -> None:
    with TemporaryDirectory() as tmp:
        master, audit = _master(tmp)
        context = master.create_context(project_id="p3", actor="engineer", completed_through=WorkflowStage.REQUIREMENTS)
        result = master.execute_stage(
            context,
            target_stage=WorkflowStage.DESIGN,
            preconditions=Preconditions(),
            handler=lambda _context, _data: {"artifact_ids": ("design-1",)},
            input_data={},
        )
        assert result.success is True
        assert context.current_stage == WorkflowStage.DESIGN.value
        assert audit.entries()
        audit.verify_integrity()


def test_precondition_error_is_typed() -> None:
    with TemporaryDirectory() as tmp:
        master, _ = _master(tmp)
        context = master.create_context(project_id="p4", actor="engineer", completed_through=WorkflowStage.REQUIREMENTS)
        try:
            master.require_preconditions(context, target_stage=WorkflowStage.EQUIPMENT, preconditions=Preconditions())
        except PreconditionError as exc:
            assert "stage order violation" in str(exc)
        else:
            raise AssertionError("expected PreconditionError")


def test_context_rejects_invalid_direct_stage_transition() -> None:
    with TemporaryDirectory() as tmp:
        master, _ = _master(tmp)
        context = master.create_context(project_id="p5", actor="engineer", completed_through=WorkflowStage.REQUIREMENTS)
        try:
            context.apply_transition(WorkflowStage.DEPLOYMENT_EXECUTION)
        except StageOrderError:
            return
        raise AssertionError("expected StageOrderError")
