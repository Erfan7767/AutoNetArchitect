"""E2E-style deployment flow tests through the UI orchestration boundary."""
from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory

from orchestrators import WorkflowStage
from ui.app import UIController


def test_ui_deployment_flow_blocks_without_design_sot_and_exposes_approval():
    with TemporaryDirectory() as tmp:
        controller = UIController.from_directory(Path(tmp))
        try:
            selected = controller.select_project("DeployE2E", "e2e-engineer", completed_through=WorkflowStage.CONFIG_GENERATION)
            assert selected.status == "success"
            blocked = controller.handle_page("deployment", {"mode": "prepare", "deployment_artifact_id": "PREP-001", "approval_required": True, "evidence_ids": ["E-DEPLOY"]})
            assert blocked.status == "blocked"
            assert blocked.approval is not None
            assert blocked.approval["status"] == "pending"
            execution = controller.handle_page("deployment", {"mode": "execute", "execution_result_id": "EXEC-001", "real_execution": True})
            assert execution.status == "blocked"
            assert execution.data["success"] is False
        finally:
            controller.close()
