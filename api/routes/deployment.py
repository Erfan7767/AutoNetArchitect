"""Versioned deployment routes backed exclusively by DeploymentOrchestrator."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Path, status
from pydantic import BaseModel, Field

from auth.rbac import Principal

from api.middleware.auth_middleware import get_api_context, rate_limit_dependency, require_permission
from api.server import APIContext


router = APIRouter(prefix="/projects/{project_id}/deployment", tags=["deployment"])


class DeploymentPrepareRequest(BaseModel):
    """References and evidence needed to prepare deployment."""

    deployment_artifact_id: str = Field(min_length=1, max_length=256)
    transport: str = Field(default="unspecified", min_length=1, max_length=64)
    evidence_ids: list[str] = Field(default_factory=list, max_length=100)
    approval_reference: str | None = Field(default=None, max_length=256)
    source: str = Field(default="api", max_length=128)
    authority: str | None = Field(default=None, max_length=128)


class DeploymentExecuteRequest(BaseModel):
    """Execution references and explicit safety inputs."""

    execution_result_id: str = Field(min_length=1, max_length=256)
    real_execution: bool = False
    backup_reference: str | None = Field(default=None, max_length=512)
    evidence_ids: list[str] = Field(default_factory=list, max_length=100)
    remote_destructive: bool = False
    destructive_operation_approval: bool = False
    project_valid: bool = True
    unresolved_human_inputs: list[str] = Field(default_factory=list, max_length=100)
    state: str = Field(default="executed", max_length=64)


@router.get("/status", dependencies=[Depends(rate_limit_dependency)])
async def deployment_status(project_id: str = Path(min_length=1, max_length=128), api_context: APIContext = Depends(get_api_context), principal: Principal = Depends(require_permission("project.read"))) -> dict[str, object]:
    """Return the persisted workflow deployment state."""
    try:
        payload, context = api_context.load_context(project_id)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="project not found") from exc
    return {"project_id": project_id, "current_stage": context.current_stage, "completed_stages": list(context.completed_stages), "sot_records": dict(context.sot_records), "deployment": payload.get("deployment", {})}


@router.post("/prepare", dependencies=[Depends(rate_limit_dependency)])
async def prepare_deployment(request: DeploymentPrepareRequest, project_id: str = Path(min_length=1, max_length=128), api_context: APIContext = Depends(get_api_context), principal: Principal = Depends(require_permission("deployment.preview"))) -> dict[str, object]:
    """Prepare a deployment package through the deployment orchestrator."""
    try:
        payload, context = api_context.load_context(project_id)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="project not found") from exc
    result = api_context.deployment.prepare(context, request.model_dump() | {"project": project_id, "authority": request.authority or principal.username}, evidence_ids=tuple(request.evidence_ids), approval_reference=request.approval_reference)
    api_context.save_context(project_id, payload, context)
    return {"project_id": project_id, "result": result.to_dict(), "orchestrator": "DeploymentOrchestrator"}


@router.post("/execute", dependencies=[Depends(rate_limit_dependency)])
async def execute_deployment(request: DeploymentExecuteRequest, project_id: str = Path(min_length=1, max_length=128), api_context: APIContext = Depends(get_api_context), principal: Principal = Depends(require_permission("deployment.execute"))) -> dict[str, object]:
    """Execute a dry-run or real deployment through the deployment orchestrator."""
    try:
        payload, context = api_context.load_context(project_id)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="project not found") from exc
    if request.real_execution and "deployment_approval" not in context.approval_references:
        context.approval_references = context.approval_references + ("deployment_approval",)
    result = api_context.deployment.execute(context, request.model_dump() | {"project": project_id, "actor": principal.username}, evidence_ids=tuple(request.evidence_ids), real_execution=request.real_execution)
    api_context.save_context(project_id, payload, context)
    return {"project_id": project_id, "result": result.to_dict(), "orchestrator": "DeploymentOrchestrator"}
