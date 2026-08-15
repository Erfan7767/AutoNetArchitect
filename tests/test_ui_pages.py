"""Tests for UI page adapters and controller delegation."""
from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory

from ui.app import UIController, create_app


PAGE_FILES = ("01_questionnaire.py", "02_requirements.py", "03_design.py", "04_equipment.py", "05_configs.py", "06_deployment.py", "07_operations.py", "08_compliance.py", "09_reports.py", "10_admin.py", "11_audit.py")


def test_all_numbered_pages_load_and_expose_render_only():
    with TemporaryDirectory() as tmp:
        app = create_app(tmp)
        try:
            for filename in PAGE_FILES:
                module = app.pages_directory / filename
                source = module.read_text(encoding="utf-8")
                assert "def render" in source
                assert "deployment" not in source.lower() or filename == "06_deployment.py"
                response = app.dispatch(filename, {})
                assert response.page in {"questionnaire", "requirements", "design", "equipment", "configs", "deployment", "operations", "compliance", "reports", "admin", "audit"}
        finally:
            app.controller.close()


def test_ui_controller_delegates_design_and_deployment_lifecycle():
    with TemporaryDirectory() as tmp:
        controller = UIController.from_directory(tmp)
        try:
            selected = controller.select_project("ui-project", "engineer", completed_through="requirements")
            assert selected.status == "success"
            design = controller.handle_page("design", {"artifact_id": "design-artifact", "evidence_ids": ["design-e1"], "approval_reference": "design-approval"})
            assert design.status == "completed"
            equipment = controller.handle_page("equipment", {"artifact_id": "bom-artifact"})
            assert equipment.status == "completed"
            configs = controller.handle_page("configs", {"artifact_id": "config-artifact"})
            assert configs.status == "completed"
            prepared = controller.handle_page("deployment", {"mode": "prepare", "deployment_artifact_id": "package-artifact", "evidence_ids": ["deploy-e1"], "approval_reference": "deployment-approval"})
            assert prepared.status == "completed"
            executed = controller.handle_page("deployment", {"mode": "execute", "execution_result_id": "dry-run-result", "real_execution": False})
            assert executed.status == "completed"
            operations = controller.handle_page("operations", {"artifact_id": "health-evidence"})
            assert operations.status == "completed"
            compliance = controller.handle_page("compliance", {"artifact_id": "compliance-evidence"})
            assert compliance.status == "completed"
            reports = controller.handle_page("reports", {"artifact_id": "report-artifact"})
            assert reports.status == "completed"
        finally:
            controller.close()


def test_real_deployment_block_is_visible_as_approval_widget():
    with TemporaryDirectory() as tmp:
        controller = UIController.from_directory(tmp)
        try:
            controller.select_project("approval-project", "engineer", completed_through="config_generation")
            active_context = controller._context()
            controller.master.register_transition_sot(active_context, sot_type="DESIGN", payload={"artifact_ids": ["design"]}, source="test", authority="engineer", evidence_ids=("e1",), approval_reference="design-approval")
            controller.state_manager.set_workflow_context(active_context.to_dict())
            prepared = controller.handle_page("deployment", {"mode": "prepare", "deployment_artifact_id": "package", "approval_reference": "deployment-approval", "evidence_ids": ["e2"]})
            assert prepared.status == "completed"
            blocked = controller.handle_page("deployment", {"mode": "execute", "execution_result_id": "real", "real_execution": True, "approval_required": True})
            assert blocked.status == "blocked"
            assert blocked.approval is not None
            assert blocked.approval["status"] == "pending"
            assert controller.state_manager.snapshot().approval_requests
        finally:
            controller.close()


def test_audit_page_is_read_only_and_contains_controller_events():
    with TemporaryDirectory() as tmp:
        controller = UIController.from_directory(tmp)
        try:
            controller.select_project("audit-project", "engineer")
            controller.handle_page("questionnaire", {"password": "secret-value"})
            response = controller.handle_page("audit", {"limit": 20})
            assert response.status == "success"
            assert response.data["read_only"] is True
        finally:
            controller.close()
