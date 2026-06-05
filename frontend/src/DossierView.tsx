import { useEffect, useState } from "react";
import type { Dossier, ActivityEvent } from "./types";
import { getDossier, getTimeline, deleteLink, getAIStatus, summarizeClient } from "./api";
import { OrgChart } from "./OrgChart";
import { NoteComposer } from "./NoteComposer";
import { TranscriptPaste } from "./TranscriptPaste";
import { TagEditor } from "./TagEditor";
import { KeyDateComposer } from "./KeyDateComposer";
import { LinkComposer } from "./LinkComposer";
import { MeetingPrepPanel } from "./MeetingPrepPanel";

/** Only http(s) URLs are safe as an anchor href; anything else (javascript:,
 *  data:) would be an XSS sink. Returns the URL if safe, else undefined. */
function safeHref(url?: string): string | undefined {
  return url && /^https?:\/\//i.test(url.trim()) ? url : undefined;
}

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
  const [timeline, setTimeline] = useState<ActivityEvent[] | null>(null);
  const [prepId, setPrepId] = useState<string | null>(null);
  const [aiEnabled, setAiEnabled] = useState(false);
  const [summary, setSummary] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const refresh = () => getDossier(clientSysId).then(setD);
  useEffect(() => { refresh(); }, [clientSysId]);
  useEffect(() => {
    getTimeline(clientSysId).then(setTimeline).catch(() => setTimeline([]));
  }, [clientSysId]);
  useEffect(() => {
    getAIStatus().then((s) => setAiEnabled(s.enabled)).catch(() => setAiEnabled(false));
  }, []);
  if (!d) return <p style={{ margin: "2rem" }}>Loading…</p>;

  return (
    <div style={{ maxWidth: 820, margin: "2rem auto", fontFamily: "system-ui" }}>
      <button onClick={onBack}>← Clients</button>
      <h1>{d.client.name}</h1>

      {aiEnabled && (
        <Section title="AI summary">
          <button
            disabled={busy}
            onClick={() => {
              setBusy(true);
              summarizeClient(clientSysId)
                .then((r) => setSummary(r.summary))
                .catch((e) => setSummary(`Error: ${e.message}`))
                .finally(() => setBusy(false));
            }}
          >
            {busy ? "Summarizing…" : "Summarize"}
          </button>
          {summary !== null && <p style={{ whiteSpace: "pre-wrap" }}>{summary}</p>}
        </Section>
      )}

      <Section title={`Tags (${d.tags.length})`}>
        <TagEditor targetTable="client" targetId={clientSysId} tags={d.tags} onChanged={refresh} />
      </Section>

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

      <Section title={`Key dates (${d.key_dates.length})`}>
        <ul>{d.key_dates.map((k) => (
          <li key={k.sys_id}>
            <span style={{ color: "#888" }}>{k.date}</span> — {k.title}{" "}
            <em style={{ color: "#888" }}>{k.type}{k.recurring ? " · recurring" : ""}</em>
          </li>
        ))}</ul>
        <KeyDateComposer clientSysId={clientSysId} onSaved={refresh} />
      </Section>

      <Section title={`Links (${d.links.length})`}>
        <ul>{d.links.map((l) => (
          <li key={l.sys_id}>
            {safeHref(l.url) ? <a href={safeHref(l.url)} target="_blank" rel="noreferrer">{l.title}</a> : l.title}{" "}
            <button aria-label={`Remove ${l.title}`} title="Remove"
              onClick={() => deleteLink(l.sys_id!).then(refresh)}
              style={{ border: "none", background: "none", color: "#b00020", cursor: "pointer" }}>×</button>
          </li>
        ))}</ul>
        <LinkComposer clientSysId={clientSysId} onSaved={refresh} />
      </Section>

      <Section title={`Meetings (${d.meetings.length})`}>
        <ul>{d.meetings.map((m) => (
          <li key={m.sys_id}>
            {m.title} <em style={{ color: "#888" }}>{m.type}</em>{" "}
            <button onClick={() => setPrepId(m.sys_id!)}>Prep</button>
          </li>
        ))}</ul>
        <TranscriptPaste clientSysId={clientSysId} onSaved={refresh} />
      </Section>

      <Section title={`Notes & RAID (${d.notes.length})`}>
        <ul>{d.notes.map((n) => <li key={n.sys_id}><strong>[{n.note_type}]</strong> {n.title}</li>)}</ul>
        <NoteComposer targetTable="client" targetId={clientSysId} onSaved={refresh} />
      </Section>

      <section>
        <h3>Timeline</h3>
        {timeline === null ? <p>Loading…</p>
          : timeline.length === 0 ? <p>No activity yet.</p>
          : (
            <ul style={{ listStyle: "none", padding: 0 }}>
              {timeline.map((e, i) => (
                <li key={i} style={{ padding: "3px 0" }}>
                  <span style={{ color: "#888" }}>{e.when.slice(0, 10)}</span> — {e.title}
                  {e.status ? <em style={{ color: "#888" }}> ({e.status})</em> : null}
                </li>
              ))}
            </ul>
          )}
      </section>

      {prepId && <MeetingPrepPanel meetingId={prepId} onClose={() => setPrepId(null)} />}
    </div>
  );
}
