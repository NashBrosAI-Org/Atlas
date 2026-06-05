from fastapi import APIRouter, Depends

from app import briefing
from app.config import get_settings
from app.main_deps import get_sn
from app.servicenow import ServiceNowClient

router = APIRouter(prefix="/api/briefing", tags=["briefing"])


@router.get("")
async def get_briefing(sn: ServiceNowClient = Depends(get_sn)) -> dict:
    """The day at a glance: Now tasks, today's meetings, reminders, radar."""
    s = get_settings()
    return await briefing.build_briefing(sn, s.sn_scope,
                                         cooling_days=s.cooling_days, stale_days=s.stale_days)
