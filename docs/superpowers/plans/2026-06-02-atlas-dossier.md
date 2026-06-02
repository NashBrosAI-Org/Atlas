# Atlas Dossier Implementation Plan (Plan 2 of the P1 series)

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Turn Atlas from a task list into a **client dossier** — drill into any client and see everything about them (contacts + org chart, engagements, themes, open tasks, recent meetings + transcripts, and pinned notes/RAID) in one view, all backed by the ServiceNow scoped app and developed against `FakeServiceNow`.

**Architecture:** Adds read/write coverage for the entities Plan 1 created but didn't wire (Contact, Engagement, Theme, Meeting, Transcript, Note). A single DRY `crud_router` factory generates the per-entity REST endpoints; one aggregate `dossier` endpoint stitches a client's related records into a single response; the React app gains a client list and a dossier page. No new ServiceNow schema — Plan 1's tables already exist.

**Tech Stack:** Unchanged from Plan 1 — Python/FastAPI/httpx/pydantic/pytest backend, React+Vite+TS frontend, ServiceNow Table API behind the `ServiceNowClient` interface.

---

## Scope boundary

**Delivers:** CRUD for Contact/Engagement/Theme/Meeting/Transcript/Note; polymorphic Note pinning; the `dossier` aggregate; a client-list page; a client dossier page with org chart, sections, a transcript paste-in, and a note composer.

**Does NOT deliver (later plans):**
- Transcript `.vtt`/`.docx` parsing or Teams/Zoom auto-pull → **Plan P2 (M365)**.
- Tags, Links, KeyDates UI, Activity timeline, stale-client radar, export/backup job → **Plan 3**.
- AI summaries/drafting/search, decks → **Plan P3**.

**Hard rules (carried from CLAUDE.md):** develop against `FakeServiceNow` only (no corporate data on the personal Mac); secrets stay out of the repo; all SN access goes through `ServiceNowClient`/`get_sn`; `types.ts` mirrors the pydantic models (change both together); routers stay thin (cross-record logic in named helpers).

---

## Design decisions (locked for this plan)

1. **One `crud_router` factory**, not six hand-written routers. It builds `GET /api/{name}` (list, optional `?client=`), `POST /api/{name}` (create), `GET /api/{name}/{sys_id}`, `PATCH /api/{name}/{sys_id}` for a given table + pydantic model. DRY; one set of tests covers all six.
2. **Table-name resolution stays consistent with Plan 1:** `f"{settings.sn_scope}_{suffix}"` (e.g. `x_vendor_atlas_contact`). The `FakeServiceNow` keys on the string, so tests are scope-agnostic.
3. **Note pinning is polymorphic** via two fields the SN `note` table already has conceptually: `target_table` + `target_id`. (SN stores these as one "Document ID" column; the REST payload carries them as two keys. Our model exposes `target_table` and `target_id`; the HTTP layer passes them through unchanged.)
4. **Dossier is read-only aggregation** done in a named helper `build_dossier(sn, client_sys_id)` — not inline in the route. It issues parallel-safe sequential `list` calls filtered by `client`, plus the client `get`.
5. **Org chart is computed on the frontend** from the flat contact list using `reports_to`. Roots = contacts whose `reports_to` is empty or points outside the set.

---

## File structure

**Backend (new/modified):**
```
backend/app/
  models.py            # MODIFY: add Contact, Engagement, Theme, Meeting, Transcript, Note
  crud.py              # NEW: crud_router(name, suffix, Model) factory
  dossier.py           # NEW: build_dossier() helper
  routers/
    dossier.py         # NEW: GET /api/clients/{sys_id}/dossier
  main.py              # MODIFY: include the six crud routers + dossier router
backend/tests/
  test_crud_router.py  # NEW: generic CRUD behavior (using Contact as the exemplar)
  test_note_pinning.py # NEW: polymorphic target round-trip
  test_dossier.py      # NEW: aggregate shape + client filtering
```

**Frontend (new/modified):**
```
frontend/src/
  types.ts             # MODIFY: add Contact/Engagement/Theme/Meeting/Transcript/Note + Dossier
  api.ts               # MODIFY: add entity calls + getDossier + createNote + createTranscript
  App.tsx              # MODIFY: minimal routing (Now | Clients | Dossier)
  ClientsView.tsx      # NEW: client list → links to dossier
  DossierView.tsx      # NEW: the client dossier page (sections)
  OrgChart.tsx         # NEW: renders reports_to tree from flat contacts
  NoteComposer.tsx     # NEW: pin a note to the client/engagement/theme/meeting
  TranscriptPaste.tsx  # NEW: paste transcript text → creates a transcript record
```

---

# TASKS

## Task 1: Add pydantic models for the six entities

