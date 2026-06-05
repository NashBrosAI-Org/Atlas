from fastapi import APIRouter, Depends, HTTPException

from app import tagging
from app.config import get_settings
from app.main_deps import get_sn
from app.models import TagAttach
from app.servicenow import ServiceNowClient

router = APIRouter(prefix="/api/tags", tags=["tags"])


def _scope() -> str:
    return get_settings().sn_scope


@router.get("")
async def list_tags(sn: ServiceNowClient = Depends(get_sn)) -> list[dict]:
    """The tag vocabulary, sorted by name."""
    tags = await sn.list(f"{_scope()}_tag")
    return sorted(tags, key=lambda t: t.get("name", "").casefold())


@router.get("/on/{target_table}/{target_id}")
async def tags_on_record(target_table: str, target_id: str,
                         sn: ServiceNowClient = Depends(get_sn)) -> list[dict]:
    return await tagging.tags_for(sn, _scope(), target_table, target_id)


@router.post("/on/{target_table}/{target_id}", status_code=201)
async def attach(target_table: str, target_id: str, body: TagAttach,
                 sn: ServiceNowClient = Depends(get_sn)) -> dict:
    return await tagging.attach_tag(sn, _scope(), body.name, target_table, target_id)


@router.delete("/on/{target_table}/{target_id}/{tag_id}")
async def detach(target_table: str, target_id: str, tag_id: str,
                 sn: ServiceNowClient = Depends(get_sn)) -> dict:
    removed = await tagging.detach_tag(sn, _scope(), tag_id, target_table, target_id)
    if not removed:
        raise HTTPException(status_code=404, detail="tag not attached to this record")
    return {"removed": True}
