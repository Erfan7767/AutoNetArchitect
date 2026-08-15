#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${ROOT_DIR}"
python3 -m ruff check . --config pyproject.toml
python3 -m ruff format --check . --config pyproject.toml
