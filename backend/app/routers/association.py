from fastapi import APIRouter, Depends

from app import association
from app.config import get_settings
from app.main_deps import get_sn
from app.servicenow import ServiceNowClient

router = APIRouter(prefix="/api/associations", tags=["associations"])


@router.get("")
async def associations(sn: ServiceNowClient = Depends(get_sn)) -> dict:
    return await association.list_associations(sn, get_settings().sn_scope)
