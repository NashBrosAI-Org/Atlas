from fastapi import APIRouter, Depends

from app import reminders
from app.config import get_settings
from app.main_deps import get_sn
from app.servicenow import ServiceNowClient

router = APIRouter(prefix="/api/reminders", tags=["reminders"])


@router.get("")
async def list_reminders(sn: ServiceNowClient = Depends(get_sn)) -> list[dict]:
    """KeyDates whose reminder window is open, soonest first."""
    return await reminders.due_reminders(sn, get_settings().sn_scope)
