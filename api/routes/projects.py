"""Versioned project routes using local-first persistence and orchestration boundaries."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Path, status
from pydantic import BaseModel, Field

from auth.rbac import Principal

from api.middleware.auth_middleware import get_api_context, get_current_principal, rate_limit_dependency, require_permission
from api.server import APIContext


router = APIRouter(prefix="/projects", tags=["projects"])


class ProjectCreateRequest(BaseModel):
    """Project creation inputs with no tenant or owner dimension."""

    name: str = Field(min_length=1, max_length=128, pattern=r"^[A-Za-z0-9_.-]+$")
    sector: str | None = Field(default=None, max_length=128)
    description: str = Field(default="", max_length=4000)


@router.post("", status_code=status.HTTP_201_CREATED, dependencies=[Depends(rate_limit_dependency)])
async def create_project(request: ProjectCreateRequest, api_context: APIContext = Depends(get_api_context), principal: Principal = Depends(require_permission("project.write"))) -> dict[str, object]:
    """Create one local project through the master orchestrator boundary."""
    try:
        return api_context.create_project(request.name, principal.username, request.sector, request.description)
    except FileExistsError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="project already exists") from exc
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.get("", dependencies=[Depends(rate_limit_dependency)])
async def list_projects(api_context: APIContext = Depends(get_api_context), principal: Principal = Depends(require_permission("project.read"))) -> dict[str, object]:
    """List local projects visible to the single local user."""
    projects = sorted(path.name.removesuffix(".project.json") for path in api_context.persistence.root.glob("*.project.json"))
    return {"projects": projects, "scope": "local-single-user", "tenant_model": "disabled"}


@router.get("/{project_id}", dependencies=[Depends(rate_limit_dependency)])
async def get_project(project_id: str = Path(min_length=1, max_length=128), api_context: APIContext = Depends(get_api_context), principal: Principal = Depends(require_permission("project.read"))) -> dict[str, object]:
    """Load one project payload after checksum verification."""
    try:
        payload, result = api_context.persistence.load(project_id)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="project not found") from exc
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="project state is unreadable or corrupt") from exc
    return {"project_id": project_id, "project": payload, "persistence": {"schema_version": result.schema_version, "checksum": result.checksum, "source": result.source}}


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(rate_limit_dependency)])
async def delete_project(project_id: str = Path(min_length=1, max_length=128), api_context: APIContext = Depends(get_api_context), principal: Principal = Depends(require_permission("project.write"))) -> None:
    """Delete one local project after API-level RBAC authorization."""
    if not api_context.persistence.exists(project_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="project not found")
    api_context.persistence.delete(project_id)
    api_context.audit_trail.record("api.project.delete", principal.username, {"project_id": project_id}, outcome="success", source="autonetarchitect.api")
    return None
