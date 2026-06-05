import { useEffect, useRef, useState } from "react";
import { search } from "./api";
import type { SearchHit } from "./types";

const TYPE_ORDER = ["client", "task", "contact", "note", "engagement"];
const TYPE_LABEL: Record<string, string> = {
  client: "Clients",
  task: "Tasks",
  contact: "Contacts",
  note: "Notes",
  engagement: "Engagements",
};

export function SearchView({ onOpenClient }: { onOpenClient: (id: string) => void }) {
  const [q, setQ] = useState("");
  const [hits, setHits] = useState<SearchHit[] | null>(null);
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState("");
  const seq = useRef(0);

  function run(query: string) {
    const term = query.trim();
    if (!term) {
      setHits(null);
      setErr("");
      return;
    }
    const mine = ++seq.current;
    setBusy(true);
    setErr("");
    search(term)
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

  // As-you-type with a small debounce guard.
  useEffect(() => {
    const t = setTimeout(() => run(q), 200);
    return () => clearTimeout(t);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [q]);

  const grouped = TYPE_ORDER.map((type) => ({
    type,
    items: (hits ?? []).filter((h) => h.type === type),
  })).filter((g) => g.items.length > 0);

  return (
    <div style={{ padding: 16, fontFamily: "system-ui", maxWidth: 820 }}>
      <h2>Search</h2>
      <input
        type="text"
        value={q}
        autoFocus
        placeholder="Search clients, tasks, contacts, notes, engagements…"
        onChange={(e) => setQ(e.target.value)}
        onKeyDown={(e) => e.key === "Enter" && run(q)}
        style={{ width: "100%", padding: "8px 10px", fontSize: 16, boxSizing: "border-box" }}
      />
      {err && <p style={{ color: "#b00020" }}>{err}</p>}

      {busy && hits === null && <p>Searching…</p>}
      {!busy && q.trim() === "" && <p style={{ color: "#888" }}>Type to search across all records.</p>}
      {!busy && q.trim() !== "" && hits !== null && hits.length === 0 && <p>No matches.</p>}

      {grouped.map((g) => (
        <div key={g.type}>
          <h3 style={{ marginTop: 24 }}>{TYPE_LABEL[g.type] ?? g.type}</h3>
          <ul style={{ listStyle: "none", padding: 0 }}>
            {g.items.map((h) => (
              <li
                key={`${h.type}:${h.sys_id}`}
                style={{
                  padding: "6px 0",
                  borderBottom: "1px solid #eee",
                  cursor: h.client ? "pointer" : "default",
                }}
                onClick={() => h.client && onOpenClient(h.client)}
              >
                <strong>{h.label}</strong>
                {h.client_name ? <span style={{ color: "#888" }}> · {h.client_name}</span> : null}
              </li>
            ))}
          </ul>
        </div>
      ))}
    </div>
  );
}
