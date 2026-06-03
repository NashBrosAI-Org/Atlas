"""Per-user filesystem locations for Atlas (writable, outside the read-only app
bundle). Override the base dir with ATLAS_DATA_DIR (used by tests)."""
from __future__ import annotations

import os
from pathlib import Path


def user_data_dir() -> Path:
    override = os.environ.get("ATLAS_DATA_DIR")
    if override:
        return Path(override)
    return Path.home() / "Library" / "Application Support" / "Atlas"


def config_file() -> Path:
    return user_data_dir() / "config.json"
