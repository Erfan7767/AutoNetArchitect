"""Tests for design-stage orchestration."""
from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory

from audit.audit_trail import AuditTrail
from orchestrators import DesignOrchestrator, MasterOrchestrator, WorkflowStage
from source_of_truth.sot_manager import SoTManager


def _design(tmp: str) -> tuple[MasterOrchestrator, DesignOrchestrator, AuditTrail]:
    audit = AuditTrail(Path(tmp) / "audit.jsonl")
    master = MasterOrchestrator(sot_manager=SoTManager(Path(tmp) / "sot.json"), audit_trail=audit)
    return master, DesignOrchestrator(master=master), audit


def test_design_registers_approved_design_sot_with_evidence() -> None:
    with TemporaryDirectory() as tmp:
        master, design, audit = _design(tmp)
        context = master.create_context(project_id="design-project", actor="architect", completed_through=WorkflowStage.REQUIREMENTS, evidence_ids=("req-evidence",))
        result = design.run(
            context,
            {"artifact_id": "design-artifact", "decision_ids": ("decision-1",), "source": "design-service"},
            evidence_ids=("design-evidence",),
            approval_reference="design-approval",
        )
        assert result.success is True
        assert context.current_stage == WorkflowStage.DESIGN.value
        assert result.data["sot_approved"] is True
        assert "DESIGN" in context.sot_records
        assert audit.query(event_type="orchestrator.sot_transition")


def test_design_blocks_missing_artifact_without_advancing() -> None:
    with TemporaryDirectory() as tmp:
        master, design, _ = _design(tmp)
        context = master.create_context(project_id="design-project-2", actor="architect", completed_through=WorkflowStage.REQUIREMENTS)
        result = design.run(context, {"decision_ids": ("decision-2",)})
        assert result.success is False
        assert context.current_stage == WorkflowStage.REQUIREMENTS.value
        assert "artifact" in " ".join(result.reasons)


def test_design_blocks_unresolved_human_input() -> None:
    with TemporaryDirectory() as tmp:
        master, design, _ = _design(tmp)
        context = master.create_context(project_id="design-project-3", actor="architect", completed_through=WorkflowStage.REQUIREMENTS, unresolved_human_inputs=("site_floor_dimensions",))
        result = design.run(context, {"artifact_id": "design-artifact"})
        assert result.success is False
        assert "HumanSuppliedMandatory" in " ".join(result.reasons)
        assert context.current_stage == WorkflowStage.REQUIREMENTS.value


def test_design_uses_injected_service_without_ui_logic() -> None:
    with TemporaryDirectory() as tmp:
        master, design, _ = _design(tmp)
        context = master.create_context(project_id="design-project-4", actor="architect", completed_through=WorkflowStage.REQUIREMENTS, evidence_ids=("e1",))
        calls: list[str] = []

        def handler(active_context, input_data):
            calls.append(active_context.workflow_id)
            assert input_data["service_input"] == "x"
            return {"artifact_ids": ("external-design",), "decision_ids": ("d-external",)}

        result = design.run(context, {"service_input": "x"}, handler=handler, approval_reference="approval")
        assert result.success is True
        assert len(calls) == 1
        assert result.artifact_ids == ("external-design",)
