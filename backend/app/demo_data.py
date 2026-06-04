"""Sample data for demo mode (USE_FAKE). Populates an in-memory FakeServiceNow so
the app looks alive on first run. Called ONLY from the desktop launcher (never in
tests — the test suite relies on the fake starting empty)."""
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
