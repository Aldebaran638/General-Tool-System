/** API calls for question bank management module */

import type {
  QuestionBankQuestion,
  QuestionBankQuestionCreate,
  QuestionBankSet,
  QuestionBankSetCreate,
  QuestionBankSetDetail,
  QuestionBankSetsResponse,
} from "./types"

const BASE = "/api/v1/question-bank-management"

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
  if (res.status === 204) return undefined as T
  return res.json() as Promise<T>
}

// ─── Set CRUD ───────────────────────────────────────────────────────────────

export function listSets(params?: {
  q?: string
  category_id?: number
}): Promise<QuestionBankSetsResponse> {
  const p = new URLSearchParams()
  if (params?.q) p.set("q", params.q)
  if (params?.category_id !== undefined) p.set("category_id", String(params.category_id))
  const query = p.toString()
  return apiFetch(`${BASE}/sets${query ? `?${query}` : ""}`)
}

export function createSet(data: QuestionBankSetCreate): Promise<QuestionBankSet> {
  return apiFetch(`${BASE}/sets`, { method: "POST", body: JSON.stringify(data) })
}

export function getSet(setId: string): Promise<QuestionBankSetDetail> {
  return apiFetch(`${BASE}/sets/${setId}`)
}

export function updateSet(
  setId: string,
  data: Partial<QuestionBankSetCreate>,
): Promise<QuestionBankSet> {
  return apiFetch(`${BASE}/sets/${setId}`, { method: "PUT", body: JSON.stringify(data) })
}

export function deleteSet(setId: string): Promise<void> {
  return apiFetch(`${BASE}/sets/${setId}`, { method: "DELETE" })
}

// ─── Question CRUD ───────────────────────────────────────────────────────────

export function createQuestion(
  setId: string,
  data: QuestionBankQuestionCreate,
): Promise<QuestionBankQuestion> {
  return apiFetch(`${BASE}/sets/${setId}/questions`, {
    method: "POST",
    body: JSON.stringify(data),
  })
}

export function updateQuestion(
  setId: string,
  questionId: string,
  data: Partial<QuestionBankQuestionCreate>,
): Promise<QuestionBankQuestion> {
  return apiFetch(`${BASE}/sets/${setId}/questions/${questionId}`, {
    method: "PUT",
    body: JSON.stringify(data),
  })
}

export function deleteQuestion(setId: string, questionId: string): Promise<void> {
  return apiFetch(`${BASE}/sets/${setId}/questions/${questionId}`, {
    method: "DELETE",
  })
}
