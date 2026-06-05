from fastapi import APIRouter, Depends
from app.config import get_settings
from app.models import Client
from app.servicenow import ServiceNowClient
from app.main_deps import get_sn

router = APIRouter(prefix="/api/clients", tags=["clients"])
_settings = get_settings()


def _table() -> str:
    return f"{_settings.sn_scope}_client"


@router.get("")
async def list_clients(sn: ServiceNowClient = Depends(get_sn)) -> list[dict]:
    return await sn.list(_table())


@router.post("", status_code=201)
async def create_client(body: Client, sn: ServiceNowClient = Depends(get_sn)) -> dict:
    payload = body.model_dump(exclude_none=True, exclude={"sys_id"})
    return await sn.create(_table(), payload)


@router.patch("/{sys_id}")
async def update_client(sys_id: str, body: dict, sn: ServiceNowClient = Depends(get_sn)) -> dict:
    return await sn.update(_table(), sys_id, body)