**Files:**
- Modify: `backend/app/models.py`
- Test: `backend/tests/test_models_plan2.py`

- [ ] **Step 1: Write the failing test**

`backend/tests/test_models_plan2.py`:
```python
from app.models import Contact, Engagement, Theme, Meeting, Transcript, Note

def test_contact_defaults():
    c = Contact(name="Jane Doe", client="c1")
    assert c.sentiment == "neutral"
    assert c.reports_to is None

def test_engagement_defaults():
    e = Engagement(name="Acme Migration", client="c1")
    assert e.status == "on_track"

def test_theme_defaults():
    t = Theme(name="Renewals", client="c1")
    assert t.status == "open"

def test_meeting_defaults():
    m = Meeting(title="Acme QBR", client="c1")
    assert m.type == "teams"

def test_transcript_minimal():
    tr = Transcript(client="c1", full_text="hello world")
    assert tr.source == "manual"

def test_note_defaults_and_target():
    n = Note(title="Risk: timeline", note_type="risk", target_table="engagement", target_id="e1")
    assert n.pinned is False
    assert n.note_type == "risk"
    assert n.target_id == "e1"
```

- [ ] **Step 2: Run to verify it fails**

Run: `cd backend && source .venv/bin/activate && pytest tests/test_models_plan2.py -v`
Expected: FAIL with `ImportError: cannot import name 'Contact'`

- [ ] **Step 3: Add models to `backend/app/models.py`** (append; keep existing `Client`/`Task`)

```python
Sentiment = Literal["champion", "neutral", "detractor"]
EngagementStatus = Literal["on_track", "at_risk", "blocked", "done"]
ThemeStatus = Literal["open", "watching", "resolved"]
MeetingType = Literal["teams", "zoom", "other"]
TranscriptSource = Literal["teams", "zoom", "manual"]
NoteType = Literal["general", "risk", "issue", "decision"]


class Contact(BaseModel):
    sys_id: Optional[str] = None
    name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    client: Optional[str] = None
    role_title: Optional[str] = None
    reports_to: Optional[str] = None      # sys_id of another Contact
    personal_notes: Optional[str] = None
    sentiment: Sentiment = "neutral"


class Engagement(BaseModel):
    sys_id: Optional[str] = None
    name: str
    client: Optional[str] = None
    status: EngagementStatus = "on_track"
    start_date: Optional[str] = None
    target_date: Optional[str] = None
    description: Optional[str] = None


class Theme(BaseModel):
    sys_id: Optional[str] = None
    name: str
    client: Optional[str] = None
    status: ThemeStatus = "open"
    description: Optional[str] = None


class Meeting(BaseModel):
    sys_id: Optional[str] = None
    title: str
    client: Optional[str] = None
    engagement: Optional[str] = None
    datetime: Optional[str] = None
    type: MeetingType = "teams"
    attendees: Optional[str] = None
    summary: Optional[str] = None


class Transcript(BaseModel):
    sys_id: Optional[str] = None
    meeting: Optional[str] = None
    client: Optional[str] = None
    full_text: str
    source: TranscriptSource = "manual"
    captured_date: Optional[str] = None


class Note(BaseModel):
    sys_id: Optional[str] = None
    title: str
    body: Optional[str] = None
    note_type: NoteType = "general"
    target_table: Optional[str] = None    # e.g. "client", "engagement", "theme", "meeting"
    target_id: Optional[str] = None       # sys_id of the pinned record
    pinned: bool = False
```

- [ ] **Step 4: Run to verify it passes**

Run: `pytest tests/test_models_plan2.py -v`
Expected: PASS (6 passed)

- [ ] **Step 5: Commit**

```bash
cd .. && git add backend/app/models.py backend/tests/test_models_plan2.py && git commit -m "feat: pydantic models for contact/engagement/theme/meeting/transcript/note"
```

---

## Task 2: Generic CRUD router factory

**Files:**
- Create: `backend/app/crud.py`
- Test: `backend/tests/test_crud_router.py`

The factory returns an `APIRouter` exposing list/create/get/patch for one entity. List supports an optional `?client=` filter. Create validates against the model and strips `sys_id`/None.

- [ ] **Step 1: Write the failing test** (Contact is the exemplar; same code path serves all six)

