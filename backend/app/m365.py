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
