from typing import Optional
from fastapi import APIRouter, Depends
from app.config import get_settings
from app.models import Task
from app.ordering import active_now_tasks
from app.servicenow import ServiceNowClient
from app.main_deps import get_sn

router = APIRouter(prefix="/api", tags=["tasks"])
_settings = get_settings()


def _table() -> str:
    return f"{_settings.sn_scope}_task"


@router.get("/tasks")
async def list_tasks(sn: ServiceNowClient = Depends(get_sn)) -> list[dict]:
    return await sn.list(_table())


@router.post("/tasks", status_code=201)
async def create_task(body: Task, sn: ServiceNowClient = Depends(get_sn)) -> dict:
    payload = body.model_dump(exclude_none=True, exclude={"sys_id"})
    return await sn.create(_table(), payload)


@router.patch("/tasks/{sys_id}")
async def update_task(sys_id: str, body: dict, sn: ServiceNowClient = Depends(get_sn)) -> dict:
    return await sn.update(_table(), sys_id, body)


@router.get("/now")
async def now_view(client: Optional[str] = None, sn: ServiceNowClient = Depends(get_sn)) -> list[dict]:
    query = {"client": client} if client else None
    return active_now_tasks(await sn.list(_table(), query=query))
