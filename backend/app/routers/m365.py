from datetime import date, timedelta

from fastapi import APIRouter, Depends, HTTPException

from app import m365
from app.config import get_settings
from app.graph import GraphClient
from app.main_deps import get_graph, get_sn
from app.models import M365Payload
from app.servicenow import ServiceNowClient

router = APIRouter(prefix="/api/m365", tags=["m365"])


@router.post("/ingest")
async def ingest(payload: M365Payload,
                 sn: ServiceNowClient = Depends(get_sn)) -> dict:
    """Bridge ingest: accept Graph-shaped messages/events fetched *externally* (Claude
    + an approved M365 connector) and run the standard ingestion against ServiceNow —
    same normalize/match/dedup/flagged→task pipeline as /sync, but without Atlas needing
    its own Graph app registration (risk R3). Localhost-only, like the rest of the app."""
    return await m365.ingest_payload(sn, get_settings().sn_scope,
                                     messages=payload.messages, events=payload.events)


@router.post("/sync")
async def sync(sn: ServiceNowClient = Depends(get_sn),
               graph: GraphClient = Depends(get_graph)) -> dict:
    """Ingest mail from Graph into retained Email records + flagged-mail tasks."""
    return await m365.ingest_emails(graph, sn, get_settings().sn_scope)


@router.post("/calendar/sync")
async def calendar_sync(start: str | None = None, end: str | None = None,
                        sn: ServiceNowClient = Depends(get_sn),
                        graph: GraphClient = Depends(get_graph)) -> dict:
    """Ingest calendar events in [start, end] (default: today .. +30d) as Meetings.
    Defaults are full-day UTC bounds — a date-only end (e.g. "2026-07-04") would sort
    before that day's timestamped events and silently drop them."""
    start = start or date.today().isoformat() + "T00:00:00Z"
    end = end or (date.today() + timedelta(days=30)).isoformat() + "T23:59:59Z"
    return await m365.ingest_events(graph, sn, get_settings().sn_scope, start, end)


@router.get("/prep/{meeting_id}")
async def meeting_prep(meeting_id: str, sn: ServiceNowClient = Depends(get_sn)) -> dict:
    """Assemble a prep brief (meeting + client context) for an upcoming meeting."""
    prep = await m365.build_meeting_prep(sn, get_settings().sn_scope, meeting_id)
    if prep is None:
        raise HTTPException(status_code=404, detail=f"meeting {meeting_id} not found")
    return prep
