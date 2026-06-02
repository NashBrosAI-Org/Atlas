export interface Client { sys_id?: string; name: string; short_code?: string; status?: string; }
export interface Task {
  sys_id?: string; title: string; client?: string;
  priority?: "critical" | "high" | "medium" | "low";
  due_date?: string; is_commitment?: boolean; status?: string;
}
