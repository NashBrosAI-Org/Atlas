import { useState } from "react";
import { createNote } from "./api";

const TYPES = ["general", "risk", "issue", "decision"] as const;

export function NoteComposer({ targetTable, targetId, onSaved }:
  { targetTable: string; targetId: string; onSaved: () => void }) {
  const [title, setTitle] = useState("");
  const [noteType, setNoteType] = useState<(typeof TYPES)[number]>("general");

  async function save() {
    if (!title.trim()) return;
    await createNote({ title, note_type: noteType, target_table: targetTable, target_id: targetId, pinned: true });
    setTitle("");
    onSaved();
  }

  return (
    <div style={{ display: "flex", gap: 6, marginTop: 8 }}>
      <select value={noteType} onChange={(e) => setNoteType(e.target.value as typeof noteType)}>
        {TYPES.map((t) => <option key={t} value={t}>{t}</option>)}
      </select>
      <input style={{ flex: 1 }} placeholder="Add a note…" value={title}
        onChange={(e) => setTitle(e.target.value)} onKeyDown={(e) => e.key === "Enter" && save()} />
      <button onClick={save}>Pin</button>
    </div>
  );
}
