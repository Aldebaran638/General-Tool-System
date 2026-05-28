/** API calls for exam management module */

import type {
  Exam,
  ExamCreate,
  ExamUpdate,
  ExamsResponse,
  PaperData,
  PaperSaveRequest,
  ParticipantsResponse,
  PublishValidation,
} from "./types"

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

// ─── Exam CRUD ──────────────────────────────────────────────────────────────

export function listExams(params?: {
  page?: number
  limit?: number
  status?: string
  q?: string
}): Promise<ExamsResponse> {
  const p = new URLSearchParams()
  if (params?.page) p.set("page", String(params.page))
  if (params?.limit) p.set("limit", String(params.limit))
  if (params?.status) p.set("status", params.status)
  if (params?.q) p.set("q", params.q)
  return apiFetch(`${BASE}?${p}`)
}

export function getExam(examId: string): Promise<Exam> {
  return apiFetch(`${BASE}/${examId}`)
}

export function createExam(data: ExamCreate): Promise<Exam> {
  return apiFetch(BASE, { method: "POST", body: JSON.stringify(data) })
}

export function updateExam(examId: string, data: ExamUpdate): Promise<Exam> {
  return apiFetch(`${BASE}/${examId}`, { method: "PUT", body: JSON.stringify(data) })
}

export function deleteExam(examId: string): Promise<void> {
  return apiFetch(`${BASE}/${examId}`, { method: "DELETE" })
}

// ─── Lifecycle ──────────────────────────────────────────────────────────────

export function publishExam(examId: string): Promise<Exam> {
  return apiFetch(`${BASE}/${examId}/publish`, { method: "POST" })
}

export function archiveExam(examId: string): Promise<Exam> {
  return apiFetch(`${BASE}/${examId}/archive`, { method: "POST" })
}

export function validateExam(examId: string): Promise<PublishValidation> {
  return apiFetch(`${BASE}/${examId}/validate`, { method: "POST" })
}

// ─── Paper ──────────────────────────────────────────────────────────────────

export function getPaper(examId: string): Promise<PaperData> {
  return apiFetch(`${BASE}/${examId}/paper`)
}

export function savePaper(examId: string, data: PaperSaveRequest): Promise<void> {
  return apiFetch(`${BASE}/${examId}/paper`, { method: "PUT", body: JSON.stringify(data) })
}

// ─── Participants ───────────────────────────────────────────────────────────

export function listParticipants(
  examId: string,
  params?: { page?: number; limit?: number; q?: string }
): Promise<ParticipantsResponse> {
  const p = new URLSearchParams()
  if (params?.page) p.set("page", String(params.page))
  if (params?.limit) p.set("limit", String(params.limit))
  if (params?.q) p.set("q", params.q)
  return apiFetch(`${BASE}/${examId}/participants?${p}`)
}

export function addParticipantsByCenters(
  examId: string,
  centerIds: number[]
): Promise<{ added: number }> {
  return apiFetch(`${BASE}/${examId}/participants/by-centers`, {
    method: "POST",
    body: JSON.stringify({ center_ids: centerIds }),
  })
}

export function addParticipantsByDepartments(
  examId: string,
  departmentIds: number[]
): Promise<{ added: number }> {
  return apiFetch(`${BASE}/${examId}/participants/by-departments`, {
    method: "POST",
    body: JSON.stringify({ department_ids: departmentIds }),
  })
}

export function addParticipantsByUsers(
  examId: string,
  userids: string[]
): Promise<{ added: number }> {
  return apiFetch(`${BASE}/${examId}/participants/by-users`, {
    method: "POST",
    body: JSON.stringify({ userids }),
  })
}

export function removeParticipant(examId: string, userid: string): Promise<void> {
  return apiFetch(`${BASE}/${examId}/participants/${userid}`, { method: "DELETE" })
}
