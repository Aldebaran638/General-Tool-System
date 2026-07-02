/** Types for exam category management module */

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
