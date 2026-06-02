# Component: Frontend (React + Vite app)

**Purpose:** The daily surface. A fast, custom local UI so the user never has to work inside a
ServiceNow Workspace. Runs at `localhost:5173`, talks only to the local backend.

**Location:** `frontend/`

## Boundaries
- ✅ Talk **only** to the local FastAPI backend at `http://localhost:8000/api` (via `src/api.ts`).
- ❌ Never call ServiceNow or Microsoft Graph directly from the browser. No tokens, secrets, or
  OAuth flows in the frontend. The backend owns all credentials and external calls.
- ❌ No corporate data cached to browser storage beyond what's needed to render.

## Guardrails
- **Types mirror the backend.** `src/types.ts` (`Client`, `Task`) must match the pydantic models
  in `backend/app/models.py`. If a field changes on one side, change both.
- **Thin and legible.** Keep views small and focused. The app's value is clarity, not chrome.
- **The "Now" view is the spine** — cross-client priority queue. Per-client *dossier* views come
  in Plan 2/3.

## Key files (Plan 1)
| File | Responsibility |
|------|----------------|
| `src/types.ts` | `Client`, `Task` TS types (mirror backend) |
| `src/api.ts` | typed `fetch` wrappers to the backend |
| `src/NowView.tsx` | the prioritized task list + client filter + Done action |
| `src/App.tsx` | mounts the app |

## How to extend (Plan 2+)
- Add a view per major surface (Client dossier, Meeting prep, etc.), each with its own file.
- Add API wrappers in `api.ts`; add matching types in `types.ts`.
- Keep external concerns in the backend — the frontend stays a dumb, fast renderer.

## Run
```bash
cd frontend && npm run dev          # needs the backend running on :8000
```
