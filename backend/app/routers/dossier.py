from fastapi import APIRouter, Depends
from app.servicenow import ServiceNowClient
from app.main_deps import get_sn
from app.dossier import build_dossier

router = APIRouter(prefix="/api/clients", tags=["dossier"])


@router.get("/{sys_id}/dossier")
async def get_dossier(sys_id: str, sn: ServiceNowClient = Depends(get_sn)) -> dict:
    return await build_dossier(sn, sys_id)
