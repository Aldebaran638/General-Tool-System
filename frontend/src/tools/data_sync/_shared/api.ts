/** Shared API calls for data_sync tool modules */

import type {
  SyncStatusResponse,
  SyncTasksResponse,
  TriggerRequest,
  SyncTask,
  WecomDepartmentsResponse,
  WecomMembersResponse,
} from "./types"

const BASE = "/api/v1/data-sync"

function authHeaders(): Record<string, string> {
  const token = localStorage.getItem("access_token")
  return token ? { Authorization: `Bearer ${token}` } : {}
}

async function apiFetch<T>(url: string, init?: RequestInit): Promise<T> {
  const res = await fetch(url, {
    ...init,
    headers: { "Content-Type": "application/json", ...authHeaders(), ...init?.headers },
  })
  if (!res.ok) {
    const body = await res.json().catch(() => ({}))
    throw new Error(body?.detail ?? `HTTP ${res.status}`)
  }
  return res.json() as Promise<T>
}

// ─── Department ───────────────────────────────────────────────────────────────

export function triggerDepartmentSync(body: TriggerRequest): Promise<SyncTask> {
  return apiFetch(`${BASE}/wecom-department/trigger`, {
    method: "POST",
    body: JSON.stringify(body),
  })
}

export function getDepartmentTasks(page = 1, limit = 20): Promise<SyncTasksResponse> {
  return apiFetch(`${BASE}/wecom-department/tasks?page=${page}&limit=${limit}`)
}

export function getDepartmentStatus(): Promise<SyncStatusResponse> {
  return apiFetch(`${BASE}/wecom-department/status`)
}

// ─── Member ───────────────────────────────────────────────────────────────────

export function triggerMemberSync(body: TriggerRequest): Promise<SyncTask> {
  return apiFetch(`${BASE}/wecom-member/trigger`, {
    method: "POST",
    body: JSON.stringify(body),
  })
}

export function getMemberTasks(page = 1, limit = 20): Promise<SyncTasksResponse> {
  return apiFetch(`${BASE}/wecom-member/tasks?page=${page}&limit=${limit}`)
}

export function getMemberStatus(): Promise<SyncStatusResponse> {
  return apiFetch(`${BASE}/wecom-member/status`)
}

// ─── Synced entity queries ──────────────────────────────────────────────────

export function getDepartments(page = 1, limit = 20): Promise<WecomDepartmentsResponse> {
  return apiFetch(`${BASE}/wecom-departments?page=${page}&limit=${limit}`)
}

export function getMembers(page = 1, limit = 20, q?: string): Promise<WecomMembersResponse> {
  const params = new URLSearchParams({ page: String(page), limit: String(limit) })
  if (q) params.set("q", q)
  return apiFetch(`${BASE}/wecom-members?${params}`)
}
