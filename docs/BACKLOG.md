# Atlas — Backlog (queue)

Smaller feature ideas and gaps not yet on the phase roadmap. The phase roadmap +
decision log live in [PROGRESS.md](PROGRESS.md); this file is the lighter-weight queue.
Status: 🔵 queued · 🟡 in progress · 🟢 done.

## Requested

- 🟢 **Client + email-domains/aliases manager.** Editable **Clients** tab listing the user's clients
  with per-client **email domains** and **aliases** (off-domain addresses). Drives M365
  auto-association ([`m365.match_client`](../backend/app/m365.py) matches domain OR alias). Backend
  `Client.email_aliases` + `PATCH /api/clients/{id}`. Shipped (PR #37).

- 🟡 **Contact role-titles manager, autofilled from email signature (editable).** Add/edit contacts'
  `role_title` (and email, reports-to, sentiment). *Today:* `role_title` is display-only in the
  OrgChart; `createContact` exists but is wired to no form; there is **no** signature parsing.
  **Two parts:** (a) contact CRUD UI — ✅ **shipped (PR #39)** (`ContactEditor`); (b) signature →
  fields extraction — an **AI/parsing capability**, still queued under P3 behind the `AIClient` seam
  (a `FakeAI`-backed `extract_contact_fields(signature) -> {role_title, email, phone}`; user edits
  before save). See the P3 extraction item below.

## Recommended

- 🟢 **Add-task form on Now** — a `TaskComposer` (title, priority, client, due date, commitment) at
  the top of the Now list; defaults the client to the active filter. Shipped (PR #38).
- 🟢 **Client CRUD UI** — create / edit clients (name, short_code, status, email_domains, aliases,
  notes) on the Clients tab. Shipped (PR #37).
- 🟢 **Contact CRUD UI** — add/edit contacts on the dossier (`ContactEditor`: composer + per-row
  Edit/Save; name, role_title, email, phone, sentiment, reports_to). Shipped (PR #39). Part (b) of
  the role-titles request — **email-signature autofill** — remains queued under P3 extraction below.
### Data safety & correctness
- 🟢 **Restore-from-backup.** `import_snapshot` upserts by `sys_id` (preserving refs); `restore_latest`
  + `POST /api/backup/restore` + a Settings "Restore latest" button. Shipped (PR #41). Follow-up:
  sys_id-remap pass for a full-wipe *live* restore (SN may not honor a supplied `sys_id` on insert).
- 🟢 **SN list pagination.** `HttpServiceNow.list` pages through `sysparm_limit`/`sysparm_offset`
  (1000/page) until a short page, so large tables come back whole. Shipped (PR #42).
- 🔵 **Frontend tests.** The frontend has no tests; add Vitest smoke tests on the composers/managers
  (the kind of bugs the manual reviews caught).

### AI (P3, behind `FakeAI` — buildable now)
- 🟢 **P3 extraction capability** — `extract_contact_fields` (AI-primary + regex fallback) +
  `POST /api/ai/extract/contact` + ContactEditor "Autofill from signature". Shipped (PR #44). The
  role-titles autofill (D32 part b) is done; transcript/email action-item extraction can reuse it.
- 🟢 **P3 drafting** — `draft_client_followup` + `POST /api/ai/draft/client/{id}` + a dossier
  "Draft follow-up" button (copy-only, never auto-sends). Shipped (PR #45).
- 🟢 **P3 prioritization-assist** — `suggest_focus` (advisory) + `POST /api/ai/prioritize` + a Now
  "AI focus" panel. Suggestions only; never writes `priority`/reorders (rule #6). Shipped (PR #46).

### UX / product
- 🔵 **Association review UI (build now, per user)** — confirm/correct auto-associated emails & meetings
  so the user can trust/fix domain-alias matching. Built against the fake now; fully exercised once M365 is live.
- 🟢 **Quick-capture** — a global "＋ Capture" nav button opens a modal (Task|Note, optional client,
  Escape/click-out to close). Shipped (PR #48).
- 🟢 **Global search** — `GET /api/search` across clients/tasks/contacts/notes/engagements + a Search
  tab. Shipped (PR #47).
- 🔵 **Self-documenting UI (user request)** — info icons / inline explainer text next to fields across the app (what each field does, how domains/aliases drive matching, etc.), so the tool teaches its own use.
- 🔵 **Modal a11y** — `MeetingPrepPanel` (and future modals) need Escape-to-close + focus handling.
- 🔵 **Retention controls UI** — surface/choose which mail folders get ingested (keeps the R1/D2
  retained-scope visible and user-controlled).
- 🔵 **Prioritization explainability** — show *why* a task ranks where it does (priority → due →
  commitment), reinforcing that the Now view is deterministic.

### Project hygiene
- 🟡 **`.md` guardrail consolidation** — slim the always-loaded `CLAUDE.md`, move per-language
  conventions to [CODE-STANDARDS.md](CODE-STANDARDS.md), add auto-loaded nested `CLAUDE.md` in
  `backend/`/`frontend/`/`servicenow/`. **Building this session.**

> Removed: ~~CSV import~~ — deemed unnecessary by the user.
> Retention-controls UI + association-review UI: **building now as stubs (user's call)**, even though
> they're most useful once live M365 is connected.
> Gated elsewhere (tracked in [PROGRESS.md](PROGRESS.md), not here): live M365 (`HttpGraph` + auth,
> work-Mac, Entra recon) and live AI (`AnthropicAI`, needs `ANTHROPIC_API_KEY`).
>
> **Decks (P3, own plan):** meeting/QBR decks as `.pptx` + web on the official ServiceNow brand kit
> — tracked in the P3 plan, not duplicated here.

## Done

_(items move here as they ship, with the PR #.)_
