import type { Client, Task, Contact, Dossier, Note, Transcript, AppSettings, AppStatus, TestResult } from "./types";
const BASE = "/api";

/** Fetch JSON, throwing on any non-2xx response (with FastAPI's `detail` if present)
 *  so callers never silently receive an error body parsed as data. */
async function http<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, init);
  if (!res.ok) {
    let detail = "";
    try {
      detail = (await res.json())?.detail ?? "";
    } catch {
      /* response body was not JSON */
    }
    throw new Error(`API ${res.status} ${res.statusText} on ${path}${detail ? `: ${detail}` : ""}`);
  }
  return res.json() as Promise<T>;
}

/** Shared init for JSON-body mutations. */
function jsonBody(method: string, body: unknown): RequestInit {
  return { method, headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) };
}

export async function getClients(): Promise<Client[]> {
  return http<Client[]>("/clients");
}
export async function getNow(client?: string): Promise<Task[]> {
  const q = client ? `?client=${encodeURIComponent(client)}` : "";
  return http<Task[]>(`/now${q}`);
}
export async function createTask(t: Partial<Task>): Promise<Task> {
  return http<Task>("/tasks", jsonBody("POST", t));
}
export async function completeTask(sys_id: string): Promise<Task> {
  return http<Task>(`/tasks/${sys_id}`, jsonBody("PATCH", { status: "done" }));
}
export async function getDossier(clientSysId: string): Promise<Dossier> {
  return http<Dossier>(`/clients/${clientSysId}/dossier`);
}
export async function createContact(c: Partial<Contact>): Promise<Contact> {
  return http<Contact>("/contacts", jsonBody("POST", c));
}
export async function createNote(n: Partial<Note>): Promise<Note> {
  return http<Note>("/notes", jsonBody("POST", n));
}
export async function createTranscript(t: Partial<Transcript>): Promise<Transcript> {
  return http<Transcript>("/transcripts", jsonBody("POST", t));
}
export async function getStatus(): Promise<AppStatus> {
  return http<AppStatus>("/status");
}
export async function getSettings(): Promise<AppSettings> {
  return http<AppSettings>("/settings");
}
export async function saveSettings(s: Partial<AppSettings> & { password?: string }): Promise<AppSettings> {
  return http<AppSettings>("/settings", jsonBody("PUT", s));
}
export async function testConnection(): Promise<TestResult> {
  return http<TestResult>("/test-connection", { method: "POST" });
}
