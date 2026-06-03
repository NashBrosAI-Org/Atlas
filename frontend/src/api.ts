import type { Client, Task, Contact, Dossier, Note, Transcript } from "./types";
const BASE = "/api";

export async function getClients(): Promise<Client[]> {
  return (await fetch(`${BASE}/clients`)).json();
}
export async function getNow(client?: string): Promise<Task[]> {
  const q = client ? `?client=${encodeURIComponent(client)}` : "";
  return (await fetch(`${BASE}/now${q}`)).json();
}
export async function createTask(t: Partial<Task>): Promise<Task> {
  return (await fetch(`${BASE}/tasks`, {
    method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(t),
  })).json();
}
export async function completeTask(sys_id: string): Promise<Task> {
  return (await fetch(`${BASE}/tasks/${sys_id}`, {
    method: "PATCH", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ status: "done" }),
  })).json();
}
export async function getDossier(clientSysId: string): Promise<Dossier> {
  return (await fetch(`${BASE}/clients/${clientSysId}/dossier`)).json();
}
export async function createContact(c: Partial<Contact>): Promise<Contact> {
  return (await fetch(`${BASE}/contacts`, {
    method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(c),
  })).json();
}
export async function createNote(n: Partial<Note>): Promise<Note> {
  return (await fetch(`${BASE}/notes`, {
    method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(n),
  })).json();
}
export async function createTranscript(t: Partial<Transcript>): Promise<Transcript> {
  return (await fetch(`${BASE}/transcripts`, {
    method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(t),
  })).json();
}