`backend/tests/test_crud_router.py`:
```python
from fastapi import FastAPI
from fastapi.testclient import TestClient
from app.crud import crud_router
from app.models import Contact
from app.main_deps import get_sn
from app.servicenow import FakeServiceNow


def _app(sn):
    app = FastAPI()
    app.include_router(crud_router("contacts", "contact", Contact))
    app.dependency_overrides[get_sn] = lambda: sn
    return TestClient(app)


def test_create_get_list_patch_roundtrip():
    sn = FakeServiceNow()
    c = _app(sn)

    created = c.post("/api/contacts", json={"name": "Jane", "client": "c1"}).json()
    assert created["sys_id"]
    assert created["sentiment"] == "neutral"

    got = c.get(f"/api/contacts/{created['sys_id']}").json()
    assert got["name"] == "Jane"

    patched = c.patch(f"/api/contacts/{created['sys_id']}", json={"sentiment": "champion"}).json()
    assert patched["sentiment"] == "champion"

    rows = c.get("/api/contacts").json()
    assert len(rows) == 1


def test_list_filters_by_client():
    sn = FakeServiceNow()
    c = _app(sn)
    c.post("/api/contacts", json={"name": "A", "client": "c1"})
    c.post("/api/contacts", json={"name": "B", "client": "c2"})
    rows = c.get("/api/contacts?client=c1").json()
    assert [r["name"] for r in rows] == ["A"]


def test_get_unknown_returns_404():
    sn = FakeServiceNow()
    c = _app(sn)
    assert c.get("/api/contacts/nope").status_code == 404
```

- [ ] **Step 2: Run to verify it fails**

Run: `pytest tests/test_crud_router.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'app.crud'`

- [ ] **Step 3: Create `backend/app/crud.py`**

```python
from typing import Optional, Type
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from app.config import get_settings
from app.servicenow import ServiceNowClient
from app.main_deps import get_sn

_settings = get_settings()


def crud_router(name: str, table_suffix: str, model: Type[BaseModel]) -> APIRouter:
    router = APIRouter(prefix=f"/api/{name}", tags=[name])

    def table() -> str:
        return f"{_settings.sn_scope}_{table_suffix}"

    @router.get("")
    async def list_records(client: Optional[str] = None, sn: ServiceNowClient = Depends(get_sn)) -> list[dict]:
        query = {"client": client} if client else None
        return await sn.list(table(), query=query)

    @router.post("", status_code=201)
    async def create_record(body: model, sn: ServiceNowClient = Depends(get_sn)) -> dict:  # type: ignore[valid-type]
        payload = body.model_dump(exclude_none=True, exclude={"sys_id"})
        return await sn.create(table(), payload)

    @router.get("/{sys_id}")
    async def get_record(sys_id: str, sn: ServiceNowClient = Depends(get_sn)) -> dict:
        rec = await sn.get(table(), sys_id)
        if rec is None:
            raise HTTPException(status_code=404, detail=f"{name} {sys_id} not found")
        return rec

    @router.patch("/{sys_id}")
    async def patch_record(sys_id: str, body: dict, sn: ServiceNowClient = Depends(get_sn)) -> dict:
        return await sn.update(table(), sys_id, body)

    return router
```

- [ ] **Step 4: Run to verify it passes**

Run: `pytest tests/test_crud_router.py -v`
Expected: PASS (3 passed)

- [ ] **Step 5: Commit**

```bash
cd .. && git add backend/app/crud.py backend/tests/test_crud_router.py && git commit -m "feat: generic CRUD router factory"
```

---

## Task 3: Wire the six entity routers

**Files:**
- Modify: `backend/app/main.py`
- Test: `backend/tests/test_entity_routes_wired.py`

- [ ] **Step 1: Write the failing test**

`backend/tests/test_entity_routes_wired.py`:
```python
def test_all_entity_routes_exist(client):
    for name in ["contacts", "engagements", "themes", "meetings", "transcripts", "notes"]:
        # POST minimal valid bodies
        body = {"name": "x", "client": "c1"} if name in ("contacts", "engagements", "themes") \
            else {"title": "x", "client": "c1"} if name == "meetings" \
            else {"full_text": "x", "client": "c1"} if name == "transcripts" \
            else {"title": "x"}  # notes
        r = client.post(f"/api/{name}", json=body)
        assert r.status_code == 201, f"{name} POST failed: {r.status_code} {r.text}"
        assert client.get(f"/api/{name}").status_code == 200
```

- [ ] **Step 2: Run to verify it fails**

Run: `pytest tests/test_entity_routes_wired.py -v`
Expected: FAIL — routes 404 (not wired yet)

- [ ] **Step 3: Modify `backend/app/main.py`** — add the six routers after the existing `clients`/`tasks` includes

```python
from app.routers import clients, tasks  # noqa: E402
from app.crud import crud_router  # noqa: E402
from app.models import Contact, Engagement, Theme, Meeting, Transcript, Note  # noqa: E402

app.include_router(clients.router)
app.include_router(tasks.router)
app.include_router(crud_router("contacts", "contact", Contact))
app.include_router(crud_router("engagements", "engagement", Engagement))
app.include_router(crud_router("themes", "theme", Theme))
app.include_router(crud_router("meetings", "meeting", Meeting))
app.include_router(crud_router("transcripts", "transcript", Transcript))
app.include_router(crud_router("notes", "note", Note))
```

