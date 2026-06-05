# Atlas — Backlog (queue)

Smaller feature ideas and gaps not yet on the phase roadmap. The phase roadmap +
decision log live in [PROGRESS.md](PROGRESS.md); this file is the lighter-weight queue.
Status: 🔵 queued · 🟡 in progress · 🟢 done.

## Requested

- 🟡 **Client + email-domains/aliases manager.** A surface where the user lists their ~6 clients and,
  per client, the **email suffixes** (domains, e.g. `acme.com`) **and aliases** (specific addresses a
  client also writes from, e.g. a personal gmail). Control surface for `Client.email_domains`/
  `email_aliases` — which drive M365 auto-association ([`m365.match_client`](../backend/app/m365.py)).
  *Why it matters:* accurate domain/alias mapping makes email→client and calendar→client association
  correct when P2 goes live. **Building this session** as an editable **Clients** tab (the natural
  home; better UX than burying it in Settings). Includes the backend `email_aliases` field + matching.

- 🟡 **Contact role-titles manager, autofilled from email signature (editable).** Add/edit contacts'
  `role_title` (and email, reports-to, sentiment). *Today:* `role_title` is display-only in the
  OrgChart; `createContact` exists but is wired to no form; there is **no** signature parsing.
  **Two parts:** (a) contact CRUD UI — **building this session** (deterministic); (b) signature →
  fields extraction — an **AI/parsing capability**, queued under P3 behind the `AIClient` seam
  (a `FakeAI`-backed `extract_contact_fields(signature) -> {role_title, email, phone}`; user edits
  before save). See the P3 extraction item below.

## Recommended

- 🟡 **Add-task form on Now** — the Now view only *completes* tasks; new ones come only from demo
  seed / mail-sync / API. **Building this session.** The most basic daily action, currently missing.
- 🟡 **Client CRUD UI** — create / edit / archive clients (name, short_code, status, email_domains,
  aliases, notes). **Building this session** (the Clients manager above).
- 🟡 **Contact CRUD UI** — add/edit contacts inline on the dossier (name, role_title, email, phone,
  reports_to, sentiment). **Building this session.**
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
