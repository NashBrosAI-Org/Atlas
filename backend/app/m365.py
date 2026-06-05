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
