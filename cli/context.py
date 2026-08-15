"""Execution context and service boundary for the AutoNetArchitect CLI."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Mapping

from audit.audit_trail import AuditTrail
from auth.auth_manager import AuthManager, AuthenticationError
from auth.rbac import PermissionDenied, Principal, RBAC
from auth.session_manager import SessionError, SessionManager
from orchestrators import DeploymentOrchestrator, DesignOrchestrator, MasterOrchestrator, OperationsOrchestrator, WorkflowContext, WorkflowStage
from persistence.project_persistence import ProjectPersistence
from source_of_truth.sot_manager import SoTManager
from log_redaction.redacting_filter import RedactingFilter

from .output_formatter import OutputFormatter


@dataclass
class CLISettings:
    """Global settings shared by one CLI invocation."""

    project: str | None = None
    output_format: str = "text"
    verbose: int = 0
    debug: bool = False
    quiet: bool = False
    no_color: bool = False
    config_path: str | None = None
    root: Path = field(default_factory=lambda: Path.home() / ".autonetarchitect")


@dataclass(frozen=True)
class CLIResult:
    """Secret-safe structured command result."""

    success: bool
    status: str
    message: str
    data: dict[str, Any] = field(default_factory=dict)
    exit_code: int = 0

    def to_dict(self) -> dict[str, Any]:
        """Serialize the result for JSON/YAML/table output."""
        return {"success": self.success, "status": self.status, "message": self.message, "data": RedactingFilter.sanitize_value(self.data), "exit_code": self.exit_code}


ServiceCallable = Callable[[str, Mapping[str, Any], "CLIContext"], Mapping[str, Any]]


class CLIContext:
    """Coordinate CLI concerns while delegating network business actions outward."""

    PERMISSION_BY_ACTION = {
        "project.read": "project.read",
        "project.write": "project.write",
        "questionnaire.read": "project.read",
        "questionnaire.write": "project.write",
        "design.read": "project.read",
        "design.write": "project.write",
        "equipment.read": "project.read",
        "equipment.write": "project.write",
        "config.read": "config.read",
        "config.generate": "config.generate",
        "validate": "project.read",
        "deploy.preview": "deployment.preview",
        "deploy.execute": "deployment.execute",
        "rollback.execute": "rollback.execute",
        "operations.read": "project.read",
        "operations.write": "project.write",
        "incident.read": "project.read",
        "incident.write": "project.write",
        "change.read": "project.read",
        "change.write": "project.write",
        "change.execute": "deployment.execute",
        "compliance.read": "project.read",
        "report.read": "project.read",
        "diagram.read": "project.read",
        "export.read": "project.read",
        "lab.preview": "deployment.preview",
        "admin": "*",
        "audit.read": "audit.read",
        "system": "*",
    }

    def __init__(self, settings: CLISettings, *, audit_trail: AuditTrail | None = None, persistence: ProjectPersistence | None = None, auth_manager: AuthManager | None = None, session_manager: SessionManager | None = None, rbac: RBAC | None = None) -> None:
        """Create a context with local-first dependencies under one root."""
        self.settings = settings
        self.settings.root.mkdir(parents=True, exist_ok=True)
        self.audit_trail = audit_trail or AuditTrail(self.settings.root / "audit.jsonl")
        self.persistence = persistence or ProjectPersistence(self.settings.root / "projects")
        self.rbac = rbac or RBAC()
        self.auth_manager = auth_manager or AuthManager(self.settings.root / "users.json", rbac=self.rbac, audit_trail=self.audit_trail)
        self.session_manager = session_manager or SessionManager(self.settings.root / "sessions.json")
        self.master = MasterOrchestrator(sot_manager=SoTManager(self.settings.root / "sot.json"), audit_trail=self.audit_trail)
        self.design = DesignOrchestrator(master=self.master)
        self.deployment = DeploymentOrchestrator(master=self.master)
        self.operations = OperationsOrchestrator(master=self.master)
        self.output = OutputFormatter(settings.output_format, no_color=settings.no_color, quiet=settings.quiet)
        self.current_project = settings.project
        self.principal: Principal = Principal("anonymous", ("viewer",))
        self.session_id: str | None = None
        self.services: dict[str, ServiceCallable] = {}
        self._load_session_pointer()

    def register_service(self, action: str, service: ServiceCallable) -> None:
        """Register an external service adapter without embedding its business logic."""
        if not action or not callable(service):
            raise ValueError("action and service callable are required")
        self.services[action] = service

    def require(self, permission_or_action: str) -> None:
        """Enforce RBAC for a command action or direct permission name."""
        permission = self.PERMISSION_BY_ACTION.get(permission_or_action, permission_or_action)
        try:
            self.rbac.enforce(self.principal, permission)
        except PermissionDenied:
            self.audit_trail.record("cli.authorization_denied", self.principal.username, {"permission": permission, "project": self.current_project}, outcome="blocked", source="autonetarchitect.cli")
            raise

    def dispatch(self, action: str, payload: Mapping[str, Any] | None = None, *, permission: str | None = None, destructive: bool = False) -> CLIResult:
        """Authorize, audit, and delegate one command action."""
        values = dict(payload or {})
        required_permission = permission or action
        try:
            self.require(required_permission)
        except PermissionDenied as exc:
            return CLIResult(False, "authorization_denied", str(exc), {"action": action}, 3)
        project = str(values.get("project") or self.current_project) if values.get("project") or self.current_project else None
        if self._requires_project(action) and not project:
            return CLIResult(False, "project_required", "A project is required for this command", {"action": action}, 4)
        if project is not None:
            self.current_project = project
        safe_payload = RedactingFilter.sanitize_value(values)
        self.audit_trail.record("cli.command", self.principal.username, {"action": action, "project": project, "payload": safe_payload, "destructive": destructive}, outcome="started", source="autonetarchitect.cli")
        try:
            result = self._dispatch_builtin(action, values, project)
            self.audit_trail.record("cli.command", self.principal.username, {"action": action, "project": project, "status": result.status, "exit_code": result.exit_code}, outcome="success" if result.success else "blocked", source="autonetarchitect.cli")
            return result
        except FileNotFoundError as exc:
            result = CLIResult(False, "project_not_found", str(exc), {"action": action, "project": project}, 4)
        except (PermissionDenied, AuthenticationError, SessionError) as exc:
            result = CLIResult(False, "authentication_or_authorization", str(exc), {"action": action}, 3)
        except Exception as exc:
            if self.settings.debug:
                raise
            result = CLIResult(False, "error", f"{type(exc).__name__}: {exc}", {"action": action}, 1)
        self.audit_trail.record("cli.command", self.principal.username, {"action": action, "project": project, "status": result.status, "exit_code": result.exit_code}, outcome="failure", source="autonetarchitect.cli")
        return result

    def login(self, username: str, password: str, *, ttl_seconds: int = 3600) -> CLIResult:
        """Authenticate and store only an opaque session pointer."""
        principal = self.auth_manager.authenticate(username, password)
        session = self.session_manager.create(principal, ttl_seconds=ttl_seconds)
        pointer = self.settings.root / "session_pointer.json"
        pointer.write_text(f"{{\"session_id\": \"{session.session_id}\"}}\n", encoding="utf-8")
        self.principal = Principal(principal.username, principal.roles, session.session_id)
        self.session_id = session.session_id
        return CLIResult(True, "authenticated", "Authentication succeeded", {"username": principal.username, "roles": list(principal.roles), "expires_at": session.expires_at})

    def logout(self) -> CLIResult:
        """Revoke the active session and remove its local pointer."""
        if self.session_id:
            self.session_manager.revoke(self.session_id)
        pointer = self.settings.root / "session_pointer.json"
        pointer.unlink(missing_ok=True)
        self.principal = Principal("anonymous", ("viewer",))
        self.session_id = None
        return CLIResult(True, "logged_out", "Session revoked", {})

    def whoami(self) -> CLIResult:
        """Return current principal metadata without credential values."""
        return CLIResult(True, "authenticated" if self.principal.username != "anonymous" else "anonymous", "Current principal", {"username": self.principal.username, "roles": list(self.principal.roles), "session_id_present": self.session_id is not None})

    def get_project(self, project: str | None = None) -> tuple[dict[str, Any], str]:
        """Load a project and return its payload plus identifier."""
        project_id = project or self.current_project
        if not project_id:
            raise FileNotFoundError("project is not selected")
        payload, _result = self.persistence.load(project_id)
        self.current_project = project_id
        return payload, project_id

    def _dispatch_builtin(self, action: str, values: Mapping[str, Any], project: str | None) -> CLIResult:
        """Handle only lifecycle boundary adaptations; domain services remain external."""
        if action == "project.create":
            project_id = str(values["name"])
            payload = {"project_id": project_id, "name": project_id, "sector": values.get("sector"), "description": values.get("description", ""), "status": "active", "workflow_context": self.master.create_context(project_id=project_id, actor=self.principal.username).to_dict()}
            result = self.persistence.save(project_id, payload)
            self.current_project = project_id
            return CLIResult(True, "created", "Project created", {"project_id": project_id, "checksum": result.checksum})
        if action == "project.list":
            projects = sorted(path.name.removesuffix(".project.json") for path in self.persistence.root.glob("*.project.json"))
            return CLIResult(True, "listed", "Projects listed", {"projects": projects})
        if action in {"project.show", "project.status"}:
            payload, project_id = self.get_project(project)
            return CLIResult(True, "loaded", "Project loaded", {"project_id": project_id, "project": payload})
        if action == "project.open":
            payload, project_id = self.get_project(str(values["name"]))
            return CLIResult(True, "opened", "Project opened", {"project_id": project_id, "project": payload})
        if action == "project.delete":
            self.persistence.delete(str(values["name"]))
            return CLIResult(True, "deleted", "Project deleted", {"project_id": str(values["name"])})
        if action in {"design.generate", "deployment.prepare", "deployment.execute", "operations.run"}:
            context = self._workflow_context(project)
            if action == "design.generate":
                result = self.design.run(context, values, evidence_ids=tuple(str(item) for item in values.get("evidence_ids", ())), approval_reference=str(values["approval_reference"]) if values.get("approval_reference") else None)
            elif action == "deployment.prepare":
                result = self.deployment.prepare(context, values, evidence_ids=tuple(str(item) for item in values.get("evidence_ids", ())), approval_reference=str(values["approval_reference"]) if values.get("approval_reference") else None)
            elif action == "deployment.execute":
                result = self.deployment.execute(context, values, evidence_ids=tuple(str(item) for item in values.get("evidence_ids", ())), real_execution=bool(values.get("real_execution", False)))
            else:
                result = self.operations.run(context, values, evidence_ids=tuple(str(item) for item in values.get("evidence_ids", ())), mutating=bool(values.get("mutating", False)))
            self._save_workflow_context(project, context)
            return CLIResult(result.success, result.status, "Workflow action completed" if result.success else "Workflow action blocked", result.to_dict(), 0 if result.success else 5)
        service = self.services.get(action)
        if service is not None:
            response = dict(service(action, values, self))
            return CLIResult(bool(response.get("success", True)), str(response.get("status", "delegated")), str(response.get("message", "Action delegated")), response)
        return CLIResult(True, "delegated", "Action delegated to registered service boundary", {"action": action, "project": project, "inputs": RedactingFilter.sanitize_value(dict(values))})

    def _workflow_context(self, project: str | None) -> WorkflowContext:
        payload, project_id = self.get_project(project)
        context_payload = payload.get("workflow_context")
        if isinstance(context_payload, dict):
            return WorkflowContext.from_dict(context_payload)
        return self.master.create_context(project_id=project_id, actor=self.principal.username)

    def _save_workflow_context(self, project: str | None, context: WorkflowContext) -> None:
        payload, project_id = self.get_project(project)
        payload["workflow_context"] = context.to_dict()
        self.persistence.save(project_id, payload)

    def _load_session_pointer(self) -> None:
        """Load and validate a locally stored opaque session pointer."""
        pointer = self.settings.root / "session_pointer.json"
        if not pointer.exists():
            return
        try:
            import json
            session_id = str(json.loads(pointer.read_text(encoding="utf-8"))["session_id"])
            principal = self.session_manager.validate(session_id)
            self.principal = principal
            self.session_id = session_id
        except (OSError, ValueError, KeyError, SessionError, TypeError):
            pointer.unlink(missing_ok=True)
            self.principal = Principal("anonymous", ("viewer",))
            self.session_id = None

    @staticmethod
    def _requires_project(action: str) -> bool:
        """Return whether an action normally operates on a project."""
        return not (action.startswith("project.") or action.startswith("admin.") or action.startswith("system.") or action.startswith("audit."))
