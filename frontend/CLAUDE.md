# frontend/ — guardrails (auto-loaded here)

Full rules: repo root [CLAUDE.md](../CLAUDE.md) · [docs/CODE-STANDARDS.md](../docs/CODE-STANDARDS.md) ·
[docs/components/frontend.md](../docs/components/frontend.md).

Quick reminders when editing here:
- **`src/types.ts` mirrors the backend pydantic models** — change both together.
- Call **only** the relative `/api` through the `http<T>` helper in `src/api.ts`. No direct
  SN/Graph/AI calls; no secrets in the client.
- Small, single-responsibility components. **Style via the design system**, not inline styles:
  reuse the primitives in `src/ui/` (`Button`, `Input`, `Select`, `Textarea`, `Checkbox`, `Field`,
  `Card`, `Badge`, `Modal`, `Toolbar`) and the classes/tokens in `src/ui.css` + `src/index.css`
  (semantic colors `--success`/`--danger`/`--warning`/`--info`/`--muted`, never hardcoded hex).
  Reach for an inline `style` only for one-off layout (flex sizing), not colors/typography. Forms:
  busy guard + `catch → error message`, controlled inputs with `?? ""`, stable `key`s.
- Render server strings as **text** (no `dangerouslySetInnerHTML`); only http(s) URLs in an `href`
  (validate the scheme — D21).
- Build/typecheck: `npm run build` (`tsc -b && vite build`) must pass.
