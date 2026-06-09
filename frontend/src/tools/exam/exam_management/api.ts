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
  MyPendingExam,
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

export function cloneExam(examId: string): Promise<Exam> {
  return apiFetch(`${BASE}/${examId}/clone`, { method: "POST" })
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

// ─── Statistics ─────────────────────────────────────────────────────────────

export interface ScoreDistribution {
  range_label: string
  count: number
}

export interface ExamStatistics {
  total_participants: number
  completed_count: number
  passed_count: number
  failed_count: number
  not_started_count: number
  in_progress_count: number
  pass_rate: number
  avg_score: number | null
  max_score: number | null
  min_score: number | null
  score_distribution: ScoreDistribution[]
}

export function getMyPendingExams(): Promise<{ data: MyPendingExam[]; count: number }> {
  return apiFetch(`${BASE}/my-pending`)
}

export function getExamStatistics(examId: string): Promise<ExamStatistics> {
  return apiFetch(`${BASE}/${examId}/statistics`)
}

export interface ParticipantDetail {
  id: string
  userid: string
  name_snapshot: string | null
  center_snapshot: string | null
  department_snapshot: string | null
  position_snapshot: string | null
  completion_status: string
  final_score: number | null
  final_passed: boolean
  completed_at: string | null
}

export interface ParticipantListResponse {
  data: ParticipantDetail[]
  count: number
}

export function getParticipantsByStatus(
  examId: string,
  status: string
): Promise<ParticipantListResponse> {
  return apiFetch(`${BASE}/${examId}/participants/by-status?status=${status}`)
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

// ─── User Search ─────────────────────────────────────────────────────────────

export interface WecomUser {
  userid: string
  name: string
  is_active: boolean
  created_at: string | null
}

export interface WecomUsersResponse {
  data: WecomUser[]
  count: number
}

export async function searchUsers(params: {
  q?: string
  page?: number
  limit?: number
}): Promise<WecomUsersResponse> {
  const p = new URLSearchParams()
  if (params.q) p.set("q", params.q)
  if (params.page) p.set("skip", String((params.page - 1) * (params.limit ?? 20)))
  if (params.limit) p.set("limit", String(params.limit))

  const res = await apiFetch<{
    data: Array<{
      id: string
      email: string
      is_active: boolean
      is_superuser: boolean
      full_name: string | null
      wecom_userid: string | null
      created_at: string | null
    }>
    count: number
  }>(`/api/v1/users/?${p}`)

  // Transform UserPublic response to WecomUser format for compatibility
  return {
    data: res.data.map((u) => ({
      userid: u.wecom_userid || u.id,
      name: u.full_name || u.email,
      is_active: u.is_active,
      created_at: u.created_at,
    })),
    count: res.count,
  }
}

// ─── Department Search ───────────────────────────────────────────────────────

export interface WecomDepartment {
  id: number
  name: string
  name_en: string | null
  parentid: number | null
  order: number
  level?: number
}

export interface WecomDepartmentsResponse {
  data: WecomDepartment[]
  count: number
}

export async function searchDepartments(params: {
  q?: string
  page?: number
  limit?: number
}): Promise<WecomDepartmentsResponse> {
  const p = new URLSearchParams()
  if (params.q) p.set("q", params.q)
  if (params.page) p.set("page", String(params.page))
  if (params.limit) p.set("limit", String(params.limit))
  return apiFetch<WecomDepartmentsResponse>(`/api/v1/data-sync/wecom-departments?${p}`)
}

export async function getCenters(params: {
  q?: string
  page?: number
  limit?: number
}): Promise<WecomDepartmentsResponse> {
  const p = new URLSearchParams()
  if (params.q) p.set("q", params.q)
  if (params.page) p.set("page", String(params.page))
  if (params.limit) p.set("limit", String(params.limit))
  return apiFetch<WecomDepartmentsResponse>(`/api/v1/data-sync/wecom-centers?${p}`)
}

export async function getDepartmentsOnly(params: {
  q?: string
  page?: number
  limit?: number
}): Promise<WecomDepartmentsResponse> {
  const p = new URLSearchParams()
  if (params.q) p.set("q", params.q)
  if (params.page) p.set("page", String(params.page))
  if (params.limit) p.set("limit", String(params.limit))
  p.set("level", "2")
  return apiFetch<WecomDepartmentsResponse>(`/api/v1/data-sync/wecom-departments?${p}`)
}
