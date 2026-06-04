# Atlas Awareness Views (Plan 3a) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add an activity timeline + a stale-client radar, surfaced both as a global **Awareness** tab and as a per-client **Timeline** in the dossier.

**Architecture:** A pure backend aggregation module (`app/awareness.py`) computes events + staleness from existing records; three thin endpoints expose it; React views render it. Records gain `sys_created_on`/`sys_updated_on` (the fake stamps them; live ServiceNow already returns them) so everything sorts by time. Radar thresholds are two configurable Settings (`cooling_days`/`stale_days`) flowing through the Plan-B `config.json` overlay.

**Tech Stack:** FastAPI + pydantic v2, `FakeServiceNow`, pytest (`asyncio_mode=auto`) with an injected clock, React/Vite.

**Spec:** `docs/superpowers/specs/2026-06-03-atlas-awareness-views-design.md`

**Assumed working dir:** `$REPO` = `/Users/nick/Atlas/.claude/worktrees/desktop-app`. Backend venv `$REPO/backend/.venv` (run from `backend/` via `./.venv/bin/python -m pytest`; desktop/frontend from repo root). Tables: `f"{sn_scope}_<entity>"`; demo scope = `x_vendor_atlas`.

---

## File structure

| File | New/Mod | Responsibility |
|---|---|---|
| `backend/app/servicenow.py` | Modify | `FakeServiceNow`: injectable clock + stamp `sys_created_on`/`sys_updated_on` |
| `backend/tests/test_fake_timestamps.py` | Create | timestamps on create/update via injected clock |
| `backend/app/awareness.py` | Create | `event_time`, `_collect_events`, `build_timeline`, `recent_activity`, `stale_radar` |
| `backend/tests/test_awareness.py` | Create | timeline order/precedence, recent feed + limit, radar tiers/active-only/no-activity |
| `backend/app/config.py` | Modify | add `cooling_days: int = 14`, `stale_days: int = 30` |
| `backend/app/routers/settings.py` | Modify | expose the two thresholds (`_NON_SECRET` + `SettingsIn`) |
| `backend/tests/test_settings_api.py` | Modify | round-trip the two thresholds |
| `backend/app/routers/awareness.py` | Create | `/api/awareness/activity`, `/timeline/{id}`, `/radar` |
| `backend/app/main.py` | Modify | include the awareness router |
| `backend/tests/test_awareness_api.py` | Create | endpoint tests incl. timeline 404 |
| `frontend/src/types.ts` | Modify | `ActivityEvent`, `RadarEntry`; extend `AppSettings` |
| `frontend/src/api.ts` | Modify | `getActivity`, `getTimeline`, `getRadar` |
| `frontend/src/AwarenessView.tsx` | Create | radar panel + recent-activity feed |
| `frontend/src/App.tsx` | Modify | `"awareness"` view + nav button |
| `frontend/src/SettingsView.tsx` | Modify | two threshold number inputs |
| `frontend/src/DossierView.tsx` | Modify | a "Timeline" section |
| `docs/PROGRESS.md` | Modify | record Plan 3a (D16) |

---

## Task 0: Baseline
- [ ] **Step 1:** `cd "$REPO/backend" && ./.venv/bin/python -m pytest -q` → all pass (59). `cd "$REPO" && ./backend/.venv/bin/python -m pytest desktop/tests -q` → 6. If red, STOP.

---

## Task 1: Record timestamps in FakeServiceNow

**Files:** Modify `backend/app/servicenow.py`; Create `backend/tests/test_fake_timestamps.py`

- [ ] **Step 1: Write the failing test** — `backend/tests/test_fake_timestamps.py`:
```python
from datetime import datetime, timezone

import pytest

from app.servicenow import FakeServiceNow


def _clock(values):
    it = iter(values)
    return lambda: next(it)


@pytest.mark.asyncio
async def test_create_stamps_created_and_updated():
    fixed = datetime(2026, 6, 1, 9, 0, 0, tzinfo=timezone.utc)
    sn = FakeServiceNow(clock=lambda: fixed)
    rec = await sn.create("x_t", {"name": "a"})
    assert rec["sys_created_on"] == "2026-06-01T09:00:00Z"
    assert rec["sys_updated_on"] == "2026-06-01T09:00:00Z"


@pytest.mark.asyncio
async def test_update_refreshes_updated_only():
    t0 = datetime(2026, 6, 1, 9, 0, 0, tzinfo=timezone.utc)
    t1 = datetime(2026, 6, 2, 9, 0, 0, tzinfo=timezone.utc)
    sn = FakeServiceNow(clock=_clock([t0, t1]))
    rec = await sn.create("x_t", {"name": "a"})        # uses t0
    updated = await sn.update("x_t", rec["sys_id"], {"name": "b"})  # uses t1
    assert updated["sys_created_on"] == "2026-06-01T09:00:00Z"
    assert updated["sys_updated_on"] == "2026-06-02T09:00:00Z"


@pytest.mark.asyncio
async def test_default_clock_is_utc_now():
    sn = FakeServiceNow()
    rec = await sn.create("x_t", {"name": "a"})
    assert rec["sys_created_on"].endswith("Z") and "T" in rec["sys_created_on"]
```

