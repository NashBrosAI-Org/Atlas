export interface Client { sys_id?: string; name: string; short_code?: string; status?: string; }
export interface Task {
  sys_id?: string; title: string; client?: string;
  engagement?: string; theme?: string;
  priority?: "critical" | "high" | "medium" | "low";
  due_date?: string; promised_date?: string;
  is_commitment?: boolean;
  status?: "open" | "in_progress" | "waiting" | "done";
  source?: "manual" | "email" | "meeting";
}
export interface Contact {
  sys_id?: string; name: string; email?: string; phone?: string; client?: string;
  role_title?: string; reports_to?: string; personal_notes?: string;
  sentiment?: "champion" | "neutral" | "detractor";
}
export interface Engagement {
  sys_id?: string; name: string; client?: string;
  status?: "on_track" | "at_risk" | "blocked" | "done";
  start_date?: string; target_date?: string; description?: string;
}
export interface Theme {
  sys_id?: string; name: string; client?: string;
  status?: "open" | "watching" | "resolved"; description?: string;
}
export interface Meeting {
  sys_id?: string; title: string; client?: string; engagement?: string;
  datetime?: string; type?: "teams" | "zoom" | "other"; attendees?: string; summary?: string;
  graph_event_id?: string;
}
export interface Transcript {
  sys_id?: string; meeting?: string; client?: string; full_text: string;
  source?: "teams" | "zoom" | "manual"; captured_date?: string;
}
export interface Note {
  sys_id?: string; title: string; body?: string;
  note_type?: "general" | "risk" | "issue" | "decision";
  target_table?: string; target_id?: string; pinned?: boolean;
}
export interface TagOnRecord { sys_id: string; name: string; link_id: string; }
export type KeyDateType = "renewal" | "qbr" | "contract_end" | "birthday" | "milestone";
export interface KeyDate {
  sys_id?: string;
  title: string;
  type?: KeyDateType;
  date?: string;
  recurring?: boolean;
  reminder_lead_days?: number;
  client?: string;
  contact?: string;
}
export interface Reminder {
  sys_id: string;
  title: string;
  type: string;
  date: string;
  days_until: number;
  recurring: boolean;
  reminder_lead_days: number;
  client: string;
  client_name: string;
  contact: string;
}
export interface Link {
  sys_id?: string;
  title: string;
  url?: string;
  client?: string;
}
export interface Dossier {
  client: Client;
  contacts: Contact[];
  engagements: Engagement[];
  themes: Theme[];
  open_tasks: Task[];
  meetings: Meeting[];
  key_dates: KeyDate[];
  links: Link[];
  notes: Note[];
  tags: TagOnRecord[];
}
export interface AppSettings {
  use_fake: boolean;
  sn_instance_url: string;
  sn_scope: string;
  sn_auth: string;
  sn_oauth_username: string;
  password_set: boolean;
  cooling_days: number;
  stale_days: number;
}
export interface ActivityEvent {
  type: string;
  title: string;
  when: string;
  client: string;
  client_name: string;
  status: string | null;
}
export interface RadarEntry {
  client: string;
  client_name: string;
  last_activity: string;
  days_quiet: number;
  tier: "cooling" | "stale";
}
export interface AppStatus {
  fake: boolean;
  configured: boolean;
}
export interface TestResult {
  ok: boolean;
  error?: string;
}
export interface BackupStatus {
  last_backup: string | null;
  count: number;
  stale: boolean;
  max_age_days: number;
  backups_dir: string;
}
export interface ExportResult {
  path: string;
  created_at: string;
  counts: Record<string, number>;
}