- [ ] **Step 4: Run to verify it passes**

Run: `pytest tests/test_entity_routes_wired.py -v`
Expected: PASS (1 passed)

- [ ] **Step 5: Commit**

```bash
cd .. && git add backend/app/main.py backend/tests/test_entity_routes_wired.py && git commit -m "feat: wire contact/engagement/theme/meeting/transcript/note routers"
```

---

## Task 4: Note polymorphic pinning round-trip

**Files:**
- Test: `backend/tests/test_note_pinning.py`

Notes already work via the generic router; this task adds a focused test that the polymorphic `target_table`/`target_id` survive create→list and that notes can be filtered to a pinned target.

- [ ] **Step 1: Write the failing test**

`backend/tests/test_note_pinning.py`:
```python
def test_note_pin_target_roundtrip(client):
    r = client.post("/api/notes", json={
        "title": "Decision: go with phased cutover",
        "note_type": "decision",
        "target_table": "engagement",
        "target_id": "eng123",
        "pinned": True,
    })
    assert r.status_code == 201
    note = r.json()
    assert note["target_table"] == "engagement"
    assert note["target_id"] == "eng123"
    assert note["note_type"] == "decision"

    # list and confirm it can be found by its target
    rows = client.get("/api/notes").json()
    pinned = [n for n in rows if n.get("target_id") == "eng123"]
    assert len(pinned) == 1
```

- [ ] **Step 2: Run to verify it passes immediately** (behavior already implemented via crud_router + model)

Run: `pytest tests/test_note_pinning.py -v`
Expected: PASS (1 passed). If it fails, the Note model or wiring is wrong — fix there, do not special-case notes.

- [ ] **Step 3: Commit**

```bash
cd .. && git add backend/tests/test_note_pinning.py && git commit -m "test: note polymorphic pinning round-trip"
```

---

## Task 5: Dossier aggregate helper + endpoint

**Files:**
- Create: `backend/app/dossier.py`, `backend/app/routers/dossier.py`
- Modify: `backend/app/main.py` (include dossier router)
- Test: `backend/tests/test_dossier.py`

`build_dossier(sn, client_sys_id)` returns a dict: the client record plus lists of its contacts, engagements, themes, open tasks, recent meetings, and notes pinned to the client. Notes are matched by `target_table == "client"` and `target_id == client_sys_id`.

- [ ] **Step 1: Write the failing test**

`backend/tests/test_dossier.py`:
```python
def test_dossier_aggregates_client_relations(client):
    cid = client.post("/api/clients", json={"name": "Acme"}).json()["sys_id"]
    other = client.post("/api/clients", json={"name": "Globex"}).json()["sys_id"]

    client.post("/api/contacts", json={"name": "Jane", "client": cid})
    client.post("/api/contacts", json={"name": "Other", "client": other})
    client.post("/api/engagements", json={"name": "Migration", "client": cid})
    client.post("/api/themes", json={"name": "Renewals", "client": cid})
    client.post("/api/tasks", json={"title": "open one", "client": cid, "status": "open"})
    client.post("/api/tasks", json={"title": "done one", "client": cid, "status": "done"})
    client.post("/api/meetings", json={"title": "QBR", "client": cid})
    client.post("/api/notes", json={"title": "pinned", "target_table": "client", "target_id": cid})
    client.post("/api/notes", json={"title": "elsewhere", "target_table": "client", "target_id": other})

    d = client.get(f"/api/clients/{cid}/dossier").json()
    assert d["client"]["name"] == "Acme"
    assert [c["name"] for c in d["contacts"]] == ["Jane"]
    assert [e["name"] for e in d["engagements"]] == ["Migration"]
    assert [t["name"] for t in d["themes"]] == ["Renewals"]
    assert [t["title"] for t in d["open_tasks"]] == ["open one"]   # done excluded
    assert [m["title"] for m in d["meetings"]] == ["QBR"]
    assert [n["title"] for n in d["notes"]] == ["pinned"]          # other client's note excluded


def test_dossier_unknown_client_404(client):
    assert client.get("/api/clients/nope/dossier").status_code == 404
```

- [ ] **Step 2: Run to verify it fails**

Run: `pytest tests/test_dossier.py -v`
Expected: FAIL — route 404 / module missing

- [ ] **Step 3: Create `backend/app/dossier.py`**

