#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${ROOT_DIR}"
python3 scripts/check_docs_links.py
python3 -m mkdocs build --strict --config-file docs/mkdocs.yml
printf '%s\n' "Documentation site written to ${ROOT_DIR}/site."