- [ ] **Step 2: Run → FAIL** (`TypeError: ... unexpected keyword 'clock'` / missing keys):
`cd "$REPO/backend" && ./.venv/bin/python -m pytest tests/test_fake_timestamps.py -q`

- [ ] **Step 3: Implement.** In `backend/app/servicenow.py`, add imports at top:
```python
from datetime import datetime, timezone
from typing import Callable, Optional
```
(`Optional`/`Callable` may already be imported — keep one copy.) Replace the `FakeServiceNow.__init__` and `create`/`update` methods with:
```python
    def __init__(self, clock: Optional[Callable[[], datetime]] = None) -> None:
        self._tables: dict[str, dict[str, dict]] = {}
        self._ids = itertools.count(1)
        self._clock = clock or (lambda: datetime.now(timezone.utc))

    def _now_iso(self) -> str:
        return self._clock().strftime("%Y-%m-%dT%H:%M:%SZ")
```
In `create`, stamp both timestamps (created/updated) on the new record:
```python
    async def create(self, table: str, payload: dict) -> dict:
        sys_id = f"fake{next(self._ids):06d}"
        ts = self._now_iso()
        record = {**payload, "sys_id": sys_id, "sys_created_on": ts, "sys_updated_on": ts}
        self._table(table)[sys_id] = record
        return record
```
In `update`, refresh only `sys_updated_on` (after applying payload):
```python
    async def update(self, table: str, sys_id: str, payload: dict) -> dict:
        record = self._table(table)[sys_id]
        record.update(payload)
        record["sys_updated_on"] = self._now_iso()
        return record
```

- [ ] **Step 4: Run → PASS** (3).

- [ ] **Step 5: Run the FULL backend suite — the new fields must not break existing tests.**
`cd "$REPO/backend" && ./.venv/bin/python -m pytest -q`
Expected: all pass. **If any test fails because it asserts a created/returned record equals an exact literal dict**, fix that test to assert the meaningful subset instead (e.g. compare specific keys, or `{k: rec[k] for k in expected} == expected`) — do NOT remove the timestamps. Report any test you changed.

- [ ] **Step 6: Commit**
```bash
cd "$REPO" && git add backend/app/servicenow.py backend/tests/test_fake_timestamps.py
git commit -m "feat: FakeServiceNow stamps sys_created_on/sys_updated_on (injectable clock)"
```

---

## Task 2: Awareness core — `event_time`, `_collect_events`, `build_timeline`

**Files:** Create `backend/app/awareness.py`, `backend/tests/test_awareness.py`

- [ ] **Step 1: Write the failing test** — `backend/tests/test_awareness.py`:
```python
from datetime import datetime, timezone

import pytest

from app.servicenow import FakeServiceNow
from app.awareness import build_timeline

SCOPE = "x_test"


def _clock(seq):
    it = iter(seq)
    return lambda: next(it)


async def _seed(sn):
    c = await sn.create(f"{SCOPE}_client", {"name": "Acme", "status": "active"})
    cid = c["sys_id"]
    await sn.create(f"{SCOPE}_task", {"title": "T1", "client": cid, "status": "open"})
    await sn.create(f"{SCOPE}_meeting", {"title": "Kickoff", "client": cid,
                                         "datetime": "2026-05-01T10:00:00Z"})
    await sn.create(f"{SCOPE}_note", {"title": "N1", "note_type": "risk",
                                      "target_table": "client", "target_id": cid})
    return cid


@pytest.mark.asyncio
async def test_timeline_newest_first_and_domain_date_wins():
    # created at increasing times; meeting.datetime (2026-05-01) is BEFORE its created stamp
    times = [datetime(2026, 6, d, 9, 0, 0, tzinfo=timezone.utc) for d in (1, 2, 3, 4)]
    sn = FakeServiceNow(clock=_clock(times))
    cid = await _seed(sn)
    tl = await build_timeline(sn, SCOPE, cid)
    assert [e["type"] for e in tl][0] in {"task", "note"}        # newest created first
    meeting = next(e for e in tl if e["type"] == "meeting")
    assert meeting["when"] == "2026-05-01T10:00:00Z"             # domain date used, not created
    whens = [e["when"] for e in tl]
    assert whens == sorted(whens, reverse=True)                  # strictly newest-first


@pytest.mark.asyncio
async def test_timeline_missing_client_returns_none():
    sn = FakeServiceNow()
    assert await build_timeline(sn, SCOPE, "nope") is None


@pytest.mark.asyncio
async def test_timeline_existing_client_no_activity_is_empty_list():
    sn = FakeServiceNow()
    c = await sn.create(f"{SCOPE}_client", {"name": "Empty", "status": "active"})
    assert await build_timeline(sn, SCOPE, c["sys_id"]) == []
```

