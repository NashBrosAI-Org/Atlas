import { useEffect, useState } from "react";
import type { Client, Task } from "./types";
import { getClients, getNow, completeTask } from "./api";

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
