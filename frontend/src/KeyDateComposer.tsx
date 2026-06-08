import { useState } from "react";
import type { KeyDateType } from "./types";
import { createKeyDate } from "./api";
import { InfoHint } from "./InfoHint";
import { Button, Input, Select, Checkbox, Toolbar } from "./ui";

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
    <Toolbar wrap>
      <Select style={{ width: "auto" }} value={type} onChange={(e) => setType(e.target.value as KeyDateType)}>
        {TYPES.map((t) => <option key={t} value={t}>{t}</option>)}
      </Select>
      <InfoHint text="What this date marks — renewals, QBRs, contract ends, birthdays, or milestones." />
      <Input style={{ flex: 1, minWidth: 140 }} placeholder="Title…" value={title}
        onChange={(e) => setTitle(e.target.value)} />
      <Input style={{ width: "auto" }} type="date" value={date} onChange={(e) => setDate(e.target.value)} />
      <Checkbox checked={recurring} onChange={(e) => setRecurring(e.target.checked)}
        label={<>recurring<InfoHint text="Recurring dates roll forward each year — birthdays, annual renewals." /></>} />
      <Button variant="primary" onClick={save}>Add</Button>
    </Toolbar>
  );
}
