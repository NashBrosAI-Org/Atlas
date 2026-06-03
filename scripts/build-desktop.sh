#!/usr/bin/env bash
# Build Atlas.app locally from this repo. Produces dist/Atlas.app.
# Requires Python 3.10-3.13 (PyInstaller does not yet support 3.14) and Node.
# Run from anywhere; resolves the repo root.
set -euo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO"

echo "==> Building frontend"
( cd frontend && npm ci && npm run build )

echo "==> Preparing build venv"
BUILD_VENV="$REPO/.build-venv"
# PyInstaller (6.11.x) supports CPython 3.8-3.13 only, so pick a compatible
# interpreter and do NOT silently fall back to a too-new python3 (e.g. 3.14).
PYBIN=""
for c in python3.13 python3.12 python3.11 python3.10; do
  if command -v "$c" >/dev/null 2>&1; then PYBIN="$c"; break; fi
done
if [ -z "$PYBIN" ]; then
  echo "ERROR: need Python 3.10-3.13 for PyInstaller; none found (have $(python3 --version 2>&1))." >&2
  exit 1
fi
echo "    using $PYBIN ($("$PYBIN" --version 2>&1))"
"$PYBIN" -m venv "$BUILD_VENV"
"$BUILD_VENV/bin/pip" install -q --upgrade pip
"$BUILD_VENV/bin/pip" install -q -r desktop/requirements.txt

echo "==> Packaging Atlas.app"
rm -rf build dist
"$BUILD_VENV/bin/pyinstaller" --noconfirm desktop/Atlas.spec

echo "==> Done: $REPO/dist/Atlas.app"
