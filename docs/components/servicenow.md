# Component: ServiceNow (scoped app — backend / system of record)

**Purpose:** Hold the data (clients, contacts, tasks, meetings, transcripts, emails, notes,
etc.), be the **skill-building** surface, and be the **demo to coworkers** ("look what I
built"). Backend only — the daily UI is the React app, **not** a ServiceNow Workspace.

**Instance:** the user's ServiceNow **employee instance** (clean, no real data). It is the
only ServiceNow in scope; there is no separate corporate ticketing instance.

## Boundaries
- ✅ Build as a **custom scoped app** with custom tables (lightweight). Reference real CSM/PPM
  later as a demo flex, but don't drag CSM/PPM bloat into the daily model now.
- ✅ All config (app, tables, OAuth endpoint) is captured in an **Update Set** and exported to
  the repo under `servicenow/updateset/` (config only — never data).
- ❌ The instance is **not a durable archive** — it can be reclaimed. It must never be the only
  copy of transcripts/emails. See [GUARDRAILS](../GUARDRAILS.md) rule #3.

## Guardrails
- **Migration-friendly names.** Client→Account, Engagement→Project, Contact→Contact, etc.
- **Polymorphic via Document ID.** `Note.target` and `TagM2M.target` use SN's Document ID field
  type, not a stack of optional references.
- **Retention is the accepted, named risk** (GUARDRAILS rule #4). Don't quietly broaden what
  corporate content gets pushed here.
- **Export discipline.** Whenever the schema changes: mark the Update Set complete, export XML,
  commit it. The eventual scheduled job (Plan 3) backs up the *data* too.

## Tables (full fields in [DATA-MODEL](../DATA-MODEL.md) and the plan)
`client · contact · engagement · theme · task · meeting · transcript · email · note · deck ·
key_date · link · tag · tag_m2m`

## OAuth (how the backend connects — Plan 1 Task 15)
- **System OAuth > Application Registry > Create OAuth API endpoint for external clients.**
- Client ID/Secret + a long refresh-token lifespan. The backend's `TokenManager` does a
  password grant once, then caches the **refresh token in the macOS Keychain**.
- The OAuth secret/credentials live in `backend/.env` on the **work Mac only** — never committed.

## Build checklist (Plan 1 Tasks 1–6, done by the user in the instance)
- [ ] Task 1: start Update Set `Atlas - Plan 1`; create scoped app `Atlas` (note the scope, e.g. `x_<vendor>_atlas`).
- [ ] Tasks 2–6: create all 14 tables per [DATA-MODEL](../DATA-MODEL.md) with the field types in the plan; seed a couple of demo records (Acme Corp + 2 tasks) for the go-live smoke test.
