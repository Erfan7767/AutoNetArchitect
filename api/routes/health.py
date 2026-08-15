"""Versioned health and readiness routes."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from auth.rbac import Principal

from api.middleware.auth_middleware import get_api_context, rate_limit_dependency, require_permission
from api.server import APIContext


router = APIRouter(prefix="/health", tags=["health"])


@router.get("/live", dependencies=[Depends(rate_limit_dependency)])
async def live() -> dict[str, object]:
    """Return process liveness without requiring credentials."""
    return {"status": "alive", "version": "v1", "scope": "local-single-user"}


@router.get("/ready", dependencies=[Depends(rate_limit_dependency)])
async def ready(api_context: APIContext = Depends(get_api_context)) -> dict[str, object]:
    """Check local persistence, audit integrity, and auth stores."""
    audit_integrity = api_context.audit_trail.verify_integrity()
    persistence_ready = api_context.persistence.root.exists()
    auth_ready = api_context.auth_manager.user_store_path.parent.exists()
    checks = {"audit_integrity": audit_integrity, "persistence": persistence_ready, "auth_store": auth_ready}
    if not all(checks.values()):
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail={"status": "not_ready", "checks": checks})
    return {"status": "ready", "checks": checks, "scope": "local-single-user", "multi_tenant": False}


@router.get("/version", dependencies=[Depends(rate_limit_dependency)])
async def version() -> dict[str, str]:
    """Return API version metadata."""
    return {"api": "v1", "application": "AutoNetArchitect", "version": "0.1.0"}


@router.get("/audit", dependencies=[Depends(rate_limit_dependency)])
async def audit_health(api_context: APIContext = Depends(get_api_context), principal: Principal = Depends(require_permission("audit.read"))) -> dict[str, object]:
    """Return protected audit-chain health metadata."""
    return {"audit_integrity": api_context.audit_trail.verify_integrity(), "entry_count": len(api_context.audit_trail.entries()), "read_only": True}
