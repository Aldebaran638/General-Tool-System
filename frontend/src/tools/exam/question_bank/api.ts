/**
 * Question Bank API — browse and download exam papers
 */

const BASE = "/api/v1/exams"

function authHeaders(): Record<string, string> {
  const token = localStorage.getItem("access_token")
  return token ? { Authorization: `Bearer ${token}` } : {}
}

async function apiFetch<T>(url: string, init?: RequestInit): Promise<T> {
  const res = await fetch(url, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...authHeaders(),
      ...init?.headers,
    },
  })
  if (!res.ok) {
    const body = await res.json().catch(() => ({}))
    throw new Error(body?.detail ?? `HTTP ${res.status}`)
  }
  return res.json() as Promise<T>
}

// ─── Types ──────────────────────────────────────────────────────────────────

export interface QuestionBankItem {
  exam_id: string
  exam_name: string
  category_id: number | null
  category_name: string | null
  status: string // PENDING / GENERATED / FAILED
  generated_at: string | null
  question_count: number
  total_score: number
}

export interface QuestionBankResponse {
  data: QuestionBankItem[]
  count: number
}

export interface OptionPublic {
  id: string
  question_id: string
  option_key: string
  option_text: string
  is_correct: boolean
  sort_no: number
}

export interface QuestionPublic {
  id: string
  exam_id: string
  question_type: string
  stem: string
  score: number
  sort_no: number
  analysis: string | null
  options: OptionPublic[]
}

export interface QuestionBankDetail {
  exam_id: string
  exam_name: string
  questions: QuestionPublic[]
  total_score: number
  question_count: number
}

// ─── API Functions ──────────────────────────────────────────────────────────

export function listQuestionBank(params?: {
  page?: number
  limit?: number
  category_id?: number
}): Promise<QuestionBankResponse> {
  const p = new URLSearchParams()
  if (params?.page) p.set("page", String(params.page))
  if (params?.limit) p.set("limit", String(params.limit))
  if (params?.category_id) p.set("category_id", String(params.category_id))
  return apiFetch(`${BASE}/question-bank?${p}`)
}

export function getQuestionBankDetail(
  examId: string,
): Promise<QuestionBankDetail> {
  return apiFetch(`${BASE}/question-bank/${examId}`)
}

export function downloadQuestionBank(examId: string): void {
  const token = localStorage.getItem("access_token")
  const url = `${BASE}/question-bank/${examId}/download`
  const a = document.createElement("a")
  a.href = token ? `${url}?access_token=${token}` : url
  a.download = "" // Browser will use the filename from the server
  document.body.appendChild(a)
  a.click()
  document.body.removeChild(a)
}
