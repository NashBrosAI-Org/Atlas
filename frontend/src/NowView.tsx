import { useEffect, useState } from "react";
import type { Client, Task, Briefing } from "./types";
import { getClients, getNow, completeTask, getBriefing, syncMail, syncCalendar, createTask, getAIStatus, suggestFocus } from "./api";
import { MeetingPrepPanel } from "./MeetingPrepPanel";
import { Button, Input, Select, Checkbox, Card, Badge, Toolbar } from "./ui";

const PRIORITIES = ["critical", "high", "medium", "low"] as const;

const PRIORITY_TONE: Record<string, "danger" | "warning" | "info" | "neutral"> = {
  critical: "danger",
  high: "warning",
  medium: "info",
  low: "neutral",
};

/** Plain-English reason a task sits where it does in the deterministic Now order. */
function rankReason(t: Task): string {
  const parts = [`priority: ${t.priority ?? "medium"}`,
                 `due: ${t.due_date ?? "none"}`,
                 t.is_commitment ? "commitment (sorts ahead of ties)" : "not a commitment"];
  return "Ranked by " + parts.join(" · ");
}

function TaskComposer({ clients, defaultClient, onAdded }:
  { clients: Client[]; defaultClient: string; onAdded: () => void }) {
  const [title, setTitle] = useState("");
  const [priority, setPriority] = useState<(typeof PRIORITIES)[number]>("medium");
  const [client, setClient] = useState(defaultClient);
  const [dueDate, setDueDate] = useState("");
  const [commitment, setCommitment] = useState(false);
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState("");

  useEffect(() => { setClient(defaultClient); }, [defaultClient]);

  async function add() {
    if (!title.trim() || busy) return;
    setBusy(true);
    setErr("");
    try {
      await createTask({
        title: title.trim(), priority, client: client || undefined,
        due_date: dueDate || undefined, is_commitment: commitment, status: "open",
      });
      setTitle(""); setDueDate(""); setCommitment(false);
      onAdded();
    } catch (e) {
      setErr(String(e));
    } finally {
      setBusy(false);
    }
  }

  return (
    <Toolbar wrap>
      <Input style={{ flex: 1, minWidth: 180 }} placeholder="Add a task…" value={title}
        onChange={(e) => setTitle(e.target.value)} onKeyDown={(e) => e.key === "Enter" && add()} />
      <Select style={{ width: "auto" }} value={priority} onChange={(e) => setPriority(e.target.value as typeof priority)}>
        {PRIORITIES.map((p) => <option key={p} value={p}>{p}</option>)}
      </Select>
      <Select style={{ width: "auto" }} value={client} onChange={(e) => setClient(e.target.value)}>
        <option value="">No client</option>
        {clients.map((c) => <option key={c.sys_id} value={c.sys_id}>{c.name}</option>)}
      </Select>
      <Input style={{ width: "auto" }} type="date" value={dueDate} onChange={(e) => setDueDate(e.target.value)} />
      <Checkbox checked={commitment} onChange={(e) => setCommitment(e.target.checked)} label="🤝" />
      <Button variant="primary" disabled={busy || !title.trim()} onClick={add}>Add</Button>
      {err && <span className="err" style={{ fontSize: 13 }}>{err}</span>}
    </Toolbar>
  );
}

function whenLabel(days: number): string {
  if (days <= 0) return "today";
  if (days === 1) return "tomorrow";
  return `in ${days} days`;
}

