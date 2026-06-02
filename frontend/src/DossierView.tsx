import { useEffect, useState } from "react";
import type { Dossier } from "./types";
import { getDossier } from "./api";
import { OrgChart } from "./OrgChart";
import { NoteComposer } from "./NoteComposer";
import { TranscriptPaste } from "./TranscriptPaste";

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <section style={{ marginTop: 20 }}>
      <h2 style={{ fontSize: 16, borderBottom: "2px solid #0a7", paddingBottom: 4 }}>{title}</h2>
      {children}
    </section>
  );
}

export function DossierView({ clientSysId, onBack }: { clientSysId: string; onBack: () => void }) {
  const [d, setD] = useState<Dossier | null>(null);
  const refresh = () => getDossier(clientSysId).then(setD);
  useEffect(() => { refresh(); }, [clientSysId]);
  if (!d) return <p style={{ margin: "2rem" }}>Loading…</p>;

  return (
    <div style={{ maxWidth: 820, margin: "2rem auto", fontFamily: "system-ui" }}>
      <button onClick={onBack}>← Clients</button>
      <h1>{d.client.name}</h1>

      <Section title={`Open tasks (${d.open_tasks.length})`}>
        <ul>{d.open_tasks.map((t) => <li key={t.sys_id}>{t.is_commitment ? "🤝 " : ""}{t.title} <em style={{ color: "#888" }}>{t.priority}</em></li>)}</ul>
      </Section>

      <Section title={`Contacts (${d.contacts.length})`}>
        <OrgChart contacts={d.contacts} />
      </Section>

      <Section title={`Engagements (${d.engagements.length})`}>
        <ul>{d.engagements.map((e) => <li key={e.sys_id}>{e.name} <em style={{ color: "#888" }}>{e.status}</em></li>)}</ul>
      </Section>

      <Section title={`Themes (${d.themes.length})`}>
        <ul>{d.themes.map((t) => <li key={t.sys_id}>{t.name} <em style={{ color: "#888" }}>{t.status}</em></li>)}</ul>
      </Section>

      <Section title={`Meetings (${d.meetings.length})`}>
        <ul>{d.meetings.map((m) => <li key={m.sys_id}>{m.title} <em style={{ color: "#888" }}>{m.type}</em></li>)}</ul>
        <TranscriptPaste clientSysId={clientSysId} onSaved={refresh} />
      </Section>

      <Section title={`Notes & RAID (${d.notes.length})`}>
        <ul>{d.notes.map((n) => <li key={n.sys_id}><strong>[{n.note_type}]</strong> {n.title}</li>)}</ul>
        <NoteComposer targetTable="client" targetId={clientSysId} onSaved={refresh} />
      </Section>
    </div>
  );
}
