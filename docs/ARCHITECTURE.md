# Atlas — Architecture

Atlas is a **client-centric command center** for someone juggling ~6 customer accounts. It is
a local app on the work Mac, backed by a ServiceNow scoped app, with Microsoft 365 and AI
layered on later.

## The three tiers (sorted by what's allowed to live where)

| Tier | Holds | Why allowed |
|------|-------|-------------|
| **ServiceNow employee instance** (cloud) | Tasks, clients, contacts, meetings, transcripts, emails, notes, synthetic/demo data — the system of record | User-controlled corporate-adjacent cloud; also the skill-building + demo surface |
| **Work Mac — local** | The FastAPI service, the React app, generated `.pptx`, *transient* M365 pulls, the export/backup files | Sanctioned corporate hardware |
| **Personal Mac — dev only** | Source code, mocks, synthetic fixtures | Never corporate data (see [CLAUDE.md](../CLAUDE.md) rule #1) |

## Shape

```
ServiceNow scoped app (DB + workflows)
        ▲  OAuth 2.0 / Table REST API
        │
FastAPI service  (localhost:8000, work Mac)  ──►  Microsoft Graph   (email/cal — Phase 2)
        │                                    ──►  Anthropic API     (AI — Phase 3, additive)
        │                                    ──►  python-pptx + web  (decks — Phase 3)
        ▼  JSON over localhost
React + Vite app  (localhost:5173)
```

## Key design decisions
- **SN is the backend, the local app is the frontend.** No ServiceNow Workspace UI — the
  custom React app is the daily surface.
- **ServiceNow access sits behind an interface** (`ServiceNowClient`) with an in-memory
  `FakeServiceNow`, so the whole backend is built and tested with **no live instance and no
  corporate data** on the personal Mac.
- **Deterministic-first.** The core value (what to work on) is plain task management, not AI.
- **Migration-friendly schema** (CSM/PPM-aligned names) — see [DATA-MODEL](DATA-MODEL.md).

## Phasing
- **P1** — SN-backed command center (manual entry, manual transcript upload). *Plan 1 = foundation slice.*
- **P2** — Microsoft 365 (email + calendar), gated on the Entra recon spike.
- **P3** — AI (summaries/drafting/prioritization), semantic search, decks (`.pptx` + web, SN brand).