- [ ] **Step 2: Run → FAIL** (`No module named 'app.awareness'`):
`cd "$REPO/backend" && ./.venv/bin/python -m pytest tests/test_awareness.py -q`

- [ ] **Step 3: Implement** — create `backend/app/awareness.py`:
```python
"""Awareness aggregation: turn the client's child records into a time-ordered
activity feed and a stale-client radar. Pure logic over the ServiceNowClient
interface — unit-tested against FakeServiceNow with an injected clock."""
from datetime import datetime, timezone
from typing import Optional

from app.servicenow import ServiceNowClient


def event_time(record: dict, domain_field: Optional[str] = None) -> str:
    """The instant an event happened: the domain date if present, else created."""
    if domain_field and record.get(domain_field):
        return record[domain_field]
    return record.get("sys_created_on", "")


def _ev(type_: str, title: str, when: str, client: str, client_name: str,
        status: Optional[str]) -> dict:
    return {"type": type_, "title": title, "when": when,
            "client": client, "client_name": client_name, "status": status}


async def _collect_events(sn: ServiceNowClient, scope: str) -> list[dict]:
    """Every activity event across all clients (unsorted)."""
    def t(s: str) -> str:
        return f"{scope}_{s}"

    clients = await sn.list(t("client"))
    name_by_id = {c["sys_id"]: c.get("name", "") for c in clients}
    events: list[dict] = []

    for r in await sn.list(t("task")):
        cid = r.get("client", "")
        events.append(_ev("task", f"Task: {r.get('title', '')}", event_time(r),
                          cid, name_by_id.get(cid, ""), r.get("status")))
    for r in await sn.list(t("meeting")):
        cid = r.get("client", "")
        events.append(_ev("meeting", f"Meeting: {r.get('title', '')}",
                          event_time(r, "datetime"), cid, name_by_id.get(cid, ""), None))
    for r in await sn.list(t("transcript")):
        cid = r.get("client", "")
        events.append(_ev("transcript", "Transcript captured",
                          event_time(r, "captured_date"), cid, name_by_id.get(cid, ""),
                          r.get("source")))
    for r in await sn.list(t("engagement")):
        cid = r.get("client", "")
        events.append(_ev("engagement", f"Engagement: {r.get('name', '')}",
                          event_time(r), cid, name_by_id.get(cid, ""), r.get("status")))
    for r in await sn.list(t("note")):
        if r.get("target_table") == "client":
            cid = r.get("target_id", "")
            events.append(_ev("note", f"Note: {r.get('title', '')}", event_time(r),
                              cid, name_by_id.get(cid, ""), r.get("note_type")))
    return events


async def build_timeline(sn: ServiceNowClient, scope: str, client_id: str) -> Optional[list[dict]]:
    """Time-ordered events for one client, or None if the client doesn't exist."""
    client = await sn.get(f"{scope}_client", client_id)
    if client is None:
        return None
    events = [e for e in await _collect_events(sn, scope) if e["client"] == client_id]
    return sorted(events, key=lambda e: e["when"], reverse=True)
```

- [ ] **Step 4: Run → PASS** (3).

- [ ] **Step 5: Commit**
```bash
cd "$REPO" && git add backend/app/awareness.py backend/tests/test_awareness.py
git commit -m "feat: awareness core — event_time + build_timeline"
```

---

## Task 3: `recent_activity` (global feed)

**Files:** Modify `backend/app/awareness.py`, `backend/tests/test_awareness.py`

