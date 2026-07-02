/**
 * Exam Participation API — for regular users
 */

const API_BASE = "/api/v1/my-exams"

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

export interface MyExam {
  id: string
  name: string
  category_id: number | null
  category_name: string | null
  description: string | null
  status: string  // PUBLISHED | ARCHIVED
  start_at: string
  end_at: string
  duration_minutes: number
  attempt_limit_type: "UNLIMITED" | "LIMITED"
  attempt_limit_count: number | null
  pass_score: number
  show_answer: boolean
  created_at: string
  // Attempt stats
  attempt_count: number
  best_score: number | null
  last_score: number | null
  passed: boolean
  completion_status: string // NOT_STARTED / IN_PROGRESS / COMPLETED / NOT_COMPLETED
  can_attempt: boolean
  is_ended: boolean
}

export interface MyExamsResponse {
  data: MyExam[]
  count: number
}

export interface ExamQuestionOption {
  id: string
  option_key: string
  option_text: string
}

export interface ExamQuestion {
  id: string
  question_type: string
  stem: string
  score: number
  sort_no: number
  options: ExamQuestionOption[]
}

export interface ExamPaper {
  exam_id: string
  exam_name: string
  duration_minutes: number
  pass_score: number
  questions: ExamQuestion[]
}

export interface SubmitAnswer {
  question_id: string
  selected_option_ids: string[]
}

export interface SubmitResult {
  total_score: number
  max_score: number
  passed: boolean
  correct_count: number
  total_count: number
}

export interface StartExamResult {
  attempt_id: string
  started_at: string
  expire_at: string | null
  duration_minutes: number
}

export async function fetchMyExams(
  page: number = 1,
  limit: number = 20,
): Promise<MyExamsResponse> {
  return apiFetch(`${API_BASE}?page=${page}&limit=${limit}`)
}

export async function fetchMyExamDetail(examId: string): Promise<MyExam> {
  return apiFetch(`${API_BASE}/${examId}`)
}

export async function fetchExamPaper(examId: string): Promise<ExamPaper> {
  return apiFetch(`${API_BASE}/${examId}/paper`)
}

export async function startExam(examId: string): Promise<StartExamResult> {
  return apiFetch(`${API_BASE}/${examId}/start`, {
    method: "POST",
  })
}

export async function submitExamAnswers(
  examId: string,
  attemptId: string,
  answers: SubmitAnswer[],
): Promise<SubmitResult> {
  return apiFetch(`${API_BASE}/${examId}/submit`, {
    method: "POST",
    body: JSON.stringify({ attempt_id: attemptId, answers }),
  })
}
