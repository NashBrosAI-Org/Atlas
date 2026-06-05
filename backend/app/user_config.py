"""Per-user persistence: non-secret settings in config.json, the SN password in
the macOS Keychain. Mirrors the small path logic from desktop/paths.py so the
backend has no import dependency on the desktop package."""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Optional

import keyring

_KEYRING_SERVICE = "atlas-sn"
_PASSWORD_KEY = "sn_password"


def _data_dir() -> Path:
    override = os.environ.get("ATLAS_DATA_DIR")
    if override:
        return Path(override)
    return Path.home() / "Library" / "Application Support" / "Atlas"


def _config_file() -> Path:
    return _data_dir() / "config.json"


def backups_dir() -> Path:
    """Where data snapshots are written (off-instance archive, CLAUDE.md rule #3)."""
    return _data_dir() / "backups"


def load_overlay() -> dict[str, Any]:
    """Non-secret settings the user saved, or {} if none yet."""
    path = _config_file()
    if not path.is_file():
        return {}
    try:
        return json.loads(path.read_text())
    except (json.JSONDecodeError, OSError):
        return {}


def save_config(values: dict[str, Any]) -> None:
    """Merge ``values`` into config.json (creating the dir/file as needed)."""
    path = _config_file()
    path.parent.mkdir(parents=True, exist_ok=True)
    current = load_overlay()
    current.update(values)
    path.write_text(json.dumps(current, indent=2))


def save_password(password: str) -> None:
    keyring.set_password(_KEYRING_SERVICE, _PASSWORD_KEY, password)


def get_password() -> Optional[str]:
    # Resilient on machines with no keyring backend (e.g. headless CI): treat a
    # missing backend as "no password stored" rather than crashing get_settings().
    try:
        return keyring.get_password(_KEYRING_SERVICE, _PASSWORD_KEY)
    except keyring.errors.KeyringError:
        return None


def clear_password() -> None:
    try:
        keyring.delete_password(_KEYRING_SERVICE, _PASSWORD_KEY)
    except keyring.errors.PasswordDeleteError:
        pass
