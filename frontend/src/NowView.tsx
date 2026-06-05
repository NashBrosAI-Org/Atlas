import { useEffect, useState } from "react";
import type { Client, Task, Briefing } from "./types";
import { getClients, getNow, completeTask, getBriefing, syncMail, syncCalendar } from "./api";

function whenLabel(days: number): string {
  if (days <= 0) return "today";
  if (days === 1) return "tomorrow";
  return `in ${days} days`;
}

function TodayCard({ onSynced }: { onSynced: () => void }) {
  const [b, setB] = useState<Briefing | null>(null);
  const [busy, setBusy] = useState(false);
  const [msg, setMsg] = useState("");

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

  if (!b) return msg ? <p style={{ color: "#b00020", fontSize: 13 }}>{msg}</p> : null;

  return (
    <div style={{ border: "1px solid #ddd", borderRadius: 8, padding: 16, marginBottom: 24, background: "#fafafa" }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <h2 style={{ margin: 0, fontSize: 16 }}>Today · {b.date}</h2>
        <span style={{ display: "flex", gap: 6 }}>
          <button disabled={busy} onClick={() => run("mail")}>Sync mail</button>
          <button disabled={busy} onClick={() => run("calendar")}>Sync calendar</button>
        </span>
      </div>
      {msg && <p style={{ fontSize: 13, color: "#555", margin: "6px 0 0" }}>{msg}</p>}

      <div style={{ marginTop: 10 }}>
        <strong style={{ fontSize: 13 }}>Meetings</strong>
        {b.todays_meetings.length === 0 ? <span style={{ color: "#888" }}> — none today</span> : (
          <ul style={{ margin: "4px 0", paddingLeft: 18 }}>
            {b.todays_meetings.map((m, i) => (
              <li key={m.sys_id ?? i}>{m.title}{" "}
                <span style={{ color: "#888" }}>{(m.datetime ?? "").slice(11, 16)}</span></li>
            ))}
          </ul>
        )}
      </div>

      <div style={{ marginTop: 6 }}>
        <strong style={{ fontSize: 13 }}>Reminders</strong>
        {b.reminders.length === 0 ? <span style={{ color: "#888" }}> — nothing due</span> : (
          <ul style={{ margin: "4px 0", paddingLeft: 18 }}>
            {b.reminders.map((r) => (
              <li key={r.sys_id}>
                <span style={{ color: r.days_until <= 1 ? "#b00020" : "#0a7", fontWeight: 600 }}>
                  📅 {whenLabel(r.days_until)}
                </span>{" "}— {r.title}{r.client_name ? ` · ${r.client_name}` : ""}
              </li>
            ))}
          </ul>
        )}
      </div>

      {b.radar.length > 0 && (
        <p style={{ fontSize: 13, color: "#b8860b", margin: "6px 0 0" }}>
          ⚠ {b.radar.length} client{b.radar.length > 1 ? "s" : ""} need attention — see the Awareness tab.
        </p>
      )}
    </div>
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
    <div style={{ maxWidth: 720, margin: "2rem auto", fontFamily: "system-ui" }}>
      <h1>Now</h1>
      <TodayCard onSynced={refresh} />
      <select value={filter} onChange={(e) => setFilter(e.target.value)}>
        <option value="">All clients</option>
        {clients.map((c) => <option key={c.sys_id} value={c.sys_id}>{c.name}</option>)}
      </select>
      <ul style={{ listStyle: "none", padding: 0 }}>
        {tasks.map((t) => (
          <li key={t.sys_id} style={{ display: "flex", gap: 8, padding: "8px 0", borderBottom: "1px solid #eee" }}>
            <span style={{ width: 70, fontWeight: 600 }}>{t.priority}</span>
            <span style={{ flex: 1 }}>{t.is_commitment ? "🤝 " : ""}{t.title}</span>
            <span style={{ width: 100, color: "#888" }}>{t.due_date ?? "—"}</span>
            <button onClick={() => completeTask(t.sys_id!).then(refresh)}>Done</button>
          </li>
        ))}
      </ul>
    </div>
  );
}
