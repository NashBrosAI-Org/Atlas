from fastapi import HTTPException
from app import tagging
from app.config import get_settings
from app.servicenow import ServiceNowClient

_settings = get_settings()


def _t(suffix: str) -> str:
    return f"{_settings.sn_scope}_{suffix}"


async def build_dossier(sn: ServiceNowClient, client_sys_id: str) -> dict:
    client = await sn.get(_t("client"), client_sys_id)
    if client is None:
        raise HTTPException(status_code=404, detail=f"client {client_sys_id} not found")

    by_client = {"client": client_sys_id}
    contacts = await sn.list(_t("contact"), query=by_client)
    engagements = await sn.list(_t("engagement"), query=by_client)
    themes = await sn.list(_t("theme"), query=by_client)
    tasks = await sn.list(_t("task"), query=by_client)
    meetings = await sn.list(_t("meeting"), query=by_client)
    key_dates = await sn.list(_t("key_date"), query=by_client)
    links = await sn.list(_t("link"), query=by_client)
    all_notes = await sn.list(_t("note"))

    open_tasks = [t for t in tasks if t.get("status") != "done"]
    notes = [n for n in all_notes
             if n.get("target_table") == "client" and n.get("target_id") == client_sys_id]
    tags = await tagging.tags_for(sn, _settings.sn_scope, "client", client_sys_id)

    return {
        "client": client,
        "contacts": contacts,
        "engagements": engagements,
        "themes": themes,
        "open_tasks": open_tasks,
        "meetings": meetings,
        "key_dates": sorted(key_dates, key=lambda k: k.get("date") or "9999-12-31"),
        "links": links,
        "notes": notes,
        "tags": tags,
    }
