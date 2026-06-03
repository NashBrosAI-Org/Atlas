#!/usr/bin/env bash
# Build Atlas.app locally from this repo. Produces dist/Atlas.app.
# Requires Python 3.11+ and Node. Run from anywhere; resolves the repo root.
set -euo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO"

echo "==> Building frontend"
( cd frontend && npm ci && npm run build )

echo "==> Preparing build venv"
BUILD_VENV="$REPO/.build-venv"
python3.11 -m venv "$BUILD_VENV" 2>/dev/null || python3 -m venv "$BUILD_VENV"
"$BUILD_VENV/bin/pip" install -q --upgrade pip
"$BUILD_VENV/bin/pip" install -q -r desktop/requirements.txt

echo "==> Packaging Atlas.app"
rm -rf build dist
"$BUILD_VENV/bin/pyinstaller" --noconfirm desktop/Atlas.spec

echo "==> Done: $REPO/dist/Atlas.app"