```python
from fastapi import HTTPException
from app.config import get_settings
from app.servicenow import ServiceNowClient

_settings = get_settings()


def _t(suffix: str) -> str:
    return f"{_settings.sn_scope}_{suffix}"


async def build_dossier(sn: ServiceNowClient, client_sys_id: str) -> dict:
    client = await sn.get(_t("client"), client_sys_id)
    if client is None:
        raise HTTPException(status_code=404, detail=f"client {client_sys_id} not found")

    by_client = {"client": client_sys_id}
    contacts = await sn.list(_t("contact"), query=by_client)
    engagements = await sn.list(_t("engagement"), query=by_client)
    themes = await sn.list(_t("theme"), query=by_client)
    tasks = await sn.list(_t("task"), query=by_client)
    meetings = await sn.list(_t("meeting"), query=by_client)
    all_notes = await sn.list(_t("note"))

    open_tasks = [t for t in tasks if t.get("status") != "done"]
    notes = [n for n in all_notes
             if n.get("target_table") == "client" and n.get("target_id") == client_sys_id]

    return {
        "client": client,
        "contacts": contacts,
        "engagements": engagements,
        "themes": themes,
        "open_tasks": open_tasks,
        "meetings": meetings,
        "notes": notes,
    }
```

- [ ] **Step 4: Create `backend/app/routers/dossier.py`**

```python
from fastapi import APIRouter, Depends
from app.servicenow import ServiceNowClient
from app.main_deps import get_sn
from app.dossier import build_dossier

router = APIRouter(prefix="/api/clients", tags=["dossier"])


@router.get("/{sys_id}/dossier")
async def get_dossier(sys_id: str, sn: ServiceNowClient = Depends(get_sn)) -> dict:
    return await build_dossier(sn, sys_id)
```

- [ ] **Step 5: Modify `backend/app/main.py`** — include the dossier router (after the crud routers)

```python
from app.routers import dossier  # noqa: E402
app.include_router(dossier.router)
```

- [ ] **Step 6: Run to verify it passes; then the full suite**

Run: `pytest tests/test_dossier.py -v && pytest -q`
Expected: dossier tests PASS, then full suite green.

- [ ] **Step 7: Commit**

```bash
cd .. && git add backend/app/dossier.py backend/app/routers/dossier.py backend/app/main.py backend/tests/test_dossier.py && git commit -m "feat: client dossier aggregate endpoint"
```

---

## Task 6: Frontend types + api calls

**Files:**
- Modify: `frontend/src/types.ts`, `frontend/src/api.ts`

- [ ] **Step 1: Add types to `frontend/src/types.ts`** (append; keep `Client`/`Task`)

```ts
export interface Contact {
  sys_id?: string; name: string; email?: string; phone?: string; client?: string;
  role_title?: string; reports_to?: string; personal_notes?: string;
  sentiment?: "champion" | "neutral" | "detractor";
}
export interface Engagement {
  sys_id?: string; name: string; client?: string;
  status?: "on_track" | "at_risk" | "blocked" | "done";
  start_date?: string; target_date?: string; description?: string;
}
export interface Theme {
  sys_id?: string; name: string; client?: string;
  status?: "open" | "watching" | "resolved"; description?: string;
}
export interface Meeting {
  sys_id?: string; title: string; client?: string; engagement?: string;
  datetime?: string; type?: "teams" | "zoom" | "other"; attendees?: string; summary?: string;
}
export interface Transcript {
  sys_id?: string; meeting?: string; client?: string; full_text: string;
  source?: "teams" | "zoom" | "manual"; captured_date?: string;
}
export interface Note {
  sys_id?: string; title: string; body?: string;
  note_type?: "general" | "risk" | "issue" | "decision";
  target_table?: string; target_id?: string; pinned?: boolean;
}
export interface Dossier {
  client: Client;
  contacts: Contact[];
  engagements: Engagement[];
  themes: Theme[];
  open_tasks: Task[];
  meetings: Meeting[];
  notes: Note[];
}
```

- [ ] **Step 2: Add calls to `frontend/src/api.ts`** (append)

```ts
import type { Contact, Dossier, Note, Transcript } from "./types";

export async function getDossier(clientSysId: string): Promise<Dossier> {
  return (await fetch(`${BASE}/clients/${clientSysId}/dossier`)).json();
}
export async function createContact(c: Partial<Contact>): Promise<Contact> {
  return (await fetch(`${BASE}/contacts`, {
    method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(c),
  })).json();
}
export async function createNote(n: Partial<Note>): Promise<Note> {
  return (await fetch(`${BASE}/notes`, {
    method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(n),
  })).json();
}
export async function createTranscript(t: Partial<Transcript>): Promise<Transcript> {
  return (await fetch(`${BASE}/transcripts`, {
    method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(t),
  })).json();
}
```

- [ ] **Step 3: Type-check + commit**

Run: `cd frontend && npm run build` (tsc must pass)
Expected: build succeeds.
```bash
cd .. && git add frontend/src/types.ts frontend/src/api.ts && git commit -m "feat: frontend types + api for dossier/contacts/notes/transcripts"
```

