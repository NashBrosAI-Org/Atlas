import { useEffect, useRef, useState } from "react";
import type { ReactNode } from "react";
import { search } from "./api";
import type { SearchHit } from "./types";
import { Button, Input, Checkbox, Card } from "./ui";

// Display order + labels for every searchable type. `defaultOn: false` keeps
// transcripts out of the default scope (long, noisy) — opt in via the filter menu.
const TYPES: { key: string; label: string; defaultOn: boolean }[] = [
  { key: "client", label: "Clients", defaultOn: true },
  { key: "task", label: "Tasks", defaultOn: true },
  { key: "contact", label: "Contacts", defaultOn: true },
  { key: "note", label: "Notes", defaultOn: true },
  { key: "engagement", label: "Engagements", defaultOn: true },
  { key: "meeting", label: "Meetings", defaultOn: true },
  { key: "theme", label: "Themes", defaultOn: true },
  { key: "key_date", label: "Key dates", defaultOn: true },
  { key: "link", label: "Links", defaultOn: true },
  { key: "transcript", label: "Transcripts", defaultOn: false },
];
const TYPE_ORDER = TYPES.map((t) => t.key);
const TYPE_LABEL: Record<string, string> = Object.fromEntries(TYPES.map((t) => [t.key, t.label]));

const STORAGE_KEY = "atlas.search.types";
const PER_TYPE_CAP = 6;

function loadEnabled(): string[] {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (raw) return JSON.parse(raw) as string[];
  } catch {
    /* corrupt/absent — fall through to defaults */
  }
  return TYPES.filter((t) => t.defaultOn).map((t) => t.key);
}

/** Highlight matches as React text nodes (never raw HTML — D21). A snippet uses
 *  the backend's `>>match<<` markers; a plain label is highlighted by query. */
function highlight(text: string, query: string): ReactNode {
  if (text.includes(">>")) {
    // parts alternate [before, match, after, …]; odd indices are matches.
    return text.split(/>>|<</).map((p, i) =>
      i % 2 === 1 ? <mark key={i}>{p}</mark> : <span key={i}>{p}</span>,
    );
  }
  const idx = query ? text.toLowerCase().indexOf(query.toLowerCase()) : -1;
  if (idx < 0) return text;
  return (
    <>
      {text.slice(0, idx)}
      <mark>{text.slice(idx, idx + query.length)}</mark>
      {text.slice(idx + query.length)}
    </>
  );
}

export function SearchView({ onOpenClient }: { onOpenClient: (id: string) => void }) {
  const [q, setQ] = useState("");
  const [hits, setHits] = useState<SearchHit[] | null>(null);
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState("");
  const [enabled, setEnabled] = useState<string[]>(loadEnabled);
  const [showFilters, setShowFilters] = useState(false);
  const seq = useRef(0);

  function run(query: string, types: string[]) {
    const term = query.trim();
    if (!term) {
      setHits(null);
      setErr("");
      return;
    }
    const mine = ++seq.current;
    setBusy(true);
    setErr("");
    search(term, types)
      .then((r) => {
        if (mine === seq.current) setHits(r);
      })
      .catch((e) => {
        if (mine === seq.current) setErr(String(e));
      })
      .finally(() => {
        if (mine === seq.current) setBusy(false);
      });
  }

  // As-you-type with a small debounce; also re-runs when the type filter changes.
  useEffect(() => {
    const t = setTimeout(() => run(q, enabled), 200);
    return () => clearTimeout(t);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [q, enabled]);

  function toggle(key: string) {
    setEnabled((prev) => {
      const next = prev.includes(key) ? prev.filter((k) => k !== key) : [...prev, key];
      localStorage.setItem(STORAGE_KEY, JSON.stringify(next));
      return next;
    });
  }

  const grouped = TYPE_ORDER.map((type) => ({
    type,
    items: (hits ?? []).filter((h) => h.type === type),
  })).filter((g) => g.items.length > 0);

  return (
    <div className="view">
      <h1>Search</h1>
      <div className="toolbar">
        <Input
          type="text"
          value={q}
          autoFocus
          placeholder="Search across all records…"
          onChange={(e) => setQ(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && run(q, enabled)}
          style={{ flex: 1 }}
        />
        <Button onClick={() => setShowFilters((s) => !s)} aria-expanded={showFilters}>
          Types ({enabled.length})
        </Button>
      </div>

      {showFilters && (
        <Card variant="muted" style={{ marginTop: 8, display: "flex", flexWrap: "wrap", gap: "6px 18px" }}>
          {TYPES.map((t) => (
            <Checkbox key={t.key} checked={enabled.includes(t.key)} onChange={() => toggle(t.key)} label={t.label} />
          ))}
        </Card>
      )}

      {err && <p className="err">{err}</p>}
      {busy && hits === null && <p>Searching…</p>}
      {!busy && q.trim() === "" && <p className="muted">Type to search across all records.</p>}
      {!busy && q.trim() !== "" && hits !== null && hits.length === 0 && <p className="muted">No matches.</p>}

      {grouped.map((g) => (
        <div key={g.type}>
          <h3 style={{ marginTop: 24 }}>
            {TYPE_LABEL[g.type] ?? g.type}
            {g.items.length > PER_TYPE_CAP ? (
              <span className="muted" style={{ fontWeight: "normal", textTransform: "none" }}> · showing {PER_TYPE_CAP} of {g.items.length}</span>
            ) : null}
          </h3>
          <ul style={{ listStyle: "none", padding: 0 }}>
            {g.items.slice(0, PER_TYPE_CAP).map((h) => (
              <li
                key={`${h.type}:${h.sys_id}`}
                className={h.client ? "list-row link-row" : "list-row"}
                style={{ display: "block" }}
                onClick={() => h.client && onOpenClient(h.client)}
              >
                <strong>{highlight(h.label, q)}</strong>
                {h.client_name ? <span className="muted"> · {h.client_name}</span> : null}
                {h.snippet ? <div className="muted" style={{ fontSize: 13 }}>{highlight(h.snippet, q)}</div> : null}
              </li>
            ))}
          </ul>
        </div>
      ))}
    </div>
  );
}
