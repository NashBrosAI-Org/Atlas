import { useEffect, useState } from "react";
import type { MeetingPrep } from "./types";
import { getMeetingPrep } from "./api";

/** Modal prep brief for a meeting: client context (open tasks, key dates, notes)
 *  plus recent activity. Fetched from GET /api/m365/prep/{id}. */
export function MeetingPrepPanel({ meetingId, onClose }:
  { meetingId: string; onClose: () => void }) {
  const [prep, setPrep] = useState<MeetingPrep | null>(null);
  const [err, setErr] = useState("");

  useEffect(() => {
    getMeetingPrep(meetingId).then(setPrep).catch((e) => setErr(String(e)));
  }, [meetingId]);

  return (
    <div onClick={onClose} style={{
      position: "fixed", inset: 0, background: "rgba(0,0,0,0.35)",
      display: "flex", alignItems: "flex-start", justifyContent: "center", zIndex: 1000,
    }}>
      <div onClick={(e) => e.stopPropagation()} style={{
        background: "#fff", borderRadius: 8, padding: 20, margin: "6vh 16px",
        maxWidth: 560, width: "100%", maxHeight: "85vh", overflowY: "auto",
        fontFamily: "system-ui", boxShadow: "0 8px 30px rgba(0,0,0,0.25)",
      }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
          <h2 style={{ margin: 0, fontSize: 17 }}>Meeting prep</h2>
          <button onClick={onClose}>Close</button>
        </div>

        {err && <p style={{ color: "#b00020" }}>{err}</p>}
        {!prep && !err && <p>Loading…</p>}
        {prep && (
          <>
            <p style={{ margin: "8px 0" }}>
              <strong>{prep.meeting.title}</strong>
              {prep.meeting.datetime ? <span style={{ color: "#888" }}> · {prep.meeting.datetime.slice(0, 16).replace("T", " ")}</span> : null}
              {prep.client ? <span> · {prep.client.name}</span> : <span style={{ color: "#888" }}> · no client linked</span>}
            </p>

            <PrepList title="Open tasks" items={prep.open_tasks.map((t) => `${t.priority ? `[${t.priority}] ` : ""}${t.title}`)} />
            <PrepList title="Key dates" items={prep.key_dates.map((k) => `${k.date ?? ""} — ${k.title}`)} />
            <PrepList title="Notes" items={prep.notes.map((n) => `[${n.note_type ?? "general"}] ${n.title}`)} />
            <PrepList title="Recent activity" items={prep.recent_activity.map((e) => `${e.when.slice(0, 10)} — ${e.title}`)} />
          </>
        )}
      </div>
    </div>
  );
}

function PrepList({ title, items }: { title: string; items: string[] }) {
  return (
    <div style={{ marginTop: 12 }}>
      <strong style={{ fontSize: 13 }}>{title}</strong>
      {items.length === 0 ? <span style={{ color: "#888" }}> — none</span> : (
        <ul style={{ margin: "4px 0", paddingLeft: 18 }}>
          {items.map((s, i) => <li key={i}>{s}</li>)}
        </ul>
      )}
    </div>
  );
}
