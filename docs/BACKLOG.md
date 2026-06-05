# Atlas — Backlog (queue)

Smaller feature ideas and gaps not yet on the phase roadmap. The phase roadmap +
decision log live in [PROGRESS.md](PROGRESS.md); this file is the lighter-weight queue.
Status: 🔵 queued · 🟡 in progress · 🟢 done.

## Requested

- 🔵 **Client + email-domains/aliases manager (Settings).** A page where the user lists
  their ~6 clients and, per client, the **email suffixes** (domains, e.g. `acme.com`) **and
  aliases** (specific addresses a client also writes from, e.g. a personal gmail). This is the
  control surface for `Client.email_domains` — which today is only set via demo seed / direct API
  yet already drives M365 auto-association ([`m365.match_client`](../backend/app/m365.py)).
  *Why it matters:* accurate domain/alias mapping is what makes email→client and calendar→client
  association correct when P2 goes live. **Needs first:** client CRUD UI (see below) — there's no
  way to create/edit a client in the app today. **Aliases also needs a small backend change:**
  `match_client` currently matches whole domains only; add an explicit per-client address list
  (e.g. `Client.email_aliases`) and check it alongside `email_domains`.

- 🔵 **Contact role-titles manager, autofilled from email signature (editable).** A page/section to
  add and edit contacts' `role_title` (and the rest: email, reports-to, sentiment). Role title (and
  email/phone) should be **auto-suggested by parsing the sender's email signature**, with the user
  able to accept/edit. *Today:* `Contact.role_title` is display-only in the OrgChart; `createContact`
  exists in the API but is wired to no form; there is **no** signature parsing. **Two parts:**
  (a) contact CRUD UI (deterministic, buildable now); (b) signature → fields extraction, which is an
  **AI/parsing capability** — fits **P3** behind the `AIClient` seam (a `FakeAI`-backed
  `extract_contact_fields(signature) -> {role_title, email, phone}`; additive, user edits before save).

## Recommended (gaps found while scoping the above)

- 🔵 **Client CRUD UI** — create / edit / archive clients (name, short_code, status, email_domains,
  aliases, notes). Prerequisite for the email-domains manager; closes the "clients are read-only in
  the app" gap (they can only be demo-seeded or POSTed directly today).
- 🔵 **Contact CRUD UI** — add/edit contacts inline on the dossier (name, role_title, email, phone,
  reports_to, sentiment). Prerequisite for the role-titles manager; the OrgChart can only display.
- 🔵 **CSV import for clients & contacts** — fast onboarding of the ~6 accounts and their people
  without hand-entry (and a natural place to bulk-set email domains).
- 🔵 **P3 extraction capability** — generalize "parse an email signature" into an `AIClient`-backed
  extractor reused for contacts, and later for pulling action items from transcripts/emails.
- 🔵 **Per-client address aliases in association** — backend `match_client` enhancement noted above
  (explicit addresses in addition to domains), so association handles clients who email from
  off-domain addresses.

## Done

_(none yet — items move here as they ship, with the PR #.)_
