import { useState } from "react";
import { createLink } from "./api";
import { Button, Input, Toolbar } from "./ui";

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
    <Toolbar wrap>
      <Input style={{ flex: 1, minWidth: 120 }} placeholder="Title…" value={title}
        onChange={(e) => setTitle(e.target.value)} />
      <Input style={{ flex: 2, minWidth: 180 }} placeholder="https://…" value={url}
        onChange={(e) => setUrl(e.target.value)} onKeyDown={(e) => e.key === "Enter" && save()} />
      <Button variant="primary" onClick={save}>Add link</Button>
    </Toolbar>
  );
}
