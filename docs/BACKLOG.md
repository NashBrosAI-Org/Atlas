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
- 🔵 **P3 extraction capability** — generalize "parse an email signature" into an `AIClient`-backed
  extractor reused for contacts, and later for pulling action items from transcripts/emails. (P3.)
- 🔵 **Association review UI** — confirm/correct auto-associated emails & meetings, so the user can
  trust (and fix) the domain/alias matching once M365 is live.
- 🔵 **Quick-capture** — a global "new note / new task" affordance for fast daily entry.

> Removed: ~~CSV import~~ — deemed unnecessary by the user.
> Gated elsewhere (tracked in [PROGRESS.md](PROGRESS.md), not here): live M365 (`HttpGraph` + auth,
> work-Mac, Entra recon) and live AI (`AnthropicAI`, needs `ANTHROPIC_API_KEY`).

## Done

_(items move here as they ship, with the PR #.)_
