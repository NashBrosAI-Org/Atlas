import { useEffect, useState } from "react";
import type { MeetingPrep } from "./types";
import { getMeetingPrep } from "./api";
import { Modal } from "./ui";

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
    <Modal title="Meeting prep" onClose={onClose} width={560}>
      {err && <p className="err">{err}</p>}
      {!prep && !err && <p>Loading…</p>}
      {prep && (
        <>
          <p style={{ marginBottom: 12 }}>
            <strong>{prep.meeting.title}</strong>
            {prep.meeting.datetime ? <span className="muted"> · {prep.meeting.datetime.slice(0, 16).replace("T", " ")}</span> : null}
            {prep.client ? <span> · {prep.client.name}</span> : <span className="muted"> · no client linked</span>}
          </p>

          <PrepList title="Open tasks" items={prep.open_tasks.map((t) => `${t.priority ? `[${t.priority}] ` : ""}${t.title}`)} />
          <PrepList title="Key dates" items={prep.key_dates.map((k) => `${k.date ?? ""} — ${k.title}`)} />
          <PrepList title="Notes" items={prep.notes.map((n) => `[${n.note_type ?? "general"}] ${n.title}`)} />
          <PrepList title="Recent activity" items={prep.recent_activity.map((e) => `${e.when.slice(0, 10)} — ${e.title}`)} />
        </>
      )}
    </Modal>
  );
}

function PrepList({ title, items }: { title: string; items: string[] }) {
  return (
    <div style={{ marginTop: 12 }}>
      <strong style={{ fontSize: 13 }}>{title}</strong>
      {items.length === 0 ? <span className="muted"> — none</span> : (
        <ul style={{ margin: "4px 0", paddingLeft: 18 }}>
          {items.map((s, i) => <li key={i}>{s}</li>)}
        </ul>
      )}
    </div>
  );
}
