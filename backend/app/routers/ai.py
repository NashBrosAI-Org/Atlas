from fastapi import APIRouter, Depends, HTTPException

from app import drafting, extraction, summaries
from app.ai import AIClient
from app.config import get_settings
from app.main_deps import get_ai, get_sn
from app.servicenow import ServiceNowClient

router = APIRouter(prefix="/api/ai", tags=["ai"])


def _require_ai_enabled() -> None:
    """`ai_enabled` is the real switch, not just a UI hint — block the AI endpoints
    server-side when it's off so nothing reaches the (future) live model or spends
    tokens behind the user's back (rule #6)."""
    if not get_settings().ai_enabled:
        raise HTTPException(status_code=403, detail="AI is disabled (set ai_enabled)")


@router.get("/status")
def status() -> dict:
    s = get_settings()
    return {"enabled": s.ai_enabled, "model": s.anthropic_model}


@router.post("/summary/client/{client_id}")
async def summary_client(client_id: str, sn: ServiceNowClient = Depends(get_sn),
                         ai: AIClient = Depends(get_ai)) -> dict:
    _require_ai_enabled()
    out = await summaries.summarize_client(sn, ai, get_settings().sn_scope, client_id)
    if out is None:
        raise HTTPException(status_code=404, detail=f"client {client_id} not found")
    return {"summary": out}


@router.post("/draft/client/{client_id}")
async def draft_client(client_id: str, sn: ServiceNowClient = Depends(get_sn),
                       ai: AIClient = Depends(get_ai)) -> dict:
    _require_ai_enabled()
    out = await drafting.draft_client_followup(sn, ai, get_settings().sn_scope, client_id)
    if out is None:
        raise HTTPException(status_code=404, detail=f"client {client_id} not found")
    return {"draft": out}


@router.post("/extract/contact")
async def extract_contact(body: dict, ai: AIClient = Depends(get_ai)) -> dict:
    """Extract {name, role_title, email, phone} from an email signature (AI + regex)."""
    _require_ai_enabled()
    return await extraction.extract_contact_fields(ai, body.get("signature", ""))


@router.post("/summary/transcript/{transcript_id}")
async def summary_transcript(transcript_id: str, sn: ServiceNowClient = Depends(get_sn),
                             ai: AIClient = Depends(get_ai)) -> dict:
    _require_ai_enabled()
    out = await summaries.summarize_transcript(sn, ai, get_settings().sn_scope, transcript_id)
    if out is None:
        raise HTTPException(status_code=404, detail=f"transcript {transcript_id} not found")
    return {"summary": out}
