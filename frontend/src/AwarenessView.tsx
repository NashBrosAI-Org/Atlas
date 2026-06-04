import { useEffect, useState } from "react";
import { getActivity, getRadar } from "./api";
import type { ActivityEvent, RadarEntry } from "./types";

const TIER_COLOR: Record<string, string> = { cooling: "#b8860b", stale: "#b00020" };

export function AwarenessView({ onOpenClient }: { onOpenClient: (id: string) => void }) {
  const [radar, setRadar] = useState<RadarEntry[] | null>(null);
  const [feed, setFeed] = useState<ActivityEvent[] | null>(null);
  const [err, setErr] = useState("");

  useEffect(() => {
    getRadar().then(setRadar).catch((e) => setErr(String(e)));
    getActivity().then(setFeed).catch((e) => setErr(String(e)));
  }, []);

  return (
    <div style={{ padding: 16, fontFamily: "system-ui", maxWidth: 820 }}>
      <h2>Awareness</h2>
      {err && <p style={{ color: "#b00020" }}>{err}</p>}

      <h3>Needs attention</h3>
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
