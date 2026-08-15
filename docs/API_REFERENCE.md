# AutoNetArchitect V1 API Reference

## API contract

The API is a local, versioned FastAPI adapter. All business workflows are delegated to the existing orchestrators and service boundaries. The API does not contain design algorithms, vendor command generation, transport logic, or an approval bypass.

The base versioned prefix is `/api/v1`. Interactive documentation is available at `/docs` when the local API is running. The API is single-user in V1 and does not expose tenant identifiers, tenant switching, or cross-tenant authorization.

## Metadata and health

| Method | Path | Authentication | Purpose |
|---|---|---|---|
| `GET` | `/` | None | API name, version, and local-scope declaration |
| `GET` | `/api/v1/health/live` | None | Process liveness |
| `GET` | `/api/v1/health/ready` | None | Local persistence, audit, and auth-store readiness |
| `GET` | `/api/v1/health/version` | None | API and application version metadata |
| `GET` | `/api/v1/health/audit` | `audit.read` | Read-only audit-chain health |

Readiness indicates that local stores and the audit chain are available. It does not indicate network reachability, device readiness, compliance certification, or production deployment approval.

## Authentication

### Login

```http
POST /api/v1/auth/login
Content-Type: application/json

{"username":"admin","password":"<entered interactively>"}
```

A successful response contains an opaque bearer token, token type, expiry duration, and non-secret user metadata. Passwords are never returned. Invalid credentials return `401`.

```json
{
  "access_token": "<JWT>",
  "token_type": "bearer",
  "expires_in": 3600,
  "user": {"username": "admin", "roles": ["admin"]}
}
```

### Session endpoints

`POST /api/v1/auth/logout` revokes the current local session and returns `204`. `GET /api/v1/auth/me` returns the authenticated username, roles, session-presence metadata, and the fixed `local-single-user` scope. Both require a valid bearer token.

JWTs are HMAC-SHA256 tokens bound to a local session record. The signing key is generated and stored below `AUTONET_API_ROOT` when the application initializes its default context. The key is not accepted from query parameters or returned by an endpoint.

## Project endpoints

Project endpoints use local-first persistence and checksum verification.

| Method | Path | Permission | Purpose |
|---|---|---|---|
| `POST` | `/api/v1/projects` | `project.write` | Create a local project through the master orchestrator boundary |
| `GET` | `/api/v1/projects` | `project.read` | List local project identifiers |
| `GET` | `/api/v1/projects/{project_id}` | `project.read` | Load a checksum-verified project |
| `DELETE` | `/api/v1/projects/{project_id}` | `project.write` | Delete a local project after authorization |

The create body is intentionally small and does not invent site facts:

```json
{
  "name": "EnterpriseGreenfield",
  "sector": "enterprise_corporate",
  "description": "Human-supplied project description"
}
```

A project can exist while still being incomplete, blocked, or awaiting human inputs. Project creation is not design approval.

## Deployment endpoints

Deployment routes are thin adapters over `DeploymentOrchestrator`.

| Method | Path | Permission | Purpose |
|---|---|---|---|
| `GET` | `/api/v1/projects/{project_id}/deployment/status` | `project.read` | Read persisted workflow and deployment state |
| `POST` | `/api/v1/projects/{project_id}/deployment/prepare` | `deployment.preview` | Prepare a deployment artifact and apply preconditions |
| `POST` | `/api/v1/projects/{project_id}/deployment/execute` | `deployment.execute` | Execute a dry-run or governed execution path |

Preparation accepts artifact references, transport metadata, evidence IDs, and optional approval reference. It does not open a device transport. Real execution requires the orchestrator's project, SoT, approval, evidence, backup, and remote-destructive gates.

Execution accepts an execution-result reference, `real_execution`, backup reference, evidence IDs, project validity, unresolved human inputs, and explicit destructive approval metadata. The route returns a structured orchestrator result, including status, success, reasons, artifact IDs, SoT record ID, audit entry ID, and generated timestamp. It does not return secrets or raw driver output.

## Rate limiting

The V1 limiter is an in-memory, fixed-window limiter intended for one local API process. A limited request returns `429 Too Many Requests` with a `Retry-After` header. It is not a distributed limiter and is not a replacement for an organization-wide gateway or WAF.

## Error semantics

| Status | Meaning |
|---:|---|
| `400` | Input is syntactically valid but violates a local request contract |
| `401` | Missing, invalid, expired, or revoked bearer authentication |
| `403` | Authenticated principal lacks the required permission |
| `404` | Project or requested local resource does not exist |
| `409` | Project state is corrupt, conflicting, or otherwise not safely readable |
| `422` | FastAPI/Pydantic request validation failed |
| `429` | Local rate limit exceeded |
| `503` | Local readiness checks failed |

A workflow-level no-go is normally returned as HTTP success with an orchestrator result whose `status` is `blocked` and `success` is `false`, because the request was understood and governed. Clients must inspect the structured result rather than infer readiness from HTTP status alone.

## Client responsibilities

Clients must preserve `result_id`, `workflow_id`, project ID, SoT record ID, audit entry ID, evidence IDs, and reasons. Clients must not retry destructive operations automatically, must not suppress blocked reasons, and must not treat dry-run or lab results as proof of production safety.
