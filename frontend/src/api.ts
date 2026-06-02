import type { Client, Task } from "./types";
const BASE = "http://localhost:8000/api";

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