---

## Task 7: OrgChart component

**Files:**
- Create: `frontend/src/OrgChart.tsx`

Builds a tree from flat contacts via `reports_to`; renders nested lists. Roots = contacts whose `reports_to` is empty or not present in the set.

- [ ] **Step 1: Create `frontend/src/OrgChart.tsx`**

```tsx
import type { Contact } from "./types";

function childrenOf(parentId: string | undefined, all: Contact[]): Contact[] {
  return all.filter((c) => (c.reports_to || "") === (parentId || ""));
}

function Node({ contact, all }: { contact: Contact; all: Contact[] }) {
  const kids = childrenOf(contact.sys_id, all);
  const badge = contact.sentiment === "champion" ? "⭐" : contact.sentiment === "detractor" ? "⚠️" : "";
  return (
    <li>
      <span>{badge} <strong>{contact.name}</strong>{contact.role_title ? ` — ${contact.role_title}` : ""}</span>
      {kids.length > 0 && <ul>{kids.map((k) => <Node key={k.sys_id} contact={k} all={all} />)}</ul>}
    </li>
  );
}

export function OrgChart({ contacts }: { contacts: Contact[] }) {
  const ids = new Set(contacts.map((c) => c.sys_id));
  const roots = contacts.filter((c) => !c.reports_to || !ids.has(c.reports_to));
  if (contacts.length === 0) return <p style={{ color: "#888" }}>No contacts yet.</p>;
  return <ul>{roots.map((r) => <Node key={r.sys_id} contact={r} all={contacts} />)}</ul>;
}
```

- [ ] **Step 2: Commit**

```bash
cd .. && git add frontend/src/OrgChart.tsx && git commit -m "feat: OrgChart component (reports_to tree)"
```

---

## Task 8: NoteComposer and TranscriptPaste components

**Files:**
- Create: `frontend/src/NoteComposer.tsx`, `frontend/src/TranscriptPaste.tsx`

- [ ] **Step 1: Create `frontend/src/NoteComposer.tsx`**

```tsx
import { useState } from "react";
import { createNote } from "./api";

const TYPES = ["general", "risk", "issue", "decision"] as const;

export function NoteComposer({ targetTable, targetId, onSaved }:
  { targetTable: string; targetId: string; onSaved: () => void }) {
  const [title, setTitle] = useState("");
  const [noteType, setNoteType] = useState<(typeof TYPES)[number]>("general");

  async function save() {
    if (!title.trim()) return;
    await createNote({ title, note_type: noteType, target_table: targetTable, target_id: targetId, pinned: true });
    setTitle("");
    onSaved();
  }

  return (
    <div style={{ display: "flex", gap: 6, marginTop: 8 }}>
      <select value={noteType} onChange={(e) => setNoteType(e.target.value as typeof noteType)}>
        {TYPES.map((t) => <option key={t} value={t}>{t}</option>)}
      </select>
      <input style={{ flex: 1 }} placeholder="Add a note…" value={title}
        onChange={(e) => setTitle(e.target.value)} onKeyDown={(e) => e.key === "Enter" && save()} />
      <button onClick={save}>Pin</button>
    </div>
  );
}
```

- [ ] **Step 2: Create `frontend/src/TranscriptPaste.tsx`**

```tsx
import { useState } from "react";
import { createTranscript } from "./api";

export function TranscriptPaste({ clientSysId, onSaved }:
  { clientSysId: string; onSaved: () => void }) {
  const [text, setText] = useState("");
  const [open, setOpen] = useState(false);

  async function save() {
    if (!text.trim()) return;
    await createTranscript({ client: clientSysId, full_text: text, source: "manual" });
    setText("");
    setOpen(false);
    onSaved();
  }

  if (!open) return <button onClick={() => setOpen(true)}>+ Paste transcript</button>;
  return (
    <div style={{ marginTop: 8 }}>
      <textarea style={{ width: "100%", height: 120 }} placeholder="Paste meeting transcript text…"
        value={text} onChange={(e) => setText(e.target.value)} />
      <div style={{ display: "flex", gap: 6 }}>
        <button onClick={save}>Save transcript</button>
        <button onClick={() => setOpen(false)}>Cancel</button>
      </div>
    </div>
  );
}
```

- [ ] **Step 3: Commit**

```bash
cd .. && git add frontend/src/NoteComposer.tsx frontend/src/TranscriptPaste.tsx && git commit -m "feat: NoteComposer + TranscriptPaste components"
```

---

## Task 9: ClientsView and DossierView + routing

**Files:**
- Create: `frontend/src/ClientsView.tsx`, `frontend/src/DossierView.tsx`
- Modify: `frontend/src/App.tsx`

Routing is minimal hash-based state (no router dependency): `App` holds `view` (`now | clients | dossier`) and a `selectedClient` sys_id.

