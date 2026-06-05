from fastapi import APIRouter, Depends
from app import search
from app.config import get_settings
from app.main_deps import get_sn
from app.servicenow import ServiceNowClient

router = APIRouter(prefix="/api/search", tags=["search"])


@router.get("")
async def do_search(q: str = "", limit: int = 50, types: str | None = None,
                    sn: ServiceNowClient = Depends(get_sn)) -> list[dict]:
    type_list = [t for t in types.split(",") if t] if types is not None else None
    return await search.search(sn, get_settings().sn_scope, q, limit=limit, types=type_list)
