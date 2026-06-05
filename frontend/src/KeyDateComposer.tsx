import { useState } from "react";
import type { KeyDateType } from "./types";
import { createKeyDate } from "./api";
import { InfoHint } from "./InfoHint";

const TYPES: KeyDateType[] = ["renewal", "qbr", "contract_end", "birthday", "milestone"];

export function KeyDateComposer({ clientSysId, onSaved }:
  { clientSysId: string; onSaved: () => void }) {
  const [title, setTitle] = useState("");
  const [type, setType] = useState<KeyDateType>("renewal");
  const [date, setDate] = useState("");
  const [recurring, setRecurring] = useState(false);

  async function save() {
    if (!title.trim() || !date) return;
    await createKeyDate({ title, type, date, recurring, client: clientSysId });
    setTitle("");
    setDate("");
    setRecurring(false);
    onSaved();
  }

  return (
    <div style={{ display: "flex", gap: 6, marginTop: 8, flexWrap: "wrap", alignItems: "center" }}>
      <select value={type} onChange={(e) => setType(e.target.value as KeyDateType)}>
        {TYPES.map((t) => <option key={t} value={t}>{t}</option>)}
      </select>
      <InfoHint text="What this date marks — renewals, QBRs, contract ends, birthdays, or milestones." />
      <input style={{ flex: 1, minWidth: 140 }} placeholder="Title…" value={title}
        onChange={(e) => setTitle(e.target.value)} />
      <input type="date" value={date} onChange={(e) => setDate(e.target.value)} />
      <label style={{ fontSize: 13 }}>
        <input type="checkbox" checked={recurring} onChange={(e) => setRecurring(e.target.checked)} /> recurring
        <InfoHint text="Recurring dates roll forward each year — birthdays, annual renewals." />
      </label>
      <button onClick={save}>Add</button>
    </div>
  );
}
