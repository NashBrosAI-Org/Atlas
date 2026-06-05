"""Association review: list ingested emails & meetings with their auto-assigned
client so the user can confirm or correct the domain/alias matching. Pure logic
over the ServiceNowClient interface."""
from app.servicenow import ServiceNowClient


async def list_associations(sn: ServiceNowClient, scope: str, limit: int = 100) -> dict:
    clients = await sn.list(f"{scope}_client")
    name_by_id = {c["sys_id"]: c.get("name", "") for c in clients}

    def row(type_: str, rec: dict, label_field: str, who_field: str) -> dict:
        cid = rec.get("client", "") or ""
        return {"type": type_, "sys_id": rec.get("sys_id"),
                "label": rec.get(label_field, ""), "who": rec.get(who_field, ""),
                "client": cid, "client_name": name_by_id.get(cid, "")}

    emails = [row("email", e, "subject", "from_addr") for e in await sn.list(f"{scope}_email")]
    meetings = [row("meeting", m, "title", "attendees") for m in await sn.list(f"{scope}_meeting")]
    return {"emails": emails[:limit], "meetings": meetings[:limit]}
