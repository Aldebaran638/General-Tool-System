/** API calls for the system dashboard tool module */

import { apiFetch } from "@/lib/api"

import type { SystemDashboardStats } from "./types"

const BASE = "/api/v1/exams"

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
