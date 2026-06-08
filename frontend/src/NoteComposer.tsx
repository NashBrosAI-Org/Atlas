import { useState } from "react";
import { createNote } from "./api";
import { Button, Input, Select, Toolbar } from "./ui";

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
    <Toolbar wrap>
      <Select style={{ width: "auto" }} value={noteType} onChange={(e) => setNoteType(e.target.value as typeof noteType)}>
        {TYPES.map((t) => <option key={t} value={t}>{t}</option>)}
      </Select>
      <Input style={{ flex: 1, minWidth: 160 }} placeholder="Add a note…" value={title}
        onChange={(e) => setTitle(e.target.value)} onKeyDown={(e) => e.key === "Enter" && save()} />
      <Button variant="primary" onClick={save}>Pin</Button>
    </Toolbar>
  );
}
