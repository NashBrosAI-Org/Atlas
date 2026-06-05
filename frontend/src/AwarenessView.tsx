import { useEffect, useState } from "react";
import { getActivity, getRadar, getReminders } from "./api";
import type { ActivityEvent, RadarEntry, Reminder } from "./types";

const TIER_COLOR: Record<string, string> = { cooling: "#b8860b", stale: "#b00020" };

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
    <div style={{ padding: 16, fontFamily: "system-ui", maxWidth: 820 }}>
      <h2>Awareness</h2>
      {err && <p style={{ color: "#b00020" }}>{err}</p>}

      <h3>Upcoming</h3>
      {reminders === null ? <p>Loading…</p>
        : reminders.length === 0 ? <p>No key dates coming up.</p>
        : (
          <ul style={{ listStyle: "none", padding: 0 }}>
            {reminders.map((r) => (
              <li key={r.sys_id} style={{ padding: "6px 0", cursor: r.client ? "pointer" : "default" }}
                  onClick={() => r.client && onOpenClient(r.client)}>
                <span style={{ color: r.days_until <= 1 ? "#b00020" : "#0a7", fontWeight: 600 }}>
                  📅 {whenLabel(r.days_until)}
                </span>
                {" "}— <strong>{r.title}</strong>
                {r.client_name ? <> · {r.client_name}</> : null}
                {" "}<em style={{ color: "#888" }}>({r.type}{r.recurring ? ", recurring" : ""} · {r.date})</em>
              </li>
            ))}
          </ul>
        )}

      <h3 style={{ marginTop: 24 }}>Needs attention</h3>
      {radar === null ? <p>Loading…</p>
        : radar.length === 0 ? <p>All active clients are current. 🎉</p>
        : (
          <ul style={{ listStyle: "none", padding: 0 }}>
            {radar.map((r) => (
              <li key={r.client} style={{ padding: "6px 0", cursor: "pointer" }}
                  onClick={() => onOpenClient(r.client)}>
                <span style={{ color: TIER_COLOR[r.tier], fontWeight: 600 }}>● {r.tier}</span>
                {" "}— <strong>{r.client_name}</strong> · quiet {r.days_quiet} days
              </li>
            ))}
          </ul>
        )}

      <h3 style={{ marginTop: 24 }}>Recent activity</h3>
      {feed === null ? <p>Loading…</p>
        : feed.length === 0 ? <p>No activity yet.</p>
        : (
          <ul style={{ listStyle: "none", padding: 0 }}>
            {feed.map((e, i) => (
              <li key={i} style={{ padding: "4px 0", borderBottom: "1px solid #eee" }}>
                <span style={{ color: "#888" }}>{e.when.slice(0, 10)}</span>{" "}
                <strong>{e.client_name}</strong> — {e.title}
                {e.status ? <em style={{ color: "#888" }}> ({e.status})</em> : null}
              </li>
            ))}
          </ul>
        )}
    </div>
  );
}