- [ ] **Step 1: Add failing tests** to `backend/tests/test_awareness.py`:
```python
from app.awareness import recent_activity


@pytest.mark.asyncio
async def test_recent_activity_across_clients_newest_first():
    times = [datetime(2026, 6, d, 9, 0, 0, tzinfo=timezone.utc) for d in range(1, 10)]
    sn = FakeServiceNow(clock=_clock(times))
    a = await sn.create(f"{SCOPE}_client", {"name": "Acme", "status": "active"})
    b = await sn.create(f"{SCOPE}_client", {"name": "Globex", "status": "active"})
    await sn.create(f"{SCOPE}_task", {"title": "old", "client": a["sys_id"]})
    await sn.create(f"{SCOPE}_task", {"title": "new", "client": b["sys_id"]})
    feed = await recent_activity(sn, SCOPE)
    assert feed[0]["title"] == "Task: new"
    assert feed[0]["client_name"] == "Globex"
    assert {e["client_name"] for e in feed} == {"Acme", "Globex"}


@pytest.mark.asyncio
async def test_recent_activity_respects_limit():
    times = [datetime(2026, 6, 1, 9, m, 0, tzinfo=timezone.utc) for m in range(10)]
    sn = FakeServiceNow(clock=_clock(times))
    c = await sn.create(f"{SCOPE}_client", {"name": "Acme", "status": "active"})
    for i in range(5):
        await sn.create(f"{SCOPE}_task", {"title": f"t{i}", "client": c["sys_id"]})
    assert len(await recent_activity(sn, SCOPE, limit=3)) == 3
```

- [ ] **Step 2: Run → FAIL** (`cannot import name 'recent_activity'`).

- [ ] **Step 3: Implement** — append to `backend/app/awareness.py`:
```python
async def recent_activity(sn: ServiceNowClient, scope: str, limit: int = 50) -> list[dict]:
    """Newest-first activity across all clients, capped at ``limit``."""
    events = await _collect_events(sn, scope)
    events.sort(key=lambda e: e["when"], reverse=True)
    return events[:limit]
```

- [ ] **Step 4: Run → PASS** (5 in this file now).

- [ ] **Step 5: Commit**
```bash
cd "$REPO" && git add backend/app/awareness.py backend/tests/test_awareness.py
git commit -m "feat: awareness recent_activity (global feed + limit)"
```

---

## Task 4: `stale_radar` (configurable tiers)

**Files:** Modify `backend/app/awareness.py`, `backend/tests/test_awareness.py`

- [ ] **Step 1: Add failing tests** to `backend/tests/test_awareness.py`:
```python
from app.awareness import stale_radar

NOW = datetime(2026, 6, 30, 12, 0, 0, tzinfo=timezone.utc)


@pytest.mark.asyncio
async def test_radar_tiers_and_active_only():
    # client activity ages: fresh (ok), 20d (cooling), 40d (stale); plus a dormant client
    sn = FakeServiceNow(clock=lambda: datetime(2026, 6, 28, 12, 0, 0, tzinfo=timezone.utc))
    fresh = await sn.create(f"{SCOPE}_client", {"name": "Fresh", "status": "active"})
    await sn.create(f"{SCOPE}_task", {"title": "x", "client": fresh["sys_id"]})  # 2d ago
    sn._clock = lambda: datetime(2026, 6, 10, 12, 0, 0, tzinfo=timezone.utc)
    cooling = await sn.create(f"{SCOPE}_client", {"name": "Cooling", "status": "active"})
    await sn.create(f"{SCOPE}_task", {"title": "y", "client": cooling["sys_id"]})  # 20d ago
    sn._clock = lambda: datetime(2026, 5, 21, 12, 0, 0, tzinfo=timezone.utc)
    stale = await sn.create(f"{SCOPE}_client", {"name": "Stale", "status": "active"})
    await sn.create(f"{SCOPE}_task", {"title": "z", "client": stale["sys_id"]})  # 40d ago
    sn._clock = lambda: datetime(2026, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
    await sn.create(f"{SCOPE}_client", {"name": "OldProspect", "status": "prospect"})  # excluded

    radar = await stale_radar(sn, SCOPE, cooling_days=14, stale_days=30, now=NOW)
    by_name = {r["client_name"]: r for r in radar}
    assert "Fresh" not in by_name           # within cooling window → omitted
    assert "OldProspect" not in by_name      # not active → excluded
    assert by_name["Cooling"]["tier"] == "cooling"
    assert by_name["Stale"]["tier"] == "stale"
    # most-overdue first
    assert radar[0]["client_name"] == "Stale"


@pytest.mark.asyncio
async def test_radar_active_client_with_no_activity_uses_own_age():
    sn = FakeServiceNow(clock=lambda: datetime(2026, 1, 1, 0, 0, 0, tzinfo=timezone.utc))
    await sn.create(f"{SCOPE}_client", {"name": "Ghost", "status": "active"})  # created long ago, no events
    radar = await stale_radar(sn, SCOPE, cooling_days=14, stale_days=30, now=NOW)
    assert radar and radar[0]["client_name"] == "Ghost" and radar[0]["tier"] == "stale"
```

- [ ] **Step 2: Run → FAIL** (`cannot import name 'stale_radar'`).