- [ ] **Step 1: Create `frontend/src/ClientsView.tsx`**

```tsx
import { useEffect, useState } from "react";
import type { Client } from "./types";
import { getClients } from "./api";

export function ClientsView({ onOpen }: { onOpen: (sysId: string) => void }) {
  const [clients, setClients] = useState<Client[]>([]);
  useEffect(() => { getClients().then(setClients); }, []);
  return (
    <div style={{ maxWidth: 720, margin: "2rem auto", fontFamily: "system-ui" }}>
      <h1>Clients</h1>
      <ul style={{ listStyle: "none", padding: 0 }}>
        {clients.map((c) => (
          <li key={c.sys_id} style={{ padding: "8px 0", borderBottom: "1px solid #eee" }}>
            <button onClick={() => onOpen(c.sys_id!)} style={{ background: "none", border: "none", color: "#0a7", cursor: "pointer", fontSize: 16 }}>
              {c.name}{c.short_code ? ` (${c.short_code})` : ""}
            </button>
          </li>
        ))}
      </ul>
    </div>
  );
}
```

- [ ] **Step 2: Create `frontend/src/DossierView.tsx`**

```tsx
import { useEffect, useState } from "react";
import type { Dossier } from "./types";
import { getDossier } from "./api";
import { OrgChart } from "./OrgChart";
import { NoteComposer } from "./NoteComposer";
import { TranscriptPaste } from "./TranscriptPaste";

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <section style={{ marginTop: 20 }}>
      <h2 style={{ fontSize: 16, borderBottom: "2px solid #0a7", paddingBottom: 4 }}>{title}</h2>
      {children}
    </section>
  );
}

export function DossierView({ clientSysId, onBack }: { clientSysId: string; onBack: () => void }) {
  const [d, setD] = useState<Dossier | null>(null);
  const refresh = () => getDossier(clientSysId).then(setD);
  useEffect(() => { refresh(); }, [clientSysId]);
  if (!d) return <p style={{ margin: "2rem" }}>Loading…</p>;

  return (
    <div style={{ maxWidth: 820, margin: "2rem auto", fontFamily: "system-ui" }}>
      <button onClick={onBack}>← Clients</button>
      <h1>{d.client.name}</h1>

      <Section title={`Open tasks (${d.open_tasks.length})`}>
        <ul>{d.open_tasks.map((t) => <li key={t.sys_id}>{t.is_commitment ? "🤝 " : ""}{t.title} <em style={{ color: "#888" }}>{t.priority}</em></li>)}</ul>
      </Section>

      <Section title={`Contacts (${d.contacts.length})`}>
        <OrgChart contacts={d.contacts} />
      </Section>

      <Section title={`Engagements (${d.engagements.length})`}>
        <ul>{d.engagements.map((e) => <li key={e.sys_id}>{e.name} <em style={{ color: "#888" }}>{e.status}</em></li>)}</ul>
      </Section>

      <Section title={`Themes (${d.themes.length})`}>
        <ul>{d.themes.map((t) => <li key={t.sys_id}>{t.name} <em style={{ color: "#888" }}>{t.status}</em></li>)}</ul>
      </Section>

      <Section title={`Meetings (${d.meetings.length})`}>
        <ul>{d.meetings.map((m) => <li key={m.sys_id}>{m.title} <em style={{ color: "#888" }}>{m.type}</em></li>)}</ul>
        <TranscriptPaste clientSysId={clientSysId} onSaved={refresh} />
      </Section>

      <Section title={`Notes & RAID (${d.notes.length})`}>
        <ul>{d.notes.map((n) => <li key={n.sys_id}><strong>[{n.note_type}]</strong> {n.title}</li>)}</ul>
        <NoteComposer targetTable="client" targetId={clientSysId} onSaved={refresh} />
      </Section>
    </div>
  );
}
```

- [ ] **Step 3: Replace `frontend/src/App.tsx`** with minimal routing

```tsx
import { useState } from "react";
import { NowView } from "./NowView";
import { ClientsView } from "./ClientsView";
import { DossierView } from "./DossierView";

type View = "now" | "clients" | "dossier";

export default function App() {
  const [view, setView] = useState<View>("now");
  const [clientSysId, setClientSysId] = useState<string | null>(null);

  return (
    <div>
      <nav style={{ display: "flex", gap: 12, padding: "8px 16px", borderBottom: "1px solid #ddd", fontFamily: "system-ui" }}>
        <button onClick={() => setView("now")}>Now</button>
        <button onClick={() => setView("clients")}>Clients</button>
      </nav>
      {view === "now" && <NowView />}
      {view === "clients" && (
        <ClientsView onOpen={(id) => { setClientSysId(id); setView("dossier"); }} />
      )}
      {view === "dossier" && clientSysId && (
        <DossierView clientSysId={clientSysId} onBack={() => setView("clients")} />
      )}
    </div>
  );
}
```

