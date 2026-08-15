#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${ROOT_DIR}"
export PYTHONPATH="${ROOT_DIR}"
export AUTONET_RUNTIME_MODE="test"

if [[ "${1:-pytest}" == "regression" ]]; then
  for runner in /home/ubuntu/run_*_tests.py; do
    python3 "${runner}"
  done
else
  python3 -m pytest tests/unit tests/integration tests/e2e tests/chaos -v --tb=short -x
fi
