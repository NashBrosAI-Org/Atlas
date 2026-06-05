"""Export/backup: dump every Atlas table to a single timestamped JSON snapshot.

The SN employee instance is NOT a durable archive (it can be reclaimed), so an
off-instance backup is mandatory — the instance must never be the only copy
(CLAUDE.md rule #3, risks R2/R3). Pure logic over the ServiceNowClient interface
so it is unit-tested against FakeServiceNow with an injected clock."""
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from app import user_config
from app.servicenow import ServiceNowClient

# The 14 modeled tables (short names; the scope prefix is applied per call), so a
# snapshot is the full data model — not just the wired-up subset.
TABLES = [
    "client", "engagement", "contact", "theme", "meeting", "transcript",
    "note", "task", "tag", "tag_m2m", "link", "key_date", "email", "deck",
]


def _iso(now: datetime) -> str:
    return now.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


async def build_export(sn: ServiceNowClient, scope: str,
                       now: Optional[datetime] = None) -> dict:
    """Read every table and return a self-describing snapshot dict."""
    now = now or datetime.now(timezone.utc)
    tables = {short: await sn.list(f"{scope}_{short}") for short in TABLES}
    counts = {short: len(rows) for short, rows in tables.items()}
    return {"created_at": _iso(now), "scope": scope, "tables": tables, "counts": counts}


async def write_export(sn: ServiceNowClient, scope: str,
                       now: Optional[datetime] = None) -> Path:
    """Build a snapshot and write it to a timestamped file in the backups dir."""
    now = now or datetime.now(timezone.utc)
    export = await build_export(sn, scope, now=now)
    dest = user_config.backups_dir()
    dest.mkdir(parents=True, exist_ok=True)
    stamp = now.astimezone(timezone.utc).strftime("%Y%m%d-%H%M%S")
    path = dest / f"atlas-backup-{stamp}.json"
    path.write_text(json.dumps(export, indent=2))
    return path


def _parse_stamp(name: str) -> Optional[datetime]:
    """`atlas-backup-YYYYMMDD-HHMMSS.json` → aware UTC datetime, else None."""
    stem = name.removeprefix("atlas-backup-").removesuffix(".json")
    try:
        return datetime.strptime(stem, "%Y%m%d-%H%M%S").replace(tzinfo=timezone.utc)
    except ValueError:
        return None


def latest_backup_time() -> Optional[datetime]:
    """Timestamp of the newest snapshot in the backups dir, or None if none exist."""
    dest = user_config.backups_dir()
    if not dest.is_dir():
        return None
    stamps = [_parse_stamp(p.name) for p in dest.glob("atlas-backup-*.json")]
    stamps = [s for s in stamps if s is not None]
    return max(stamps) if stamps else None


def is_backup_stale(max_age_days: int, now: Optional[datetime] = None) -> bool:
    """True when there is no backup, or the newest one is older than max_age_days."""
    now = now or datetime.now(timezone.utc)
    latest = latest_backup_time()
    if latest is None:
        return True
    return (now - latest).days >= max_age_days


async def autobackup_if_stale(sn: ServiceNowClient, scope: str, max_age_days: int,
                              now: Optional[datetime] = None) -> Optional[Path]:
    """Write a snapshot only if the newest backup is older than max_age_days (or
    none exists). The on-launch "scheduled" trigger — called from the desktop
    launcher so a recent off-instance copy always exists (risks R2/R3)."""
    now = now or datetime.now(timezone.utc)
    if not is_backup_stale(max_age_days, now):
        return None
    return await write_export(sn, scope, now=now)
