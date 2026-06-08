import { useEffect, useState } from "react";
import type { Client } from "./types";
import { getClients, createClient, updateClient } from "./api";
import { Button, Input, Select, Textarea, Field, Card, Badge } from "./ui";

const STATUSES = ["active", "prospect", "dormant"];

const STATUS_TONE: Record<string, "success" | "info" | "neutral"> = {
  active: "success",
  prospect: "info",
  dormant: "neutral",
};

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
    <div className="view view--narrow">
      <h1>Clients</h1>

      <Card variant="muted" className="section">
        <h2>Add client</h2>
        <div className="stack">
          <Field label="Name *">
            <Input value={name} onChange={(e) => setName(e.target.value)} placeholder="Acme Corp" />
          </Field>
          <Field label="Short code">
            <Input value={shortCode} onChange={(e) => setShortCode(e.target.value)} placeholder="ACME" />
          </Field>
          <Field label="Status">
            <Select value={status} onChange={(e) => setStatus(e.target.value)}>
              {STATUSES.map((s) => <option key={s} value={s}>{s}</option>)}
            </Select>
          </Field>
          <div>
            <Button variant="primary" disabled={busy || !name.trim()} onClick={add}>Add client</Button>
          </div>
          {msg && <p className="err" style={{ fontSize: 12 }}>{msg}</p>}
        </div>
      </Card>

      <ul style={{ listStyle: "none", padding: 0, margin: 0 }}>
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
    <li style={{ borderBottom: "1px solid var(--border)", padding: "10px 0" }}>
      <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
        <Button variant="ghost" onClick={() => onOpen(client.sys_id!)}
          style={{ flex: 1, justifyContent: "flex-start", fontSize: 15 }}>
          {client.name}{client.short_code ? ` (${client.short_code})` : ""}
        </Button>
        <Badge tone={STATUS_TONE[client.status ?? "active"] ?? "neutral"}>{client.status}</Badge>
        <Button size="sm" onClick={() => setEditing((v) => !v)}>{editing ? "Cancel" : "Edit"}</Button>
      </div>

      {editing && (
        <div className="stack" style={{ marginTop: 10, paddingLeft: 4 }}>
          <Field label="Short code">
            <Input value={draft.short_code ?? ""} onChange={(e) => set({ short_code: e.target.value })} />
          </Field>
          <Field label="Status">
            <Select value={draft.status ?? "active"} onChange={(e) => set({ status: e.target.value })}>
              {STATUSES.map((s) => <option key={s} value={s}>{s}</option>)}
            </Select>
          </Field>
          <Field label="Email domains"
            hint="Domains (e.g. acme.com) auto-match incoming mail/meetings to this client."
            help="Domains and aliases drive automatic email/meeting → client matching.">
            <Input value={draft.email_domains ?? ""} onChange={(e) => set({ email_domains: e.target.value })} placeholder="acme.com, acme.io" />
          </Field>
          <Field label="Email aliases"
            hint="Specific addresses a client also writes from, e.g. a personal gmail.">
            <Input value={draft.email_aliases ?? ""} onChange={(e) => set({ email_aliases: e.target.value })} placeholder="someone@gmail.com" />
          </Field>
          <Field label="Notes">
            <Textarea value={draft.notes ?? ""} onChange={(e) => set({ notes: e.target.value })} />
          </Field>
          <div>
            <Button variant="primary" size="sm" disabled={busy} onClick={save}>Save</Button>
          </div>
          {err && <p className="err" style={{ fontSize: 12 }}>{err}</p>}
        </div>
      )}
    </li>
  );
}
