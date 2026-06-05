import { useEffect, useState } from "react";
import { getAssociations, getClients, reassignAssociation } from "./api";
import type { Association, Client } from "./types";

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
          : rows.length === 0 ? <p>Nothing to review.</p>
          : (
            <ul style={{ listStyle: "none", padding: 0 }}>
              {rows.map((row) => (
                <li key={row.sys_id} style={{ padding: "6px 0", borderBottom: "1px solid #eee" }}>
                  <strong>{row.label}</strong>
                  {row.who ? <span style={{ color: "#888" }}> · {row.who}</span> : null}
                  {row.client_name ? (
                    <>
                      {" "}
                      <button
                        style={{ border: "none", background: "none", color: "#06c", cursor: "pointer", padding: 0 }}
                        onClick={() => onOpenClient(row.client)}
                      >
                        {row.client_name}
                      </button>
                    </>
                  ) : null}
                  {" "}
                  <select
                    value={row.client || NONE}
                    disabled={busy === row.sys_id}
                    onChange={(e) => reassign(row, e.target.value)}
                  >
                    <option value={NONE}>— none —</option>
                    {clients.map((c) => (
                      <option key={c.sys_id} value={c.sys_id ?? ""}>{c.name}</option>
                    ))}
                  </select>
                </li>
              ))}
            </ul>
          )}
      </>
    );
  }

  return (
    <div style={{ padding: 16, fontFamily: "system-ui", maxWidth: 820 }}>
      <h2>Associations</h2>
      <p style={{ color: "#888" }}>Confirm or correct the client auto-assigned to each ingested email and meeting.</p>
      {err && <p style={{ color: "#b00020" }}>{err}</p>}
      {section("Emails", emails)}
      {section("Meetings", meetings)}
    </div>
  );
}
