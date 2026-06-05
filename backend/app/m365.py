"""Microsoft 365 ingestion: turn Graph messages into retained Email records,
associate them to a client, and raise tasks from flagged mail. Pure logic over
the GraphClient + ServiceNowClient interfaces — unit-tested against FakeGraph +
FakeServiceNow. Retention of mail content in ServiceNow is the consciously-owned
risk R1/D2; keep the ingest filter narrow."""
from typing import Optional

from app.graph import GraphClient
from app.servicenow import ServiceNowClient


def _addr(holder: Optional[dict]) -> str:
    return (holder or {}).get("emailAddress", {}).get("address", "") if holder else ""


def normalize_message(msg: dict) -> dict:
    """Map a Graph message to an x_atlas_sn_email row (minus client/sys_id)."""
    recipients = msg.get("toRecipients") or []
    to_addr = ", ".join(_addr(r) for r in recipients if _addr(r))
    body = (msg.get("body") or {}).get("content") or msg.get("bodyPreview", "")
    return {
        "graph_message_id": msg.get("id", ""),
        "subject": msg.get("subject", ""),
        "from_addr": _addr(msg.get("from")),
        "to_addr": to_addr,
        "received_date": msg.get("receivedDateTime", ""),
        "body": body,
    }


def _domain(addr: str) -> str:
    return addr.split("@", 1)[1].lower() if "@" in addr else ""


def match_client(from_addr: str, clients: list[dict]) -> Optional[str]:
    """Return the sys_id of the client whose email_domains contains the sender's
    domain, else None. email_domains is a comma/space-separated list."""
    dom = _domain(from_addr)
    if not dom:
        return None
    for c in clients:
        domains = {d.strip().lower() for d in (c.get("email_domains") or "").replace(",", " ").split()}
        if dom in domains:
            return c.get("sys_id")
    return None


def _is_flagged(msg: dict) -> bool:
    return (msg.get("flag") or {}).get("flagStatus") == "flagged"


async def ingest_emails(graph: GraphClient, sn: ServiceNowClient, scope: str,
                        since: Optional[str] = None) -> dict:
    """Pull messages, retain new ones as Email records (idempotent on
    graph_message_id), associate by sender domain, and raise a Task from each
    flagged message. Returns counts."""
    existing = {e.get("graph_message_id") for e in await sn.list(f"{scope}_email")}
    clients = await sn.list(f"{scope}_client")

    ingested = skipped = tasks_created = 0
    for msg in await graph.list_messages(since=since):
        gid = msg.get("id", "")
        if not gid or gid in existing:
            skipped += 1
            continue
        row = normalize_message(msg)
        client_id = match_client(row["from_addr"], clients)
        if client_id:
            row["client"] = client_id
        await sn.create(f"{scope}_email", row)
        existing.add(gid)
        ingested += 1
        if _is_flagged(msg):
            task = {"title": f"Follow up: {row['subject']}", "source": "email",
                    "priority": "medium", "status": "open"}
            if client_id:
                task["client"] = client_id
            await sn.create(f"{scope}_task", task)
            tasks_created += 1
    return {"ingested": ingested, "skipped": skipped, "tasks_created": tasks_created}
