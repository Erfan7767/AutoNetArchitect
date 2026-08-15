"""Shared deterministic setup for deployment chaos tests."""
from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any, Callable, Mapping

from orchestrators import DeploymentOrchestrator, WorkflowContext, WorkflowStage
from source_of_truth.sot_manager import SoTType
from tests.final_test_helpers import create_master


class PreparedDeployment:
    """Temporary prepared deployment context with real orchestrator state."""

    def __init__(self) -> None:
        """Create an isolated temporary deployment scenario."""
        self.temporary = TemporaryDirectory(prefix="autonet-chaos-")
        root = Path(self.temporary.name)
        self.master, self.audit, self.sot = create_master(root)
        self.context = self.master.create_context(project_id="ChaosProject", actor="chaos-engineer", completed_through=WorkflowStage.CONFIG_GENERATION, evidence_ids=("E-DESIGN", "E-DEPLOY"))
        self.master.register_transition_sot(self.context, sot_type=SoTType.DESIGN, payload={"project_id": "ChaosProject", "intent": "chaos-test"}, source="chaos-fixture", authority="chaos-engineer", evidence_ids=("E-DESIGN",), approval_reference="design-review")
        prepared = DeploymentOrchestrator(master=self.master).prepare(self.context, {"deployment_artifact_id": "CHAOS-PREP", "source": "chaos-fixture", "authority": "chaos-engineer"}, evidence_ids=("E-DEPLOY", "E-DEPLOY-APPROVAL"), approval_reference="deployment-review")
        if not prepared.success:
            raise AssertionError(f"chaos setup failed: {prepared.reasons}")
        self.deployment = DeploymentOrchestrator(master=self.master)

    def close(self) -> None:
        """Release temporary state."""
        self.temporary.cleanup()


def run_failing_deploy(handler: Callable[[WorkflowContext, Mapping[str, Any]], Mapping[str, Any]], *, real_execution: bool = False, payload: Mapping[str, Any] | None = None):
    """Run one injected deployment failure and return its bounded result."""
    prepared = PreparedDeployment()
    try:
        values = {"execution_result_id": "CHAOS-EXEC", "backup_reference": "BACKUP-CHAOS", "real_execution": real_execution} | dict(payload or {})
        return prepared.deployment.execute(prepared.context, values, handler=handler, evidence_ids=("E-EXEC",), real_execution=real_execution)
    finally:
        prepared.close()
