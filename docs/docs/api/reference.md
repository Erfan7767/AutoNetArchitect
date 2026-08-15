# API reference

The API is a local FastAPI adapter with versioned routes under `/api/v1`. It is local-single-user in V1 and has no tenant identifier or cross-tenant authorization model.

## Health and metadata

| Method | Path | Meaning |
|---|---|---|
| `GET` | `/` | API metadata and local scope |
| `GET` | `/api/v1/health/live` | Process liveness |
| `GET` | `/api/v1/health/ready` | Local persistence/auth/audit readiness |
| `GET` | `/api/v1/health/version` | Version metadata |

Readiness is not network reachability, compliance certification, or production deployment approval.

## Authentication and projects

`POST /api/v1/auth/login` creates a local session and returns an opaque bearer token. `GET /api/v1/auth/me` reads the authenticated local identity. `POST /api/v1/auth/logout` revokes the current session. Project routes require the corresponding RBAC permission and use checksum-verified local persistence.

Client code must preserve structured workflow status, reasons, evidence IDs, audit IDs, and SoT record IDs. It must not infer success or readiness from an HTTP success status alone. A governed no-go result may be returned as a structured `blocked` outcome with HTTP success because the request was understood and policy-evaluated.

## Deployment routes

Deployment routes are adapters over the deployment orchestrator. Preparation and execution retain dry-run, approval, backup, verification, rollback, and audit boundaries. The API does not accept raw device passwords in normal request models and does not return secret values.

## Rate limits and errors

The V1 rate limiter is an in-memory fixed-window limiter for one local process. A distributed deployment requires an external gateway policy. Common response statuses are `401` for authentication failure, `403` for permission failure, `404` for missing resources, `409` for corrupt/conflicting state, `422` for validation errors, `429` for local rate limits, and `503` for readiness failure.
