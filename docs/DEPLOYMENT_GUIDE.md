# AutoNetArchitect V1 Deployment Guide

## Deployment posture

AutoNetArchitect V1 is released as a supervised engineering control plane. The supported deployment posture is local-first: one installation, one local state root, one local user model, and explicit human governance. The container and API examples in this guide are baselines for controlled environments, not a certification of the target host, network, or organizational process.

A deployment of AutoNetArchitect does not automatically authorize a network change. Network changes remain subject to the project workflow, review checkpoints, approval authority, backup requirements, verification evidence, rollback planning, and the target organization's change process.

## Installation from a source checkout

Use Python 3.11 or newer. Create an isolated virtual environment, install the runtime set, and install the project in editable mode only for development:

```bash
python3 -m venv .venv
. .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m pip install -e .
```

For development and release verification, install `requirements-dev.txt`. Optional Arabic shaping, additional rendering, analysis, and external UI integrations are isolated in `requirements-optional.txt`; they are not required for the V1 CLI, API, or framework-neutral UI shell.

## Local CLI

The console entry point is:

```bash
autonet --help
autonet system info --help
```

The equivalent module invocation is:

```bash
python -m autonetarchitect --help
```

The CLI stores local state through its configured context. Credentials are never passed as command arguments in release examples. Login sessions store opaque session metadata and audit events, not plaintext passwords.

## Local API

Start the API on loopback for a local workstation:

```bash
AUTONET_API_ROOT="$HOME/.autonetarchitect-api" \
AUTONET_API_HOST=127.0.0.1 \
AUTONET_API_PORT=8000 \
python -m api.server
```

The API is available at `http://127.0.0.1:8000`. The versioned route prefix is `/api/v1`. Liveness, readiness, and OpenAPI endpoints are:

```text
GET /api/v1/health/live
GET /api/v1/health/ready
GET /api/v1/health/version
GET /docs
GET /openapi.json
```

The first local API start creates `api_jwt_secret` beneath `AUTONET_API_ROOT` when no key is supplied programmatically. The file is created with restrictive permissions. Back up the complete state root using an approved local procedure; do not copy the key into `.env`, logs, reports, tickets, or shell history.

## Docker baseline

Build and start the local compose service:

```bash
docker compose build
docker compose up
```

The compose file binds port `8000` to `127.0.0.1` and stores application state in the named volume `autonetarchitect_state`. It runs as a non-root container user, drops capabilities, enables `no-new-privileges`, uses a read-only filesystem with a dedicated writable state volume, and exposes a liveness healthcheck.

For a controlled remote environment, do not simply change the bind address and call the result production-ready. Review TLS termination, network access controls, identity integration, secrets management, backup and restore, logging, monitoring, patching, and organizational approval responsibilities first. V1 does not provide multi-tenant isolation or a hosted identity plane.

## State and backup

The local state root includes authentication metadata, sessions, audit entries, project persistence, Source of Truth records, and the API signing key. Treat it as sensitive application state. Backups must be encrypted according to the target organization's policy, access controlled, integrity checked, and tested for restoration. Do not place the state root in a publicly shared directory.

A backup of application state is not the same as a network-device configuration backup. A network deployment requires its own device backup reference and verification evidence before real execution is permitted by the deployment layer.

## Network deployment readiness

Before a real deployment path can be considered for human approval, the workflow must have a valid project state, resolved human-mandatory inputs affecting execution, authoritative design and deployment SoT records, required evidence, explicit approval references, a backup reference, and a verification/rollback plan. Remote-destructive operations remain blocked unless the specific policy and explicit human approval path allow them.

The safe first action for a new environment is a dry-run or lab validation. A lab result is validation evidence; it is not a replacement for production change control, field verification, or post-deployment acceptance.

## Recovery and rollback

If the application state is corrupt, stop using the affected state root and preserve the original copy for investigation. Restore from an integrity-verified backup through the local persistence procedures. Do not manually edit checksums or SoT records to force readiness.

For network changes, use the recorded rollback scope and device backup references. A rollback result must be recorded as an outcome with evidence; merely generating rollback commands is not proof that rollback succeeded.

## Release acceptance checklist

| Area | Required evidence |
|---|---|
| Installation | Reproducible dependency installation and package build output |
| Authentication | Local user, role, session, logout, and failed-login behavior tested |
| State | Save/load roundtrip, checksum verification, and backup/restore test |
| Governance | Review/approval/no-go behavior verified for the target workflow |
| Deployment | Dry-run, backup gate, real-execution approval, verification, and rollback evidence |
| Security | Secret redaction, restricted state root, non-root container, and audit integrity |
| Testing | Unit, integration, E2E, performance, chaos, and regression results recorded |
| Operations | Read-only monitoring baseline and explicit change authorization for mutations |

Passing this checklist supports a release review. It does not constitute a regulatory certification or a universal production-safe claim.

## Multi-stage container details

The release `Dockerfile` uses a Python 3.11 builder stage for native build dependencies and a separate Python 3.11 runtime stage. The runtime stage installs only the declared runtime image dependency `graphviz`, copies the built Python installation, retains the V1 API/CLI source boundary and non-packaged `data/` catalog, and runs as the dedicated non-root `autonet` user with UID/GID 10001.

The default container command is `python -m uvicorn api.server:app --host 0.0.0.0 --port 8000`, which starts the implemented local FastAPI server using the `AUTONET_API_ROOT` state volume. The container healthcheck calls `GET /api/v1/health/live` over loopback. The image may be used for a CLI smoke check by overriding the command, for example:

```bash
docker run --rm autonetarchitect:0.1.0 autonet --help
```

Overriding the command for a CLI check does not start the API and therefore should not be used as an API service deployment. Compose remains the supported local API service path and adds the read-only root filesystem, dropped capabilities, `no-new-privileges`, localhost bind, and dedicated state volume. The Dockerfile itself provides the image baseline; host hardening and Compose runtime controls remain separately required.

## Compose API and optional UI services

The main `docker-compose.yml` defines two local services. The `api` service uses the release image and persists the complete API state root at `/var/lib/autonetarchitect`. Its port is bound to `127.0.0.1:8000` by default, and its healthcheck uses the implemented versioned route `/api/v1/health/live` rather than an unimplemented `/health` path.

The `ui` service is an optional Streamlit adapter built from the same Dockerfile with `INSTALL_EXTRAS=optional`. It runs `ui/streamlit_app.py`, binds `127.0.0.1:8501`, waits for API liveness, and performs only a read-only liveness/scope presentation. It does not duplicate orchestrator logic and does not bypass API authentication, RBAC, approval, audit, backup, verification, or rollback gates. The optional UI image is therefore a convenience adapter, not an independent execution plane.

The Compose configuration intentionally uses the implemented API state root rather than an `AUTONET_DATABASE_PATH` setting. V1 API persistence is local file-based under `AUTONET_API_ROOT`; an environment variable that is not consumed by the application would create a misleading source-of-truth claim. The Compose file binds both services to loopback, uses read-only root filesystems, drops all capabilities, enables `no-new-privileges`, and provides temporary writable space only through `/tmp`.
