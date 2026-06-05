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
- 🟡 **Restore-from-backup.** `app/backup.py` can *export* every table but there's **no import/restore**
  — for risk **R2** (instance reclaim) a backup you can't restore is half a mitigation. Add
  `import_export(file)` + `POST /api/backup/restore` (idempotent upsert by `sys_id`) + a Settings
  "Restore" affordance. **Building this session.**
- 🟡 **SN list pagination.** `HttpServiceNow.list` does a single GET — fine for ~6 clients but
  transcripts/emails will hit SN's default row cap. Add `sysparm_limit`/`sysparm_offset` paging
  (mirrors the `@odata.nextLink` note for Graph). **Building this session.**
- 🔵 **Frontend tests.** The frontend has no tests; add Vitest smoke tests on the composers/managers
  (the kind of bugs the manual reviews caught).

### AI (P3, behind `FakeAI` — buildable now)
- 🔵 **P3 extraction capability** — generalize "parse an email signature" into an `AIClient`-backed
  extractor reused for contacts (the role-titles autofill, part b above), and later for pulling
  action items from transcripts/emails.
- 🔵 **P3 drafting** — draft a follow-up email / note from a client or meeting context (Sonnet-class);
  inserts a draft into the composer for the human to edit; never auto-sends.
- 🔵 **P3 prioritization-assist** — AI *suggests* an ordering/flags for open tasks in a separate panel;
  **must not** write `priority` or reorder the deterministic Now list (rule #6) — it annotates.

### UX / product
- 🔵 **Association review UI** — confirm/correct auto-associated emails & meetings, so the user can
  trust (and fix) the domain/alias matching once M365 is live.
- 🔵 **Quick-capture** — a global "new note / new task" affordance for fast daily entry.
- 🔵 **Global search** — deterministic keyword search across clients/tasks/notes (cheap interim before
  P3 semantic search).
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
> Gated elsewhere (tracked in [PROGRESS.md](PROGRESS.md), not here): live M365 (`HttpGraph` + auth,
> work-Mac, Entra recon) and live AI (`AnthropicAI`, needs `ANTHROPIC_API_KEY`).
>
> **Decks (P3, own plan):** meeting/QBR decks as `.pptx` + web on the official ServiceNow brand kit
> — tracked in the P3 plan, not duplicated here.

## Done

_(items move here as they ship, with the PR #.)_
