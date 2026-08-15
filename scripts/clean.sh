#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${ROOT_DIR}"
find . -type d -name '__pycache__' -prune -exec rm -rf {} +
find . -type f -name '*.pyc' -delete
rm -rf build dist *.egg-info .pytest_cache .mypy_cache .ruff_cache .tox .nox htmlcov site coverage.xml bandit-report.json pip-audit.json safety-report.json
printf '%s\n' "Generated development artifacts removed."
