/** API calls for exam category management module */

import { apiFetch } from "@/lib/api"

const BASE = "/api/v1/exams"

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
