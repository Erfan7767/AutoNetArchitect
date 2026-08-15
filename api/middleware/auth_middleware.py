"""FastAPI authentication and RBAC dependencies."""
from __future__ import annotations

from typing import Callable

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from auth.rbac import PermissionDenied, Principal

from api.server import APIAuthenticationError, APIContext


bearer_scheme = HTTPBearer(auto_error=False)


def get_api_context(request: Request) -> APIContext:
    """Return the application API context."""
    context = getattr(request.app.state, "api_context", None)
    if not isinstance(context, APIContext):
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="API context is not initialized")
    return context


async def get_current_principal(request: Request, credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme)) -> Principal:
    """Verify the Bearer JWT and its local session backing record."""
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Bearer authentication is required", headers={"WWW-Authenticate": "Bearer"})
    context = get_api_context(request)
    try:
        principal = context.principal_from_token(credentials.credentials)
    except APIAuthenticationError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc), headers={"WWW-Authenticate": "Bearer"}) from exc
    request.state.principal = principal
    return principal


def require_permission(permission: str) -> Callable[..., Principal]:
    """Build a dependency enforcing one RBAC permission."""
    if not permission:
        raise ValueError("permission is required")

    async def dependency(request: Request, principal: Principal = Depends(get_current_principal)) -> Principal:
        """Enforce the selected permission for the authenticated principal."""
        context = get_api_context(request)
        try:
            context.rbac.enforce(principal, permission)
        except PermissionDenied as exc:
            context.audit_trail.record("api.authorization_denied", principal.username, {"permission": permission, "path": request.url.path}, outcome="blocked", source="autonetarchitect.api")
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="permission denied") from exc
        return principal

    return dependency


async def rate_limit_dependency(request: Request) -> None:
    """Apply the shared local rate limiter."""
    context = get_api_context(request)
    await context.rate_limiter.dependency(request)
