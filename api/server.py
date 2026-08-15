"""FastAPI application foundation and local authentication context."""
from __future__ import annotations

import base64
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
import hashlib
import hmac
import json
import os
from pathlib import Path
import secrets
from typing import Any, Mapping

from fastapi import FastAPI

from audit.audit_trail import AuditTrail
from auth.auth_manager import AuthManager, AuthenticationError
from auth.rbac import Principal, RBAC
from auth.session_manager import SessionError, SessionManager
from orchestrators import DeploymentOrchestrator, DesignOrchestrator, MasterOrchestrator, OperationsOrchestrator, WorkflowContext, WorkflowStage
from persistence.project_persistence import ProjectPersistence
from source_of_truth.sot_manager import SoTManager

from .middleware.rate_limiter import RateLimiter


class APIAuthenticationError(RuntimeError):
    """Raised for invalid or expired local API tokens."""


@dataclass(frozen=True)
class APISettings:
    """Local V1 API settings with no tenant dimension."""

    root: Path
    jwt_secret: bytes
    jwt_ttl_seconds: int = 3600
    rate_limit: int = 60
    rate_window_seconds: int = 60

    @classmethod
    def from_root(cls, root: str | Path, *, jwt_secret: str | bytes | None = None, jwt_ttl_seconds: int = 3600, rate_limit: int = 60, rate_window_seconds: int = 60) -> "APISettings":
        """Create settings and persist a local HMAC key when none is supplied."""
        directory = Path(root)
        directory.mkdir(parents=True, exist_ok=True)
        key_path = directory / "api_jwt_secret"
        if jwt_secret is None:
            if key_path.exists():
                secret_value = key_path.read_bytes()
            else:
                secret_value = secrets.token_bytes(32)
                key_path.write_bytes(secret_value)
                key_path.chmod(0o600)
        elif isinstance(jwt_secret, str):
            secret_value = jwt_secret.encode("utf-8")
        else:
            secret_value = bytes(jwt_secret)
        if len(secret_value) < 32:
            raise ValueError("jwt_secret must contain at least 32 bytes")
        if jwt_ttl_seconds <= 0 or jwt_ttl_seconds > 86400:
            raise ValueError("jwt_ttl_seconds must be between 1 and 86400")
        if rate_limit <= 0 or rate_window_seconds <= 0:
            raise ValueError("rate limit and rate window must be positive")
        return cls(directory, secret_value, jwt_ttl_seconds, rate_limit, rate_window_seconds)


class APIContext:
    """Shared local API dependency container."""

    def __init__(self, settings: APISettings) -> None:
        """Initialize local auth, persistence, audit, and orchestrator dependencies."""
        self.settings = settings
        self.root = settings.root
        self.audit_trail = AuditTrail(self.root / "audit.jsonl")
        self.rbac = RBAC()
        self.auth_manager = AuthManager(self.root / "users.json", rbac=self.rbac, audit_trail=self.audit_trail)
        self.session_manager = SessionManager(self.root / "sessions.json")
        self.persistence = ProjectPersistence(self.root / "projects")
        self.sot_manager = SoTManager(self.root / "sot.json")
        self.master = MasterOrchestrator(sot_manager=self.sot_manager, audit_trail=self.audit_trail)
        self.design = DesignOrchestrator(master=self.master)
        self.deployment = DeploymentOrchestrator(master=self.master)
        self.operations = OperationsOrchestrator(master=self.master)
        self.rate_limiter = RateLimiter(settings.rate_limit, settings.rate_window_seconds)

    def authenticate(self, username: str, password: str) -> dict[str, Any]:
        """Authenticate local credentials and issue a signed JWT bound to a session."""
        principal = self.auth_manager.authenticate(username, password)
        session = self.session_manager.create(principal, ttl_seconds=self.settings.jwt_ttl_seconds)
        now = datetime.now(timezone.utc)
        claims = {"sub": principal.username, "roles": list(principal.roles), "sid": session.session_id, "iat": int(now.timestamp()), "exp": int(now.timestamp()) + self.settings.jwt_ttl_seconds, "scope": "local-single-user"}
        token = encode_jwt(claims, self.settings.jwt_secret)
        return {"access_token": token, "token_type": "bearer", "expires_in": self.settings.jwt_ttl_seconds, "user": {"username": principal.username, "roles": list(principal.roles)}}

    def principal_from_token(self, token: str) -> Principal:
        """Verify JWT signature and the backing local session."""
        claims = decode_jwt(token, self.settings.jwt_secret)
        username = claims.get("sub")
        session_id = claims.get("sid")
        roles = claims.get("roles")
        if not isinstance(username, str) or not isinstance(session_id, str) or not isinstance(roles, list):
            raise APIAuthenticationError("token claims are incomplete")
        try:
            principal = self.session_manager.validate(session_id)
        except SessionError as exc:
            raise APIAuthenticationError("session is invalid or expired") from exc
        if principal.username != username or tuple(principal.roles) != tuple(str(item) for item in roles):
            raise APIAuthenticationError("token and session claims do not match")
        return Principal(principal.username, principal.roles, session_id)

    def logout(self, principal: Principal) -> None:
        """Revoke the local session associated with a principal."""
        if principal.session_id:
            self.session_manager.revoke(principal.session_id)
        self.audit_trail.record("api.logout", principal.username, {"session_id_present": principal.session_id is not None}, outcome="success", source="autonetarchitect.api")

    def create_project(self, project_id: str, actor: str, sector: str | None, description: str) -> dict[str, Any]:
        """Create a local project and initialize its workflow context."""
        context = self.master.create_context(project_id=project_id, actor=actor)
        payload = {"project_id": project_id, "name": project_id, "sector": sector, "description": description, "status": "active", "workflow_context": context.to_dict()}
        result = self.persistence.save(project_id, payload)
        self.audit_trail.record("api.project.create", actor, {"project_id": project_id, "sector": sector, "checksum": result.checksum}, outcome="success", source="autonetarchitect.api")
        return {"project_id": project_id, "checksum": result.checksum, "workflow_id": context.workflow_id, "status": "active"}

    def load_context(self, project_id: str) -> tuple[dict[str, Any], WorkflowContext]:
        """Load a project and its persisted orchestration context."""
        payload, _result = self.persistence.load(project_id)
        raw_context = payload.get("workflow_context")
        if isinstance(raw_context, dict):
            return payload, WorkflowContext.from_dict(raw_context)
        context = self.master.create_context(project_id=project_id, actor="api")
        payload["workflow_context"] = context.to_dict()
        self.persistence.save(project_id, payload)
        return payload, context

    def save_context(self, project_id: str, payload: dict[str, Any], context: WorkflowContext) -> None:
        """Persist a workflow context after an orchestrator operation."""
        payload["workflow_context"] = context.to_dict()
        self.persistence.save(project_id, payload)


