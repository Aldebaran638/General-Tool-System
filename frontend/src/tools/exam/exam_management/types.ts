/** Types for exam management module */

export interface TrainerInfo {
  id: string
  name: string
}

export interface Exam {
  id: string
  name: string
  trainer_ids: string[] | null
  trainers: TrainerInfo[] | null
  category_id: number | null
  category_name: string | null
  status: "DRAFT" | "PUBLISHED" | "ARCHIVED"
  start_at: string
  end_at: string
  duration_minutes: number
  attempt_limit_type: "UNLIMITED" | "LIMITED"
  attempt_limit_count: number | null
  pass_score: number
  submit_rule: "ALL_REQUIRED" | "ANY"
  show_answer: boolean
  random_question_order: boolean
  random_option_order: boolean
  created_by: string
  published_at: string | null
  created_at: string | null
  updated_at: string | null
}

export interface ExamsResponse {
  data: Exam[]
  count: number
}

export interface ExamCreate {
  name: string
  trainer_ids?: string[]
  category_id?: number | null
  start_at: string
  end_at: string
  duration_minutes: number
  attempt_limit_type?: "UNLIMITED" | "LIMITED"
  attempt_limit_count?: number
  pass_score: number
  submit_rule?: "ALL_REQUIRED" | "ANY"
  show_answer?: boolean
  random_question_order?: boolean
  random_option_order?: boolean
}

export interface ExamUpdate {
  name?: string
  trainer_ids?: string[]
  category_id?: number | null
  start_at?: string
  end_at?: string
  duration_minutes?: number
  attempt_limit_type?: "UNLIMITED" | "LIMITED"
  attempt_limit_count?: number
  pass_score?: number
  submit_rule?: "ALL_REQUIRED" | "ANY"
  show_answer?: boolean
  random_question_order?: boolean
  random_option_order?: boolean
}

export interface QuestionOption {
  id: string
  question_id: string
  option_key: string
  option_text: string
  is_correct: boolean
  sort_no: number
}

export interface Question {
  id: string
  exam_id: string
  question_type: "SINGLE_CHOICE" | "MULTIPLE_CHOICE" | "TRUE_FALSE"
  stem: string
  score: number
  sort_no: number
  analysis: string | null
  options: QuestionOption[]
}

export interface PaperData {
  questions: Question[]
  total_score: number
  question_count: number
}

export interface OptionCreate {
  option_key: string
  option_text: string
  is_correct?: boolean
  sort_no?: number
}

export interface QuestionCreate {
  question_type: "SINGLE_CHOICE" | "MULTIPLE_CHOICE" | "TRUE_FALSE"
  stem: string
  score: number
  sort_no?: number
  analysis?: string
  options: OptionCreate[]
}

export interface PaperSaveRequest {
  questions: QuestionCreate[]
}

export interface ExamParticipant {
  id: string
  exam_id: string
  userid: string
  name_snapshot: string | null
  center_snapshot: string | null
  department_snapshot: string | null
  position_snapshot: string | null
  wecom_status_snapshot: number | null
  created_at: string | null
}

export interface ParticipantsResponse {
  data: ExamParticipant[]
  count: number
}

export interface PublishValidation {
  valid: boolean
  errors: string[]
}

export interface MyPendingExam {
  id: string
  name: string
  start_at: string
  end_at: string
  is_in_progress: boolean
}
