#!/usr/bin/env bash
# Atlas installer (macOS). Builds Atlas.app from THIS checkout and installs it to
# ~/Applications. No Apple Developer ID needed: building locally means macOS
# trusts the result (no Gatekeeper quarantine). Run from a checkout of the repo:
#   bash scripts/install.sh
set -euo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO"

echo "==> Atlas installer (macOS)"

# Node is needed for the frontend build (build-desktop.sh runs `npm ci`).
if ! command -v node >/dev/null 2>&1; then
  echo "ERROR: Node.js is required. Install it from https://nodejs.org (or 'brew install node')." >&2
  exit 1
fi

# Build dist/Atlas.app. build-desktop.sh selects a PyInstaller-compatible Python
# (3.10-3.13) and errors clearly if none is present.
bash scripts/build-desktop.sh

# Install into the user's Applications folder.
DEST="$HOME/Applications"
mkdir -p "$DEST"
rm -rf "$DEST/Atlas.app"
cp -R "$REPO/dist/Atlas.app" "$DEST/Atlas.app"

echo "==> Installed: $DEST/Atlas.app"
open "$DEST/Atlas.app"
echo "==> Launched. Find Atlas anytime in ~/Applications (or via Spotlight)."
echo "==> Next: in Atlas, open Help for setup, then Settings to connect your ServiceNow instance."
