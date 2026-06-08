import { useState } from "react";
import type { TagOnRecord } from "./types";
import { attachTag, detachTag } from "./api";
import { InfoHint } from "./InfoHint";
import { Input, Badge } from "./ui";

/** Tag chips for a record, with inline add (Enter) and per-chip remove (×). */
export function TagEditor({ targetTable, targetId, tags, onChanged }:
  { targetTable: string; targetId: string; tags: TagOnRecord[]; onChanged: () => void }) {
  const [name, setName] = useState("");
  const [busy, setBusy] = useState(false);

  async function add() {
    const n = name.trim();
    if (!n || busy) return;
    setBusy(true);
    try {
      await attachTag(targetTable, targetId, n);
      setName("");
      onChanged();
    } finally {
      setBusy(false);
    }
  }

  async function remove(tagId: string) {
    setBusy(true);
    try {
      await detachTag(targetTable, targetId, tagId);
      onChanged();
    } finally {
      setBusy(false);
    }
  }

  return (
    <div style={{ display: "flex", flexWrap: "wrap", gap: 6, alignItems: "center" }}>
      {tags.map((t) => (
        <Badge key={t.link_id} tone="accent" pill
          onRemove={busy ? undefined : () => remove(t.sys_id)} removeLabel={`Remove ${t.name}`}>
          {t.name}
        </Badge>
      ))}
      <Input placeholder="Add tag…" value={name} disabled={busy}
        onChange={(e) => setName(e.target.value)} onKeyDown={(e) => e.key === "Enter" && add()}
        style={{ width: 140 }} />
      <InfoHint text="Tags are cross-cutting labels you can filter and search by." />
    </div>
  );
}
