"""Versioned local authentication routes."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, Field

from auth.auth_manager import AuthenticationError
from auth.rbac import Principal

from api.middleware.auth_middleware import get_api_context, get_current_principal, rate_limit_dependency
from api.server import APIContext


router = APIRouter(prefix="/auth", tags=["auth"])


class LoginRequest(BaseModel):
    """Local login request; password is never logged or returned."""

    username: str = Field(min_length=1, max_length=128)
    password: str = Field(min_length=12, max_length=512)


class LoginResponse(BaseModel):
    """Bearer token response."""

    access_token: str
    token_type: str
    expires_in: int
    user: dict[str, object]


@router.post("/login", response_model=LoginResponse, dependencies=[Depends(rate_limit_dependency)])
async def login(request: LoginRequest, api_context: APIContext = Depends(get_api_context)) -> dict[str, object]:
    """Authenticate a local user and return a signed short-lived JWT."""
    try:
        result = api_context.authenticate(request.username, request.password)
    except (AuthenticationError, ValueError) as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid username or password", headers={"WWW-Authenticate": "Bearer"}) from exc
    api_context.audit_trail.record("api.login", request.username, {"roles": result["user"]["roles"]}, outcome="success", source="autonetarchitect.api")
    return result


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(rate_limit_dependency)])
async def logout(principal: Principal = Depends(get_current_principal), api_context: APIContext = Depends(get_api_context)) -> None:
    """Revoke the current local session."""
    api_context.logout(principal)
    return None


@router.get("/me", dependencies=[Depends(rate_limit_dependency)])
async def me(principal: Principal = Depends(get_current_principal)) -> dict[str, object]:
    """Return authenticated principal metadata."""
    return {"username": principal.username, "roles": list(principal.roles), "session_id_present": principal.session_id is not None, "scope": "local-single-user"}
