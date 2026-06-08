import { useState } from "react";
import { createTranscript } from "./api";
import { Button, Textarea, Toolbar } from "./ui";

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

  if (!open) return <Button onClick={() => setOpen(true)}>+ Paste transcript</Button>;
  return (
    <div className="stack" style={{ marginTop: 8 }}>
      <Textarea style={{ minHeight: 120 }} placeholder="Paste meeting transcript text…"
        value={text} onChange={(e) => setText(e.target.value)} />
      <Toolbar>
        <Button variant="primary" onClick={save}>Save transcript</Button>
        <Button onClick={() => setOpen(false)}>Cancel</Button>
      </Toolbar>
    </div>
  );
}
