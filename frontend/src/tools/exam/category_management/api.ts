/** API calls for exam category management module */

const BASE = "/api/v1/exams"

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
  if (res.status === 204) return undefined as T
  return res.json() as Promise<T>
}

// ─── Types ──────────────────────────────────────────────────────────────────

export interface ExamCategory {
  id: number
  name: string
  sort_order: number
  created_at: string | null
}

export interface ExamCategoriesResponse {
  data: ExamCategory[]
  count: number
}

// ─── Category CRUD ──────────────────────────────────────────────────────────

export function listExamCategories(): Promise<ExamCategoriesResponse> {
  return apiFetch(`${BASE}/categories`)
}

export function createExamCategory(data: {
  name: string
  sort_order?: number
}): Promise<ExamCategory> {
  return apiFetch(`${BASE}/categories`, {
    method: "POST",
    body: JSON.stringify(data),
  })
}

export function updateExamCategory(
  id: number,
  data: { name?: string; sort_order?: number },
): Promise<ExamCategory> {
  return apiFetch(`${BASE}/categories/${id}`, {
    method: "PUT",
    body: JSON.stringify(data),
  })
}

export function deleteExamCategory(id: number): Promise<void> {
  return apiFetch(`${BASE}/categories/${id}`, { method: "DELETE" })
}
