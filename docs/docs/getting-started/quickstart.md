# Quickstart

## CLI

```bash
autonet --help
python -m autonetarchitect --help
```

Use the command-specific help before invoking a workflow stage. The CLI remains an adapter over orchestrators and services; it does not contain a separate design or deployment engine.

## API

```bash
export AUTONET_API_ROOT="$HOME/.autonetarchitect-api"
export AUTONET_API_HOST=127.0.0.1
export AUTONET_API_PORT=8000
PYTHONPATH="$PWD" python -m api.server
```

The local API is available at `http://127.0.0.1:8000/docs`. API versioned routes live under `/api/v1`. Authentication, RBAC, rate limiting, audit, and local-single-user boundaries remain active in development.

## Quality checks

```bash
make install-dev
make lint
make format-check
make typecheck
make test
make security
make docs
make build
```

A CI success means that the declared checks completed for the commit and environment. It does not approve a network change, certify compliance, or establish broad production safety.

## Safe workflow first action

For a new design, begin with human-supplied requirements and a dry-run or lab validation. Do not place device credentials in shell history, fixtures, issue reports, or CI variables unless the integration explicitly requires a protected secret and the organization's policy authorizes it. Real deployment remains supervised and governed by the project layers.
