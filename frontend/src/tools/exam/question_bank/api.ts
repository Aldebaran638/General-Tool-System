/**
 * Question Bank API — browse and download exam papers
 */

import { apiFetch } from "@/lib/api"

const BASE = "/api/v1/exams"

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
  category_ids?: number[]
}): Promise<QuestionBankResponse> {
  const p = new URLSearchParams()
  if (params?.page) p.set("page", String(params.page))
  if (params?.limit) p.set("limit", String(params.limit))
  if (params?.category_ids?.length) {
    p.set("category_ids", params.category_ids.join(","))
  }
  return apiFetch(`${BASE}/question-bank?${p}`)
}

export function getQuestionBankDetail(
  examId: string,
): Promise<QuestionBankDetail> {
  return apiFetch(`${BASE}/question-bank/${examId}`)
}

function filenameFromDisposition(disposition: string | null): string {
  if (!disposition) return "exam_paper.docx"
  const utf8Match = disposition.match(/filename\*=UTF-8''([^;]+)/i)
  if (utf8Match?.[1]) return decodeURIComponent(utf8Match[1])
  const asciiMatch = disposition.match(/filename="?([^";]+)"?/i)
  return asciiMatch?.[1] ?? "exam_paper.docx"
}

export function generatePaper(examId: string): Promise<{
  status: string
  docx_path: string | null
  generated_at: string | null
}> {
  return apiFetch(`${BASE}/${examId}/generate-paper`, { method: "POST" })
}

export async function downloadQuestionBank(examId: string): Promise<void> {
  const token = localStorage.getItem("access_token")
  const url = `${BASE}/question-bank/${examId}/download`
  const res = await fetch(url, {
    headers: token ? { Authorization: `Bearer ${token}` } : {},
  })
  if (!res.ok) {
    const body = await res.json().catch(() => ({}))
    throw new Error(body?.detail ?? `HTTP ${res.status}`)
  }

  const blob = await res.blob()
  const objectUrl = URL.createObjectURL(blob)
  const a = document.createElement("a")
  a.href = objectUrl
  a.download = filenameFromDisposition(res.headers.get("content-disposition"))
  document.body.appendChild(a)
  a.click()
  document.body.removeChild(a)
  window.setTimeout(() => URL.revokeObjectURL(objectUrl), 60_000)
}
