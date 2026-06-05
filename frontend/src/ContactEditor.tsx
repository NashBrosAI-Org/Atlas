import { useEffect, useState } from "react";
import type { Contact } from "./types";
import { createContact, updateContact } from "./api";

const SENTIMENTS: Contact["sentiment"][] = ["champion", "neutral", "detractor"];

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

/** Composer (add a new contact) + editable list (per-row edit) for a client's
 *  contacts. The OrgChart hierarchy display lives above this in the dossier. */
export function ContactEditor({ contacts, clientSysId, onChanged }: {
  contacts: Contact[]; clientSysId: string; onChanged: () => void;
}) {
  return (
    <div style={{ marginTop: 12 }}>
      <ContactComposer contacts={contacts} clientSysId={clientSysId} onSaved={onChanged} />
      {contacts.length > 0 && (
        <ul style={{ listStyle: "none", padding: 0, marginTop: 12 }}>
          {contacts.map((c) => (
            <ContactRow key={c.sys_id} contact={c} contacts={contacts} onSaved={onChanged} />
          ))}
        </ul>
      )}
    </div>
  );
}

function ContactComposer({ contacts, clientSysId, onSaved }: {
  contacts: Contact[]; clientSysId: string; onSaved: () => void;
}) {
  const [name, setName] = useState("");
  const [roleTitle, setRoleTitle] = useState("");
  const [email, setEmail] = useState("");
  const [phone, setPhone] = useState("");
  const [sentiment, setSentiment] = useState<Contact["sentiment"]>("neutral");
  const [reportsTo, setReportsTo] = useState("");
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState("");

  async function add() {
    if (!name.trim() || busy) return;
    setBusy(true);
    setErr("");
    try {
      await createContact({
        name: name.trim(),
        role_title: roleTitle.trim() || undefined,
        email: email.trim() || undefined,
        phone: phone.trim() || undefined,
        sentiment,
        reports_to: reportsTo || undefined,
        client: clientSysId,
      });
      setName(""); setRoleTitle(""); setEmail(""); setPhone("");
      setSentiment("neutral"); setReportsTo("");
      await onSaved();
    } catch (e) {
      setErr(String(e));
    } finally {
      setBusy(false);
    }
  }

  return (
    <div style={{ border: "1px solid #eee", borderRadius: 6, padding: 12, background: "#fafafa" }}>
      <strong style={{ fontSize: 14 }}>Add contact</strong>
      <label style={labelStyle}>Name *
        <input style={inputStyle} value={name} onChange={(e) => setName(e.target.value)} placeholder="Jane Doe" />
      </label>
      <label style={labelStyle}>Role / title
        <input style={inputStyle} value={roleTitle} onChange={(e) => setRoleTitle(e.target.value)} placeholder="VP Engineering" />
      </label>
      <label style={labelStyle}>Email
        <input style={inputStyle} value={email} onChange={(e) => setEmail(e.target.value)} placeholder="jane@acme.com" />
      </label>
      <label style={labelStyle}>Phone
        <input style={inputStyle} value={phone} onChange={(e) => setPhone(e.target.value)} placeholder="+1 555 0100" />
      </label>
      <label style={labelStyle}>Sentiment
        <select style={inputStyle} value={sentiment ?? "neutral"} onChange={(e) => setSentiment(e.target.value as Contact["sentiment"])}>
          {SENTIMENTS.map((s) => <option key={s} value={s}>{s}</option>)}
        </select>
      </label>
      <label style={labelStyle}>Reports to
        <select style={inputStyle} value={reportsTo} onChange={(e) => setReportsTo(e.target.value)}>
          <option value="">— none —</option>
          {contacts.map((c) => <option key={c.sys_id} value={c.sys_id}>{c.name}</option>)}
        </select>
      </label>
      <button style={{ ...btnStyle, marginTop: 8 }} disabled={busy || !name.trim()} onClick={add}>Add contact</button>
      {err && <p style={{ ...helpStyle, color: "#b00020" }}>{err}</p>}
    </div>
  );
}

function ContactRow({ contact, contacts, onSaved }: {
  contact: Contact; contacts: Contact[]; onSaved: () => void;
}) {
  const [editing, setEditing] = useState(false);
  const [draft, setDraft] = useState<Contact>(contact);
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState("");

  useEffect(() => { setDraft(contact); }, [contact]);

  const set = (patch: Partial<Contact>) => setDraft({ ...draft, ...patch });

  // A contact cannot report to itself.
  const managerOptions = contacts.filter((c) => c.sys_id !== contact.sys_id);

  async function save() {
    if (!contact.sys_id || !draft.name.trim() || busy) return;
    setBusy(true);
    setErr("");
    try {
      await updateContact(contact.sys_id, {
        name: draft.name.trim(),
        role_title: draft.role_title,
        email: draft.email,
        phone: draft.phone,
        sentiment: draft.sentiment ?? "neutral",
        reports_to: draft.reports_to || undefined,
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
        <span style={{ flex: 1 }}>
          <strong>{contact.name}</strong>{contact.role_title ? ` — ${contact.role_title}` : ""}
        </span>
        <span style={{ fontSize: 12, color: "#999" }}>{contact.sentiment ?? "neutral"}</span>
        <button style={btnStyle} onClick={() => setEditing((v) => !v)}>{editing ? "Cancel" : "Edit"}</button>
      </div>

      {editing && (
        <div style={{ marginTop: 8, paddingLeft: 4 }}>
          <label style={labelStyle}>Name *
            <input style={inputStyle} value={draft.name ?? ""} onChange={(e) => set({ name: e.target.value })} />
          </label>
          <label style={labelStyle}>Role / title
            <input style={inputStyle} value={draft.role_title ?? ""} onChange={(e) => set({ role_title: e.target.value })} />
          </label>
          <label style={labelStyle}>Email
            <input style={inputStyle} value={draft.email ?? ""} onChange={(e) => set({ email: e.target.value })} />
          </label>
          <label style={labelStyle}>Phone
            <input style={inputStyle} value={draft.phone ?? ""} onChange={(e) => set({ phone: e.target.value })} />
          </label>
          <label style={labelStyle}>Sentiment
            <select style={inputStyle} value={draft.sentiment ?? "neutral"} onChange={(e) => set({ sentiment: e.target.value as Contact["sentiment"] })}>
              {SENTIMENTS.map((s) => <option key={s} value={s}>{s}</option>)}
            </select>
          </label>
          <label style={labelStyle}>Reports to
            <select style={inputStyle} value={draft.reports_to ?? ""} onChange={(e) => set({ reports_to: e.target.value })}>
              <option value="">— none —</option>
              {managerOptions.map((c) => <option key={c.sys_id} value={c.sys_id}>{c.name}</option>)}
            </select>
          </label>
          <button style={{ ...btnStyle, marginTop: 8 }} disabled={busy || !draft.name.trim()} onClick={save}>Save</button>
          {err && <p style={{ ...helpStyle, color: "#b00020" }}>{err}</p>}
        </div>
      )}
    </li>
  );
}