- [ ] **Step 3: Implement** — append to `backend/app/awareness.py`:
```python
def _days_since(iso: str, now: datetime) -> int:
    if not iso:
        return 10 ** 6  # no timestamp at all → treat as very stale
    dt = datetime.fromisoformat(iso.replace("Z", "+00:00"))
    return (now - dt).days


async def stale_radar(sn: ServiceNowClient, scope: str, cooling_days: int,
                      stale_days: int, now: Optional[datetime] = None) -> list[dict]:
    """Active clients quiet for >= cooling_days, classified cooling/stale,
    most-overdue first. A client with no events is judged by its own age."""
    now = now or datetime.now(timezone.utc)
    clients = [c for c in await sn.list(f"{scope}_client") if c.get("status") == "active"]

    last_by_client: dict[str, str] = {}
    for e in await _collect_events(sn, scope):
        cid = e["client"]
        if cid and (cid not in last_by_client or e["when"] > last_by_client[cid]):
            last_by_client[cid] = e["when"]

    entries: list[dict] = []
    for c in clients:
        cid = c["sys_id"]
        last = last_by_client.get(cid) or c.get("sys_created_on", "")
        days = _days_since(last, now)
        if days >= stale_days:
            tier = "stale"
        elif days >= cooling_days:
            tier = "cooling"
        else:
            continue
        entries.append({"client": cid, "client_name": c.get("name", ""),
                        "last_activity": last, "days_quiet": days, "tier": tier})
    entries.sort(key=lambda x: x["days_quiet"], reverse=True)
    return entries
```

- [ ] **Step 4: Run → PASS** (7 in this file). Then full suite green.

- [ ] **Step 5: Commit**
```bash
cd "$REPO" && git add backend/app/awareness.py backend/tests/test_awareness.py
git commit -m "feat: awareness stale_radar (configurable tiers, active-only)"
```

---

## Task 5: Threshold settings (`cooling_days`/`stale_days`)

**Files:** Modify `backend/app/config.py`, `backend/app/routers/settings.py`, `backend/tests/test_settings_api.py`