- [ ] **Step 4: Type-check / build**

Run: `cd frontend && npm run build`
Expected: tsc + vite build succeed (no type errors).

- [ ] **Step 5: Commit**

```bash
cd .. && git add frontend/src/ClientsView.tsx frontend/src/DossierView.tsx frontend/src/App.tsx && git commit -m "feat: clients list + dossier view + routing"
```

---

## Task 10: Manual end-to-end verification (against the mock)

- [ ] **Step 1: Start backend (fake mode)**

```bash
cd backend && source .venv/bin/activate && USE_FAKE=true uvicorn app.main:app --reload --port 8000
```

- [ ] **Step 2: Seed a client with relations**

```bash
CID=$(curl -s -X POST localhost:8000/api/clients -H 'content-type: application/json' -d '{"name":"Acme Corp","short_code":"ACME"}' | python3 -c 'import sys,json;print(json.load(sys.stdin)["sys_id"])')
curl -s -X POST localhost:8000/api/contacts -H 'content-type: application/json' -d "{\"name\":\"Jane Doe\",\"client\":\"$CID\",\"role_title\":\"VP IT\",\"sentiment\":\"champion\"}"
MGR=$(curl -s -X POST localhost:8000/api/contacts -H 'content-type: application/json' -d "{\"name\":\"Bob Boss\",\"client\":\"$CID\",\"role_title\":\"CIO\"}" | python3 -c 'import sys,json;print(json.load(sys.stdin)["sys_id"])')
# make Jane report to Bob
JANE=$(curl -s "localhost:8000/api/contacts?client=$CID" | python3 -c 'import sys,json;print([c for c in json.load(sys.stdin) if c["name"]=="Jane Doe"][0]["sys_id"])')
curl -s -X PATCH localhost:8000/api/contacts/$JANE -H 'content-type: application/json' -d "{\"reports_to\":\"$MGR\"}"
curl -s -X POST localhost:8000/api/engagements -H 'content-type: application/json' -d "{\"name\":\"Migration\",\"client\":\"$CID\",\"status\":\"at_risk\"}"
curl -s -X POST localhost:8000/api/tasks -H 'content-type: application/json' -d "{\"title\":\"Send Acme SOW\",\"client\":\"$CID\",\"priority\":\"high\",\"is_commitment\":true}"
curl -s "localhost:8000/api/clients/$CID/dossier" | python3 -m json.tool
```
Expected: the dossier JSON shows the client, both contacts, the engagement, the open task, and empty meetings/themes/notes.

- [ ] **Step 3: Frontend click-through**

```bash
cd frontend && npm run dev   # http://localhost:5173
```
Open the app → **Clients** → click **Acme Corp**. Expected: dossier page shows Open tasks (Send Acme SOW 🤝), an org chart with **Bob Boss → Jane Doe (⭐)**, the at-risk engagement, and working **+ Paste transcript** and note composer (add a note, see it appear after save).

- [ ] **Step 4: Final full backend suite**

Run: `cd backend && source .venv/bin/activate && pytest -q`
Expected: all Plan 1 + Plan 2 tests green.

---

## Self-Review (author)

**Spec coverage:** Contact/Engagement/Theme/Meeting/Transcript/Note models ✓ (T1), generic CRUD ✓ (T2), six routers wired ✓ (T3), polymorphic note pin ✓ (T4), dossier aggregate ✓ (T5), frontend types/api ✓ (T6), org chart ✓ (T7), note + transcript composers ✓ (T8), clients list + dossier + routing ✓ (T9), e2e verify ✓ (T10). Transcript file-parsing / Teams pull, Tags/Links/KeyDates, AI, decks explicitly deferred.

**Placeholder scan:** none — complete code in every code step; the DRY `crud_router` is written once and reused, not "similar to".

**Type consistency:** `crud_router(name, table_suffix, model)` signature used identically in T3; pydantic field names (`reports_to`, `target_table`, `target_id`, `note_type`, `full_text`, `role_title`) match the SN reference in Plan 1 and the TS interfaces in T6; `Dossier` keys (`client/contacts/engagements/themes/open_tasks/meetings/notes`) match between `build_dossier` (T5) and `types.ts`/`DossierView` (T6/T9).

---

## After this plan
- **Plan 3:** Tags, Links, KeyDates + reminders, Activity timeline, stale-client radar, export/backup job.
- **Plan P2 (M365):** Entra recon → email + calendar, email→task, transcript auto-pull, meeting-prep assembler, morning briefing.
- **Plan P3:** AI summaries/drafting/prioritization, semantic search, decks (SN brand).
