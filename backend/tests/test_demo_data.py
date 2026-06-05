import pytest

from app.servicenow import FakeServiceNow
from app.demo_data import seed_demo
from app.config import get_settings


def _t(suffix: str) -> str:
    return f"{get_settings().sn_scope}_{suffix}"


@pytest.mark.asyncio
async def test_seed_populates_clients_and_tasks():
    fake = FakeServiceNow()
    await seed_demo(fake)
    clients = await fake.list(_t("client"))
    tasks = await fake.list(_t("task"))
    assert len(clients) >= 3
    assert len(tasks) >= 4
    # tasks reference real client sys_ids
    client_ids = {c["sys_id"] for c in clients}
    assert all(t["client"] in client_ids for t in tasks if t.get("client"))


@pytest.mark.asyncio
async def test_seed_is_idempotent():
    fake = FakeServiceNow()
    await seed_demo(fake)
    n = len(await fake.list(_t("client")))
    await seed_demo(fake)  # second call must not duplicate
    assert len(await fake.list(_t("client"))) == n


@pytest.mark.asyncio
async def test_seed_dossier_shape_for_first_client():
    fake = FakeServiceNow()
    await seed_demo(fake)
    clients = await fake.list(_t("client"))
    cid = clients[0]["sys_id"]
    # at least one client has contacts + a pinned client note (so the dossier looks alive)
    contacts_any = False
    for c in clients:
        if await fake.list(_t("contact"), {"client": c["sys_id"]}):
            contacts_any = True
            break
    notes = await fake.list(_t("note"))
    assert contacts_any
    assert any(n.get("target_table") == "client" for n in notes)


@pytest.mark.asyncio
async def test_seed_produces_radar_flaggable_clients():
    from app.awareness import stale_radar

    fake = FakeServiceNow()
    await seed_demo(fake)
    radar = await stale_radar(fake, get_settings().sn_scope, cooling_days=14, stale_days=30)
    tiers = {r["client_name"]: r["tier"] for r in radar}
    assert tiers.get("Stark Solutions") == "stale"
    assert tiers.get("Wonka Industries") == "cooling"


@pytest.mark.asyncio
async def test_seed_produces_due_reminders():
    from app.reminders import due_reminders

    fake = FakeServiceNow()
    await seed_demo(fake)
    rems = await due_reminders(fake, get_settings().sn_scope)
    titles = {r["title"] for r in rems}
    # The renewal (5d) and birthday (3d) land in the window; the QBR (90d) does not.
    assert "Acme contract renewal" in titles
    assert "Jane Doe birthday" in titles
    assert "Globex QBR" not in titles


@pytest.mark.asyncio
async def test_seed_demo_graph_populates_mail_and_calendar():
    from app.graph import FakeGraph
    from app.demo_data import seed_demo_graph

    g = FakeGraph()
    seed_demo_graph(g)

    msgs = await g.list_messages()
    assert len(msgs) >= 2
    assert any((m.get("flag") or {}).get("flagStatus") == "flagged" for m in msgs)
    evs = await g.list_events("2000-01-01T00:00:00Z", "2100-01-01T00:00:00Z")
    assert len(evs) >= 2


def test_seed_demo_graph_noop_without_seed_method():
    from app.demo_data import seed_demo_graph
    seed_demo_graph(object())  # must not raise on a client lacking .seed()
