import { useEffect, useState } from "react";
import type { Contact } from "./types";
import { createContact, updateContact, getAIStatus, extractContactFromSignature } from "./api";
import { Button, Input, Select, Textarea, Field, Card, Badge } from "./ui";

const SENTIMENTS: Contact["sentiment"][] = ["champion", "neutral", "detractor"];

const SENTIMENT_TONE: Record<string, "success" | "danger" | "neutral"> = {
  champion: "success",
  detractor: "danger",
  neutral: "neutral",
};

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
  const [aiEnabled, setAiEnabled] = useState(false);
  const [signature, setSignature] = useState("");
  const [autofilling, setAutofilling] = useState(false);

  useEffect(() => {
    getAIStatus().then((s) => setAiEnabled(s.enabled)).catch(() => setAiEnabled(false));
  }, []);

  async function autofill() {
    if (!signature.trim() || autofilling) return;
    setAutofilling(true);
    setErr("");
    try {
      const f = await extractContactFromSignature(signature);
      // Pre-fill the composer; the user reviews/edits before clicking Add.
      if (f.name) setName(f.name);
      if (f.role_title) setRoleTitle(f.role_title);
      if (f.email) setEmail(f.email);
      if (f.phone) setPhone(f.phone);
    } catch (e) {
      setErr(String(e));
    } finally {
      setAutofilling(false);
    }
  }

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
    <Card variant="muted">
      <h2>Add contact</h2>
      <div className="stack">
        {aiEnabled && (
          <div className="stack" style={{ paddingBottom: 12, borderBottom: "1px solid var(--border)" }}>
            <Field label="Autofill from signature" help="Pre-fills the fields below — review before adding.">
              <Textarea value={signature} onChange={(e) => setSignature(e.target.value)}
                placeholder="Paste an email signature here…" />
            </Field>
            <div>
              <Button size="sm" disabled={autofilling || !signature.trim()} onClick={autofill}>
                {autofilling ? "Autofilling…" : "Autofill"}
              </Button>
            </div>
          </div>
        )}
        <Field label="Name *">
          <Input value={name} onChange={(e) => setName(e.target.value)} placeholder="Jane Doe" />
        </Field>
        <Field label="Role / title">
          <Input value={roleTitle} onChange={(e) => setRoleTitle(e.target.value)} placeholder="VP Engineering" />
        </Field>
        <Field label="Email">
          <Input value={email} onChange={(e) => setEmail(e.target.value)} placeholder="jane@acme.com" />
        </Field>
        <Field label="Phone">
          <Input value={phone} onChange={(e) => setPhone(e.target.value)} placeholder="+1 555 0100" />
        </Field>
        <Field label="Sentiment">
          <Select value={sentiment ?? "neutral"} onChange={(e) => setSentiment(e.target.value as Contact["sentiment"])}>
            {SENTIMENTS.map((s) => <option key={s} value={s}>{s}</option>)}
          </Select>
        </Field>
        <Field label="Reports to">
          <Select value={reportsTo} onChange={(e) => setReportsTo(e.target.value)}>
            <option value="">— none —</option>
            {contacts.map((c) => <option key={c.sys_id} value={c.sys_id}>{c.name}</option>)}
          </Select>
        </Field>
        <div>
          <Button variant="primary" disabled={busy || !name.trim()} onClick={add}>Add contact</Button>
        </div>
        {err && <p className="err" style={{ fontSize: 12 }}>{err}</p>}
      </div>
    </Card>
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
        sentiment: draft.sentiment,
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
    <li style={{ borderBottom: "1px solid var(--border)", padding: "10px 0" }}>
      <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
        <span style={{ flex: 1 }}>
          <strong>{contact.name}</strong>{contact.role_title ? ` — ${contact.role_title}` : ""}
        </span>
        <Badge tone={SENTIMENT_TONE[contact.sentiment ?? "neutral"] ?? "neutral"}>{contact.sentiment ?? "neutral"}</Badge>
        <Button size="sm" onClick={() => setEditing((v) => !v)}>{editing ? "Cancel" : "Edit"}</Button>
      </div>

      {editing && (
        <div className="stack" style={{ marginTop: 10, paddingLeft: 4 }}>
          <Field label="Name *">
            <Input value={draft.name ?? ""} onChange={(e) => set({ name: e.target.value })} />
          </Field>
          <Field label="Role / title">
            <Input value={draft.role_title ?? ""} onChange={(e) => set({ role_title: e.target.value })} />
          </Field>
          <Field label="Email">
            <Input value={draft.email ?? ""} onChange={(e) => set({ email: e.target.value })} />
          </Field>
          <Field label="Phone">
            <Input value={draft.phone ?? ""} onChange={(e) => set({ phone: e.target.value })} />
          </Field>
          <Field label="Sentiment">
            <Select value={draft.sentiment ?? "neutral"} onChange={(e) => set({ sentiment: e.target.value as Contact["sentiment"] })}>
              {SENTIMENTS.map((s) => <option key={s} value={s}>{s}</option>)}
            </Select>
          </Field>
          <Field label="Reports to">
            <Select value={draft.reports_to ?? ""} onChange={(e) => set({ reports_to: e.target.value })}>
              <option value="">— none —</option>
              {managerOptions.map((c) => <option key={c.sys_id} value={c.sys_id}>{c.name}</option>)}
            </Select>
          </Field>
          <div>
            <Button variant="primary" size="sm" disabled={busy || !draft.name.trim()} onClick={save}>Save</Button>
          </div>
          {err && <p className="err" style={{ fontSize: 12 }}>{err}</p>}
        </div>
      )}
    </li>
  );
}
