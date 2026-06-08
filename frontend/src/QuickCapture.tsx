import { useEffect, useState } from "react";
import type { Client } from "./types";
import { getClients, createTask, createNote } from "./api";
import { Modal, Button, Input, Textarea, Select, Checkbox } from "./ui";

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
    <Modal title="Quick capture" onClose={onClose} width={480}>
      <div className="toolbar" style={{ marginBottom: 14 }}>
        <Button variant={mode === "task" ? "primary" : "secondary"} size="sm"
          onClick={() => setMode("task")} disabled={busy}>Task</Button>
        <Button variant={mode === "note" ? "primary" : "secondary"} size="sm"
          onClick={() => setMode("note")} disabled={busy}>Note</Button>
      </div>

      <div className="stack">
        <Input
          placeholder={mode === "task" ? "Task title…" : "Note title…"}
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          onKeyDown={(e) => { if (e.key === "Enter" && mode === "task") save(); }}
        />

        {mode === "task" ? (
          <>
            <Select value={priority} onChange={(e) => setPriority(e.target.value as typeof priority)}>
              {PRIORITIES.map((p) => <option key={p} value={p}>{p}</option>)}
            </Select>
            <Input type="date" value={dueDate ?? ""} onChange={(e) => setDueDate(e.target.value)} />
            <Checkbox checked={commitment} onChange={(e) => setCommitment(e.target.checked)} label="🤝 commitment" />
          </>
        ) : (
          <>
            <Textarea
              placeholder="Note body…"
              value={body ?? ""}
              onChange={(e) => setBody(e.target.value)}
              rows={4}
            />
            <Select value={noteType} onChange={(e) => setNoteType(e.target.value as typeof noteType)}>
              {NOTE_TYPES.map((t) => <option key={t} value={t}>{t}</option>)}
            </Select>
          </>
        )}

        <Select value={client} onChange={(e) => setClient(e.target.value)}>
          <option value="">No client</option>
          {clients.map((c) => <option key={c.sys_id} value={c.sys_id}>{c.name}</option>)}
        </Select>

        <div className="toolbar">
          <Button variant="primary" disabled={busy || !title.trim()} onClick={save}>
            {busy ? "Saving…" : `Save ${mode}`}
          </Button>
          {err && <span className="err" style={{ fontSize: 13 }}>{err}</span>}
        </div>
      </div>
    </Modal>
  );
}
