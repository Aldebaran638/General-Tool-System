/** API calls for the system dashboard tool module */

import type { SystemDashboardStats } from "./types"

const BASE = "/api/v1/exams"

function authHeaders(): Record<string, string> {
  const token = localStorage.getItem("access_token")
  return token ? { Authorization: `Bearer ${token}` } : {}
}

async function apiFetch<T>(url: string): Promise<T> {
  const res = await fetch(url, { headers: authHeaders() })
  if (!res.ok) {
    const body = await res.json().catch(() => ({}))
    throw new Error(body?.detail ?? `HTTP ${res.status}`)
  }
  return res.json()
}

export function getSystemDashboardStats(params?: {
  start_date?: string
  end_date?: string
}): Promise<SystemDashboardStats> {
  const searchParams = new URLSearchParams()
  if (params?.start_date) searchParams.set("start_date", params.start_date)
  if (params?.end_date) searchParams.set("end_date", params.end_date)
  const query = searchParams.toString()
  return apiFetch(`${BASE}/admin/dashboard/stats${query ? `?${query}` : ""}`)
}
