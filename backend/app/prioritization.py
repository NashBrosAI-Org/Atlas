"""AI prioritization-assist: a brief, advisory focus suggestion over the open tasks.
Pure logic over AIClient. ADVISORY ONLY (rule #6) — it never writes priority,
reorders, or mutates tasks; the deterministic Now ordering stays authoritative."""
from app.ai import AIClient
from app.ordering import active_now_tasks
from app.servicenow import ServiceNowClient

_SYSTEM = ("You advise a client-services manager on what to focus on. The app's task ordering is "
           "deterministic and authoritative — you only suggest and explain, you never reorder or "
           "change priorities. Given the open tasks, give a brief focus for today (3-5 bullets), "
           "calling out commitments and imminent due dates. Do not invent tasks.")


async def suggest_focus(sn: ServiceNowClient, ai: AIClient, scope: str) -> str:
    tasks = active_now_tasks(await sn.list(f"{scope}_task"))
    lines = [
        f"- {t.get('title', '')} [priority={t.get('priority', '')}, "
        f"due={t.get('due_date') or '-'}, commitment={str(t.get('is_commitment')) in ('True', 'true', '1')}]"
        for t in tasks[:30]
    ]
    prompt = "Open tasks (deterministic order):\n" + ("\n".join(lines) or "none")
    return await ai.complete(system=_SYSTEM, prompt=prompt, max_tokens=500)
