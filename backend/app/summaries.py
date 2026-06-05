"""AI summaries: assemble context from existing records and ask the AIClient to
summarize. Pure logic over AIClient + ServiceNowClient. Additive (rule #6) — the
app never depends on these; only /api/ai/* calls them."""
from typing import Optional

from app import dossier
from app.ai import AIClient
from app.servicenow import ServiceNowClient

_SYSTEM = ("You are an assistant to a client-services manager. Summarize the client "
           "concisely for someone about to engage them. The app's task prioritization is "
           "deterministic and authoritative; your summary is assistance, not direction.")


async def summarize_client(sn: ServiceNowClient, ai: AIClient, scope: str,
                           client_id: str) -> Optional[str]:
    record = await sn.get(f"{scope}_client", client_id)
    if record is None:
        return None
    doss = await dossier.build_dossier(sn, client_id)
    lines = [f"Client: {doss['client'].get('name', '')} (status {doss['client'].get('status', '')})"]
    lines.append("Open tasks: " + ("; ".join(t.get("title", "") for t in doss["open_tasks"]) or "none"))
    lines.append("Engagements: " + "; ".join(e.get("name", "") for e in doss["engagements"]))
    lines.append("Recent notes: " + "; ".join(n.get("title", "") for n in doss["notes"]))
    prompt = "\n".join(lines)
    return await ai.complete(system=_SYSTEM, prompt=prompt, max_tokens=512)
