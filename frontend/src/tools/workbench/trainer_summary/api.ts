/** API calls for the trainer summary tool module */

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

export interface TrainerSummaryItem {
  trainer_id: string
  trainer_name: string
  exam_id: string
  exam_name: string
  center: string | null
  start_at: string
  participant_count: number
}

export interface TrainerSummaryResponse {
  data: TrainerSummaryItem[]
  count: number
}

export function getTrainerSummary(): Promise<TrainerSummaryResponse> {
  return apiFetch(`${BASE}/admin/trainers/summary`)
}
