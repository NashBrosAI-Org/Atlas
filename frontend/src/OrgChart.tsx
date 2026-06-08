import type { Contact } from "./types";

function childrenOf(parentId: string | undefined, all: Contact[]): Contact[] {
  return all.filter((c) => (c.reports_to || "") === (parentId || ""));
}

function Node({ contact, all }: { contact: Contact; all: Contact[] }) {
  const kids = childrenOf(contact.sys_id, all);
  const badge = contact.sentiment === "champion" ? "⭐" : contact.sentiment === "detractor" ? "⚠️" : "";
  return (
    <li>
      <span>{badge} <strong>{contact.name}</strong>{contact.role_title ? ` — ${contact.role_title}` : ""}</span>
      {kids.length > 0 && <ul>{kids.map((k) => <Node key={k.sys_id} contact={k} all={all} />)}</ul>}
    </li>
  );
}

export function OrgChart({ contacts }: { contacts: Contact[] }) {
  const ids = new Set(contacts.map((c) => c.sys_id));
  const roots = contacts.filter((c) => !c.reports_to || !ids.has(c.reports_to));
  if (contacts.length === 0) return <p className="muted">No contacts yet.</p>;
  return <ul>{roots.map((r) => <Node key={r.sys_id} contact={r} all={contacts} />)}</ul>;
}
