from fastapi import APIRouter, Depends

from app import backup, user_config
from app.config import get_settings
from app.main_deps import get_sn
from app.servicenow import ServiceNowClient

router = APIRouter(prefix="/api/backup", tags=["backup"])


@router.post("/export")
async def export(sn: ServiceNowClient = Depends(get_sn)) -> dict:
    """Write a full snapshot of every table to a timestamped file off-instance."""
    s = get_settings()
    path = await backup.write_export(sn, s.sn_scope)
    export = await backup.build_export(sn, s.sn_scope)
    return {"path": str(path), "created_at": export["created_at"], "counts": export["counts"]}


@router.get("/status")
def status() -> dict:
    """Last-backup time, snapshot count, and whether a backup is overdue."""
    s = get_settings()
    latest = backup.latest_backup_time()
    dest = user_config.backups_dir()
    count = len(list(dest.glob("atlas-backup-*.json"))) if dest.is_dir() else 0
    return {
        "last_backup": latest.strftime("%Y-%m-%dT%H:%M:%SZ") if latest else None,
        "count": count,
        "stale": backup.is_backup_stale(s.backup_max_age_days),
        "max_age_days": s.backup_max_age_days,
        "backups_dir": str(dest),
    }