- [ ] **Step 1: Add failing test** to `backend/tests/test_settings_api.py` (reuses the file's `_client` helper):
```python
def test_threshold_settings_roundtrip(monkeypatch, tmp_path):
    c = _client(monkeypatch, tmp_path)
    defaults = c.get("/api/settings").json()
    assert defaults["cooling_days"] == 14 and defaults["stale_days"] == 30
    c.put("/api/settings", json={"cooling_days": 7, "stale_days": 21})
    got = c.get("/api/settings").json()
    assert got["cooling_days"] == 7 and got["stale_days"] == 21
```

- [ ] **Step 2: Run → FAIL** (`KeyError: 'cooling_days'`):
`cd "$REPO/backend" && ./.venv/bin/python -m pytest tests/test_settings_api.py::test_threshold_settings_roundtrip -q`

- [ ] **Step 3: Implement.**
In `backend/app/config.py`, add two fields to `Settings` (anywhere among the fields):
```python
    cooling_days: int = 14
    stale_days: int = 30
```
In `backend/app/routers/settings.py`, add the two keys to `_NON_SECRET`:
```python
_NON_SECRET = ("use_fake", "sn_instance_url", "sn_scope", "sn_auth", "sn_oauth_username",
               "cooling_days", "stale_days")
```
and to the `SettingsIn` model:
```python
    cooling_days: int | None = None
    stale_days: int | None = None
```

- [ ] **Step 4: Run → PASS.** Then full suite green.

- [ ] **Step 5: Commit**
```bash
cd "$REPO" && git add backend/app/config.py backend/app/routers/settings.py backend/tests/test_settings_api.py
git commit -m "feat: configurable radar thresholds (cooling_days/stale_days)"
```

---

## Task 6: Awareness endpoints

**Files:** Create `backend/app/routers/awareness.py`, `backend/tests/test_awareness_api.py`; Modify `backend/app/main.py`

- [ ] **Step 1: Write the failing test** — `backend/tests/test_awareness_api.py`:
```python
from fastapi.testclient import TestClient

import app.user_config as uc
import app.main_deps as deps
from app.main import app
from app.servicenow import FakeServiceNow


def _client(monkeypatch, tmp_path):
    monkeypatch.setenv("ATLAS_DATA_DIR", str(tmp_path))
    monkeypatch.setattr(uc, "get_password", lambda: None)
    sn = FakeServiceNow()
    app.dependency_overrides[deps.get_sn] = lambda: sn
    return TestClient(app), sn


def _scope():
    from app.config import get_settings
    return get_settings().sn_scope


def teardown_function():
    app.dependency_overrides.clear()


def test_activity_and_radar_and_timeline(monkeypatch, tmp_path):
    c, sn = _client(monkeypatch, tmp_path)
    scope = _scope()
    import anyio
    cid = anyio.run(lambda: sn.create(f"{scope}_client", {"name": "Acme", "status": "active"}))["sys_id"]
    anyio.run(lambda: sn.create(f"{scope}_task", {"title": "T1", "client": cid}))

    act = c.get("/api/awareness/activity")
    assert act.status_code == 200 and any(e["title"] == "Task: T1" for e in act.json())

    tl = c.get(f"/api/awareness/timeline/{cid}")
    assert tl.status_code == 200 and len(tl.json()) == 1

    assert c.get("/api/awareness/timeline/nope").status_code == 404
    assert c.get("/api/awareness/radar").status_code == 200  # list (maybe empty)
```
(If `anyio` import is awkward, create the records by POSTing to `/api/clients` and `/api/tasks` instead — both exist — and read sys_id from the response.)

- [ ] **Step 2: Run → FAIL** (404s — router missing):
`cd "$REPO/backend" && ./.venv/bin/python -m pytest tests/test_awareness_api.py -q`

- [ ] **Step 3: Implement** — create `backend/app/routers/awareness.py`:
```python
from fastapi import APIRouter, Depends, HTTPException

from app import awareness
from app.config import get_settings
from app.main_deps import get_sn
from app.servicenow import ServiceNowClient

router = APIRouter(prefix="/api/awareness", tags=["awareness"])


@router.get("/activity")
async def activity(limit: int = 50, sn: ServiceNowClient = Depends(get_sn)) -> list[dict]:
    return await awareness.recent_activity(sn, get_settings().sn_scope, limit=limit)


@router.get("/timeline/{client_id}")
async def timeline(client_id: str, sn: ServiceNowClient = Depends(get_sn)) -> list[dict]:
    tl = await awareness.build_timeline(sn, get_settings().sn_scope, client_id)
    if tl is None:
        raise HTTPException(status_code=404, detail=f"client {client_id} not found")
    return tl


@router.get("/radar")
async def radar(sn: ServiceNowClient = Depends(get_sn)) -> list[dict]:
    s = get_settings()
    return await awareness.stale_radar(sn, s.sn_scope, s.cooling_days, s.stale_days)
```

- [ ] **Step 4: Wire into `backend/app/main.py`** — with the other router imports/includes, BEFORE `mount_frontend(app, _dist)`:
```python
from app.routers import awareness as awareness_router  # noqa: E402
app.include_router(awareness_router.router)
```

- [ ] **Step 5: Run → PASS.** Then full suite green.

- [ ] **Step 6: Commit**
```bash
cd "$REPO" && git add backend/app/routers/awareness.py backend/tests/test_awareness_api.py backend/app/main.py
git commit -m "feat: /api/awareness activity/timeline/radar endpoints"
```

---

## Task 7: Frontend — Awareness tab

**Files:** Modify `frontend/src/types.ts`, `frontend/src/api.ts`, `frontend/src/App.tsx`, `frontend/src/SettingsView.tsx`; Create `frontend/src/AwarenessView.tsx`

- [ ] **Step 1: Types** — append to `frontend/src/types.ts`:
```ts
export interface ActivityEvent {
  type: string;
  title: string;
  when: string;
  client: string;
  client_name: string;
  status: string | null;
}
export interface RadarEntry {
  client: string;
  client_name: string;
  last_activity: string;
  days_quiet: number;
  tier: "cooling" | "stale";
}
```
And add `cooling_days: number;` + `stale_days: number;` to the existing `AppSettings` interface.

- [ ] **Step 2: API** — append to `frontend/src/api.ts`:
```ts
import type { ActivityEvent, RadarEntry } from "./types";

export async function getActivity(limit = 50): Promise<ActivityEvent[]> {
  return http<ActivityEvent[]>(`/awareness/activity?limit=${limit}`);
}
export async function getTimeline(clientId: string): Promise<ActivityEvent[]> {
  return http<ActivityEvent[]>(`/awareness/timeline/${clientId}`);
}
export async function getRadar(): Promise<RadarEntry[]> {
  return http<RadarEntry[]>("/awareness/radar");
}
```
(Merge the `import type` with the existing one from `./types` if you prefer — both compile.)

- [ ] **Step 3: Create `frontend/src/AwarenessView.tsx`:**
```tsx
import { useEffect, useState } from "react";
import { getActivity, getRadar } from "./api";
import type { ActivityEvent, RadarEntry } from "./types";

const TIER_COLOR: Record<string, string> = { cooling: "#b8860b", stale: "#b00020" };

export function AwarenessView({ onOpenClient }: { onOpenClient: (id: string) => void }) {
  const [radar, setRadar] = useState<RadarEntry[] | null>(null);
  const [feed, setFeed] = useState<ActivityEvent[] | null>(null);
  const [err, setErr] = useState("");

  useEffect(() => {
    getRadar().then(setRadar).catch((e) => setErr(String(e)));
    getActivity().then(setFeed).catch((e) => setErr(String(e)));
  }, []);

  return (
    <div style={{ padding: 16, fontFamily: "system-ui", maxWidth: 820 }}>
      <h2>Awareness</h2>
      {err && <p style={{ color: "#b00020" }}>{err}</p>}

      <h3>Needs attention</h3>
      {radar === null ? <p>Loading…</p>
        : radar.length === 0 ? <p>All active clients are current. 🎉</p>
        : (
          <ul style={{ listStyle: "none", padding: 0 }}>
            {radar.map((r) => (
              <li key={r.client} style={{ padding: "6px 0", cursor: "pointer" }}
                  onClick={() => onOpenClient(r.client)}>
                <span style={{ color: TIER_COLOR[r.tier], fontWeight: 600 }}>● {r.tier}</span>
                {" "}— <strong>{r.client_name}</strong> · quiet {r.days_quiet} days
              </li>
            ))}
          </ul>
        )}

      <h3 style={{ marginTop: 24 }}>Recent activity</h3>
      {feed === null ? <p>Loading…</p>
        : feed.length === 0 ? <p>No activity yet.</p>
        : (
          <ul style={{ listStyle: "none", padding: 0 }}>
            {feed.map((e, i) => (
              <li key={i} style={{ padding: "4px 0", borderBottom: "1px solid #eee" }}>
                <span style={{ color: "#888" }}>{e.when.slice(0, 10)}</span>{" "}
                <strong>{e.client_name}</strong> — {e.title}
                {e.status ? <em style={{ color: "#888" }}> ({e.status})</em> : null}
              </li>
            ))}
          </ul>
        )}
    </div>
  );
}
```

- [ ] **Step 4: Wire into `frontend/src/App.tsx`** (READ it first). Add the import `import { AwarenessView } from "./AwarenessView";`; add `"awareness"` to the `View` union; add a nav button `<button onClick={() => setView("awareness")}>Awareness</button>`; and render it, reusing the existing dossier-open pattern:
```tsx
{view === "awareness" && (
  <AwarenessView onOpenClient={(id) => { setClientSysId(id); setView("dossier"); }} />
)}
```
(`setClientSysId`/`setView("dossier")` already exist from the Clients→Dossier flow.)

- [ ] **Step 5: Settings inputs** — in `frontend/src/SettingsView.tsx`, add a "Radar thresholds" group (these always apply, even in demo mode, so place them OUTSIDE the `use_fake`-disabled fieldset). Add to the saved payload in `save()` too:
```tsx
      <fieldset>
        <legend>Radar thresholds (days)</legend>
        <label>Cooling after
          <input type="number" min={1} value={s.cooling_days}
                 onChange={(e) => set({ cooling_days: Number(e.target.value) })} />
        </label>
        <label>Stale after
          <input type="number" min={1} value={s.stale_days}
                 onChange={(e) => set({ stale_days: Number(e.target.value) })} />
        </label>
      </fieldset>
```
In `save()`, include `cooling_days: s.cooling_days, stale_days: s.stale_days` in the `saveSettings({...})` call.

- [ ] **Step 6: Build to verify:**
```bash
cd "$REPO/frontend" && npm run build
```
Expected: tsc + vite succeed.

- [ ] **Step 7: Commit**
```bash
cd "$REPO" && git add frontend/src/types.ts frontend/src/api.ts frontend/src/AwarenessView.tsx frontend/src/App.tsx frontend/src/SettingsView.tsx
git commit -m "feat: Awareness tab (radar + recent activity) + threshold settings UI"
```

---

## Task 8: Dossier timeline section

**Files:** Modify `frontend/src/DossierView.tsx`

- [ ] **Step 1: READ `frontend/src/DossierView.tsx`** to learn its structure (it takes `clientSysId` + `onBack`, fetches the dossier on mount).

- [ ] **Step 2: Add a Timeline section.** Import `getTimeline` and `ActivityEvent`, add state, fetch on mount keyed by `clientSysId`, and render a "Timeline" section near the bottom:
```tsx
// add near the other imports:
import { getTimeline } from "./api";
import type { ActivityEvent } from "./types";

// inside the component, with the other hooks:
const [timeline, setTimeline] = useState<ActivityEvent[] | null>(null);
useEffect(() => {
  getTimeline(clientSysId).then(setTimeline).catch(() => setTimeline([]));
}, [clientSysId]);

// in the JSX, as a new section:
<section>
  <h3>Timeline</h3>
  {timeline === null ? <p>Loading…</p>
    : timeline.length === 0 ? <p>No activity yet.</p>
    : (
      <ul style={{ listStyle: "none", padding: 0 }}>
        {timeline.map((e, i) => (
          <li key={i} style={{ padding: "3px 0" }}>
            <span style={{ color: "#888" }}>{e.when.slice(0, 10)}</span> — {e.title}
            {e.status ? <em style={{ color: "#888" }}> ({e.status})</em> : null}
          </li>
        ))}
      </ul>
    )}
</section>
```
Match the existing component's `useState`/`useEffect` import style and JSX conventions; if the file uses a different state-var naming pattern, follow it.

- [ ] **Step 3: Build to verify:**
```bash
cd "$REPO/frontend" && npm run build
```
Expected: succeeds.

- [ ] **Step 4: Commit**
```bash
cd "$REPO" && git add frontend/src/DossierView.tsx
git commit -m "feat: client timeline section in the dossier"
```

---

## Task 9: Build, smoke-test, document

- [ ] **Step 1: Full suites green**
```bash
cd "$REPO/backend" && ./.venv/bin/python -m pytest -q
cd "$REPO" && ./backend/.venv/bin/python -m pytest desktop/tests -q
```

- [ ] **Step 2: Build + smoke the packaged app** (demo data already seeds clients/tasks → radar + feed should populate):
```bash
cd "$REPO" && bash scripts/build-desktop.sh
pkill -9 -f "Atlas.app/Contents/MacOS/Atlas" 2>/dev/null; sleep 1
open dist/Atlas.app; sleep 7
port=$(lsof -nP -iTCP -sTCP:LISTEN 2>/dev/null | grep -E "^Atlas" | grep -oE '127\.0\.0\.1:[0-9]+' | head -1 | cut -d: -f2)
B="http://127.0.0.1:$port"; echo "port=$port"
curl -s "$B/api/awareness/activity" | head -c 300; echo
curl -s "$B/api/awareness/radar" | head -c 300; echo
pkill -9 -f "Atlas.app/Contents/MacOS/Atlas" 2>/dev/null
```
Expected: activity returns events for the demo clients; radar returns a list (the demo seed's hardcoded near-future dates mean clients may or may not be "stale" depending on the run date — either way it's a valid list). Open the **Awareness** tab manually to eyeball it if desired.

- [ ] **Step 3: PROGRESS.md** — add decision **D16**:
```markdown
**D16 — Awareness views (Plan 3a).** Activity timeline + stale-client radar, both as a
global Awareness tab and a per-client dossier timeline. Backend `app/awareness.py`
(`build_timeline`/`recent_activity`/`stale_radar`) aggregates events from existing records,
ordered by domain date or the new `sys_created_on` (now stamped by FakeServiceNow; live SN
already returns it). Radar tiers (cooling/stale) use configurable `cooling_days`/`stale_days`
settings (defaults 14/30, active clients only). Endpoints under `/api/awareness/`. First slice
of Plan 3; tags/key-dates/export remain. Plan: `docs/superpowers/plans/2026-06-03-atlas-awareness-views.md`.
```
Update the Desktop/status line to note Plan 3a complete.

- [ ] **Step 4: Commit**
```bash
cd "$REPO" && git add docs/PROGRESS.md
git commit -m "docs: record Awareness views (D16)"
```

---

## Done criteria
- Backend suite green (existing 59 + new: fake-timestamps 3, awareness 7, awareness-api ~1, settings threshold 1).
- `npm run build` clean; Awareness tab renders radar + feed; dossier shows a Timeline.
- Packaged app: `/api/awareness/activity` + `/radar` return data on demo seed.

## Self-review
- Spec coverage: timestamps (T1) ✅, timeline (T2) ✅, recent feed (T3) ✅, radar tiers/active-only/no-activity (T4) ✅, configurable thresholds (T5) ✅, endpoints + 404 (T6) ✅, Awareness tab + settings UI (T7) ✅, dossier timeline (T8) ✅, build/smoke/docs (T9) ✅.
- No placeholders: all code shown; frontend App/Dossier/Settings edits are concrete with "read first / match existing style" notes for the two files whose internals vary.
- Type consistency: event shape `{type,title,when,client,client_name,status}` and `radar_entry {client,client_name,last_activity,days_quiet,tier}` identical across `awareness.py`, endpoints, `types.ts`, and the React views; `cooling_days`/`stale_days` consistent across config/settings/AppSettings/UI.
