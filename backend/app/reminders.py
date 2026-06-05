"""Reminders: surface KeyDates whose reminder window is open (today is within
`reminder_lead_days` of the date, and the date hasn't passed). Recurring dates
(renewals, birthdays) roll to their next annual occurrence. Pure logic over the
ServiceNowClient interface — unit-tested against FakeServiceNow with an injected
`today`."""
from datetime import date
from typing import Optional

from app.servicenow import ServiceNowClient


def _as_int(value, default: int) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _parse_date(s: str) -> Optional[date]:
    try:
        return date.fromisoformat(s.strip()[:10])
    except (TypeError, ValueError, AttributeError):
        return None


def _effective_date(d: date, recurring: bool, today: date) -> date:
    """The date the reminder counts down to: the literal date, or — for recurring
    dates — the next annual occurrence on/after today."""
    if not recurring:
        return d
    for year in (today.year, today.year + 1):
        try:
            occ = d.replace(year=year)
        except ValueError:  # Feb 29 in a non-leap year → use Feb 28
            occ = d.replace(year=year, day=28)
        if occ >= today:
            return occ
    return d


async def due_reminders(sn: ServiceNowClient, scope: str,
                        today: Optional[date] = None) -> list[dict]:
    today = today or date.today()
    clients = await sn.list(f"{scope}_client")
    name_by_id = {c["sys_id"]: c.get("name", "") for c in clients}

    out: list[dict] = []
    for kd in await sn.list(f"{scope}_key_date"):
        d = _parse_date(kd.get("date", ""))
        if d is None:
            continue
        recurring = str(kd.get("recurring")) in ("True", "true", "1")
        lead = _as_int(kd.get("reminder_lead_days"), 7)
        eff = _effective_date(d, recurring, today)
        days_until = (eff - today).days
        if 0 <= days_until <= lead:
            cid = kd.get("client", "")
            out.append({
                "sys_id": kd.get("sys_id"),
                "title": kd.get("title", ""),
                "type": kd.get("type", ""),
                "date": eff.isoformat(),
                "days_until": days_until,
                "recurring": recurring,
                "reminder_lead_days": lead,
                "client": cid,
                "client_name": name_by_id.get(cid, ""),
                "contact": kd.get("contact", ""),
            })
    out.sort(key=lambda r: r["days_until"])
    return out
