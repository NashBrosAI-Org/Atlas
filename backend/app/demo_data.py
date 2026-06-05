"""Sample data for demo mode (USE_FAKE). Populates an in-memory FakeServiceNow so
the app looks alive on first run. Auto-invoked ONLY by the desktop launcher — it
never runs against the app's shared fake during tests, so other tests start empty.
(test_demo_data.py calls it directly against its own throwaway FakeServiceNow.)"""
from datetime import datetime, timedelta, timezone

from app.config import get_settings
from app.servicenow import ServiceNowClient


async def seed_demo(sn: ServiceNowClient) -> None:
    scope = get_settings().sn_scope

    def t(suffix: str) -> str:
        return f"{scope}_{suffix}"

    # Idempotent: if any clients already exist, assume seeded.
    if await sn.list(t("client")):
        return

    acme = await sn.create(t("client"), {"name": "Acme Corp", "short_code": "ACME",
                                         "status": "active", "email_domains": "acme.com"})
    globex = await sn.create(t("client"), {"name": "Globex", "short_code": "GLBX",
                                           "status": "active", "email_domains": "globex.com"})
    initech = await sn.create(t("client"), {"name": "Initech", "short_code": "INI",
                                            "status": "prospect"})

    await sn.create(t("task"), {"title": "Renewal proposal for Acme", "client": acme["sys_id"],
                                "priority": "critical", "due_date": "2026-06-10",
                                "is_commitment": True, "status": "open"})
    await sn.create(t("task"), {"title": "Follow up on Globex SSO ticket", "client": globex["sys_id"],
                                "priority": "high", "due_date": "2026-06-12", "status": "in_progress"})
    await sn.create(t("task"), {"title": "Send Initech onboarding deck", "client": initech["sys_id"],
                                "priority": "medium", "due_date": "2026-06-20", "status": "open"})
    await sn.create(t("task"), {"title": "Quarterly review prep — Acme", "client": acme["sys_id"],
                                "priority": "medium", "status": "open"})
    await sn.create(t("task"), {"title": "Archive old Globex tickets", "client": globex["sys_id"],
                                "priority": "low", "status": "waiting"})

    jane = await sn.create(t("contact"), {"name": "Jane Doe", "client": acme["sys_id"],
                                          "role_title": "VP Engineering", "email": "jane@acme.com",
                                          "sentiment": "champion"})
    await sn.create(t("contact"), {"name": "John Roe", "client": acme["sys_id"],
                                   "role_title": "Procurement", "email": "john@acme.com",
                                   "sentiment": "neutral", "reports_to": jane["sys_id"]})

    await sn.create(t("engagement"), {"name": "Acme Platform Rollout", "client": acme["sys_id"],
                                      "status": "on_track", "target_date": "2026-09-01"})
    await sn.create(t("theme"), {"name": "SSO migration", "client": globex["sys_id"],
                                 "status": "watching"})
    await sn.create(t("note"), {"title": "Acme renewal at risk if SSO slips", "note_type": "risk",
                                "target_table": "client", "target_id": acme["sys_id"], "pinned": True})

    # Key dates — two land inside the reminder window (computed relative to today so
    # the Awareness "Upcoming" panel always demonstrates), one is far off.
    today = datetime.now(timezone.utc).date()
    await sn.create(t("key_date"), {"title": "Acme contract renewal", "type": "renewal",
                                    "date": (today + timedelta(days=5)).isoformat(),
                                    "reminder_lead_days": "7", "client": acme["sys_id"]})
    await sn.create(t("key_date"), {"title": "Jane Doe birthday", "type": "birthday",
                                    "date": (today + timedelta(days=3)).isoformat(),
                                    "recurring": "true", "reminder_lead_days": "7",
                                    "client": acme["sys_id"], "contact": jane["sys_id"]})
    await sn.create(t("key_date"), {"title": "Globex QBR", "type": "qbr",
                                    "date": (today + timedelta(days=90)).isoformat(),
                                    "reminder_lead_days": "7", "client": globex["sys_id"]})

    await sn.create(t("link"), {"title": "Acme SharePoint", "url": "https://example.com/acme-sp",
                                "client": acme["sys_id"]})
    await sn.create(t("link"), {"title": "Globex Jira board", "url": "https://example.com/globex-jira",
                                "client": globex["sys_id"]})

    # Backdate two active clients so the stale-client radar visibly demonstrates in demo
    # mode (FakeServiceNow stamps sys_created_on from its clock). Demo-only; relies on the
    # fake's _clock, so guard for it.
    if hasattr(sn, "_clock"):
        original_clock = sn._clock
        now = datetime.now(timezone.utc)
        try:
            sn._clock = lambda: now - timedelta(days=20)  # cooling (>= 14 days quiet)
            wonka = await sn.create(t("client"), {"name": "Wonka Industries",
                                                  "short_code": "WONK", "status": "active"})
            await sn.create(t("task"), {"title": "Check in with Wonka", "client": wonka["sys_id"],
                                        "priority": "medium", "status": "open"})
            sn._clock = lambda: now - timedelta(days=45)  # stale (>= 30 days quiet)
            stark = await sn.create(t("client"), {"name": "Stark Solutions",
                                                  "short_code": "STRK", "status": "active"})
            await sn.create(t("task"), {"title": "Stark renewal — overdue touch",
                                        "client": stark["sys_id"], "priority": "high", "status": "open"})
        finally:
            sn._clock = original_clock


def seed_demo_graph(graph) -> None:
    """Seed the demo FakeGraph with synthetic mail + calendar so the M365 sync
    buttons and the morning briefing demonstrate in demo mode. Synthetic only —
    no corporate data (hard rule #1). Senders/attendees use the demo clients'
    domains (acme.com / globex.com) so association produces visible results."""
    if not hasattr(graph, "seed"):
        return
    now = datetime.now(timezone.utc)

    def iso(dt: datetime) -> str:
        return dt.strftime("%Y-%m-%dT%H:%M:%SZ")

    graph.seed(
        messages=[
            {"id": "demo-msg-1", "subject": "Renewal paperwork",
             "receivedDateTime": iso(now - timedelta(hours=2)),
             "from": {"emailAddress": {"address": "jane@acme.com", "name": "Jane Doe"}},
             "toRecipients": [{"emailAddress": {"address": "me@firm.com"}}],
             "body": {"contentType": "text", "content": "Can you send the renewal paperwork?"},
             "flag": {"flagStatus": "flagged"}},
            {"id": "demo-msg-2", "subject": "SSO ticket update",
             "receivedDateTime": iso(now - timedelta(days=1)),
             "from": {"emailAddress": {"address": "ops@globex.com"}},
             "toRecipients": [{"emailAddress": {"address": "me@firm.com"}}],
             "body": {"contentType": "text", "content": "Update on the SSO ticket."},
             "flag": {"flagStatus": "notFlagged"}},
        ],
        events=[
            {"id": "demo-evt-1", "subject": "Acme weekly sync",
             "start": {"dateTime": iso(now.replace(hour=15, minute=0, second=0, microsecond=0))},
             "attendees": [{"emailAddress": {"address": "jane@acme.com"}}], "isOnlineMeeting": True},
            {"id": "demo-evt-2", "subject": "Globex QBR",
             "start": {"dateTime": iso(now + timedelta(days=3))},
             "attendees": [{"emailAddress": {"address": "ops@globex.com"}}], "isOnlineMeeting": True},
        ],
    )
