#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${ROOT_DIR}"
export PYTHONPATH="${ROOT_DIR}"
export AUTONET_RUNTIME_MODE="test"
python3 -m pytest tests/unit/ tests/ci/ --cov=autonetarchitect --cov-config=coverage_config/.coveragerc --cov-report=term-missing --cov-report=xml --cov-report=html
