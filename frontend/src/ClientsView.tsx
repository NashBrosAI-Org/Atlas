import { useEffect, useState } from "react";
import type { Client } from "./types";
import { getClients, createClient, updateClient } from "./api";

const STATUSES = ["active", "prospect", "dormant"];

const inputStyle: React.CSSProperties = {
  display: "block", width: "100%", boxSizing: "border-box",
  padding: "6px 8px", margin: "4px 0", fontSize: 14,
  border: "1px solid #ccc", borderRadius: 4, fontFamily: "inherit",
};
const labelStyle: React.CSSProperties = { fontSize: 12, color: "#555", marginTop: 8 };
const btnStyle: React.CSSProperties = {
  padding: "6px 12px", fontSize: 14, border: "1px solid #ccc",
  borderRadius: 4, background: "#f7f7f7", cursor: "pointer",
};
const helpStyle: React.CSSProperties = { fontSize: 12, color: "#888", margin: "4px 0 0" };

export function ClientsView({ onOpen }: { onOpen: (sysId: string) => void }) {
  const [clients, setClients] = useState<Client[]>([]);
  const [name, setName] = useState("");
  const [shortCode, setShortCode] = useState("");
  const [status, setStatus] = useState("active");
  const [busy, setBusy] = useState(false);
  const [msg, setMsg] = useState("");

  const refresh = () => getClients().then(setClients).catch((e) => setMsg(String(e)));
  useEffect(() => { refresh(); }, []);

  async function add() {
    if (!name.trim() || busy) return;
    setBusy(true);
    setMsg("");
    try {
      await createClient({ name: name.trim(), short_code: shortCode.trim() || undefined, status });
      setName(""); setShortCode(""); setStatus("active");
      await refresh();
    } catch (e) {
      setMsg(String(e));
    } finally {
      setBusy(false);
    }
  }

  return (
    <div style={{ maxWidth: 720, margin: "2rem auto", fontFamily: "system-ui" }}>
      <h1>Clients</h1>

      <div style={{ border: "1px solid #eee", borderRadius: 6, padding: 12, marginBottom: 16, background: "#fafafa" }}>
        <strong style={{ fontSize: 14 }}>Add client</strong>
        <label style={labelStyle}>Name *
          <input style={inputStyle} value={name} onChange={(e) => setName(e.target.value)} placeholder="Acme Corp" />
        </label>
        <label style={labelStyle}>Short code
          <input style={inputStyle} value={shortCode} onChange={(e) => setShortCode(e.target.value)} placeholder="ACME" />
        </label>
        <label style={labelStyle}>Status
          <select style={inputStyle} value={status} onChange={(e) => setStatus(e.target.value)}>
            {STATUSES.map((s) => <option key={s} value={s}>{s}</option>)}
          </select>
        </label>
        <button style={{ ...btnStyle, marginTop: 8 }} disabled={busy || !name.trim()} onClick={add}>Add client</button>
        {msg && <p style={{ ...helpStyle, color: "#b00020" }}>{msg}</p>}
      </div>

      <ul style={{ listStyle: "none", padding: 0 }}>
        {clients.map((c) => (
          <ClientRow key={c.sys_id} client={c} onOpen={onOpen} onSaved={refresh} />
        ))}
      </ul>
    </div>
  );
}

function ClientRow({ client, onOpen, onSaved }: {
  client: Client; onOpen: (sysId: string) => void; onSaved: () => void;
}) {
  const [editing, setEditing] = useState(false);
  const [draft, setDraft] = useState<Client>(client);
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState("");

  useEffect(() => { setDraft(client); }, [client]);

  const set = (patch: Partial<Client>) => setDraft({ ...draft, ...patch });

  async function save() {
    if (!client.sys_id || busy) return;
    setBusy(true);
    setErr("");
    try {
      await updateClient(client.sys_id, {
        short_code: draft.short_code,
        status: draft.status,
        email_domains: draft.email_domains,
        email_aliases: draft.email_aliases,
        notes: draft.notes,
      });
      await onSaved();
      setEditing(false);
    } catch (e) {
      setErr(String(e));
    } finally {
      setBusy(false);
    }
  }

  return (
    <li style={{ padding: "8px 0", borderBottom: "1px solid #eee" }}>
      <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
        <button onClick={() => onOpen(client.sys_id!)} style={{ background: "none", border: "none", color: "#0a7", cursor: "pointer", fontSize: 16, flex: 1, textAlign: "left", padding: 0 }}>
          {client.name}{client.short_code ? ` (${client.short_code})` : ""}
        </button>
        <span style={{ fontSize: 12, color: "#999" }}>{client.status}</span>
        <button style={btnStyle} onClick={() => setEditing((v) => !v)}>{editing ? "Cancel" : "Edit"}</button>
      </div>

      {editing && (
        <div style={{ marginTop: 8, paddingLeft: 4 }}>
          <label style={labelStyle}>Short code
            <input style={inputStyle} value={draft.short_code ?? ""} onChange={(e) => set({ short_code: e.target.value })} />
          </label>
          <label style={labelStyle}>Status
            <select style={inputStyle} value={draft.status ?? "active"} onChange={(e) => set({ status: e.target.value })}>
              {STATUSES.map((s) => <option key={s} value={s}>{s}</option>)}
            </select>
          </label>
          <label style={labelStyle}>Email domains
            <input style={inputStyle} value={draft.email_domains ?? ""} onChange={(e) => set({ email_domains: e.target.value })} placeholder="acme.com, acme.io" />
          </label>
          <label style={labelStyle}>Email aliases
            <input style={inputStyle} value={draft.email_aliases ?? ""} onChange={(e) => set({ email_aliases: e.target.value })} placeholder="someone@gmail.com" />
          </label>
          <p style={helpStyle}>Domains and aliases drive automatic email/meeting → client matching.</p>
          <label style={labelStyle}>Notes
            <textarea style={{ ...inputStyle, minHeight: 60, resize: "vertical" }} value={draft.notes ?? ""} onChange={(e) => set({ notes: e.target.value })} />
          </label>
          <button style={{ ...btnStyle, marginTop: 8 }} disabled={busy} onClick={save}>Save</button>
          {err && <p style={{ ...helpStyle, color: "#b00020" }}>{err}</p>}
        </div>
      )}
    </li>
  );
}
