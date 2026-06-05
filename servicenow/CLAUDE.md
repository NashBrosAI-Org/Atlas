# servicenow/ — guardrails (auto-loaded here)

Full rules: repo root [CLAUDE.md](../CLAUDE.md) · [docs/CODE-STANDARDS.md](../docs/CODE-STANDARDS.md) ·
[docs/components/servicenow.md](../docs/components/servicenow.md) · schema in
[docs/DATA-MODEL.md](../docs/DATA-MODEL.md).

Quick reminders when editing here:
- The scoped app is **Fluent code via `now-sdk`** (`.now.ts` tables), *not* hand-built in the UI.
  Deploy with `now-sdk install` to `nnash.service-now.com` (Zurich, MFA on).
- Table/field names are **CSM/PPM-aligned** (rule #5) and must match `DATA-MODEL.md`. A new backend
  field that persists live needs the matching Fluent column here **and** a re-install — keep the
  pydantic model, `frontend/src/types.ts`, and the `.now.ts` table in sync.
- Live backend auth is **basic auth** (OAuth is walled on `nnash` — D11). `now-sdk auth` is
  interactive (code-paste) — run it in a real terminal, not a background runner.
