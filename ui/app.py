"""Minimal V1 UI shell that delegates workflow actions to orchestrators."""
from __future__ import annotations

from dataclasses import dataclass
import importlib.util
from pathlib import Path
from typing import Any, Mapping

from audit.audit_trail import AuditTrail
from orchestrators import DeploymentOrchestrator, DesignOrchestrator, MasterOrchestrator, OperationsOrchestrator, Preconditions, WorkflowContext, WorkflowStage
from source_of_truth.sot_manager import SoTManager

from .background_jobs import BackgroundJobManager
from .components.approval_widget import ApprovalWidget
from .components.log_viewer import LogViewer
from .state_manager import UIStateManager, mask_for_ui


@dataclass(frozen=True)
class PageResponse:
    """Secret-safe response returned to a page adapter."""

    page: str
    status: str
    message: str
    data: dict[str, Any]
    approval: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        """Serialize the response for a UI framework or API adapter."""
        return {"page": self.page, "status": self.status, "message": self.message, "data": mask_for_ui(self.data), "approval": mask_for_ui(self.approval) if self.approval is not None else None}


class UIController:
    """Primary UI-facing adapter around existing orchestrator entry points."""

    def __init__(self, *, state_manager: UIStateManager, master: MasterOrchestrator, audit_trail: AuditTrail, jobs: BackgroundJobManager | None = None) -> None:
        """Create a controller with explicit local persistence and orchestration dependencies."""
        self.state_manager = state_manager
        self.master = master
        self.design = DesignOrchestrator(master=master)
        self.deployment = DeploymentOrchestrator(master=master)
        self.operations = OperationsOrchestrator(master=master)
        self.audit_trail = audit_trail
        self.jobs = jobs or BackgroundJobManager()

    @classmethod
    def from_directory(cls, directory: str | Path) -> "UIController":
        """Build a local V1 controller using files below one directory."""
        root = Path(directory)
        root.mkdir(parents=True, exist_ok=True)
        state = UIStateManager(root / "ui_state.json")
        audit = AuditTrail(root / "audit.jsonl")
        master = MasterOrchestrator(sot_manager=SoTManager(root / "sot.json"), audit_trail=audit)
        return cls(state_manager=state, master=master, audit_trail=audit)

    def select_project(self, project_id: str, actor: str, *, completed_through: WorkflowStage | str = WorkflowStage.QUESTIONNAIRE) -> PageResponse:
        """Select one project and initialize its supervised workflow context."""
        context = self.master.create_context(project_id=project_id, actor=actor, completed_through=completed_through)
        self.state_manager.set_project(project_id, actor)
        self.state_manager.set_workflow_context(context.to_dict())
        return PageResponse("10_admin", "success", "Project selected", {"project_id": project_id, "actor": actor, "workflow_id": context.workflow_id, "current_stage": context.current_stage})

    def handle_page(self, page: str, payload: Mapping[str, Any] | None = None) -> PageResponse:
        """Handle one page action while keeping page modules free of business logic."""
        values = dict(payload or {})
        self.state_manager.set_page(page)
        if page == "questionnaire":
            self.state_manager.update_values(values)
            return PageResponse(page, "saved", "Questionnaire values saved locally", {"field_count": len(values), "local_only": True})
        if page == "admin":
            return PageResponse(page, "success", "Local UI state loaded", self.state_manager.snapshot().to_dict())
        if page == "audit":
            return PageResponse(page, "success", "Audit entries loaded", self.audit_view(event_type=values.get("event_type"), outcome=values.get("outcome"), limit=int(values.get("limit", 100))).render())
        context = self._context()
        if context is None:
            return PageResponse(page, "blocked", "Select a project before using workflow pages", {"requires_project": True})
        if page == "design":
            result = self.design.run(context, values, evidence_ids=tuple(str(item) for item in values.get("evidence_ids", ())), approval_reference=str(values["approval_reference"]) if values.get("approval_reference") else None)
        elif page == "deployment":
            result = self._deployment_action(context, values)
        elif page == "operations":
            result = self.operations.run(context, values, evidence_ids=tuple(str(item) for item in values.get("evidence_ids", ())), mutating=bool(values.get("mutating", False)))
        else:
            result = self._generic_stage(context, page, values)
        self.state_manager.set_workflow_context(context.to_dict())
        approval = self._approval_for(result, values)
        return PageResponse(page, result.status, "Workflow action completed" if result.success else "Workflow action blocked", result.to_dict(), approval)

    def submit_page_job(self, page: str, payload: Mapping[str, Any] | None = None) -> str:
        """Queue one page action without changing page business semantics."""
        return self.jobs.submit(f"ui:{page}", self.handle_page, page, dict(payload or {}), metadata={"page": page})

    def audit_view(self, *, event_type: str | None = None, outcome: str | None = None, limit: int = 100) -> LogViewer:
        """Return a read-only sanitized audit view."""
        viewer = LogViewer.from_entries(self.audit_trail.entries(), source="audit")
        return viewer.filter(event_type=event_type, outcome=outcome, limit=limit)

    def close(self) -> None:
        """Release UI background worker resources."""
        self.jobs.shutdown()

    def _context(self) -> WorkflowContext | None:
        """Load the active context from local state."""
        payload = self.state_manager.snapshot().workflow_context
        if not payload:
            return None
        return WorkflowContext.from_dict(payload)

    def _deployment_action(self, context: WorkflowContext, values: Mapping[str, Any]) -> Any:
        """Route deployment preparation or execution to the deployment orchestrator."""
        mode = str(values.get("mode", "prepare"))
        evidence_ids = tuple(str(item) for item in values.get("evidence_ids", ()))
        if mode == "prepare":
            return self.deployment.prepare(context, values, evidence_ids=evidence_ids, approval_reference=str(values["approval_reference"]) if values.get("approval_reference") else None)
        if mode == "execute":
            return self.deployment.execute(context, values, evidence_ids=evidence_ids, real_execution=bool(values.get("real_execution", False)))
        return self.master.blocked(context, stage=WorkflowStage.DEPLOYMENT_PREPARATION, reasons=(f"unsupported deployment UI mode: {mode}",))

    def _generic_stage(self, context: WorkflowContext, page: str, values: Mapping[str, Any]) -> Any:
        """Adapt an externally produced artifact to the master orchestrator."""
        stage_map = {"requirements": WorkflowStage.REQUIREMENTS, "equipment": WorkflowStage.EQUIPMENT, "configs": WorkflowStage.CONFIG_GENERATION, "compliance": WorkflowStage.COMPLIANCE, "reports": WorkflowStage.REPORTS}
        if page not in stage_map:
            return self.master.blocked(context, stage=WorkflowStage.REQUIREMENTS, reasons=(f"unsupported workflow UI page: {page}",))
        stage = stage_map[page]
        preconditions = Preconditions(
            project_valid=bool(values.get("project_valid", context.project_valid)),
            unresolved_human_inputs=tuple(str(item) for item in values.get("unresolved_human_inputs", ())),
            required_evidence_ids=tuple(str(item) for item in values.get("required_evidence_ids", ())),
            required_approval_references=tuple(str(item) for item in values.get("required_approval_references", ())),
            required_sot_types=tuple(str(item) for item in values.get("required_sot_types", ())),
        )
        return self.master.execute_stage(context, target_stage=stage, preconditions=preconditions, handler=self._artifact_handler, input_data=values)

    @staticmethod
    def _artifact_handler(context: WorkflowContext, values: Mapping[str, Any]) -> Mapping[str, Any]:
        """Adapt a service-produced artifact ID; never generate domain artifacts in UI."""
        artifact = values.get("artifact_id") or values.get("artifact_reference") or values.get("result_id")
        if not artifact:
            return {}
        return {"artifact_ids": (str(artifact),), "source": "external_ui_service_adapter"}

    def _approval_for(self, result: Any, values: Mapping[str, Any]) -> dict[str, Any] | None:
        """Create a visible approval widget and persist a pending request when required."""
        reasons = tuple(str(item) for item in getattr(result, "reasons", ()))
        approval_requested = bool(values.get("approval_required", False)) or any("approval" in item.lower() for item in reasons)
        if not approval_requested:
            return None
        required_role = str(values.get("required_role", "engineer"))
        widget = ApprovalWidget.pending(action=f"{getattr(result, 'stage', 'workflow')}_action", stage=str(getattr(result, "stage", "unknown")), reasons=reasons, required_role=required_role) if approval_requested else ApprovalWidget.from_result(result, required_role=required_role)
        self.state_manager.add_approval_request(action=widget.action, stage=widget.stage, reasons=widget.reasons, required_role=widget.required_role)
        return widget.render()


