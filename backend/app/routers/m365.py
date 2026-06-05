from fastapi import APIRouter, Depends

from app import m365
from app.config import get_settings
from app.graph import GraphClient
from app.main_deps import get_graph, get_sn
from app.servicenow import ServiceNowClient

router = APIRouter(prefix="/api/m365", tags=["m365"])


@router.post("/sync")
async def sync(sn: ServiceNowClient = Depends(get_sn),
               graph: GraphClient = Depends(get_graph)) -> dict:
    """Ingest mail from Graph into retained Email records + flagged-mail tasks."""
    return await m365.ingest_emails(graph, sn, get_settings().sn_scope)