def create_app(api_context: APIContext | None = None) -> FastAPI:
    """Create the versioned FastAPI application."""
    from .routes.auth import router as auth_router
    from .routes.deployment import router as deployment_router
    from .routes.health import router as health_router
    from .routes.projects import router as projects_router

    default_root = Path(os.environ.get("AUTONET_API_ROOT", str(Path.home() / ".autonetarchitect-api")))
    context = api_context or APIContext(APISettings.from_root(default_root))
    application = FastAPI(title="AutoNetArchitect API", version="0.1.0", docs_url="/docs", redoc_url="/redoc")
    application.state.api_context = context
    application.include_router(auth_router, prefix="/api/v1")
    application.include_router(projects_router, prefix="/api/v1")
    application.include_router(deployment_router, prefix="/api/v1")
    application.include_router(health_router, prefix="/api/v1")

    @application.get("/", tags=["meta"])
    async def root() -> dict[str, Any]:
        """Return API metadata and local-scope declaration."""
        return {"name": "AutoNetArchitect API", "version": "v1", "scope": "local-single-user", "multi_tenant": False}

    return application


def encode_jwt(claims: Mapping[str, Any], secret: bytes) -> str:
    """Create an HS256 JWT using only the Python standard library."""
    header = {"alg": "HS256", "typ": "JWT"}
    encoded_header = _b64url(json.dumps(header, sort_keys=True, separators=(",", ":")).encode("utf-8"))
    encoded_claims = _b64url(json.dumps(dict(claims), sort_keys=True, separators=(",", ":")).encode("utf-8"))
    unsigned = f"{encoded_header}.{encoded_claims}".encode("ascii")
    signature = hmac.new(secret, unsigned, hashlib.sha256).digest()
    return f"{encoded_header}.{encoded_claims}.{_b64url(signature)}"


def decode_jwt(token: str, secret: bytes) -> dict[str, Any]:
    """Verify and decode an HS256 JWT with strict algorithm and expiry checks."""
    if not isinstance(token, str):
        raise APIAuthenticationError("token must be a string")
    parts = token.split(".")
    if len(parts) != 3:
        raise APIAuthenticationError("token format is invalid")
    try:
        header = json.loads(_b64url_decode(parts[0]).decode("utf-8"))
        claims = json.loads(_b64url_decode(parts[1]).decode("utf-8"))
        supplied = _b64url_decode(parts[2])
    except (ValueError, json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise APIAuthenticationError("token encoding is invalid") from exc
    if header.get("alg") != "HS256" or header.get("typ") != "JWT":
        raise APIAuthenticationError("token algorithm is not allowed")
    expected = hmac.new(secret, f"{parts[0]}.{parts[1]}".encode("ascii"), hashlib.sha256).digest()
    if not hmac.compare_digest(supplied, expected):
        raise APIAuthenticationError("token signature is invalid")
    try:
        expiry = int(claims.get("exp", 0)) if isinstance(claims, dict) else 0
    except (TypeError, ValueError):
        raise APIAuthenticationError("token expiry claim is invalid")
    if expiry <= int(datetime.now(timezone.utc).timestamp()):
        raise APIAuthenticationError("token is expired")
    return claims


def _b64url(value: bytes) -> str:
    """Encode bytes without padding."""
    return base64.urlsafe_b64encode(value).decode("ascii").rstrip("=")


def _b64url_decode(value: str) -> bytes:
    """Decode unpadded URL-safe base64."""
    return base64.urlsafe_b64decode(value + "=" * (-len(value) % 4))


app = create_app()


def main() -> None:
    """Run the local API with Uvicorn when the optional server entry point is used."""
    import uvicorn
    host = os.environ.get("AUTONET_API_HOST", "127.0.0.1")
    port = int(os.environ.get("AUTONET_API_PORT", "8000"))
    uvicorn.run("api.server:app", host=host, port=port, reload=False)
