import type { Client, Task, Contact, Dossier, Note, Transcript, AppSettings, AppStatus, TestResult, ActivityEvent, RadarEntry, BackupStatus, ExportResult, TagOnRecord, KeyDate, Reminder, Link, Briefing, SyncResult, MeetingPrep, AIStatus } from "./types";
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
export async function createClient(c: Partial<Client>): Promise<Client> {
  return http<Client>("/clients", jsonBody("POST", c));
}
export async function updateClient(sysId: string, patch: Partial<Client>): Promise<Client> {
  return http<Client>(`/clients/${sysId}`, jsonBody("PATCH", patch));
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
export async function updateContact(sysId: string, patch: Partial<Contact>): Promise<Contact> {
  return http<Contact>(`/contacts/${sysId}`, jsonBody("PATCH", patch));
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
export async function getActivity(limit = 50): Promise<ActivityEvent[]> {
  return http<ActivityEvent[]>(`/awareness/activity?limit=${limit}`);
}
export async function getTimeline(clientId: string): Promise<ActivityEvent[]> {
  return http<ActivityEvent[]>(`/awareness/timeline/${clientId}`);
}
export async function getRadar(): Promise<RadarEntry[]> {
  return http<RadarEntry[]>("/awareness/radar");
}
export async function getBackupStatus(): Promise<BackupStatus> {
  return http<BackupStatus>("/backup/status");
}
export async function runExport(): Promise<ExportResult> {
  return http<ExportResult>("/backup/export", { method: "POST" });
}
export async function restoreBackup(): Promise<{ created: number; updated: number; from: string }> {
  return http("/backup/restore", { method: "POST" });
}
export async function getTagsOn(table: string, id: string): Promise<TagOnRecord[]> {
  return http<TagOnRecord[]>(`/tags/on/${table}/${encodeURIComponent(id)}`);
}
export async function attachTag(table: string, id: string, name: string): Promise<unknown> {
  return http(`/tags/on/${table}/${encodeURIComponent(id)}`, jsonBody("POST", { name }));
}
export async function detachTag(table: string, id: string, tagId: string): Promise<unknown> {
  return http(`/tags/on/${table}/${encodeURIComponent(id)}/${tagId}`, { method: "DELETE" });
}
export async function getReminders(): Promise<Reminder[]> {
  return http<Reminder[]>("/reminders");
}
export async function createKeyDate(k: Partial<KeyDate>): Promise<KeyDate> {
  return http<KeyDate>("/key-dates", jsonBody("POST", k));
}
export async function createLink(l: Partial<Link>): Promise<Link> {
  return http<Link>("/links", jsonBody("POST", l));
}
export async function deleteLink(sys_id: string): Promise<unknown> {
  return http(`/links/${sys_id}`, { method: "DELETE" });
}
export async function getBriefing(): Promise<Briefing> {
  return http<Briefing>("/briefing");
}
export async function syncMail(): Promise<SyncResult> {
  return http<SyncResult>("/m365/sync", { method: "POST" });
}
export async function syncCalendar(): Promise<SyncResult> {
  return http<SyncResult>("/m365/calendar/sync", { method: "POST" });
}
export async function getMeetingPrep(meetingId: string): Promise<MeetingPrep> {
  return http<MeetingPrep>(`/m365/prep/${meetingId}`);
}
export async function getAIStatus(): Promise<AIStatus> { return http<AIStatus>("/ai/status"); }
export async function summarizeClient(id: string): Promise<{ summary: string }> {
  return http(`/ai/summary/client/${id}`, { method: "POST" });
}
export async function extractContactFromSignature(signature: string): Promise<{ name: string; role_title: string; email: string; phone: string }> {
  return http("/ai/extract/contact", jsonBody("POST", { signature }));
}
