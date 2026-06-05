# P2 — Entra / Microsoft Graph Recon Checklist (the gate)

This is the **gating spike** for all of P2 (Microsoft 365). It addresses named risks **R3**
(Entra app-registration / Graph + Teams-transcript permissions may need IT) and **R4** (the
work-laptop proxy may block `login.microsoftonline.com` / `graph.microsoft.com`).

> **Where this runs:** the **work Mac**, against the corporate tenant. Per hard rule #1, no
> corporate M365 data touches the personal Mac — everything on the personal Mac is built behind
> `FakeGraph` (see the P2 plan). This checklist produces *facts and decisions*, not corporate
> content; record the decisions below and commit them, but **never** paste real mail/calendar
> content into the repo.

**Outcome of this spike:** the "Recon results" table at the bottom is filled in, and we know
whether P2 live integration is GO / GO-with-caveats / BLOCKED. The live `HttpGraph` + auth tasks in
the P2 plan stay parked until this is GO.

---

## 0. Decide the permission model before touching the portal

Atlas reads **the signed-in user's own** mailbox and calendar — not the whole tenant. That means
**delegated** permissions via an interactive sign-in, **not** application permissions:

| Capability | Graph scope (delegated) | Notes |
|---|---|---|
| Read mail | `Mail.Read` | The core of email→task / retention (D2). |
| Read calendar | `Calendars.Read` | Meeting-prep + morning briefing. |
| Keep a refresh token | `offline_access` | So Atlas reconnects without re-login each launch. |
| Identify the user | `User.Read` | Sanity check + display name. |
| Teams transcripts | `OnlineMeetingTranscript.Read.All` | **Application** permission, admin-only, organizer-policy gated. **Out of P2 scope** — transcripts stay manual-paste (P1). Track as a separate, harder spike. |

**Auth flow:** desktop app, no client secret on disk → **authorization-code flow with PKCE**
(preferred) or **device-code flow** (fallback if the embedded browser is awkward). Both are public-
client flows; neither stores a secret. The refresh token goes in the macOS Keychain, same as the
ServiceNow password (D11/D14).

---

## 1. App registration (Entra ID / Azure AD)

- [ ] Sign in to the Entra admin center for the corporate tenant.
- [ ] **App registrations → New registration.** Name: `Atlas (personal command center)`.
- [ ] Supported account types: **Single tenant** (this org only).
- [ ] Platform: **Mobile and desktop applications**; add redirect URI `http://localhost` (auth-code
      + PKCE) and enable **"Allow public client flows"** (needed for device-code fallback).
- [ ] Record **Application (client) ID** and **Directory (tenant) ID**.
- [ ] **API permissions → add** the delegated scopes from the table above (`Mail.Read`,
      `Calendars.Read`, `offline_access`, `User.Read`).
- [ ] Note whether each shows **"Admin consent required = Yes"** for this tenant.

## 2. Consent — can *you* consent, or does IT have to?

- [ ] Attempt user consent on first sign-in (the flow will prompt).
- [ ] If it says **"Need admin approval"** → this is the R3 blocker. Capture the exact scope(s)
      requiring admin consent and raise a request with IT (grant admin consent for the Atlas app's
      delegated scopes for your account only). Record the ticket/owner in the results table.
- [ ] Confirm whether a **Conditional Access** policy or **app-consent policy** blocks the grant.

## 3. Network / proxy reachability (R4) — run on the work laptop, on the work network

- [ ] `curl -sS -o /dev/null -w "%{http_code}\n" https://login.microsoftonline.com/` → expect a
      redirect/200, not a hang or proxy error.
- [ ] `curl -sS -o /dev/null -w "%{http_code}\n" https://graph.microsoft.com/v1.0/$metadata` →
      expect `200`.
- [ ] If either fails: identify the proxy. Check `HTTPS_PROXY`/`HTTP_PROXY` env, and whether the
      proxy does **TLS interception** (a corporate root CA in the chain) — if so, `httpx` must trust
      that CA bundle (`SSL_CERT_FILE` / `verify=<ca-bundle>`). Record the proxy URL + CA path.
- [ ] Confirm **MFA** behaviour on the chosen flow (device-code can interact badly with some CA
      policies; auth-code in a real browser usually satisfies MFA cleanly).

## 4. Smoke test the token + one real call (work Mac)

- [ ] Using the registered client ID + tenant ID, acquire a token interactively (MSAL device-code
      is the quickest one-off: `az`/`msal` or a 20-line script). **Do not commit the token.**
- [ ] `GET https://graph.microsoft.com/v1.0/me` with the token → confirm your identity.
- [ ] `GET https://graph.microsoft.com/v1.0/me/messages?$top=1&$select=subject,from,receivedDateTime`
      → confirm a `200` and the shape (you only need the *shape*, not the content — note the field
      names so `FakeGraph` mirrors them).
- [ ] `GET https://graph.microsoft.com/v1.0/me/calendarView?startDateTime=…&endDateTime=…&$top=1`
      → confirm a `200` and the shape.
- [ ] Note paging: Graph returns `@odata.nextLink`; record that `HttpGraph` must follow it.

## 5. Decide retention scope (keep R1/D2 visible)

- [ ] Confirm which mail folders Atlas ingests (e.g. Inbox + Sent only, or flagged-only) so we don't
      silently broaden retained corporate content (rule #4). Record the chosen filter — it becomes a
      setting (`m365_mail_filter`).

---

## Recon results (fill in, then commit — facts/decisions only, no corporate content)

| Item | Result |
|---|---|
| Tenant (directory) ID | _e.g. captured, stored in Keychain/.env on work Mac — record only "captured", not the value if it's sensitive_ |
| Client (application) ID | |
| Delegated scopes granted | `Mail.Read` / `Calendars.Read` / `offline_access` / `User.Read` — granted? |
| Admin consent needed? | yes/no — which scopes; IT ticket + owner |
| Auth flow chosen | auth-code+PKCE / device-code |
| Proxy blocks Graph? (R4) | yes/no; proxy URL + CA bundle path if TLS-intercepted |
| MFA / Conditional Access | clean / needs work — describe |
| `/me/messages` shape verified | yes/no — field names to mirror in `FakeGraph` |
| `/me/calendarView` shape verified | yes/no |
| Mail ingest filter (retention) | e.g. Inbox+Sent, or flagged-only |
| **Verdict** | **GO / GO-with-caveats / BLOCKED** + one line |

When the verdict is GO, return to the P2 plan and unpark the **Phase 4 — live `HttpGraph` + auth**
tasks (work-Mac only).
