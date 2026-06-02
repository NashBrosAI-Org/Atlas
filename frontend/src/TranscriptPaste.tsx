import { useState } from "react";
import { createTranscript } from "./api";

export function TranscriptPaste({ clientSysId, onSaved }:
  { clientSysId: string; onSaved: () => void }) {
  const [text, setText] = useState("");
  const [open, setOpen] = useState(false);

  async function save() {
    if (!text.trim()) return;
    await createTranscript({ client: clientSysId, full_text: text, source: "manual" });
    setText("");
    setOpen(false);
    onSaved();
  }

  if (!open) return <button onClick={() => setOpen(true)}>+ Paste transcript</button>;
  return (
    <div style={{ marginTop: 8 }}>
      <textarea style={{ width: "100%", height: 120 }} placeholder="Paste meeting transcript text…"
        value={text} onChange={(e) => setText(e.target.value)} />
      <div style={{ display: "flex", gap: 6 }}>
        <button onClick={save}>Save transcript</button>
        <button onClick={() => setOpen(false)}>Cancel</button>
      </div>
    </div>
  );
}
