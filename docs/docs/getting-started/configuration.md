# Configuration

## Environment files

`.env.example` documents local API settings without credential material. `.env.test` contains deterministic test paths and loopback ports only. Copy values into a local `.env` only when the deployment environment requires it; do not commit that file.

| Variable | Purpose | Safe V1 default |
|---|---|---|
| `AUTONET_API_ROOT` | API local state root | `./runtime-data/api` in the template; `$HOME/.autonetarchitect-api` when unset locally |
| `AUTONET_API_HOST` | API bind host | `127.0.0.1` |
| `AUTONET_API_PORT` | API port | `8000` |
| `AUTONET_API_URL` | Optional UI adapter API base URL | `http://127.0.0.1:8000` |
| `AUTONET_RUNTIME_MODE` | Wrapper/runtime context | `local-single-user` |
| `AUTONET_LOG_LEVEL` | Wrapper/test logging hint | `INFO` |
| `PYTHONPATH` | Local import path for runners | repository root |

The API signing key is generated and stored below `AUTONET_API_ROOT` by the local API context. V1 does not accept a raw signing key from `.env.example`; protect the state root and its backups instead. The template intentionally excludes `AUTONET_DATABASE_PATH`, vault-path, JWT-secret, CORS, SSH timeout/concurrency, feature-toggle, and cache-backend variables because the current V1 implementation does not read them as application configuration. Listing an environment variable is not sufficient evidence that a component supports it.

## Dependency groups

Runtime dependencies are installed from `requirements.txt`. CI and developer tools are installed from `requirements-dev.txt`. Optional reporting/UI/analysis packages are installed from `requirements-optional.txt`. MkDocs site packages are installed from `docs/requirements-docs.txt`. Keeping these groups separate prevents an optional integration from becoming an implicit runtime requirement.

## Configuration discipline

Configuration values that affect a network design or deployment must be sourced from the human, authoritative evidence, or an explicitly registered assumption. CI variables must not be used to fabricate ASNs, public prefixes, device identities, physical dimensions, power values, or credentials. Secret values must be supplied only through the approved secret boundary and must never be printed in logs or documentation artifacts.
