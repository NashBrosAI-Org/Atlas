from fastapi import APIRouter, Depends, HTTPException

from app import awareness
from app.config import get_settings
from app.main_deps import get_sn
from app.servicenow import ServiceNowClient

router = APIRouter(prefix="/api/awareness", tags=["awareness"])


@router.get("/activity")
async def activity(limit: int = 50, sn: ServiceNowClient = Depends(get_sn)) -> list[dict]:
    return await awareness.recent_activity(sn, get_settings().sn_scope, limit=limit)


@router.get("/timeline/{client_id}")
async def timeline(client_id: str, sn: ServiceNowClient = Depends(get_sn)) -> list[dict]:
    tl = await awareness.build_timeline(sn, get_settings().sn_scope, client_id)
    if tl is None:
        raise HTTPException(status_code=404, detail=f"client {client_id} not found")
    return tl


@router.get("/radar")
async def radar(sn: ServiceNowClient = Depends(get_sn)) -> list[dict]:
    s = get_settings()
    return await awareness.stale_radar(sn, s.sn_scope, s.cooling_days, s.stale_days)
