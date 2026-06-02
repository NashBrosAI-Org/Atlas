from typing import Optional
from fastapi import APIRouter, Depends
from app.config import get_settings
from app.models import Task
from app.servicenow import ServiceNowClient
from app.main_deps import get_sn

router = APIRouter(prefix="/api", tags=["tasks"])
_settings = get_settings()

_PRIORITY_RANK = {"critical": 0, "high": 1, "medium": 2, "low": 3}


def _table() -> str:
    return f"{_settings.sn_scope}_task"


def _now_sort_key(t: dict):
    rank = _PRIORITY_RANK.get(t.get("priority", "medium"), 2)
    due = t.get("due_date") or "9999-12-31"
    commit = 0 if str(t.get("is_commitment")) in ("True", "true", "1") else 1
    return (rank, due, commit)


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
    rows = await sn.list(_table(), query=query)
    rows = [t for t in rows if t.get("status") != "done"]
    return sorted(rows, key=_now_sort_key)
