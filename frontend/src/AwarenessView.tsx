import { useEffect, useState } from "react";
import { getActivity, getRadar, getReminders } from "./api";
import type { ActivityEvent, RadarEntry, Reminder } from "./types";
import { Badge } from "./ui";

const TIER_TONE: Record<string, "warning" | "danger"> = { cooling: "warning", stale: "danger" };

function whenLabel(days: number): string {
  if (days === 0) return "today";
  if (days === 1) return "tomorrow";
  return `in ${days} days`;
}

export function AwarenessView({ onOpenClient }: { onOpenClient: (id: string) => void }) {
  const [radar, setRadar] = useState<RadarEntry[] | null>(null);
  const [feed, setFeed] = useState<ActivityEvent[] | null>(null);
  const [reminders, setReminders] = useState<Reminder[] | null>(null);
  const [err, setErr] = useState("");

  useEffect(() => {
    getRadar().then(setRadar).catch((e) => setErr(String(e)));
    getActivity().then(setFeed).catch((e) => setErr(String(e)));
    getReminders().then(setReminders).catch((e) => setErr(String(e)));
  }, []);

  return (
    <div className="view">
      <h1>Awareness</h1>
      {err && <p className="err">{err}</p>}

      <h3>Upcoming</h3>
      {reminders === null ? <p>Loading…</p>
        : reminders.length === 0 ? <p className="muted">No key dates coming up.</p>
        : (
          <ul style={{ listStyle: "none", padding: 0 }}>
            {reminders.map((r) => (
              <li key={r.sys_id} className={r.client ? "link-row" : undefined} style={{ padding: "6px 0" }}
                  onClick={() => r.client && onOpenClient(r.client)}>
                <span style={{ color: r.days_until <= 1 ? "var(--danger)" : "var(--success)", fontWeight: 600 }}>
                  📅 {whenLabel(r.days_until)}
                </span>
                {" "}— <strong>{r.title}</strong>
                {r.client_name ? <> · {r.client_name}</> : null}
                {" "}<em className="muted">({r.type}{r.recurring ? ", recurring" : ""} · {r.date})</em>
              </li>
            ))}
          </ul>
        )}

      <h3 style={{ marginTop: 24 }}>Needs attention</h3>
      {radar === null ? <p>Loading…</p>
        : radar.length === 0 ? <p className="muted">All active clients are current. 🎉</p>
        : (
          <ul style={{ listStyle: "none", padding: 0 }}>
            {radar.map((r) => (
              <li key={r.client} className="link-row" style={{ padding: "6px 0", display: "flex", alignItems: "center", gap: 8 }}
                  onClick={() => onOpenClient(r.client)}>
                <Badge tone={TIER_TONE[r.tier] ?? "warning"}>● {r.tier}</Badge>
                <span><strong>{r.client_name}</strong> · quiet {r.days_quiet} days</span>
              </li>
            ))}
          </ul>
        )}

      <h3 style={{ marginTop: 24 }}>Recent activity</h3>
      {feed === null ? <p>Loading…</p>
        : feed.length === 0 ? <p className="muted">No activity yet.</p>
        : (
          <ul style={{ listStyle: "none", padding: 0 }}>
            {feed.map((e, i) => (
              <li key={i} className="list-row">
                <span className="muted">{e.when.slice(0, 10)}</span>{" "}
                <strong>{e.client_name}</strong> — {e.title}
                {e.status ? <em className="muted"> ({e.status})</em> : null}
              </li>
            ))}
          </ul>
        )}
    </div>
  );
}
