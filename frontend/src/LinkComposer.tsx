import { useState } from "react";
import { createLink } from "./api";

export function LinkComposer({ clientSysId, onSaved }:
  { clientSysId: string; onSaved: () => void }) {
  const [title, setTitle] = useState("");
  const [url, setUrl] = useState("");

  async function save() {
    if (!title.trim()) return;
    await createLink({ title, url, client: clientSysId });
    setTitle("");
    setUrl("");
    onSaved();
  }

  return (
    <div style={{ display: "flex", gap: 6, marginTop: 8, flexWrap: "wrap" }}>
      <input style={{ flex: 1, minWidth: 120 }} placeholder="Title…" value={title}
        onChange={(e) => setTitle(e.target.value)} />
      <input style={{ flex: 2, minWidth: 180 }} placeholder="https://…" value={url}
        onChange={(e) => setUrl(e.target.value)} onKeyDown={(e) => e.key === "Enter" && save()} />
      <button onClick={save}>Add link</button>
    </div>
  );
}
