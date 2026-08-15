"""Integration test for the governed end-to-end logical pipeline."""
from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory

from source_of_truth.sot_manager import SoTType

from orchestrators import DeploymentOrchestrator, OperationsOrchestrator, WorkflowStage
from tests.final_test_helpers import context_at, create_master, fixture_project


def test_full_pipeline_preserves_order_sot_and_read_only_operations():
    with TemporaryDirectory() as tmp:
        root = Path(tmp)
        master, audit, sot = create_master(root)
        project = fixture_project("enterprise_greenfield")
        context = master.create_context(project_id=project["project_id"], actor="integration-engineer", evidence_ids=("EVID-DESIGN-001",))
        for stage in (WorkflowStage.REQUIREMENTS, WorkflowStage.DESIGN, WorkflowStage.EQUIPMENT, WorkflowStage.CONFIG_GENERATION):
            result = master.advance(context, stage, artifact_ids=(f"{stage.value}:001",))
            assert result.success is True
            assert result.stage == stage.value
        design_record = master.register_transition_sot(context, sot_type=SoTType.DESIGN, payload={"project_id": context.project_id, "intent": "secure-resilient-enterprise"}, source="integration-fixture", authority="integration-engineer", evidence_ids=("EVID-DESIGN-001",), approval_reference="design-review-001")
        assert design_record.approved is True
        deployment = DeploymentOrchestrator(master=master)
        prepared = deployment.prepare(context, {"deployment_artifact_id": "DEPLOY-PREP-001", "source": "integration", "authority": "integration-engineer"}, evidence_ids=("EVID-DESIGN-001", "EVID-DEPLOY-APPROVAL"), approval_reference="deployment-prep-review")
        assert prepared.success is True
        assert prepared.stage == WorkflowStage.DEPLOYMENT_PREPARATION.value
        dry_run = deployment.execute(context, {"execution_result_id": "EXEC-DRY-001", "state": "dry_run"}, real_execution=False)
        assert dry_run.success is True
        operations = OperationsOrchestrator(master=master)
        operational = operations.run(context, {"operational_artifact_id": "OPS-001", "service": "read-only-health"}, evidence_ids=("OPS-EVID-001",), mutating=False)
        assert operational.success is True
        assert operational.data["mode"] == "read_only"
        for stage in (WorkflowStage.COMPLIANCE, WorkflowStage.REPORTS):
            completed = master.advance(context, stage, artifact_ids=(f"{stage.value}:001",))
            assert completed.success is True
        assert context.current_stage == WorkflowStage.REPORTS.value
        assert set(context.sot_records).issuperset({SoTType.DESIGN.value, SoTType.DEPLOYMENT.value, SoTType.OPERATIONAL.value})
        assert audit.verify_integrity() is True
