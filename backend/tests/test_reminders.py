from datetime import date

import pytest

from app import reminders
from app.servicenow import FakeServiceNow

SCOPE = "x_atlas_sn"


@pytest.fixture
def sn() -> FakeServiceNow:
    return FakeServiceNow()


async def _seed_client(sn, name="Acme"):
    return (await sn.create(f"{SCOPE}_client", {"name": name}))["sys_id"]


async def test_due_reminders_only_within_lead_window(sn):
    cid = await _seed_client(sn)
    # Reminder lead 7 days; "today" is 2026-06-04.
    await sn.create(f"{SCOPE}_key_date", {
        "title": "Renewal", "type": "renewal", "date": "2026-06-09",
        "reminder_lead_days": "7", "client": cid})            # 5 days out → due
    await sn.create(f"{SCOPE}_key_date", {
        "title": "Far off", "type": "qbr", "date": "2026-08-01",
        "reminder_lead_days": "7", "client": cid})            # 58 days out → not yet
    await sn.create(f"{SCOPE}_key_date", {
        "title": "Passed", "type": "milestone", "date": "2026-05-01",
        "reminder_lead_days": "7", "client": cid})            # already past → gone

    due = await reminders.due_reminders(sn, SCOPE, today=date(2026, 6, 4))

    assert [r["title"] for r in due] == ["Renewal"]
    r = due[0]
    assert r["days_until"] == 5
    assert r["date"] == "2026-06-09"
    assert r["client"] == cid
    assert r["client_name"] == "Acme"


async def test_due_reminders_includes_day_of_and_sorts_soonest_first(sn):
    cid = await _seed_client(sn)
    await sn.create(f"{SCOPE}_key_date", {"title": "Today", "date": "2026-06-04",
                                          "reminder_lead_days": "3", "client": cid})
    await sn.create(f"{SCOPE}_key_date", {"title": "Tomorrow", "date": "2026-06-05",
                                          "reminder_lead_days": "3", "client": cid})

    due = await reminders.due_reminders(sn, SCOPE, today=date(2026, 6, 4))

    assert [r["title"] for r in due] == ["Today", "Tomorrow"]
    assert [r["days_until"] for r in due] == [0, 1]


async def test_due_reminders_skips_dateless_entries(sn):
    await _seed_client(sn)
    await sn.create(f"{SCOPE}_key_date", {"title": "No date", "reminder_lead_days": "7"})
    assert await reminders.due_reminders(sn, SCOPE, today=date(2026, 6, 4)) == []


async def test_recurring_rolls_to_next_annual_occurrence(sn):
    cid = await _seed_client(sn)
    # A birthday recorded in 2020; its 2026 anniversary (06-07) is 3 days out.
    await sn.create(f"{SCOPE}_key_date", {
        "title": "Jane bday", "type": "birthday", "date": "2020-06-07",
        "recurring": "true", "reminder_lead_days": "7", "client": cid})

    due = await reminders.due_reminders(sn, SCOPE, today=date(2026, 6, 4))

    assert len(due) == 1
    assert due[0]["days_until"] == 3
    assert due[0]["date"] == "2026-06-07"   # next anniversary, not the original year


async def test_non_recurring_past_date_is_not_resurrected(sn):
    cid = await _seed_client(sn)
    await sn.create(f"{SCOPE}_key_date", {
        "title": "One-off 2020", "date": "2020-06-07",
        "recurring": "false", "reminder_lead_days": "7", "client": cid})
    assert await reminders.due_reminders(sn, SCOPE, today=date(2026, 6, 4)) == []