function TodayCard({ onSynced }: { onSynced: () => void }) {
  const [b, setB] = useState<Briefing | null>(null);
  const [busy, setBusy] = useState(false);
  const [msg, setMsg] = useState("");
  const [prepId, setPrepId] = useState<string | null>(null);

  const refresh = () => getBriefing().then(setB).catch((e) => setMsg(String(e)));
  useEffect(() => { refresh(); }, []);

  async function run(kind: "mail" | "calendar") {
    setBusy(true);
    setMsg("");
    try {
      const r = kind === "mail" ? await syncMail() : await syncCalendar();
      const extra = r.tasks_created ? `, ${r.tasks_created} task(s)` : "";
      setMsg(`Synced ${kind}: ${r.ingested} new${extra} (${r.skipped} already had).`);
      await refresh();
      onSynced();  // mail sync can create tasks → refresh the Now list too
    } catch (e) {
      setMsg(String(e));
    } finally {
      setBusy(false);
    }
  }

  if (!b) return msg ? <p className="err" style={{ fontSize: 13 }}>{msg}</p> : null;

  return (
    <Card variant="muted" className="section">
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <h2 style={{ margin: 0 }}>Today · {b.date}</h2>
        <Toolbar>
          <Button size="sm" disabled={busy} onClick={() => run("mail")}>Sync mail</Button>
          <Button size="sm" disabled={busy} onClick={() => run("calendar")}>Sync calendar</Button>
        </Toolbar>
      </div>
      {msg && <p className="muted" style={{ fontSize: 13, marginTop: 6 }}>{msg}</p>}

      <div style={{ marginTop: 12 }}>
        <strong style={{ fontSize: 13 }}>Meetings</strong>
        {b.todays_meetings.length === 0 ? <span className="muted"> — none today</span> : (
          <ul style={{ margin: "4px 0", paddingLeft: 18 }}>
            {b.todays_meetings.map((m, i) => (
              <li key={m.sys_id ?? i}>{m.title}{" "}
                <span className="muted">{(m.datetime ?? "").slice(11, 16)}</span>{" "}
                {m.sys_id && <Button size="sm" variant="ghost" onClick={() => setPrepId(m.sys_id!)}>Prep</Button>}</li>
            ))}
          </ul>
        )}
      </div>

      <div style={{ marginTop: 6 }}>
        <strong style={{ fontSize: 13 }}>Reminders</strong>
        {b.reminders.length === 0 ? <span className="muted"> — nothing due</span> : (
          <ul style={{ margin: "4px 0", paddingLeft: 18 }}>
            {b.reminders.map((r) => (
              <li key={r.sys_id}>
                <span style={{ color: r.days_until <= 1 ? "var(--danger)" : "var(--success)", fontWeight: 600 }}>
                  📅 {whenLabel(r.days_until)}
                </span>{" "}— {r.title}{r.client_name ? ` · ${r.client_name}` : ""}
              </li>
            ))}
          </ul>
        )}
      </div>

      {b.radar.length > 0 && (
        <p style={{ fontSize: 13, color: "var(--warning)", margin: "8px 0 0" }}>
          ⚠ {b.radar.length} client{b.radar.length > 1 ? "s" : ""} need attention — see the Awareness tab.
        </p>
      )}

      {prepId && <MeetingPrepPanel meetingId={prepId} onClose={() => setPrepId(null)} />}
    </Card>
  );
}

/** Advisory AI focus suggestion (rule #6). It NEVER reorders or mutates the task
 *  list — the deterministic Now order stays authoritative; this is text-only help. */
function FocusPanel() {
  const [enabled, setEnabled] = useState(false);
  const [suggestion, setSuggestion] = useState("");
  const [busy, setBusy] = useState(false);
  const [msg, setMsg] = useState("");

  useEffect(() => { getAIStatus().then((s) => setEnabled(s.enabled)).catch(() => setEnabled(false)); }, []);

  async function run() {
    if (busy) return;
    setBusy(true);
    setMsg("");
    try {
      const r = await suggestFocus();
      setSuggestion(r.suggestion);
    } catch (e) {
      setMsg(String(e));
    } finally {
      setBusy(false);
    }
  }

  if (!enabled) return null;

  return (
    <Card variant="accent" style={{ margin: "12px 0" }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", gap: 12 }}>
        <strong style={{ fontSize: 13 }}>AI focus (suggestion — your Now order is unchanged)</strong>
        <Button size="sm" disabled={busy} onClick={run}>Suggest focus</Button>
      </div>
      {msg && <p className="err" style={{ fontSize: 13, marginTop: 6 }}>{msg}</p>}
      {suggestion && (
        <div style={{ whiteSpace: "pre-wrap", fontSize: 13, marginTop: 8 }}>{suggestion}</div>
      )}
    </Card>
  );
}

export function NowView() {
  const [clients, setClients] = useState<Client[]>([]);
  const [tasks, setTasks] = useState<Task[]>([]);
  const [filter, setFilter] = useState<string>("");

  const refresh = () => getNow(filter || undefined).then(setTasks);
  useEffect(() => { getClients().then(setClients); }, []);
  useEffect(() => { refresh(); }, [filter]);

  return (
    <div className="view view--narrow">
      <h1>Now</h1>
      <TodayCard onSynced={refresh} />
      <div className="stack">
        <Select style={{ width: "auto" }} value={filter} onChange={(e) => setFilter(e.target.value)}>
          <option value="">All clients</option>
          {clients.map((c) => <option key={c.sys_id} value={c.sys_id}>{c.name}</option>)}
        </Select>
        <TaskComposer clients={clients} defaultClient={filter} onAdded={refresh} />
      </div>
      <FocusPanel />
      <p className="muted" style={{ fontSize: 12, margin: "12px 0 0" }}>
        Ordered deterministically: <strong>priority</strong> → <strong>due date</strong> →
        commitments first. (Hover a task to see why it ranks where it does.)
      </p>
      <ul style={{ listStyle: "none", padding: 0, margin: "4px 0 0" }}>
        {tasks.map((t) => (
          <li key={t.sys_id} title={rankReason(t)} className="list-row">
            <span style={{ width: 78 }}>
              <Badge tone={PRIORITY_TONE[t.priority ?? "medium"] ?? "neutral"}>{t.priority}</Badge>
            </span>
            <span style={{ flex: 1 }}>{t.is_commitment ? "🤝 " : ""}{t.title}</span>
            <span className="muted" style={{ width: 100 }}>{t.due_date ?? "—"}</span>
            <Button size="sm" onClick={() => completeTask(t.sys_id!).then(refresh)}>Done</Button>
          </li>
        ))}
      </ul>
    </div>
  );
}