def load_page(page_file: str | Path) -> Any:
    """Load a numbered page module without requiring a UI framework."""
    path = Path(page_file)
    spec = importlib.util.spec_from_file_location(f"autonet_ui_page_{path.stem}", path)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load UI page: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class AppShell:
    """Framework-neutral application shell for CLI, HTTP, or GUI adapters."""

    PAGE_FILES = (
        "01_questionnaire.py", "02_requirements.py", "03_design.py", "04_equipment.py", "05_configs.py", "06_deployment.py", "07_operations.py", "08_compliance.py", "09_reports.py", "10_admin.py", "11_audit.py",
    )

    def __init__(self, controller: UIController, *, pages_directory: str | Path | None = None) -> None:
        """Create a shell around one controller and optional page directory."""
        self.controller = controller
        self.pages_directory = Path(pages_directory) if pages_directory is not None else Path(__file__).parent / "pages"

    def dispatch(self, page_file: str, payload: Mapping[str, Any] | None = None) -> PageResponse:
        """Dispatch through the page adapter and return its response."""
        if page_file not in self.PAGE_FILES:
            raise ValueError(f"unsupported UI page: {page_file}")
        module = load_page(self.pages_directory / page_file)
        return module.render(self.controller, dict(payload or {}))


def create_app(directory: str | Path) -> AppShell:
    """Create a minimal local application shell."""
    controller = UIController.from_directory(directory)
    return AppShell(controller)


if __name__ == "__main__":
    print("AutoNetArchitect V1 UI shell is framework-neutral; use create_app(directory) from an adapter.")
