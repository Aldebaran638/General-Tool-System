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

export interface TrainerExamItem {
  exam_id: string
  exam_name: string
  center: string | null
  start_at: string
  participant_count: number
}

export interface TrainerGroup {
  trainer_id: string
  trainer_name: string
  exam_count: number
  total_participants: number
  exams: TrainerExamItem[]
}

export interface TrainerSummaryResponse {
  data: TrainerGroup[]
  count: number
}

export function getTrainerSummary(params?: {
  q?: string
  start_date?: string
  end_date?: string
}): Promise<TrainerSummaryResponse> {
  const searchParams = new URLSearchParams()
  if (params?.q) searchParams.set("q", params.q)
  if (params?.start_date) searchParams.set("start_date", params.start_date)
  if (params?.end_date) searchParams.set("end_date", params.end_date)
  const query = searchParams.toString()
  return apiFetch(`${BASE}/admin/trainers/summary${query ? `?${query}` : ""}`)
}
