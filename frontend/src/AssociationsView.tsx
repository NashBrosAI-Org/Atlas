import { useEffect, useState } from "react";
import { getAssociations, getClients, reassignAssociation } from "./api";
import type { Association, Client } from "./types";
import { Button, Select } from "./ui";

const NONE = "";

export function AssociationsView({ onOpenClient }: { onOpenClient: (id: string) => void }) {
  const [emails, setEmails] = useState<Association[] | null>(null);
  const [meetings, setMeetings] = useState<Association[] | null>(null);
  const [clients, setClients] = useState<Client[]>([]);
  const [busy, setBusy] = useState<string | null>(null);
  const [err, setErr] = useState("");

  function load() {
    getAssociations()
      .then((a) => { setEmails(a.emails); setMeetings(a.meetings); })
      .catch((e) => setErr(String(e)));
    getClients().then(setClients).catch((e) => setErr(String(e)));
  }

  useEffect(load, []);

  async function reassign(row: Association, client: string) {
    setBusy(row.sys_id);
    setErr("");
    try {
      await reassignAssociation(row.type, row.sys_id, client);
      load();
    } catch (e) {
      setErr(String(e));
    } finally {
      setBusy(null);
    }
  }

  function section(title: string, rows: Association[] | null) {
    return (
      <>
        <h3 style={{ marginTop: 24 }}>{title}</h3>
        {rows === null ? <p>Loading…</p>
          : rows.length === 0 ? <p className="muted">Nothing to review.</p>
          : (
            <ul style={{ listStyle: "none", padding: 0 }}>
              {rows.map((row) => (
                <li key={row.sys_id} className="list-row" style={{ flexWrap: "wrap" }}>
                  <span style={{ flex: 1, minWidth: 200 }}>
                    <strong>{row.label}</strong>
                    {row.who ? <span className="muted"> · {row.who}</span> : null}
                    {row.client_name ? (
                      <Button variant="ghost" onClick={() => onOpenClient(row.client)}>
                        {row.client_name}
                      </Button>
                    ) : null}
                  </span>
                  <Select
                    style={{ width: "auto" }}
                    value={row.client || NONE}
                    disabled={busy === row.sys_id}
                    onChange={(e) => reassign(row, e.target.value)}
                  >
                    <option value={NONE}>— none —</option>
                    {clients.map((c) => (
                      <option key={c.sys_id} value={c.sys_id ?? ""}>{c.name}</option>
                    ))}
                  </Select>
                </li>
              ))}
            </ul>
          )}
      </>
    );
  }

  return (
    <div className="view">
      <h1>Associations</h1>
      <p className="muted">Confirm or correct the client auto-assigned to each ingested email and meeting.</p>
      {err && <p className="err">{err}</p>}
      {section("Emails", emails)}
      {section("Meetings", meetings)}
    </div>
  );
}
