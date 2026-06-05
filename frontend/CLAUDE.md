# frontend/ — guardrails (auto-loaded here)

Full rules: repo root [CLAUDE.md](../CLAUDE.md) · [docs/CODE-STANDARDS.md](../docs/CODE-STANDARDS.md) ·
[docs/components/frontend.md](../docs/components/frontend.md).

Quick reminders when editing here:
- **`src/types.ts` mirrors the backend pydantic models** — change both together.
- Call **only** the relative `/api` through the `http<T>` helper in `src/api.ts`. No direct
  SN/Graph/AI calls; no secrets in the client.
- Small, single-responsibility components; inline styles matching the existing ones. Forms: busy
  guard + `catch → error message`, controlled inputs with `?? ""`, stable `key`s.
- Render server strings as **text** (no `dangerouslySetInnerHTML`); only http(s) URLs in an `href`
  (validate the scheme — D21).
- Build/typecheck: `npm run build` (`tsc -b && vite build`) must pass.
