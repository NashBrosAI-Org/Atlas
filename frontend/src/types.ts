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
export interface Dossier {
  client: Client;
  contacts: Contact[];
  engagements: Engagement[];
  themes: Theme[];
  open_tasks: Task[];
  meetings: Meeting[];
  notes: Note[];
}
