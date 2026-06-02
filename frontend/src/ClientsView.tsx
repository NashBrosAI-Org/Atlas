import { useEffect, useState } from "react";
import type { Client } from "./types";
import { getClients } from "./api";

export function ClientsView({ onOpen }: { onOpen: (sysId: string) => void }) {
  const [clients, setClients] = useState<Client[]>([]);
  useEffect(() => { getClients().then(setClients); }, []);
  return (
    <div style={{ maxWidth: 720, margin: "2rem auto", fontFamily: "system-ui" }}>
      <h1>Clients</h1>
      <ul style={{ listStyle: "none", padding: 0 }}>
        {clients.map((c) => (
          <li key={c.sys_id} style={{ padding: "8px 0", borderBottom: "1px solid #eee" }}>
            <button onClick={() => onOpen(c.sys_id!)} style={{ background: "none", border: "none", color: "#0a7", cursor: "pointer", fontSize: 16 }}>
              {c.name}{c.short_code ? ` (${c.short_code})` : ""}
            </button>
          </li>
        ))}
      </ul>
    </div>
  );
}
