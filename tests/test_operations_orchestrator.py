"""Tests for operations lifecycle orchestration."""
from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory

from audit.audit_trail import AuditTrail
from orchestrators import DeploymentOrchestrator, DesignOrchestrator, MasterOrchestrator, OperationsOrchestrator, WorkflowStage
from source_of_truth.sot_manager import SoTManager


def _operational_context(root: Path):
    audit = AuditTrail(root / "audit.jsonl")
    master = MasterOrchestrator(sot_manager=SoTManager(root / "sot.json"), audit_trail=audit)
    context = master.create_context(project_id="operations-project", actor="operator", completed_through=WorkflowStage.CONFIG_GENERATION, evidence_ids=("e1",), approval_references=("deployment_approval",))
    master.register_transition_sot(context, sot_type="DESIGN", payload={"artifact_ids": ["design-artifact"]}, source="design-service", authority="architect", evidence_ids=("design-e1",), approval_reference="design-approval")
    deployment = DeploymentOrchestrator(master=master)
    assert deployment.prepare(context, {"deployment_artifact_id": "deployment-package"}, evidence_ids=("deploy-e1",), approval_reference="deployment-approval").success is True
    assert deployment.execute(context, {"execution_result_id": "execution-result", "backup_reference": "backup://operations-project", "destructive_operation_approval": True}, evidence_ids=("exec-e1",), real_execution=True).success is True
    return master, context, audit


def test_operations_requires_deployment_sot_and_correct_stage():
    with TemporaryDirectory() as tmp:
        root = Path(tmp)
        audit = AuditTrail(root / "audit.jsonl")
        master = MasterOrchestrator(sot_manager=SoTManager(root / "sot.json"), audit_trail=audit)
        context = master.create_context(project_id="operations-project-2", actor="operator", completed_through=WorkflowStage.REQUIREMENTS)
        operations = OperationsOrchestrator(master=master)
        result = operations.run(context, {"artifact_id": "ops-evidence"})
        assert result.success is False
        assert "stage order violation" in " ".join(result.reasons)


def test_operations_defaults_to_read_only_and_registers_operational_sot():
    with TemporaryDirectory() as tmp:
        master, context, audit = _operational_context(Path(tmp))
        operations = OperationsOrchestrator(master=master)
        result = operations.run(context, {"artifact_id": "health-evidence", "service": "health_checker"}, evidence_ids=("health-e1",))
        assert result.success is True
        assert result.data["mode"] == "read_only"
        assert context.current_stage == WorkflowStage.OPERATIONS.value
        assert "OPERATIONAL" in context.sot_records
        assert audit.query(event_type="orchestrator.sot_transition")


def test_operations_high_risk_mutation_requires_approval():
    with TemporaryDirectory() as tmp:
        master, context, _audit = _operational_context(Path(tmp))
        operations = OperationsOrchestrator(master=master)
        result = operations.run(context, {"artifact_id": "maintenance-action", "high_risk": True}, mutating=True)
        assert result.success is False
        assert "high-risk operational mutation" in " ".join(result.reasons)
        assert context.current_stage == WorkflowStage.DEPLOYMENT_EXECUTION.value


def test_operations_uses_injected_service_and_audits_transition():
    with TemporaryDirectory() as tmp:
        master, context, audit = _operational_context(Path(tmp))
        operations = OperationsOrchestrator(master=master)
        calls: list[str] = []

        def handler(active_context, input_data):
            calls.append(active_context.project_id)
            assert input_data["query"] == "health"
            return {"artifact_ids": ("health-result",), "observation_count": 2}

        result = operations.run(context, {"query": "health"}, handler=handler, evidence_ids=("observation-e1",))
        assert result.success is True
        assert calls == ["operations-project"]
        assert audit.verify_integrity() is True
