import { useEffect, useState } from "react";
import type { Client } from "./types";
import { getClients, createTask, createNote } from "./api";

const PRIORITIES = ["critical", "high", "medium", "low"] as const;
const NOTE_TYPES = ["general", "risk", "issue", "decision"] as const;

/** Global quick-capture modal: create a task or a note from anywhere.
 *  Mirrors MeetingPrepPanel's overlay (backdrop + click-outside + stopPropagation
 *  + Close, plus Escape-to-close). Backend endpoints already exist. */
export function QuickCapture({ onClose, onSaved }:
  { onClose: () => void; onSaved?: () => void }) {
  const [mode, setMode] = useState<"task" | "note">("task");
  const [clients, setClients] = useState<Client[]>([]);

  // Shared
  const [title, setTitle] = useState("");
  const [client, setClient] = useState("");

  // Task fields
  const [priority, setPriority] = useState<(typeof PRIORITIES)[number]>("medium");
  const [dueDate, setDueDate] = useState("");
  const [commitment, setCommitment] = useState(false);

  // Note fields
  const [body, setBody] = useState("");
  const [noteType, setNoteType] = useState<(typeof NOTE_TYPES)[number]>("general");

  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState("");

  useEffect(() => { getClients().then(setClients).catch((e) => setErr(String(e))); }, []);

  // Escape-to-close.
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => { if (e.key === "Escape") onClose(); };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [onClose]);

  async function save() {
    if (!title.trim() || busy) return;
    setBusy(true);
    setErr("");
    try {
      if (mode === "task") {
        await createTask({
          title: title.trim(), priority, client: client || undefined,
          due_date: dueDate || undefined, is_commitment: commitment, status: "open",
        });
      } else {
        const base = { title: title.trim(), body: body || undefined, note_type: noteType };
        // When a client is chosen, target the note at the client record; otherwise leave untargeted.
        await createNote(client
          ? { ...base, target_table: "client", target_id: client, pinned: false }
          : base);
      }
      onSaved?.();
      onClose();
    } catch (e) {
      setErr(String(e));
    } finally {
      setBusy(false);
    }
  }

  return (
    <div onClick={onClose} style={{
      position: "fixed", inset: 0, background: "rgba(0,0,0,0.35)",
      display: "flex", alignItems: "flex-start", justifyContent: "center", zIndex: 1000,
    }}>
      <div onClick={(e) => e.stopPropagation()} style={{
        background: "#fff", borderRadius: 8, padding: 20, margin: "6vh 16px",
        maxWidth: 480, width: "100%", maxHeight: "85vh", overflowY: "auto",
        fontFamily: "system-ui", boxShadow: "0 8px 30px rgba(0,0,0,0.25)",
      }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
          <h2 style={{ margin: 0, fontSize: 17 }}>Quick capture</h2>
          <button onClick={onClose}>Close</button>
        </div>

        <div style={{ display: "flex", gap: 6, margin: "12px 0" }}>
          <button
            onClick={() => setMode("task")}
            style={{ fontWeight: mode === "task" ? 700 : 400 }}
            disabled={busy}
          >Task</button>
          <button
            onClick={() => setMode("note")}
            style={{ fontWeight: mode === "note" ? 700 : 400 }}
            disabled={busy}
          >Note</button>
        </div>

        <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
          <input
            placeholder={mode === "task" ? "Task title…" : "Note title…"}
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            onKeyDown={(e) => { if (e.key === "Enter" && mode === "task") save(); }}
          />

          {mode === "task" ? (
            <>
              <select value={priority} onChange={(e) => setPriority(e.target.value as typeof priority)}>
                {PRIORITIES.map((p) => <option key={p} value={p}>{p}</option>)}
              </select>
              <input type="date" value={dueDate ?? ""} onChange={(e) => setDueDate(e.target.value)} />
              <label style={{ fontSize: 13 }}>
                <input type="checkbox" checked={commitment} onChange={(e) => setCommitment(e.target.checked)} /> 🤝 commitment
              </label>
            </>
          ) : (
            <>
              <textarea
                placeholder="Note body…"
                value={body ?? ""}
                onChange={(e) => setBody(e.target.value)}
                rows={4}
                style={{ resize: "vertical", fontFamily: "inherit" }}
              />
              <select value={noteType} onChange={(e) => setNoteType(e.target.value as typeof noteType)}>
                {NOTE_TYPES.map((t) => <option key={t} value={t}>{t}</option>)}
              </select>
            </>
          )}

          <select value={client} onChange={(e) => setClient(e.target.value)}>
            <option value="">No client</option>
            {clients.map((c) => <option key={c.sys_id} value={c.sys_id}>{c.name}</option>)}
          </select>

          <div style={{ display: "flex", gap: 8, alignItems: "center" }}>
            <button disabled={busy || !title.trim()} onClick={save}>
              {busy ? "Saving…" : `Save ${mode}`}
            </button>
            {err && <span style={{ color: "#b00020", fontSize: 13 }}>{err}</span>}
          </div>
        </div>
      </div>
    </div>
  );
}
