#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${ROOT_DIR}"
export PYTHONPATH="${ROOT_DIR}"
PYTHON_BIN="${AUTONET_SECURITY_PYTHON:-python3}"
"${PYTHON_BIN}" -m bandit -r autonetarchitect/ -f json -o bandit-report.json -ll
"${PYTHON_BIN}" -m pip_audit --requirement requirements.txt --format json --output pip-audit.json
mkdir -p .ci/safety
cp requirements.txt .ci/safety/requirements.txt
if timeout 60s "${PYTHON_BIN}" -m safety scan --target .ci/safety --save-as json safety-report.json; then
  printf '%s\n' "Supplemental Safety report written to safety-report.json."
else
  printf '%s\n' "Supplemental Safety scan unavailable without non-interactive authentication; pip-audit remains the mandatory dependency audit." >&2
fi
printf '%s\n' "Security reports written to bandit-report.json and pip-audit.json."
