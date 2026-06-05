from typing import Optional, Type
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from app.config import get_settings
from app.servicenow import ServiceNowClient
from app.main_deps import get_sn

_settings = get_settings()


def crud_router(name: str, table_suffix: str, model: Type[BaseModel]) -> APIRouter:
    router = APIRouter(prefix=f"/api/{name}", tags=[name])

    def table() -> str:
        return f"{_settings.sn_scope}_{table_suffix}"

    @router.get("")
    async def list_records(client: Optional[str] = None, sn: ServiceNowClient = Depends(get_sn)) -> list[dict]:
        query = {"client": client} if client else None
        return await sn.list(table(), query=query)

    @router.post("", status_code=201)
    async def create_record(body: model, sn: ServiceNowClient = Depends(get_sn)) -> dict:  # type: ignore[valid-type]
        payload = body.model_dump(exclude_none=True, exclude={"sys_id"})
        return await sn.create(table(), payload)

    @router.get("/{sys_id}")
    async def get_record(sys_id: str, sn: ServiceNowClient = Depends(get_sn)) -> dict:
        rec = await sn.get(table(), sys_id)
        if rec is None:
            raise HTTPException(status_code=404, detail=f"{name} {sys_id} not found")
        return rec

    @router.patch("/{sys_id}")
    async def patch_record(sys_id: str, body: dict, sn: ServiceNowClient = Depends(get_sn)) -> dict:
        return await sn.update(table(), sys_id, body)

    @router.delete("/{sys_id}")
    async def delete_record(sys_id: str, sn: ServiceNowClient = Depends(get_sn)) -> dict:
        if not await sn.delete(table(), sys_id):
            raise HTTPException(status_code=404, detail=f"{name} {sys_id} not found")
        return {"deleted": True}

    return router
