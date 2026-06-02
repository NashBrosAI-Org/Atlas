# Atlas — Guardrails (read before changing anything)

These are the **hard rules** for Atlas. They override convenience. If a change would
violate one, stop and raise it — don't route around it. Each rule has a *why*, because a
rule whose reason you don't understand is a rule you'll eventually break.

## Hard rules

1. **No corporate M365 data on the personal Mac.**
   Development happens on the personal Mac against `FakeServiceNow` / synthetic data only.
   Real credentials and the live ServiceNow instance are touched **only on the work Mac**.
   *Why:* corporate email/calendar content must not land on uncontrolled hardware.

2. **Secrets never enter the repo.**
   OAuth client secret, refresh token, and passwords live in `backend/.env` (gitignored)
   and the **macOS Keychain** (`keyring`, service `atlas-sn`). Only `.env.example` is committed.
   *Why:* a leaked secret in git history is forever.

3. **The SN employee instance is NOT a durable archive.**
   It is "not infinite" (can be reclaimed). Therefore the export/backup of transcripts +
   emails + the Update Set is **mandatory, not optional** — the instance is never the only copy.
   *Why:* losing the instance must not lose the data.

4. **Retention-past-policy is an accepted, named risk.**
   Routing email/meeting content into the SN instance to retain it beyond the company's
   retention window is a **legal/compliance risk the user has consciously accepted** and will
   own with IT. Keep this visible; do not silently expand what corporate data gets retained.
   *Why:* this is the single highest-risk decision in the project — it stays on the board.

5. **Schema names mirror CSM/PPM.**
   `Client`→Account, `Engagement`→Project, `Contact`→Contact, etc. Don't introduce names that
   make a future migration to CSM/PPM a rebuild instead of a mapping.

6. **AI is additive, not core.**
   v1 prioritization ("Now" view) is **deterministic** (priority → due date → commitment).
   No feature may *require* the Anthropic API to function; AI only enhances (Phase 3).

7. **Dev → clone, never copy data.**
   Build on the personal Mac → private git repo → clone to the work Mac. Code flows through
   git; data never does.

## Named risks (keep current)

| # | Risk | Owner / mitigation |
|---|------|--------------------|
| R1 | Retention past company policy (legal/compliance) | User owns w/ IT; rule #4 |
| R2 | Employee instance "not infinite" → data loss | Mandatory export/backup (rule #3) |
| R3 | Entra app-reg / Graph + Teams-transcript perms may need IT | Recon spike gates P2; not v1 |
| R4 | Work-laptop proxy may block `*.service-now.com` / Graph | Recon R1 before go-live (Task 15) |

## Per-component guardrails
- Backend: [`components/backend.md`](components/backend.md)
- ServiceNow: [`components/servicenow.md`](components/servicenow.md)
- Frontend: [`components/frontend.md`](components/frontend.md)

## See also
- Architecture: [`ARCHITECTURE.md`](ARCHITECTURE.md)
- Data model: [`DATA-MODEL.md`](DATA-MODEL.md)
- Progress: [`PROGRESS.md`](PROGRESS.md)
- The implementation plan: [`superpowers/plans/2026-06-02-atlas-foundation.md`](superpowers/plans/2026-06-02-atlas-foundation.md)
