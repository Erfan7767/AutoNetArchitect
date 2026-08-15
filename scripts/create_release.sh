#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${ROOT_DIR}"
VERSION="$(sed -n 's/^version = "\([^"]*\)"$/\1/p' pyproject.toml | head -n 1)"
if [[ -z "${VERSION}" ]]; then
  printf '%s\n' "Unable to determine package version." >&2
  exit 1
fi
if [[ "${1:-v${VERSION}}" != "v${VERSION}" ]]; then
  printf '%s\n' "Release argument must match v${VERSION}." >&2
  exit 1
fi
rm -rf build dist *.egg-info
python3 -m build
python3 -m twine check dist/*
sha256sum dist/* > dist/SHA256SUMS.txt
printf '%s\n' "Release artifacts built for v${VERSION}; publication remains an explicit hosting-platform action."
