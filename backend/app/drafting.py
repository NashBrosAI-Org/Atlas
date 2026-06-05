"""AI drafting: compose a follow-up email from a client's context. Pure logic over
AIClient + ServiceNowClient. Additive (rule #6) — only /api/ai/* calls it; the
draft is a starting point the human edits and sends, never auto-sent."""
from typing import Optional

from app import dossier
from app.ai import AIClient
from app.servicenow import ServiceNowClient

_SYSTEM = ("You are drafting a short, professional follow-up email to a client on behalf of their "
           "account manager. Use the supplied context. Keep it concise and specific; reference open "
           "items and any upcoming key dates. Output only the email (subject + body), no preamble. "
           "Do not invent commitments or facts not in the context.")


async def draft_client_followup(sn: ServiceNowClient, ai: AIClient, scope: str,
                                client_id: str) -> Optional[str]:
    record = await sn.get(f"{scope}_client", client_id)
    if record is None:
        return None
    doss = await dossier.build_dossier(sn, client_id)
    lines = [f"Client: {doss['client'].get('name', '')}"]
    lines.append("Open tasks: " + ("; ".join(t.get("title", "") for t in doss["open_tasks"]) or "none"))
    lines.append("Key dates: " + ("; ".join(
        f"{k.get('title', '')} ({k.get('date', '')})" for k in doss["key_dates"]) or "none"))
    lines.append("Recent notes: " + ("; ".join(n.get("title", "") for n in doss["notes"]) or "none"))
    return await ai.complete(system=_SYSTEM, prompt="\n".join(lines), max_tokens=700)
